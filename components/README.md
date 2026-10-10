# Component adapters

One file per component skill. An adapter answers five questions about its
component and points to the component's own sections for the answers; it
does not retell them. A component is connected by its own instructions;
`framework.md` says in which order and what ties components together.

A new component is connected by a new adapter in this directory; nothing
else in ml-scaffold changes. What it adds to a file the templates share
(README, `AGENTS.md`, the access protocol) are its parts:
`templates/<lang>/parts/<slot>/<component>.*`, one file per slot, put
where the template has `{{parts <slot>}}` (`render.py`). The slots are
the `{{parts …}}` lines of `templates/<lang>/`.

## Sections

1. **Purpose.** What the component gives the project, when it is needed.
2. **From people.** Credentials: file, section, where to get them, how to
   check them without seeing the values. Administrator actions. "None" is an
   answer.
3. **Roles.** Which roles the component requires and which it fills (the
   list below); where its tie to another component is already written
   (recipe, integration, extension). The path of a component's recipe for
   another is named only here, in adapters: recipes move between
   components, and then only adapters change.
4. **Connecting.** The component's section to follow, and what stays in the
   repository afterwards: config file, `AGENTS.md` line,
   `conventions-local.md` section, hooks, row of the access table,
   `.gitignore` lines.
5. **Checking.** Locally, and in the end-to-end smoke run.
6. **Setup steps**, when the component adds to a step of `framework.md`:
   one subsection per step it touches (`### Step 2`, …), then `### Ties`
   (its ties with other components and resources), `### Values` (the
   values of its own config files, written with `{{…}}` as in
   `framework.md`) and `### Known gaps`. `framework.md` reads the
   connected adapters at every step, in the order of `components`. The
   transport's adapter carries steps 4 and 5 whole ("Step 1" too: the
   paragraph of step 1's message about who runs its tasks); without a
   transport, `framework.md` runs the smoke run locally.

A gap is something the component should say and does not. The adapter
describes the manual step and marks it `Gap:`; the gap goes to the
component's own board. What only matters when a component is connected
by ml-scaffold is not a gap: the adapter defines it (task-tracker has no
connecting section, and needs none).

## Roles

| role | what it is | filled by |
|---|---|---|
| log | where results, protocols and decisions are recorded | research-log |
| board | where tasks and specs live | task-tracker |
| transport | runs a committed tree remotely, brings results back | an infrastructure component; none: runs are local |
| run tracker | records runs, metrics, checkpoints; finds them back | mlflow-tracking |
| data source | pins dataset versions, delivers them to tasks | an infrastructure component; none: data as the project keeps it |
| skeleton | training code layout with docking points | lightning-hydra |

## Infrastructure values

Addresses and images shared by every project on the infrastructure are not
written in adapters. They are keys of [`infra.toml`](../infra.toml), named here as
`infra:<key>`. A value made from the project's (a mount path, a remote)
is a key of its `[derived]` table, named `{{<key>}}`.

## Access table

The README of the project has one table of access, one row per credential,
in the format mlflow-tracking uses (its "Secrets" section):

| access | file, section | keys | where | check |
|---|---|---|---|---|

The component's own docs give its rows in this format; the adapter carries
them, with a "where to get it" column, in a table per language of
`templates/<lang>/`: for `en`, headed
`| access | file, section | keys | where to get | where needed | check |`,
for `ru`, `| доступ | файл и секция | ключи | где взять | где нужен | проверка |`.
`render.py` copies the rows of the project's language into README and into
the access protocol, with `<infra:key>` replaced; block lines
(`{{#if infra.<key>}}`, `{{#if transport}}`) inside a table keep or drop
rows. A component whose docs have no rows yet: the adapter writes them and
marks it `Gap:`.
