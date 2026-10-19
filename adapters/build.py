"""Generate the Codex, Gemini CLI and Cursor adapters from the Claude Code sources.

Sources of truth: skills/molbytes-scaffold/ and agents/*.md (Claude Code format),
version from .claude-plugin/plugin.json. Never edit the generated files by hand.

    python adapters/build.py          # regenerate
    python adapters/build.py --check  # exit 1 if anything is out of date
"""
import json
import pathlib
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
ADAPTERS = ROOT / "adapters"
SKILL = ROOT / "skills" / "molbytes-scaffold"
NOTICE = "Gerado por adapters/build.py a partir de agents/{name}.md. Não edite à mão."

# Tiers each agent can run at (model-routing.md, including --economico).
AGENT_TIERS = {
    "scaffold-architect": ["forte", "medio"],
    "scaffold-designer": ["medio"],
    "scaffold-planner": ["medio"],
    "scaffold-router": ["leve"],
    "scaffold-implementer": ["leve", "medio", "forte"],
    "scaffold-tester": ["medio"],
    "scaffold-security": ["forte", "medio"],
    "scaffold-reviewer": ["forte", "medio"],
}
GEMINI_MODEL = {"leve": "flash-lite", "medio": "flash", "forte": "pro"}
# Twice the largest budget in references/watchdog.md, in minutes.
GEMINI_TIMEOUT = {
    "scaffold-architect": 40, "scaffold-designer": 30, "scaffold-planner": 30,
    "scaffold-router": 10, "scaffold-implementer": 60, "scaffold-tester": 60,
    "scaffold-security": 80, "scaffold-reviewer": 60,
}


def parse_agent(path):
    text = path.read_text(encoding="utf-8")
    _, front, body = text.split("---\n", 2)
    meta = {}
    for line in front.strip().splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    return meta, body.strip() + "\n"


def yaml_str(value):
    return json.dumps(value, ensure_ascii=False)


def write(out, rel, content):
    path = out / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def build(out):
    plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    version, description = plugin["version"], plugin["description"]
    agents = {p.stem: parse_agent(p) for p in sorted((ROOT / "agents").glob("*.md"))}
    assert set(agents) == set(AGENT_TIERS), "AGENT_TIERS is out of sync with agents/"

    for name, (meta, body) in agents.items():
        notice = NOTICE.format(name=name)

        # Codex: one TOML per agent, no model (the orchestrator passes it at spawn time).
        assert "'''" not in body
        write(out, f"codex/agents/{name}.toml",
              f"# {notice}\n"
              f"name = {yaml_str(name)}\n"
              f"description = {yaml_str(meta['description'])}\n"
              f"developer_instructions = '''\n{body}'''\n")

        # Cursor: model inherit (the orchestrator names the model per call).
        write(out, f"cursor/agents/{name}.md",
              f"---\nname: {name}\ndescription: {yaml_str(meta['description'])}\n"
              f"model: inherit\n---\n\n<!-- {notice} -->\n\n{body}")

        # Gemini CLI: no model per call, so one agent per tier.
        for tier in AGENT_TIERS[name]:
            write(out, f"gemini-cli/agents/{name}-{tier}.md",
                  f"---\nname: {name}-{tier}\n"
                  f"description: {yaml_str(meta['description'] + f' Nível {tier}.')}\n"
                  f"model: {GEMINI_MODEL[tier]}\n"
                  f"max_turns: {meta['maxTurns']}\n"
                  f"timeout_mins: {GEMINI_TIMEOUT[name]}\n---\n\n<!-- {notice} -->\n\n{body}")

    # Gemini CLI extension: manifest, command and a copy of the skill.
    write(out, "gemini-cli/gemini-extension.json", json.dumps(
        {"name": "molbytes", "version": version, "description": description},
        ensure_ascii=False, indent=2) + "\n")
    write(out, "gemini-cli/commands/molbytes-scaffold.toml",
          "description = \"molbytes.scaffold: da ideia ao código testado, auditado e revisado\"\n"
          "prompt = '''\nAtive a skill `molbytes-scaffold` e siga as instruções dela como orquestrador.\n"
          "Descrição do projeto: {{args}}\n'''\n")
    for src in sorted(SKILL.rglob("*")):
        if src.is_file() and "__pycache__" not in src.parts:
            rel = src.relative_to(SKILL).as_posix()
            write(out, f"gemini-cli/skills/molbytes-scaffold/{rel}",
                  src.read_text(encoding="utf-8").replace("\r\n", "\n"))


def manifests():
    """Version-synced manifests that live outside adapters/ (repo root)."""
    plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    common = {k: plugin[k] for k in ("name", "version", "description", "author", "homepage", "repository", "license", "keywords")}
    files = {
        ".codex-plugin/plugin.json": common,
        ".cursor-plugin/plugin.json": {**common, "agents": "./adapters/cursor/agents/"},
        ".cursor-plugin/marketplace.json": {
            "name": "molbytes",
            "owner": {"name": "MolBytes", "url": "https://www.molbytes.io"},
            "plugins": [{"name": "molbytes", "source": "./", "description": plugin["description"], "version": plugin["version"]}],
        },
    }
    return {rel: json.dumps(data, ensure_ascii=False, indent=2) + "\n" for rel, data in files.items()}


def snapshot(base, dirs):
    # Text compared without CR: git on Windows may check files out with CRLF.
    return {p.relative_to(base).as_posix(): p.read_bytes().replace(b"\r\n", b"\n")
            for d in dirs if (base / d).exists() for p in (base / d).rglob("*") if p.is_file()}


def main():
    targets = ["codex", "cursor", "gemini-cli"]
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        build(tmp)
        fresh = snapshot(tmp, targets)
    fresh_manifests = manifests()

    if "--check" in sys.argv:
        stale = sorted(set(fresh) ^ set(snapshot(ADAPTERS, targets)))
        current = snapshot(ADAPTERS, targets)
        stale += sorted(k for k in fresh if k in current and current[k] != fresh[k])
        for rel, content in fresh_manifests.items():
            path = ROOT / rel
            if not path.exists() or path.read_text(encoding="utf-8").replace("\r\n", "\n") != content:
                stale.append(rel)
        if stale:
            print("Desatualizado (rode python adapters/build.py):")
            print("\n".join(f"  {s}" for s in stale))
            sys.exit(1)
        print("Adaptadores em dia.")
        return

    for t in targets:
        shutil.rmtree(ADAPTERS / t, ignore_errors=True)
    build(ADAPTERS)
    for rel, content in fresh_manifests.items():
        write(ROOT, rel, content)
    print(f"Gerados {len(fresh)} arquivos em adapters/ e {len(fresh_manifests)} manifestos.")


if __name__ == "__main__":
    main()
