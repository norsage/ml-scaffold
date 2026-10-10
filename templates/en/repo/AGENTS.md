# {{project.title}}

## Components

<!-- Each component adds its line here when it is connected (framework.md
     of ml-scaffold, step 2); research-log's section goes above this
     one. -->

## Access

Do not open credentials and do not pass them in commands, arguments or
`--env`. The files that hold them (`~/.ssh/id_*`, `~/.aws/credentials`,
`~/.mlflow/credentials`, `.env`) are closed to reading by the agent
settings in `.claude/settings.json` and `opencode.json`; do not lift the
ban and do not read around it.

A new member, or a request to set up access: the access setup protocol in
[`docs/protocols/`](docs/protocols/) (`access-setup`), step by step. The
same when a component's check shows that access is missing. Rules: the
"Access" section of [`docs/conventions-local.md`](docs/conventions-local.md#access).

{{parts agents}}
## A new clone

Git hooks do not travel with the repository. Once in every new clone:

```bash
uv sync
uv run pre-commit install
```

{{#if research-log}}
research-log's hooks are installed as its section above says.
{{/if}}

The skills live in `.agents/skills/` (for Claude Code, links from
`.claude/skills/`) and are edited only in their sources, see
[`docs/conventions-local.md`](docs/conventions-local.md#anything-else-this-project-decided).
