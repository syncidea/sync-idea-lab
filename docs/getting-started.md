# Настройка Java 21 и IntelliJ IDEA

[README проекта](../README.md) содержит команды для скачивания задачи, запуска тестов и сдачи решения.

## Открыть задачу в IntelliJ IDEA

1. Откройте корневой `pom.xml` как Maven-проект.
2. В **Project Structure → Project** укажите JDK 21 как **Project SDK**.
3. В настройках Maven выберите **Maven Wrapper**, а в настройках Maven Runner укажите JDK 21.
4. Дождитесь загрузки зависимостей. Для проверки запускайте команду из README в терминале IDE.

## Если сборка не запускается

- `release version 21 not supported` означает, что сборка выбрала старую Java. Выполните
  `.\mvnw.cmd --version` в PowerShell или `./mvnw --version` в Linux и macOS. Проверьте версию и путь
  Java в выводе Wrapper. Если команда работает в терминале, но падает в IDE, проверьте Maven Runner.
- Для первого запуска нужен доступ к Maven Central, откуда Wrapper и Maven загружают необходимые файлы.
  Если скачивание оборвалось, проверьте соединение и повторите команду.
- `UnsupportedOperationException` в результатах тестов стартового проекта ожидаемо до реализации задачи.
