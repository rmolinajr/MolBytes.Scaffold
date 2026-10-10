# Changelog

Todas as mudanças relevantes do molbytes.scaffold.

## v0.13

Menos tokens na sessão principal:

- Pontos de compactação sugerem `/clear` + `/molbytes:molbytes-scaffold
  continuar` (sessão recomeça leve pelo `state.md`); `/compact` fica como
  alternativa, porque relê a conversa inteira para resumi-la.
- Todos os subagentes gravam o trabalho em arquivo e respondem em até 10
  linhas. O reviewer grava o próprio `code-review-report.md` em vez de
  devolvê-lo inteiro.
- Regras do implementador gravadas uma vez em `.project/regras-implementacao.md`
  (convenções e regras por área, inclusive de extensões); as regras de código
  seguro passaram para o próprio agente. O prompt de cada implementador fica
  só com o ticket, o arquivo de regras e o modelo.
- `runs.log` registra os tokens de cada subagente no `END`, e o
  `pipeline-report.md` mostra tokens por estágio.

## v0.12

- Ticket de correção (`FIX-...`, `SECURITY-...`): todo implementador lançado
  fora do estágio 7 (plano de teste, segurança, review, merge, estágio 11)
  recebe um ticket com arquivos permitidos, teste e critério.
- Estágio 11: testes no `scaffold-tester` e rescan no `scaffold-security`; a
  sessão principal só faz o gate e o relatório. Orçamentos no watchdog.
- Escalonamento único: falha de teste repete no mesmo modelo e depois sobe um
  nível; `TRAVADO:` sobe direto. Correção do plano usa o modelo mais alto dos
  tickets de origem.
- Implementadores do estágio 7 em segundo plano, para o `status` responder
  durante a onda.
- Triagem de segurança: baixa e falso positivo ficam em `findings.yaml`; o
  orquestrador os copia para `tech_debt` (agora com `origem` e
  `preexistente`).
- Índice de tickets com `security_reqs`, `criterios_aceite` e `testes` iguais
  no planner e em `stages.md`.
- Modo alteração: estágio 3 só com o que a mudança traz; propõe pular o design
  quando não há tela nova.
- Capa sem número de versão; README e INSTALL com o estado atual e esforço
  médio na sessão principal.

## v0.11

- Contrato das extensões (`references/extensoes.md`, contrato 1): quando e
  como carregar (depois da pasta de documentos e do modo; várias em ordem
  alfabética), a linha `Contrato: extensões 1` que a extensão declara, o que
  ela pode acrescentar (perguntas no grill-me dentro do limite, arquivos na
  pasta de documentos, pausas, roteamento calibrado com motivo explícito,
  condições no gate) e o que não pode mudar (estágios, pausas, gate,
  formatos de arquivo, flags). Conflito: o pipeline prevalece.

## v0.10.2

- Retomada numa sessão nova: `/molbytes:molbytes-scaffold continuar` (só
  `continuar` não carrega a skill numa sessão nova).
- `state.md` registra `Flags:` e `Extensão:`; depois de uma compactação o
  orquestrador reaplica as flags e invoca a extensão de novo.
- `--sem-design`: planner, tester e plano de teste usam a spec quando não há
  `.project/design/`. `--ate` aceita número ou nome do estágio.
- Estágio 9: comandos em bash (a ferramenta do Claude Code), relatórios brutos
  na pasta de documentos (no modo externo, nada é criado no projeto do
  cliente) e varreduras sem `.project/`.
- README: exemplos de execução (projeto novo, alteração, `--ate`,
  `--sem-design`, retomada), tabela de flags e comandos durante o pipeline.

## v0.10.1

- O orquestrador sugere também esforço médio para a sessão principal e não
  invoca skills de processo de outros plugins durante o pipeline.
- INSTALL: seção "Custo" (sonnet com esforço médio, uma sessão por ciclo,
  desligar plugins de processo como `superpowers` no projeto do pipeline).

## v0.10

Menos gasto de tokens, a partir de uma execução real (sessão principal em opus
gastou mais que todos os subagentes; 77% dos tickets em opus; implementadores
lendo spec e tickets inteiros):

- Seção "Custo" no orquestrador: sugere `/model sonnet` para a sessão
  principal, proíbe trabalho pesado nela (merge, depuração e correção vão para
  subagente), leitura só por trechos e saída de teste filtrada; compactação a
  cada onda do estágio 7.
- Tickets em dois níveis: índice curto `tickets.yaml` e um arquivo
  autossuficiente por ticket em `tickets/<id>.md` (até ~4 mil caracteres). O
  implementador lê só o dele; o router lê só o índice.
- Spec com até ~30 mil caracteres; ciclos acima de ~30 tickets são divididos.
- Roteamento: opus só com motivo de uma lista fechada; na dúvida, sonnet;
  acima de 25% em opus, o plano do estágio 6 mostra a lista com os motivos.

## v0.9

- Plano de teste no estágio 8: `plano-de-teste.yaml` liga cada item a um
  critério de aceite, fluxo, risco ou requisito de segurança; os testes são
  executados e cada item marcado (`passou`, `falhou`, `bloqueado`, `manual`).
  Falhas são corrigidas automaticamente no código (no máximo 2 tentativas por
  item; depois a skill pergunta), sem afrouxar o teste. O estágio 11 roda o
  plano de novo e o gate exige os itens automatizados passando ou aceitos;
  testes manuais vão como lista no relatório. Ver `references/plano-de-teste.md`.

## v0.8

- Alteração de sistema existente: se o projeto já tem código, a skill pergunta
  se é projeto novo ou alteração. Na alteração, registra o ponto de partida
  (`base_commit` e testes que já falham, que não bloqueiam o gate) e procura a
  documentação do sistema no projeto; se não achar, pergunta se há em outro
  lugar. Sem documentação, só altera o sistema. Com documentação, ela é
  atualizada junto com o código (campo `docs` nos tickets), conferida no code
  review e exigida no gate do estágio 11. Detalhes em `references/alteracao.md`.

## v0.7

- Pasta de documentos: no início, a skill pergunta se os documentos ficam em
  `.project/` (padrão) ou numa pasta separada, com git próprio, para não sujar
  o projeto do cliente. O vínculo fica em `~/.molbytes/projetos.json`; se a
  pasta sumir, a skill diz onde procurou e pergunta onde estão os documentos.
  Subagentes recebem o caminho real. Detalhes em `references/documentos.md`.

## v0.6

- Extensões: antes do estágio 1 (e ao retomar), o orquestrador carrega uma
  skill `molbytes-extension` se houver uma instalada e segue a tabela dela
  sobre em que estágio entra cada referência. Permite templates por stack,
  domínio ou empresa sem alterar o pipeline.

## v0.5.2

- Agentes sem viés de PDV: o designer adapta o design ao produto e aos
  dispositivos da spec; o reviewer prioriza os riscos altos de `risks.yaml` em
  vez de uma ordem fixa (dinheiro, sync offline).
- `references/security.md`: superfícies de ataque, pagamentos e revisão manual
  passam a valer conforme o projeto ("se houver", "ex.:").
- INSTALL.md: seção "Recomendados (opcional)".

## v0.5.1

- Layout padrão de plugin: `skills/` e `agents/` na raiz do repositório. Com
  os caminhos personalizados em `.claude/`, o plugin carregava a skill mas não
  os 8 subagentes.

## v0.5

- Ticket `INFRA-000` obrigatório: estrutura, runner de testes, linter e todas as
  dependências antes da onda 1.
- Manifestos de dependência (`package.json`, lockfiles...) só em tickets de
  infra: acaba o conflito entre implementadores paralelos.
- Testes unitários sem banco, porta fixa ou serviço externo durante o estágio 7.
- Pausa para aprovação depois do estágio 6 (tickets por modelo, ondas, tempo
  estimado) antes do estágio 7, o mais caro.
- `.project/security/raw/` fora do git (o relatório do gitleaks contém os
  segredos achados); `findings.yaml` nunca guarda o valor do segredo.
- O orquestrador cola as regras no prompt dos subagentes: funciona com a skill
  instalada no projeto ou em `~/.claude/`.
- Reexecução de ticket também apaga arquivos novos (`git clean`).
- Texto genérico ("o usuário"), sem nomes nem caminhos pessoais.
- Licença MIT.
- `/agents` saiu do Claude Code: verificação agora por `/plugin` e parada por `/tasks`.
- Distribuição como plugin do Claude Code (`/plugin install molbytes@molbytes`).

## v0.4 — segurança

- Modelo de ameaças e dados pessoais (LGPD/RGPD) já na spec; `security_requirements`
  testáveis viram critérios de aceite dos tickets.
- Regras de código seguro para todo implementador.
- Novo estágio 9: audit → triage → fix → verify, com o novo subagente
  `scaffold-security` (opus).
- Achado médio: o usuário decide corrigir ou aceitar o risco (fica registrado).
- Correção sempre começa por um teste que reproduz a falha; verificação feita
  por outro agente; no máximo 2 tentativas por achado.
- Estágio 11: testes finais + rescan rápido + gate (não termina com crítico ou
  alto aberto).

## v0.3

- `maxTurns` em todos os subagentes: o Claude Code encerra quem passar do limite.
- Orçamento de tempo por ticket/estágio, registrado em `.project/runs.log`.
- Aviso quando um subagente passa de 2x o tempo esperado.
- Comando `status` para ver o que está rodando e há quanto tempo.
- Para ver ou parar um subagente: `/agents` (aba Running) ou `/tasks`.
- Reexecução automática um nível de modelo acima quando um agente trava.

## v0.2

- `.project/state.md`: checkpoint atualizado a cada estágio.
- Pontos de compactação sugeridos nos estágios 2, 5 e 7.
- Retomada por `continuar` após /compact ou em sessão nova.
- Recomendação de `/autocompact 500k`.
