"""Tests of scripts/install_components.py with a fake component in a git repo."""

from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SCRIPT = SKILL / "scripts" / "install_components.py"

INSTALL_SH = """#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[ "$1" = --project ] || exit 2
mkdir -p .agents/skills .claude/skills
rm -rf .agents/skills/fake .claude/skills/fake
cp -R "$SCRIPT_DIR" .agents/skills/fake
rm -rf .agents/skills/fake/.git
ln -s ../../.agents/skills/fake .claude/skills/fake
echo "installed fake"
"""


def sh(*args: str, cwd: Path) -> str:
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True).stdout


def fake_component(tmp: Path) -> Path:
    src = tmp / "fake-src"
    src.mkdir()
    (src / "SKILL.md").write_text("v1\n")
    (src / "install.sh").write_text(INSTALL_SH)
    sh("git", "init", "-q", cwd=src)
    sh("git", "add", ".", cwd=src)
    sh("git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "v1", cwd=src)
    return src


def run(project: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(project), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_install_lock_check(tmp_path: Path) -> None:
    src = fake_component(tmp_path)
    project = tmp_path / "p"
    project.mkdir()
    (project / "ml-scaffold.toml").write_text('[project]\ncomponents = ["fake"]\n')

    # uncommitted change in the source: not installed by default
    (src / "SKILL.md").write_text("v2 uncommitted\n")
    out = run(project, "--source", f"fake={src}")
    assert out.returncode == 0, out.stderr
    assert "installed fake" in out.stdout
    assert "uncommitted changes" in out.stdout
    assert (project / ".agents/skills/fake/SKILL.md").read_text() == "v1\n"
    lock = tomllib.loads((project / "skills.lock").read_text())
    assert lock["fake"]["rev"] == sh("git", "rev-parse", "HEAD", cwd=src).strip()
    assert lock["fake"]["tree"].startswith("sha256:")
    assert "ml-scaffold" in lock

    ok = run(project, "--check", "--source", f"fake={src}")
    assert ok.returncode == 0 and ok.stdout.startswith("ok"), ok.stdout

    (project / ".agents/skills/fake/SKILL.md").write_text("edited in place\n")
    bad = run(project, "--check", "--source", f"fake={src}")
    assert bad.returncode == 1 and bad.stdout.startswith("modified"), bad.stdout

    # --worktree takes the uncommitted file and says so in the lock
    out = run(project, "--worktree", "--source", f"fake={src}")
    assert out.returncode == 0, out.stderr
    assert (project / ".agents/skills/fake/SKILL.md").read_text() == "v2 uncommitted\n"
    assert tomllib.loads((project / "skills.lock").read_text())["fake"]["worktree"] is True


def test_behind(tmp_path: Path) -> None:
    src = fake_component(tmp_path)
    project = tmp_path / "p"
    project.mkdir()
    (project / "ml-scaffold.toml").write_text('[project]\ncomponents = ["fake"]\n')
    assert run(project, "--source", f"fake={src}").returncode == 0
    (src / "SKILL.md").write_text("v2\n")
    sh("git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qam", "v2", cwd=src)
    out = run(project, "--check", "--source", f"fake={src}")
    assert out.returncode == 0 and out.stdout.startswith("behind"), out.stdout


def test_missing_and_unknown(tmp_path: Path) -> None:
    project = tmp_path / "p"
    project.mkdir()
    (project / "ml-scaffold.toml").write_text('[project]\ncomponents = ["research-log"]\n')
    out = run(project, "--check")
    assert out.returncode == 1 and out.stdout.startswith("missing")
    out = run(project, "--only", "nope")
    assert out.returncode == 2 and "not in ml-scaffold.toml" in out.stderr


def test_bytecode_excluded_in_a_git_project(tmp_path: Path) -> None:
    src = fake_component(tmp_path)
    project = tmp_path / "p"
    project.mkdir()
    sh("git", "init", "-q", cwd=project)
    (project / "ml-scaffold.toml").write_text('[project]\ncomponents = ["fake"]\n')
    for _ in range(2):  # twice: the line is added once
        out = run(project, "--source", f"fake={src}")
        assert out.returncode == 0, out.stderr
    lines = (project / ".git/info/exclude").read_text().splitlines()
    assert lines.count("__pycache__/") == 1
    cache = project / ".agents/skills/fake/__pycache__"
    cache.mkdir()
    (cache / "x.pyc").write_bytes(b"\0")
    assert "__pycache__" not in sh("git", "status", "--porcelain", "-uall", cwd=project)


def test_version_of_a_build(tmp_path: Path) -> None:
    """VERSION of a core with a pack's files on top carries both revisions."""
    import importlib.util
    import shutil

    skill = tmp_path / "skill"
    shutil.copytree(SKILL / "scripts", skill / "scripts")
    (skill / "VERSION").write_text("core@aaa+acme@bbb-dirty\n")
    spec = importlib.util.spec_from_file_location("ic", skill / "scripts" / "install_components.py")
    assert spec and spec.loader
    ic = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ic)
    assert ic.skill_entry() == {
        "source": str(skill),
        "rev": "core@aaa+acme@bbb",
        "worktree": True,
    }
    (skill / "SOURCE").write_text("https://example.org/ml-scaffold.git\n")
    assert ic.skill_entry()["source"] == "https://example.org/ml-scaffold.git"


def test_check_says_when_the_skill_moved(tmp_path: Path) -> None:
    src = fake_component(tmp_path)
    project = tmp_path / "p"
    project.mkdir()
    (project / "ml-scaffold.toml").write_text('[project]\ncomponents = ["fake"]\n')
    assert run(project, "--source", f"fake={src}").returncode == 0
    lock = (project / "skills.lock").read_text()
    rev = tomllib.loads(lock)["ml-scaffold"]["rev"]
    (project / "skills.lock").write_text(lock.replace(f'"{rev}"', '"core@old+acme@old"', 1))
    out = run(project, "--check", "--source", f"fake={src}")
    assert out.returncode == 0, out.stdout
    assert out.stdout.startswith("differs   ml-scaffold: skills.lock has core@old+acme@old")
