# research-log

## Purpose

The project's record of what the work established: hypotheses,
experiments, technotes, findings, protocols, decisions, with stable ids.
Always connected; it is where the brief becomes `vision.md`. The smoke
run is not a log entry: smoke and debug runs go to the task tracker (the
skill's `docs/conventions.md`), here the setup task's Notes.

## From people

- Credentials: none.
- Administrator: none. The hosting settings that keep the server from
  rewriting branches unseen are the project owner's:
  `references/git-hosting.md` of the skill.
- The person starting the project: the brief, read back and corrected
  (`references/initialisation.md`, "The brief"); decisions to freeze before
  the first computation, if any.

## Roles

- Fills: log.
- Requires: none. Takes task ids from a board in `motivated_by` of an
  experiment, one free-form string; takes MLflow run ids through
  `record_run.py --tracker mlflow --run-id` (mlflow-tracking, section
  "research-log").

## Connecting

Follow `references/initialisation.md` of the skill from step 0; do not run
`init.py` directly. ml-scaffold feeds it:

- the brief, with what ml-scaffold needs from it (`SKILL.md`, "Brief");
- `conventions-local.md`: what the project's stack is, from the repository
  files ml-scaffold has rendered by then, plus the sections `framework.md`
  writes (the components' sections, access). The skill's presets
  (`presets/python-uv.md`, `python-qa.md`, `structural-bio.md`) are the
  starting point the procedure offers; take them through it, without a
  reference back to `presets/`.

Installed at step 0 by `install_components.py`; connecting does not run
its `install.sh` again (from the installed copy it syncs the copy onto
itself and deletes it).

Stays in the repository:

- `docs/` board: `.research-log.md`, `conventions.md` (the skill's),
  `conventions-local.md`, `vision.md`, kind directories.
- `AGENTS.md`: the section from `templates/<lang>/agents-section.md`.
- Hooks: `rebase_runs.py --install-hooks` once per clone (git does not copy
  hooks), named in `AGENTS.md` and README "new clone".
- Pre-commit: `check.py`, `index.py --check`, on `^docs/`.
- CI: `GIT_DEPTH: 0` for `check.py` (it needs the whole history and the
  `research-log/*` tags).

## Checking

- Locally: `python3 <research-log>/scripts/index.py && python3 <research-log>/scripts/check.py`.
- End to end: `check.py` passes with the protocols ml-scaffold puts in
  (access setup and those of the adapters) and `vision.md`.
