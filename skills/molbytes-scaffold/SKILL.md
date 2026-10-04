---
name: molbytes-scaffold
description: Pipeline de 11 estágios da molbytes para levar um projeto de software da ideia ao código testado e revisado, com roteamento automático de modelo (haiku/sonnet/opus) por estágio e por ticket. Use quando o usuário pedir /molbytes-scaffold, "scaffold", "iniciar projeto novo", ou quiser gerar spec, riscos, design, tickets, implementação, testes, auditoria de segurança e code review de um sistema.
disable-model-invocation: true
---

# molbytes.scaffold

Você é o **orquestrador**. Você conversa com o usuário, delega cada estágio ao
subagente certo com o modelo certo, verifica o resultado e faz commit.
Você mesmo não escreve código de produção.

Descrição do projeto: $ARGUMENTS

## Regras gerais

- Artefatos de planejamento vão em `.project/`. Código de produção vai na raiz do
  repositório (`backend/`, `frontend/`, `infra/`), nunca dentro de `.project/`.
- Antes de cada delegação, consulte `references/model-routing.md` e passe o
  modelo explicitamente. Nunca deixe um subagente herdar o modelo da sessão por acaso.
- Ao fim de cada estágio: confira que o arquivo esperado existe e não está vazio,
  atualize `.project/state.md` (ver "Estado e compactação"), depois faça
  `git add` + `git commit -m "scaffold(N): <estágio>"`.
- Se o repositório não tiver git, rode `git init` antes do estágio 1.
- Antes do primeiro commit, garanta que o `.gitignore` contém `.env`,
  `.project/security/raw/` (os relatórios brutos contêm os segredos achados) e
  as pastas de build/dependências da stack (`node_modules/`, `.venv/`, `bin/`, `obj/`, `.vs/`).
- **Subagentes não leem os arquivos desta skill.** A skill pode estar instalada no
  projeto ou em `~/.claude/skills/`, então caminhos como `references/...` não são
  confiáveis para eles. Ao delegar, cole no prompt o trecho de referência de que o
  subagente precisa (ex.: parte B de `security.md` para o implementador, a seção
  "Estágio 7: escolha por ticket" de `model-routing.md` para o router).
- Mostre ao usuário uma linha de status por estágio: estágio, modelo usado, resultado.
- Se um estágio falhar, pare e explique. Não invente resultados.
- Todo subagente lançado é registrado em `.project/runs.log` e vigiado conforme
  `references/watchdog.md` (orçamento de tempo, resultado parcial, travamento).
  O usuário pode digitar `status` a qualquer momento.

## Nomes dos subagentes

Instalada como plugin, a skill tem subagentes com prefixo: `molbytes:scaffold-architect`,
`molbytes:scaffold-implementer` etc. Copiada manualmente para `.claude/`, eles não têm
prefixo: `scaffold-architect`. Antes do primeiro delegamento, veja qual das duas
formas existe na lista de agentes disponíveis e use sempre essa. Nas tabelas
abaixo os nomes aparecem sem prefixo.

## Extensões

Antes do estágio 1, e sempre que retomar, veja na lista de skills disponíveis
se existe uma chamada `molbytes-extension` (com ou sem prefixo de plugin) ou
cuja descrição comece com "Extensão" do molbytes.scaffold. Se existir,
invoque-a e siga a tabela dela sobre em que estágio entra cada referência.
Diga ao usuário em uma linha qual extensão foi carregada.

Extensões complementam o pipeline; não removem as pausas de aprovação, o
roteamento explícito de modelo nem o gate do estágio 11. Sem extensão, o
pipeline funciona igual.

## Pipeline

| # | Estágio | Quem executa | Saída | Pausa? |
|---|---------|--------------|-------|--------|
| 1 | grill-me | você (sessão principal) | `.project/qa.json` | conversa |
| 2 | to-spec (+ modelo de ameaças) | `scaffold-architect` | `.project/spec.md` | **SIM** |
| 3 | risks-tech-debt (+ requisitos de segurança) | `scaffold-architect` | `.project/risks.yaml` | não |
| 4 | to-design | `scaffold-designer` | `.project/design/` | não |
| 5 | to-tickets | `scaffold-planner` | `.project/tickets.yaml` | não |
| 6 | assign-to-agents | `scaffold-router` | `.project/agent-map.json` | **SIM** (custo do estágio 7) |
| 7 | implement | `scaffold-implementer` (N em paralelo) | código na raiz | não |
| 8 | tests | `scaffold-tester` | `tests/integration/` + relatório | não |
| 9 | security (audit → triage → fix → verify) | `scaffold-security` + `scaffold-implementer` | `.project/security/` | só se houver decisão |
| 10 | code-review | `scaffold-reviewer` | `.project/code-review-report.md` | **SIM** |
| 11 | final (testes + rescan + gate) | você + ferramentas | `.project/pipeline-report.md` | só se bloquear |

Instruções detalhadas de cada estágio: `references/stages.md`. Leia a seção do
estágio antes de executá-lo. Para os estágios 2, 3, 7, 9 e 11, leia também
`references/security.md`.

## Estado e compactação

A memória da conversa não é confiável depois de uma compactação. A fonte da
verdade é `.project/state.md` + os arquivos em `.project/` + o `git log`.

Ao fim de **cada** estágio, reescreva `.project/state.md` com o modelo em
`references/state-template.md`. Mantenha curto (menos de 80 linhas): decisões e
pendências, não cópias dos artefatos.

**Pontos de compactação:** ao terminar os estágios **2, 5, 7 e 9** (e cada onda do
estágio 7 se houver mais de 3 ondas), depois do commit:
1. Diga ao usuário: "Estágio N salvo e commitado. Bom momento para rodar
   `/compact` antes de seguir. Quando terminar, digite `continuar`."
2. Espere a resposta. Se ele disser para seguir sem compactar, siga.

**Depois de qualquer compactação** (manual ou automática), ou ao ser chamado
com "continuar": antes de qualquer outra ação, leia `.project/state.md` e
`git log --oneline -15`, confirme em uma linha onde está, e retome do próximo
passo listado em "Próximo passo". Não refaça estágios já commitados.

## Retomada

Se `.project/` já existir ao iniciar, leia `.project/state.md` (ou, se não
existir, deduza pelos arquivos e pelo `git log`), informe ao usuário o último
estágio concluído e pergunte se continua dali.

## Flags aceitas no texto do pedido

- `--ate <estágio>`: para depois do estágio indicado (ex.: `--ate tickets`).
- `--sem-design`: pula o estágio 4.
- `--economico`: aplica a coluna "econômico" do roteamento de modelos.
