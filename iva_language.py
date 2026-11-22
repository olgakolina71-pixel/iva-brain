"""IVA Language v0.3: tiny Russian dialogue + explicit concept memory.

This is a symbolic learning experiment, not a neural language model.
It extracts a few simple relations from examples explicitly supplied via teach().
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
RELATIONS = ("любит", "изучает", "создаёт", "создает", "помогает", "использует")


class IVaLanguage:
    def __init__(self, memory_path: str | Path = DEFAULT_MEMORY, seed: int | None = None):
        self.memory_path = Path(memory_path)
        self.rng = random.Random(seed)
        self.memory = self._load_memory()

    def _load_memory(self) -> dict:
        empty = {"turns": [], "examples": [], "facts": [], "last_topic": None}
        if not self.memory_path.exists():
            return empty
        try:
            data = json.loads(self.memory_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return empty
            for key, value in empty.items():
                data.setdefault(key, value)
            return data
        except (OSError, json.JSONDecodeError):
            return empty

    def _save(self) -> None:
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        self.memory_path.write_text(
            json.dumps(self.memory, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    @staticmethod
    def _clean(text: str) -> str:
        return " ".join(text.strip().split())[:2000]

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return TOKEN_RE.findall(text.lower())

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"[^а-яёa-z0-9 ]", "", value.lower()).strip()

    def _extract_fact(self, example: str) -> dict | None:
        sentence = self._normalize(example)
        match = re.match(r"^(.+?)\s+(?:это|является)\s+(.+)$", sentence)
        if match:
            subject, obj = match.groups()
            relation = "это"
        else:
            relation_pattern = "|".join(map(re.escape, RELATIONS))
            match = re.match(rf"^(.+?)\s+({relation_pattern})\s+(.+)$", sentence)
            if not match:
                return None
            subject, relation, obj = match.groups()
        subject, obj = subject.strip(), obj.strip()
        if not subject or not obj or len(subject) > 60 or len(obj) > 100:
            return None
        if relation == "создает":
            relation = "создаёт"
        return {"subject": subject, "relation": relation, "object": obj}

    def teach(self, example: str) -> int:
        example = self._clean(example)
        tokens = self._tokens(example)
        if len(tokens) < 3:
            return 0
        self.memory["examples"].append(example)
        self.memory["examples"] = self.memory["examples"][-500:]
        fact = self._extract_fact(example)
        if fact and fact not in self.memory["facts"]:
            self.memory["facts"].append(fact)
            self.memory["facts"] = self.memory["facts"][-1000:]
        self._save()
        return len(tokens)

    def generate(self, max_words: int = 18) -> str:
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
        sentence = re.sub(r"\s+([.!?])", r"\1", " ".join(result).strip())
        return sentence[:240]

    def _answer_fact_question(self, text: str) -> str | None:
        q = self._normalize(text)
        facts = self.memory.get("facts", [])
        # "Что такое робот?" / "Кто такой робот?"
        match = re.match(r"^(?:что|кто)\s+(?:такое|такой|такая)\s+(.+)$", q)
        if match:
            subject = match.group(1).strip()
            found = [f for f in facts if f["subject"] == subject and f["relation"] == "это"]
            if found:
                return f"{subject.capitalize()} — это {found[-1]['object']}."
        # "Что любит робот?" / "Что изучает IVA?"
        match = re.match(r"^что\s+(любит|изучает|создаёт|помогает|использует)\s+(.+)$", q)
        if match:
            relation, subject = match.groups()
            found = [f for f in facts if f["subject"] == subject and f["relation"] == relation]
            if found:
                return f"{subject.capitalize()} {relation} {found[-1]['object']}."
        # "Кто любит программирование?"
        match = re.match(r"^(?:кто|что)\s+(любит|изучает|создаёт|помогает|использует)\s+(.+)$", q)
        if match:
            relation, obj = match.groups()
            found = [f for f in facts if f["relation"] == relation and f["object"] == obj]
            if found:
                names = ", ".join(f["subject"] for f in found[-3:])
                return f"По моим примерам, {names} {relation} {obj}."
        return None

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

        fact_answer = self._answer_fact_question(text)
        if fact_answer:
            answer = fact_answer
        elif any(w in words for w in ("привет", "здравствуй", "хай", "ку")):
            answer = "Привет! О чём поговорим?"
        elif any(x in s for x in ("кто ты", "как тебя зовут", "что ты такое")):
            answer = "Я IVA. Я учусь находить простые связи между понятиями в примерах, которым меня явно обучили."
        elif any(x in s for x in ("что ты умеешь", "что умеешь")):
            answer = "Я могу вести простой диалог, собирать фразы и отвечать на некоторые вопросы по фактам из моих примеров."
        elif any(w in words for w in ("спасибо", "спс", "благодарю")):
            answer = "Пожалуйста! Можем продолжать."
        elif any(w in words for w in ("пока", "увидимся")):
            answer = "Пока! До следующего разговора."
        elif any(x in s for x in ("как дела", "как ты")):
            answer = "Я работаю. Могу рассказать, что уже выучила."
        elif topic:
            self.memory["last_topic"] = topic
            answer = f"Ты упомянул «{topic}». Я пока не знаю о нём достаточно. Можешь научить меня через /teach?"
        else:
            answer = "Я прочитала сообщение. Можешь привести пример или объяснить подробнее?"

        self._remember(text, answer)
        return answer

    def reset_memory(self) -> None:
        self.memory = {"turns": [], "examples": [], "facts": [], "last_topic": None}
        self._save()
