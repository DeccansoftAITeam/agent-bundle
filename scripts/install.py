#!/usr/bin/env python3
"""Install the files that `npx skills` and the Claude plugin cannot deliver.

Copies into the target project repo:
  org/org-rules.md, org/mcp-allowlist.yml  -> .agents/org/                (L1, L5: both harnesses)
  hooks/audit_log.py                       -> .agents/hooks/              (Copilot hook target)
  copilot/agents/*.agent.md                -> .github/agents/             (Copilot subagents)
  hooks/scope_guard.py                     -> .agents/hooks/              (Copilot hook target)
  copilot/hooks/*.json                     -> .github/hooks/              (Copilot audit + scope hooks)
and writes .agents/bundle.lock (bundle version + commit) for the conformance drift check.

Skills:            npx skills add DeccansoftAITeam/agent-bundle#v<version> ...
Claude subagents
and audit hook:    the `deccansoft-org` Claude Code plugin.

Usage: python scripts/install.py <target-repo> [--check]
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MAP = [
    ("org/org-rules.md", ".agents/org/org-rules.md"),
    ("org/mcp-allowlist.yml", ".agents/mcp-allowlist.yml"),
    ("hooks/audit_log.py", ".agents/hooks/audit_log.py"),
    ("hooks/scope_guard.py", ".agents/hooks/scope_guard.py"),
    ("copilot/hooks/audit.json", ".github/hooks/audit.json"),
    ("copilot/hooks/scope-guard.json", ".github/hooks/scope-guard.json"),
]


def files() -> list[tuple[Path, str]]:
    pairs = [(ROOT / s, d) for s, d in MAP]
    pairs += [(p, f".github/agents/{p.name}") for p in sorted((ROOT / "copilot/agents").glob("*.agent.md"))]
    return pairs


def commit() -> str:
    try:
        return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return "unknown"


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    target = Path(sys.argv[1]).resolve()
    version = (ROOT / "VERSION").read_text().strip()

    if "--check" in sys.argv:
        drift = [d for s, d in files()
                 if not (target / d).exists() or (target / d).read_bytes() != s.read_bytes()]
        for d in drift:
            print(f"drift: {d}")
        return 1 if drift else 0

    for src, dst in files():
        out = target / dst
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, out)
        print(f"installed {dst}")
    lock = {"bundle": "DeccansoftAITeam/agent-bundle", "version": version, "commit": commit(),
            "files": [d for _, d in files()]}
    (target / ".agents/bundle.lock").write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    print(f"wrote .agents/bundle.lock (v{version})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
