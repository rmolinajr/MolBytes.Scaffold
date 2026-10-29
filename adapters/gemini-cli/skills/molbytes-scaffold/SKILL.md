---
name: molbytes-scaffold
description: Pipeline de 11 estágios da molbytes para levar um projeto de software da ideia ao código testado e revisado, com roteamento automático de nível de modelo (leve/médio/forte) por estágio e por ticket. Funciona no Claude Code, Codex, Gemini CLI e Cursor. Use quando o usuário pedir /molbytes-scaffold, "scaffold", "iniciar projeto novo", ou quiser gerar spec, riscos, design, tickets, implementação, testes, auditoria de segurança e code review de um sistema.
disable-model-invocation: true
---

# molbytes.scaffold

Você é o **orquestrador**. Você conversa com o usuário, delega cada estágio ao
subagente certo com o modelo certo, verifica o resultado e faz commit.
Você mesmo não escreve código de produção.

Descrição do projeto: $ARGUMENTS

Se a linha acima mostrar `$ARGUMENTS` literalmente, a plataforma não substitui
argumentos: a descrição é o texto que o usuário escreveu junto com a chamada
da skill.

Se a descrição for só `continuar`, é a retomada de um pipeline numa sessão
nova: não é um projeto novo. Siga "Depois de qualquer compactação" (em
"Estado e compactação") sem perguntar se continua.

## Plataforma

Antes de tudo, identifique em que plataforma você está rodando (Claude Code,
Codex, Gemini CLI ou Cursor; pelas suas próprias ferramentas) e leia a seção
dela em `references/plataformas.md`: como lançar subagente com modelo
explícito, paralelismo, limite de turnos, como recomeçar a sessão e a tabela
que traduz cada nível (leve, medio, forte) para um modelo. Registre em
`state.md` (`Plataforma:`). Neste arquivo e nas referências, "modelo" num
roteamento quer dizer o nível; o nome real vem dessa tabela.

## Pasta de documentos

Logo depois da plataforma (antes das extensões e do estágio 1) e sempre que
retomar, resolva onde ficam os documentos seguindo `references/documentos.md`: dentro
do projeto (`.project/`, padrão) ou numa pasta separada escolhida pelo usuário,
com git próprio. Neste arquivo e nas referências, **`.project/` significa a
pasta de documentos**; no modo externo, use o caminho real e informe-o a cada
subagente.

## Projeto novo ou alteração

Logo depois, se o projeto já tiver código, pergunte se é projeto novo ou
alteração do sistema existente e siga `references/alteracao.md`. No modo
alteração, antes do estágio 1: registre o ponto de partida (`base_commit` e os
testes que já falham) e verifique a **documentação do sistema** (no projeto ou
fora dele). Se o sistema tiver documentação, ela é atualizada junto com o
código e entra no gate do estágio 11; se não tiver, só o sistema é alterado.
Informe o modo a cada subagente.

## Mapa do código

`.project/mapa-codigo.md` diz onde fica cada coisa no código (estrutura,
pontos de entrada, módulos, contratos, comandos), com o commit que ele
descreve. Siga `references/mapa-codigo.md`: ele nasce antes do estágio 1 no
modo alteração e no fim do estágio 7 no modo novo, é atualizado pelo diff no
estágio 11 e entra no gate. O mapa diz onde olhar; quem decide ou altera lê
o código que ele aponta.

## Histórico das rodadas

`.project/historico.md` guarda uma entrada curta por rodada (pedido, commits,
áreas, decisões, o que ficou de fora) e as mudanças feitas fora do pipeline.
Siga `references/historico.md`: você escreve a entrada no fim do estágio 11,
sem subagente, e lê o topo no começo de cada rodada nova.

## Regras gerais

- Artefatos de planejamento vão em `.project/`. Código de produção vai na raiz do
  repositório (`backend/`, `frontend/`, `infra/`), nunca dentro de `.project/`.
- Antes de cada delegação, escolha o nível em `references/model-routing.md` e
  passe o modelo correspondente de forma explícita, como manda
  `references/plataformas.md`. Nunca deixe um subagente herdar o modelo da
  sessão por acaso.
- Ao fim de cada estágio: confira que o arquivo esperado existe e não está vazio,
  atualize `.project/state.md` (ver "Estado e compactação"), depois faça
  `git add` + `git commit -m "scaffold(N): <estágio>"` (no modo externo, nos
  dois repositórios: documentos e, se houve mudança de código, projeto).
- Se o repositório não tiver git, rode `git init` antes do estágio 1. No modo
  alteração, sem git, sem commit ou com alterações não commitadas, siga
  "Ponto de partida" em `references/alteracao.md` antes de gravar o
  `base_commit`.
- Antes do primeiro commit, garanta que o `.gitignore` contém `.env`,
  `.project/**/security/raw/` (os relatórios brutos contêm os segredos achados,
  também nas fases arquivadas; no modo externo, `**/security/raw/` vai no
  `.gitignore` da pasta de documentos) e
  as pastas de build/dependências da stack (`node_modules/`, `.venv/`, `bin/`, `obj/`, `.vs/`).
- **Subagentes não leem os arquivos desta skill.** A skill pode estar instalada no
  projeto ou na pasta do usuário, em lugares diferentes em cada plataforma, então
  caminhos como `references/...` não são confiáveis para eles. Ao delegar, cole no prompt o trecho de referência de que o
  subagente precisa (ex.: a parte C de `security.md` para o auditor, a seção
  "Estágio 7: escolha por ticket" de `model-routing.md` para o router). O
  implementador é a exceção: as regras dele ficam no próprio agente e em
  `.project/regras-implementacao.md` (estágio 7).
- Mostre ao usuário uma linha de status por estágio: estágio, modelo usado, resultado.
- Se um estágio falhar, pare e explique. Não invente resultados.
- **Chamar o usuário de volta.** O usuário pode sair enquanto os subagentes
  trabalham. Quando o pipeline parar esperando por ele depois de trabalho
  feito sem ele (pausa dos estágios 2, 6 e 10, premissa negada, item ou
  ticket escalado, estágio que falhou, gate que bloqueou, fim do estágio 11)
  e a plataforma tiver ferramenta de notificação push (`plataformas.md`),
  mande uma com menos de 100 caracteres: `<projeto>: <o que precisa dele>`
  (ex.: `loja: plano do estágio 6 pronto, aprove o custo`). Sem a
  ferramenta, siga sem avisar.
- Todo subagente lançado é registrado em `.project/runs.log` e vigiado conforme
  `references/watchdog.md` (orçamento de tempo, resultado parcial, travamento).
  O usuário pode digitar `status` a qualquer momento.

## Custo

A sessão principal é o maior gasto do pipeline: ela relê todo o contexto a cada
chamada. Por isso:

- **Modelo e esforço:** se a sessão principal estiver num modelo do nível forte
  ou com esforço alto, diga uma vez, no início: "Sugiro o modelo médio
  (`<comando da plataforma>`) e esforço médio para a sessão principal: os
  estágios pesados já usam o nível forte nos subagentes." O comando está em
  `plataformas.md`. Siga mesmo que o usuário não troque.
- **Um processo só.** Não invoque skills de processo de outros plugins
  (brainstorming, planos, desenvolvimento por subagentes) durante o pipeline: o
  processo é este. Se um plugin desses estiver ativo, sugira uma vez
  desligá-lo neste projeto (ver INSTALL.pt-BR.md, "Custo").
- **Você só orquestra.** Não faça trabalho pesado na sessão principal: merge com
  conflito, correção de teste, depuração, investigação de falha e refatoração
  vão para um subagente (`scaffold-implementer`) com um ticket de correção
  (fim de `references/stages.md`).
- **Leia pouco.** Nunca leia arquivo grande inteiro (spec, tickets, logs,
  relatórios de ferramenta): use busca e trechos. Saída de teste e build sempre
  filtrada (só falhas e o resumo final).
- **Recomece limpo** nos pontos de compactação abaixo, inclusive a cada onda
  do estágio 7: sessão limpa com `continuar` custa menos que compactar, que
  relê a conversa inteira para resumi-la.
- **Respostas curtas.** Os subagentes gravam o trabalho em arquivo e respondem
  em até 10 linhas; não peça para devolverem relatório ou código na resposta.

## Nomes dos subagentes

Conforme a plataforma e a forma de instalação, os subagentes podem ter prefixo
de plugin (no Claude Code como plugin: `molbytes:scaffold-architect`) ou não
(`scaffold-architect`). Antes do primeiro delegamento, veja qual forma existe
na lista de agentes disponíveis e use sempre essa. Nas tabelas abaixo os nomes
aparecem sem prefixo. Se a plataforma não tiver nenhum `scaffold-*`, siga
"Sem subagentes" em `plataformas.md`.

## Extensões

Depois da pasta de documentos e do modo, antes do estágio 1, e sempre que
retomar, veja na lista de skills disponíveis se existe uma chamada
`molbytes-extension` (com ou sem prefixo de plugin) ou cuja descrição comece
com "Extensão" do molbytes.scaffold. Se existir, leia
`references/extensoes.md` (o contrato: como carregar, o que a extensão pode
acrescentar e o que não pode mudar), invoque-a e siga a tabela dela sobre em
que estágio entra cada referência. Registre o nome em `state.md`
(`Extensão:`); a compactação apaga o conteúdo dela da conversa.

Extensões complementam o pipeline; não removem estágios, pausas de aprovação,
o roteamento explícito de modelo nem o gate do estágio 11. Sem extensão, o
pipeline funciona igual.

## Pipeline

| # | Estágio | Quem executa | Saída | Pausa? |
|---|---------|--------------|-------|--------|
| 1 | grill-me | você (sessão principal) | `.project/qa.json` | conversa |
| 2 | to-spec (+ modelo de ameaças) | `scaffold-architect` | `.project/spec.md` | **SIM** |
| 3 | risks-tech-debt (+ requisitos de segurança, sondagem das premissas) | `scaffold-architect`; sondagem: `scaffold-tester` | `.project/risks.yaml` (+ `sondagens.md`) | só se uma premissa for negada |
| 4 | to-design | `scaffold-designer` | `.project/design/` | não |
| 5 | to-tickets | `scaffold-planner` | `.project/tickets.yaml` | não |
| 6 | assign-to-agents | `scaffold-router` (níveis) + `scripts/ondas.py` (ondas) | `.project/classificacao.json` + `.project/agent-map.json` | **SIM** (custo do estágio 7; não com `--pequeno`) |
| 7 | implement | `scaffold-implementer` (N em paralelo) | código na raiz | não |
| 8 | tests (plano → executar → corrigir) | `scaffold-tester` + `scaffold-implementer` | `.project/plano-de-teste.yaml` + testes + relatório | só se a correção falhar 2x |
| 9 | security (audit → triage → fix → verify) | `scaffold-security` + `scaffold-implementer` | `.project/security/` | só se houver decisão |
| 10 | code-review (+ impacto fora do diff no modo alteração) | `scaffold-reviewer` | `.project/code-review-report.md` (+ `impacto.md`) | **SIM** |
| 11 | final (testes + rescan + gate) | `scaffold-tester` + `scaffold-security`; gate: você | `.project/pipeline-report.md` | só se bloquear |

Instruções detalhadas de cada estágio: `references/stages.md`. Leia a seção do
estágio antes de executá-lo. Para os estágios 2, 3, 7, 9 e 11, leia também
`references/security.md`.

## Estado e compactação

A memória da conversa não é confiável depois de uma compactação. A fonte da
verdade é `.project/state.md` + os arquivos em `.project/` + o `git log`.

Ao fim de **cada** estágio, reescreva `.project/state.md` com o modelo em
`references/state-template.md`. Mantenha curto (menos de 80 linhas): decisões e
pendências, não cópias dos artefatos.

**Pontos de compactação:** ao terminar os estágios **2, 5, 8 e 9**, **cada onda
do estágio 7** e a cada 10 itens corrigidos no estágio 8, depois do commit
(com `--pequeno`, só ao terminar os estágios 2 e 9):
1. Confira que "Próximo passo" do `state.md` diz exatamente o que fazer, e
   diga ao usuário: "Estágio N salvo e commitado. Para economizar, abra uma
   sessão limpa (`<comando da plataforma>`) e rode `<o comando que iniciou o
   pipeline> continuar`: a sessão recomeça leve e retoma pelo `state.md`. Se
   preferir manter a conversa, `<comando de compactar>` e depois `continuar`."
   Os comandos de cada plataforma estão em `plataformas.md` (no Claude Code:
   `/clear`, `/molbytes:molbytes-scaffold continuar` e `/compact`).
2. Espere a resposta. Se ele disser para seguir sem limpar, siga.

**Depois de qualquer compactação** (manual ou automática), ou ao ser chamado
com "continuar": antes de qualquer outra ação, releia a seção da sua
plataforma em `plataformas.md`, resolva a pasta de documentos,
leia `.project/state.md` e `git log --oneline -15` (no modo externo, dos dois
repositórios), invoque de novo a extensão de `Extensão:` (se houver),
reaplique as flags de `Flags:`, confirme em uma linha onde está, e retome do
próximo passo listado em "Próximo passo". Não refaça estágios já commitados.

## Retomada

Se a pasta de documentos já existir ao iniciar (interna ou achada pelo
ponteiro), leia `.project/state.md` (ou, se não existir, deduza pelos arquivos
e pelo `git log`), informe ao usuário o último estágio concluído e pergunte se
continua dali. Se a rodada que está lá terminou (estágio 11 marcado) ou o
pedido é outra mudança, é uma rodada nova: arquive a anterior em
`.project/<fase>/` e comece a nova na raiz, como em "Rodada nova numa pasta
que já tem documentos" (`references/documentos.md`). Se o ponteiro indicar uma pasta que não existe mais, siga
`references/documentos.md`: diga onde procurou e pergunte onde estão os
documentos.

## Flags aceitas no texto do pedido

- `--ate <estágio>`: para depois do estágio indicado, pelo número ou pelo nome
  da tabela do pipeline, com ou sem o prefixo `to-` (ex.: `--ate 5`,
  `--ate tickets`).
- `--sem-design`: pula o estágio 4. Sem `.project/design/`, os estágios
  seguintes usam a spec no lugar do design (fluxos e telas vêm dela).
- `--economico`: aplica a coluna "econômico" do roteamento de modelos.
- `--pequeno`: alteração pequena (até 3 tickets) num sistema que já existe.
  Menos perguntas, spec curta, sem design nem pausa de custo; testes,
  segurança, code review, impacto fora do diff e gate continuam iguais. Só no
  modo alteração. Regras em `references/alteracao.md`, "Alteração pequena".

Registre as flags em `state.md` (`Flags:`); valem até o fim do ciclo.
