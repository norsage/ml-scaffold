<!-- Body of the project's setup task on the project's board (framework.md
     of ml-scaffold, step 1). Replaces the sections of task-tracker's
     template, without this comment. -->

## Context

The project was set up by the ml-scaffold skill from the brief
(`docs/brief.md`): components {{components}}. The order of steps and the
check of each: the skill's `framework.md`; here, what is done, what waits
on a person and what went otherwise. The project's values:
`ml-scaffold.toml`; the skills' versions: `skills.lock`.

## Steps

- [ ] 2. Skeleton, components connected, repository files; pre-commit green
- [ ] 3. Access setup protocol: checks clean{{#if transport}}, credentials on the remote side in one task{{/if}}
{{parts setup-steps}}
{{#if !transport}}
- [ ] 5. Local smoke run: {{#if mlflow-tracking}}tracking without training, {{/if}}training with trainer=debug; a Notes entry: the commit, {{#if mlflow-tracking}}the MLflow run, {{/if}}what went wrong
{{/if}}
- [ ] 6. First tasks from the brief; handoff (the last Notes entry)

## Notes

<!-- One entry per stop: date, step, what waits on whom, how it ended.
     The first entries: the name's question of step 0.2 if it was asked, the date of step 1's message (questions{{#if transport}}, remote tasks{{/if}}) or "not needed", and
     the date of the access protocol's message (step 3) or "not needed". Separately: where a person was needed beyond the brief, that
     message and the administrator's actions, and where framework.md did
     not work as written: these are remarks for ml-scaffold. -->
