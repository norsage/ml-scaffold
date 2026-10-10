<!-- The last Notes entry of the setup task (framework.md of ml-scaffold,
     step 6). Fill in the angle brackets, without this comment. -->

### Handoff, <date>

What works:

- `uv sync`, `uv run pytest`, pre-commit over the whole tree{{#if lightning-hydra}}; `python scripts/train.py trainer=debug` locally{{/if}}.
{{parts handoff-works}}

What waits on whom:

- <item: who, what, where it is written; "nothing" if so>
- First push: remote <`origin` = <url>, added <date> | not added>; pushed by the person, or by the agent on their separate word; after the push, the first CI pipeline, if there is one.

Where to start: `AGENTS.md`, then `docs/vision.md`, then
`python3 .agents/skills/task-tracker/scripts/next.py --all`. First tasks:
<ids and titles>.

Component gaps the project works around: <items or "none">.
