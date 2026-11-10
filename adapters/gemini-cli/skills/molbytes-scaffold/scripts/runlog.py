"""Grava o `.project/runs.log` do watchdog (molbytes.scaffold).

O orquestrador não escreve a linha à mão: numa execução real, a coluna de
minutos passou a receber turnos, o status ganhou frases livres e linhas
perderam a data, e o que lê o log (o `status`, a calibração do roteamento)
passou a contar errado. O script carimba a hora, calcula os minutos pelo
relógio e só aceita os status da lista. Só biblioteca padrão do Python 3.8+.

    python runlog.py <documentos> start <agente> <ticket> <nível>/<modelo> <orçamento min>
    python runlog.py <documentos> end <agente> <ticket> <ok|parcial|travado|falhou> [--tokens N] [--turnos N] [--nota TEXTO]
    python runlog.py <documentos> abertos

Formato (watchdog.md):

    <início ISO> | START | <agente> | <ticket ou estágio> | <nível>/<modelo> | orçamento <min>
    <fim ISO> | END | <agente> | <ticket ou estágio> | ok|parcial|travado|falhou | <min reais> | <tokens> tokens | <nota>

`end` fecha o START aberto mais recente do mesmo agente e ticket; sem START
aberto, não grava nada e sai com código 1. A nota (turnos, motivo do parcial)
fica no último campo, nunca no status nem nos minutos. `abertos` lista os
START sem END com o tempo decorrido e o orçamento (o comando `status`).
"""
from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

STATUS = ("ok", "parcial", "travado", "falhou")
SEP = " | "


def agora() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _data(texto: str) -> datetime | None:
    try:
        quando = datetime.fromisoformat(texto.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return quando if quando.tzinfo else quando.replace(tzinfo=timezone.utc)


def _limpo(texto: str) -> str:
    """Um campo não pode ter `|` nem quebra de linha: viraria outro campo."""
    return re.sub(r"\s+", " ", texto.replace("|", "/")).strip()


def ler(texto: str) -> list:
    """Linhas do log como dicionários: tipo, quando, agente, ticket e os campos seguintes."""
    linhas = []
    for numero, linha in enumerate(texto.splitlines(), 1):
        partes = [p.strip() for p in linha.split("|")]
        if len(partes) < 5 or partes[1] not in ("START", "END"):
            continue
        linhas.append({"linha": numero, "tipo": partes[1], "quando": _data(partes[0]),
                       "agente": partes[2], "ticket": partes[3], "resto": partes[4:]})
    return linhas


def abertos(texto: str) -> list:
    """START sem END, na ordem do log. Um END fecha o START aberto mais recente do mesmo agente e ticket."""
    pilha = []
    for item in ler(texto):
        if item["tipo"] == "START":
            pilha.append(item)
            continue
        for i in range(len(pilha) - 1, -1, -1):
            if pilha[i]["agente"] == item["agente"] and pilha[i]["ticket"] == item["ticket"]:
                del pilha[i]
                break
    return pilha


def linha_start(quando: datetime, agente: str, ticket: str, nivel: str, orcamento: str) -> str:
    if not re.fullmatch(r"\d+", orcamento.strip()):
        raise ValueError(f"orçamento deve ser um número de minutos, não {orcamento!r}")
    if "/" not in nivel:
        raise ValueError(f"nível deve vir como <nível>/<modelo> (ex.: medio/sonnet), não {nivel!r}")
    campos = [quando.isoformat(), "START", _limpo(agente), _limpo(ticket), _limpo(nivel), f"orçamento {orcamento.strip()}"]
    return SEP.join(campos)


def linha_end(texto: str, quando: datetime, agente: str, ticket: str, status: str,
              tokens: str | None = None, turnos: str | None = None, nota: str | None = None) -> str:
    status = status.strip().lower()
    if status not in STATUS:
        raise ValueError(f"status {status!r} fora da lista: {', '.join(STATUS)} (o resto vai em --nota)")
    agente, ticket = _limpo(agente), _limpo(ticket)
    aberto = next((s for s in reversed(abertos(texto)) if s["agente"] == agente and s["ticket"] == ticket), None)
    if aberto is None:
        raise LookupError(f"nenhum START aberto de {agente} / {ticket} no runs.log")
    if aberto["quando"] is None:
        raise LookupError(f"o START da linha {aberto['linha']} não tem data legível")
    minutos = max(0, round((quando - aberto["quando"]).total_seconds() / 60))
    if tokens is not None and not re.fullmatch(r"\d+", tokens.strip()):
        raise ValueError(f"tokens deve ser um número, não {tokens!r}")
    extra = "; ".join(x for x in [f"turnos {turnos.strip()}" if turnos else "", _limpo(nota or "")] if x)
    campos = [quando.isoformat(), "END", agente, ticket, status, str(minutos), f"{tokens.strip() if tokens else '?'} tokens"]
    if extra:
        campos.append(extra)
    return SEP.join(campos)


def _opcoes(args: list, nomes: tuple) -> tuple:
    valores, soltos, i = {n: None for n in nomes}, [], 0
    while i < len(args):
        if args[i] in valores and i + 1 < len(args):
            valores[args[i]] = args[i + 1]
            i += 2
        else:
            soltos.append(args[i])
            i += 1
    return valores, soltos


def main(args: list) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    uso = "\n".join(l.strip() for l in __doc__.splitlines() if l.strip().startswith("python runlog.py"))
    if len(args) < 2:
        print(uso)
        return 2
    pasta, comando, resto = Path(args[0]), args[1], args[2:]
    arquivo = pasta / "runs.log"
    texto = arquivo.read_text(encoding="utf-8") if arquivo.exists() else ""
    try:
        if comando == "start" and len(resto) == 4:
            nova = linha_start(agora(), *resto)
        elif comando == "end":
            opcoes, soltos = _opcoes(resto, ("--tokens", "--turnos", "--nota"))
            if len(soltos) != 3:
                print(uso)
                return 2
            nova = linha_end(texto, agora(), *soltos, tokens=opcoes["--tokens"],
                             turnos=opcoes["--turnos"], nota=opcoes["--nota"])
        elif comando == "abertos" and not resto:
            momento = agora()
            for s in abertos(texto):
                passou = "?" if s["quando"] is None else str(round((momento - s["quando"]).total_seconds() / 60))
                orcamento = next((re.sub(r"\D", "", c) for c in s["resto"] if "orçamento" in c or "orcamento" in c), "?")
                print(f"{s['ticket']} | {s['agente']} | {s['resto'][0] if s['resto'] else '?'} | {passou} min | orçamento {orcamento or '?'}")
            return 0
        else:
            print(uso)
            return 2
    except (ValueError, LookupError) as erro:
        print(f"erro: {erro}. Nada gravado.")
        return 1
    pasta.mkdir(parents=True, exist_ok=True)
    separador = "" if not texto or texto.endswith("\n") else "\n"
    with arquivo.open("a", encoding="utf-8", newline="\n") as saida:
        saida.write(f"{separador}{nova}\n")
    print(nova)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
