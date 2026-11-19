"""Провайдеры возвращают только данные. Никаких API-вызовов или команд из ответа модели."""
from pathlib import Path
from typing import Protocol
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lab import ROOT, read_json, require


class Provider(Protocol):
    def generate(self, topic: dict) -> dict: ...


class FixtureProvider:
    def generate(self, topic: dict) -> dict:
        require(topic.get("fixture") == "stable-distinct", "No reviewed fixture for selected topic")
        return read_json(ROOT / "tools/challenge_generator/fixtures/stable-distinct.json")


def get_provider(name: str) -> Provider:
    require(name == "fixture", "Only fixture provider is enabled; paid API access requires owner approval")
    return FixtureProvider()
