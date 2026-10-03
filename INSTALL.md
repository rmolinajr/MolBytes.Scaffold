# Instalar molbytes.scaffold (Claude Code) — v0.5

Não há script para instalar. A skill são arquivos Markdown que o Claude Code lê.

## Opção A — em todos os projetos (recomendado)

Copie o conteúdo da pasta `.claude` deste ZIP para a pasta `.claude` do seu
usuário (`%USERPROFILE%\.claude\` no Windows, `~/.claude/` no macOS/Linux).

Resultado esperado:

    ~/.claude/skills/molbytes-scaffold/SKILL.md
    ~/.claude/skills/molbytes-scaffold/references/model-routing.md
    ~/.claude/skills/molbytes-scaffold/references/security.md
    ~/.claude/skills/molbytes-scaffold/references/stages.md
    ~/.claude/skills/molbytes-scaffold/references/state-template.md
    ~/.claude/skills/molbytes-scaffold/references/watchdog.md
    ~/.claude/agents/scaffold-*.md   (8 arquivos)

Se já existir `~/.claude/agents/`, só acrescente os arquivos.

Os subagentes não dependem de onde a skill está instalada: o orquestrador cola
no prompt de cada um as regras de que ele precisa.

## Opção B — só num projeto

Copie a pasta `.claude` para a raiz do projeto
(ex.: `<pasta-do-projeto>/.claude/`).
Vantagem: a skill vai junto no git do projeto.

## Usar

1. Abra o Claude Code na pasta do projeto.
2. Confira que os subagentes aparecem: `/agents`.
3. Rode:

       /molbytes-scaffold Sistema PDV para restaurante: terminal, cozinha, admin, offline-first, Stripe e PIX

4. Responda o grill-me, aprove a spec, aprove o plano de implementação
   (estágio 6) e aprove o code review no final.

Sugestão: rode a sessão principal em sonnet (`/model sonnet`). Os estágios
pesados já vão para opus pelos subagentes, então não precisa pagar opus na
conversa inteira.

## Compactação de contexto (uma vez só)

Rode no Claude Code:

    /autocompact 500k

Isso compacta a conversa quando ela chega a ~50% da janela de 1M, como rede de
segurança. Fica salvo nas suas configurações para as próximas sessões. Para
voltar ao padrão: `/autocompact auto`.

Além disso, a skill avisa nos fins dos estágios 2, 5, 7 e 9 que é um bom momento
para `/compact`. Rode, depois digite `continuar`: ela relê `.project/state.md`
e segue de onde parou. Isso também funciona para retomar em outro dia, numa
sessão nova.

## Backup (antes de formatar o PC)

Faça backup de `~/.claude/skills/` e `~/.claude/agents/`, ou guarde este ZIP
no seu drive.

## Status

v0.5, ainda não testada numa execução real. Espere ajustes depois do primeiro
projeto. Ajuste modelos em `references/model-routing.md` com base em
`.project/model-log.md`.

## Novidades da v0.2

- `.project/state.md`: checkpoint atualizado a cada estágio.
- Pontos de compactação sugeridos nos estágios 2, 5 e 7.
- Retomada por `continuar` após /compact ou em sessão nova.
- Recomendação de `/autocompact 500k`.

## Novidades da v0.3

- `maxTurns` em todos os subagentes: o Claude Code encerra quem passar do limite.
- Orçamento de tempo por ticket/estágio, registrado em `.project/runs.log`.
- Aviso quando um subagente passa de 2x o tempo esperado.
- Digite `status` para ver o que está rodando e há quanto tempo.
- Para ver ou parar um subagente: `/agents` (aba Running) ou `/tasks`.
- Reexecução automática um nível de modelo acima quando um agente trava.

## Novidades da v0.4 — segurança

- Modelo de ameaças e dados pessoais (LGPD/RGPD) já na spec; `security_requirements`
  testáveis viram critérios de aceite dos tickets.
- Regras de código seguro para todo implementador.
- Novo estágio 9: audit → triage → fix → verify, com o novo subagente
  `scaffold-security` (opus).
- Achado médio: você decide corrigir ou aceitar o risco (fica registrado).
- Correção sempre começa por um teste que reproduz a falha; verificação feita
  por outro agente; no máximo 2 tentativas por achado.
- Estágio 11: testes finais + rescan rápido + gate (não termina com crítico ou
  alto aberto).

## Novidades da v0.5

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

### Pré-requisito: imagens Docker

Com o Docker Desktop aberto, baixe uma vez (PowerShell):

    docker pull zricethezav/gitleaks:latest
    docker pull semgrep/semgrep
    docker pull aquasec/trivy

Isso continua não substituindo um pentest profissional antes de processar
pagamentos reais.
