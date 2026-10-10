# task-tracker

## Purpose

Tasks and specs of the project in `docs/tasks/` and `docs/specs/`. Always
connected: the first tasks from the brief go here, and the agent that takes
the project over works from this board.

## From people

- Credentials: none.
- Administrator: none.

## Roles

- Fills: board.
- Requires: none. The one tie to research-log is an experiment's
  `motivated_by`, holding a task id.

## Connecting

The skill has no initialisation: it builds `docs/tasks/` and `docs/specs/`
on first use (`new.py`).

Installed at step 0 by `install_components.py`; connecting does not run
its `install.sh` again (from the installed copy it syncs the copy onto
itself and deletes it).

Stays in the repository:

- `.gitignore`: `docs/tasks/_handoffs/` (SKILL.md, "Resume state"). The
  board lock is outside the repository (task-tracker fb483f5); older
  installs wrote `docs/tasks/.tt.lock` and need it ignored too.
- Pre-commit: `index.py --board docs --check` on `^docs/`, `refs.py --check`
  on every commit.
- Access rows: none.
- `AGENTS.md`: `Tasks and specs live in docs/tasks/ and docs/specs/ and are worked through the task-tracker skill.`
  The skill is standalone and has no connecting section; this adapter is
  where its connection is defined.
- `docs/.task-tracker.md` only if a setting differs from the defaults.

## Checking

- Locally: `index.py --board docs --check`, `refs.py --check`.
- End to end: the first tasks from the brief exist and `next.py --all`
  lists them.
