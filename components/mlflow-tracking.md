# mlflow-tracking

## Purpose

Runs logged to MLflow with reproducibility tags (`git.sha`,
`runner.task_id`, `exp`), checkpoints by MLflow run id, resuming, and
finding runs back for the log. Connected in every training project.

Where runs go is the infrastructure's: `infra:mlflow_uri`. A database in the project
(`sqlite:///logs/mlflow.db`, SKILL.md "Local store") needs no login and
suits runs on one machine; a server (`infra:mlflow_login` true) gives every
member a personal login.

## From people

- With a local store: none.
- With a server: a personal login with a password that is the server's own;
  from the administrator. SKILL.md, "Secrets". Administrator: the login;
  multipart upload on the server for large artifacts (SKILL.md,
  "Checkpoints"). The project's author grants the login access to the
  project's experiment (`access.py`, SKILL.md "Access to the experiment").

Access row: SKILL.md, end of "Secrets"; only with a server.

| access | file, section | keys | where to get | where needed | check |
|---|---|---|---|---|---|
{{#if infra.mlflow_login}}
| MLflow | `~/.mlflow/credentials`, `[mlflow]` | `mlflow_tracking_username`, `mlflow_tracking_password` | a personal login on the MLflow server (<infra:mlflow_uri>), from the administrator; a password for MLflow only | laptop{{#if transport}}, HPC home{{/if}} | `doctor.py` there |
{{/if}}

The same rows in Russian (`render.py` copies the table of the project's
language into README and the access protocol):

| доступ | файл и секция | ключи | где взять | где нужен | проверка |
|---|---|---|---|---|---|
{{#if infra.mlflow_login}}
| MLflow | `~/.mlflow/credentials`, `[mlflow]` | `mlflow_tracking_username`, `mlflow_tracking_password` | личный логин на сервере MLflow (<infra:mlflow_uri>), у администратора; пароль только от MLflow | ноутбук{{#if transport}}, HPC-home{{/if}} | `doctor.py` там же |
{{/if}}

## Roles

- Fills: run tracker.
- Requires: none. With a transport, the transport's part is in SKILL.md
  "Transport" and in the transport's adapter (login on the remote side,
  `RUNNER_*`, Hydra output directories).
- With the skeleton: `integrations/lightning.md`, `integrations/hydra.md`
  fill the lightning-hydra docking points (logger, Hydra callback,
  checkpoints, resume).
- With the log: SKILL.md "research-log" (`record_run.py --tracker mlflow`).

## Connecting

SKILL.md, "Connecting a project".

Installed at step 0 by `install_components.py`; connecting does not run
its `install.sh` again (from the installed copy it syncs the copy onto
itself and deletes it).

Stays in the repository:

- `src/<pkg>/tracking.py` from `templates/__pkg__/tracking.py`; with
  Lightning and Hydra also `mlflow_lightning.py`, `mlflow_hydra.py`
  (integrations). `__pkg__` in the copies becomes the package name.
- `mlflow-skinny` in dependencies (`uv add mlflow-skinny`, framework.md
  step 2.3); with a local store also `sqlalchemy` and `alembic` (SKILL.md,
  "Local store").
- `mlflow.toml`: `tracking_uri` = `infra:mlflow_uri`, `experiment` = project
  name; `shared_checkpoints` only when the transport's adapter asks for it
  (a checkpoint root several users' tasks write to). The experiment is
  created by the first run.
- `.gitignore`: nothing of its own; a local store lives under `logs/`,
  which the skeleton ignores.
- `AGENTS.md`: `Runs are tracked with the mlflow-tracking skill (src/<pkg>/tracking.py, mlflow.toml).`
- With a server: the access row in README; `conventions-local.md` tools
  row "MLflow server" (`render.py`).

## Checking

- Locally: `uv run python <mlflow-tracking>/scripts/doctor.py`, all `ok`
  (with a local store: the database is writable).
- End to end: `find_runs.py --task-id <task_id>` (or, locally, the
  experiment's last run) finds the smoke run `FINISHED` with `git.sha` =
  the commit; `show_run.py` shows the checkpoint with its sha256. With a
  transport, `doctor.py` from the remote side first (the transport's
  adapter).
