# Plataformas

O pipeline é o mesmo em todas as plataformas. Muda só o mecanismo: como lançar
um subagente com o modelo certo, se ele roda em paralelo, como recomeçar a
sessão. Leia só a seção da sua plataforma. Se não souber em qual está,
pergunte ao usuário.

## Níveis de modelo

| Nível | Claude Code | Codex | Gemini CLI | Cursor |
|---|---|---|---|---|
| `leve` | `haiku` | `gpt-6-luna` | `flash-lite` | o menor da família em uso (ex.: Claude Haiku, GPT Luna) |
| `medio` | `sonnet` | `gpt-6.1-sol` | `flash` | o intermediário (ex.: Claude Sonnet, GPT Sol) |
| `forte` | `opus` | `gpt-6-astra` | `pro` | o mais forte (ex.: Claude Opus, GPT Astra) |

Nomes de modelo mudam com frequência. Se a plataforma recusar um nome, ou se
o usuário preferir outros, pergunte uma vez quais modelos usar em cada nível
e grave em `state.md` (`Modelos: leve=..., medio=..., forte=...`). Essa linha,
quando existe, vale mais que a tabela.

## Claude Code

- **Lançar:** ferramenta Agent, `subagent_type` = `scaffold-*` (com ou sem o
  prefixo `molbytes:`), parâmetro `model` = `haiku`, `sonnet` ou `opus`.
- **Paralelo:** várias chamadas na mesma mensagem; no estágio 7, com
  `run_in_background: true`. O aviso de término chega sozinho.
- **Tokens:** o resultado do subagente (ou o aviso de término, em segundo
  plano) traz o uso dele, com `total_tokens`; é esse número que vai no END do
  `runs.log`.
- **Limite de turnos:** `maxTurns` no frontmatter de cada agente (já vem
  definido).
- **Tarefas em execução:** `/tasks`.
- **Comandos:** sessão limpa `/clear`; compactar `/compact`; modelo
  `/model sonnet`; retomar `/molbytes:molbytes-scaffold continuar` (cópia
  manual: `/molbytes-scaffold continuar`).
- **Pasta fora do projeto:** `permissions.additionalDirectories` em
  `~/.claude/settings.json`, ou `/add-dir <pasta>` na sessão.

## Codex

- **Lançar:** peça ao Codex um subagente pelo nome (`scaffold-architect`
  etc.) e informe o modelo do nível ao lançar. As definições do molbytes
  (`.codex/agents/` ou `~/.codex/agents/`) não fixam modelo, então vale o que
  você passar; sem modelo, o Codex usa `[agents] default_subagent_model` ou o
  modelo da sessão, o que este pipeline não permite.
- **Paralelo:** subagentes lançados juntos rodam em paralelo, e o Codex espera
  todos terminarem antes de responder. Não há segundo plano: `status` e o
  watchdog (camada 2) rodam ao fim de cada onda. O limite de execuções
  simultâneas é `[agents] max_concurrent_threads_per_session`; se a onda for
  maior, lance em lotes.
- **Limite de turnos:** não há. Só o orçamento de tempo do `runs.log` protege
  contra subagente travado.
- **Comandos:** sessão limpa `/new`; compactar `/compact`; modelo `/model`;
  retomar `$molbytes-scaffold continuar`.
- **Pasta fora do projeto:** o sandbox só grava na pasta do projeto. Abra o
  Codex com `--add-dir <pasta>` ou acrescente a pasta em
  `[sandbox_workspace_write] writable_roots` do `~/.codex/config.toml`.
- **Docker (estágio 9):** o sandbox pode bloquear o `docker`. O Codex pede
  aprovação para rodar fora dele: avise o usuário que é esperado.
- **Windows:** o shell é PowerShell; rode os comandos bash de `security.md`
  com `bash -c` (Git Bash).

## Gemini CLI

O Google está trocando o Gemini CLI pelo Antigravity CLI (desde junho de 2026
o Gemini CLI só atende chave de API paga e Code Assist Standard/Enterprise).
O Antigravity importa esta extensão com `agy plugin import gemini`.

- **Agentes por nível:** o Gemini CLI não escolhe modelo por chamada, então a
  extensão traz um agente por nível: `<nome>-<nível>` (ex.:
  `scaffold-implementer-forte`, `scaffold-router-leve`). Para lançar
  `scaffold-implementer` no nível forte, chame `scaffold-implementer-forte`.
  Existem: `scaffold-architect-forte|medio`, `scaffold-designer-medio`,
  `scaffold-planner-medio`, `scaffold-router-leve`,
  `scaffold-implementer-leve|medio|forte`, `scaffold-tester-medio`,
  `scaffold-security-forte|medio`, `scaffold-reviewer-forte|medio`. Nível
  sem agente: use o mais próximo acima e diga ao usuário em uma linha.
- **Lançar:** cada agente é uma ferramenta; chame pelo nome com o prompt.
- **Paralelo:** se várias chamadas no mesmo turno não rodarem em paralelo,
  rode os tickets da onda um por vez (a ordem dentro da onda não importa).
- **Limite de turnos:** `max_turns` e `timeout_mins` na definição de cada
  agente (já vêm definidos).
- **Comandos:** sessão limpa `/clear`; compactar `/compress`; modelo
  `/model set flash`; retomar `/molbytes-scaffold continuar`.
- **Pasta fora do projeto:** `/directory add <pasta>` na sessão, ou abra o
  Gemini CLI com `--include-directories <pasta>`.

## Cursor

- **Lançar:** subagente pelo nome (`scaffold-architect` etc.), informando o
  modelo do nível ao lançar. As definições do molbytes para o Cursor usam
  `model: inherit`, então sem modelo explícito o subagente herda o da sessão,
  o que este pipeline não permite.
- **Paralelo:** várias chamadas na mesma mensagem; no estágio 7, em segundo
  plano quando disponível.
- **Limite de turnos:** não há. Só o orçamento de tempo do `runs.log`.
- **Comandos:** sessão limpa: novo chat (CLI: `/clear`); compactar
  `/summarize`; modelo: seletor de modelo (CLI: `/model`); retomar
  `/molbytes-scaffold continuar`.
- **Pasta fora do projeto:** acrescente a pasta ao workspace.

## Sem subagentes

Se a plataforma não mostrar nenhum agente `scaffold-*`, pare antes do estágio
2 e diga ao usuário para instalar os agentes conforme o INSTALL.md da
plataforma. Não rode os estágios na sessão principal: o roteamento de modelo,
o paralelismo e a separação entre quem corrige e quem verifica dependem dos
subagentes.
