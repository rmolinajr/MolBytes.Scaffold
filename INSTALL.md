# Instalar molbytes.scaffold (Claude Code) — v0.10

A skill são arquivos Markdown que o Claude Code lê. Há três formas de instalar.

## Opção 1 — plugin (recomendado)

No Claude Code:

    /plugin marketplace add rmolinajr/MolBytes.Scaffold
    /plugin install molbytes@molbytes

Para atualizar depois: `/plugin marketplace update molbytes`.

Como plugin, o comando fica `/molbytes:molbytes-scaffold` e os subagentes
aparecem como `molbytes:scaffold-*` (confira em `/plugin` → Installed → molbytes).

## Opção 2 — cópia manual em todos os projetos

Copie as pastas `skills/` e `agents/` deste repositório para a pasta `.claude`
do seu usuário (`%USERPROFILE%\.claude\` no Windows, `~/.claude/` no macOS/Linux).

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

Copie as pastas `skills/` e `agents/` para dentro de `.claude/` na raiz do
projeto (ex.: `<pasta-do-projeto>/.claude/skills/` e `.claude/agents/`).
Vantagem: a skill vai junto no git do projeto.

## Usar

1. Abra o Claude Code na pasta do projeto.
2. Confira que os subagentes foram carregados: em `/plugin` → Installed, ou
   pergunte ao Claude "liste os subagentes scaffold disponíveis".
3. Rode (como plugin, use `/molbytes:molbytes-scaffold`):

       /molbytes-scaffold Sistema PDV para restaurante: terminal, cozinha, admin, offline-first, Stripe e PIX

4. Responda o grill-me, aprove a spec, aprove o plano de implementação
   (estágio 6) e aprove o code review no final.

Para alterar um sistema que já existe, abra o Claude Code na pasta dele e
descreva a mudança (ex.: `/molbytes-scaffold Alteração: aceitar PIX no
checkout`). A skill procura a documentação do sistema; se não achar, pergunta
se há em outro lugar. Se houver, ela é atualizada junto com o código; se não
houver, só o sistema é alterado.

**Rode a sessão principal em sonnet** (`/model sonnet`). É a decisão que mais
pesa no custo: a sessão principal relê todo o contexto a cada passo, e os
estágios pesados já vão para opus pelos subagentes. Numa execução real com a
sessão principal em opus, ela gastou mais que todos os subagentes juntos.

## Onde ficam os documentos

No início de um projeto novo, a skill pergunta onde guardar os documentos
(spec, design, tickets, relatórios):

1. **Dentro do projeto**, em `.project/` (padrão).
2. **Em outra pasta**, para não misturar documentos com o código do cliente.
   Você escolhe a pasta-mãe (ex.: `D:\Clientes`) e a skill cria
   `<pasta-mãe>/<nome-do-projeto>/`.

**A pasta de documentos precisa estar em git para não haver perdas.** Na opção
2, a skill roda `git init` nela e faz um commit por estágio. O git local não
protege contra perda do disco: configure um remoto privado para ela
(ex.: um repositório privado no GitHub) e faça push.

Para o Claude Code não pedir permissão a cada arquivo gravado fora do projeto,
autorize a pasta-mãe uma vez em `~/.claude/settings.json`:

```json
{
  "permissions": {
    "additionalDirectories": ["D:/Clientes"]
  }
}
```

ou use `/add-dir D:\Clientes` na sessão.

O vínculo entre projeto e documentos fica em `~/.molbytes/projetos.json`, fora
do projeto do cliente. Se a pasta for movida ou apagada, a skill avisa onde
procurou e pergunta onde estão os documentos.

## Custo

- Sessão principal em **sonnet com esforço médio**: orquestrar não precisa de
  mais, e o raciocínio da sessão principal conta como saída, o token mais caro.
- **Uma sessão por ciclo** (projeto novo ou cada alteração): o `state.md`
  permite retomar numa sessão nova sem perder nada; conversa de dias fica cara.
- **Plugins de processo** (ex.: `superpowers`) competem com o pipeline e geram
  etapas a mais. Desligue só no projeto onde roda o pipeline, em
  `.claude/settings.local.json` (não vai para o git):

  ```json
  { "enabledPlugins": { "superpowers@claude-plugins-official": false } }
  ```

- Plugins e skills que você não usa entram no contexto de toda sessão:
  desligue-os.

## Compactação de contexto (uma vez só)

Rode no Claude Code:

    /autocompact 200k

Isso compacta a conversa quando ela chega a ~200 mil tokens, como rede de
segurança (contexto grande é relido a cada passo e encarece tudo). Fica salvo nas suas configurações para as próximas sessões. Para
voltar ao padrão: `/autocompact auto`.

Além disso, a skill avisa nos fins dos estágios 2, 5, 8 e 9 e a cada onda do 7 que é um bom momento
para `/compact`. Rode, depois digite `continuar`: ela relê o `state.md` da pasta de documentos
e segue de onde parou. Isso também funciona para retomar em outro dia, numa
sessão nova.

## Backup (antes de formatar o PC)

Como plugin, basta reinstalar pelo marketplace. Na cópia manual, faça backup
de `~/.claude/skills/` e `~/.claude/agents/`. Se usa pasta de documentos
externa, faça backup também de `~/.molbytes/projetos.json` (ou apenas responda
onde estão os documentos quando a skill perguntar).

## Status

v0.10, ainda não testada numa execução real. Espere ajustes depois do primeiro
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

## Recomendados (opcional)

O pipeline funciona sozinho; nada abaixo é dependência. São complementos para
antes ou depois dele:

| Complemento | Quando ajuda |
|---|---|
| `frontend-design` | Estágio 7, tickets de frontend: transforma os wireframes do designer em interface com acabamento. |
| `superpowers` | Depois do pipeline: debugging guiado, TDD e verificação antes de dar como pronto, para quando um ticket trava ou surge um bug. |
| `/security-review` e `/code-review` | Nos PRs depois da entrega: revisam cada mudança nova. Já vêm no Claude Code. |

Os dois plugins estão no marketplace oficial da Anthropic:

    /plugin install frontend-design@claude-plugins-official
    /plugin install superpowers@claude-plugins-official

Se o marketplace não estiver adicionado: `/plugin marketplace add anthropics/claude-plugins-official`.

Não recomendados junto: uma skill `grill-me` completa (o estágio 1 já faz a
entrevista no formato que o `qa.json` espera) e plugins de memória de sessão
(duplicam o papel de `.project/state.md` + git na retomada).

---

molbytes.scaffold é um produto [MolBytes](https://www.molbytes.io), criado por
Roberto Molina.
