"""Tests of scripts/render.py: uv run --with pytest pytest tests/"""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parent.parent
RENDER = SKILL / "scripts" / "render.py"
spec = importlib.util.spec_from_file_location("render", RENDER)
assert spec and spec.loader
render = importlib.util.module_from_spec(spec)
spec.loader.exec_module(render)

ALL = ["research-log", "task-tracker", "mlflow-tracking", "lightning-hydra"]
LANGS = sorted(p.name for p in (SKILL / "templates").iterdir() if p.is_dir())
FRAGMENTS = ["conventions-local", "setup-task", "handoff", "brief", "protocols/access"]


def project(
    tmp_path: Path, components: list[str] = ALL, name: str = "ddg-pred", lang: str = "ru"
) -> Path:
    comps = ", ".join(f'"{c}"' for c in components)
    (tmp_path / "ml-scaffold.toml").write_text(
        f'[project]\nname = "{name}"\npkg = "ddg"\nlang = "{lang}"\ncomponents = [{comps}]\n'
        '[resources]\nruns_volume = ""\n[infra]\nmlflow_uri = "https://mlflow.example.org/"\n'
    )
    return tmp_path


def run(*args: str, script: Path = RENDER) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args], capture_output=True, text=True, check=False
    )


def infra_skill(tmp_path: Path) -> Path:
    """A copy of the skill with an infrastructure component on top, as a
    pack's install would lay it: an adapter that fills the transport, parts,
    a derived value and an infra key."""
    skill = tmp_path / "skill"
    for d in ("scripts", "components", "templates"):
        shutil.copytree(SKILL / d, skill / d)
    shutil.copy(SKILL / "infra.toml", skill / "infra.toml")
    (skill / "components" / "remote.md").write_text(
        "# remote\n\n## Roles\n\n- Fills: transport.\n- Requires: none.\n\n"
        "| доступ | файл и секция | ключи | где взять | где нужен | проверка |\n"
        "|---|---|---|---|---|---|\n| remote | `~/.remote` | — | <infra:remote_host> | ноутбук | `remote ping` |\n"
    )
    for lang in LANGS:
        parts = skill / "templates" / lang / "parts"
        (parts / "agents").mkdir(parents=True, exist_ok=True)
        (parts / "agents" / "remote.md").write_text("## Remote\n\nmount {{runs_mount}}\n\n")
        (parts / "claude-allow").mkdir(exist_ok=True)
        (parts / "claude-allow" / "remote.json").write_text('      "Bash(remote run:*)",\n')
        (parts / "gitignore").mkdir(exist_ok=True)
        (parts / "gitignore" / "remote.gitignore").write_text("# remote\n.remote/\n")
    infra = (
        (skill / "infra.toml")
        .read_text()
        .replace(
            "[derived]",
            'remote_host = "r.example.org"\n\n[derived]\nruns_mount = "/mnt/{{project.name}}-runs"',
        )
    )
    (skill / "infra.toml").write_text(infra)
    return skill


def test_values_derived_and_infra_override(tmp_path: Path) -> None:
    v = render.load_values(project(tmp_path))
    assert v["runs_env"] == "DDG_PRED_RUNS"
    assert v["infra.mlflow_uri"] == "https://mlflow.example.org/"
    assert v["infra.mlflow_login"] is False
    assert v["resources.runs_volume"] == "<runs_volume>"
    assert "infra.derived" not in v


def test_python_value(tmp_path: Path) -> None:
    p = project(tmp_path)
    assert render.load_values(p)["project.python"] == ""
    text = (
        (p / "ml-scaffold.toml").read_text().replace('lang = "ru"', 'lang = "ru"\npython = "3.13"')
    )
    (p / "ml-scaffold.toml").write_text(text)
    assert render.load_values(p)["project.python"] == "3.13"
    (p / "ml-scaffold.toml").write_text(text.replace('"3.13"', '"3.13.1"'))
    with pytest.raises(render.Error, match="minor version"):
        render.load_values(p)


@pytest.mark.parametrize("bad", ["Ddg", "1ddg", "ddg_pred"])
def test_bad_name(tmp_path: Path, bad: str) -> None:
    with pytest.raises(render.Error):
        render.load_values(project(tmp_path, name=bad))


def test_unknown_component(tmp_path: Path) -> None:
    with pytest.raises(render.Error, match="no adapter"):
        render.load_values(project(tmp_path, components=["nope"]))


def test_blocks_and_placeholders(tmp_path: Path) -> None:
    v = render.load_values(project(tmp_path, components=["research-log", "mlflow-tracking"]))
    text = (
        "a {{project.name}}\n"
        "{{#if mlflow-tracking}}\nml\n{{#if task-tracker}}\ntt\n{{/if}}\n{{/if}}\n"
        "{{#if !lightning-hydra}}\nno skeleton\n{{/if}}\n"
        "x{{#if mlflow-tracking}} y{{/if}}{{#if task-tracker}} z{{/if}}\n"
    )
    assert render.render(text, v, "t") == "a ddg-pred\nml\nno skeleton\nx y\n"


def test_role_and_infra_conditions(tmp_path: Path) -> None:
    v = render.load_values(project(tmp_path))
    assert v["_roles"] == ["board", "log", "run-tracker", "skeleton"]
    text = (
        "{{#if run-tracker}}\ntracker\n{{/if}}\n{{#if !transport}}\nlocal\n{{/if}}\n"
        "{{#if infra.mlflow_login}}\nlogin\n{{/if}}\n"
    )
    assert render.render(text, v, "t") == "tracker\nlocal\n"
    with pytest.raises(render.Error, match="unknown infra key"):
        render.render("{{#if infra.nope}}\n{{/if}}\n", v, "t")
    with pytest.raises(render.Error, match="unknown component or role"):
        render.render("{{#if nope}}\n{{/if}}\n", v, "t")


def test_unknown_placeholder(tmp_path: Path) -> None:
    v = render.load_values(project(tmp_path))
    with pytest.raises(render.Error, match="unknown placeholder"):
        render.render("{{nope}}\n", v, "t")
    with pytest.raises(render.Error, match="not closed"):
        render.render("{{#if mlflow-tracking}}\n", v, "t")


def test_access_rows_follow_the_infra(tmp_path: Path) -> None:
    p = project(tmp_path)
    assert render.access_rows(render.load_values(p)) == []  # a local store: no login
    text = (
        (p / "ml-scaffold.toml").read_text().replace("[infra]\n", "[infra]\nmlflow_login = true\n")
    )
    (p / "ml-scaffold.toml").write_text(text)
    rows = render.access_rows(render.load_values(p))
    assert len(rows) == 1 and rows[0].startswith("| MLflow |")
    assert "https://mlflow.example.org/" in rows[0] and "infra:" not in rows[0]
    assert "HPC" not in rows[0]  # no transport


def test_merge_toml_adds_missing_keeps_existing() -> None:
    existing = '[project]\nname = "x"\n\n[tool.ruff]\nline-length = 120\nsrc = ["lib"]\n\n[tool.uv.sources]\na = 1\n'
    fragment = '[tool.ruff]\nsrc = ["src"]\nextend-exclude = [".agents"]\n[tool.pyright]\ninclude = ["src"]\n'
    text, added, kept = render.merge_toml(existing, fragment)
    data = tomllib.loads(text)
    assert data["tool"]["ruff"] == {
        "line-length": 120,
        "src": ["lib"],
        "extend-exclude": [".agents"],
    }
    assert data["tool"]["pyright"] == {"include": ["src"]}
    assert added == ["tool.ruff.extend-exclude", "tool.pyright.include"]
    assert kept == ["tool.ruff.src"]
    # the key went into its table, before the next header
    assert text.index("extend-exclude") < text.index("[tool.uv.sources]")


def test_merge_lines_keeps_comments() -> None:
    text, new = render.merge_lines("logs/\n.venv/\n", ".venv/\n# data\n/data/**\n")
    assert new == ["/data/**"]
    assert text == "logs/\n.venv/\n# data\n/data/**\n"


@pytest.mark.parametrize("lang", LANGS)
def test_files_idempotent_and_check(tmp_path: Path, lang: str) -> None:
    p = project(tmp_path, lang=lang)
    (p / "pyproject.toml").write_text('[project]\nname = "ddg"\n')
    (p / ".gitignore").write_text("logs/\n")
    first = run("files", str(p))
    assert first.returncode == 0, first.stderr
    assert "wrote       scripts/log_smoke_run.py" in first.stdout
    assert "DDG_PRED_RUNS" in (p / "scripts" / "log_smoke_run.py").read_text()
    readme = (p / "README.md").read_text()
    assert "{{" not in readme and "\n\n\n" not in readme
    json.loads((p / ".claude" / "settings.json").read_text())
    json.loads((p / "opencode.json").read_text())
    second = run("files", str(p))
    assert "wrote" not in second.stdout and "added" not in second.stdout
    check = run("files", "--check", str(p))
    assert check.returncode == 0, check.stdout


def test_files_without_pyproject_reports(tmp_path: Path) -> None:
    out = run("files", str(project(tmp_path)))
    assert "missing     pyproject.toml" in out.stdout
    assert not (tmp_path / "pyproject.toml").exists()


def test_component_files_skipped_when_not_connected(tmp_path: Path) -> None:
    p = project(tmp_path, components=["research-log", "task-tracker"])
    (p / "pyproject.toml").write_text('[project]\nname = "ddg"\n')
    run("files", str(p))
    assert not (p / "scripts" / "log_smoke_run.py").exists()


@pytest.mark.parametrize("lang", LANGS)
@pytest.mark.parametrize("name", FRAGMENTS)
def test_fragments_render(tmp_path: Path, name: str, lang: str) -> None:
    out = run("fragment", name, str(project(tmp_path, lang=lang)))
    assert out.returncode == 0, out.stderr
    assert "{{" not in out.stdout


@pytest.mark.parametrize("lang", LANGS)
def test_fragments_render_minimal(tmp_path: Path, lang: str) -> None:
    p = project(tmp_path, components=["research-log", "task-tracker"], lang=lang)
    for name in FRAGMENTS:
        out = run("fragment", name, str(p))
        assert out.returncode == 0, out.stderr


def test_languages_share_the_machine_parts() -> None:
    """Every language has the same files, slots and conditions: prose is
    translated, what render.py reads is not."""
    import re

    def shape(lang: str) -> dict[str, list[str]]:
        root = SKILL / "templates" / lang
        return {
            p.relative_to(root).as_posix(): re.findall(r"\{\{[#/]?[^}]*\}\}", p.read_text())
            for p in sorted(root.rglob("*"))
            if p.is_file()
        }

    shapes = {lang: shape(lang) for lang in LANGS}
    first = shapes[LANGS[0]]
    for lang, s in shapes.items():
        assert s.keys() == first.keys(), lang
        for rel in s:
            assert sorted(s[rel]) == sorted(first[rel]), (lang, rel)


def test_files_only_agent_settings(tmp_path: Path) -> None:
    p = project(tmp_path)
    out = run("files", str(p), "--only", ".claude/settings.json", "--only", "opencode.json")
    assert out.returncode == 0, out.stderr
    assert sorted(x.name for x in p.rglob("*") if x.is_file()) == [
        "ml-scaffold.toml",
        "opencode.json",
        "settings.json",
    ]
    claude = json.loads((p / ".claude" / "settings.json").read_text())
    assert "Read(~/.aws/credentials)" in claude["permissions"]["deny"]
    assert "Read(~/.config/ml-scaffold/deny-probe)" in claude["permissions"]["deny"]
    assert claude["permissions"]["allow"] == []
    opencode = json.loads((p / "opencode.json").read_text())
    # OpenCode 1.18 matches read/edit patterns as globs over the absolute path:
    # `~/...` and absolute patterns never match, `*/...` does.
    assert opencode["permission"]["read"]["*/.config/ml-scaffold/deny-probe"] == "deny"
    assert not [k for k in opencode["permission"]["read"] if k.startswith(("~", "/"))]
    assert run("files", str(p), "--only", "nope.json").returncode == 2


def test_access_protocol_local(tmp_path: Path) -> None:
    out = run("fragment", "protocols/access", str(project(tmp_path)))
    assert out.returncode == 0, out.stderr
    assert "doctor.py" in out.stdout
    assert "[mlflow]" not in out.stdout  # a local store needs no login


def test_infra_component_through_parts(tmp_path: Path) -> None:
    """An infrastructure component reaches the shared files only through its adapter,
    parts and infra.toml: nothing in the core names it."""
    skill = infra_skill(tmp_path)
    script = skill / "scripts" / "render.py"
    (tmp_path / "p").mkdir()
    p = project(tmp_path / "p", [*ALL, "remote"])
    (p / "pyproject.toml").write_text('[project]\nname = "ddg"\n')
    out = run("files", str(p), script=script)
    assert out.returncode == 0, out.stderr
    agents = (p / "AGENTS.md").read_text()
    assert "## Remote\n\nmount /mnt/ddg-pred-runs\n" in agents
    allow = json.loads((p / ".claude" / "settings.json").read_text())["permissions"]["allow"]
    assert allow == ["Bash(remote run:*)"]
    assert "# remote\n.remote/\n" in (p / ".gitignore").read_text()
    setup = run("fragment", "setup-task", str(p), script=script).stdout
    assert "trainer=debug" not in setup  # the transport carries the smoke run
    access = run("fragment", "protocols/access", str(p), script=script).stdout
    assert "| remote | `~/.remote` | — | r.example.org |" in access


def test_a_language_without_a_components_parts_fails(tmp_path: Path) -> None:
    """An infrastructure component with parts and files in one language only: a
    project in another language fails loudly instead of losing them."""
    skill = infra_skill(tmp_path)
    script = skill / "scripts" / "render.py"
    shutil.rmtree(skill / "templates" / "en" / "parts" / "agents")
    (skill / "templates" / "ru" / "repo" / "scripts" / "remote_entry.sh").write_text("true\n")
    (tmp_path / "p").mkdir()
    p = project(tmp_path / "p", [*ALL, "remote"], lang="en")
    (p / "pyproject.toml").write_text('[project]\nname = "ddg"\n')
    out = run("files", str(p), script=script)
    assert out.returncode == 2 and "lacks scripts/remote_entry.sh" in out.stderr
    (skill / "templates" / "ru" / "repo" / "scripts" / "remote_entry.sh").unlink()
    out = run("files", str(p), script=script)
    assert out.returncode == 2 and "only in another language" in out.stderr
    (skill / "templates" / "ru" / "protocols").mkdir(exist_ok=True)
    (skill / "templates" / "ru" / "protocols" / "remote-runs.md").write_text("x\n")
    out = run("fragment", "protocols/remote-runs", str(p), script=script)
    assert out.returncode == 2 and "only in ru" in out.stderr
