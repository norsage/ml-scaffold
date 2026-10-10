# {{project.title}}

{{project.description}}

{{#if research-log}}
The project's aim and limits are in [`docs/vision.md`](docs/vision.md), the
original assignment in [`docs/brief.md`](docs/brief.md).
{{/if}}

## Repository layout

| Directory | What is there |
|---|---|
{{#if lightning-hydra}}
| `src/{{project.pkg}}/` | code: data, model, utilities ([`src/README.md`](src/README.md)) |
| `scripts/train.py` | the one entry point of training |
| `configs/` | Hydra configs ([`configs/README.md`](configs/README.md)) |
{{/if}}
{{#if !lightning-hydra}}
| `src/{{project.pkg}}/` | the project's code |
{{/if}}
| `scripts/` | entry points{{#if transport}}, remote tasks among them{{/if}} |
| `tests/` | tests |
| `docs/` | the research log and the tasks |
{{parts readme-layout}}

How code is written here: [`docs/conventions-local.md`](docs/conventions-local.md).

## Quick start

You need [uv](https://docs.astral.sh/uv/); it installs Python itself.

```bash
uv sync
uv run pytest
```

After cloning, install the git hooks once: pre-commit runs the linters and
tests before every commit.

```bash
uv run pre-commit install
{{#if research-log}}
python3 .agents/skills/research-log/scripts/rebase_runs.py --install-hooks
{{/if}}
```

Versions of the other tools are in
[`docs/conventions-local.md`](docs/conventions-local.md#external-tools).

## Joining the project

You need access to the project's repository.
{{parts readme-join}}

{{#if parts.readme-admin}}
First ask the administrator, in one message, for:
{{parts readme-admin}}

The login and keys serve every project: if you have them already, skip
this request.

{{/if}}
{{#if mlflow-tracking}}
{{#if infra.mlflow_login}}
Then ask the project's author to give your login write access to the
project's MLflow experiment. The author tells their agent: "give user
`<login>` access to the project".

{{/if}}
{{/if}}
1. Clone the project, then `uv sync` and the hooks from "Quick start".
2. Start the agent in the project directory and ask it: "set up my
   access".
{{#if access_rows}}
   It shows where to put the login, password and keys, and checks them
   on the laptop{{#if transport}} and on the remote side{{/if}}.
{{/if}}
   The steps are the access setup protocol
   ([`docs/protocols/`](docs/protocols/), `access-setup`); it can be
   followed by hand, without the agent.
{{#if mlflow-tracking}}
{{#if infra.mlflow_login}}

If you like, change the MLflow password the administrator sent for your
own. The command asks for the login, the old and the new password; the
new one may not contain `"` or `\`. Change it before step 2{{#if transport}}, or the old one stays on the remote side{{/if}}.

```bash
printf 'Login: '; read -r U; printf 'Old password: '; read -rs OLD; echo; printf 'New password: '; read -rs NEW; echo; curl -fsS -u "$U:$OLD" -X PATCH "{{infra.mlflow_uri}}api/2.0/mlflow/users/update-password" -H 'Content-Type: application/json' -d "{\"username\":\"$U\",\"password\":\"$NEW\"}" && echo ok; unset OLD NEW
```
{{/if}}
{{/if}}

{{#if research-log}}
## Research log

The log lives in `docs/` and follows the conventions of the research-log
skill (`.agents/skills/research-log/`). Every record has a permanent
identifier:

| Directory | What is there |
|---|---|
| `hypotheses/` | claims before they are tested, and what would refute them |
| `experiments/` | training and evaluation runs, with the commit and tool versions |
| `technotes/` | checks of tools: speed, agreement |
| `findings/` | claims the runs have borne out |
| `protocols/` | repeatable procedures |
| `decisions/` | choices made, and why |

Results and metrics are in the log's records, not in the README. How
records are written: [`docs/conventions.md`](docs/conventions.md).
{{#if task-tracker}}
Current tasks are in [`docs/tasks/`](docs/tasks/).
{{/if}}

Records cite commit SHAs, so branches are not merged by squash. If a
branch was rewritten by the Rebase button of a merge request, the steps
are in
[`git-hosting.md`](.agents/skills/research-log/references/git-hosting.md).

{{/if}}
{{parts readme-sections}}
## Access

{{#if access_rows}}
The repository holds only addresses and profile names, in the components'
configs at its root. Logins, passwords and keys each person keeps in their
own home directory, mode 600. They never go into the repository,
environment variables or command arguments.

| Access | File, section | Keys | Where to get | Where needed | Check |
|---|---|---|---|---|---|
{{access_rows}}

The steps on the laptop{{#if transport}} and on the remote side{{/if}}: the access setup protocol in
[`docs/protocols/`](docs/protocols/) (`access-setup`).
{{/if}}
{{#if !access_rows}}
The project needs no logins or keys: runs and their history are kept in
the project. If some appear, they go into the home directory, mode 600,
not into the repository; the steps are the access setup protocol in
[`docs/protocols/`](docs/protocols/) (`access-setup`).
{{/if}}

## Working with agents

Instructions for agents are in [`AGENTS.md`](AGENTS.md), the skills in
`.agents/skills/`. The skills are edited in their own repositories, not
here.
