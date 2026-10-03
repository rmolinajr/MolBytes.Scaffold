# MolBytes.Scaffold

Skill para o [Claude Code](https://claude.com/claude-code) que leva um projeto
de software da ideia ao código testado, auditado e revisado, em 11 estágios.

Uma sessão principal atua como **orquestrador**: conversa com você, delega cada
estágio a um subagente especializado com o modelo certo (haiku, sonnet ou opus),
confere o resultado e faz commit. Ela mesma não escreve código de produção.

## Pipeline

| # | Estágio | Subagente | Saída | Pausa para você |
|---|---------|-----------|-------|-----------------|
| 1 | grill-me | sessão principal | `.project/qa.json` | conversa |
| 2 | spec + modelo de ameaças | `scaffold-architect` | `.project/spec.md` | **aprovar spec** |
| 3 | riscos, dívida técnica, requisitos de segurança | `scaffold-architect` | `.project/risks.yaml` | — |
| 4 | design | `scaffold-designer` | `.project/design/` | — |
| 5 | tickets | `scaffold-planner` | `.project/tickets.yaml` | — |
| 6 | roteamento de modelos e ondas | `scaffold-router` | `.project/agent-map.json` | **aprovar plano e custo** |
| 7 | implementação paralela por ondas | `scaffold-implementer` | código | — |
| 8 | testes de integração | `scaffold-tester` | `tests/integration/` | — |
| 9 | segurança: audit → triage → fix → verify | `scaffold-security` + `scaffold-implementer` | `.project/security/` | achados médios |
| 10 | code review | `scaffold-reviewer` | `.project/code-review-report.md` | **decidir correções** |
| 11 | testes finais + rescan + gate | sessão principal | `.project/pipeline-report.md` | se bloquear |

## Destaques

- **Retomável:** `.project/state.md` + git são a fonte da verdade. Depois de
  `/compact` ou numa sessão nova, digite `continuar`.
- **Paralelismo sem conflito:** tickets da mesma onda nunca tocam os mesmos
  arquivos; um ticket `INFRA-000` prepara estrutura, testes e dependências antes
  de tudo.
- **Roteamento de modelo por ticket:** pagamentos, auth, sync offline e
  concorrência vão para opus; config e CRUD trivial para haiku; o resto sonnet.
  Escala automaticamente quando os testes falham.
- **Segurança em duas pontas:** modelo de ameaças e requisitos testáveis antes
  do código; gitleaks, semgrep e trivy (via Docker) + revisão OWASP depois. Toda
  correção começa por um teste que reproduz a falha e é verificada por outro
  agente.
- **Watchdog:** `maxTurns` por subagente, orçamento de tempo em
  `.project/runs.log`, comando `status` a qualquer momento.
- **Sem números inventados:** relatórios só com o que testes e ferramentas
  mostraram.

## Uso rápido

```
/molbytes-scaffold Sistema PDV para restaurante: terminal, cozinha, admin, offline-first, Stripe e PIX
```

Flags no texto do pedido: `--ate <estágio>`, `--sem-design`, `--economico`.

Instalação, pré-requisitos (Docker) e histórico de versões: [INSTALL.md](INSTALL.md).

## Estrutura

```
.claude/
  skills/molbytes-scaffold/
    SKILL.md                    # orquestrador
    references/
      stages.md                 # instruções de cada estágio
      model-routing.md          # qual modelo em cada estágio/ticket
      security.md               # ameaças, código seguro, auditoria, rescan
      watchdog.md               # limites, orçamento de tempo, reexecução
      state-template.md         # modelo do .project/state.md
  agents/
    scaffold-*.md               # 8 subagentes
```

## Status

v0.5, ainda não validada numa execução completa. Não substitui um pentest
profissional antes de processar pagamentos reais.
