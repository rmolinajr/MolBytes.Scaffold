# Histórico das rodadas

`.project/historico.md` responde **quando e por que** o sistema mudou: uma
entrada curta por rodada, para achar uma mudança antiga sem abrir fase por
fase. O mapa do código diz onde está cada coisa; a spec diz como o sistema
funciona; o histórico diz quando e por que mudou. O detalhe de cada rodada
continua nos arquivos dela (`.project/<fase>/` depois de arquivada, a raiz
enquanto é a rodada atual).

Não é o `state.md` (estado da rodada atual, reescrito a cada estágio) nem o
CHANGELOG do cliente (documentação do sistema, que segue `alteracao.md`).

## Formato

Entrada mais nova no topo, logo abaixo do título, para quem lê só o começo
do arquivo:

```markdown
# Histórico

## fase3 — 2026-11-12 — concluído
Pedido: aceitar PIX no checkout
Modo: alteração · commits a1b2c3d..e4f5g6h
Mudou: Pagamentos (provedor PIX novo), Pedidos (status "aguardando PIX")
Decisões: webhook com assinatura HMAC; QR expira em 30 min
Fora / dívida: estorno PIX (fora do MVP); TD-004
Premissas abertas: P-02 (prazo de compensação, confirmar com o suporte)

## fora do pipeline — 2026-11-03
Commits: 9f8e7d6..a1b2c3d (3 commits)
Áreas: Relatórios (filtro por loja), Pedidos
```

Regras:

- Até ~10 linhas por entrada. Nada de código, segredo ou dado pessoal.
- Áreas com os nomes de "Módulos" do `mapa-codigo.md`, para a busca achar as
  duas coisas pelo mesmo nome.
- Decisões são as que valem para as próximas rodadas (de "Decisões que valem
  para os próximos estágios" do `state.md` e das mudanças que o usuário pediu
  na spec), não o passo a passo.
- No cabeçalho, o resultado do gate: `concluído` ou `concluído com
  pendências`. Com pendências, a linha `Pendências:` resume quais.
- Commits: do `base_commit` (no modo novo, o primeiro commit) ao último
  commit de código da rodada.
- Entradas antigas não se reescrevem; a única exceção é a linha
  `Depois do gate:` da rodada atual (abaixo).

## Quem escreve e quando

Você (sessão principal), sem subagente: os dados já estão nos resumos.

- **Fim do estágio 11**, depois do `pipeline-report.md`: a entrada da rodada,
  a partir do relatório e do `state.md`. Entra no commit final.
- **Depois do gate**, quando houver correção de teste manual: acrescente à
  entrada da rodada a linha `Depois do gate:` com os `FIX-MANUAL-<n>` e o que
  cada um corrigiu, em poucas palavras. Entra no commit do fix.
- **Começo de rodada nova** (modo alteração), se a atualização do mapa achar
  diff desde o `Commit:` dele: a entrada `fora do pipeline`, com os commits e
  as áreas que o diff toca. Assim o que alguém mudou à mão também fica
  registrado.

## Quem lê

- **Começo de rodada nova:** você lê as 3 entradas do topo (não o arquivo
  inteiro) e diz ao usuário, em uma linha, a última rodada e o que ficou
  pendente.
- **Estágio 2:** o architect busca no histórico as áreas que a alteração
  toca. Se a alteração muda uma decisão registrada, a spec diz qual, de que
  fase e por que muda; o usuário vê isso na aprovação da spec.

## Projeto com fases de antes do histórico

Sem `historico.md`, mas com fases em `.project/<fase>/`: no começo da rodada
nova, proponha montá-lo ("Há N fases sem histórico. Monto uma entrada por
fase a partir dos relatórios?"). Com o sim, uma entrada por fase, a partir do
`pipeline-report.md` e do `state.md` de cada uma (busca e trechos, não os
arquivos inteiros); o que não estiver lá fica de fora, sem inventar. Commit
`scaffold(0): histórico das fases anteriores`.

## Arquivamento

O histórico fica na raiz da pasta de documentos, como a `spec.md` e o mapa,
e nunca vai para `.project/<fase>/`.
