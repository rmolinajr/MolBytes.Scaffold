# Watchdog de subagentes

Objetivo: detectar subagente que já deveria ter terminado e continua rodando,
sem gastar tokens vigiando.

## Camada 1 — limite duro (a plataforma aplica, quando tem)

Onde a plataforma permite, cada subagente tem um limite de turnos na
definição dele (`maxTurns` no Claude Code; equivalentes em
`references/plataformas.md`). Ao atingir o limite, a plataforma encerra o
subagente. Sem esse limite na plataforma, a camada 2 é a única proteção. Trate como **parcial** qualquer retorno que não
traga o resumo final pedido (arquivos alterados, comando e resultado dos
testes), mesmo que não venha marcado como tal.

| Subagente | limite de turnos |
|---|---|
| scaffold-router | 10 |
| scaffold-planner | 30 |
| scaffold-designer | 30 |
| scaffold-architect | 40 |
| scaffold-reviewer | 40 |
| scaffold-tester | 50 |
| scaffold-security | 50 |
| scaffold-implementer | 60 |

Valores iniciais. Ajuste com base em `.project/runs.log`.

## Camada 2 — orçamento de tempo (o orquestrador verifica)

Ao lançar cada subagente, registre em `.project/runs.log` (use `date` no shell):

    <inicio ISO> | START | <agente> | <ticket ou estágio> | <nível>/<modelo> | orçamento <min>

Ao receber o resultado:

    <fim ISO> | END | <agente> | <ticket ou estágio> | ok|parcial|travado|falhou | <min reais> | <tokens> tokens

`<tokens>` é o total que a plataforma mostra no resultado do subagente (ou
no aviso de término, em segundo plano); se não mostrar, use `?`. É o dado que
permite calibrar o roteamento por custo, não só por tempo. Grave o END de
cada subagente assim que o resultado ou o aviso dele chegar, antes de tratar
o próximo: numa execução real, os ENDs gravados em lote no fim da onda saíram
com `?` em 36 de 45 linhas, porque o total já não estava à mão.

Orçamento esperado (minutos):

| Tipo | leve | medio | forte |
|---|---|---|---|
| ticket complexidade baixa | 5 | 8 | 10 |
| ticket complexidade média | — | 15 | 20 |
| ticket complexidade alta | — | 25 | 30 |
| estágios 2-6 | 5 | 15 | 20 |
| sondagem das premissas (estágio 3) | — | 20 | — |
| mapa do código: gerar | — | 20 | — |
| mapa do código: atualizar | — | 10 | — |
| estágio 8 | — | 25 | 30 |
| 9.1 audit (ferramentas + revisão) | — | — | 40 |
| 9.3 fix por ticket | — | — | 20 |
| 9.4 verify por ticket | — | — | 15 |
| ticket de correção (FIX-...) | — | 15 | 20 |
| estágio 10 | — | 25 | 30 |
| 11 testes | — | 20 | — |
| 11 rescan | — | 15 | 20 |

**Quando verificar** (nunca em loop, nunca com `sleep`):
- quando qualquer subagente da onda termina;
- ao fim de cada onda do estágio 7;
- quando o usuário digitar `status`.

Não fique perguntando repetidamente se os subagentes terminaram: cada checagem
reenvia a conversa inteira e custa tokens. A plataforma avisa quando um
subagente em segundo plano termina (ou devolve o resultado, quando roda em
primeiro plano).

Em cada verificação, para cada START sem END, calcule o tempo decorrido:
- acima de **1,5x** o orçamento: marque como "lento" no `status`;
- acima de **2x**: avise o usuário:

  > ⚠️ `BE-004` (scaffold-implementer, medio) está rodando há 34 min;
  > o esperado era 15. Veja no painel de tarefas (`/tasks` no Claude Code;
  > nas outras plataformas, ver `plataformas.md`).
  > Se estiver repetindo a mesma coisa, pare ele por lá e me diga `parei BE-004`.

O orquestrador não força a parada de um subagente: quem para é o usuário, pelo
painel de tarefas da plataforma. Os outros subagentes da onda continuam.

## Tratamento do resultado

| Resultado | Ação |
|---|---|
| ok | segue normal |
| parcial (bateu o limite de turnos) | ver `git diff` dos arquivos do ticket; se avançou, continuar **uma vez** de onde parou; se não avançou, tratar como travado |
| `TRAVADO:` (o próprio agente desistiu) ou parado pelo usuário | reexecutar uma vez com o modelo um nível acima (leve→medio→forte), com o erro relatado no prompt |
| falhou de novo em forte | parar o ticket, marcar em `state.md` > Pendências, seguir com os tickets que não dependem dele, e avisar o usuário |

Antes de reexecutar um ticket, descarte alterações parciais dos arquivos dele
para não misturar duas tentativas. `git checkout` sozinho não apaga arquivos
novos, então use os dois:

    git checkout -- <arquivos>
    git clean -fd -- <arquivos>

Confira antes com `git status -- <arquivos>` que só há arquivos do ticket.

Registre toda reexecução em `.project/model-log.md` (tabela "Reexecuções" e,
se o nível subiu, "Escaladas"; formato em `model-routing.md`).

## Comando `status`

Quando o usuário digitar `status`, responda com uma tabela curta:

| Ticket | Agente | Nível/modelo | Rodando há | Orçamento | Situação |
|---|---|---|---|---|---|

seguida do estágio/onda atual. Dados de `.project/runs.log` + `date`.
