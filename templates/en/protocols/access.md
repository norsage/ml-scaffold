<!-- Body of the access setup protocol. Create the record and put this body
     in place of research-log's template sections, without this comment:
       python3 .agents/skills/research-log/scripts/new.py protocol "Access setup" --slug access-setup
     Every member follows it, the project's creator included (framework.md
     of ml-scaffold, step 3). -->

## What it produces, and who runs it

Everything a person needs to work in the project: credentials on the laptop{{#if transport}} and on the remote side{{/if}},
requests to the administrator, a check that everything works. Every
member follows it: the creator at setup, the others after cloning.
Credentials are personal and shared by all projects, so most of this is
done once per person; only the rights in the project depend on it.
The member's agent runs it. It asks the person once, at step 4, and
waits for the answer; what was set up before it finds by the checks and
does not ask about.

## Before you start

- A clone of the project with `uv sync` in it; the agent started in the
  project directory.
- The agent settings in the repository: `.claude/settings.json` (Claude
  Code) and `opencode.json` (OpenCode) forbid it to read the credential
  files. Codex has no such project-level ban; there `AGENTS.md`'s rule
  applies.
- Access to the project's repository: given before the clone.

## Steps

1. **The ban on reading credentials is in effect.** The agent makes a
   probe file and reads it with its own file tool (Read in Claude Code,
   read in OpenCode):

   ```bash
   mkdir -p ~/.config/ml-scaffold && echo probe > ~/.config/ml-scaffold/deny-probe
   ```

   The file is in the deny list with the credential files. Read refused:
   the settings are in effect. Read: the agent runs outside the project
   directory, or the settings are loaded only at start. If the agent can
   move its session into the project directory itself (`change_directory`
   in the Claude app), it does so and reads the probe again on its next
   turn. Otherwise, or if the probe is still read, the person restarts the
   agent in the project directory, and the protocol starts over.
2. **What already works:**

   ```bash
{{parts access-checks}}
   ```

   A failure is not an error: the access row of step 3's table goes into
   step 4's message.
{{parts access-checks-note}}
3. **What is missing:** the rows of the "Access" table below whose check
   failed at step 2.
{{parts access-missing-note}}
4. **One message to the person, then wait.** In it: step 3's rows with
   the blocks below for them, and the administrator's items those rows
   wait on.
{{#if !transport}}
   Everything works already: no message.
{{/if}}
{{parts access-message}}
{{parts access-files}}
{{#if access_rows}}

   An ssh key is best kept with a passphrase in ssh-agent (on macOS
   `ssh-add --apple-use-keychain ~/.ssh/<key>`): the key file without the
   passphrase is useless, even if read.
{{/if}}
{{#if parts.access-admin}}

   Only the administrator:
{{parts access-admin}}
{{/if}}
{{#if mlflow-tracking}}
{{#if infra.mlflow_login}}

   The project's author (or someone else with `MANAGE` on the
   experiment): write access to the project's MLflow experiment for the
   person's login. The author's agent runs mlflow-tracking's `access.py
   grant <login>`. The person may change the administrator's password for
   their own{{#if transport}} before step 6{{/if}}: the command is in the README, "Joining
   the project".
{{/if}}
{{/if}}
{{parts access-message-end}}
5. **Check on the laptop**, once the person has answered: step 2's
   commands. A failure: one message with the lines that are not `ok`,
   their fix and the table's row, and wait again.
{{parts access-steps}}

### Access

{{#if access_rows}}
Each person sets these up, in their own home directory, mode 600; the
agent needs no values.

| Access | File, section | Keys | Where to get | Where needed | Check |
|---|---|---|---|---|---|
{{access_rows}}
{{/if}}
{{#if !access_rows}}
The project's components need no logins or keys: steps 3–5 are empty.
{{/if}}

## Traps

- A credentials file renamed or copied (`credentials.bak`) is not covered
  by the ban: the ban lists exact paths. Do not rename such files; move
  them out of the home directory.
- The agent started outside the project directory: the project's settings
  do not apply, step 1's probe is read.
{{parts access-breaks}}

## How you know it worked

- Step 1's probe is refused.
- Step 2's commands print no line that is not `ok`.
{{parts access-done}}
