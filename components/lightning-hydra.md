# lightning-hydra

## Purpose

Training skeleton on PyTorch Lightning + Hydra: one entry point
`scripts/train.py`, code in `src/<pkg>/{data,model,utils}`, config groups,
experiments as files, torch + PyG for Mac (MPS) and Linux (CUDA) from one
`uv.lock`. Connected in every training project; trains locally with no
external service.

## From people

- Credentials: none (SKILL.md, "Deploying into a project").
- The developer: the Python version, if they want other than the
  skeleton's default (`python` in `ml-scaffold.toml`, from the brief or
  asked). Supported versions and why the others are not: SKILL.md,
  "Environment".
- Administrator: none. The network must reach `data.pyg.org` and
  `download.pytorch.org` for `uv lock` (SKILL.md, "Environment").

## Roles

- Fills: skeleton.
- Requires: none. Offers docking points (SKILL.md, "Docking points"):
  - logger, Hydra callback, checkpoints, resume: filled by the run tracker,
    mlflow-tracking `integrations/lightning.md` and `integrations/hydra.md`;
  - `hydra.run.dir`, `hydra.sweep.dir`, `paths.log_dir`: filled by the
    transport (its adapter, "Step 2"), so that a remote task's outputs
    come back;
  - `configs/data/` fields: the data source, paths `data/<path>`.

## Connecting

SKILL.md, "Deploying into a project": `scaffold.py <project> --pkg <name>
[--python <version>]`; it refuses a version the skeleton does not run on,
with the reason, which goes to the developer as it is.
It writes only missing files and lists the existing ones (`pyproject.toml`,
`.gitignore`) for a merge by hand; ml-scaffold runs it before rendering its
own repository files or merges after, by the order in `framework.md`.

Installed at step 0 by `install_components.py`; connecting does not run
its `install.sh` again (from the installed copy it syncs the copy onto
itself and deletes it).

Stays in the repository:

- the skeleton: `src/<pkg>/`, `scripts/train.py`, `configs/`,
  `tests/test_train.py`, `configs/README.md`, `src/README.md`;
- `pyproject.toml`: torch, PyG, Lightning, Hydra, indexes with platform
  markers, `[tool.uv]` environments;
- `.gitignore`: `logs/`;
- `.python-version`: the interpreter, locally and in remote tasks;
- `AGENTS.md`: `Training follows the lightning-hydra skill: entry point scripts/train.py, configs in configs/ (see configs/README.md), outputs in logs/.`

## Checking

- Locally: `uv run pytest` (the smoke test runs `train.py trainer=debug`);
  `python scripts/train.py --cfg job` for the resolved config.
- End to end: `train.py` with the debug trainer in the smoke run
  (`framework.md`, step 5): locally, or in a remote task through the
  transport. On GPU not yet part of the skill (its GPU smoke task is
  planned).
