# Estágios em detalhe

No **modo alteração**, siga também `references/alteracao.md` (ponto de
partida, documentação do sistema e as regras de cada estágio marcadas abaixo).

## 1. grill-me (sessão principal)

Entreviste o usuário sobre o projeto. Uma pergunta por vez, no máximo 8.
Cubra: usuários e papéis, fluxos principais, stack (se ele já tiver preferência),
restrições (offline, pagamentos, LGPD/RGPD, países), integrações, prazo e o que
fica fora do MVP. Não pergunte o que já está na descrição.

Salve em `.project/qa.json`:
```json
{ "descricao": "...", "respostas": [{"pergunta": "...", "resposta": "..."}],
  "stack": {}, "fora_do_mvp": [] }
```

## 2. to-spec → scaffold-architect (pausa)

Peça ao architect para gerar `.project/spec.md` a partir de `qa.json`, com:
visão geral, arquitetura, modelos de dados, endpoints/contratos, fluxos de
usuário, requisitos não funcionais, fora do escopo, e a seção
**"Segurança e dados pessoais"** descrita em `references/security.md` (parte A).

**Modo alteração com documentação do sistema:** a spec ganha a seção
"Documentação afetada" (ver `alteracao.md`).

**Tamanho:** a spec tem no máximo ~30 mil caracteres. Ela descreve decisões,
contratos e regras; detalhe de implementação fica nos tickets. Spec maior é
lida inteira por vários agentes e multiplica o custo.

Depois: mostre um resumo de 10 linhas, peça ao usuário para revisar o arquivo e
**espere a aprovação explícita** antes de continuar. Se ele pedir mudanças,
reenvie ao architect com as mudanças.

## 3. risks-tech-debt → scaffold-architect

Gere `.project/risks.yaml`:
```yaml
risks:
  - id: RISK-001
    titulo: ...
    severidade: alta|media|baixa
    mitigacao: ...
    quando: mvp|v2
tech_debt:
  - id: TD-001
    titulo: ...
    motivo: ...
    origem: risco          # risco | SECURITY-00X | code-review
    preexistente: false    # modo alteração: código que a alteração não tocou
```
Riscos de severidade alta com `quando: mvp` viram requisitos na etapa 5.

Inclua também a lista `security_requirements` (formato em
`references/security.md`, parte A). Cada requisito precisa ser testável.

## 4. to-design → scaffold-designer

Gere em `.project/design/`: `design-system.md` (cores, tipografia, espaçamento),
`screens.md` (wireframes em texto de cada tela), `user-flows.md`,
`components.md`. Sem Figma: tudo em Markdown.

## 5. to-tickets → scaffold-planner

Gere dois tipos de arquivo:

- `.project/tickets.yaml`: o **índice**, só com os campos abaixo (sem descrição
  longa). É o que o router e o orquestrador leem.
- `.project/tickets/<id>.md`: **um arquivo por ticket**, autossuficiente, com a
  descrição, os critérios, os testes e os **trechos da spec, do design e dos
  riscos que o ticket usa** (copiados, não referenciados). Do pipeline, o
  implementador lê só este arquivo e o `regras-implementacao.md` (estágio 7).
  Máximo de ~4 mil caracteres por ticket.

Convenções que valem para todos os tickets (nomes, estrutura, padrão de
testes) ficam no topo do índice, em `convencoes:`, curtas; no estágio 7 elas
vão para a seção "Todos" de `regras-implementacao.md`.

**Tamanho do ciclo:** se passar de ~30 tickets, pare e proponha ao usuário
dividir em ciclos menores (cada um com seus estágios 5 a 11). Ciclo grande faz
o contexto do orquestrador crescer sem parar.

Topo do índice e cada ticket:
```yaml
convencoes:                         # até ~10 linhas, valem para todos os tickets
  - ...
tickets:
- id: BE-001
  titulo: ...
  area: backend|frontend|infra
  depende_de: []
  arquivos: [backend/app/auth.py]   # diretórios/arquivos que o ticket toca
  docs: [README.md]                 # modo alteração: documentos do sistema que o ticket atualiza
  security_reqs: [SR-001]           # requisitos de segurança que o ticket cumpre
  criterios_aceite: [...]
  testes: [...]
```
Tickets pequenos (meio dia de trabalho humano no máximo). Inclua os riscos altos
do MVP como tickets ou critérios de aceite. Cada item de `security_requirements`
deve aparecer como critério de aceite (com teste) em pelo menos um ticket, que
o lista em `security_reqs`.

**Ticket de bootstrap obrigatório:** o primeiro ticket é sempre `INFRA-000`, sem
dependências, e todos os outros dependem dele. Ele cria a estrutura de pastas,
o runner de testes unitários (com um teste trivial passando), o linter, o
`.gitignore`, o `.env.example` e **todas as dependências previstas pela spec**.

**Manifestos de dependência** (`package.json`, lockfiles, `requirements.txt`,
`pyproject.toml`, `*.csproj`, `go.mod`...) só aparecem em `arquivos` do
`INFRA-000` ou de tickets de infra dedicados. Ticket comum não os lista; se o
implementador precisar de um pacote novo, ele pede ao orquestrador, que o
adiciona entre ondas.

## 6. assign-to-agents → scaffold-router (leve)

O router lê só o índice `tickets.yaml` e as regras de `references/model-routing.md`
(coladas no prompt; com extensão que traz roteamento calibrado, cole também a
tabela dela, conforme `references/extensoes.md`) e gera
`.project/agent-map.json`:
```json
{ "ondas": [
    { "onda": 1, "tickets": [
      {"id": "BE-001", "area": "backend", "complexity": "alta",
       "model": "forte", "motivo": "autenticação"} ] } ] }
```
Ondas respeitam `depende_de`. Dentro de uma onda, dois tickets **não podem**
tocar os mesmos arquivos (evita conflito na execução paralela).

**Limite do nível forte:** se mais de 25% dos tickets ficarem em `forte`, o router lista
cada um com o motivo da lista fechada de `model-routing.md`; mostre essa lista
ao usuário junto com o plano.

Mostre ao usuário: total de tickets, quantos em cada nível (forte/medio/leve), número de
ondas e tempo estimado (soma dos orçamentos de `watchdog.md` pela onda mais
lenta). **Espere aprovação explícita** antes do estágio 7, o mais caro. Se o
usuário pedir, rebaixe tickets ou aplique `--economico` e reenvie ao router.

## 7. implement → scaffold-implementer (paralelo por onda)

Para cada onda, em ordem:
- Lance um `scaffold-implementer` por ticket, **em paralelo e em segundo
  plano** quando a plataforma permitir, com o modelo do nível que o
  `agent-map.json` dá para aquele ticket (como lançar e o que fazer se a
  plataforma não roda em paralelo ou não escolhe modelo por chamada:
  `references/plataformas.md`). Em segundo plano, você recebe o aviso de cada
  um que termina e pode responder `status` enquanto a onda roda.
- Antes da onda 1, grave **uma vez** `.project/regras-implementacao.md`: as
  convenções do topo do índice (seção "Todos") e, se houver extensão ou
  convenção do projeto existente, uma seção por camada (`backend`, `frontend`,
  `banco`, `infra`, `interface`); o implementador lê as das camadas que os
  arquivos do ticket tocam. Atualize o arquivo só se uma regra mudar.
- O prompt do implementador é curto: o caminho de `.project/tickets/<id>.md`,
  o de `.project/regras-implementacao.md` e o modelo. As regras de código
  seguro já estão no próprio agente. Não cole regras no prompt nem mande ler a
  spec ou o `tickets.yaml` inteiros.
- Testes unitários rodados durante a onda não podem depender de banco real,
  porta fixa ou serviço externo (vários implementadores rodam ao mesmo tempo na
  mesma pasta). Testes que precisam disso ficam para o estágio 8.
- Registre START de cada um em `.project/runs.log`. A cada subagente que
  termina, faça a verificação de `references/watchdog.md` nos que ainda rodam.
- Ao terminar a onda, rode os testes unitários da área, com saída filtrada (só
  falhas e resumo). Falha atribuível a um ticket: relance esse ticket conforme
  o escalonamento de `model-routing.md`. Conflito de merge ou falha que não é
  de um ticket só vai para um subagente com um **ticket de correção** (fim
  deste arquivo), não para você.
- **Worktree não fica para trás.** Se os implementadores rodarem em worktree
  isolada (ex.: `isolation: "worktree"` no Claude Code), cada ticket
  mergeado sai na hora: `git worktree remove <caminho>` e
  `git branch -d <branch>` (ex.: `worktree-agent-…` no Claude Code). Ticket relançado ou descartado também: a worktree e a
  branch da tentativa que não vai ser mergeada saem (`-D` só para essas).
  Nunca `--force`: worktree com alteração não commitada é mostrada ao usuário.
  Antes do commit da onda, rode `git worktree prune`; `git worktree list` deve
  mostrar só a pasta do projeto.
- Commit por onda: `scaffold(7): onda N`.
- **Modo alteração:** o ticket traz a lista `docs`; o implementador atualiza
  esses documentos junto com o código.

## 8. tests → scaffold-tester + scaffold-implementer

Siga `references/plano-de-teste.md`:

1. **8.1 plano** — o tester gera `.project/plano-de-teste.yaml`, ligando cada
   item a um critério de aceite, fluxo, risco alto ou `security_requirements`
   (ex.: webhook sem assinatura é rejeitado, pagamento não duplica cobrança).
   Mostre só o resumo ao usuário e siga.
2. **8.2 executar** — o tester escreve os testes que faltam, roda tudo e marca
   cada item (`passou`, `falhou`, `bloqueado`, `manual`).
3. **8.3 corrigir** — cada `falhou` vai para um `scaffold-implementer`, que
   corrige o código (não afrouxa o teste). Máximo de 2 tentativas por item;
   depois, pergunte ao usuário.
4. **8.4 relatório** — `.project/test-report.md` com totais reais, correções,
   aceites e a lista "Testes manuais a fazer". Só números que a ferramenta
   mostrou.

## 9. security → scaffold-security + scaffold-implementer

Siga `references/security.md`, parte C, na ordem:

1. **9.1 audit** — rode as ferramentas e peça ao `scaffold-security` (forte) a
   revisão manual. Saída: `.project/security/findings.yaml`.
2. **9.2 triage** — `scaffold-security` classifica cada achado. Baixo e falso
   positivo justificado ficam com status `divida` ou `falso_positivo` e não
   bloqueiam; você (não o agente, que só escreve em `security/`) os copia para
   `risks.yaml` em `tech_debt`, com `origem: SECURITY-00X`.
3. Se não sobrar crítico, alto ou médio: vá para o estágio 10.
4. Se houver **médio**: pergunte ao usuário, para cada um, "corrigir" ou
   "aceitar o risco". Aceite vira registro em `.project/security/accepted.md`
   com a justificativa dele.
5. **9.3 fix** — para cada SECURITY-00X a corrigir, escreva o ticket de
   correção `SECURITY-00X` e lance um `scaffold-implementer` no nível forte. Primeiro ele escreve o teste que
   reproduz a falha (precisa falhar), depois corrige.
6. **9.4 verify** — `scaffold-security` (não o implementador) confere os três
   critérios da parte C. Se reprovar, volta ao 9.3 com o motivo. **Máximo de
   2 tentativas de correção por ticket**; depois disso, pare e pergunte ao
   usuário o que fazer.

Commit ao fim do 9.2 (`scaffold(9): security triage`) e a cada ticket
verificado (`scaffold(9): fix SECURITY-00X`).

## 10. code-review → scaffold-reviewer (pausa)

O reviewer não altera código; ele mesmo grava `.project/code-review-report.md`
com achados classificados como crítico/importante/sugestão, cada um com
arquivo e linha, e responde só com o resumo.
Rode também os linters do projeto, se existirem. A segurança já foi auditada no
estágio 9: o reviewer foca em corretude e manutenção, mas ainda registra
qualquer problema de segurança que notar.

**Modo alteração com documentação do sistema:** o reviewer confere se cada
documento da "Documentação afetada" bate com o código.

Apresente o resumo ao usuário e **pergunte** se quer que os críticos sejam
corrigidos antes de seguir: um ticket de correção `FIX-REVIEW-<n>` por crítico,
no nível forte.

## 11. final → testes + rescan + gate

1. **Testes** → `scaffold-tester` (medio): roda a suíte completa (unitários +
   integração), atualiza o `plano-de-teste.yaml` e devolve só totais e falhas.
   Falha nova passa pela correção do 8.3.
2. **Rescan** → `scaffold-security` (medio): roda o rescan rápido de
   `references/security.md`, parte D, e devolve "nada novo" ou a lista de
   achados novos. Achado novo: triagem em outra chamada, no nível forte.
3. **Gate** (você, lendo os resumos): o pipeline só termina como "concluído" se:
   - todos os testes passam e todo item automatizado do plano está `passou`
     ou `aceito` (itens `manual` não bloqueiam);
   - não há achado crítico ou alto aberto;
   - todo achado médio aberto está em `accepted.md`;
   - **modo alteração:** nenhuma falha de teste nova em relação ao ponto de
     partida, e todo documento do sistema da "Documentação afetada" foi
     atualizado (os de `site` vão para o relatório como atualização manual).
   Se algo falhar, mostre o motivo e pergunte ao usuário: corrigir agora, ou
   encerrar como "concluído com pendências" (registrado no relatório).
4. **Limpeza:** não pode sobrar worktree nem branch criada pelo pipeline
   (estágio 7 e tickets de correção dos estágios 8 a 11). Confira
   `git worktree list` e as branches das worktrees do pipeline (no Claude
   Code, `git branch --list "worktree-agent-*"`): o que está
   mergeado sai como no estágio 7; o que não está vai para as pendências do
   relatório e é mostrado ao usuário.
5. Gere `.project/pipeline-report.md`: estágios, modelos usados, tokens por
   estágio (somados do `runs.log`), escaladas,
   resultado dos testes, resumo de segurança (achados por severidade:
   corrigidos, aceitos, em dívida), resumo do plano de teste (itens por status)
   e a lista "Testes manuais a fazer", pendências. Commit final.

## Ticket de correção (implementador fora da onda)

Sempre que um `scaffold-implementer` for lançado fora de um ticket do estágio 5
(conflito de merge, falha da onda que não é de um ticket só, item do plano
de teste, achado de segurança, crítico do code review, falha nova no estágio
11),
escreva antes `.project/tickets/<id>.md`, com até ~2 mil caracteres:

- **id:** `FIX-<origem>` (ex.: `FIX-TP-007`, `FIX-REVIEW-3`, `FIX-MERGE-2`) ou
  o próprio `SECURITY-00X`;
- **origem:** o item, achado, ticket ou onda que gerou a correção;
- **problema:** a falha resumida (erro, arquivo:linha, saída filtrada);
- **arquivos:** os que ele pode mexer (os do ticket de origem e os apontados
  pela falha);
- **teste:** o que precisa passar no fim (o do item, o de reprodução ou a
  suíte da área);
- **critério:** quando está corrigido.

O ticket de correção não entra no `tickets.yaml`. O implementador o trata
como qualquer ticket: no prompt, o caminho dele, o de `regras-implementacao.md`
e o modelo; mexe só nos arquivos listados. Modelo: o da regra do estágio de
origem (8.3, 9.3, 10); sem regra (merge, falha da onda), medio e, na 2ª
tentativa, forte. Registre o START no `runs.log` com esse id.
