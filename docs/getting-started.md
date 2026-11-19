# Первый запуск

Установите JDK 21 (например, Temurin 21) и Git. Python 3.12+ нужен редакторским
инструментам, для Java-решения достаточно JDK и Wrapper. Maven отдельно не нужен.
IntelliJ IDEA: откройте корневой pom.xml, выберите Project SDK 21 и Maven Wrapper,
для Maven runner также выберите JDK 21.

После создания репозитория адрес будет указан в README. Пока ссылка `<REPOSITORY_URL>` —
заглушка, её нельзя использовать как реальную команду clone.

PowerShell из корня локальной копии:

```powershell
$env:JAVA_HOME = 'C:\path\to\jdk-21'
& "$env:JAVA_HOME\bin\java.exe" --version
.\mvnw.cmd --version
.\mvnw.cmd -pl challenges/java-core/SIL-001-idempotency-registry clean test-compile
.\mvnw.cmd -pl challenges/java-core/SIL-001-idempotency-registry clean test
```

Первая Maven-команда компилирует starter и JUnit-код; вторая проверяет реализацию и до
выполнения TODO падает. В логах ищите имя теста и ожидаемый/фактический результат.
Отчёты: `challenges/java-core/SIL-001-idempotency-registry/target/surefire-reports`.

Linux/macOS:

```sh
export JAVA_HOME=/path/to/jdk-21
./mvnw -pl challenges/java-core/SIL-001-idempotency-registry clean test-compile
./mvnw -pl challenges/java-core/SIL-001-idempotency-registry clean test
```

`release version 21 not supported` означает, что Maven использует старый JDK: проверьте
его вывод `--version`, JAVA_HOME и Maven runner IDE. Для задания нужен JDK 21.
Изменение `$env:JAVA_HOME` действует только в текущем PowerShell.

Первый запуск требует доступа к Maven Central. После загрузки зависимостей возможен
`-o` (offline), но только если все нужные плагины и зависимости уже в локальном cache.
Не копируйте Maven credentials/settings.xml в PR.

Работа участника после публикации:

```powershell
git switch -c submission/SIL-001
# Правьте только Java в src/main/java выбранной задачи, затем запустите тесты.
git add challenges/java-core/SIL-001-idempotency-registry/src/main/java
git commit -m '[submission SIL-001] Реализовать реестр'
# Push в свой fork и открытие PR — действия самого участника после публикации.
```

Проверка решения через Python: `python tools/check_solution.py SIL-001`.
Полная проверка редакторского каталога: `python tools/editorial.py`.
