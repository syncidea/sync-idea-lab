# Sync IDEA Lab

Бесплатная практика по Java от [Sync IDEA](https://t.me/sync_idea_java). Выберите задачу,
допишите реализацию, запустите открытые JUnit-тесты и отправьте решение на разбор через Pull Request.

| Задача | Уровень | Что попрактикуете | Время |
| --- | --- | --- | --- |
| [SIL-001 · Одно событие — одна обработка в пределах TTL](challenges/java-core/SIL-001-idempotency-registry/README.md) | Middle | Многопоточность, идемпотентность и работа со временем | Около 90 минут |

## 1. Подготовьте окружение

Установите [Git](https://git-scm.com/install/) и [JDK 21](https://adoptium.net/temurin/releases/?version=21).
Для сдачи понадобится аккаунт GitHub. Maven Wrapper входит в проект и загрузит нужную версию Maven
при первом запуске. Для SIL-001 достаточно Git и JDK 21.

Откройте терминал и проверьте установку:

```text
git --version
java -version
```

В выводе `java -version` должна быть версия `21`. Если Windows выбирает другую Java, укажите
папку установленного JDK в PowerShell. Замените путь в примере своим:

```powershell
$env:JAVA_HOME = 'C:\path\to\jdk-21'
$env:Path = "$env:JAVA_HOME\bin;$env:Path"
java -version
```

## 2. Сделайте свою копию и создайте ветку

1. Нажмите **Fork → Create fork** в [репозитории Sync IDEA Lab](https://github.com/syncidea/sync-idea-lab).
   Форк — это копия проекта в вашем аккаунте GitHub, куда можно отправлять свои коммиты.
2. Откройте **Code → HTTPS** в своём форке и скопируйте адрес. В первой команде подставьте этот адрес
   вместо примера с `ВАШ_ЛОГИН`.
3. Скачайте копию и заведите отдельную ветку для задачи:

```text
git clone https://github.com/ВАШ_ЛОГИН/sync-idea-lab.git
cd sync-idea-lab
git switch -c submission/SIL-001
```

Дальше запускайте команды из папки `sync-idea-lab`, где лежат `mvnw.cmd` и корневой `pom.xml`.
Если работаете в IntelliJ IDEA, откройте эту папку как Maven-проект и выберите JDK 21 для проекта
и Maven Runner. [Настройка IDE и частые ошибки сборки](docs/getting-started.md).

## 3. Соберите задачу и напишите решение

Откройте [условие SIL-001](challenges/java-core/SIL-001-idempotency-registry/README.md) и прочитайте контракт,
примеры и критерии приёмки. Сначала проверьте, что проект собирается. В PowerShell:

```powershell
.\mvnw.cmd --version
.\mvnw.cmd -pl challenges/java-core/SIL-001-idempotency-registry clean test-compile
```

В Linux и macOS используйте `./mvnw` с теми же аргументами. В выводе Wrapper проверьте `Java version: 21`.
`test-compile` компилирует стартовый код и тесты и должен завершиться сообщением `BUILD SUCCESS`.

Реализуйте логику в [IdempotencyRegistry.java](challenges/java-core/SIL-001-idempotency-registry/src/main/java/dev/syncidea/lab/idempotency/IdempotencyRegistry.java).
В учебной сдаче можно изменять и добавлять только `.java`-файлы в `src/main/java` выбранной задачи.
Сохраните публичный API и используйте исходные тесты и конфигурацию сборки.

Запустите поведенческие тесты после реализации:

```powershell
.\mvnw.cmd -pl challenges/java-core/SIL-001-idempotency-registry clean test
```

До реализации падения с `UnsupportedOperationException` ожидаемы. Если тест падает после ваших изменений,
найдите его имя и сравните ожидаемое и фактическое поведение с условием. Подробные отчёты записываются
в `challenges/java-core/SIL-001-idempotency-registry/target/surefire-reports`.

## 4. Отправьте решение

После успешного запуска тестов проверьте список изменений. Добавьте только Java-исходники задачи:

```text
git status --short
git add -- challenges/java-core/SIL-001-idempotency-registry/src/main/java
git diff --cached --name-only
git commit -m "[submission SIL-001] Реестр идемпотентности"
git push -u origin submission/SIL-001
```

Откройте свой форк на GitHub и нажмите **Compare & pull request**. Проверьте обе стороны:

| Сторона PR | Репозиторий | Ветка |
| --- | --- | --- |
| **base** — куда отправляете | `syncidea/sync-idea-lab` | `main` |
| **head** — откуда берутся изменения | Ваш форк `ВАШ_ЛОГИН/sync-idea-lab` | `submission/SIL-001` |

Проверьте заголовок PR перед отправкой. Он должен начинаться с **`[submission SIL-001]`**.
Например, `[submission SIL-001] Реестр идемпотентности`. Заполните шаблон PR:
кратко опишите подход, укажите команду проверки и результат тестов. Решение и обсуждение будут
видны публично. Для навигации по форме см. [инструкцию GitHub по PR из форка](https://docs.github.com/en/pull-requests/how-tos/create-pull-requests/creating-a-pull-request-from-a-fork).

## 5. Посмотрите проверки и ответьте на замечания

На вкладке **Checks** в своём PR найдите **Submission CI → submission**. Этот запуск показывает,
проходит ли решение открытые тесты. Если GitHub пишет, что запуск ждёт одобрения, дождитесь
подтверждения от сопровождающего.

| Результат | Что делать |
| --- | --- |
| `submission` зелёный | Дождитесь обратной связи по решению. |
| `Test selected challenge` красный | Откройте этот шаг в логах и воспроизведите падение локально командой `clean test` из шага 3. |
| `Gate paths and copy Java sources into trusted build` красный | Сверьте ID в заголовке PR и список файлов на вкладке **Files changed**. Разрешены только `.java` в `src/main/java` выбранной задачи. |
| `publication-policy` красный | Для учебной сдачи это ожидаемо. Проверка блокирует слияние, чтобы задача сохранила исходный вид для следующих учеников. |

Чтобы исправить решение, закоммитьте изменения в той же ветке и выполните `git push`. GitHub
обновит существующий PR и перезапустит проверки. После разбора учебный PR закрывается без merge.

Если нашли ошибку в условии или тестах, [создайте issue](https://github.com/syncidea/sync-idea-lab/issues/new/choose) с ID задачи и шагами воспроизведения.

Код доступен по [MIT](LICENSE), тексты задач — по [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
[Подробнее о лицензиях и авторстве](LICENSE-SCOPE.md).
