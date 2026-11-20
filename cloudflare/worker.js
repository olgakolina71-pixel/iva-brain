import { DurableObject } from "cloudflare:workers";

const clamp = (n) => Math.max(0, Math.min(1, Number(n) || 0));
const now = () => Date.now();

export class IVABrain extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    ctx.blockConcurrencyWhile(async () => {
      ctx.storage.sql.exec("CREATE TABLE IF NOT EXISTS memories (id INTEGER PRIMARY KEY AUTOINCREMENT, ts INTEGER NOT NULL, text TEXT NOT NULL, importance REAL NOT NULL, kind TEXT NOT NULL DEFAULT 'experience', consolidated INTEGER NOT NULL DEFAULT 0)");
      ctx.storage.sql.exec("CREATE TABLE IF NOT EXISTS experiences (id INTEGER PRIMARY KEY AUTOINCREMENT, ts INTEGER NOT NULL, event TEXT NOT NULL, decision TEXT NOT NULL, feedback TEXT)");
      ctx.storage.sql.exec("CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY CHECK(id=1), data TEXT NOT NULL)");
      const row = ctx.storage.sql.exec("SELECT data FROM state WHERE id=1").toArray()[0];
      if (!row) {
        const state = {
          energy: 0.82, fatigue: 0.12, interest: 0.5, curiosity: 0.55,
          laziness: 0.25, mood: 0.5, asleep: false, internal_days: 0,
          last_tick: now(), activity: "наблюдение", last_autonomy_day: -1,
          version: "0.1"
        };
        ctx.storage.sql.exec("INSERT INTO state(id,data) VALUES(1,?)", JSON.stringify(state));
      }
      if (await ctx.storage.getAlarm() === null) await ctx.storage.setAlarm(now() + 600000);
    });
  }

  getState() {
    const row = this.ctx.storage.sql.exec("SELECT data FROM state WHERE id=1").toArray()[0];
    return JSON.parse(row.data);
  }

  save(state) {
    this.ctx.storage.sql.exec("UPDATE state SET data=? WHERE id=1", JSON.stringify(state));
  }

  tick(state) {
    const timestamp = now();
    const elapsed = Math.max(0, timestamp - (state.last_tick || timestamp));
    const internalDays = elapsed / 3600000; // 1 real hour = 1 IVA internal day
    state.internal_days += internalDays;
    if (state.asleep) {
      state.fatigue = clamp(state.fatigue - internalDays * 0.30);
      state.energy = clamp(state.energy + internalDays * 0.30);
      if (state.energy >= 0.78 && state.fatigue <= 0.28) {
        state.asleep = false;
        state.activity = "самостоятельное пробуждение";
        state.mood = clamp(state.mood + 0.02);
      }
    } else {
      state.fatigue = clamp(state.fatigue + internalDays * 0.045);
      state.energy = clamp(state.energy - internalDays * 0.045);
      if (state.fatigue > 0.72 || state.energy < 0.24) {
        state.asleep = true;
        state.activity = "сон и консолидация памяти";
      }
    }
    state.last_tick = timestamp;
    return state;
  }

  decide(state) {
    if (state.asleep) return "спать";
    const score = state.interest * 0.36 + state.curiosity * 0.36 + state.energy * 0.28
      - state.laziness * 0.24 - state.fatigue * 0.28;
    if (score > 0.57) return "исследовать событие";
    if (score > 0.35) return "наблюдать, отложить";
    return "не уделять внимание сейчас";
  }

  async observe(event) {
    event = String(event || "").trim().slice(0, 2000);
    if (!event) return { error: "event text is required" };
    const state = this.tick(this.getState());
    if (state.asleep) {
      state.asleep = false;
      state.activity = "пробуждение по событию";
    }
    const words = event.toLowerCase().match(/[a-zа-яё0-9]{3,}/gi) || [];
    const novelty = Math.min(0.9, 0.35 + Math.min(words.length, 15) / 30);
    state.curiosity = clamp(state.curiosity * 0.76 + novelty * 0.24);
    state.interest = clamp(0.28 + Math.min(words.length, 12) / 18);
    const importance = clamp(0.25 + novelty * 0.4 + state.interest * 0.35);
    const decision = this.decide(state);
    this.ctx.storage.sql.exec("INSERT INTO memories(ts,text,importance,kind) VALUES(?,?,?,'experience')", now(), event, importance);
    this.ctx.storage.sql.exec("INSERT INTO experiences(ts,event,decision) VALUES(?,?,?)", now(), event, decision);
    state.energy = clamp(state.energy - 0.025);
    state.fatigue = clamp(state.fatigue + 0.035);
    state.activity = decision;
    if (state.fatigue > 0.72 || state.energy < 0.24) {
      state.asleep = true;
      state.activity = "сон после события";
    }
    this.save(state);
    return { decision, state };
  }

  async feedback(value) {
    value = String(value || "").toLowerCase();
    if (!["good", "bad", "neutral"].includes(value)) return { error: "feedback must be good, bad, or neutral" };
    const last = this.ctx.storage.sql.exec("SELECT id FROM experiences ORDER BY id DESC LIMIT 1").toArray()[0];
    if (!last) return { error: "no experience yet" };
    this.ctx.storage.sql.exec("UPDATE experiences SET feedback=? WHERE id=?", value, last.id);
    const state = this.tick(this.getState());
    if (value === "good") {
      state.mood = clamp(state.mood + 0.05);
      state.curiosity = clamp(state.curiosity + 0.025);
      state.laziness = clamp(state.laziness - 0.02);
    } else if (value === "bad") {
      state.mood = clamp(state.mood - 0.05);
      state.laziness = clamp(state.laziness + 0.03);
    } else {
      state.mood = clamp(state.mood * 0.98 + 0.01);
    }
    this.save(state);
    return { saved: value, state };
  }

  async sleep(reason = "manual") {
    const state = this.tick(this.getState());
    state.asleep = true;
    state.activity = "сон: " + String(reason).slice(0, 80);
    const rows = this.ctx.storage.sql.exec("SELECT id,text FROM memories WHERE consolidated=0 ORDER BY id LIMIT 100").toArray();
    if (rows.length) {
      const frequencies = {};
      for (const row of rows) {
        const terms = row.text.toLowerCase().match(/[a-zа-яё]{4,}/gi) || [];
        for (const term of terms) frequencies[term] = (frequencies[term] || 0) + 1;
      }
      const themes = Object.entries(frequencies).sort((a,b) => b[1]-a[1]).slice(0,8).map(([term]) => term);
      const summary = "Консолидация " + rows.length + " воспоминаний. Повторяющиеся темы: " + (themes.join(", ") || "нет выраженных тем") + ".";
      this.ctx.storage.sql.exec("INSERT INTO memories(ts,text,importance,kind,consolidated) VALUES(?,?,0.65,'sleep_summary',1)", now(), summary);
      this.ctx.storage.sql.exec("UPDATE memories SET consolidated=1 WHERE id IN (" + rows.map(() => "?").join(",") + ")", ...rows.map(row => row.id));
    }
    this.save(state);
    return { sleep: true, state };
  }

  async wake(reason = "manual") {
    const state = this.tick(this.getState());
    state.asleep = false;
    state.energy = Math.max(state.energy, 0.3);
    state.fatigue = Math.min(state.fatigue, 0.65);
    state.activity = "пробуждение: " + String(reason).slice(0,80);
    this.save(state);
    return { wake: true, state };
  }

  async memories(limit = 20) {
    limit = Math.max(1, Math.min(50, Number(limit) || 20));
    return this.ctx.storage.sql.exec("SELECT id,ts,text,importance,kind,consolidated FROM memories ORDER BY id DESC LIMIT ?", limit).toArray();
  }

  async status() {
    const state = this.tick(this.getState());
    this.save(state);
    const experienceCount = this.ctx.storage.sql.exec("SELECT COUNT(*) AS n FROM experiences").toArray()[0].n;
    const memoryCount = this.ctx.storage.sql.exec("SELECT COUNT(*) AS n FROM memories").toArray()[0].n;
    return { status: "ok", state, experience_count: experienceCount, memory_count: memoryCount };
  }

  async alarm() {
    let state = this.tick(this.getState());
    if (!state.asleep) {
      const day = Math.floor(state.internal_days);
      if (day > state.last_autonomy_day) {
        const recent = this.ctx.storage.sql.exec("SELECT text FROM memories ORDER BY id DESC LIMIT 5").toArray();
        state.last_autonomy_day = day;
        if (recent.length && state.curiosity > 0.35 && state.laziness < 0.75) {
          const task = "самостоятельно пересмотреть " + recent.length + " недавних воспоминаний";
          state.activity = task;
          this.ctx.storage.sql.exec("INSERT INTO memories(ts,text,importance,kind) VALUES(?,?,0.35,'self_task')", now(), task);
          state.energy = clamp(state.energy - 0.015);
          state.fatigue = clamp(state.fatigue + 0.02);
        } else {
          state.activity = "ничего не делать; отдых/наблюдение";
        }
      }
      if (state.fatigue > 0.72 || state.energy < 0.24) {
        state.asleep = true;
        state.activity = "автоматический сон";
      }
    } else if (state.energy >= 0.78 && state.fatigue <= 0.28) {
      state.asleep = false;
      state.activity = "самостоятельное пробуждение";
    }
    this.save(state);
    await this.ctx.storage.setAlarm(now() + 600000);
  }

  async handle(request) {
    const url = new URL(request.url);
    if (request.method === "GET" && url.pathname === "/status") return Response.json(await this.status());
    if (request.method === "GET" && url.pathname === "/memories") return Response.json(await this.memories(url.searchParams.get("limit")));
    if (request.method === "POST" && url.pathname === "/event") return Response.json(await this.observe((await request.json()).event));
    if (request.method === "POST" && url.pathname === "/feedback") return Response.json(await this.feedback((await request.json()).value));
    if (request.method === "POST" && url.pathname === "/sleep") return Response.json(await this.sleep("API request"));
    if (request.method === "POST" && url.pathname === "/wake") return Response.json(await this.wake("API request"));
    return new Response("Not found", { status: 404 });
  }
}

export default {
  async fetch(request, env) {
    const authorization = request.headers.get("Authorization") || "";
    if (!env.API_TOKEN || authorization !== "Bearer " + env.API_TOKEN) return new Response("Unauthorized", { status: 401 });
    const id = env.BRAIN.idFromName("iva-main");
    return env.BRAIN.get(id).handle(request);
  }
};
