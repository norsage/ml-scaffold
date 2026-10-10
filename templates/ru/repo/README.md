# {{project.title}}

{{project.description}}

{{#if research-log}}
Цель и границы проекта описаны в [`docs/vision.md`](docs/vision.md),
исходное задание — в [`docs/brief.md`](docs/brief.md).
{{/if}}

## Структура репозитория

| Каталог | Что там |
|---|---|
{{#if lightning-hydra}}
| `src/{{project.pkg}}/` | код: данные, модель, утилиты ([`src/README.md`](src/README.md)) |
| `scripts/train.py` | единственная точка входа обучения |
| `configs/` | конфиги Hydra ([`configs/README.md`](configs/README.md)) |
{{/if}}
{{#if !lightning-hydra}}
| `src/{{project.pkg}}/` | код проекта |
{{/if}}
| `scripts/` | точки входа{{#if transport}}, в том числе задачи на HPC{{/if}} |
| `tests/` | тесты |
| `docs/` | журнал исследования и задачи |
{{parts readme-layout}}

Правила работы с кодом описаны в
[`docs/conventions-local.md`](docs/conventions-local.md).

## Быстрый старт

Нужен [uv](https://docs.astral.sh/uv/); Python ставит он сам.

```bash
uv sync
uv run pytest
```

После клонирования один раз установите хуки git: pre-commit запускает
линтеры и тесты перед каждым коммитом.

```bash
uv run pre-commit install
{{#if research-log}}
python3 .agents/skills/research-log/scripts/rebase_runs.py --install-hooks
{{/if}}
```

Версии остальных инструментов перечислены в
[`docs/conventions-local.md`](docs/conventions-local.md#внешние-инструменты).

## Присоединиться к проекту

Нужен доступ к репозиторию проекта.
{{parts readme-join}}

{{#if parts.readme-admin}}
Сначала попросите администратора, одним сообщением:
{{parts readme-admin}}

Логин и ключи одни на все проекты: если они уже есть, этот запрос не нужен.

{{/if}}
{{#if mlflow-tracking}}
{{#if infra.mlflow_login}}
Затем попросите автора проекта открыть вашему логину запись в эксперимент
MLflow проекта. Автор говорит своему агенту: «дай пользователю `<логин>`
доступ к проекту».

{{/if}}
{{/if}}
1. Клонируйте проект, затем `uv sync` и хуки из «Быстрого старта».
2. Запустите агента в каталоге проекта и попросите: «настрой мне
   доступы».
{{#if access_rows}}
   Он покажет, куда вписать логин, пароль и ключи, и проверит их на
   ноутбуке{{#if transport}} и на HPC{{/if}}.
{{/if}}
   Порядок действий описан в протоколе настройки доступов
   ([`docs/protocols/`](docs/protocols/), `access-setup`); без агента его
   можно пройти вручную.
{{#if mlflow-tracking}}
{{#if infra.mlflow_login}}

По желанию пароль MLflow, присланный администратором, можно сменить на
свой. Команда спрашивает логин, старый и новый пароль; в новом не должно
быть `"` и `\`. Смените пароль до шага 2{{#if transport}}, иначе на HPC останется старый{{/if}}.

```bash
printf 'Логин: '; read -r U; printf 'Старый пароль: '; read -rs OLD; echo; printf 'Новый пароль: '; read -rs NEW; echo; curl -fsS -u "$U:$OLD" -X PATCH "{{infra.mlflow_uri}}api/2.0/mlflow/users/update-password" -H 'Content-Type: application/json' -d "{\"username\":\"$U\",\"password\":\"$NEW\"}" && echo ok; unset OLD NEW
```
{{/if}}
{{/if}}

{{#if research-log}}
## Журнал исследования

Журнал лежит в `docs/` и ведётся по соглашениям скилла research-log
(`.agents/skills/research-log/`). Каждая запись имеет постоянный
идентификатор:

| Каталог | Что там |
|---|---|
| `hypotheses/` | утверждения до проверки и что их опровергло бы |
| `experiments/` | прогоны обучения и оценки, с коммитом и версиями инструментов |
| `technotes/` | проверки инструментов: скорость, сверка |
| `findings/` | утверждения, подтверждённые прогонами |
| `protocols/` | повторяемые процедуры |
| `decisions/` | зафиксированные решения и их обоснование |

Результаты и метрики хранятся в записях журнала, в README их нет.
Правила записи описаны в [`docs/conventions.md`](docs/conventions.md).
{{#if task-tracker}}
Текущие задачи лежат в [`docs/tasks/`](docs/tasks/).
{{/if}}

Записи ссылаются на SHA коммитов, поэтому ветки не сливаются через squash.
Если ветку переписали кнопкой Rebase в merge request, порядок действий
описан в
[`git-hosting.md`](.agents/skills/research-log/references/git-hosting.md).

{{/if}}
{{parts readme-sections}}
## Доступы

{{#if access_rows}}
В репозитории лежат только адреса и имена профилей, в конфигах
компонентов в корне. Логины, пароли и ключи каждый заводит сам, в своём
домашнем каталоге, с правами 600. В репозиторий, переменные окружения и
аргументы команд они не попадают.

| Доступ | Файл и секция | Ключи | Где взять | Где нужен | Проверка |
|---|---|---|---|---|---|
{{access_rows}}

Порядок действий на ноутбуке{{#if transport}} и на HPC{{/if}} — протокол настройки доступов в
[`docs/protocols/`](docs/protocols/) (`access-setup`).
{{/if}}
{{#if !access_rows}}
Логинов и ключей проект не требует: прогоны и их история хранятся в
проекте. Если они появятся, их заводят в домашнем каталоге, с правами 600,
а не в репозитории; порядок — протокол настройки доступов в
[`docs/protocols/`](docs/protocols/) (`access-setup`).
{{/if}}

## Работа с агентами

Инструкции для агентов лежат в [`AGENTS.md`](AGENTS.md), скиллы — в
`.agents/skills/`. Скиллы правятся в своих исходных репозиториях, а не здесь.
