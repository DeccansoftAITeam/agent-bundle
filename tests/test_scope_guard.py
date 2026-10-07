import json
import subprocess
import sys
from pathlib import Path

GUARD = Path(__file__).resolve().parent.parent / "hooks" / "scope_guard.py"


def run(tmp: Path, event: dict, harness: str = "claude") -> subprocess.CompletedProcess:
    event = {"cwd": str(tmp), **event}
    return subprocess.run([sys.executable, str(GUARD), harness], input=json.dumps(event),
                          capture_output=True, text=True)


def activate(tmp: Path, task: str = "T-007-02", scope: str = "- `backend/app/features/sla/**`\n- `backend/tests/{conftest,test_x}.py`\n"):
    d = tmp / ".agents/progress"
    d.mkdir(parents=True)
    (d / "ACTIVE").write_text(task)
    (d / f"{task}.md").write_text(f"# {task}\n\n## Files in scope\n{scope}\n## Done\n- `not/a/scope.py`\n")


def edit(path: str) -> dict:
    return {"tool_name": "Edit", "tool_input": {"file_path": path}}


def test_no_active_task_allows(tmp_path):
    assert run(tmp_path, edit("anything.py")).returncode == 0


def test_in_scope_allowed(tmp_path):
    activate(tmp_path)
    assert run(tmp_path, edit("backend/app/features/sla/sweep.py")).returncode == 0
    assert run(tmp_path, edit("backend/tests/conftest.py")).returncode == 0


def test_out_of_scope_blocked_claude(tmp_path):
    activate(tmp_path)
    r = run(tmp_path, edit("backend/app/features/auth/login.py"))
    assert r.returncode == 2 and "outside the Files in scope" in r.stderr


def test_sections_after_scope_are_ignored(tmp_path):
    activate(tmp_path)
    assert run(tmp_path, edit("not/a/scope.py")).returncode == 2


def test_progress_dir_always_allowed(tmp_path):
    activate(tmp_path)
    assert run(tmp_path, edit(".agents/progress/T-007-02.md")).returncode == 0


def test_absolute_path_outside_repo_blocked(tmp_path):
    activate(tmp_path)
    outside = tmp_path.parent / "elsewhere.py"
    assert run(tmp_path, edit(str(outside))).returncode == 2


def test_copilot_deny_json(tmp_path):
    activate(tmp_path)
    r = run(tmp_path, {"toolName": "edit", "toolArgs": json.dumps({"path": "infra/main.tf"})}, "copilot")
    assert r.returncode == 0 and json.loads(r.stdout)["permissionDecision"] == "deny"


def test_non_edit_tool_allowed(tmp_path):
    activate(tmp_path)
    assert run(tmp_path, {"tool_name": "Bash", "tool_input": {"command": "ls"}}).returncode == 0


def test_missing_scope_section_blocks(tmp_path):
    activate(tmp_path, scope="")
    d = tmp_path / ".agents/progress"
    (d / "T-007-02.md").write_text("# no scope here\n")
    assert run(tmp_path, edit("x.py")).returncode == 2
