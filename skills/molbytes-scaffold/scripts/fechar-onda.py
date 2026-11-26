"""Fecha uma onda do estágio 7 num comando só (molbytes.scaffold).

Cada chamada do orquestrador relê o contexto inteiro da sessão, e o fim da
onda é quando ele está maior. Numa execução real, o orquestrador fechava cada
onda em uma dezena de chamadas de uma ferramenta só (feitos, `git diff` dos
testes, worktrees, leitura do mapa para achar a próxima onda). Este script faz
a parte mecânica numa chamada e imprime poucas linhas. Só biblioteca padrão do
Python 3.8+.

    python fechar-onda.py <documentos> <onda> <id> [<id> ...] [--parcial] [--repo PASTA]

Roda depois da suíte da onda passar e antes do commit `scaffold(7): onda N`:

1. **Trava dos testes** (só se o `state.md` tem `Testes travados: <sha>` e
   existe `testes-travados.txt`): verifica o histórico desde a trava e o diff
   desde `Base da onda:` separadamente, cada um com as aprovações daquela etapa.
2. **Worktrees:** roda `git worktree prune` e lista as que ficaram. Worktree
   de subagente (`agent-` no nome ou na branch) que ficou é erro; as outras
   (sessões abertas do usuário) só aparecem como aviso.
3. **Feitos:** com 1 e 2 limpos, acrescenta a `feitos.txt` os ids da onda ativa.
   Correções `FIX-*` fora do índice são informativas. Uma onda incompleta
   exige `--parcial` para registrar os concluídos sem avançar. Rodar de novo
   não repete nada. Sem `feitos.txt` depois
   da onda 1 (rodada que começou antes dele), recusa: criar o arquivo só com
   esta onda faria o replano trazer de volta tudo o que já foi feito.
4. **Próxima onda:** a onda seguinte do plano ativo, com o nível de cada ticket
   e o `suite`. A partir do início do replano, ele substitui o mapa original.

Código de saída: 0 tudo certo; 1 validação, trava ou worktree de subagente
pendente (resolva e rode de novo); 2 uso errado ou arquivo que falta.
`--repo`: raiz do projeto (padrão: a do git da pasta atual); use no modo de
documentos externos.
"""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

_spec = importlib.util.spec_from_file_location("ondas", Path(__file__).with_name("ondas.py"))
ondas = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ondas)


def caminho_teste(item: str) -> str:
    """O caminho de um item de `testes_alterados` (`tests/x.py: motivo`, `arquivo: tests/x.py`)."""
    texto = item.strip()
    rotulo = re.match(r"(?:arquivo|caminho|path|file)\s*:\s*(.+)$", texto)
    if rotulo:
        texto = rotulo.group(1)
    texto = re.split(r":\s|\s+#|\s+\(|\s+[—–-]\s", texto, maxsplit=1)[0]
    return _normal(texto)


def _normal(caminho: str) -> str:
    texto = caminho.strip().strip("\"'").replace("\\", "/")
    while texto.startswith("./"):
        texto = texto[2:]
    return texto


def aprovados(indice: list, ids: list) -> set:
    """Testes que os tickets fechados podiam mudar (aprovados com o plano do estágio 6)."""
    por_id = {t["id"]: t for t in indice}
    return {caminho_teste(i) for tid in ids for i in por_id.get(tid, {}).get("testes_alterados", []) if caminho_teste(i)}


def sha_travado(state: str) -> str | None:
    return _sha_estado(state, "Testes travados")


def _sha_estado(state: str, chave: str) -> str | None:
    m = re.search(rf"^[ \t]*(?:- +)?{chave}:[ \t]*([0-9a-fA-F]{{7,64}})\b", state, re.MULTILINE)
    return m.group(1) if m else None


def travados_mudados(mudados: list, travados: list, livres: set) -> list:
    """Arquivos travados que mudaram e não estão liberados. `travados` aceita pasta (termina em /)."""
    alvos = [_normal(t) for t in travados if _normal(t)]
    saida = []
    for arq in (_normal(m) for m in mudados):
        if arq in livres:
            continue
        if any(arq == a or (a.endswith("/") and arq.startswith(a)) for a in alvos):
            saida.append(arq)
    return sorted(set(saida))


def worktrees(porcelana: str, raiz: str) -> tuple:
    """(de subagente, outras): worktrees que não são a pasta do projeto.

    A primeira do `git worktree list` é sempre a principal; `raiz` também sai
    (o script pode rodar de dentro de uma worktree).
    """
    blocos = [b for b in porcelana.strip().split("\n\n") if b.strip()]
    sub, outras = [], []
    raiz_n = _normal(str(Path(raiz).resolve())).lower().rstrip("/")
    for n, bloco in enumerate(blocos):
        campos = dict(l.split(" ", 1) for l in bloco.splitlines() if " " in l)
        caminho = campos.get("worktree", "")
        if n == 0 or _normal(str(Path(caminho).resolve())).lower().rstrip("/") == raiz_n:
            continue
        branch = campos.get("branch", "").replace("refs/heads/", "")
        nome = f"{caminho} ({branch or 'sem branch'})"
        (sub if re.search(r"agent-", Path(caminho).name + " " + branch) else outras).append(nome)
    return sub, outras


def acrescentar(texto: str, ids: list) -> tuple:
    """(texto novo, ids acrescentados), sem repetir os que já estão."""
    ja = set(ondas.ler_ids(texto))
    novos = []
    for tid in ids:
        if tid not in ja and tid not in novos:
            novos.append(tid)
    if not novos:
        return texto, []
    sep = "" if not texto or texto.endswith("\n") else "\n"
    return texto + sep + "\n".join(novos) + "\n", novos


def _ler_plano(arq: Path) -> tuple:
    mapa = json.loads(arq.read_text(encoding="utf-8-sig"))
    ondas_mapa = mapa.get("ondas") if isinstance(mapa, dict) else None
    if not isinstance(ondas_mapa, list):
        raise ValueError(f"{arq.name} sem lista de ondas")
    ondas_por_numero = {}
    for onda in ondas_mapa:
        numero = onda.get("onda") if isinstance(onda, dict) else None
        if type(numero) is not int or numero < 1 or numero in ondas_por_numero:
            raise ValueError(f"{arq.name} tem número de onda inválido ou repetido")
        tickets = onda.get("tickets")
        if not isinstance(tickets, list) or not all(
            isinstance(t, dict) and isinstance(t.get("id"), str) and t["id"] for t in tickets
        ):
            raise ValueError(f"{arq.name}, onda {numero}: lista de tickets inválida")
        ondas_por_numero[numero] = onda
    inicio = mapa.get("a_partir", min(ondas_por_numero, default=1))
    if type(inicio) is not int or inicio < 1 or any(n < inicio for n in ondas_por_numero):
        raise ValueError(f"{arq.name} tem início de replano inválido")
    return inicio, ondas_por_numero


def _ondas_do_plano(pasta: Path, numeros: tuple) -> list:
    """(arquivo, onda) de cada número, respeitando a fronteira do replano."""
    replano = pasta / "ondas-replano.json"
    original = pasta / "agent-map.json"
    inicio, novas = _ler_plano(replano) if replano.exists() else (None, {})
    antigas = {}
    if inicio is None or min(numeros) < inicio:
        _, antigas = _ler_plano(original)
    return [(replano.name, novas.get(n)) if inicio is not None and n >= inicio
            else (original.name, antigas.get(n)) for n in numeros]


def _git(repo: Path, *args: str) -> str:
    feito = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    if feito.returncode != 0:
        erro = feito.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git {' '.join(args)}: {erro or 'comando falhou'}")
    return feito.stdout.decode("utf-8", errors="surrogateescape")


def _caminhos_diff(repo: Path, *commits: str) -> list:
    return _git(repo, "diff", "--name-only", "--no-renames", "-z", *commits, "--").split("\0")


def _trava_da_onda(repo: Path, estado: str, travados: list, indice: list, numero: int,
                   feitos: set, ids_onda: set, ids_fechados: set) -> tuple:
    sha = sha_travado(estado)
    anterior = ""
    if numero > 1:
        anterior = _git(repo, "log", "-1", "--first-parent", "--format=%H",
                        f"--grep=^scaffold(7): onda {numero - 1}$", f"{sha}..HEAD").strip()
    base = _sha_estado(estado, "Base da onda") or anterior or sha
    try:
        _git(repo, "merge-base", "--is-ancestor", sha, base)
        _git(repo, "merge-base", "--is-ancestor", base, "HEAD")
        if anterior:
            _git(repo, "merge-base", "--is-ancestor", anterior, base)
    except RuntimeError as erro:
        raise ValueError(f"Base da onda {base} precisa seguir a trava e o último fechamento no histórico de HEAD") from erro

    # Uma mudança antiga só fica dispensada da permissão da onda atual se for
    # de ticket já concluído. Entre o fechamento anterior e a abertura desta
    # onda, nenhum teste travado pode ganhar alterações à parte.
    livres_anteriores = aprovados(indice, feitos - ids_onda)
    historico = _caminhos_diff(repo, sha, anterior or base)
    quebrados = travados_mudados(historico, travados, livres_anteriores)
    if anterior and anterior != base:
        quebrados += travados_mudados(_caminhos_diff(repo, anterior, base), travados, set())

    livres = aprovados(indice, ids_fechados | (feitos & ids_onda))
    mudados = _caminhos_diff(repo, base)
    mudados += _git(repo, "ls-files", "--others", "--exclude-standard", "-z").split("\0")
    quebrados += travados_mudados(mudados, travados, livres)
    usados = livres & {_normal(m) for m in mudados}
    return base, sorted(set(quebrados)), len(usados)


def _gravar_feitos(arq: Path, texto: str) -> None:
    temporario = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                         dir=arq.parent, delete=False) as saida:
            temporario = Path(saida.name)
            saida.write(texto)
        temporario.replace(arq)
    finally:
        if temporario is not None:
            temporario.unlink(missing_ok=True)


def main(args: list) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    uso = "uso: python fechar-onda.py <documentos> <onda> <id> [<id> ...] [--parcial] [--repo PASTA]"
    repo_arg, parcial, soltos, i = None, False, [], 0
    while i < len(args):
        if args[i] == "--repo" and i + 1 < len(args):
            repo_arg, i = args[i + 1], i + 2
        elif args[i] == "--parcial":
            parcial, i = True, i + 1
        else:
            soltos.append(args[i])
            i += 1
    if len(soltos) < 3 or not soltos[1].isdigit() or int(soltos[1]) < 1:
        print(uso)
        return 2
    pasta, numero, ids = Path(soltos[0]), int(soltos[1]), soltos[2:]
    indice_arq = pasta / "tickets.yaml"
    if not indice_arq.exists():
        print(f"erro: {indice_arq} não existe")
        return 2
    try:
        repo = Path(repo_arg) if repo_arg else Path(_git(Path.cwd(), "rev-parse", "--show-toplevel").strip())
    except RuntimeError as erro:
        print(f"erro: {erro} (use --repo)")
        return 2
    try:
        indice = ondas.ler_indice(indice_arq.read_text(encoding="utf-8-sig"))
        (arquivo, onda), (arquivo_seguinte, proxima) = _ondas_do_plano(pasta, (numero, numero + 1))
    except (OSError, ValueError) as erro:
        print(f"erro: {erro}")
        return 1
    if onda is None:
        print(f"erro: onda {numero} não pertence ao plano ativo ({arquivo}). Nada gravado.")
        return 1

    feitos_arq = pasta / "feitos.txt"
    if not feitos_arq.exists() and numero > 1:
        print(f"erro: {feitos_arq} não existe e esta é a onda {numero}. Crie-o antes com os ids que as "
              "ondas anteriores fecharam (um por linha): um feitos.txt só com esta onda faria o "
              "ondas.py --feitos trazer de volta tudo o que já foi feito. Nada gravado.")
        return 2
    texto = feitos_arq.read_text(encoding="utf-8-sig") if feitos_arq.exists() else ""
    feitos = set(ondas.ler_ids(texto))
    no_indice = {t["id"] for t in indice}
    ids_onda = [t["id"] for t in onda["tickets"]]
    fora = [tid for tid in ids if tid not in no_indice]
    ids_indice = [tid for tid in ids if tid in no_indice]
    invalidos = [tid for tid in ids_indice if tid not in ids_onda]
    invalidos += [tid for tid in fora if not re.fullmatch(r"FIX-[\w.-]+", tid)]
    if invalidos:
        print(f"erro: ids fora da onda {numero} ({arquivo}): {', '.join(invalidos)}. Nada gravado.")
        return 1
    sem_fechar = [tid for tid in ids_onda if tid not in feitos and tid not in ids_indice]
    if sem_fechar and not parcial:
        print(f"erro: onda {numero} incompleta ({arquivo}): {', '.join(sem_fechar)}. "
              "Use --parcial para registrar os concluídos sem avançar. Nada gravado.")
        return 1

    problemas, linhas = [], []

    state = pasta / "state.md"
    travados_arq = pasta / "testes-travados.txt"
    estado = state.read_text(encoding="utf-8-sig") if state.exists() else ""
    if sha_travado(estado) and travados_arq.exists():
        try:
            travados = [l.split("#", 1)[0].strip() for l in travados_arq.read_text(encoding="utf-8-sig").splitlines()]
            base, quebrados, liberados = _trava_da_onda(repo, estado, travados, indice, numero,
                                                      feitos, set(ids_onda), set(ids_indice))
        except (OSError, RuntimeError, ValueError) as erro:
            print(f"erro: {erro}")
            return 2
        if quebrados:
            problemas.append(f"trava: {len(quebrados)} teste(s) travado(s) mudaram sem aprovação em "
                             f"testes_alterados: {', '.join(quebrados[:10])}"
                             + (" ..." if len(quebrados) > 10 else ""))
        else:
            linhas.append(f"trava: ok desde {base}" + (f" ({liberados} liberado(s) pelo plano)" if liberados else ""))
    else:
        linhas.append("trava: sem testes travados ainda")

    try:
        _git(repo, "worktree", "prune")
        sub, outras = worktrees(_git(repo, "worktree", "list", "--porcelain"), str(repo))
    except RuntimeError as erro:
        print(f"erro: {erro}")
        return 2
    if sub:
        problemas.append(f"worktrees de subagente que ficaram ({len(sub)}): {'; '.join(sub)}. "
                         "Mergeada: git worktree remove + git branch -d; descartada: remove + branch -D; "
                         "com alteração não commitada: mostre ao usuário")
    linhas.append("worktrees: ok" + (f" (aviso: {len(outras)} de outras sessões)" if outras else ""))

    if fora:
        linhas.append(f"fora do índice (não vão para feitos.txt): {', '.join(fora)}")

    if problemas:
        for p in problemas:
            print(f"erro: {p}")
        print(f"Onda {numero} não fechada: nada gravado. Resolva e rode de novo.")
        return 1

    novo, acrescentados = acrescentar(texto, ids_indice)
    if acrescentados:
        try:
            _gravar_feitos(feitos_arq, novo)
        except OSError as erro:
            print(f"erro ao gravar {feitos_arq}: {erro}")
            return 2
    total = len(set(ondas.ler_ids(novo)))
    status = "parcial" if sem_fechar else "fechada"
    print(f"onda {numero} {status}: {', '.join(ids)} (feitos.txt: {len(acrescentados)} novo(s), {total} no total)")
    for linha in linhas:
        print(linha)
    if sem_fechar:
        print(f"pendentes nesta onda: {', '.join(sem_fechar)}")
    elif proxima is None:
        print(f"próxima: a onda {numero + 1} não está no plano. Fim de {arquivo_seguinte}, ou replaneje com ondas.py --feitos")
    else:
        tickets = ", ".join(f"{t.get('id')} {t.get('model', '?')}" for t in proxima.get("tickets", []))
        print(f"próxima: onda {numero + 1} ({arquivo_seguinte}, suite {proxima.get('suite', '?')}): {tickets}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
