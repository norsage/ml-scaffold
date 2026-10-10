# {{project.title}}

## Компоненты

<!-- Каждый компонент при подключении дописывает сюда свою строку
     (framework.md ml-scaffold, шаг 2); раздел журнала research-log
     встаёт выше этого раздела. -->

## Доступы

Креды не открывай и не передавай в командах, аргументах и `--env`.
Файлы с ними (`~/.ssh/id_*`, `~/.aws/credentials`, `~/.mlflow/credentials`,
`.env`) закрыты для чтения настройками агентов в `.claude/settings.json` и
`opencode.json`; запрет не снимай и в обход него не читай.

Новый участник или просьба настроить доступы — протокол настройки
доступов в [`docs/protocols/`](docs/protocols/) (`access-setup`), по шагам.
Он же — когда проверка компонента показывает, что доступа нет. Правила —
раздел «Доступы» [`docs/conventions-local.md`](docs/conventions-local.md#доступы).

{{parts agents}}
## Новый клон

Хуки git через репозиторий не передаются. В каждом новом клоне один раз:

```bash
uv sync
uv run pre-commit install
```

{{#if research-log}}
Хуки research-log ставятся по его разделу выше.
{{/if}}

Скиллы лежат в `.agents/skills/` (для Claude Code — ссылки из
`.claude/skills/`) и правятся только в своих исходниках, см.
[`docs/conventions-local.md`](docs/conventions-local.md#прочие-договорённости-проекта).
