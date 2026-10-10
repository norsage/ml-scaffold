#!/usr/bin/env python3
"""Install the project's component skills and pin what was installed.

    python3 install_components.py [PROJECT] [--source NAME=PATH ...] [--worktree] [--only NAME ...]
    python3 install_components.py [PROJECT] --check

Reads the components from PROJECT/ml-scaffold.toml and their sources from the
skill's skills.toml. Each component is installed with its own
`install.sh --project`, run in the project root, into .agents/skills/<name>/
with a link from .claude/skills/<name>; its full output is printed.

By default the committed tree at `rev` (empty: HEAD) is installed, taken with
`git archive`, so the pinned revision describes the installed files exactly.
--worktree installs the checkout as it is, uncommitted changes included, and
records `worktree = true`: for a component under development, not for a
project handed over.

skills.lock in the project root records, per component, the source, the
revision, and a sha256 over the installed files; also the revision of
ml-scaffold itself. Commit it with .agents/ and .claude/.

--check writes nothing: per component `ok`, `modified` (the installed files
differ from the lock: edited in place), `missing` or `unlocked`, and `behind`
when the source has moved past the pinned revision (information only);
`differs` when ml-scaffold itself is not the revision the lock records
(information: a setup resumed after an update). Exit 1 if any component is
not `ok` or `behind`.

Exit 0 on success, 1 on a failed install or check, 2 on bad input.
Python 3.11+ standard library only; needs git and bash.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import tomllib
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
LOCK = "skills.lock"
CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "ml-scaffold" / "sources"


class Error(Exception):
    pass


def git(*args: str, cwd: Path) -> str:
    out = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)
    if out.returncode != 0:
        raise Error(f"git {' '.join(args)} in {cwd}: {out.stderr.strip()}")
    return out.stdout.strip()


def tree_hash(root: Path) -> str:
    """sha256 over the sorted relative paths and contents of the installed
    files; symlinks by their target."""
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if "__pycache__" in p.parts or p.name == ".DS_Store":
            continue
        rel = p.relative_to(root).as_posix()
        if p.is_symlink():
            h.update(f"L {rel} {os.readlink(p)}\n".encode())
        elif p.is_file():
            h.update(f"F {rel} {hashlib.sha256(p.read_bytes()).hexdigest()}\n".encode())
    return "sha256:" + h.hexdigest()


def components(project: Path) -> list[str]:
    path = project / "ml-scaffold.toml"
    if not path.is_file():
        raise Error(f"{path} not found (framework.md, step 0)")
    comps = tomllib.loads(path.read_text()).get("project", {}).get("components", [])
    if not comps:
        raise Error(f"{path}: [project] components is empty")
    return comps


def sources(overrides: list[str]) -> dict[str, dict[str, str]]:
    src = tomllib.loads((SKILL / "skills.toml").read_text())
    for o in overrides:
        name, sep, path = o.partition("=")
        if not sep:
            raise Error(f"--source {o!r}: expected NAME=PATH")
        src.setdefault(name, {})["path"] = path
        src[name]["git"] = ""
    return src


def resolve(name: str, src: dict[str, str]) -> tuple[Path, str]:
    """The checkout to install from, and the source to record."""
    path = Path(os.path.expanduser(src.get("path", ""))) if src.get("path") else None
    if path and (path / "SKILL.md").is_file():
        return path, src.get("git") or str(path)
    url = src.get("git")
    if not url:
        raise Error(f"{name}: no checkout at {src.get('path')!r} and no git remote in skills.toml")
    dest = CACHE / name
    if (dest / ".git").is_dir():
        git("remote", "set-url", "origin", url, cwd=dest)  # skills.toml may have moved
        git("fetch", "--quiet", "origin", cwd=dest)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        git("clone", "--quiet", url, str(dest), cwd=dest.parent)
    if not src.get("rev"):
        git("checkout", "--quiet", "--detach", "origin/HEAD", cwd=dest)
    return dest, url


def install(project: Path, name: str, src: dict[str, str], worktree: bool) -> dict[str, object]:
    checkout, source = resolve(name, src)
    rev = git("rev-parse", src.get("rev") or "HEAD", cwd=checkout)
    dirty = bool(git("status", "--porcelain", cwd=checkout))
    with tempfile.TemporaryDirectory(prefix=f"ml-scaffold-{name}-") as tmp:
        if worktree:
            from_dir = checkout
        else:
            archive = Path(tmp) / "src.tar"
            git("archive", "--format=tar", "-o", str(archive), rev, cwd=checkout)
            from_dir = Path(tmp) / name
            from_dir.mkdir()
            with tarfile.open(archive) as t:
                t.extractall(from_dir, filter="data")
        print(
            f"--- {name}: bash install.sh --project ({source} @ {rev[:12]}"
            f"{', worktree' + (' with uncommitted changes' if dirty else '') if worktree else ''})"
        )
        out = subprocess.run(
            ["bash", str(from_dir / "install.sh"), "--project"],
            cwd=project,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
        sys.stdout.write(out.stdout)
        sys.stderr.write(out.stderr)
        if out.returncode != 0:
            raise Error(f"{name}: install.sh exited {out.returncode}")
    installed = project / ".agents" / "skills" / name
    if not (installed / "SKILL.md").is_file():
        raise Error(f"{name}: install.sh did not produce {installed}/SKILL.md")
    if not worktree and dirty:
        print(
            f"note: {name}: the checkout has uncommitted changes; installed the commit {rev[:12]} without them"
        )
    entry: dict[str, object] = {"source": source, "rev": rev, "tree": tree_hash(installed)}
    if worktree:
        entry["worktree"] = True
    entry["installed"] = dt.datetime.now().astimezone().date().isoformat()  # local date
    return entry


def read_lock(project: Path) -> dict[str, dict]:
    path = project / LOCK
    return tomllib.loads(path.read_text()) if path.is_file() else {}


def write_lock(project: Path, lock: dict[str, dict]) -> None:
    lines = [
        "# Component skills installed in .agents/skills/, written by install_components.py",
        "# of ml-scaffold. Committed. `tree` is a sha256 over the installed files:",
        "# `install_components.py --check` tells an in-place edit from the pinned rev.",
    ]
    for name in sorted(lock, key=lambda n: (n != "ml-scaffold", n)):
        lines.append("")
        lines.append(f"[{name}]")
        for k, v in lock[name].items():
            lines.append(
                f"{k} = {'true' if v is True else 'false' if v is False else json.dumps(str(v))}"
            )
    (project / LOCK).write_text("\n".join(lines) + "\n")


def skill_entry() -> dict[str, object]:
    """This skill's source and revision. An installed copy has VERSION: the
    commit it came from, or `core@<sha>+<pack>@<sha>` for a build of the core
    with an organisation pack's files laid over it; `-dirty` after a sha marks a tree with
    uncommitted changes. The source is the remote it came from (SOURCE of an
    installed copy, origin of a checkout); a local path only without one."""
    entry: dict[str, object] = {"source": str(SKILL)}
    if (SKILL / "SOURCE").is_file():
        entry["source"] = (SKILL / "SOURCE").read_text().strip()
    else:
        try:
            entry["source"] = git("remote", "get-url", "origin", cwd=SKILL)
        except Error:
            pass
    if (SKILL / "VERSION").is_file():  # an installed copy (install.sh)
        rev = (SKILL / "VERSION").read_text().strip()
        entry["rev"] = rev.replace("-dirty", "")
        if "-dirty" in rev:
            entry["worktree"] = True
        return entry
    try:
        entry["rev"] = git("rev-parse", "HEAD", cwd=SKILL)
        if git("status", "--porcelain", cwd=SKILL):
            entry["worktree"] = True
    except Error:
        entry["rev"] = "unknown"
    return entry


def check(project: Path, src: dict[str, dict[str, str]]) -> int:
    lock = read_lock(project)
    bad = 0
    if "ml-scaffold" in lock and (now := skill_entry()["rev"]) != lock["ml-scaffold"].get("rev"):
        # Information: a setup resumed after the skill was updated follows
        # the rules of the installed revision, not those it started with.
        print(
            f"differs   ml-scaffold: {LOCK} has {lock['ml-scaffold'].get('rev')}, installed {now};"
            " the setup started under the other revision (git of the skill has it)"
        )
    for name in components(project):
        installed = project / ".agents" / "skills" / name
        link = project / ".claude" / "skills" / name
        if not (installed / "SKILL.md").is_file() or not link.exists():
            print(f"missing   {name}")
            bad += 1
            continue
        if name not in lock:
            print(f"unlocked  {name}")
            bad += 1
            continue
        if tree_hash(installed) != lock[name].get("tree"):
            print(f"modified  {name}: installed files differ from {LOCK}; reinstall or record why")
            bad += 1
            continue
        status = f"ok        {name} @ {str(lock[name].get('rev'))[:12]}"
        path = src.get(name, {}).get("path")
        checkout = Path(os.path.expanduser(path)) if path else None
        default = "HEAD"
        if not (checkout and (checkout / ".git").exists()):
            # The cache clone as of the last install: no network in a check.
            checkout, default = CACHE / name, "origin/HEAD"
        if (checkout / ".git").exists():
            try:
                head = git("rev-parse", src.get(name, {}).get("rev") or default, cwd=checkout)
                if head != lock[name].get("rev"):
                    status = f"behind    {name} @ {str(lock[name].get('rev'))[:12]}, source at {head[:12]}"
            except Error:
                pass
        print(status)
    return 1 if bad else 0


def exclude_bytecode(project: Path) -> None:
    """`__pycache__/` in the clone's own exclude file: the components' scripts
    run before step 2 brings `.gitignore`, and their bytecode must not reach
    the first commits. Local to the clone, so it never conflicts with the
    `.gitignore` that scaffold.py writes."""
    info = project / ".git" / "info"
    if not info.parent.is_dir():
        return
    exclude = info / "exclude"
    lines = exclude.read_text().splitlines() if exclude.exists() else []
    if "__pycache__/" not in lines:
        info.mkdir(exist_ok=True)
        exclude.write_text("\n".join([*lines, "__pycache__/"]) + "\n")
        print("added __pycache__/ to .git/info/exclude")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("project", nargs="?", default=".")
    ap.add_argument("--source", action="append", default=[], metavar="NAME=PATH")
    ap.add_argument("--only", action="append", default=[], metavar="NAME")
    ap.add_argument("--worktree", action="store_true", help="install checkouts as they are")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    project = Path(args.project).resolve()
    try:
        src = sources(args.source)
        if args.check:
            return check(project, src)
        wanted = components(project)
        names = args.only or wanted
        unknown = [n for n in names if n not in wanted]
        if unknown:
            raise Error(f"not in ml-scaffold.toml components: {', '.join(unknown)}")
        lock = read_lock(project)
        for name in names:
            if name not in src:
                raise Error(f"{name}: not in {SKILL / 'skills.toml'}")
            lock[name] = install(project, name, src[name], args.worktree)
        lock["ml-scaffold"] = skill_entry()
        write_lock(project, lock)
        exclude_bytecode(project)
        print(f"wrote {LOCK}")
        return 0
    except Error as e:
        print(f"install_components.py: {e}", file=sys.stderr)
        return 1 if "install.sh" in str(e) else 2


if __name__ == "__main__":
    sys.exit(main())
