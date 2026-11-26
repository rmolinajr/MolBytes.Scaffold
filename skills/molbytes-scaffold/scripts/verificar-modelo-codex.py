"""Resolve e valida o modelo de uma delegação do molbytes.scaffold no Codex."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


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
        if not separador or nivel not in ORDEM or nivel in modelos or not modelo.strip():
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
    *,
    estagio: int,
) -> dict[str, str]:
    if type(estagio) is not int or not 1 <= estagio <= 11:
        raise ValueError("estágio deve ser um inteiro de 1 a 11")
    if not tarefa.strip():
        raise ValueError("tarefa vazia")
    if agente not in NIVEIS_POR_AGENTE:
        raise ValueError(f"agente desconhecido: {agente}")
    if nivel not in ORDEM:
        raise ValueError(f"nível desconhecido: {nivel}")
    if nivel not in NIVEIS_POR_AGENTE[agente]:
        permitidos = ", ".join(sorted(NIVEIS_POR_AGENTE[agente], key=ORDEM.get))
        raise ValueError(f"{agente} não aceita nível {nivel}; use: {permitidos}")
    if minimo is not None and minimo not in ORDEM:
        raise ValueError(f"nível mínimo desconhecido: {minimo}")
    if estagio == 9:
        minimo = "forte"
    if minimo and ORDEM[nivel] < ORDEM[minimo]:
        raise ValueError(f"a tarefa exige no mínimo {minimo}; recebido: {nivel}")
    return {
        "tarefa": tarefa,
        "agente": agente,
        "nivel": nivel,
        "modelo": modelos[nivel],
    }


def verificar_lote(tarefas, modelos, disponiveis=None):
    if not isinstance(tarefas, list) or not tarefas:
        raise ValueError("informe uma lista de tarefas não vazia")
    resultados = []
    for i, item in enumerate(tarefas, 1):
        try:
            resultado = verificar(
                item["agente"], item["nivel"], item["tarefa"],
                item.get("minimo"), modelos, estagio=item["estagio"],
            )
            resultado["motivo"] = item.get("motivo", "")
            resultado["disponibilidade"] = "confirmada" if disponiveis is not None else "não verificada"
            resultados.append(resultado)
        except (KeyError, TypeError, AttributeError, ValueError) as erro:
            raise ValueError(f"tarefa {i}: {erro}") from erro
    if disponiveis is not None:
        ausentes = {resultado["modelo"] for resultado in resultados} - disponiveis
        if ausentes:
            raise ValueError("modelos ausentes no Codex: " + ", ".join(sorted(ausentes)))
    return resultados


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida o nível e resolve o modelo antes de lançar um subagente no Codex."
    )
    parser.add_argument("--lote", help="Arquivo JSON com tarefas ou - para ler da entrada padrão")
    parser.add_argument("--agente", choices=sorted(NIVEIS_POR_AGENTE))
    parser.add_argument("--nivel", choices=sorted(ORDEM, key=ORDEM.get))
    parser.add_argument("--tarefa")
    parser.add_argument("--estagio", type=int)
    parser.add_argument("--motivo")
    parser.add_argument("--minimo", choices=sorted(ORDEM, key=ORDEM.get))
    parser.add_argument(
        "--modelos",
        help="Mapa alternativo: leve=<modelo>,medio=<modelo>,forte=<modelo>",
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--disponiveis", help="IDs separados por vírgula, obtidos do ambiente Codex")
    args = parser.parse_args()
    try:
        modelos = modelos_configurados(args.modelos)
        disponiveis = (
            {item.strip() for item in args.disponiveis.split(",") if item.strip()}
            if args.disponiveis is not None else None
        )
        campos = {
            chave: getattr(args, chave)
            for chave in ("agente", "nivel", "tarefa", "estagio", "minimo", "motivo")
        }
        if args.lote:
            if any(valor is not None for valor in campos.values()):
                raise ValueError("--lote deve ser usado sem os campos da tarefa individual")
            tarefas = json.loads(sys.stdin.read() if args.lote == "-" else Path(args.lote).read_text(encoding="utf-8-sig"))
        else:
            if any(campos[chave] is None for chave in ("agente", "nivel", "tarefa", "estagio")):
                raise ValueError("informe --agente, --nivel, --tarefa e --estagio, ou use --lote")
            tarefas = [campos]
        resultados = verificar_lote(tarefas, modelos, disponiveis)
    except (ValueError, OSError) as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        return 2
    if args.json or args.lote:
        print(json.dumps(resultados if args.lote else resultados[0], ensure_ascii=True))
    else:
        resultado = resultados[0]
        print(
            f"ROTA OK | {resultado['tarefa']} | {resultado['agente']} | "
            f"{resultado['nivel']} | {resultado['modelo']} | "
            f"disponibilidade: {resultado['disponibilidade']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
