"""Move os artefatos de uma rodada encerrada para <documentos>/<fase>."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ARTEFATOS = {
    "state.md", "qa.json", "risks.yaml", "sondagens.md", "tickets.yaml",
    "tickets", "classificacao.json", "agent-map.json", "ondas-replano.json",
    "feitos.txt", "regras-implementacao.md", "plano-de-teste.yaml",
    "testes-travados.txt", "testes-intermitentes.txt", "test-report.md",
    "security", "code-review-report.md", "impacto.md", "pipeline-report.md",
    "runs.log", "model-log.md", "runs-faixa.jsonl", "runs-orquestrador.jsonl",
}
PERSISTENTES = {
    ".git", ".gitignore", "projeto.json", "spec.md", "design",
    "docs-sistema.yaml", "mapa-codigo.md", "historico.md",
}
PADROES = re.compile(
    r"reconhecimento-.+\.md|runs-(?:faixa|orquestrador)\.[A-Za-z0-9_-]+\.jsonl"
)


def arquivar(pasta: Path, fase: str, extras: list[str]) -> list[str]:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", fase) or fase in ARTEFATOS | PERSISTENTES:
        raise ValueError(f"nome de fase inválido: {fase}")
    nomes = ARTEFATOS | set(extras)
    for nome in extras:
        if not re.fullmatch(r"[a-zA-Z0-9_-]+(?:\.[a-zA-Z0-9_-]+)+", nome) or nome.lower() in PERSISTENTES:
            raise ValueError(f"nome de artefato adicional inválido: {nome}")
    destino = pasta / fase
    if destino.exists() or destino.is_symlink():
        raise FileExistsError(f"a pasta da fase já existe: {destino}")
    fontes = sorted(
        p for p in pasta.iterdir()
        if p.name in nomes or PADROES.fullmatch(p.name)
    )
    if not fontes:
        raise ValueError("nenhum artefato de rodada na pasta de documentos")

    destino.mkdir()
    movidos = []
    try:
        for fonte in fontes:
            fonte.rename(destino / fonte.name)
            movidos.append(fonte)
    except OSError:
        for fonte in reversed(movidos):
            (destino / fonte.name).rename(fonte)
        destino.rmdir()
        raise
    return [fonte.name for fonte in movidos]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("documentos", type=Path)
    parser.add_argument("fase")
    parser.add_argument("--extra", action="append", default=[], metavar="ARQUIVO")
    args = parser.parse_args()
    try:
        arquivos = arquivar(args.documentos, args.fase, args.extra)
    except (OSError, ValueError) as erro:
        print(f"erro: {erro}", file=sys.stderr)
        return 1
    print(f"Fase {args.fase} arquivada: {len(arquivos)} artefato(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
