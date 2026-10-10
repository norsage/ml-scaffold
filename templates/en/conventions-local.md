<!-- Sections of conventions-local.md from ml-scaffold. Each section below
     goes into the section of the same name in the file research-log
     created (init.py): appended to what is there, without this comment and
     without a mention of ml-scaffold. The rest about the stack and the code
     layout comes from research-log's procedure (presets python-uv,
     python-qa) and the skeleton; the preset's sentence about the version
     in `requires-python` is replaced by the paragraph below. -->

## Stack and environment

The Python version is pinned in `.python-version` (the one in the file), not
in `requires-python`: `uv.lock` pins packages, not the interpreter. Without
`.python-version` uv takes any installed Python in the `requires-python`
range, and where there is none (a remote task) downloads the newest one, so
the laptop and the task run different versions. Changing the version: edit
`.python-version` and `requires-python`, `uv lock`, commit; on a remote side
that is a new environment.
{{#if lightning-hydra}}
Which versions the skeleton supports and why: the "Environment" section of
the lightning-hydra skill.
{{/if}}

## External tools

| Tool | Version | How it is installed | Notes |
|---|---|---|---|
{{parts conventions-tools}}
{{#if mlflow-tracking}}
| MLflow {{#if infra.mlflow_login}}server{{/if}}{{#if !infra.mlflow_login}}store{{/if}} | `mlflow.toml` | — | runs, metrics, artifacts; the client is `mlflow-skinny` from `uv.lock` |
{{/if}}

{{parts conventions-sections}}
## Access

Logins, passwords and keys live only in the home directory of whoever runs,
mode 600: on the laptop{{#if transport}} and on the remote side{{/if}}. They never go into the repository,
the project's configs, the tasks' environment variables (`--env`) or command
arguments. The project's configs hold only addresses and profile names. The
table of access is in the access setup protocol and in the "Access" section
of [`README.md`](../README.md).

1. The agent does not touch secrets: it does not open or print the files
   that hold them and does not pass values in commands. It learns the state
   of access from the components' checks; when something is missing, it
   shows the person the path and the section with placeholders, and the
   person fills it in.
{{#if mlflow-tracking}}
{{#if infra.mlflow_login}}
1. MLflow: a personal login for every member, with a password for MLflow
   only: the server knows who ran what, and access is revoked for one
   person. A service account only for automation without a person (CI).
{{/if}}
{{/if}}
{{parts conventions-access}}

How to set up and check access{{#if transport}}, on the laptop and on the remote side{{/if}}: the access
setup protocol in [`protocols/`](protocols/) (`access-setup`); every member
follows it.
{{parts conventions-access-end}}

## Commit messages

Conventional Commits. The subject is `type(scope): what was done`: in
English, imperative, lowercase first letter, no full stop, at most 72
characters. The `commit-msg` hook of pre-commit checks the subject.

| Type | When |
|---|---|
| `feat` | a new capability |
| `fix` | a fix |
| `perf` | faster, same behaviour |
| `refactor` | reworked, same behaviour |
| `test` | tests only |
| `docs` | tasks, spikes, decisions, experiments, conventions with no code change |
| `build` | dependencies, build, `pyproject.toml` |
| `chore` | the rest: tools, pre-commit, cleanup |

The scope is optional. A commit with code and documents takes its type from
the code.
{{#if task-tracker}}
Tasks the commit closes or files go in parentheses at the end of the
subject, with their suffix: `feat(data): add loader (0006.jyn)`.
{{/if}}

## Anything else this project decided

The agent's skills ({{components}}) live in the project, in
`.agents/skills/`. Codex, OpenCode, Cursor, Copilot and Gemini CLI read
them there; for Claude Code, `.claude/skills/` has relative symlinks to the
same directories. The skills' versions are in `skills.lock`. The copied
skills are not edited: a change goes to the skill's source, then the skill
is reinstalled from the project root and committed:

```bash
bash <skill source>/install.sh --project
```

{{#if research-log}}
After an update of research-log, run its `upgrade.py`.
{{/if}}
{{#if task-tracker}}

research-log keeps the log in `docs/{hypotheses,experiments,technotes,findings,protocols,decisions}/`,
task-tracker the tasks in `docs/tasks/` and the specs in `docs/specs/`. They
are linked in one place: an experiment's `motivated_by` holds a task id.
{{/if}}
