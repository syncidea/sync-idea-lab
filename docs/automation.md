# Автоматизация

## Что работает без ключей

FixtureProvider реализует интерфейс `Provider.generate(topic) -> dict`.
`generate.py` принимает только структурированные данные фиксированной схемы, сам задаёт
пути и POM, валидирует в disposable tree. Prompt в `tools/challenge_generator/prompt.md`.
Dry-run детерминирован, не меняет файлы, не вызывает API и не исполняет ответ провайдера.
Локальная подготовка не открывает PR и ничего не публикует.

`editorial-ci.yml`: push main или проверенный редакторский PR → каталог, Python-тесты,
компиляция starter + JUnit; поведенческие тесты не запускаются.
`submission-ci.yml`: pull_request → trusted-base policy → разрешённые Java → JUnit одной задачи.
`prepare-challenge.yml`: доверенный default branch → fixture draft → editorial → артефакт на 7 дней.

Второй job создания draft PR имеет `contents: write`, `pull-requests: write`, не исполняет Java
и не принимает артефакты из пользовательских PR. Он заново воспроизводит тот же фиксированный
fixture из доверенного коммита. Write token передаётся только шагу push/PR и не сохраняется в Git config.
LLM secrets сейчас отсутствуют во всех jobs. Нет auto-merge, Telegram API и платных запросов.

## Включение после согласия владельца

Ручной workflow_dispatch по умолчанию создаёт только артефакт. Input `create_draft_pr: true`
разрешает отдельный draft-pr job. Требуется включить Settings → Actions → General → Workflow
permissions → **Allow GitHub Actions to create and approve pull requests**; использование для
одобрения PR кодом не реализовано. Если политика аккаунта запрещает эту настройку, оставьте
artifact-only и подготовьте PR вручную. Скрипт откажется перезаписывать существующую ветку/PR.
Повтор после сбоя между push и PR требует ручной проверки ветки, force-push отсутствует.

Расписание уже описано, но job закрыт repository variable `ENABLE_WEEKLY_PREPARATION=true`.
До согласия переменная отсутствует: расписание ничего не готовит. Для создания draft PR по
расписанию дополнительно требуется `ENABLE_DRAFT_PR=true`. Вторник `17 13 * * 2` — 16:17 МСК.
Время выбрано вне начала часа; cron может задерживаться/пропускаться и работает с default branch.
Публикация в среду 19:00 МСК (= 16:00 UTC) только ручным merge; расписание её не выполняет.
[Поведение расписаний GitHub](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).

PR от GITHUB_TOKEN обычно не запускает новые workflows из-за защиты от рекурсии. Поэтому
draft уже проверен prepare job, а перед merge владелец добавляет редакторский коммит
(дата/status/reference evidence), после которого выполняется обычный pull_request CI.
Не обходите required checks. Если нужен отдельный бот с CI по его событиям, согласуйте GitHub App.
[Ограничения GITHUB_TOKEN](https://docs.github.com/en/actions/how-tos/writing-workflows/choosing-when-your-workflow-runs/triggering-a-workflow).

## Токены

MVP выбирает короткоживущий repository-scoped **GITHUB_TOKEN**, доступный только в opt-in job.
GitHub App пригодится позже: installation token, точные права и независимые события, но потребует
создания/установки App и защищённого ключа. PAT привязан к человеку, требует срока/ротации и
легче получает лишние права, поэтому по умолчанию не используется.
[Официальные правила минимальных прав](https://docs.github.com/en/actions/reference/security/secure-use).

## Реальный AI-адаптер — следующий отдельный шаг

Ни модель, ни API key не выбраны. В будущем конфигурация включает provider/model и переменную
`LAB_LLM_API_KEY`; код адаптера реализует тот же Provider без изменения ядра.
Добавляются явный opt-in затрат, лимит запросов/токенов, таймаут, структурированный JSON,
проверка неоднозначностей и отдельный контур компиляции без ключа. Ответ модели не управляет
shell, POM, workflow или правами. Не передавать секретный environment в исполнение сгенерированного кода.

OpenAI API: API key и оплата по условиям выбранной модели/токенов; доступ и бюджет этого
аккаунта не проверялись. Перед подключением сверяем [официальные тарифы OpenAI API](https://developers.openai.com/api/docs/pricing)
и согласуем лимит расходов. Не предполагаем наличие оплаченного API-доступа.

GitHub Models как альтернативу **не подключаем**: по [официальной документации GitHub](https://docs.github.com/en/github-models)
сервис полностью закрыт 30 июля 2026, включая inference API и BYOK. Поэтому сравнивать
его прежние бесплатные квоты с текущим OpenAI API было бы неверно. Новый альтернативный
provider выбирается отдельно после проверки актуальных прав/условий. Проверено 16.11.2026.
Сейчас используется только локальный fixture.

## Границы автономии

Разрешены локальные файлы, генерация draft, проверки, документация, чтение публичных
технических источников и загрузка закреплённых открытых зависимостей.
Владелец решает: где создать репозиторий, лицензию, push/PR/merge, rulesets и права,
секреты, платные API, включение расписания и отправку Telegram. Никакого молчаливого включения.
