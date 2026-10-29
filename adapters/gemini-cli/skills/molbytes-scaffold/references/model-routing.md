# Roteamento de modelos

O pipeline escolhe **níveis**, não nomes de modelo: `leve`, `medio` e `forte`.
Cada plataforma traduz o nível para um modelo dela (tabela "Níveis" em
`references/plataformas.md`). No Claude Code: leve = haiku, medio = sonnet,
forte = opus. Em arquivos antigos ou extensões, `haiku`, `sonnet` e `opus`
valem como esses níveis.

Ao lançar um subagente, passe o modelo do nível de forma explícita, do jeito
que a plataforma permite (por chamada ou pela definição do agente; ver
`plataformas.md`). Nunca deixe um subagente herdar o modelo da sessão por
acaso.

## Padrão por estágio

| Estágio | Padrão | Econômico | Por quê |
|---------|--------|-----------|---------|
| 1 grill-me | sessão principal | sessão principal | conversa com o usuário |
| mapa do código (gerar e atualizar) | medio | medio | `scaffold-architect` lê estrutura e diff, não decide nada |
| 2 to-spec | forte | medio | decisões de arquitetura; erro aqui se propaga |
| 3 risks | forte | medio | exige ver o que não é óbvio |
| 3 sondagem das premissas | medio | medio | `scaffold-tester` faz chamadas de teste e registra o que viu |
| 4 design | medio | medio | trabalho estruturado |
| 5 tickets | medio | medio | decomposição da spec |
| 6 assign | leve | leve | classificação simples |
| 7 implement | por ticket (abaixo) | medio em tudo | depende da complexidade |
| 8 tests: plano e execução | medio | medio | escrever e rodar testes |
| 8 tests: correção de falha | o mais alto entre os tickets de `origem` (sem ticket: medio); forte na 2ª tentativa | medio; forte na 2ª | corrigir sem afrouxar o teste |
| 9 security: audit, triage, verify | forte | forte | auditor precisa ser o mais forte |
| 9 security: fix | forte | forte | correção de segurança não pode ser superficial |
| 10 code-review | forte | medio | segurança já foi auditada no 9 |
| 10 impacto fora do diff (modo alteração) | forte | medio | achar o que o diff não mostra |
| 11 final: testes | medio | medio | `scaffold-tester` roda a suíte e o plano |
| 11 final: rescan | medio; forte para triar achado novo | igual | só ferramentas; triagem exige o auditor forte |
| 11 final: gate e relatório | sessão principal | sessão principal | lê só resumos |
| depois do gate: correção de teste manual | medio; forte na 2ª tentativa | igual | defeito achado pela pessoa ou na conta real |

O estágio 9 continua em forte mesmo no modo econômico: é o filtro de segurança.

## Estágio 7: escolha por ticket

O `scaffold-router` marca cada ticket com `complexity` e `model` (o nível). Regras:

**forte** só se a lógica **do próprio ticket** implementa um destes (lista
fechada; use o item como `motivo`):
- `dinheiro`: cálculo ou movimento de dinheiro, cobrança, estorno, idempotência de pagamento
- `auth`: regra de autenticação ou autorização (login, sessão, tokens, permissões, políticas de acesso por tenant)
- `cripto`: criptografia, assinatura, segredos
- `offline`: sincronização offline e resolução de conflitos
- `concorrencia`: travas, filas com ordem ou idempotência, transação com várias tabelas sob concorrência
- `migracao-dados`: migração que transforma dados existentes

Só **usar** algo pronto (ler dados de um tenant pelo repositório que já filtra,
chamar um serviço de auth existente, gravar dado pessoal com o padrão do
projeto) não é motivo para forte: é medio.

**leve** se o ticket é só:
- arquivos de configuração, README, `.env.example`
- CRUD trivial copiando um padrão já existente no repo
- ajustes de estilo/CSS sem lógica

**medio** para todo o resto (padrão). Na dúvida, medio: o escalonamento
automático sobe de nível se os testes falharem.

**Limite:** forte em mais de 25% dos tickets indica classificação frouxa. Nesse
caso, o resumo de `scripts/ondas.py` lista os tickets em forte com o motivo, e
o orquestrador mostra a lista ao usuário no estágio 6.

## Escalonamento automático

Quem relança é você (orquestrador): o implementador anterior já encerrou.

- **Testes do ticket falharam:** relance uma vez no mesmo modelo, com a saída
  filtrada das falhas no prompt. Falhou de novo: suba um nível
  (leve→medio→forte).
- **`TRAVADO:` ou parado pelo usuário:** suba um nível direto, com o erro no
  prompt (ver `watchdog.md`).
- **Falhou em forte:** o ticket vira pendência (ver `watchdog.md`).
- **Correção de item do plano de teste (estágio 8):** regra própria em
  `plano-de-teste.md` (2ª tentativa em forte).
- **Crítico do code review (estágio 10):** correção em forte.
- Registre toda escalada em `.project/model-log.md` (formato abaixo). Isso
  serve para ajustar esta tabela com dados reais.

## `model-log.md`

Formato fixo: ferramentas leem estas tabelas para calibrar o roteamento.
Crie o arquivo no estágio 6 com as três seções, mesmo vazias; acrescente
linhas, nunca mude os cabeçalhos. Níveis como `leve`, `medio` e `forte`; um
ticket por linha.

```markdown
# Model log

## Estágio 6: correções do orquestrador

| Ticket | Router | Final | Motivo |
|---|---|---|---|

## Escaladas

| Ticket | Inicial | Final | Motivo |
|---|---|---|---|

## Reexecuções

| Ticket | Nível | Motivo |
|---|---|---|
```

- **Estágio 6:** todo nível que você ou o usuário mudarem depois do router
  (ex.: "rebaixe" na pausa do plano, com motivo `pedido do usuário`).
- **Escaladas:** toda subida de nível do estágio 7 em diante (testes falharam
  duas vezes, `TRAVADO:`, 2ª tentativa em forte); `Final` é o nível com que o
  ticket terminou.
- **Reexecuções:** relançamento no mesmo nível (`watchdog.md`).

Observações livres (pendências, ocorrências) vão depois das tabelas, em
seções próprias.

## Ajuste

Esta tabela é ponto de partida. Depois de 2-3 projetos, revise
`.project/model-log.md`: tickets que sempre escalam para forte devem virar forte
direto; estágios em forte que nunca acham nada podem descer para medio.
