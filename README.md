# Deccansoft Agent Bundle

The org-level agent configuration from Deccansoft SDLC v2: the **central standards repo** that every project installs from. It is changed only by the Platform/Standards Owner, through PRs, and released as SemVer tags (`v2.1.2`).

| Layer | Contents | Path |
|---|---|---|
| L1 Org rules | Forbidden actions, modes, attribution, injection hygiene | `org/org-rules.md` |
| L4 Skills | `grill`, `spec-draft`, `scaffold`, `acceptance-tdd`, `migration-writer`, `test-generator` | `skills/` |
| L4 Subagents | `code-reviewer`, `security-reviewer` (read-only) | `agents/` (Claude) → `copilot/agents/` (generated) |
| Audit hook | One JSON line per tool call, secrets redacted | `hooks/audit_log.py` |
| Scope guard hook | Blocks edits outside the active task's "Files in scope" (`.agents/progress/ACTIVE`) | `hooks/scope_guard.py` |
| L5 Tool allow-list | Approved MCP servers | `org/mcp-allowlist.yml` |

## Install into a project (pin the version)

Run all three steps from the project root.

```sh
# 1. Skills, for both harnesses (writes skills-lock.json; commit it)
DISABLE_TELEMETRY=1 npx skills add DeccansoftAITeam/agent-bundle#v2.1.2 \
  --skill '*' -a claude-code -a github-copilot --copy -y
#    Claude Code → .claude/skills/     GitHub Copilot → .agents/skills/

# 2. Claude Code: subagents + audit hook (plugin)
claude plugin marketplace add DeccansoftAITeam/agent-bundle
claude plugin install deccansoft-org@deccansoft
#    or inside a session: /plugin marketplace add … then /plugin install …

# 3. Org rules, MCP allow-list, Copilot subagents + Copilot audit hook
git clone --depth 1 --branch v2.1.2 https://github.com/DeccansoftAITeam/agent-bundle /tmp/agent-bundle
python /tmp/agent-bundle/scripts/install.py .
```

Commit the results. Permission deny-lists (`.claude/settings.json`, `.vscode/settings.json`) and `CODEOWNERS` are **not** part of the bundle. They come from the project scaffold, live in the repo and are protected by CODEOWNERS, because a gate that a developer can uninstall isn't a gate.

## What goes where

| | Claude Code | GitHub Copilot |
|---|---|---|
| Skills | `npx skills` → `.claude/skills/` | `npx skills` → `.agents/skills/` |
| Subagents | plugin `deccansoft-org` | `install.py` → `.github/agents/` |
| Audit + scope hooks | plugin (`hooks/hooks.json`) | `install.py` → `.github/hooks/{audit,scope-guard}.json` |
| Org rules | `install.py` → `.agents/org/`, imported by `CLAUDE.md` | same file, referenced by `AGENTS.md` |

## Drift check (used by conformance)

```sh
python /tmp/agent-bundle/scripts/install.py . --check   # exit 1 on drift
npx skills list                                          # versions match skills-lock.json
```

## Changing the bundle (PSO only)

1. Edit `skills/`, `agents/`, `hooks/` or `org/`.
2. Run `python scripts/build_copilot.py` to regenerate the Copilot agents.
3. Bump `VERSION`, `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` together.
4. PR → review → merge → tag `vX.Y.Z`. Projects upgrade by re-running the install steps with the new tag, in a PR.

## Tests

`uvx pytest -q tests`
