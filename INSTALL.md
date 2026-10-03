# Instalar molbytes.scaffold (Claude Code) — v0.5

A skill são arquivos Markdown que o Claude Code lê. Há três formas de instalar.

## Opção 1 — plugin (recomendado)

No Claude Code:

    /plugin marketplace add rmolinajr/MolBytes.Scaffold
    /plugin install molbytes@molbytes

Para atualizar depois: `/plugin marketplace update molbytes`.

Como plugin, o comando fica `/molbytes:molbytes-scaffold` e os subagentes
aparecem como `molbytes:scaffold-*` em `/agents`.

## Opção 2 — cópia manual em todos os projetos

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

## Opção 3 — só num projeto

Copie a pasta `.claude` para a raiz do projeto
(ex.: `<pasta-do-projeto>/.claude/`).
Vantagem: a skill vai junto no git do projeto.

## Usar

1. Abra o Claude Code na pasta do projeto.
2. Confira que os subagentes aparecem: `/agents`.
3. Rode (como plugin, use `/molbytes:molbytes-scaffold`):

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

Como plugin, basta reinstalar pelo marketplace. Na cópia manual, faça backup
de `~/.claude/skills/` e `~/.claude/agents/`.

## Status

v0.5, ainda não testada numa execução real. Espere ajustes depois do primeiro
projeto. Ajuste modelos em `references/model-routing.md` com base em
`.project/model-log.md`.

Histórico de versões: [CHANGELOG.md](CHANGELOG.md).

## Pré-requisito: imagens Docker

Com o Docker Desktop aberto, baixe uma vez (PowerShell):

    docker pull zricethezav/gitleaks:latest
    docker pull semgrep/semgrep
    docker pull aquasec/trivy

Isso continua não substituindo um pentest profissional antes de processar
pagamentos reais.

---

molbytes.scaffold é um produto [MolBytes](https://www.molbytes.io), criado por
Roberto Molina.
