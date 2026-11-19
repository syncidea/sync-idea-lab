# Архитектура MVP и план

## Discovery 16.11.2026

В рабочей папке был только Sync_IDEA_Lab_Codex_Brief.md (32 111 байт), Git отсутствовал.
Документ полностью прочитан. Оригинал и копия PROJECT_BRIEF.md хранятся локально у владельца.

Обнаружены Git 2.52.0.windows.1, Python 3.14.6, Node и Docker CLI. В PATH Java 8,
Maven/javac/gh отсутствовали. Найден установленный GraalVM JDK 21.0.7 в пользовательской
папке `.jdks`, он использован через JAVA_HOME только в процессах проверок. Docker daemon
не проверялся: для MVP он не требуется. GitHub CLI на Windows не установлен и локально не нужен;
доверенный workflow использует gh с GitHub-hosted Ubuntu runner.

Доступны shell, файловые изменения, публичная документация и инструменты Codex.
Доступ к GitHub-аккаунту/организации не проверялся; внешние ресурсы и секреты не создавались.
Использованы только чтение официальной документации/метаданных и загрузка открытых зависимостей.

## Схема

```text
topics.json → fixture adapter → structured payload → schema validation → draft module
                                                             ↓
                       editorial: metadata + Python tests + Maven test-compile
                                                             ↓
external trusted Java sources → temporary copy → JUnit → aggregate evidence
                                                             ↓
                  owner review → approved/published → manual merge → Telegram draft

fork PR → trusted base SHA → diff allowlist → Java overlay → selected module JUnit
                                                    → review → close (no merge)
```

## Решения и компромиссы

1. **Maven reactor с независимыми учебными модулями**, общий parent и закреплённые плагины.
   Один Wrapper, единые Java/JUnit, команды `-pl`. Модуль не зависит от другого задания.
   Добавление задания меняет список modules, что делает генератор. Отдельные Maven-проекты
   дали бы больше свободы ценой дублирования и дрейфа версий.
2. **Открытые тесты и внешняя локальная реализация**. Starter компилируется, `test-compile`
   не запускает поведенческие тесты. Изолированный прогон локального решения выполняется
   до одобрения. Нет скрытых тестов, приватного репозитория, хранилища участников и leaderboard.
   Минус: можно подгонять решение под тесты, поэтому нужен review.
3. **Локальный fixture generator + opt-in GitHub draft workflow**. Python stdlib и JSON
   вместо YAML для данных: JSON — разрешённый ТЗ эквивалент, строгий парсер без PyYAML и eval.
   Генератор уже воспроизводим, API-адаптер остаётся интерфейсом. Нет расходов и догадок о
   доступных моделях/правах. До отдельного согласия реальный LLM-провайдер не реализуется.

## Состояния

`backlog → draft → approved → published`. Запись темы и challenge.json должны совпадать.
Backlog не имеет модуля. Draft компилируется, но может ждать проверки внешней реализации.
Approved требует `reference_verified: true`, установленного редактором после фактической
проверки. Published дополнительно требует даты и совпадающей записи published.json.
Наличие boolean в JSON само по себе не доказательство: reviewer читает отчёт и CI.

SIL-001 локально `approved`. Дату публикации определит владелец при первом выпуске.
Индекс публикаций пуст, поскольку ни GitHub-публикация, ни merge ещё не выполнялись.
Текущие показатели канала не запрашивались, числа из ТЗ не используются как актуальные.

## Последовательность реализации

1. Discovery, контракт SIL-001, parent Maven/Wrapper, starter и JUnit — выполнено.
2. Проверка компиляции, красного starter и зелёной внешней реализации — выполнено.
3. Каталог, строгие валидаторы, fixture provider, dry-run и защита от повторов — выполнено.
4. Trusted-base submission, separate editorial, opt-in prepare draft и регрессии — выполнено.
5. Документация, шаблоны, Git-аудит и инструкции ruleset — выполнено локально.
6. Владелец выбрал `syncidea/sync-idea-lab`, MIT для кода и CC BY 4.0 для текстов заданий.
   После одобрения первого push предстоит проверить CI на GitHub.

## Версии

Java release 21; Maven 3.9.16; Wrapper 3.3.4 (only-script); JUnit BOM 5.14.4;
Compiler 3.16.0; Surefire 3.6.1; Clean 3.5.0; Resources 3.3.1; Jar 3.5.0.
Набор реально собран на Java 21.0.7. Python инструментов 3.12+, stdlib; CI 3.14.
SHA официальных actions закреплены в YAML и сверены с release tags 16.11.2026.
JDK в CI закреплён на LTS-линейке 21: актуальный security patch выбирает setup-java;
не закрепляем старый локальный patch 21.0.7 для публичных runners.

Maven ZIP проверен по upstream SHA-512, его SHA-256 записан в Wrapper properties.
Wrapper scripts взяты из официального only-script ZIP 3.3.4, с проверкой опубликованного
checksum SHA-1 по HTTPS (более сильного checksum у этого ZIP в Central не было).
Лицензия сторонних скриптов указана в [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).
[Документация Maven Wrapper](https://maven.apache.org/tools/wrapper/).

## Ближайшая итерация

SIL-003: Spring Boot REST endpoint регистрации, Bean Validation, единый ответ об ошибках,
граница транзакции и тесты MVC/service. Сначала без внешней БД и контейнеров; PostgreSQL и
Testcontainers добавить отдельным заданием о конкурентной уникальности после согласования.
Версию Spring и совместимость Java 21 проверить перед началом той итерации.
