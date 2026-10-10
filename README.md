# ml-scaffold

A skill for Claude Code and other agents: set up a new ML research project
from a brief, up to a green smoke run recorded on the project's own board.
The project is built from component skills, each connected by its own
instructions:

| component | gives the project |
|---|---|
| [research-log](https://github.com/norsage/research-log) | the research record: hypotheses, experiments, findings, protocols, decisions |
| [task-tracker](https://github.com/norsage/task-tracker) | the task board and specs |
| [mlflow-tracking](https://github.com/norsage/mlflow-tracking) | runs in MLflow, a local SQLite store by default |
| [lightning-hydra](https://github.com/norsage/lightning-hydra) | the training skeleton on Lightning + Hydra |

The person gives the brief and answers one message; the agent does the rest
by [`framework.md`](framework.md): installs and pins the components,
renders the repository files, connects the components in order, puts an
access protocol into the project, and runs the smoke run (a run logged to
MLflow, then one batch through `train.py trainer=debug`).

Infrastructure of your own (a remote cluster, a data registry, an MLflow
server) is added as components: an adapter in [`components/`](components/),
its values in [`infra.toml`](infra.toml), its source in
[`skills.toml`](skills.toml), its templates in `templates/<lang>/`. Steps
that need a transport (resources, a remote smoke run) come from the
transport's adapter; without one, the smoke run is local.

## Install

```sh
git clone https://github.com/norsage/ml-scaffold.git
bash ml-scaffold/install.sh            # into ~/.agents/skills/, linked from ~/.claude/skills/
bash ml-scaffold/install.sh --symlink  # link the clone, for developing the skill
```

It is installed once per machine: it sets projects up and is not needed in
them afterwards. A project gets the rendered files and the skill's
revision in `skills.lock`. The components, which the agent uses every day,
are installed into each project by `scripts/install_components.py`.

Then ask the agent, in an empty directory: "/ml-scaffold set up a project
from this brief: …". Name the skill: when an agent has many skills, Claude
Code drops the descriptions of the least used ones from its list, and a
skill used once per project is among them; without its description the
request goes to another skill (research-log, for one).

## What is inside

| file | what |
|---|---|
| [`SKILL.md`](SKILL.md) | the agent's entry point |
| [`framework.md`](framework.md) | the setup order, ties between components, resuming |
| [`components/`](components/) | adapters of the components; a new component is a new adapter |
| [`infra.toml`](infra.toml) | addresses and settings of the infrastructure |
| [`skills.toml`](skills.toml) | where the components are installed from |
| [`templates/`](templates/) | the project's values and file templates, `en` and `ru` |
| [`scripts/`](scripts/) | `render.py`, `install_components.py` |

## Checking

```sh
uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run pytest -q
```
