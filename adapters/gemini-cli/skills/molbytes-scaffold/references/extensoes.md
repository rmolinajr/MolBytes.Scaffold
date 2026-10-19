# Extensões (contrato 1)

Uma extensão é uma skill que acrescenta conhecimento ao pipeline: regras por
stack ou domínio, compliance, design, relatórios. Ela complementa o pipeline;
nunca o substitui. Sem extensão, o pipeline funciona igual.

## Como o orquestrador acha e carrega

1. **Quando:** depois de resolver a pasta de documentos e o modo (novo ou
   alteração), antes do estágio 1. Assim a extensão já sabe `Documentos:` e
   `Modo:`.
2. **Qual:** skill chamada `molbytes-extension` (com ou sem prefixo de plugin)
   ou cuja descrição comece com "Extensão" e cite o molbytes.scaffold. Mais de
   uma: carregue todas, em ordem alfabética do nome.
3. **Contrato:** confira a linha `Contrato: extensões <N>` no corpo da
   extensão. Se faltar ou se `N` for maior que 1, diga em uma linha ("a
   extensão X usa o contrato N; este pipeline conhece o 1") e use só o que
   este arquivo permite.
4. **Registro:** diga ao usuário em uma linha qual extensão foi carregada e
   grave o nome em `state.md` (`Extensão:`; várias separadas por vírgula).
5. **Retomada:** depois de compactação ou `continuar`, invoque de novo cada
   extensão de `Extensão:`. A compactação apaga o conteúdo dela da conversa.

## O que a extensão precisa ter

- Frontmatter **sem** `disable-model-invocation`: o orquestrador precisa
  invocá-la.
- A linha `Contrato: extensões 1`.
- Uma tabela de onde cada referência entra, com as colunas
  `Estágio | Quando | Referência`. Estágio é `início` (antes do estágio 1),
  `todos` ou o número de 1 a 11. Caminhos relativos à pasta da extensão.

## O que a extensão pode acrescentar

| Onde | O que pode | Regra |
|---|---|---|
| Subagentes | Regras e trechos de referência | Subagentes não leem a pasta da extensão. Regras de código por área vão para `.project/regras-implementacao.md` (gravado uma vez, ver estágio 7 em `stages.md`); trechos para os outros estágios, você cola no prompt. |
| 1 grill-me | Mostrar opções antes de perguntar, pular perguntas que ela já responde, acrescentar perguntas | O limite de 8 perguntas vale para o total. Respostas extras vão em `qa.json`, na chave `extensao`. |
| Pasta de documentos | Arquivos próprios (ex.: painel para o cliente, protótipo, briefing) | Nunca sobrescreve arquivo do pipeline nem escreve código de produção. Entra no commit do estágio. |
| Pausas | Pausas novas (ex.: aprovação do cliente) | Registre a pausa em `state.md` ("Próximo passo"). |
| 6 roteamento | Trocar o modelo padrão de um tipo de ticket com base em dados reais | O router continua gravando `model` e `motivo` de cada ticket na `classificacao.json`; o motivo cita a extensão. As ondas continuam saindo de `scripts/ondas.py`. Valem o limite do nível forte e a aprovação do plano. Nomes de modelo do Claude na tabela da extensão valem como nível: haiku = leve, sonnet = medio, opus = forte. |
| 11 gate | Condições de bloqueio e itens no `pipeline-report.md` | Só acrescenta; nunca afrouxa uma condição do gate. |

## O que a extensão não pode mudar

- Pular ou remover estágios, pausas de aprovação, o gate do estágio 11, o
  watchdog (`runs.log`) ou o commit por estágio.
- Deixar um subagente sem modelo explícito, trocar os subagentes do pipeline
  ou lançar outros.
- Mudar o formato dos arquivos do pipeline (`state.md`, `runs.log`,
  `qa.json`, `tickets.yaml`, `classificacao.json`, `agent-map.json`,
  `model-log.md`, `plano-de-teste.yaml`, `findings.yaml`): só acrescentar o
  que este arquivo permite.
- Reduzir requisitos de segurança ou o escopo da auditoria.
- Ignorar flags: com `--sem-design`, o que ela faria no estágio 4 também é
  pulado; com `--ate`, ela para junto.

## Conflitos

- **Extensão contra o pipeline:** o pipeline prevalece. Diga ao usuário em uma
  linha o que da extensão foi ignorado.
- **Entre extensões:** pergunte ao usuário qual vale e registre a decisão em
  `state.md`.
