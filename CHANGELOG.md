# Changelog

Todas as mudanças relevantes do molbytes.scaffold.

## v0.19.0

Histórico das rodadas, para saber quando e por que o sistema mudou sem abrir
fase por fase (ainda sem execução real):

- `.project/historico.md` (`references/historico.md`): uma entrada por
  rodada, a mais nova no topo, com até ~10 linhas: pedido, modo, commits,
  áreas (com os nomes de "Módulos" do mapa), decisões, o que ficou de fora,
  premissas abertas e o resultado do gate.
- Escrito pela sessão principal, sem subagente, no fim do estágio 11; a
  correção de teste manual acrescenta a linha `Depois do gate:`.
- Mudanças feitas fora do pipeline: no começo da rodada nova, se o mapa
  achar diff, entra uma entrada `fora do pipeline` com os commits e as áreas.
- Lido no começo de cada rodada nova (as 3 entradas do topo) e pelo
  architect no estágio 2: se a alteração muda uma decisão registrada, a spec
  diz qual, de que fase e por que.
- Projetos com fases de antes do histórico: a skill propõe montar uma
  entrada por fase a partir dos relatórios.
- Fica na raiz da pasta de documentos, como a `spec.md` e o mapa.

## v0.18.1

Ponto de partida do modo alteração em projeto sem git ou com mudanças não
commitadas (antes, depois do `git init` não havia commit para o
`base_commit` nem para o `Commit:` do mapa, e o código antigo contava como
mudança da rodada, inclusive nos achados de segurança):

- Sem git ou sem commit: `git init`, `.gitignore` das regras gerais, o
  usuário confere a lista do que entra e a skill faz o commit local
  `scaffold(0): ponto de partida`, sem a pasta de documentos.
- Com alterações não commitadas: a skill não começa; o usuário escolhe entre
  ela commitar como estão ou ele commitar ou guardar com `git stash`.

## v0.18.0

Mapa do código, para cada rodada não redescobrir o sistema do zero (ainda
sem execução real):

- `.project/mapa-codigo.md` (`references/mapa-codigo.md`): visão e comandos,
  estrutura, pontos de entrada, módulos, contratos, arquivos de registro e
  convenções. É um índice, com caminho em cada item e sem código copiado nem
  segredo, de até ~15 mil caracteres. O mapa diz onde olhar; quem decide ou
  altera lê o código que ele aponta.
- Carimbo `Commit:` (último commit de código mapeado). Quem lê confere o diff
  desde ele, e área com arquivo no diff se confirma no código.
- Gerado pelo `scaffold-architect` (medio) antes do estágio 1 no modo
  alteração e no fim do estágio 7 no modo novo. Atualizado pelo diff, só nas
  seções afetadas, no estágio 11 e no começo de cada rodada nova, se o código
  mudou fora do pipeline. Os implementadores não editam o mapa (todos da
  onda mexeriam no mesmo arquivo).
- Lido no grill-me (alteração), pelo architect (estágio 2), pelo planner
  (`arquivos`, arquivos de registro e trecho copiado em cada ticket) e pelo
  tester ("Comandos").
- Gate do estágio 11: não fecha como "concluído" se o mapa não cobre o
  código atual. Na rodada nova, o mapa fica na raiz, como a `spec.md`.
- `state.md` ganha `Mapa do código:`; orçamentos do mapa em `watchdog.md` e
  nível em `model-routing.md`.
- Extensões carregam antes do mapa do código e podem acrescentar trecho ao
  prompt dele (onde olhar em cada stack); o formato do mapa não muda.

## v0.17.0

Ajustes de uma execução real no modo alteração (integração com serviço
externo). O gate passou com toda a suíte verde, mas os testes manuais acharam
defeitos depois dele, a maioria de premissas sobre o serviço que a conta de
teste respondia no mesmo dia:

- **Premissas sobre terceiros:** a spec ganha a seção "Premissas sobre
  terceiros" (id, o que se supõe, como confirmar, o que muda se for falsa). No
  fim do estágio 3, com conta de teste disponível, o `scaffold-tester` sonda
  as premissas (só conta de teste, operações reversíveis, credencial fora dos
  arquivos) e grava `sondagens.md`; premissa negada volta à spec com
  aprovação do usuário. Simuladores de serviço externo reproduzem as
  respostas gravadas, inclusive os erros. Premissa aberta vira item `manual`
  do plano e entra no relatório final.
- **Arquivos de registro** (rótulos, traduções, categorias, listas de
  contrato) com um ticket dono: o dono depende de todos os tickets que criam
  valores para ele (no caso real, as chaves criadas em ondas seguintes
  chegaram cruas à tela).
- **Depois do gate:** defeito de teste manual vira ticket `FIX-MANUAL-<n>`,
  com START/END no `runs.log` e a seção "Testes manuais" no
  `pipeline-report.md`.
- "Testes manuais a fazer" começa por "Preparar o ambiente" (migrações,
  dados, configuração, contas de teste).
- `runs.log`: o END é gravado assim que o subagente termina, com o total de
  tokens do resultado (gravados em lote, 36 de 45 saíram com `?`).
- Rodada nova: vai para a raiz também quando o projeto tem fases em
  subpastas de antes da 0.16 ou uma rodada antiga sem `state.md`.
- Estágio 9: numa worktree, o gitleaks varre o histórico pelo repositório
  principal (`--log-opts=--all`); antes, ele não via o histórico.

## v0.16.0

Rodada nova num projeto que já tem pasta de documentos (antes, cada sessão
improvisava uma subpasta para a fase nova, e a retomada e as ferramentas que
leem `.project/state.md` não achavam o estado):

- A rodada atual fica sempre na raiz de `.project/`. Ao começar outra mudança
  (estágio 11 da anterior marcado, ou o usuário diz que é outro pedido), a
  rodada anterior vai para `.project/<fase>/` com `git mv` e commit
  `scaffold(0): arquiva <fase>`. Rodada não terminada só é arquivada com a
  confirmação do usuário (`references/documentos.md`, "Rodada nova numa pasta
  que já tem documentos").
- `spec.md`, `design/` e `docs-sistema.yaml` ficam na raiz e evoluem com o
  sistema; o resto (estado, tickets, roteamento, testes, segurança,
  relatórios, `runs.log`, `model-log.md`) vai com a fase.
- `state.md` ganha `Fase:` e `Fases anteriores:`.
- `.gitignore` com `.project/**/security/raw/` (externo: `**/security/raw/`),
  para os relatórios brutos das fases arquivadas continuarem fora do git.
  Pastas com a entrada antiga são corrigidas antes de arquivar.

## v0.15.0

Ondas por script, não pelo modelo (numa execução real, as ondas do router
vieram com 60 dependências fora de ordem e 48 conflitos de arquivo num ciclo,
e com tickets inventados e duplicados em outro):

- Estágio 6 em dois passos: o `scaffold-router` só classifica (nível e motivo
  em `.project/classificacao.json`) e `scripts/ondas.py` monta o
  `agent-map.json`, no mesmo formato de antes. O script recusa id duplicado,
  dependência que não existe, ciclo, ticket sem classificação, inventado ou
  repetido, nível inválido e forte sem motivo, e não grava nada com erro.
  Ondas: `INFRA-000` sozinho na 1; cada ticket na primeira onda depois das
  dependências sem conflito de arquivo (diretório conflita com o que está
  dentro). Mesma entrada, mesmas ondas.
- O script roda com `python3`, `python`, `py -3` ou na imagem
  `python:3.12-slim` do estágio 9; sem nenhum, o orquestrador monta as ondas e
  confere por uma lista de verificação em `stages.md`, e avisa no plano.
- `model-log.md` com formato fixo (`model-routing.md`): tabelas "Estágio 6:
  correções do orquestrador", "Escaladas" e "Reexecuções", com níveis. Mudança
  de nível depois do router (inclusive pedido do usuário) passa a ser
  registrada.
- `tests/test_ondas.py` (`python -m unittest discover tests`).

## v0.14.0

Codex, Gemini CLI e Cursor, além do Claude Code (adaptadores novos, ainda sem
execução real nessas plataformas):

- Roteamento por nível: `leve`, `medio` e `forte` no lugar de haiku, sonnet e
  opus. `agent-map.json`, `runs.log` e `state.md` gravam o nível; nomes do
  Claude em extensões e arquivos antigos valem como nível.
- `references/plataformas.md`: por plataforma, o modelo de cada nível, como
  lançar subagente com modelo explícito, paralelismo, limite de turnos,
  comandos de sessão e pasta fora do projeto. `SKILL.md` e as referências não
  citam mais comandos do Claude Code fora dessa tabela; `state.md` ganha
  `Plataforma:` e, se o usuário trocar, `Modelos:`.
- `adapters/build.py` gera, a partir de `skills/` e `agents/`: subagentes do
  Codex em TOML, extensão do Gemini CLI (um subagente por nível, porque ele
  não escolhe modelo por chamada) e subagentes do Cursor (`model: inherit`),
  além de `.codex-plugin/` e `.cursor-plugin/`. `--check` acusa adaptador
  desatualizado.
- Sem nenhum `scaffold-*` disponível, o pipeline para antes do estágio 2 e
  pede a instalação dos agentes.

## v0.13.3

Worktree e branch do pipeline não ficam para trás (numa execução real
sobraram worktrees `worktree-agent-*` depois do merge):

- Estágio 7: com implementadores em worktree isolada, cada ticket mergeado tem
  a worktree e a branch removidas na hora; tentativa relançada ou descartada
  também. Sem `--force`; antes do commit da onda, `git worktree list` só com a
  pasta do projeto.
- Estágio 11: passo de limpeza antes do relatório; o que não está mergeado vai
  para as pendências e é mostrado ao usuário.

## v0.13.2

Coerência depois das mudanças da v0.10.2 à v0.13.1 (revisão de todos os
arquivos):

- Nenhum texto manda mais colar regras no prompt do implementador; as
  convenções saem de `convencoes:` no topo do `tickets.yaml` (o planner as
  escreve) para a seção "Todos" de `regras-implementacao.md`.
- O implementador lê as seções das camadas que os seus arquivos tocam (antes,
  `banco` e `interface` nunca eram lidas).
- Falha de testes ao fim da onda: o ticket que falhou é relançado pelo
  escalonamento; ticket de correção só para merge e falha que não é de um
  ticket só. Modelo e orçamento definidos para o ticket de correção.
- `END` do `runs.log` aceita estágio, como o `START`. Versões e destaque de
  retomada atualizados no README e no INSTALL.

## v0.13.1

Estágio 9 mais seguro para o código do cliente (comandos testados num projeto
de teste com segredo, SQL concatenado e dependência vulnerável):

- Imagens com versão fixa: gitleaks v8.30.1, semgrep 1.178.0, trivy 0.74.0.
- Projeto montado somente leitura (`:ro`) em todos os scanners.
- semgrep com `--metrics off` e regras fixas (`p/default`, `p/owasp-top-ten`,
  `p/secrets`): `--config auto` exige enviar métricas. Sem checagem de versão.
- pip-audit e bandit num container descartável com versões fixas, em vez de
  `pip install` no Python da máquina.

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
