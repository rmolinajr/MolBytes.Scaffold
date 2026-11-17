"""Resolve e valida o modelo de uma delegação do molbytes.scaffold no Codex."""

from __future__ import annotations

import argparse
import json
import sys


MODELOS_PADRAO = {
    "leve": "gpt-6-luna",
    "medio": "gpt-6.1-sol",
    "forte": "gpt-6-astra",
}
ORDEM = {"leve": 0, "medio": 1, "forte": 2}
NIVEIS_POR_AGENTE = {
    "scaffold-architect": {"medio", "forte"},
    "scaffold-designer": {"medio"},
    "scaffold-planner": {"medio"},
    "scaffold-router": {"leve"},
    "scaffold-implementer": {"leve", "medio", "forte"},
    "scaffold-tester": {"medio"},
    "scaffold-security": {"medio", "forte"},
    "scaffold-reviewer": {"medio", "forte"},
}


def modelos_configurados(valor: str | None) -> dict[str, str]:
    if not valor:
        return dict(MODELOS_PADRAO)
    modelos: dict[str, str] = {}
    for item in valor.split(","):
        nivel, separador, modelo = item.strip().partition("=")
        if not separador or nivel not in ORDEM or not modelo.strip():
            raise ValueError(
                "--modelos deve usar leve=<modelo>,medio=<modelo>,forte=<modelo>"
            )
        modelos[nivel] = modelo.strip()
    ausentes = set(ORDEM) - set(modelos)
    if ausentes:
        raise ValueError("faltam níveis em --modelos: " + ", ".join(sorted(ausentes)))
    return modelos


def verificar(
    agente: str,
    nivel: str,
    tarefa: str,
    minimo: str | None,
    modelos: dict[str, str],
) -> dict[str, str]:
    if agente not in NIVEIS_POR_AGENTE:
        raise ValueError(f"agente desconhecido: {agente}")
    if nivel not in ORDEM:
        raise ValueError(f"nível desconhecido: {nivel}")
    if nivel not in NIVEIS_POR_AGENTE[agente]:
        permitidos = ", ".join(sorted(NIVEIS_POR_AGENTE[agente], key=ORDEM.get))
        raise ValueError(f"{agente} não aceita nível {nivel}; use: {permitidos}")
    if minimo and ORDEM[nivel] < ORDEM[minimo]:
        raise ValueError(f"a tarefa exige no mínimo {minimo}; recebido: {nivel}")
    return {
        "tarefa": tarefa,
        "agente": agente,
        "nivel": nivel,
        "modelo": modelos[nivel],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida o nível e resolve o modelo antes de lançar um subagente no Codex."
    )
    parser.add_argument("--agente", required=True, choices=sorted(NIVEIS_POR_AGENTE))
    parser.add_argument("--nivel", required=True, choices=sorted(ORDEM, key=ORDEM.get))
    parser.add_argument("--tarefa", required=True)
    parser.add_argument("--minimo", choices=sorted(ORDEM, key=ORDEM.get))
    parser.add_argument(
        "--modelos",
        help="Mapa alternativo: leve=<modelo>,medio=<modelo>,forte=<modelo>",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        resultado = verificar(
            args.agente,
            args.nivel,
            args.tarefa,
            args.minimo,
            modelos_configurados(args.modelos),
        )
    except ValueError as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(resultado, ensure_ascii=False))
    else:
        print(
            f"MODELO OK | {resultado['tarefa']} | {resultado['agente']} | "
            f"{resultado['nivel']} | {resultado['modelo']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
