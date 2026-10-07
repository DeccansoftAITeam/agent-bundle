#!/usr/bin/env python3
"""Regenerate copilot/agents/*.agent.md from agents/*.md (single source).

Run after editing any subagent. CI fails if the output differs (--check).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTICE = "<!-- GENERATED from agents/ by scripts/build_copilot.py. Do not edit. -->\n"
TOOLS = {"Read": "read", "Grep": "search", "Glob": "search", "Bash": "execute"}


def convert(text: str) -> str:
    def tools(m: re.Match) -> str:
        names = sorted({TOOLS.get(t.strip(), t.strip().lower()) for t in m.group(1).split(",")})
        return "tools: [" + ", ".join(f"'{n}'" for n in names) + "]"

    text = re.sub(r"^tools: (.+)$", tools, text, count=1, flags=re.M)
    m = re.match(r"(---\n.*?\n---\n)(.*)", text, re.S)
    return m.group(1) + NOTICE + m.group(2) if m else NOTICE + text


def main() -> int:
    out = {ROOT / "copilot/agents" / f"{p.stem}.agent.md": convert(p.read_text(encoding="utf-8"))
           for p in sorted((ROOT / "agents").glob("*.md"))}
    if "--check" in sys.argv:
        drift = [p for p, b in out.items() if not p.exists() or p.read_text(encoding="utf-8") != b]
        for p in drift:
            print(f"drift: {p.relative_to(ROOT)}")
        return 1 if drift else 0
    for p, body in out.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8", newline="\n")
    print(f"built {len(out)} copilot agents")
    return 0


if __name__ == "__main__":
    sys.exit(main())
