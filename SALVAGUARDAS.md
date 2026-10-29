# Salvaguardas

Cada regra que protege uma rodada, onde ela está e quanto ela segura. Uma
regra vale o que vale o mecanismo que a aplica: uma frase no prompt pode ser
ignorada; um script que para o estágio, não.

## Níveis

Do mais forte para o mais fraco:

| Nível | Quem aplica | Um agente pode ignorar? |
|---|---|---|
| 🧪 Script | `scripts/ondas.py` ou um comando que o orquestrador roda e cujo resultado decide (ex.: `git diff` vazio) | Não: com erro, o estágio não segue |
| 🔧 Ferramentas | o `tools:` do agente; a plataforma só dá a ele essas ferramentas | Não, onde a plataforma respeita o campo (Claude Code). Nos adaptadores, depende da plataforma |
| 🧭 Pausa | um passo que espera a resposta do usuário | Não: nada anda sem a resposta |
| 📝 Prompt | uma instrução num agente ou numa referência | Sim. O backstop é a revisão ou o gate |

O público não tem hooks: ele roda em quatro plataformas. Uma extensão ou um
plugin da plataforma pode acrescentar um hook (ex.: bloquear a edição de um
teste travado no Claude Code), nunca tirar uma regra daqui.

**Ao propor uma correção do pipeline**, use o nível mais forte que ainda é
barato: script, depois ferramentas, depois pausa, e prompt por último. Regra
que já estava escrita e foi quebrada pede um nível mais forte, não mais texto.

## Testes

| Regra | Nível | Onde |
|---|---|---|
| Os testes travam no fim do 8.2: commit, `testes-travados.txt` e o sha em `Testes travados:` do `state.md`, tirado do git, não do relato de um agente | 🧪 Script | `plano-de-teste.md`, "Trava dos testes" |
| Depois de cada correção, `git diff --name-only <Testes travados>` nos travados; mudança sem o sim do usuário vai a ele (aceitar ou desfazer) | 🧪 Script → 🧭 Pausa | `plano-de-teste.md` |
| O gate exige o mesmo diff vazio | 🧪 Script | `stages.md`, estágio 11 |
| O implementador não edita teste travado: responde `TESTE ERRADO:` | 📝 Prompt | `agents/scaffold-implementer.md` |
| O reviewer confere o diff dos travados, skip novo, exclusão no runner, fixture mudada | 📝 Prompt | `agents/scaffold-reviewer.md` |
| Correção de segurança começa por um teste que reproduz a falha e falha | 📝 Prompt | `agents/scaffold-implementer.md`, `security.md` |
| Testes unitários sem banco real, porta fixa ou serviço externo (implementadores em paralelo) | 📝 Prompt | `agents/scaffold-implementer.md` |
| Modo alteração: teste que já falhava no ponto de partida não bloqueia; falha nova bloqueia | 🧪 Script | `alteracao.md` |

## Planejamento e ondas

| Regra | Nível | Onde |
|---|---|---|
| Índice sem id duplicado, dependência que não existe ou ciclo | 🧪 Script | `scripts/ondas.py` |
| Todo requisito de segurança está em `security_reqs` de algum ticket, e nenhum ticket cita um que não existe | 🧪 Script | `scripts/ondas.py` |
| Classificação sem ticket faltando, inventado ou repetido, nível inválido ou forte sem motivo | 🧪 Script | `scripts/ondas.py` |
| Na mesma onda, nenhum arquivo (nem diretório e algo dentro dele) em dois tickets | 🧪 Script | `scripts/ondas.py` |
| Forte acima de 25%: a lista vai ao usuário | 🧪 Script → 🧭 Pausa | `scripts/ondas.py`, estágio 6 |
| Spec aprovada (2), custo aprovado (6, menos com `--pequeno`), code review (10), premissa negada (3) | 🧭 Pausa | `stages.md` |
| Planner, router e designer não rodam comandos | 🔧 Ferramentas | `tools:` dos agentes |
| Spec até ~30 mil caracteres, ticket até ~4 mil, ciclo até ~30 tickets | 📝 Prompt | `stages.md` |

## Escopo do código

| Regra | Nível | Onde |
|---|---|---|
| O implementador mexe só nos arquivos do ticket; outro arquivo, ele para e pede | 📝 Prompt | `agents/scaffold-implementer.md` |
| Manifestos de dependência só no `INFRA-000` ou em ticket de infra; pacote novo, ele pede | 📝 Prompt | `agents/scaffold-implementer.md`, estágio 5 |
| Só o orquestrador faz commit, um por estágio ou onda | 📝 Prompt | `SKILL.md` |
| Worktree e branch de tentativa saem sem `--force`; no fim, `git worktree list` só com a pasta do projeto | 📝 Prompt + 🧪 Script no gate | estágios 7 e 11 |
| Reviewer e auditor não editam código (sem `Edit`) | 🔧 Ferramentas | `tools:` dos agentes |

## Segurança

| Regra | Nível | Onde |
|---|---|---|
| `.gitignore` com `.env` e `security/raw/` antes do primeiro commit | 📝 Prompt | `SKILL.md`, regras gerais |
| Regras de código seguro (segredo por variável de ambiente, SQL parametrizado, autorização no servidor...) | 📝 Prompt | `agents/scaffold-implementer.md`, `security.md` parte B |
| Estágio 9: gitleaks, semgrep e as ferramentas da stack, com o histórico do git | 🧪 Script | `security.md` parte C |
| Achado médio: corrigir ou aceitar, com o motivo em `accepted.md` | 🧭 Pausa | estágio 9 |
| A correção é conferida pelo auditor, não pelo implementador; 2 tentativas e depois o usuário | 🧭 Pausa | estágio 9.4 |
| Gate: nenhum crítico ou alto aberto; todo médio aberto está aceito | 🧪 Script | estágio 11 |
| Sondagem só em conta de teste, credencial por variável ou cofre, chamadas reversíveis | 📝 Prompt | `agents/scaffold-tester.md`, estágio 3 |
| Impacto fora do diff só lê e roda testes; nunca banco ou serviço de verdade | 📝 Prompt | `agents/scaffold-reviewer.md` |

## Modo alteração

| Regra | Nível | Onde |
|---|---|---|
| Ponto de partida: sem git, commit local; com mudança não commitada, o usuário escolhe antes de começar | 🧭 Pausa | `alteracao.md` |
| O mapa do código cobre o código: diff do `Commit:` dele até o `HEAD` vazio | 🧪 Script | gate, `mapa-codigo.md` |
| Todo documento da "Documentação afetada" atualizado | 🧪 Script | gate, `alteracao.md` |
| Todo `bug` do `impacto.md` corrigido; todo `não provado` de impacto alto corrigido ou aceito | 🧪 Script + 🧭 Pausa | estágios 10 e 11 |

## Execução

| Regra | Nível | Onde |
|---|---|---|
| Todo subagente com modelo explícito | 📝 Prompt | `SKILL.md`, `plataformas.md` |
| Todo subagente no `runs.log`, com orçamento de tempo; travado ou parcial vira ação | 📝 Prompt | `watchdog.md` |
| Limite de turnos por agente | 🔧 Ferramentas | `maxTurns` dos agentes |
| Escalada: teste do ticket falhou 2 vezes, nível acima; falhou em forte, vira pendência e o usuário é avisado | 📝 Prompt | `model-routing.md`, `watchdog.md` |
| Extensão não remove estágio, pausa, roteamento explícito nem o gate | 📝 Prompt | `extensoes.md` |

## Falhas conhecidas

| Falha | Por quê | Backstop |
|---|---|---|
| Tudo que é 📝 pode ser ignorado por um agente | O público não tem hooks | Code review, conferências e gate |
| O implementador pode editar fora dos arquivos do ticket | Não há script que compare o diff com `arquivos` | Code review; conflito entre tickets no `ondas.py` |
| Reviewer e auditor têm `Write`: podem gravar fora dos relatórios | Precisam gravar os relatórios | Diff da rodada no gate e no code review |
| Um segredo commitado no meio da rodada só aparece no estágio 9 | Não há varredura a cada commit | gitleaks lê o histórico; rescan no 11 |
| Texto de documento, ticket, página ou resposta de serviço é lido como texto comum: um texto feito para isso pode desviar um agente | Aceito por enquanto | Pausas e gate; o agente não tem credencial de produção |
