"""Fecha uma onda do estágio 7 num comando só (molbytes.scaffold).

Cada chamada do orquestrador relê o contexto inteiro da sessão, e o fim da
onda é quando ele está maior. Numa execução real, o orquestrador fechava cada
onda em uma dezena de chamadas de uma ferramenta só (feitos, `git diff` dos
testes, worktrees, leitura do mapa para achar a próxima onda). Este script faz
a parte mecânica numa chamada e imprime poucas linhas. Só biblioteca padrão do
Python 3.8+.

    python fechar-onda.py <documentos> <onda> <id> [<id> ...] [--repo PASTA]

Roda depois da suíte da onda passar e antes do commit `scaffold(7): onda N`:

1. **Trava dos testes** (só se o `state.md` tem `Testes travados: <sha>` e
   existe `testes-travados.txt`): arquivo travado que mudou desde o sha e não
   está em `testes_alterados` de um ticket fechado (`tickets.yaml`) é listado.
2. **Worktrees:** roda `git worktree prune` e lista as que ficaram. Worktree
   de subagente (`agent-` no nome ou na branch) que ficou é erro; as outras
   (sessões abertas do usuário) só aparecem como aviso.
3. **Feitos:** com 1 e 2 limpos, acrescenta a `feitos.txt` os ids que estão
   no `tickets.yaml` e ainda não estão lá. Id fora do índice (ticket de
   correção) não entra. Rodar de novo não repete nada. Sem `feitos.txt` depois
   da onda 1 (rodada que começou antes dele), recusa: criar o arquivo só com
   esta onda faria o replano trazer de volta tudo o que já foi feito.
4. **Próxima onda:** a onda seguinte do `ondas-replano.json` (se ele tem essa
   onda) ou do `agent-map.json`, com o nível de cada ticket e o `suite`.

Código de saída: 0 tudo certo; 1 trava ou worktree de subagente pendente (nada
gravado: resolva e rode de novo); 2 uso errado ou arquivo que falta.
`--repo`: raiz do projeto (padrão: a do git da pasta atual); use no modo de
documentos externos.
"""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
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
    m = re.search(r"^Testes travados:\s*([0-9a-fA-F]{7,40})\b", state, re.MULTILINE)
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


def onda_do_plano(pasta: Path, numero: int) -> tuple:
    """(arquivo, onda) da onda `numero`: o replano tem prioridade quando tem essa onda."""
    for nome in ("ondas-replano.json", "agent-map.json"):
        arq = pasta / nome
        if not arq.exists():
            continue
        try:
            mapa = json.loads(arq.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for onda in mapa.get("ondas", []):
            if onda.get("onda") == numero:
                return nome, onda
    return None, None


def _git(repo: Path, *args: str) -> str:
    feito = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
    if feito.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {feito.stderr.strip()}")
    return feito.stdout


def main(args: list) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    uso = "uso: python fechar-onda.py <documentos> <onda> <id> [<id> ...] [--repo PASTA]"
    repo_arg, soltos, i = None, [], 0
    while i < len(args):
        if args[i] == "--repo" and i + 1 < len(args):
            repo_arg, i = args[i + 1], i + 2
        else:
            soltos.append(args[i])
            i += 1
    if len(soltos) < 3 or not soltos[1].isdigit():
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
    indice = ondas.ler_indice(indice_arq.read_text(encoding="utf-8"))
    no_indice = {t["id"] for t in indice}
    fora = [tid for tid in ids if tid not in no_indice]
    ids_indice = [tid for tid in ids if tid in no_indice]
    problemas, linhas = [], []

    state = pasta / "state.md"
    travados_arq = pasta / "testes-travados.txt"
    sha = sha_travado(state.read_text(encoding="utf-8")) if state.exists() else None
    if sha and travados_arq.exists():
        try:
            mudados = _git(repo, "diff", "--name-only", sha).splitlines()
            mudados += _git(repo, "ls-files", "--others", "--exclude-standard").splitlines()
        except RuntimeError as erro:
            print(f"erro: {erro}")
            return 2
        livres = aprovados(indice, ids_indice)
        travados = [l.split("#", 1)[0].strip() for l in travados_arq.read_text(encoding="utf-8").splitlines()]
        quebrados = travados_mudados(mudados, travados, livres)
        if quebrados:
            problemas.append(f"trava: {len(quebrados)} teste(s) travado(s) mudaram desde {sha} sem estar em "
                             f"testes_alterados dos tickets da onda: {', '.join(quebrados[:10])}"
                             + (" ..." if len(quebrados) > 10 else ""))
        else:
            usados = sorted(livres & {_normal(m) for m in mudados})
            linhas.append(f"trava: ok desde {sha}" + (f" ({len(usados)} liberado(s) pelo plano)" if usados else ""))
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

    arquivo, onda = onda_do_plano(pasta, numero)
    if onda is not None:
        sem_fechar = [t["id"] for t in onda.get("tickets", []) if t.get("id") not in ids
                      and t.get("id") not in ondas.ler_ids((pasta / "feitos.txt").read_text(encoding="utf-8")
                                                          if (pasta / "feitos.txt").exists() else "")]
        if sem_fechar:
            linhas.append(f"aviso: da onda {numero} ({arquivo}) sem fechar: {', '.join(sem_fechar)}")
    if fora:
        linhas.append(f"fora do índice (não vão para feitos.txt): {', '.join(fora)}")

    if problemas:
        for p in problemas:
            print(f"erro: {p}")
        print(f"Onda {numero} não fechada: nada gravado. Resolva e rode de novo.")
        return 1

    feitos_arq = pasta / "feitos.txt"
    if not feitos_arq.exists() and numero > 1:
        print(f"erro: {feitos_arq} não existe e esta é a onda {numero}. Crie-o antes com os ids que as "
              "ondas anteriores fecharam (um por linha): um feitos.txt só com esta onda faria o "
              "ondas.py --feitos trazer de volta tudo o que já foi feito. Nada gravado.")
        return 2
    texto = feitos_arq.read_text(encoding="utf-8") if feitos_arq.exists() else ""
    novo, acrescentados = acrescentar(texto, ids_indice)
    if acrescentados:
        with feitos_arq.open("w", encoding="utf-8", newline="\n") as saida:
            saida.write(novo)
    total = len(set(ondas.ler_ids(novo)))
    print(f"onda {numero} fechada: {', '.join(ids) or 'nenhum id'} "
          f"(feitos.txt: {len(acrescentados)} novo(s), {total} no total)")
    for linha in linhas:
        print(linha)
    arquivo, proxima = onda_do_plano(pasta, numero + 1)
    if proxima is None:
        print(f"próxima: a onda {numero + 1} não está no plano. Fim do mapa, ou replaneje com ondas.py --feitos")
    else:
        tickets = ", ".join(f"{t.get('id')} {t.get('model', '?')}" for t in proxima.get("tickets", []))
        print(f"próxima: onda {numero + 1} ({arquivo}, suite {proxima.get('suite', '?')}): {tickets}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
