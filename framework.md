# Framework: setup order and ties

How a new project is set up from a brief to a green smoke run: on the
machine of the person, or, when a transport is connected, on its remote
side. Each component is connected by its own instructions, through its
adapter in [`components/`](components/); this file says in which order,
what ties three or more components together, and where a person has to
act. What a component adds to a step is in its adapter, under that step
([`components/README.md`](components/README.md), "Setup steps"): read the
adapters of the connected components at every step, in the order of
`components`.

`<skill>` below is this skill's directory, `<c>` a component's directory in
the project (`.agents/skills/<c>`). Values written `{{…}}` come from
`render.py values` (project file and [`infra.toml`](infra.toml)).

## Values

The project's values live in `ml-scaffold.toml` at its root, copied from
[`templates/ml-scaffold.toml`](templates/ml-scaffold.toml) at step 0 and
committed. Infrastructure values are the skill's defaults: take them, do not ask.

```bash
python3 <skill>/scripts/render.py values
```

| value | example (`name = "ddg"`) | used by |
|---|---|---|
| `project.name` | `ddg` | MLflow experiment; what the adapters name after the project |
| `project.pkg` | `ddg` | `src/<pkg>/`, `scaffold.py --pkg` |
| `runs_env` | `DDG_RUNS` | root of run directories: checkpoints and other heavy outputs |

`infra.toml` `[derived]` makes the values above from the project's; an
infrastructure with its own components adds theirs there, and their adapters say where
they go.

## Who does what

- The output of a command that creates something (a resource, a task, a
  board item) is read whole, never cut with `tail`, `head` or `grep`: the
  id it prints is needed next, and listing commands may not find it again.
- The agent runs everything, the transport's tasks included, without
  asking for each, once the person has answered the transport's paragraph
  in the message of step 1 (the transport's adapter, "Step 1": what the
  agent runs, what it never does, and where the project keeps the answer).
  "Continue", "go on" or "продолжай" is not that answer: without a yes or
  a no to the paragraph itself, ask it again. If the person says no, every
  such command goes to them as a command block, and each such stop is
  noted in the setup task.
- The agent never opens a credentials file and never puts a secret in a
  command. It learns the state of access from the components' checks
  (each adapter's "Checking"); a component that moves credentials
  elsewhere reads the file itself and prints names and outcomes, never
  values.
- The person: the brief, the project's name when the request gives none
  (step 0.2, the first stop), the answers to step 1's message when it has
  something to ask (one message, then the agent waits), and what the access protocol's checks did not
  find (step 3, one message, then wait; none when everything is in
  place). Access set up before (another project, an earlier run) is found
  by the protocol's checks and not asked about. After step 3 the setup
  runs without them up to the smoke run. A stop for anything else is a gap
  of the skill: record it in the setup task (below) for the skill's board.
- Other projects on the machine (an earlier project of the same name, a
  sibling checkout) are not read to fill this one: the setup works from
  the brief, the skill and the components. A project the brief names as
  a source of data or code is a first task (step 6), not a template.

## Order

Every step ends with a check; the checks are what a resumed session reads
to find where it stopped (see [Resuming](#resuming)). Commit at the end of
every step, in the project's format from the first commit on, though its
`commit-msg` hook comes only at step 2: Conventional Commits, English,
imperative, at most 72 characters, the setup task's id in parentheses at
the end (`conventions-local.md`, the commit messages section); not in the
scope, which is a part of the code and admits no dot. Step 0 has no task yet:

```text
chore: install components and agent settings
docs: add brief, research log and setup task (0001.xxx)
chore: scaffold skeleton, configs and protocols (0001.xxx)
```

### 0. Directory, components

1. An empty directory (or one with only the brief), `git init`. A project
   that already has code is not set up by this skill (not yet).
   The directory is the one the person names; when the session runs in
   another empty directory, ask which before writing anything.
   When the person's request carries the brief ([`SKILL.md`](SKILL.md),
   "Brief"), write it to `docs/brief.md` now, in their words, before
   anything else: a restart at 0.4 starts a new session that no longer
   has the request, only the files.
2. `ml-scaffold.toml` from the template: name and package by
   [`SKILL.md`](SKILL.md), "Brief" (a name the person gave for the project
   or its repository comes before the directory's name), `lang`, the
   components. Every component of the template is connected by default;
   drop one only when the user says so. A name the person's request or
   the brief gives for the project or its repository is taken without
   asking. When they give none, this is the setup's first stop, before
   anything is installed: one message with the proposed name (the
   directory's, else from the brief's title) and what it names (the
   package, the MLflow experiment, what the adapters name after the
   project), then wait. Its Notes entry goes into the setup task once
   there is one (step 1.2). A name given with the request is the way to
   send the agent through the whole setup without a stop. After step 2 a
   new name is a rename of the package; after step 4, new resources too.
3. Install the components into the project: [`SKILL.md`](SKILL.md),
   "Installing components" (`install_components.py`), full output. It
   writes `skills.lock`.

4. **Agent settings**, before any credential exists or is asked for: the
   agent's own tools may not read the credential files (accidental
   leaks; a sandbox is not part of this skill yet).

   ```bash
   python3 <skill>/scripts/render.py files --only .claude/settings.json --only opencode.json
   mkdir -p ~/.config/ml-scaffold && echo probe > ~/.config/ml-scaffold/deny-probe
   ```

   Then read `~/.config/ml-scaffold/deny-probe` with the agent's own file
   tool (Read in Claude Code, read in OpenCode); it is in the deny lists
   with the credential files. Refused: the settings are in effect. Read:
   they are not, because the session runs outside the project directory
   or the tool loads project settings only at start. If the agent can move
   its own session into the project directory (`change_directory` in the
   Claude desktop app), it does so and reads the probe again on its next
   turn: refused there, go on. Still read, or no way to move (Claude Code
   in a terminal, OpenCode): ask the person to restart the agent in the
   project directory and resume. That message is also step 1's message
   (step 1.1: the questions, the transport's paragraph), so
   that the person answers it once, in the new session; note it in the
   setup task as soon as there is one. A file
   reported as `exists`: merge its deny list by hand. Codex has no
   project-level deny that leaves the components' own scripts working:
   there the rule is `AGENTS.md`'s, and the access protocol
   recommends an ssh key with a passphrase. The access protocol repeats
   this probe as its step 1, for those who join later.

Check: `install_components.py --check` prints `ok` for every component;
the agent's read of the deny probe is refused.

### 1. Brief → log and board

1. research-log, `references/initialisation.md` of the skill, steps 0–2:
   the brief, then `init.py`. The brief lives in `docs/brief.md`, not at
   the root (`init.py` finds it there; one already at the root is moved
   with `git mv`): it is the assignment as given, kept for whoever later
   asks how far `vision.md` has moved from it, and the project's
   `README.md` links it. When the person's request already carries the
   question, it is the brief: [`SKILL.md`](SKILL.md), "Brief". What
   ml-scaffold needs from the brief beyond that procedure, and the default
   for each fact the brief leaves out: the same section, and `render.py
   fragment brief`; the name is already settled (0.2). Stop
   at "3. What init.py leaves": `conventions-local.md` is written at step
   2, when the repository has files to read.

   A message to the person at this step only when there is something to
   ask, unless 0.4's restart line already carried it: research-log's one
   round of questions, if any; the transport's paragraph (its adapter,
   "Step 1"), when a transport is connected. The name is settled at 0.2
   and is not asked again. The message ends the agent's turn: it is the
   one stop before step 3, and with its answer step 3 stops only for
   missing credentials. Write it to the person first, then its Notes
   entry in the setup task (date, what was asked); the answer gets its
   own entry when it comes. A Notes entry is never written for a message
   that has not been sent. Nothing to ask: no message, a Notes entry
   saying so, and on to step 2.
2. The setup task on the project's board (task-tracker), from
   [`templates/<lang>/setup-task.md`](templates/en/setup-task.md):

   ```bash
   python3 .agents/skills/task-tracker/scripts/new.py task "Project setup by ml-scaffold" --priority high
   ```

   then its body from `render.py fragment setup-task`. Its checklist is
   steps 2–6; its Notes collect every stop for a person and every
   deviation from this file. It also gives `refs.py --check` a board to
   scan from the first commit.

Check: `docs/vision.md` has the question; `next.py --all` (task-tracker)
shows the setup task in progress; its Notes have step 1's message or
that none was needed, the answer to the name's question when 0.2 asked
it, and, with a transport, the answer to its paragraph.

### 2. Skeleton, connections, repository files

No credentials yet; nothing here needs the network beyond package indexes.

1. Skeleton (lightning-hydra adapter):
   `scaffold.py . --pkg <pkg> [--python <python>]`, with `python` from
   `ml-scaffold.toml` when set. It writes `pyproject.toml`, `.gitignore`
   and `.python-version`; everything after merges into them.
   **Python version.** `uv.lock` pins packages, not the interpreter: without
   `.python-version` uv takes whatever installed Python fits
   `requires-python`, and where no Python is installed (a remote task's
   image) downloads the newest allowed one. `.python-version` is read
   locally and in remote tasks, and a transport may key its environment
   on it; commit it. A version the skeleton does not run on is refused
   with the reason (exit 2): give the developer that reason and the
   supported versions, and let them choose; never substitute one
   silently. (On 2026-10-04, without it, a remote task got 3.14.2 while
   the laptop had 3.12.6, and Hydra 1.3 failed.)
2. Components, each by its adapter's "Connecting", in the order of
   `components` (research-log and task-tracker are already in from step 1,
   the skeleton from 2.1), with the values of [Values for the components'
   own files](#values-for-the-components-own-files). Connecting is the
   component's copy and config steps: it was installed at step 0, and its
   `install.sh` is not run again. Each adds its own
   `AGENTS.md` line under the components heading and its own `.gitignore`
   line. The `AGENTS.md` lines go in after step 2.4 writes the file.
3. Dependencies, before the repository files (a `default-groups` entry
   naming a missing group stops every `uv` command): the development tools,
   then what each adapter's "Connecting" adds, in the same order.

   ```bash
   uv add --dev pre-commit pyright pytest ruff
   uv add mlflow-skinny    # mlflow-tracking
   uv add sqlalchemy alembic    # mlflow-tracking with a local store (infra.mlflow_uri sqlite:)
   ```

4. Repository files:

   ```bash
   python3 <skill>/scripts/render.py files --dry-run
   python3 <skill>/scripts/render.py files
   ```

   It writes `AGENTS.md`, `README.md`, `.pre-commit-config.yaml`, the
   agent settings, `scripts/log_smoke_run.py` (with mlflow-tracking) and
   the files the connected components' templates add; appends to
   `.gitignore`, adds keys to `pyproject.toml`. What it reports as
   `exists` or `keeps` is the project's; leave it.
5. What the adapters add at step 2 ("Step 2" of each): a transport's
   output directories in the skeleton's configs, for one.
6. research-log, `initialisation.md` step 3 onwards: `AGENTS.md` section,
   `vision.md` read-back, `conventions-local.md`. None of the three waits
   for the user: what the procedure would show them goes into the step 6
   report, and they correct it there. For the last, read the
   repository as the procedure says (it now has `pyproject.toml`, the
   skeleton, the configs), take the presets it offers for the stack and
   tests, and merge in the sections of `render.py fragment
   conventions-local` (tools rows, the components' sections, access,
   commit messages, skills).
7. Protocols (research-log `new.py protocol`), bodies from the templates:
   access, always: `render.py fragment protocols/access`, slug
   `access-setup`; the protocols the adapters name in their "Step 2".
8. `uv sync`, `uv run pytest`, `uv run pre-commit install`, the research-log
   hooks (`rebase_runs.py --install-hooks`), `git add -A`, `uv run
   pre-commit run --all-files`. The first run of `ruff format` reformats
   the copied mlflow-tracking templates to the skeleton's line length: add
   them and run again. Commit `.agents/`, `.claude/skills/`, `skills.lock`
   and the rest in one commit naming the setup task.

Check: `.python-version` is committed; `render.py files --check` exits 0;
`uv run pytest` passes;
`pre-commit run --all-files` passes (component gaps: see
[Known gaps](#known-gaps)); each adapter's local check ("Checking").

### 3. Access

The project's access protocol (`docs/protocols/`, slug `access-setup`),
every step, as anyone who joins later does: its checks find what is in
place, one message asks for the rest (the transport's paragraph was
already sent at step 1: not again), the agent waits and checks again.
What the components change about it at setup is in their adapters'
"Step 3". No message at all when the checks find everything and, with a
transport, its answer has come at step 1. Note the date of the message,
or that none was needed, in the setup task.

Check: the protocol's "How you know it worked", as the adapters' "Step 3"
narrows it.

### 4. Resources

What the adapters' "Step 4" make, in the order of `components`: the
transport's storage, the data source's datasets. Ids go to
`ml-scaffold.toml` `[resources]` and where each adapter says; commit.
No adapter has a "Step 4": nothing to do, go to step 5. The MLflow
experiment needs nothing: the first run creates it.

Check: each adapter's "Step 4" check.

### 5. Smoke run

With a transport: its adapter's "Step 5", whole; the other adapters'
"Step 5" add to it (what a task needs from them). Without one, locally,
from the committed tree:

1. **Tracking, no training** (mlflow-tracking): what a training run logs,
   with a fake checkpoint.

   ```bash
   uv run python .agents/skills/mlflow-tracking/scripts/doctor.py && uv run python scripts/log_smoke_run.py
   ```

   Every doctor line `ok`; then `find_runs.py --sha "$(git rev-parse HEAD)"`
   (FINISHED, `git.sha`), `show_run.py <run id>` (checkpoint with sha256).
   With the default local store the run is in `logs/mlflow.db`.
2. **Training, debug trainer**: one batch of train, val and test through
   the skeleton.

   ```bash
   uv run python scripts/train.py trainer=debug
   ```

   Exit code 0, Hydra's `.hydra/config.yaml` under
   `logs/runs/default/<date_time>/`. It logs to MLflow when the skeleton's
   logger docking point is filled by the run tracker (mlflow-tracking's
   Lightning integration as configs, not yet); until then it logs CSV
   into `logs/`, and the MLflow part of the end-to-end check is stage 1.
3. Record: one Notes entry of the setup task for both stages: the commit,
   the MLflow run id of stage 1, and what went wrong. Not a technote:
   smoke and debug runs go to the task tracker (research-log
   `docs/conventions.md`, where a document goes).

Check: the setup task's Notes have the smoke entry with the commit and the
stage 1 MLflow run id (with a transport, what its "Step 5" adds).

### 6. First tasks and handoff

1. First tasks from the brief on the project's board: rules in
   [`SKILL.md`](SKILL.md), "First tasks". Before the commit, check each
   against them: a task that waits on a person is `blocked` with
   `blocked_by`; no path outside the repository (`~/…`, another project's
   checkout): name the source so that someone on another machine finds it
   (a repository URL, a registry dataset), or ask the person for one.
2. Handoff for the agent that takes the project over: the setup task's last
   Notes entry, from `render.py fragment handoff`, filled in. It is
   committed, unlike `docs/tasks/_handoffs/` (per-session resume state,
   ignored by git), because the next agent may start from a fresh clone.
3. Close the setup task (`status: done`), commit, and tell the user what
   works, one line per step, what is waiting on whom, and what to read
   and correct (step 2.6): the `vision.md` question, the `AGENTS.md`
   section, `docs/conventions-local.md`, and the defaults taken for what
   the brief left out ([`SKILL.md`](SKILL.md), "Brief").
4. The remote, if the person gives it: `git remote add origin <url>`. No
   push: the first push publishes the repository and starts its CI, and
   it waits for the person's own word for it, a separate one from the
   URL. The handoff names it among what waits on whom.

## Ties

A tie touches three components or more, or a component and a project
resource. A tie of two components is written by the one whose commands it
contains, and a tie that involves a component this file does not know of
is in that component's adapter ("Ties"); this table points there.

| tie | components | where | check |
|---|---|---|---|
| checkpoints of training | lightning-hydra, mlflow-tracking, run directories | the tracker's integration fills the checkpoint docking point with root `${oc.env:{{runs_env}},logs/ckpt}` | when mlflow-tracking's Lightning integration as configs is done |
| smoke run | all | step 5 | the setup task's Notes entry of step 5 |

### Values for the components' own files

Each component copies its own config template at step 2; fill it with
the values below and those of its adapter ("Values"):

| file | key | value |
|---|---|---|
| `mlflow.toml` | `tracking_uri` | `{{infra.mlflow_uri}}` |
| | `experiment` | `{{project.name}}` |

## Resuming

A new session continues from the setup task: its checklist says which steps
are done, its Notes what was waiting on whom. Then the check of the first
step not done, which is also how to tell a step done by hand:

| step | done when |
|---|---|
| 0 | `ml-scaffold.toml` exists, `install_components.py --check` all `ok`, the deny probe refused |
| 1 | `docs/vision.md`, the setup task on the board, its Notes with step 1's message and the answer to it, or that none was needed (a message with no answer noted: ask again, whatever a summary of an earlier session says) |
| 2 | `.python-version` committed, `render.py files --check` exit 0, `pre-commit run --all-files` passes |
| 3 | the access protocol's checks clean, and what the adapters' "Step 3" asks noted in the setup task |
| 4 | each adapter's "Step 4" check; no "Step 4": nothing |
| 5 | the smoke entry in the setup task's Notes |
| 6 | first tasks on the board, the setup task `done` |

`install_components.py --check` says `differs` for ml-scaffold when the
skill installed now is not the revision the setup started under
(`skills.lock`): go on by the installed one, and name the difference in
the setup task's Notes; the earlier rules are in the skill's git.

A task submitted to a transport but not fetched: its adapter says how to
find it before submitting it again.

## Known gaps

Recorded on the components' boards; until they close, the setup notes them
and goes on. The adapters list their own.

- mlflow-tracking: Lightning integration as configs is not there yet; until then,
  the smoke run's training stage logs no MLflow run.
