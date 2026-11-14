"""Monta e valida as ondas do estágio 6 (molbytes.scaffold).

Lê o índice `tickets.yaml` (estágio 5), a `classificacao.json` do
`scaffold-router` e, se existir, o `risks.yaml` (estágio 3), e grava o
`agent-map.json` do estágio 7. Só biblioteca padrão do Python 3.8+.

Valida antes de gravar (com erro, não grava nada e sai com código 1):
- índice: id duplicado, dependência que não existe, ciclo de dependências;
- requisitos de segurança (com `risks.yaml`): requisito que nenhum ticket
  lista em `security_reqs`, ticket que lista requisito que não existe;
- classificação: ticket sem classificação, ticket que não está no índice,
  ticket repetido, nível inválido, `forte` sem motivo.

Ondas: o ticket `*INFRA-000` fica sozinho na onda 1. Os outros entram, na
ordem do índice respeitando as dependências, na primeira onda depois de todas
as dependências em que nenhum outro ticket toca os mesmos arquivos (um
diretório conflita com o que está dentro dele). Mesma entrada, mesmas ondas.

Verificação de fim de onda: cada onda leva `suite`, "area" (só os testes do
que a onda tocou) ou "completa" (a suíte inteira e os builds de todas as
plataformas): a cada SUITE_A_CADA ondas e na última.

O resumo avisa quando há SEQUENCIA_FINA ou mais ondas seguidas de um ticket
só: quase sempre uma cadeia de dependências de ordem, que deixa a rodada em
série. A lista vai ao usuário com o plano.

Replanejar no estágio 7 (`--feitos ARQ`): quando o orquestrador parte um
ticket, cria tickets novos (no `tickets.yaml`) ou passa do fim do mapa, as
ondas que faltam saem daqui, e não de uma fila escrita à mão. Só os tickets
em aberto (os do índice fora de `--feitos` e de `--fora`) entram, pelas mesmas
regras; dependência de ticket feito já está satisfeita. `--fora ARQ`: tickets
deixados de fora de propósito (o motivo fica no `state.md`); quem depende
deles fica de fora também, com aviso. Ticket em aberto sem classificação entra
como medio, com aviso. As ondas são numeradas a partir de `--a-partir N` e o
resultado vai para `ondas-replano.json`; o `agent-map.json` não muda.
`--max-por-onda N` limita os tickets por onda (nas duas formas de uso).
ARQ: ids separados por espaço, vírgula ou linha; `#` começa comentário.

Uso: python ondas.py <pasta de documentos> [--classificacao ARQ] [--saida ARQ]
                     [--feitos ARQ [--fora ARQ] [--a-partir N]] [--max-por-onda N]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

NIVEIS = {"leve": "leve", "medio": "medio", "médio": "medio", "forte": "forte",
          "haiku": "leve", "sonnet": "medio", "opus": "forte"}
LIMITE_FORTE = 0.25
SUITE_A_CADA = 5
SEQUENCIA_FINA = 5


def _escalar(valor: str) -> str:
    valor = valor.strip()
    aspas = re.match(r"([\"'])(.*?)\1", valor)          # entre aspas, com ou sem comentário depois
    if aspas:
        return aspas.group(2)
    return re.sub(r"\s+#.*$", "", valor).strip()


def _lista(valor: str) -> list:
    # Até o primeiro `]`: o que vem depois (`[A, B]  # motivo`) é comentário.
    texto = valor.strip()
    fim = texto.find("]")
    corpo = (texto[1:fim] if fim >= 0 else texto[1:]).strip()
    if not corpo:
        return []
    itens = re.findall(r"\"[^\"]*\"|'[^']*'|[^,]+", corpo)
    return [_escalar(i) for i in itens if _escalar(i)]


def ler_indice(texto: str) -> list:
    """Tickets do índice: id, area, depende_de, arquivos, security_reqs (e a linha onde começam).

    Lê o formato do estágio 5: um ticket por item `- id:`, campos um por linha,
    listas como `[a, b]` ou em bloco (`- a`). Outros campos são ignorados.
    """
    tickets, atual, recuo, chave_lista, acumulado = [], None, 0, None, None
    for numero, linha in enumerate(texto.splitlines(), 1):
        if acumulado is not None:                       # lista [..] em várias linhas
            acumulado[1] += " " + linha.strip()
            if "]" in linha:
                atual[acumulado[0]] = _lista(acumulado[1])
                acumulado = None
            continue
        if not linha.strip() or linha.lstrip().startswith("#"):
            continue
        espacos = len(linha) - len(linha.lstrip())
        novo = re.match(r"(\s*)-\s+id:\s*(.+)$", linha)
        if novo:
            atual = {"id": _escalar(novo.group(2)), "area": "", "depende_de": [],
                     "arquivos": [], "security_reqs": [], "linha": numero}
            tickets.append(atual)
            recuo, chave_lista = len(novo.group(1)), None
            continue
        if atual is None:
            continue
        if espacos <= recuo:                            # saiu do ticket (outra chave do topo)
            atual, chave_lista = None, None
            continue
        item = re.match(r"\s*-\s+(.*)$", linha)
        if item and chave_lista:
            atual[chave_lista].append(_escalar(item.group(1)))
            continue
        campo = re.match(r"\s*([\w-]+):\s*(.*)$", linha)
        if not campo:
            continue
        chave, valor = campo.group(1), campo.group(2).strip()
        chave_lista = None
        if chave not in ("area", "depende_de", "arquivos", "security_reqs"):
            continue
        if chave == "area":
            atual["area"] = _escalar(valor)
        elif valor.startswith("[") and "]" not in valor:
            acumulado = [chave, valor]
        elif valor.startswith("["):
            atual[chave] = _lista(valor)
        elif not valor:
            chave_lista = chave
        else:
            atual[chave] = [_escalar(valor)]
    return tickets


def ler_requisitos(texto: str) -> list:
    """Ids da lista `security_requirements` do `risks.yaml`, na ordem."""
    ids, dentro = [], False
    for linha in texto.splitlines():
        if not linha.strip() or linha.lstrip().startswith("#"):
            continue
        if not linha[:1].isspace() and not linha.startswith("-"):   # chave do topo
            dentro = linha.split(":", 1)[0].strip() == "security_requirements"
            continue
        item = re.match(r"\s*-\s+id:\s*(.+)$", linha)
        if dentro and item:
            ids.append(_escalar(item.group(1)))
    return ids


def ler_classificacao(texto: str) -> list:
    dados = json.loads(texto)
    if isinstance(dados, dict):
        dados = dados.get("tickets", [])
    if not isinstance(dados, list):
        raise ValueError("classificação deve ser uma lista de tickets (ou {\"tickets\": [...]})")
    return dados


def _caminho(p: str) -> str:
    p = p.replace("\\", "/").strip()
    p = re.split(r"[*?\[]", p, 1)[0]                  # padrão vira o diretório antes dele
    while p.startswith("./"):
        p = p[2:]
    return p.rstrip("/")


def conflitam(a: list, b: list) -> bool:
    for x in map(_caminho, a):
        for y in map(_caminho, b):
            if not x or not y or x == y or x.startswith(y + "/") or y.startswith(x + "/"):
                return True
    return False


def _peca(filho: str, pai: str) -> bool:
    """`FE-020a`, `FE-021A` e `BE-030C0` são peças de `FE-020`, `FE-021` e `BE-030C`; `FE-0200` não é."""
    resto = filho[len(pai):]
    if filho == pai or not filho.startswith(pai):
        return False
    return resto[:1].isalpha() or (pai[-1:].isalpha() and resto[:1].isdigit())


def ler_ids(texto: str) -> list:
    """Ids de um arquivo de `--feitos`/`--fora`: separados por espaço, vírgula ou linha; `#` é comentário."""
    ids = []
    for linha in texto.splitlines():
        ids += [i for i in re.split(r"[\s,;]+", linha.split("#", 1)[0]) if i]
    return ids


def montar(indice: list, classificacao: list, requisitos: list | None = None,
           feitos: list | None = None, fora: list | None = None, inicio: int = 1,
           max_por_onda: int | None = None) -> tuple:
    """(agent-map, erros, avisos). Com erro, o agent-map é None.

    `requisitos`: ids de `security_requirements` do `risks.yaml`; None quando
    ele não existe (a cobertura não é conferida).
    `feitos` (replanejar no estágio 7): ids já feitos; só os outros entram, e
    as ondas começam em `inicio`. `fora`: deixados de fora de propósito.
    """
    erros, avisos = [], []
    replano = feitos is not None
    feitos_set, fora_set = set(feitos or []), set(fora or [])
    pecas = {}      # replanejar: pai partido -> peças no índice
    por_id = {}
    for t in indice:
        if t["id"] in por_id:
            erros.append(f"tickets.yaml: {t['id']} aparece mais de uma vez (linhas {por_id[t['id']]['linha']} e {t['linha']})")
        else:
            por_id[t["id"]] = t
    for t in por_id.values():
        for dep in t["depende_de"]:
            if dep not in por_id:
                erros.append(f"tickets.yaml: {t['id']} depende de {dep}, que não existe")
        if not t["arquivos"]:
            avisos.append(f"tickets.yaml: {t['id']} sem `arquivos` (não entra na checagem de conflito)")
    if requisitos is not None:
        cobertos = set()
        for t in por_id.values():
            for sr in t["security_reqs"]:
                if sr in requisitos:
                    cobertos.add(sr)
                else:
                    erros.append(f"tickets.yaml: {t['id']} lista {sr} em `security_reqs`, que não existe no risks.yaml")
        for sr in requisitos:
            if sr not in cobertos:
                erros.append(f"tickets.yaml: {sr} (risks.yaml) não está em `security_reqs` de nenhum ticket")

    classes = {}
    for c in classificacao:
        tid = str(c.get("id", "")).strip() if isinstance(c, dict) else ""
        if not tid:
            erros.append(f"classificação: item sem id: {c!r}")
            continue
        if tid in classes:
            erros.append(f"classificação: {tid} aparece mais de uma vez")
            continue
        if tid not in por_id:
            if replano:     # ticket partido ou tirado do índice no estágio 7
                avisos.append(f"classificação: {tid} não está no tickets.yaml (ignorado)")
            else:
                erros.append(f"classificação: {tid} não está no tickets.yaml")
            continue
        nivel = NIVEIS.get(str(c.get("model", "")).strip().lower())
        if not nivel:
            erros.append(f"classificação: {tid} com nível inválido {c.get('model')!r} (use leve, medio ou forte)")
            continue
        if nivel == "forte" and not str(c.get("motivo", "")).strip():
            erros.append(f"classificação: {tid} em forte sem motivo")
        classes[tid] = {"id": tid, "area": c.get("area") or por_id[tid]["area"],
                        "complexity": c.get("complexity", ""), "model": nivel,
                        "motivo": str(c.get("motivo", "")).strip()}
    abertos = list(por_id)
    if replano:
        for nome, ids in (("--feitos", feitos_set), ("--fora", fora_set)):
            for tid in sorted(ids - set(por_id)):
                avisos.append(f"{nome}: {tid} não está no tickets.yaml")
        # Quem depende de ticket fora fica fora também (em cadeia), com aviso.
        fora_tudo = set(fora_set) - feitos_set
        mudou = True
        while mudou:
            mudou = False
            for tid, t in por_id.items():
                if tid in fora_tudo or tid in feitos_set:
                    continue
                motivo = next((d for d in t["depende_de"] if d in fora_tudo), None)
                if motivo:
                    fora_tudo.add(tid)
                    avisos.append(f"{tid} fica fora também: depende de {motivo}, que está fora")
                    mudou = True
        abertos = [tid for tid in por_id if tid not in feitos_set and tid not in fora_tudo]
        # Pai partido com as peças no índice (FE-020 → FE-020a, BE-030 → BE-030A): sai do plano
        # e quem depende dele espera todas as peças. O que depende de uma das "peças" é o ticket
        # que fecha a série (BE-030C depois de BE-030C0…C11) e fica.
        for pai in abertos:
            filhos = [f for f in por_id if _peca(f, pai)]
            if filhos and not set(filhos) & set(por_id[pai]["depende_de"]):
                pecas[pai] = filhos
                avisos.append(f"{pai} partido em {', '.join(filhos)}: entra pelas peças")
        abertos = [tid for tid in abertos if tid not in pecas]
    for tid in abertos:
        if tid in classes or any(e.startswith(f"classificação: {tid} ") for e in erros):
            continue
        if replano:
            avisos.append(f"classificação: {tid} sem classificação; entra como medio")
            classes[tid] = {"id": tid, "area": por_id[tid]["area"], "complexity": "", "model": "medio", "motivo": ""}
        else:
            erros.append(f"classificação: {tid} não foi classificado")
    if erros:
        return None, erros, avisos

    # Ordem topológica estável: entre os prontos, o que vem antes no índice. Dependência de
    # ticket feito (replanejar) já está satisfeita.
    ordem_indice = {tid: i for i, tid in enumerate(por_id)}

    def deps_de(tid):
        saida = set(por_id[tid]["depende_de"])
        for d in por_id[tid]["depende_de"]:
            saida.update(pecas.get(d, []))
        return saida

    pendentes = {tid: deps_de(tid) & set(abertos) for tid in abertos}
    ordem = []
    while pendentes:
        prontos = sorted((tid for tid, deps in pendentes.items() if not deps), key=ordem_indice.get)
        if not prontos:
            return None, ["tickets.yaml: ciclo de dependências entre " + ", ".join(sorted(pendentes, key=ordem_indice.get))], avisos
        for tid in prontos:
            ordem.append(tid)
            del pendentes[tid]
        for deps in pendentes.values():
            deps.difference_update(prontos)

    infra = [tid for tid in ordem if tid.upper().endswith("INFRA-000")]
    onda_de, ondas = {}, {}
    for tid in ordem:
        if tid in infra[:1]:
            onda_de[tid] = 1
            ondas.setdefault(1, []).append(tid)
            continue
        onda = max([onda_de[d] for d in deps_de(tid) if d in onda_de] + [1 if infra else 0]) + 1
        while (any(conflitam(por_id[tid]["arquivos"], por_id[outro]["arquivos"]) for outro in ondas.get(onda, []))
               or (max_por_onda and len(ondas.get(onda, [])) >= max_por_onda)):
            onda += 1
        onda_de[tid] = onda
        ondas.setdefault(onda, []).append(tid)

    desloca = inicio - 1
    ultima = max(ondas) + desloca if ondas else 0
    mapa = {"fonte": "scripts/ondas.py --feitos" if replano else "scripts/ondas.py", "ondas": [
        {"onda": n + desloca, "suite": "completa" if (n + desloca) % SUITE_A_CADA == 0 or n + desloca == ultima else "area",
         "tickets": [classes[tid] for tid in sorted(ondas[n], key=ordem_indice.get)]}
        for n in sorted(ondas)]}
    return mapa, [], avisos


def sequencia_fina(mapa: dict) -> list:
    """A maior sequência de ondas seguidas com um ticket só (sem contar o INFRA-000 sozinho na 1)."""
    maior, atual = [], []
    for onda in mapa["ondas"]:
        sozinho = len(onda["tickets"]) == 1 and not onda["tickets"][0]["id"].upper().endswith("INFRA-000")
        atual = atual + [onda] if sozinho else []
        if len(atual) > len(maior):
            maior = atual
    return maior


def resumo(mapa: dict) -> list:
    tickets = [t for onda in mapa["ondas"] for t in onda["tickets"]]
    conta = {n: sum(1 for t in tickets if t["model"] == n) for n in ("forte", "medio", "leve")}
    total = len(tickets)
    maior = max(len(onda["tickets"]) for onda in mapa["ondas"]) if mapa["ondas"] else 0
    pct = conta["forte"] / total if total else 0
    if "--feitos" in mapa.get("fonte", ""):
        faixa = f", da {mapa['ondas'][0]['onda']} à {mapa['ondas'][-1]['onda']}" if mapa["ondas"] else ""
        topo = f"ondas-replano.json: {total} tickets em aberto em {len(mapa['ondas'])} ondas{faixa} (maior onda: {maior})"
    else:
        topo = f"agent-map.json: {total} tickets em {len(mapa['ondas'])} ondas (maior onda: {maior})"
    linhas = [topo,
              f"Níveis: forte {conta['forte']} ({pct:.0%}) · medio {conta['medio']} · leve {conta['leve']}"]
    if pct > LIMITE_FORTE:
        linhas.append(f"Forte acima de {LIMITE_FORTE:.0%}; mostre ao usuário:")
        linhas += [f"- {t['id']}: {t['motivo']}" for t in tickets if t["model"] == "forte"]
    finas = sequencia_fina(mapa)
    if len(finas) >= SEQUENCIA_FINA:
        sozinhas = sum(1 for onda in mapa["ondas"] if len(onda["tickets"]) == 1)
        ids = [onda["tickets"][0]["id"] for onda in finas]
        linhas.append(f"Ondas de um ticket só: {sozinhas} de {len(mapa['ondas'])}; {len(finas)} seguidas, "
                      f"da onda {finas[0]['onda']} à {finas[-1]['onda']} ({' → '.join(ids)}). "
                      "Mostre ao usuário: essa cadeia roda em série.")
    return linhas


def main(args: list) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    opcoes = {"--classificacao": None, "--saida": None, "--feitos": None, "--fora": None,
              "--a-partir": None, "--max-por-onda": None}
    posicionais = []
    i = 0
    while i < len(args):
        if args[i] in opcoes and i + 1 < len(args):
            opcoes[args[i]] = args[i + 1]
            i += 2
        else:
            posicionais.append(args[i])
            i += 1
    uso = "\n".join(__doc__.strip().splitlines()[-2:])
    if len(posicionais) != 1:
        print(uso)
        return 2
    numeros = {}
    for chave in ("--a-partir", "--max-por-onda"):
        if opcoes[chave] is not None:
            if not opcoes[chave].isdigit() or int(opcoes[chave]) < 1:
                print(f"erro: {chave} pede um número a partir de 1")
                return 2
            numeros[chave] = int(opcoes[chave])
    if (opcoes["--fora"] or "--a-partir" in numeros) and not opcoes["--feitos"]:
        print("erro: --fora e --a-partir só valem com --feitos (replanejar)")
        return 2
    pasta = Path(posicionais[0])
    indice_arq = pasta / "tickets.yaml"
    classes_arq = Path(opcoes["--classificacao"] or pasta / "classificacao.json")
    replano = opcoes["--feitos"] is not None
    saida = Path(opcoes["--saida"] or pasta / ("ondas-replano.json" if replano else "agent-map.json"))
    if replano and saida.name == "agent-map.json":
        print("erro: replanejar não grava no agent-map.json (é o plano aprovado, que a faixa lê); use outra --saida")
        return 2
    listas = {}
    for chave in ("--feitos", "--fora"):
        if opcoes[chave] is not None:
            arq = Path(opcoes[chave])
            if not arq.exists():
                print(f"erro: {arq} não existe")
                return 2
            listas[chave] = ler_ids(arq.read_text(encoding="utf-8"))
    for arq in (indice_arq, classes_arq):
        if not arq.exists():
            print(f"erro: {arq} não existe")
            return 2
    try:
        classificacao = ler_classificacao(classes_arq.read_text(encoding="utf-8"))
    except (ValueError, json.JSONDecodeError) as erro:
        print(f"erro: {classes_arq}: {erro}")
        return 1
    riscos_arq = pasta / "risks.yaml"
    requisitos = ler_requisitos(riscos_arq.read_text(encoding="utf-8")) if riscos_arq.exists() else None
    mapa, erros, avisos = montar(ler_indice(indice_arq.read_text(encoding="utf-8")), classificacao, requisitos,
                                 feitos=listas.get("--feitos"), fora=listas.get("--fora"),
                                 inicio=numeros.get("--a-partir", 1), max_por_onda=numeros.get("--max-por-onda"))
    for aviso in avisos:
        print(f"aviso: {aviso}")
    if erros:
        for erro in erros:
            print(f"erro: {erro}")
        print(f"Nada gravado. {len(erros)} erro(s).")
        return 1
    saida.write_text(json.dumps(mapa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n".join(resumo(mapa)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
