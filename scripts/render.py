#!/usr/bin/env python3
"""Render ml-scaffold templates with the values of a project.

    python3 render.py files [PROJECT] [--dry-run | --check] [--only PATH ...]
    python3 render.py fragment NAME [PROJECT]
    python3 render.py values [PROJECT]

Values come from PROJECT/ml-scaffold.toml (templates/ml-scaffold.toml is the
starting point) and the skill's infra.toml, overridden by the [infra] table of
the project file; the [derived] table of infra.toml makes values from them
(`runs_env = "{{project.env}}_RUNS"`). PROJECT defaults to the current
directory.

files     Renders templates/<lang>/repo/ into the project, once:
          - a missing file is written; an existing one is left as it is and
            listed as `exists` (it belongs to the project);
          - .gitignore gets the template's lines it lacks, appended;
          - pyproject.toml gets the template's keys its tables lack; a key
            the project set differently is kept and listed as `keeps`. The
            file itself comes from the skeleton (or `uv init`), not from here.
          --dry-run prints the same list and writes nothing. --check writes
          nothing and prints `same`, `differs` or `missing` per file and
          `missing <key>` per absent line or key; exit 1 if anything is
          missing. --only PATH renders just that file (repeatable), e.g. the
          agents' settings at step 0.
fragment  Prints templates/<lang>/<NAME>.md rendered: a section of
          conventions-local.md, a protocol body, the setup task's body.
values    Prints every value a template can use, `key = value`.

Template syntax: `{{project.name}}`, `{{infra.mlflow_uri}}`, derived values
(`values` lists them); a line `{{#if <cond>}}` (or `{{#if !<cond>}}`) opens a
block kept only if the condition holds (does not), `{{/if}}` closes it;
`{{#if <cond>}}text{{/if}}` inside a line does the same for text (not nested,
not across lines). A condition is a component (connected), a role (filled by
a connected component: `transport`, `run-tracker`, components/README.md),
`infra.<key>` (a true value), `parts.<slot>` (some part renders text) or
`access_rows` (some adapter has a row). `{{access_rows}}` is the rows of the access tables
of the connected components' adapters. A line `{{parts <slot>}}` is the
rendered files templates/<lang>/parts/<slot>/<component>.* of the connected
components, in the order of `components`: what a component adds to a file
the template shares. In a .json file a comma before `]` or `}` is dropped, so
that a part's entries can each end with one. An unknown placeholder or
condition is an error.

Exit 0 on success, 1 when --check finds something missing, 2 on bad input.
Python 3.11+ standard library only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tomllib
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
PROJECT_FILE = "ml-scaffold.toml"
PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z0-9_.\-]+)\s*\}\}")
BLOCK_OPEN = re.compile(r"^\s*\{\{#if\s+(!?)([A-Za-z0-9_.\-]+)\s*\}\}\s*$")
BLOCK_CLOSE = re.compile(r"^\s*\{\{/if\}\}\s*$")
INLINE = re.compile(r"\{\{#if\s+(!?)([A-Za-z0-9_.\-]+)\s*\}\}(.*?)\{\{/if\}\}")
PARTS = re.compile(r"^\s*\{\{parts\s+([A-Za-z0-9_\-]+)\s*\}\}\s*$")
# "- Fills: run tracker." in an adapter's Roles section.
FILLS = re.compile(r"^- Fills:\s*(.+?)\.?\s*$", re.MULTILINE)
# Header of the access table of an adapter, by the project's language.
ACCESS_HEADER = {"en": "| access |", "ru": "| доступ |"}
NAME = re.compile(r"^[a-z][a-z0-9-]*$")
PKG = re.compile(r"^[a-z][a-z0-9_]*$")


class Error(Exception):
    pass


# --- values ---------------------------------------------------------------------


def load_values(project: Path) -> dict[str, object]:
    path = project / PROJECT_FILE
    if not path.is_file():
        raise Error(
            f"{path} not found: copy {SKILL / 'templates' / PROJECT_FILE} there and fill in [project]"
        )
    data = tomllib.loads(path.read_text())
    infra = tomllib.loads((SKILL / "infra.toml").read_text())
    derived = infra.pop("derived", {})
    infra.update(data.get("infra", {}))
    p = data.get("project", {})
    for key in ("name", "pkg", "lang", "components"):
        if not p.get(key):
            raise Error(f"{path}: [project] {key} is empty")
    if not NAME.match(p["name"]):
        raise Error(f"{path}: name {p['name']!r}: lowercase letters, digits and dashes")
    if p.get("python") and not re.fullmatch(r"3\.\d+", p["python"]):
        raise Error(f"{path}: python {p['python']!r}: a minor version such as 3.12")
    if not PKG.match(p["pkg"]):
        raise Error(f"{path}: pkg {p['pkg']!r}: lowercase letters, digits and underscores")
    unknown = [c for c in p["components"] if not (SKILL / "components" / f"{c}.md").is_file()]
    if unknown:
        raise Error(f"{path}: no adapter for {', '.join(unknown)} in {SKILL / 'components'}")
    if not (SKILL / "templates" / p["lang"]).is_dir():
        raise Error(f"no templates for lang {p['lang']!r} in {SKILL / 'templates'}")

    name = p["name"]
    env = name.upper().replace("-", "_")
    values: dict[str, object] = {
        "project.name": name,
        "project.pkg": p["pkg"],
        "project.title": p.get("title") or name,
        "project.description": (p.get("description") or "").strip(),
        "project.lang": p["lang"],
        "project.python": p.get("python") or "",
        "project.env": env,
        "components": ", ".join(p["components"]),
    }
    for key, value in data.get("resources", {}).items():
        values[f"resources.{key}"] = value or f"<{key}>"
    for key, value in infra.items():
        values[f"infra.{key}"] = value
    values["_components"] = list(p["components"])
    values["_roles"] = sorted(
        role.strip().replace(" ", "-")
        for c in p["components"]
        for m in FILLS.finditer((SKILL / "components" / f"{c}.md").read_text())
        for role in m.group(1).split(",")
        if role.strip().lower() != "none"
    )
    for key, tpl in derived.items():
        values[key] = render(str(tpl), values, f"infra.toml [derived] {key}")
    return values


# --- templates ------------------------------------------------------------------


ROLES = ("log", "board", "transport", "run-tracker", "data-source", "skeleton")


def _holds(cond: str, values: dict[str, object], where: str) -> bool:
    if cond.startswith("parts."):
        return bool(parts(cond[6:], values).strip())
    if cond == "access_rows":
        return bool(access_rows(values))
    if cond.startswith("infra."):
        if cond not in values:
            raise Error(f"{where}: block for unknown infra key {cond[6:]!r}")
        return bool(values[cond])
    if cond in ROLES:
        return cond in values["_roles"]  # type: ignore[operator]
    if not (SKILL / "components" / f"{cond}.md").is_file():
        raise Error(f"{where}: block for unknown component or role {cond!r}")
    return cond in values["_components"]  # type: ignore[operator]


def parts(slot: str, values: dict[str, object]) -> str:
    """The parts of the connected components for one slot, rendered."""
    lang = str(values["project.lang"])
    root = SKILL / "templates" / lang / "parts" / slot
    out = []
    for comp in values["_components"]:  # type: ignore[union-attr]
        if not any(root.glob(f"{comp}.*")):
            elsewhere = sorted(
                p.relative_to(SKILL).as_posix()
                for p in (SKILL / "templates").glob(f"*/parts/{slot}/{comp}.*")
            )
            if elsewhere:
                raise Error(
                    f"{comp} has parts for {{{{parts {slot}}}}} only in another language"
                    f" ({', '.join(elsewhere)}), none in templates/{lang}/parts/{slot}/:"
                    " translate them, or set lang to one the component has"
                )
        for path in sorted(root.glob(f"{comp}.*")):
            rel = path.relative_to(SKILL).as_posix()
            out.append(render(path.read_text(), values, rel, tidy=False))
    return "".join(out)


def render(text: str, values: dict[str, object], where: str, tidy: bool = True) -> str:
    out: list[str] = []
    stack: list[bool] = []
    for n, line in enumerate(text.splitlines(keepends=True), 1):
        if m := BLOCK_OPEN.match(line):
            stack.append(_holds(m.group(2), values, f"{where}:{n}") != (m.group(1) == "!"))
            continue
        if BLOCK_CLOSE.match(line):
            if not stack:
                raise Error(f"{where}:{n}: {{{{/if}}}} without {{{{#if}}}}")
            stack.pop()
            continue
        if not all(stack):
            continue
        if line.strip() == "{{access_rows}}":
            out.extend(row + "\n" for row in access_rows(values))
            continue
        if m := PARTS.match(line):
            out.append(parts(m.group(1), values))
            continue
        line = INLINE.sub(
            lambda m, n=n: (
                m.group(3)
                if _holds(m.group(2), values, f"{where}:{n}") != (m.group(1) == "!")
                else ""
            ),
            line,
        )
        out.append(PLACEHOLDER.sub(lambda m, n=n: _value(m.group(1), values, where, n), line))
    if stack:
        raise Error(f"{where}: {{{{#if}}}} not closed")
    text = "".join(out)
    if tidy and where.endswith(".md"):
        # Dropped blocks and empty values leave runs of blank lines.
        text = re.sub(r"\n{3,}", "\n\n", text).lstrip("\n")
    if tidy and where.endswith(".json"):
        text = re.sub(r",(\s*[\]}])", r"\1", text)
    return text


def _value(key: str, values: dict[str, object], where: str, n: int) -> str:
    if key.startswith("_") or key not in values:
        raise Error(f"{where}:{n}: unknown placeholder {{{{{key}}}}}")
    return str(values[key])


def access_rows(values: dict[str, object]) -> list[str]:
    """Rows of the access table of every connected component's adapter, the
    table in the project's language, with `infra:<key>` replaced by its value.
    Block lines (`{{#if infra.mlflow_login}}`) inside a table keep or drop rows."""
    rows: list[str] = []
    header = ACCESS_HEADER.get(str(values["project.lang"]), "| access |")
    for comp in values["_components"]:  # type: ignore[union-attr]
        where = f"components/{comp}.md"
        table: list[str] = []
        in_table = False
        for line in (SKILL / where).read_text().splitlines():
            if line.startswith(header):
                in_table = True
                continue
            if not in_table:
                continue
            if not line.startswith(("|", "{{")):
                break
            if not line.startswith("|---"):
                table.append(line + "\n")
        for line in render("".join(table), values, where, tidy=False).splitlines():
            rows.append(
                re.sub(
                    r"<?infra:([a-z0-9_]+)>?",
                    lambda m, comp=comp: _infra(m.group(1), values, comp),
                    line,
                )
            )
    return rows


def _infra(key: str, values: dict[str, object], comp: str) -> str:
    if f"infra.{key}" not in values:
        raise Error(f"components/{comp}.md: unknown infra key {key!r}")
    return str(values[f"infra.{key}"])


# --- pyproject.toml merge ---------------------------------------------------------


def _toml_value(v: object) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        return "[" + ", ".join(_toml_value(x) for x in v) + "]"
    raise Error(f"pyproject fragment: unsupported value {v!r}")


def _leaves(d: dict, path: tuple[str, ...] = ()) -> list[tuple[tuple[str, ...], str, object]]:
    out = []
    for k, v in d.items():
        if isinstance(v, dict):
            out.extend(_leaves(v, path + (k,)))
        else:
            out.append((path, k, v))
    return out


def _header(path: tuple[str, ...]) -> re.Pattern[str]:
    return re.compile(r"^\[\s*" + r"\s*\.\s*".join(map(re.escape, path)) + r"\s*\]\s*(#.*)?$")


def merge_toml(existing: str, fragment: str) -> tuple[str, list[str], list[str]]:
    """Add the fragment's keys that `existing` lacks. Returns the new text, the
    added keys and the keys the project has with another value."""
    have = tomllib.loads(existing)
    lines = existing.splitlines()
    added: list[str] = []
    kept: list[str] = []
    appended: dict[tuple[str, ...], list[str]] = {}
    for path, key, value in _leaves(tomllib.loads(fragment)):
        table = have
        for p in path:
            table = table.get(p, {}) if isinstance(table, dict) else {}
        dotted = ".".join(path + (key,))
        if isinstance(table, dict) and key in table:
            if table[key] != value:
                kept.append(dotted)
            continue
        added.append(dotted)
        entry = f"{key} = {_toml_value(value)}"
        hdr = _header(path)
        at = next((i for i, line in enumerate(lines) if hdr.match(line)), None)
        if at is None:
            appended.setdefault(path, []).append(entry)
            continue
        end = next(
            (i for i in range(at + 1, len(lines)) if lines[i].lstrip().startswith("[")), len(lines)
        )
        while end > at + 1 and not lines[end - 1].strip():
            end -= 1
        lines.insert(end, entry)
    for path, entries in appended.items():
        if lines and lines[-1].strip():
            lines.append("")
        lines.append("[" + ".".join(path) + "]")
        lines.extend(entries)
    text = "\n".join(lines) + "\n"
    try:
        tomllib.loads(text)
    except tomllib.TOMLDecodeError as e:
        raise Error(f"pyproject.toml would not parse after the merge ({e}); merge by hand") from e
    return text, added, kept


def merge_lines(existing: str, fragment: str) -> tuple[str, list[str]]:
    have = {line.strip() for line in existing.splitlines()}
    new: list[str] = []
    for line in fragment.splitlines():
        if line.strip() and not line.startswith("#") and line.strip() not in have:
            new.append(line)
            have.add(line.strip())
    if not new:
        return existing, []
    # Keep the template's comments above the lines they explain.
    block: list[str] = []
    comment: list[str] = []
    for line in fragment.splitlines():
        if line.startswith("#"):
            comment.append(line)
        elif line in new:
            block.extend(comment)
            comment = []
            block.append(line)
        elif not line.strip():
            comment = []
    text = existing if existing.endswith("\n") or not existing else existing + "\n"
    return text + "\n".join(block) + "\n", new


# --- commands -------------------------------------------------------------------


def repo_templates(lang: str) -> list[Path]:
    root = SKILL / "templates" / lang / "repo"
    return sorted(p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts)


def cmd_files(project: Path, dry_run: bool, check: bool, only: list[str]) -> int:
    values = load_values(project)
    lang = str(values["project.lang"])
    root = SKILL / "templates" / lang / "repo"
    others = {
        t.relative_to(d).as_posix()
        for d in (SKILL / "templates").glob("*/repo")
        if d.parent.name != lang
        for t in repo_templates(d.parent.name)
    }
    if lacking := sorted(others - {t.relative_to(root).as_posix() for t in repo_templates(lang)}):
        raise Error(
            f"templates/{lang}/repo/ lacks {', '.join(lacking)}, which another language has:"
            " translate them, or set lang to one that has them"
        )
    missing = 0
    rels = [
        t.relative_to(root).as_posix().replace("__pkg__", str(values["project.pkg"]))
        for t in repo_templates(str(values["project.lang"]))
    ]
    if unknown := sorted(set(only) - set(rels)):
        raise Error(f"no template for {', '.join(unknown)}; there are: {', '.join(rels)}")
    for tpl in repo_templates(str(values["project.lang"])):
        rel = tpl.relative_to(root).as_posix().replace("__pkg__", str(values["project.pkg"]))
        if only and rel not in only:
            continue
        text = render(tpl.read_text(), values, f"templates/{values['project.lang']}/repo/{rel}")
        if not text.strip():
            continue  # every line is for a component the project does not connect
        target = project / rel
        exists = target.is_file()
        old = target.read_text() if exists else ""
        if rel == "pyproject.toml":
            if not exists:
                # A fragment, not a project: the skeleton or `uv init` writes it.
                print(
                    f"{'missing':11} {rel}: create it first (lightning-hydra scaffold.py or uv init)"
                )
                missing += 1
                continue
            new, added, kept = merge_toml(old, text)
            if check:
                print(f"{'missing' if added else 'same':8} {rel}")
                for k in added:
                    print(f"missing  {rel}: {k}")
                missing += len(added)
            else:
                for k in added:
                    print(f"{'would add' if dry_run else 'added':11} {rel}: {k}")
                if not dry_run and new != old:
                    target.write_text(new)
            for k in kept:
                print(f"{'keeps':11} {rel}: {k} (the project's value)")
            continue
        if rel == ".gitignore":
            new, added_lines = merge_lines(old, text) if exists else (text, [])
            if check:
                print(f"{'same' if exists and not added_lines else 'missing':8} {rel}")
                for line in added_lines:
                    print(f"missing  {rel}: {line}")
                missing += (not exists) + len(added_lines)
            else:
                if not exists:
                    print(f"{'would write' if dry_run else 'wrote':11} {rel}")
                for line in added_lines:
                    print(f"{'would add' if dry_run else 'added':11} {rel}: {line}")
                if not dry_run and new != old:
                    target.write_text(new)
            continue
        if check:
            status = "missing" if not exists else ("same" if old == text else "differs")
            print(f"{status:8} {rel}")
            missing += not exists
            continue
        if exists:
            print(f"{'exists':11} {rel}")
            continue
        print(f"{'would write' if dry_run else 'wrote':11} {rel}")
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
            if os.access(tpl, os.X_OK):
                target.chmod(0o755)
    return 1 if check and missing else 0


def cmd_fragment(project: Path, name: str) -> int:
    values = load_values(project)
    lang = str(values["project.lang"])
    path = SKILL / "templates" / lang / f"{name}.md"
    if not path.is_file():
        names = sorted(
            p.relative_to(SKILL / "templates" / lang).with_suffix("").as_posix()
            for p in (SKILL / "templates" / lang).rglob("*.md")
            if not {"repo", "parts"} & set(p.relative_to(SKILL / "templates" / lang).parts)
        )
        elsewhere = sorted(
            p.relative_to(SKILL / "templates").parts[0]
            for p in (SKILL / "templates").glob(f"*/{name}.md")
            if p.is_file()
        )
        if elsewhere:
            raise Error(
                f"no fragment {name!r} in templates/{lang}/, only in {', '.join(elsewhere)}:"
                " translate it, or set lang to one that has it"
            )
        raise Error(f"no fragment {name!r}; there are: {', '.join(names)}")
    sys.stdout.write(render(path.read_text(), values, f"templates/{lang}/{name}.md"))
    return 0


def cmd_values(project: Path) -> int:
    for key, value in load_values(project).items():
        if not key.startswith("_"):
            print(f"{key} = {value}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("files", help="render the repository files")
    f.add_argument("project", nargs="?", default=".")
    mode = f.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--check", action="store_true")
    f.add_argument("--only", action="append", default=[], metavar="PATH", help="just this file")
    g = sub.add_parser("fragment", help="print a rendered fragment")
    g.add_argument("name")
    g.add_argument("project", nargs="?", default=".")
    v = sub.add_parser("values", help="print the values")
    v.add_argument("project", nargs="?", default=".")
    args = ap.parse_args(argv)
    project = Path(args.project).resolve()
    try:
        if args.cmd == "files":
            return cmd_files(project, args.dry_run, args.check, args.only)
        if args.cmd == "fragment":
            return cmd_fragment(project, args.name)
        return cmd_values(project)
    except Error as e:
        print(f"render.py: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
