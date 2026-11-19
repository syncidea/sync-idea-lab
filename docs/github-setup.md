# Чек-лист владельца перед GitHub

Никакие пункты ниже автоматически не применены. Пока нет remote и публичного репозитория.

1. Явно разрешить создание публичного `syncidea/sync-idea-lab` и первый push.
2. Лицензии согласованы. MIT применяется к коду, CC BY 4.0 — к текстам заданий.
   Правообладатель — Vladimir Chavkin. См. [LICENSE-SCOPE.md](../LICENSE-SCOPE.md).
3. Подтвердить владельца `@syncidea` в `.github/CODEOWNERS`, указать приватный контакт модерации
   и включить private vulnerability reporting.
4. Прочитать `git diff --cached`, проверить `python tools/validate_catalog.py`,
   `python tools/audit_publication.py`, `python tools/editorial.py`. Проверить имена/авторство коммита.
5. Создать репозиторий без автогенерации README/LICENSE, установить main как default branch.
   Создание, добавление remote и push выполняются только после отдельного разрешения.
6. Actions → General: разрешить нужные официальные actions, read-only default workflow permissions;
   **не включать Send write tokens to workflows from pull requests**, не передавать secrets fork PR.
   Для внешних contributors оставить approval запуска (желательно всех внешних участников),
   разрешить только GitHub-hosted runners для PR. Не подключать self-hosted runner.
7. Rules → Rulesets → New branch ruleset → target `main`, enforcement Active:
   Require a pull request before merging; минимум 1 approval; dismiss stale approvals;
   require approval of most recent reviewable push; require code owner review после заполнения
   CODEOWNERS; require conversation resolution; block force pushes и deletions.
   Required status checks: **publication-policy** и **editorial** (выбрать после первого прогона).
   `submission` не required для merge: учебные PR не сливаются. Bypass list пуст по возможности.
   Если тип аккаунта/тариф/организация не позволяют ruleset, использовать Branch protection rule
   с теми же доступными параметрами. Если нет технического enforcement — ручной merge только
   владельцем и обязательная проверка типа PR, ограничение явно сообщить участникам.
8. Если владелец единственный сопровождающий и GitHub не позволяет одобрять свой PR, добавить
   доверенного reviewer либо осознанно определить ограниченный bypass владельца. Не обещать
   независимое одобрение при отсутствии второго человека; submission всё равно не мержить.
9. Создать labels: submission, challenge-publication, documentation, bug. Labels помогают навигации;
   policy использует заголовок и пути, а не изменяемые labels. Возможные цвета: 0969da, 8250df,
   1a7f37, cf222e. Автосоздание не выполнялось.
10. Проверить реальный fork PR: допустимое Java-изменение, красный starter, зелёное решение,
    отказ при изменении тестов/POM/workflow; убедиться, что publication-policy блокирует merge.
    GitHub workflows локально статически проверены, реального GitHub-прогона ещё не было.
    Перед approval запуска внешнего PR просматривать изменения `.github/workflows`:
    PR может менять определение собственной проверки. Одного required check с совпадающим
    именем недостаточно против такой подмены. Если доступен организационный required workflow
    из доверенного источника, включить его; для MVP обязательны code owner review и ручной контроль.
11. Одобрить публикационный PR SIL-001: published, дата, индекс и рабочие ссылки. Цель —
    среда 19:00 МСК, без обещания автоматического merge. Только после merge заменить placeholder
    в Telegram-анонсе и отдельно разрешить его отправку.
12. По желанию включить draft PR workflow и переменные расписания из automation.md.
    API key LLM для MVP не нужен. Платный AI и Telegram-бот — отдельные решения.

Подготовленный локальный Git не настроен на чужую identity и не содержит внешнего remote.
Если initial commit ещё отсутствует, владелец выбирает `user.name`/`user.email` перед commit.
Не публикуйте локальные ТЗ, solutions, reports/local, target или секреты.

[GitHub rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
и [безопасность Actions](https://docs.github.com/en/actions/reference/security/secure-use).
