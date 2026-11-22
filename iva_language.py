"""IVA Language v0.2: a tiny learnable Russian text experiment.

This is NOT a large language model. It learns word-to-word transitions only
from examples explicitly supplied with teach(text), then composes short text.
All learned examples stay in a local JSON file.
"""
from __future__ import annotations

import json
import random
import re
from collections import defaultdict
from pathlib import Path
from datetime import datetime, timezone

TOKEN_RE = re.compile(r"[а-яёa-z0-9]+|[.!?]", re.IGNORECASE)
DEFAULT_MEMORY = Path("iva_memory.json")


class IVaLanguage:
    def __init__(self, memory_path: str | Path = DEFAULT_MEMORY, seed: int | None = None):
        self.memory_path = Path(memory_path)
        self.rng = random.Random(seed)
        self.memory = self._load_memory()

    def _load_memory(self) -> dict:
        empty = {"turns": [], "examples": [], "last_topic": None}
        if not self.memory_path.exists():
            return empty
        try:
            data = json.loads(self.memory_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return empty
            data.setdefault("turns", [])
            data.setdefault("examples", [])
            data.setdefault("last_topic", None)
            return data
        except (OSError, json.JSONDecodeError):
            return empty

    def _save(self) -> None:
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        self.memory_path.write_text(
            json.dumps(self.memory, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _clean(text: str) -> str:
        return " ".join(text.strip().split())[:2000]

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return TOKEN_RE.findall(text.lower())

    def teach(self, example: str) -> int:
        """Add one explicitly supplied sentence as a local training example."""
        example = self._clean(example)
        tokens = self._tokens(example)
        if len(tokens) < 3:
            return 0
        self.memory["examples"].append(example)
        self.memory["examples"] = self.memory["examples"][-500:]
        self._save()
        return len(tokens)

    def generate(self, max_words: int = 18) -> str:
        """Generate a short sequence from learned word transitions."""
        transitions: dict[str, list[str]] = defaultdict(list)
        starts: list[str] = []
        for example in self.memory.get("examples", []):
            words = self._tokens(example)
            if words:
                starts.append(words[0])
                for left, right in zip(words, words[1:]):
                    transitions[left].append(right)
        if not starts:
            return "Я пока не выучила примеры. Научи меня командой /teach текст."
        word = self.rng.choice(starts)
        result = [word]
        for _ in range(max_words - 1):
            choices = transitions.get(word)
            if not choices:
                break
            word = self.rng.choice(choices)
            if word in {".", "!", "?"}:
                if len(result) >= 4:
                    result.append(word)
                    break
                continue
            result.append(word)
        sentence = " ".join(result).strip()
        sentence = re.sub(r"\s+([.!?])", r"\1", sentence)
        return sentence[:240]

    def _remember(self, user_text: str, answer: str) -> None:
        self.memory["turns"].append({
            "time": datetime.now(timezone.utc).isoformat(),
            "user": user_text,
            "iva": answer,
        })
        self.memory["turns"] = self.memory["turns"][-20:]
        self._save()

    def reply(self, user_text: str) -> str:
        text = self._clean(user_text)
        if not text:
            return "Напиши что-нибудь — я прочитаю."
        s = text.lower()
        words = [w for w in self._tokens(s) if w not in {".", "!", "?"}]
        topic = next((w for w in words if len(w) > 4), None)

        if any(w in words for w in ("привет", "здравствуй", "хай", "ку")):
            answer = "Привет! О чём поговорим?"
        elif any(x in s for x in ("кто ты", "как тебя зовут", "что ты такое")):
            answer = "Я IVA. Я экспериментирую с языком и учусь составлять короткие фразы на примерах, которым меня явно обучили."
        elif any(x in s for x in ("что ты умеешь", "что умеешь")):
            answer = "Я могу поддержать простой диалог и учиться связям между словами на примерах через /teach. Это пока маленький эксперимент, а не полноценная языковая модель."
        elif any(w in words for w in ("спасибо", "спс", "благодарю")):
            answer = "Пожалуйста! Можем продолжать."
        elif any(w in words for w in ("пока", "увидимся")):
            answer = "Пока! До следующего разговора."
        elif any(x in s for x in ("как дела", "как ты")):
            answer = "Я работаю. У меня нет человеческих чувств, но я могу рассказать о состоянии своей системы."
        elif topic:
            self.memory["last_topic"] = topic
            answer = f"Ты упомянул «{topic}». Что именно ты хотел бы об этом рассказать?"
        else:
            answer = "Я прочитала сообщение. Можешь привести пример или объяснить подробнее?"

        self._remember(text, answer)
        return answer

    def reset_memory(self) -> None:
        self.memory = {"turns": [], "examples": [], "last_topic": None}
        self._save()
