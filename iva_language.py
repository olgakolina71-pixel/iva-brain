"""IVA Language v0.1 — a small, transparent Russian text interface for IVA Brain.

This is a starter conversational layer, not a pretrained language model.
It uses simple intent detection and response composition; it does not claim
to understand language like a large neural language model.
"""
from __future__ import annotations

import json
import random
import re
from pathlib import Path
from datetime import datetime, timezone

MEMORY_PATH = Path("iva_memory.json")
TOKEN_RE = re.compile(r"[a-zа-яё0-9]+", re.IGNORECASE)

class IVaLanguage:
    def __init__(self, memory_path: str | Path = MEMORY_PATH, seed: int | None = None):
        self.memory_path = Path(memory_path)
        self.rng = random.Random(seed)
        self.memory = self._load_memory()

    def _load_memory(self) -> dict:
        if not self.memory_path.exists():
            return {"turns": [], "user_name": None, "last_topic": None}
        try:
            data = json.loads(self.memory_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("Memory must be an object")
            data.setdefault("turns", [])
            data.setdefault("user_name", None)
            data.setdefault("last_topic", None)
            return data
        except (OSError, json.JSONDecodeError, ValueError):
            return {"turns": [], "user_name": None, "last_topic": None}

    def _save(self) -> None:
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        self.memory_path.write_text(
            json.dumps(self.memory, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _clean(text: str) -> str:
        return " ".join(text.strip().split())[:2000]

    def _remember(self, user_text: str, answer: str) -> None:
        self.memory["turns"].append({
            "time": datetime.now(timezone.utc).isoformat(),
            "user": user_text,
            "iva": answer,
        })
        self.memory["turns"] = self.memory["turns"][-20:]
        self._save()

    def _intent(self, text: str) -> str:
        s = text.lower().strip()
        words = set(TOKEN_RE.findall(s))
        if not words:
            return "empty"
        if words & {"привет", "здравствуй", "хай", "ку", "hello", "hi"}:
            return "greeting"
        if any(q in s for q in ("кто ты", "что ты такое", "как тебя зовут")):
            return "identity"
        if any(q in s for q in ("что ты умеешь", "твои возможности", "что умеешь")):
            return "capabilities"
        if any(q in s for q in ("как дела", "как ты", "твоё настроение", "твое настроение")):
            return "status"
        if any(q in s for q in ("пока", "до встречи", "увидимся")):
            return "farewell"
        if any(q in s for q in ("спасибо", "благодарю", "спс")):
            return "thanks"
        if any(q in s for q in ("помнишь", "что я говорил", "о чём мы")):
            return "memory"
        if s.endswith("?") or words & {"почему", "зачем", "когда", "где", "сколько", "как"}:
            return "question"
        return "statement"

    def reply(self, user_text: str) -> str:
        text = self._clean(user_text)
        if not text:
            return "Напиши что-нибудь — я прочитаю."
        intent = self._intent(text)

        if intent == "greeting":
            answer = self.rng.choice(["Привет! О чём поговорим?", "Привет! Я на связи.", "О, привет! Что обсудим?"])
        elif intent == "identity":
            answer = "Я IVA — экспериментальная система. Сейчас мой языковой модуль простой: я распознаю некоторые типы сообщений и составляю ответы."
        elif intent == "capabilities":
            answer = "Пока я умею вести простой текстовый диалог, распознавать базовые намерения и хранить последние сообщения. Сложные вопросы и свободное рассуждение мне ещё предстоит освоить."
        elif intent == "status":
            answer = "Я работаю и готов продолжать разговор. У меня нет человеческого настроения, но я могу сообщить своё состояние."
        elif intent == "farewell":
            answer = "Пока! История последних сообщений сохранится локально."
        elif intent == "thanks":
            answer = self.rng.choice(["Пожалуйста!", "Рад помочь. Что дальше?", "Не за что!"])
        elif intent == "memory":
            recent = self.memory.get("turns", [])[-2:]
            if recent:
                answer = "Я храню последние сообщения этой беседы. Последняя тема: " + (self.memory.get("last_topic") or "пока не определена") + "."
            else:
                answer = "Пока в моей памяти нет прошлых сообщений."
        elif intent == "question":
            answer = "Я вижу вопрос, но пока не умею надёжно отвечать на любые темы. Можешь переформулировать его проще — мой языковой модуль ещё развивается."
        else:
            answer = self.rng.choice([
                "Я прочитал сообщение. Расскажешь об этом подробнее?",
                "Интересно. Что ты имеешь в виду?",
                "Я пока не до конца понимаю такие фразы, но могу продолжить разговор.",
            ])

        if intent not in {"greeting", "farewell", "thanks", "empty"}:
            self.memory["last_topic"] = text[:120]
        self._remember(text, answer)
        return answer

    def reset_memory(self) -> None:
        self.memory = {"turns": [], "user_name": None, "last_topic": None}
        self._save()
