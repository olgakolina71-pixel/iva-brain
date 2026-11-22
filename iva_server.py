"""IVA local browser chat. Run: python iva_server.py"""
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock
from urllib.parse import urlparse
from iva_language import IVaLanguage

HOST, PORT, THINK_SECONDS = "127.0.0.1", 8765, 3
iva = IVaLanguage()
lock = Lock()

PAGE = r"""<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>IVA Chat</title><style>
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at top,#20265a,#090e1b 65%);color:#edf1ff;font:16px system-ui;min-height:100dvh;display:grid;place-items:center;padding:16px}.app{width:min(820px,100%);height:min(900px,calc(100dvh - 32px));min-height:480px;background:#10182bed;border:1px solid #293653;border-radius:24px;display:flex;flex-direction:column;overflow:hidden;box-shadow:0 24px 90px #0008}header{padding:18px 22px;background:#151f35;border-bottom:1px solid #293653;display:flex;align-items:center;gap:13px}.logo{width:44px;height:44px;border-radius:14px;background:linear-gradient(135deg,#8b7cff,#48c8d5);display:grid;place-items:center;font-weight:900}h1{font-size:18px;margin:0}.sub{font-size:12px;color:#9eacc8}.online{margin-left:auto;color:#8fe0bd;font-size:12px}#messages{flex:1;overflow:auto;padding:22px;display:flex;flex-direction:column;gap:14px}.msg{max-width:80%;padding:12px 15px;border-radius:18px;line-height:1.5;white-space:pre-wrap;overflow-wrap:anywhere}.user{align-self:flex-end;background:#685bd4;border-bottom-right-radius:5px}.iva{align-self:flex-start;background:#1a2944;border:1px solid #30415f;border-bottom-left-radius:5px}.who{font-size:11px;color:#b5c2df;margin-bottom:4px}#typing{min-height:28px;padding:0 22px;color:#aab7d1;font-size:13px}form{display:flex;gap:10px;padding:14px;background:#151f35;border-top:1px solid #293653}textarea{flex:1;resize:none;min-height:48px;max-height:130px;border:1px solid #394968;border-radius:15px;background:#0b1325;color:white;padding:13px;font:inherit;outline:none}textarea:focus{border-color:#8b7cff}button{border:0;border-radius:14px;padding:0 20px;background:#8172f5;color:white;font-weight:700}button:disabled{opacity:.5}.note{text-align:center;color:#7788a8;font-size:11px;padding:0 12px 12px}@media(max-width:560px){body{padding:0}.app{height:100dvh;border:0;border-radius:0}.msg{max-width:90%}#messages{padding:16px}header{padding:14px 16px}form{padding:10px}}
</style></head><body><main class="app"><header><div class="logo">IVA</div><div><h1>IVA</h1><div class="sub">Локальный чат • экспериментальная версия</div></div><div class="online">● локально</div></header><section id="messages" aria-live="polite"><div class="msg iva"><div class="who">IVA</div>Привет! Напиши сообщение — я отвечу примерно через 3 секунды.</div></section><div id="typing"></div><form id="form"><textarea id="input" rows="1" placeholder="Напиши сообщение…"></textarea><button id="send">Отправить</button></form><div class="note">Ничего не скачивается. Переписка хранится локально в iva_memory.json.</div></main><script>
const f=document.querySelector('#form'),i=document.querySelector('#input'),m=document.querySelector('#messages'),t=document.querySelector('#typing'),b=document.querySelector('#send');
function add(s,c){let n=document.createElement('div');n.className='msg '+c;let w=document.createElement('div');w.className='who';w.textContent=c==='user'?'Ты':'IVA';let p=document.createElement('div');p.textContent=s;n.append(w,p);m.append(n);m.scrollTop=m.scrollHeight}
async function send(){let s=i.value.trim();if(!s||b.disabled)return;add(s,'user');i.value='';i.style.height='auto';b.disabled=true;t.textContent='IVA думает…';try{let r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:s})});let d=await r.json();if(!r.ok)throw Error(d.error||'Ошибка');add(d.reply,'iva')}catch(e){add('Ошибка: '+e.message,'iva')}finally{b.disabled=false;t.textContent='';i.focus()}}
f.addEventListener('submit',e=>{e.preventDefault();send()});i.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}});i.addEventListener('input',()=>{i.style.height='auto';i.style.height=Math.min(i.scrollHeight,130)+'px'});
</script></body></html>"""

class Handler(BaseHTTPRequestHandler):
    def send_data(self, code, data, kind):
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if urlparse(self.path).path == "/":
            self.send_data(200, PAGE.encode(), "text/html; charset=utf-8")
        else:
            self.send_data(404, b"Not found", "text/plain")

    def do_POST(self):
        if urlparse(self.path).path != "/api/chat":
            self.send_data(404, b'{"error":"Not found"}', "application/json")
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size < 1 or size > 10000:
                raise ValueError("Сообщение пустое или слишком большое.")
            data = json.loads(self.rfile.read(size).decode("utf-8"))
            message = str(data.get("message", "")).strip()
            if not message or len(message) > 2000:
                raise ValueError("Напиши сообщение до 2000 символов.")
            time.sleep(THINK_SECONDS)
            with lock:
                answer = iva.reply(message)
            body = json.dumps({"reply": answer}, ensure_ascii=False).encode()
            self.send_data(200, body, "application/json; charset=utf-8")
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            body = json.dumps({"error": str(exc)}, ensure_ascii=False).encode()
            self.send_data(400, body, "application/json; charset=utf-8")

    def log_message(self, fmt, *args):
        print("[IVA] " + (fmt % args))

if __name__ == "__main__":
    print(f"IVA запущена: http://{HOST}:{PORT}")
    print("Остановить: Ctrl+C")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
