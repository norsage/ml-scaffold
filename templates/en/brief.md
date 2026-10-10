<!-- What ml-scaffold takes from the brief beyond what research-log asks
     (references/initialisation.md, "The brief"). The brief follows
     research-log's template; these items go into its "Data" and
     "Constraints", and the project's name into its `project:` block. What
     the brief does not say is not asked: take the item's default and name
     it in step 6's report. For the agent, not the person: these headings
     are not shown to them. The brief lives in docs/brief.md. Facts about
     the setup itself (the directory, the repository's name and host) do
     not go into the brief: they belong in ml-scaffold.toml and the setup
     task. -->

- **Project and package name.** Short, in Latin letters: it becomes the
  name of the MLflow experiment and of what the components name after the
  project (their adapters say what). The name the person gave the project
  or the repository, if it fits (lowercase Latin letters, digits, a dash;
  in the package the dash becomes `_`); else the directory's name, if it
  fits; else a short name from the brief's title. A prefix or suffix of the
  directory is not kept on a guess. A name the person gave is taken
  without asking; otherwise the proposed one is asked at framework.md
  step 0.2, the setup's first stop, with what it names.
{{parts brief}}
{{#if lightning-hydra}}
- **Python version.** If the brief or the developer names one, write it
  to `python` in `ml-scaffold.toml`; if not, the skeleton's default. A
  version the skeleton does not run on is refused by `scaffold.py` with the
  reason (3.14, say: Hydra 1.3 fails on it): give the reason and the
  supported versions to the developer and let them choose, never
  substitute another silently.
{{/if}}
- **Who else is in the project.** Other members set up their access
  themselves, by the project's access setup protocol; their number matters
  only for quotas.
