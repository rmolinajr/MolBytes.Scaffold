# Roteamento de modelos

O Claude Code escolhe o modelo de um subagente nesta ordem:
1. parâmetro `model` passado na chamada do Agent tool;
2. campo `model` no frontmatter do subagente;
3. variável de ambiente `CLAUDE_CODE_SUBAGENT_MODEL`;
4. modelo da sessão principal.

O orquestrador usa o item 1 quando precisa escolher em tempo real (estágio 7)
e deixa o item 2 como padrão seguro para o resto.

## Padrão por estágio

| Estágio | Padrão | Econômico | Por quê |
|---------|--------|-----------|---------|
| 1 grill-me | sessão principal | sessão principal | conversa com o usuário |
| 2 to-spec | opus | sonnet | decisões de arquitetura; erro aqui se propaga |
| 3 risks | opus | sonnet | exige ver o que não é óbvio |
| 4 design | sonnet | sonnet | trabalho estruturado |
| 5 tickets | sonnet | sonnet | decomposição da spec |
| 6 assign | haiku | haiku | classificação simples |
| 7 implement | por ticket (abaixo) | sonnet em tudo | depende da complexidade |
| 8 tests: plano e execução | sonnet | sonnet | escrever e rodar testes |
| 8 tests: correção de falha | modelo do ticket; opus na 2ª tentativa | sonnet; opus na 2ª | corrigir sem afrouxar o teste |
| 9 security: audit, triage, verify | opus | opus | auditor precisa ser o mais forte |
| 9 security: fix | opus | opus | correção de segurança não pode ser superficial |
| 10 code-review | opus | sonnet | segurança já foi auditada no 9 |
| 11 final | sessão principal | sessão principal | só roda ferramentas e testes |

O estágio 9 continua em opus mesmo no modo econômico: é o filtro de segurança.

## Estágio 7: escolha por ticket

O `scaffold-router` marca cada ticket com `complexity` e `model`. Regras:

**opus** só se a lógica **do próprio ticket** implementa um destes (lista
fechada; use o item como `motivo`):
- `dinheiro`: cálculo ou movimento de dinheiro, cobrança, estorno, idempotência de pagamento
- `auth`: regra de autenticação ou autorização (login, sessão, tokens, permissões, políticas de acesso por tenant)
- `cripto`: criptografia, assinatura, segredos
- `offline`: sincronização offline e resolução de conflitos
- `concorrencia`: travas, filas com ordem ou idempotência, transação com várias tabelas sob concorrência
- `migracao-dados`: migração que transforma dados existentes

Só **usar** algo pronto (ler dados de um tenant pelo repositório que já filtra,
chamar um serviço de auth existente, gravar dado pessoal com o padrão do
projeto) não é motivo para opus: é sonnet.

**haiku** se o ticket é só:
- arquivos de configuração, README, `.env.example`
- CRUD trivial copiando um padrão já existente no repo
- ajustes de estilo/CSS sem lógica

**sonnet** para todo o resto (padrão). Na dúvida, sonnet: o escalonamento
automático sobe para opus se os testes falharem.

**Limite:** opus em mais de 25% dos tickets indica classificação frouxa. Nesse
caso, o router lista os tickets em opus com o motivo, e o orquestrador mostra a
lista ao usuário no estágio 6.

## Escalonamento automático

- Se um implementador em sonnet ou haiku entregar um ticket cujos testes falham
  duas vezes seguidas, reexecute o ticket com `model: opus`.
- Se o reviewer (estágio 10) apontar problema crítico num arquivo, a correção é
  feita em opus.
- Registre toda escalada em `.project/model-log.md` (ticket, modelo inicial,
  modelo final, motivo). Isso serve para ajustar esta tabela com dados reais.

## Ajuste

Esta tabela é ponto de partida. Depois de 2-3 projetos, revise
`.project/model-log.md`: tickets que sempre escalam para opus devem virar opus
direto; estágios em opus que nunca acham nada podem descer para sonnet.
