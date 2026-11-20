"""IVA Brain v0.1 — experience-based experimental cognitive system.
No dataset training. State and memories are persisted in SQLite.
"""
from __future__ import annotations
import json, sqlite3, time
from dataclasses import dataclass, asdict
from pathlib import Path

DB_PATH = Path(__file__).with_name("iva_memory.sqlite3")

@dataclass
class BrainState:
    energy: float = 0.80
    fatigue: float = 0.15
    interest: float = 0.50
    curiosity: float = 0.55
    laziness: float = 0.25
    mood: float = 0.50
    asleep: bool = False
    internal_days: float = 0.0
    last_tick: float = 0.0

def clamp(v):
    return max(0.0, min(1.0, float(v)))

class IVABrain:
    def __init__(self, db_path=DB_PATH):
        self.db = sqlite3.connect(str(db_path))
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY CHECK(id=1), data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS experiences (id INTEGER PRIMARY KEY, ts REAL, event TEXT, action TEXT, feedback TEXT);
        CREATE TABLE IF NOT EXISTS memories (id INTEGER PRIMARY KEY, ts REAL, content TEXT, importance REAL DEFAULT 0.5, consolidated INTEGER DEFAULT 0);
        """)
        row = self.db.execute("SELECT data FROM state WHERE id=1").fetchone()
        self.state = BrainState(**json.loads(row["data"])) if row else BrainState(last_tick=time.time())
        self._tick()
        self._save()

    def _tick(self):
        now=time.time()
        if not self.state.last_tick: self.state.last_tick=now
        elapsed=max(0,now-self.state.last_tick)
        # Default: one real hour maps to one internal IVA day.
        self.state.internal_days += elapsed/3600.0
        if not self.state.asleep:
            self.state.fatigue=clamp(self.state.fatigue + elapsed/3600*0.04)
            self.state.energy=clamp(self.state.energy - elapsed/3600*0.04)
        else:
            self.state.fatigue=clamp(self.state.fatigue - elapsed/3600*0.30)
            self.state.energy=clamp(self.state.energy + elapsed/3600*0.30)
        self.state.last_tick=now

    def _save(self):
        self.db.execute("INSERT INTO state(id,data) VALUES(1,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data",(json.dumps(asdict(self.state)),))
        self.db.commit()

    def status(self):
        self._tick(); self._save()
        s=self.state
        mode="СОН" if s.asleep else "БОДРСТВУЕТ"
        return (f"IVA {mode} | внутреннее время: {s.internal_days:.2f} дней\n"
                f"энергия {s.energy:.2f} | усталость {s.fatigue:.2f} | интерес {s.interest:.2f}\n"
                f"любопытство {s.curiosity:.2f} | лень {s.laziness:.2f} | настроение {s.mood:.2f}")

    def observe(self, event):
        self._tick()
        event=event.strip()
        if not event: return "Событие пустое."
        if self.state.asleep:
            self.wake("event")
        words=set(event.lower().split())
        novelty=0.55 if len(words)>3 else 0.25
        self.state.curiosity=clamp(self.state.curiosity*0.75+novelty*0.25)
        self.state.interest=clamp(0.35+min(len(words),12)/20)
        importance=clamp(0.25+novelty*0.45+self.state.interest*0.3)
        self.db.execute("INSERT INTO memories(ts,content,importance) VALUES(?,?,?)",(time.time(),event,importance))
        action=self.decide(event)
        self.db.execute("INSERT INTO experiences(ts,event,action) VALUES(?,?,?)",(time.time(),event,action))
        self.state.energy=clamp(self.state.energy-0.03)
        self.state.fatigue=clamp(self.state.fatigue+0.04)
        if self.state.fatigue>0.82 or self.state.energy<0.18:
            self.sleep("tired")
            action += " (решение: отдохнуть)"
        self._save()
        return "Событие записано в опыт. Решение IVA: "+action

    def decide(self, event=""):
        s=self.state
        if s.asleep: return "оставаться во сне"
        if s.fatigue>0.78 or s.energy<0.20: return "пойти спать"
        score=s.interest*0.40+s.curiosity*0.35+s.energy*0.25-s.laziness*0.30-s.fatigue*0.25
        if score>0.55: return "исследовать / уделить внимание"
        if score>0.30: return "отложить и наблюдать"
        return "не заниматься этим сейчас"

    def feedback(self, value):
        self._tick()
        value=value.strip().lower()
        if value not in {"good","bad","neutral"}:
            return "Используй feedback good, bad или neutral."
        row=self.db.execute("SELECT id,action FROM experiences ORDER BY id DESC LIMIT 1").fetchone()
        if not row: return "Пока нет опыта для обратной связи."
        self.db.execute("UPDATE experiences SET feedback=? WHERE id=?",(value,row["id"]))
        if value=="good":
            self.state.mood=clamp(self.state.mood+0.06); self.state.curiosity=clamp(self.state.curiosity+0.03)
        elif value=="bad":
            self.state.mood=clamp(self.state.mood-0.06); self.state.laziness=clamp(self.state.laziness+0.04)
        else:
            self.state.mood=clamp(self.state.mood*0.98+0.01)
        self._save()
        return f"Обратная связь запомнена: {value}. Внутреннее состояние обновлено."

    def sleep(self, reason="self"):
        self._tick()
        self.state.asleep=True
        # Consolidate recent memories into a lightweight summary by recurring words.
        rows=self.db.execute("SELECT content FROM memories WHERE consolidated=0 ORDER BY id").fetchall()
        if rows:
            summary="Во время сна IVA обработала "+str(len(rows))+" воспоминаний."
            self.db.execute("INSERT INTO memories(ts,content,importance,consolidated) VALUES(?,?,0.65,1)",(time.time(),summary))
            self.db.execute("UPDATE memories SET consolidated=1 WHERE consolidated=0")
        self.state.laziness=clamp(self.state.laziness-0.05)
        self._save()

    def wake(self, reason="event"):
        self._tick()
        self.state.asleep=False
        self.state.energy=clamp(max(self.state.energy,0.25))
        self.state.fatigue=clamp(min(self.state.fatigue,0.70))
        self._save()

    def close(self):
        self._save()
        self.db.close()
