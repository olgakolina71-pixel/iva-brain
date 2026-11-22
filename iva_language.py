"""IVA Language v0.4: tiny dialogue learner with example-based retrieval.

Learns explicit facts and user-approved dialogue pairs locally. This is a small
retrieval/symbolic experiment, not a neural language model or general understanding.
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
STOP_WORDS = {"это", "как", "что", "кто", "где", "когда", "почему", "зачем", "ли", "а", "и", "в", "на", "я", "ты", "мы", "вы", "он", "она", "они", "мне", "меня", "тебя", "про", "для", "же", "ну"}


class IVaLanguage:
    def __init__(self, memory_path: str | Path = DEFAULT_MEMORY, seed: int | None = None):
        self.memory_path = Path(memory_path)
        self.rng = random.Random(seed)
        self.memory = self._load_memory()

    def _load_memory(self) -> dict:
        empty = {"turns": [], "examples": [], "facts": [], "dialogues": [], "last_topic": None}
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
        self.memory_path.write_text(json.dumps(self.memory, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _clean(text: str) -> str:
        return " ".join(text.strip().split())[:2000]

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return TOKEN_RE.findall(text.lower())

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"[^а-яёa-z0-9 ]", "", value.lower()).strip()

    @staticmethod
    def _keywords(text: str) -> set[str]:
        return {w for w in TOKEN_RE.findall(text.lower()) if w not in STOP_WORDS and len(w) > 1}

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

    def _extract_fact(self, example: str) -> dict | None:
        sentence = self._normalize(example)
        match = re.match(r"^(.+?)\s+(?:это|является)\s+(.+)$", sentence)
        if match:
            subject, obj = match.groups()
            relation = "это"
        else:
            pattern = "|".join(map(re.escape, RELATIONS))
            match = re.match(rf"^(.+?)\s+({pattern})\s+(.+)$", sentence)
            if not match:
                return None
            subject, relation, obj = match.groups()
        subject, obj = subject.strip(), obj.strip()
        if not subject or not obj or len(subject) > 60 or len(obj) > 100:
            return None
        return {"subject": subject, "relation": "создаёт" if relation == "создает" else relation, "object": obj}

    def learn_dialogue(self, user_text: str, iva_text: str) -> bool:
        user_text, iva_text = self._clean(user_text), self._clean(iva_text)
        if len(self._keywords(user_text)) < 1 or not iva_text:
            return False
        pair = {"user": user_text, "iva": iva_text}
        if pair not in self.memory["dialogues"]:
            self.memory["dialogues"].append(pair)
            self.memory["dialogues"] = self.memory["dialogues"][-1000:]
            self._save()
        return True

    def _retrieve_dialogue(self, text: str) -> str | None:
        query = self._keywords(text)
        if not query:
            return None
        best_score, best_answer = 0.0, None
        # Reuse both explicitly saved examples and ordinary past chat turns.
        # This is automatic example retrieval, not neural-network training.
        past_pairs = list(self.memory.get("dialogues", [])) + list(self.memory.get("turns", []))
        for pair in past_pairs:
            candidate = self._keywords(pair.get("user", ""))
            if not candidate:
                continue
            overlap = len(query & candidate)
            # Jaccard rewards meaningful overlap without favoring long examples.
            score = overlap / len(query | candidate)
            if score > best_score:
                best_score, best_answer = score, pair.get("iva")
        return best_answer if best_score >= 0.34 else None

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
        return re.sub(r"\s+([.!?])", r"\1", " ".join(result).strip())[:240]

    def _answer_fact_question(self, text: str) -> str | None:
        q = self._normalize(text)
        facts = self.memory.get("facts", [])
        match = re.match(r"^(?:что|кто)\s+(?:такое|такой|такая)\s+(.+)$", q)
        if match:
            subject = match.group(1).strip()
            found = [f for f in facts if f["subject"] == subject and f["relation"] == "это"]
            if found:
                return f"{subject.capitalize()} — это {found[-1]['object']}."
        match = re.match(r"^что\s+(любит|изучает|создаёт|помогает|использует)\s+(.+)$", q)
        if match:
            relation, subject = match.groups()
            found = [f for f in facts if f["subject"] == subject and f["relation"] == relation]
            if found:
                return f"{subject.capitalize()} {relation} {found[-1]['object']}."
        match = re.match(r"^(?:кто|что)\s+(любит|изучает|создаёт|помогает|использует)\s+(.+)$", q)
        if match:
            relation, obj = match.groups()
            found = [f for f in facts if f["relation"] == relation and f["object"] == obj]
            if found:
                names = ", ".join(f["subject"] for f in found[-3:])
                return f"По моим примерам, {names} {relation} {obj}."
        return None

    def _remember(self, user_text: str, answer: str) -> None:
        self.memory["turns"].append({"time": datetime.now(timezone.utc).isoformat(), "user": user_text, "iva": answer})
        self.memory["turns"] = self.memory["turns"][-100:]
        self._save()

    def reply(self, user_text: str) -> str:
        text = self._clean(user_text)
        if not text:
            return "Напиши что-нибудь — я прочитаю."
        s = text.lower()
        words = [w for w in self._tokens(s) if w not in {".", "!", "?"}]

        fact_answer = self._answer_fact_question(text)
        learned_answer = self._retrieve_dialogue(text)
        if fact_answer:
            answer = fact_answer
        elif learned_answer:
            answer = learned_answer
        elif any(w in words for w in ("привет", "здравствуй", "хай", "ку")):
            answer = "Привет! Как настроение? О чём хочешь поговорить?"
        elif any(x in s for x in ("кто ты", "как тебя зовут", "что ты такое")):
            answer = "Я IVA. Я пока учусь разговаривать на примерах и запоминать связи между понятиями."
        elif any(x in s for x in ("что ты умеешь", "что умеешь")):
            answer = "Я могу отвечать на некоторые выученные вопросы и искать похожие диалоги в своей памяти. Чему научимся дальше?"
        elif any(w in words for w in ("спасибо", "спс", "благодарю")):
            answer = "Пожалуйста! Что ещё обсудим?"
        elif any(w in words for w in ("пока", "увидимся")):
            answer = "Пока! До следующего разговора."
        elif any(x in s for x in ("как дела", "как ты")):
            answer = "Я на связи и готова учиться. А у тебя как?"
        elif "?" in text:
            answer = "Я пока не знаю ответа. Объясни мне его, а потом проверь, запомнила ли я."
        else:
            topic = next((w for w in words if len(w) > 4), None)
            if topic:
                self.memory["last_topic"] = topic
                answer = f"Интересная тема — «{topic}». Расскажешь, что ты об этом думаешь?"
            else:
                answer = "Я тебя слушаю. Расскажи чуть подробнее?"
        self._remember(text, answer)
        return answer

    def reset_memory(self) -> None:
        self.memory = {"turns": [], "examples": [], "facts": [], "dialogues": [], "last_topic": None}
        self._save()
