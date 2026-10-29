# MolBytes.Scaffold

[English](README.md) · **Português (Brasil)**

![MolBytes Scaffold](assets/cover.png)

> Por [MolBytes](https://www.molbytes.io) · criado por Roberto Molina · [página do projeto](https://www.molbytes.io/projetos/molbytes-scaffold)

![versão](https://img.shields.io/badge/versão-0.19.1-blue)
![licença](https://img.shields.io/badge/licença-MIT-green)
![feito para](https://img.shields.io/badge/feito%20para-Claude%20Code%20·%20Codex%20·%20Gemini%20CLI%20·%20Cursor-d97757)

Skill para o [Claude Code](https://claude.com/claude-code), o Codex, o Gemini
CLI e o Cursor que leva um projeto de software da ideia ao código testado,
auditado e revisado, em 11 estágios.

Uma sessão principal atua como **orquestrador**: conversa com você, delega cada
estágio a um subagente especializado com o nível de modelo certo (leve, médio
ou forte; no Claude Code, haiku, sonnet ou opus),
confere o resultado e faz commit. Ela mesma não escreve código de produção.

## Pipeline

| # | Estágio | Subagente | Saída | Pausa para você |
|---|---------|-----------|-------|-----------------|
| 1 | grill-me | sessão principal | `.project/qa.json` | conversa |
| 2 | spec + modelo de ameaças | `scaffold-architect` | `.project/spec.md` | **aprovar spec** |
| 3 | riscos, dívida técnica, requisitos de segurança | `scaffold-architect` | `.project/risks.yaml` | — |
| 4 | design | `scaffold-designer` | `.project/design/` | — |
| 5 | tickets | `scaffold-planner` | `.project/tickets.yaml` | — |
| 6 | roteamento de modelos e ondas | `scaffold-router` + `scripts/ondas.py` | `.project/agent-map.json` | **aprovar plano e custo** |
| 7 | implementação paralela por ondas | `scaffold-implementer` | código | — |
| 8 | plano de teste → executar → corrigir falhas | `scaffold-tester` + `scaffold-implementer` | `.project/plano-de-teste.yaml` + testes | se a correção falhar 2x |
| 9 | segurança: audit → triage → fix → verify | `scaffold-security` + `scaffold-implementer` | `.project/security/` | achados médios |
| 10 | code review | `scaffold-reviewer` | `.project/code-review-report.md` | **decidir correções** |
| 11 | testes finais + rescan + gate | `scaffold-tester` + `scaffold-security` | `.project/pipeline-report.md` | se bloquear |

## Destaques

- **Retomável:** `state.md` + git são a fonte da verdade. Nos pontos de
  pausa, `/clear` e `/molbytes:molbytes-scaffold continuar` (o mesmo comando
  serve numa sessão nova); depois de `/compact`, só `continuar`.
- **Extensível:** uma skill de extensão acrescenta regras por stack, domínio
  ou compliance sem mudar o pipeline; o contrato está em
  `references/extensoes.md`.
- **Alteração de sistema existente:** a skill procura a documentação do
  sistema (no projeto ou fora) e a atualiza junto com o código; sem
  documentação, só altera o sistema. Mudança pequena sai mais barata: riscos
  só do que muda e design pulado quando não há tela nova.
- **Mapa do código:** `.project/mapa-codigo.md` diz onde fica cada coisa
  (estrutura, pontos de entrada, módulos, contratos, comandos), com o commit
  que descreve. É atualizado pelo diff e conferido no gate: a rodada nova
  parte do mapa em vez de redescobrir o código.
- **Histórico das rodadas:** `.project/historico.md` guarda uma entrada curta
  por rodada (pedido, commits, áreas, decisões, o que ficou de fora) e as
  mudanças feitas fora do pipeline: "quando e por que isso mudou?" tem
  resposta sem abrir fase por fase.
- **Documentos fora do projeto, se quiser:** spec, design e relatórios ficam em
  `.project/` ou numa pasta separada com git próprio, para não sujar o projeto
  do cliente. Ver [INSTALL.pt-BR.md](INSTALL.pt-BR.md#onde-ficam-os-documentos).
- **Paralelismo sem conflito:** tickets da mesma onda nunca tocam os mesmos
  arquivos; um ticket `INFRA-000` prepara estrutura, testes e dependências antes
  de tudo. As ondas saem de um script (`scripts/ondas.py`), não do modelo: ele
  confere dependências, conflitos de arquivo e tickets faltando ou inventados.
- **Roteamento de modelo por ticket:** pagamentos, auth, sync offline e
  concorrência vão para o nível forte; config e CRUD trivial para o leve; o
  resto para o médio. Cada plataforma traduz o nível para um modelo dela.
  Quando os testes falham, tenta de novo no mesmo modelo e depois sobe um
  nível.
- **Segurança em duas pontas:** modelo de ameaças e requisitos testáveis antes
  do código; gitleaks, semgrep e trivy (via Docker) + revisão OWASP depois. Toda
  correção começa por um teste que reproduz a falha e é verificada por outro
  agente.
- **Watchdog:** limite de turnos por subagente (onde a plataforma tem), orçamento de tempo em
  `.project/runs.log`, comando `status` a qualquer momento (os
  implementadores rodam em segundo plano).
- **Sessão principal leve:** ela só orquestra. Toda correção (teste,
  segurança, review, merge) vai para um implementador com um ticket de
  correção, e os testes e o rescan do estágio 11 rodam em subagentes.
- **Plano de teste com correção:** cada requisito vira item de um plano de
  teste; o que falha é corrigido no código (sem afrouxar o teste) e testado de
  novo; testes manuais vão como lista no relatório.
- **Sem números inventados:** relatórios só com o que testes e ferramentas
  mostraram.

## Uso rápido

Instale como plugin no Claude Code:

```
/plugin marketplace add rmolinajr/MolBytes.Scaffold
/plugin install molbytes@molbytes
```

E rode, com o Claude Code aberto na pasta do projeto:

```
/molbytes:molbytes-scaffold Sistema PDV para restaurante: terminal, cozinha, admin, offline-first, Stripe e PIX
```

Copiada à mão para `~/.claude/skills/` (sem plugin), o comando é só
`/molbytes-scaffold`.

### Exemplos

Projeto novo, do grill-me ao gate:

```
/molbytes:molbytes-scaffold Agenda para clínicas: agendamento online, lembrete por WhatsApp, painel do médico
```

Alterar um sistema que já existe (abra o Claude Code na pasta dele):

```
/molbytes:molbytes-scaffold Alteração: aceitar PIX no checkout
```

Só até os tickets, para revisar o plano antes de gastar com implementação:

```
/molbytes:molbytes-scaffold Agenda para clínicas: agendamento online e lembretes --ate tickets
```

API sem interface, pulando o design e com o roteamento econômico:

```
/molbytes:molbytes-scaffold API de cotação de frete para lojas virtuais --sem-design --economico
```

Retomar em outro dia, numa sessão nova:

```
/molbytes:molbytes-scaffold continuar
```

### Flags

| Flag | O que faz |
|---|---|
| `--ate <estágio>` | Para depois do estágio indicado, pelo número ou pelo nome (`--ate 5`, `--ate tickets`). |
| `--sem-design` | Pula o estágio 4; tickets e testes usam a spec no lugar do design. |
| `--economico` | Usa a coluna "econômico" do roteamento de modelos. |

### Durante o pipeline

Digite na conversa:

| Comando | O que faz |
|---|---|
| `status` | Tabela dos subagentes rodando (ticket, modelo, tempo, orçamento) e o estágio ou a onda atual. |
| `continuar` | Depois de `/compact`: relê o `state.md` e segue do próximo passo. Depois de `/clear` (mais barato), use `/molbytes:molbytes-scaffold continuar`. |
| `aprovado`, ou o que mudar | Resposta às pausas: spec (estágio 2), plano e custo (6) e code review (10). |

Recomendados do Claude Code: `/model sonnet` na sessão principal (os
estágios pesados já usam opus nos subagentes) e, nos pontos que a skill avisa
(fim dos estágios 2, 5, 8 e 9 e de cada onda do 7), `/clear` seguido de
`/molbytes:molbytes-scaffold continuar`: a sessão recomeça leve, pelo
`state.md`. `/compact` também serve, mas custa mais.

### Outras plataformas

| Plataforma | Instalar | Rodar |
|---|---|---|
| Codex | copiar a skill e `adapters/codex/agents/` | `$molbytes-scaffold <descrição>` |
| Gemini CLI | `gemini extensions install ./MolBytes.Scaffold/adapters/gemini-cli` | `/molbytes-scaffold <descrição>` |
| Cursor | plugin pela URL do repositório, ou cópia manual | `/molbytes-scaffold <descrição>` |

Os adaptadores são novos na v0.14.0 e ainda não rodaram um projeto real
nessas plataformas. Passo a passo em [INSTALL.pt-BR.md](INSTALL.pt-BR.md).

Outras formas de instalar e pré-requisitos (Docker): [INSTALL.pt-BR.md](INSTALL.pt-BR.md). Histórico: [CHANGELOG.md](CHANGELOG.md).

## Estrutura

```
.claude-plugin/
  plugin.json                   # manifesto do plugin (autor, versão, licença)
  marketplace.json              # permite instalar com /plugin
.codex-plugin/plugin.json       # plugin do Codex (gerado)
.cursor-plugin/                 # plugin e marketplace do Cursor (gerados)
skills/molbytes-scaffold/
  SKILL.md                      # orquestrador
  references/
    stages.md                   # instruções de cada estágio
    model-routing.md            # qual modelo em cada estágio/ticket
    security.md                 # ameaças, código seguro, auditoria, rescan
    watchdog.md                 # limites, orçamento de tempo, reexecução
    state-template.md           # modelo do .project/state.md
    documentos.md               # pasta de documentos: interna ou externa
    alteracao.md                # alteração de sistema existente e sua documentação
    mapa-codigo.md              # mapa do código: onde fica cada coisa, em dia pelo diff
    historico.md                # histórico das rodadas: quando e por que o sistema mudou
    plano-de-teste.md           # plano de teste, execução, correção automática
    extensoes.md                # contrato das skills de extensão
    plataformas.md              # Claude Code, Codex, Gemini CLI, Cursor: níveis e comandos
agents/
  scaffold-*.md                 # 8 subagentes (formato Claude Code, fonte dos adaptadores)
adapters/
  build.py                      # gera os adaptadores a partir de skills/ e agents/
  codex/agents/                 # subagentes em TOML
  gemini-cli/                   # extensão: skill, comando e um subagente por nível
  cursor/agents/                # subagentes com model: inherit
```

Depois de mudar `skills/`, `agents/` ou a versão em `.claude-plugin/plugin.json`,
rode `python adapters/build.py`; `python adapters/build.py --check` falha se
algum adaptador estiver desatualizado.

## Status

v0.19.1, em evolução: os ajustes da v0.10 em diante vieram de execuções reais
no Claude Code, a mais recente (v0.17.0) alterando um sistema existente. O
mapa do código (v0.18.0) e o histórico das rodadas (v0.19.0) ainda não
rodaram num projeto real, nem os adaptadores de Codex, Gemini CLI e Cursor.
Não substitui um pentest profissional antes de processar pagamentos reais.

## Autor

Criado por **Roberto Molina**, fundador da **MolBytes**.

- Site: [www.molbytes.io](https://www.molbytes.io)
- Página do projeto: [molbytes.io/projetos/molbytes-scaffold](https://www.molbytes.io/projetos/molbytes-scaffold)

## Suporte e contato

Dúvidas, sugestões ou uso em empresa: fale com a MolBytes pelo site
[www.molbytes.io](https://www.molbytes.io).

## Licença

[MIT](LICENSE) — livre para usar, modificar e distribuir, mantendo o aviso de
copyright da MolBytes.
