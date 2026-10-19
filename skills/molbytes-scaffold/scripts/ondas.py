"""Monta e valida as ondas do estágio 6 (molbytes.scaffold).

Lê o índice `tickets.yaml` (estágio 5) e a `classificacao.json` do
`scaffold-router` e grava o `agent-map.json` do estágio 7. Só biblioteca
padrão do Python 3.8+.

Valida antes de gravar (com erro, não grava nada e sai com código 1):
- índice: id duplicado, dependência que não existe, ciclo de dependências;
- classificação: ticket sem classificação, ticket que não está no índice,
  ticket repetido, nível inválido, `forte` sem motivo.

Ondas: o ticket `*INFRA-000` fica sozinho na onda 1. Os outros entram, na
ordem do índice respeitando as dependências, na primeira onda depois de todas
as dependências em que nenhum outro ticket toca os mesmos arquivos (um
diretório conflita com o que está dentro dele). Mesma entrada, mesmas ondas.

Uso: python ondas.py <pasta de documentos> [--classificacao ARQ] [--saida ARQ]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

NIVEIS = {"leve": "leve", "medio": "medio", "médio": "medio", "forte": "forte",
          "haiku": "leve", "sonnet": "medio", "opus": "forte"}
LIMITE_FORTE = 0.25


def _escalar(valor: str) -> str:
    valor = valor.strip()
    if valor[:1] in "\"'" and valor[-1:] == valor[:1] and len(valor) >= 2:
        return valor[1:-1]
    return re.sub(r"\s+#.*$", "", valor).strip()


def _lista(valor: str) -> list:
    corpo = valor.strip()[1:-1].strip()
    if not corpo:
        return []
    itens = re.findall(r"\"[^\"]*\"|'[^']*'|[^,]+", corpo)
    return [_escalar(i) for i in itens if _escalar(i)]


def ler_indice(texto: str) -> list:
    """Tickets do índice: id, area, depende_de, arquivos (e a linha onde começam).

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
                     "arquivos": [], "linha": numero}
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
        if chave not in ("area", "depende_de", "arquivos"):
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


def montar(indice: list, classificacao: list) -> tuple:
    """(agent-map, erros, avisos). Com erro, o agent-map é None."""
    erros, avisos = [], []
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
    for tid in por_id:
        if tid not in classes and not any(e.startswith(f"classificação: {tid} ") for e in erros):
            erros.append(f"classificação: {tid} não foi classificado")
    if erros:
        return None, erros, avisos

    # Ordem topológica estável: entre os prontos, o que vem antes no índice.
    ordem_indice = {tid: i for i, tid in enumerate(por_id)}
    pendentes = {tid: set(t["depende_de"]) for tid, t in por_id.items()}
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
        onda = max([onda_de[d] for d in por_id[tid]["depende_de"]] + [1 if infra else 0]) + 1
        while any(conflitam(por_id[tid]["arquivos"], por_id[outro]["arquivos"]) for outro in ondas.get(onda, [])):
            onda += 1
        onda_de[tid] = onda
        ondas.setdefault(onda, []).append(tid)

    mapa = {"fonte": "scripts/ondas.py", "ondas": [
        {"onda": n, "tickets": [classes[tid] for tid in sorted(ondas[n], key=ordem_indice.get)]}
        for n in sorted(ondas)]}
    return mapa, [], avisos


def resumo(mapa: dict) -> list:
    tickets = [t for onda in mapa["ondas"] for t in onda["tickets"]]
    conta = {n: sum(1 for t in tickets if t["model"] == n) for n in ("forte", "medio", "leve")}
    total = len(tickets)
    maior = max(len(onda["tickets"]) for onda in mapa["ondas"]) if mapa["ondas"] else 0
    pct = conta["forte"] / total if total else 0
    linhas = [f"agent-map.json: {total} tickets em {len(mapa['ondas'])} ondas (maior onda: {maior})",
              f"Níveis: forte {conta['forte']} ({pct:.0%}) · medio {conta['medio']} · leve {conta['leve']}"]
    if pct > LIMITE_FORTE:
        linhas.append(f"Forte acima de {LIMITE_FORTE:.0%}; mostre ao usuário:")
        linhas += [f"- {t['id']}: {t['motivo']}" for t in tickets if t["model"] == "forte"]
    return linhas


def main(args: list) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    opcoes = {"--classificacao": None, "--saida": None}
    posicionais = []
    i = 0
    while i < len(args):
        if args[i] in opcoes and i + 1 < len(args):
            opcoes[args[i]] = args[i + 1]
            i += 2
        else:
            posicionais.append(args[i])
            i += 1
    if len(posicionais) != 1:
        print(__doc__.strip().splitlines()[-1])
        return 2
    pasta = Path(posicionais[0])
    indice_arq = pasta / "tickets.yaml"
    classes_arq = Path(opcoes["--classificacao"] or pasta / "classificacao.json")
    saida = Path(opcoes["--saida"] or pasta / "agent-map.json")
    for arq in (indice_arq, classes_arq):
        if not arq.exists():
            print(f"erro: {arq} não existe")
            return 2
    try:
        classificacao = ler_classificacao(classes_arq.read_text(encoding="utf-8"))
    except (ValueError, json.JSONDecodeError) as erro:
        print(f"erro: {classes_arq}: {erro}")
        return 1
    mapa, erros, avisos = montar(ler_indice(indice_arq.read_text(encoding="utf-8")), classificacao)
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
