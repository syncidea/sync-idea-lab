"""Доверенный entrypoint подготовки fixture; используется только workflow_dispatch/schedule."""
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "challenge_generator"))
from generate import generate
from lab import ROOT, require, main_guard


def prepare(challenge_id: str | None) -> dict:
    plan = generate(ROOT, challenge_id, "fixture", True)
    if plan["changed"]:
        output = ROOT / "docs/releases" / plan["id"]
        output.mkdir(parents=True, exist_ok=True)
        (output / "pr.md").write_text(
            f"# [challenge-publication] {plan['id']}\n\n"
            "Draft: fixture provider, без LLM/API.\n\n"
            "Генератор проверил структуру и метаданные. Workflow отдельно запускает editorial; "
            "его фактический статус смотрите в Actions.\n\n"
            "- [ ] Проверить постановку и сложность\n"
            "- [ ] Проверить внешнюю локальную реализацию на публичных тестах\n"
            "- [ ] Зафиксировать агрегированный отчёт без исходников решения\n"
            "- [ ] Согласовать лицензию и дату\n"
            "- [ ] Перевести draft → approved → published, обновить published.json\n"
            "- [ ] Получить review владельца и вручную выполнить merge\n\n"
            "Эталон не включён. Behavioral tests генератор не запускал. Auto-merge отсутствует.\n",
            encoding="utf-8")
        (output / "telegram.md").write_text(
            f"#LiveCoding · {plan['id']}\n\nНовая бесплатная Java-практика Sync IDEA Lab!\n"
            f"Задача и открытые тесты: <REPOSITORY_URL>/tree/main/{plan['module']}\n\n"
            "Fork → решение → PR → review. Учебные PR закрываем без merge.\n"
            "Ссылка-заглушка заменяется после создания репозитория. Не отправлено в Telegram.\n",
            encoding="utf-8")
    return plan


def main():
    plan = prepare(os.environ.get("CHALLENGE_ID") or None)
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
            output.write(f"id={plan['id']}\nchanged={str(plan['changed']).lower()}\n")


if __name__ == "__main__":
    main_guard(main)
