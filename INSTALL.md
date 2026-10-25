# Installing molbytes.scaffold

**English** · [Português (Brasil)](INSTALL.pt-BR.md)

The skill is a set of Markdown files that the agent reads. It works in
[Claude Code](#claude-code), [Codex](#codex), [Gemini CLI](#gemini-cli)
and [Cursor](#cursor). The pipeline is the same; what changes is the
installation and each platform's commands (table in
`references/plataformas.md`).

The skill's instructions, its in-pipeline commands (`continuar`, `aprovado`),
its flags and the files it creates are in Brazilian Portuguese. You can
describe your project in English.

## Claude Code

There are three ways to install it.

### Option 1 — plugin (recommended)

In Claude Code:

    /plugin marketplace add rmolinajr/MolBytes.Scaffold
    /plugin install molbytes@molbytes

To update later: `/plugin marketplace update molbytes`.

As a plugin, the command is `/molbytes:molbytes-scaffold` and the subagents
show up as `molbytes:scaffold-*` (check under `/plugin` → Installed → molbytes).

### Option 2 — manual copy for all projects

Copy the `skills/` and `agents/` folders from this repository into your user's
`.claude` folder (`%USERPROFILE%\.claude\` on Windows, `~/.claude/` on
macOS/Linux).

Expected result:

    ~/.claude/skills/molbytes-scaffold/SKILL.md
    ~/.claude/skills/molbytes-scaffold/references/   (10 .md files)
    ~/.claude/agents/scaffold-*.md   (8 files)

If `~/.claude/agents/` already exists, just add the files.

The subagents don't depend on where the skill is installed: the orchestrator
pastes into each one's prompt the rules it needs (the implementer reads its
own from `.project/regras-implementacao.md`, written once).

### Option 3 — a single project only

Copy the `skills/` and `agents/` folders into `.claude/` at the project root
(e.g. `<project-folder>/.claude/skills/` and `.claude/agents/`).
Advantage: the skill travels with the project's git.

### Use

1. Open Claude Code in the project folder.
2. Check that the subagents were loaded: under `/plugin` → Installed, or ask
   Claude "list the available scaffold subagents".
3. Run it (as a plugin, use `/molbytes:molbytes-scaffold`):

       /molbytes-scaffold POS system for restaurants: terminal, kitchen, admin, offline-first, Stripe and PIX

4. Answer the grill-me, approve the spec, approve the implementation plan
   (stage 6) and approve the code review at the end.

To change a system that already exists, open Claude Code in its folder and
describe the change (e.g. `/molbytes-scaffold Change: accept PIX at
checkout`). The skill looks for the system's documentation; if it can't find
it, it asks whether there is some elsewhere. If there is, it is updated along
with the code; if there isn't, only the system is changed.

**Run the main session on sonnet, with medium effort** (`/model sonnet`). It
is the decision that weighs most on cost: the main session rereads the whole
context at every step, and the heavy stages already go to opus through the
subagents. In a real run with the main session on opus, it spent more than
all the subagents put together. The same holds on every platform: main
session on the medium model.

## Codex

Adapter new in v0.14.0, not yet tested on a real project in Codex. Copy the
skill and the subagents (bash; on Windows, Git Bash):

    git clone https://github.com/rmolinajr/MolBytes.Scaffold.git
    mkdir -p ~/.agents/skills ~/.codex/agents
    cp -r MolBytes.Scaffold/skills/molbytes-scaffold ~/.agents/skills/
    cp MolBytes.Scaffold/adapters/codex/agents/*.toml ~/.codex/agents/

For a single project, use `.agents/skills/` and `.codex/agents/` at its root.
Alternative for the skill: `codex plugin marketplace add rmolinajr/MolBytes.Scaffold`
(the subagents still need copying: Codex plugins don't ship agents).

Use: open Codex in the project folder and run

    $molbytes-scaffold POS system for restaurants: terminal, kitchen, admin, offline-first, Stripe and PIX

The subagents don't pin a model: the orchestrator passes the one for each
tier (`gpt-6-luna`, `gpt-6.1-sol`, `gpt-6-astra`). If you want others, say so
at the start; the skill records the choice in `state.md`. To write documents
outside the project, open Codex with `--add-dir <folder>`. In stage 9 Codex
asks for approval to run Docker outside the sandbox.

## Gemini CLI

Adapter new in v0.14.0, not yet tested on a real project in Gemini CLI. Since
June 2026 Gemini CLI only serves paid API keys and Code Assist
Standard/Enterprise; Google is replacing it with the Antigravity CLI, which
imports the extension with `agy plugin import gemini`.

The extension lives in `adapters/gemini-cli/` (skill, command and subagents):

    git clone https://github.com/rmolinajr/MolBytes.Scaffold.git
    gemini extensions install ./MolBytes.Scaffold/adapters/gemini-cli

To update: `git pull` in the clone and install again.

Use: open Gemini CLI in the project folder and run

    /molbytes-scaffold POS system for restaurants: terminal, kitchen, admin, offline-first, Stripe and PIX

Gemini CLI doesn't choose a model per call, so there is one subagent per tier
(`scaffold-implementer-leve`, `-medio`, `-forte` etc., on `flash-lite`,
`flash` and `pro`). Check with `/agents list`. To write documents outside the
project: `/directory add <folder>`.

## Cursor

Adapter new in v0.14.0, not yet tested on a real project in Cursor.

- **Plugin:** in the editor, `/add-plugin` (or the Marketplace panel) with the
  URL `https://github.com/rmolinajr/MolBytes.Scaffold`. In the CLI:
  `agent plugin marketplace add https://github.com/rmolinajr/MolBytes.Scaffold`
  and then `/plugin`.
- **Manual copy:**

      git clone https://github.com/rmolinajr/MolBytes.Scaffold.git
      mkdir -p ~/.cursor/skills ~/.cursor/agents
      cp -r MolBytes.Scaffold/skills/molbytes-scaffold ~/.cursor/skills/
      cp MolBytes.Scaffold/adapters/cursor/agents/*.md ~/.cursor/agents/

Cursor also reads `~/.claude/skills/` and `~/.claude/agents/` (Settings →
Agents → Third-Party Imports). If you already have the Claude Code manual
copy, the skill shows up in Cursor; agents in `~/.cursor/agents/` take
precedence over those in `~/.claude/agents/`.

Use: `/molbytes-scaffold <description>` in the agent chat. The subagents use
`model: inherit`; the orchestrator states each tier's model when it launches
them. To write documents outside the project, add the folder to the
workspace.

## Where the documents live

At the start of a new project, the skill asks where to keep the documents
(spec, design, tickets, reports):

1. **Inside the project**, in `.project/` (default).
2. **In another folder**, so documents don't mix with the client's code.
   You choose the parent folder (e.g. `D:\Clients`) and the skill creates
   `<parent-folder>/<project-name>/`.

**The documents folder must be in git so nothing is lost.** With option 2,
the skill runs `git init` in it and commits once per stage. Local git doesn't
protect against disk loss: set up a private remote for it (e.g. a private
GitHub repository) and push.

So that Claude Code doesn't ask for permission for every file written outside
the project, authorize the parent folder once in `~/.claude/settings.json`
(on the other platforms, see their section above):

```json
{
  "permissions": {
    "additionalDirectories": ["D:/Clients"]
  }
}
```

or use `/add-dir D:\Clients` in the session.

The link between project and documents is kept in `~/.molbytes/projetos.json`,
outside the client's project. If the folder is moved or deleted, the skill
says where it looked and asks where the documents are.

## Cost

- Main session on **sonnet with medium effort** (on the other platforms, the
  medium model): orchestrating doesn't need more, and the main session's
  reasoning counts as output, the most expensive token.
- **One session per cycle** (a new project or each change): `state.md` lets
  you resume in a new session without losing anything; a conversation that
  lasts for days gets expensive.
- **Process plugins** (e.g. `superpowers`) compete with the pipeline and add
  extra steps. Turn them off only in the project where the pipeline runs, in
  `.claude/settings.local.json` (not committed to git):

  ```json
  { "enabledPlugins": { "superpowers@claude-plugins-official": false } }
  ```

- Plugins and skills you don't use go into the context of every session:
  turn them off.

## Context compaction (Claude Code, once)

Run in Claude Code:

    /autocompact 200k

This compacts the conversation when it reaches ~200k tokens, as a safety net
(a large context is reread at every step and makes everything more
expensive). It is saved in your settings for future sessions. To go back to
the default: `/autocompact auto`.

On top of that, at the end of stages 2, 5, 8 and 9 and after each wave of
stage 7, the skill tells you it is a good moment to restart the session. The
cheapest way is `/clear` followed by `/molbytes:molbytes-scaffold continuar`
(manual copy: `/molbytes-scaffold continuar`): the session comes back light
and the skill resumes from the `state.md` in the documents folder.
`/compact` followed by `continuar` also works, but it rereads the whole
conversation to summarize it. The same `/molbytes:molbytes-scaffold continuar`
resumes on another day.

On the other platforms, the equivalent commands are in
`references/plataformas.md`.

## Backup (before reformatting your PC)

As a plugin, just reinstall from the marketplace. With the manual copy, back
up `~/.claude/skills/` and `~/.claude/agents/`. If you use an external
documents folder, also back up `~/.molbytes/projetos.json` (or just answer
where the documents are when the skill asks).

## Status

v0.17.0, evolving: the changes from v0.10 onward came from real runs in
Claude Code. Expect adjustments with each project. Tune models in
`references/model-routing.md` based on `.project/model-log.md`.

Version history: [CHANGELOG.md](CHANGELOG.md) (in Portuguese).

## Prerequisite: Docker images

With Docker Desktop running, pull these once (PowerShell):

    docker pull zricethezav/gitleaks:v8.30.1
    docker pull semgrep/semgrep:1.178.0
    docker pull aquasec/trivy:0.74.0
    docker pull python:3.12-slim

These are the versions pinned in `references/security.md` (part C). The
project is mounted read-only in the containers, and semgrep runs without
sending metrics.

The stage 6 waves come from `scripts/ondas.py` (Python 3.8+, standard library
only). Without Python installed, the skill runs the script in the
`python:3.12-slim` image above; with neither, the orchestrator builds the
waves and checks them against a checklist.

This still does not replace a professional pentest before processing real
payments.

## Recommended (optional)

The pipeline works on its own; nothing below is a dependency. These are
add-ons for before or after it:

| Add-on | When it helps |
|---|---|
| `frontend-design` | Stage 7, frontend tickets: turns the designer's wireframes into a polished interface. |
| `superpowers` | After the pipeline: guided debugging, TDD and verification before calling something done, for when a ticket gets stuck or a bug shows up. |
| `/security-review` and `/code-review` | On PRs after delivery: they review each new change. They come with Claude Code. |

Both plugins are in Anthropic's official marketplace:

    /plugin install frontend-design@claude-plugins-official
    /plugin install superpowers@claude-plugins-official

If the marketplace isn't added: `/plugin marketplace add anthropics/claude-plugins-official`.

Not recommended alongside it: a full `grill-me` skill (stage 1 already runs
the interview in the format `qa.json` expects) and session-memory plugins
(they duplicate the role of `.project/state.md` + git when resuming).

---

molbytes.scaffold is a [MolBytes](https://www.molbytes.io) product, created by
Roberto Molina.
