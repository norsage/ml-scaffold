---
name: ml-scaffold
description: Sets up a new ML research project (Lightning + Hydra training, MLflow tracking, research log and task board, plus components of the organisation's own infrastructure such as remote runs or a data registry) from a brief and the person's credentials, up to a green smoke run recorded in the setup task on the project's board. Installs the component skills into the project and pins them, renders the repository files once, orders the components' own connecting steps, and asks the person only for the brief, credentials and administrator requests. Use when someone wants to start, bootstrap, scaffold or set up a new training or research project of this kind, or asks to deploy these skills together; when a directory has ml-scaffold.toml; or when resuming a setup whose board has the task "Project setup by ml-scaffold".
---

# ml-scaffold

Instructions, templates and two scripts for setting up a project on
component skills: research-log, task-tracker, mlflow-tracking and
lightning-hydra, and the infrastructure's own, added with their adapters. The components connect themselves, by their own
instructions; this skill says in which order, ties them together, and keeps
the person's part to the brief, credentials and administrator requests.

| file | what |
|---|---|
| [`framework.md`](framework.md) | the setup order, steps 0–6, the ties between components, how to resume |
| [`components/`](components/) | one adapter per component: what it needs from people, its roles, how it connects, how to check it |
| [`infra.toml`](infra.toml) | addresses and settings of the infrastructure: defaults, not questions |
| [`skills.toml`](skills.toml) | where each component is installed from |
| [`templates/`](templates/) | `ml-scaffold.toml` (the project's values) and, per language (`en`, `ru`), repository files, fragments and the components' parts |
| [`scripts/render.py`](scripts/render.py) | renders repository files and fragments with the project's values |
| [`scripts/install_components.py`](scripts/install_components.py) | installs the components into the project, writes `skills.lock` |

## Setting a project up

Follow [`framework.md`](framework.md) from step 0, in order. Before each
component's step, read its adapter in `components/`; the adapter names the
component's own section to follow, and that section is the authority.

Track the setup on the project's own board (framework.md, step 1): the
setup task's checklist is the progress, its Notes the log of every stop.
A resumed session starts there.

What only the person does, so that the rest runs without them up to the
smoke run:

| step | what | how to ask |
|---|---|---|
| 0 | the project's name, only when the request and the brief give none | the setup's first stop, one message with the proposed name and what it names, then wait: framework.md step 0.2 |
| 0 | only if the agent settings are still not in effect after the agent moved its session into the project: restart the agent there | one line, framework.md step 0.4 |
| 1 | the brief; questions only on what cannot be acted on; with a transport, the answer about its tasks | one message, then wait (with a restart at step 0, the same message); none when there is nothing to ask: research-log `references/initialisation.md`, defaults below ("Brief"), framework.md step 1 |
| 3 | what the access protocol's checks did not find | the protocol's one message, then wait; none if nothing is missing |

The agent runs the transport's tasks itself, once the person has answered
its paragraph (framework.md, "Who does what"). Anything else that needs
the person is a gap in this skill: do it, and record it in the setup
task's Notes so that it reaches this skill's board.

## Access: every participant

Access is set up by each person, not once per project: credentials live
in their home (and, with a transport, on its remote side), and most of
them serve every project. The procedure is a protocol the setup puts into the project
(framework.md, step 2.7, slug `access-setup`, from
[`templates/<lang>/protocols/access.md`](templates/en/protocols/access.md)),
so that whoever clones the project later finds it there, without this
skill: the project's `AGENTS.md` and README point to it. The creator
passes the same protocol at step 3; access set up before is found by its
checks and not asked about.

## Values

`ml-scaffold.toml` at the project root holds the project's values; copy
[`templates/ml-scaffold.toml`](templates/ml-scaffold.toml) and fill in
`[project]`. Infrastructure values come from [`infra.toml`](infra.toml); a project
overrides one in its `[infra]` table only for a reason the person gives.

```bash
python3 <skill>/scripts/render.py values
```

## Installing components

```bash
python3 <skill>/scripts/install_components.py
python3 <skill>/scripts/install_components.py --check
```

Each component's own `install.sh --project` runs in the project root, with
its full output; components land in `.agents/skills/<name>/`, linked from
`.claude/skills/<name>`. What is installed is the committed tree at the
revision in `skills.toml` (empty: the head of the default branch), so `skills.lock`
pins exactly what the project has: source, revision, a hash of the installed
files, and this skill's own revision. Commit `.agents/`, `.claude/skills/`
and `skills.lock` together.

- A component is cloned from its `git` remote into
  `~/.cache/ml-scaffold/sources/`. One with a local checkout in `path`
  (an infrastructure component with no remote yet) installs from it;
  `--source <component>=<path>` does the same for one run, while
  developing that component.
- `--worktree` installs a checkout with its uncommitted changes and records
  it; use it only while developing that component.
- `--check`: `ok`, `modified` (edited in place: the installed files are
  never edited; the change goes to the component's source), `missing`,
  `unlocked`, and `behind` when the source has moved on (information).
- Updating components in a deployed project: not yet.

## Repository files

```bash
python3 <skill>/scripts/render.py files --dry-run
python3 <skill>/scripts/render.py files
python3 <skill>/scripts/render.py files --check
```

Written once, then the project's: `AGENTS.md`, `README.md`,
`.pre-commit-config.yaml`, the agent settings, `scripts/log_smoke_run.py`,
and the files the connected components' templates add. `.gitignore` gets the lines it lacks;
`pyproject.toml` gets the keys its tables lack and keeps the ones the project
set. A file that exists is listed as `exists` and left alone.

Who writes what. The template writes what no component writes; a line a
component adds by its own connecting section (its `AGENTS.md` line, its
`.gitignore` line, its config file) is the component's, and the template
does not carry it. Three files are shared:

| file | written by | then |
|---|---|---|
| `pyproject.toml` | lightning-hydra `scaffold.py` | `uv add` (framework.md 2.3), then `render.py` adds tool settings |
| `.gitignore` | lightning-hydra `scaffold.py` | components add their lines, `render.py` adds the rest |
| `AGENTS.md` | `render.py` | each component adds its line under the components heading, research-log its section |
| `docs/conventions-local.md` | research-log `init.py` | its procedure fills stack and layout; `render.py fragment conventions-local` gives the rest |

Fragments, printed for the agent to place (`render.py fragment <name>`):
`conventions-local`, `protocols/access`, `setup-task`, `brief`, `handoff`,
and those the adapters name. Templates exist for `lang = "en"` and
`lang = "ru"`: the prose is translated, everything a script reads is the
same.

A component adds to a shared file through its parts,
`templates/<lang>/parts/<slot>/<component>.*`, which `render.py` puts where
the file has `{{parts <slot>}}` (components/README.md).

## Brief

The brief is research-log's (`references/initialisation.md`, "The brief"):
the person's assignment, in their words, or composed with them by that
procedure. It goes to `docs/brief.md` (framework.md, step 1).

A request that already carries the question (what to find out, the data,
the measure of success) is the brief they brought: it is written down
without an interview and without showing it first. Their sentences go into
the template's sections, tightened at most; nothing is added. Facts about
the setup itself (the directory, the repository's name and host, the
components) are not the assignment: they go to `ml-scaffold.toml` or the
setup task, not to the brief. The brief keeps everything the request said
about the work: the data to add, the tools to publish, where the project
comes from. A brief the agent composed or drafted any
section of is shown before it is written, as research-log says.

ml-scaffold needs a few more facts from it, listed in
`render.py fragment brief` (the project's name, the datasets, the compute);
for whichever the brief does not carry, take the default below and name it
in the step 6 report; do not ask, except for the name (below). Ask only what the brief cannot be acted
on without, inside research-log's one round of questions.

| fact | default when the brief is silent |
|---|---|
| project and package name | a name the person gave for the project or its repository ("the repository will be called X"), if it fits (`[a-z][a-z0-9-]*`; the package with `_`); else the directory's name, if it fits; else a short name from the brief's title. Never a directory's prefix or suffix kept on a guess. A name the person gave is taken without asking; otherwise the proposed name is asked, the setup's first stop (framework.md 0.2) |
| datasets | none: no import, a spike "which data" among the first tasks. With a data source, its adapter says what a named dataset becomes (step 4, or a first task) |
| compute, sizes of resources | the adapters' defaults (`render.py fragment brief` names them) |
| Python | the skeleton's default (lightning-hydra) |
| components | all of `templates/ml-scaffold.toml` |

Never ask the person for an infrastructure value or for anything a component can
check.

## First tasks

At step 6, from the brief and `docs/vision.md`, on the project's board
(task-tracker). The agent that takes the project over works from them
without the person, so each task:

1. Comes from something the brief says. Nothing invented to fill the board;
   what the brief leaves open becomes a spike with the question as its
   title, or a question to the person now.
2. Can be done by an agent: it names the data (`data/<path>.dvc` or the
   registry dataset), the entry point or the module to write, and what is
   observable at the end (a test, a technote, an experiment in the log).
3. Leaves to the person only what is theirs: a threshold or a split chosen
   before the numbers exist is a research-log decision, taken with the
   person now (research-log, "Decisions"), not a task for the executor.
   A task that waits on a person says so (`status: blocked`,
   `blocked_by: "<who and what>"`): a licence, a choice among variants, a
   merge someone else does.
4. Has `depends_on` where order matters and a priority.
5. Names nothing outside the repository by a local path (`~/…`, another
   project's checkout): a repository URL, a registry dataset, a document
   link, or the person to ask. The agent that takes it over may run on
   another machine.

Typical first tasks of such a project, when the brief supports them:
the datasets the brief names, as the data source's adapter says; the
project's DataModule in place
of the skeleton's stub; a baseline run recorded as an
experiment; spikes for the brief's open questions. A spec only when the
brief describes several tasks of engineering work; the question itself is
in `vision.md`, not in a spec.

## Handoff

The handoff is the setup task's last Notes entry, from `render.py fragment
handoff`, filled in: what works, what waits on whom, where to start, the
component gaps the project works around. It is committed with the closed
setup task. `docs/tasks/_handoffs/` is for per-session resume state and is
not committed, so it is not the handoff.

## Credentials

The agent never reads, prints or passes a secret. It gives the person one
list (the access protocol), and checks with the components' own commands, which print
names, modes and the server's answer but never a value. To a transport's
remote side the credentials travel only through the transport's own
script, which reads the files itself and prints keys and outcomes, never
values (its adapter, "Step 3").

The list is built from the adapters' access rows, so that a later
connector (a password manager or vault that writes the files) can replace
the person's editor without changing anything else. What has to stay fixed
for that: each credential is a file and an INI section with named keys in
the person's home (the rows); each has a check that reads only names and
modes (the last column); a remote copy is made from the local file by the
transport. A connector fills the file; the checks and the remote step stay
as they are.

## Checking this skill

```bash
uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run pytest -q
```

The end-to-end check is setting a new project up.
