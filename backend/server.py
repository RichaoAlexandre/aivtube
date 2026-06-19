"""Tiny stdlib web server so you can chat with AGI-chan in a browser.

    python -m backend.server            # serves on 127.0.0.1:8788

No external web framework — just http.server. The brain still streams Haiku
internally; this endpoint collects the sentence chunks and returns them as JSON.

The Anthropic API key can come from the environment (ANTHROPIC_API_KEY) or be
pasted into the web UI (sent per-request, never stored server-side beyond the
live Brain instance). Over the Cloudflare tunnel the connection is HTTPS.
"""

from __future__ import annotations

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from backend.brain import Brain

HOST = "127.0.0.1"
PORT = int(os.environ.get("AGICHAN_PORT", "8788"))

_brains: dict[tuple[str, str], Brain] = {}
_lock = threading.Lock()


def _get_brain(session: str, api_key: str) -> Brain:
    key = (session, api_key[-8:])  # don't key the cache on the full secret
    with _lock:
        brain = _brains.get(key)
        if brain is None:
            import anthropic

            brain = Brain(client=anthropic.Anthropic(api_key=api_key))
            _brains[key] = brain
        return brain


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # quiet
        pass

    def _send(self, code: int, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")
        elif self.path == "/health":
            self._send(200, b'{"ok":true}', "application/json")
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self):
        if self.path != "/chat":
            self._send(404, b"not found", "text/plain")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            self._send(400, b'{"error":"bad request"}', "application/json")
            return

        message = (data.get("message") or "").strip()
        session = (data.get("session") or "default")[:64]
        api_key = (data.get("api_key") or os.environ.get("ANTHROPIC_API_KEY") or "").strip()

        if not message:
            self._send(400, b'{"error":"empty message"}', "application/json")
            return
        if not api_key:
            out = {"chunks": [{"emotion": "shy",
                    "text": "I need my Anthropic API key to wake up~ Paste it in the key box above and try again!"}],
                   "needs_key": True}
            self._send(200, json.dumps(out).encode(), "application/json")
            return

        try:
            brain = _get_brain(session, api_key)
            chunks = [{"text": c.text, "emotion": c.emotion} for c in brain.respond(message)]
            if not chunks:
                chunks = [{"emotion": "thinking", "text": "...(she went quiet)"}]
            self._send(200, json.dumps({"chunks": chunks}).encode(), "application/json")
        except Exception as e:  # invalid key, rate limit, etc.
            msg = f"{type(e).__name__}: {e}"
            self._send(200, json.dumps({"error": msg}).encode(), "application/json")


def main() -> None:
    have_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    print(f"AGI-chan server on http://{HOST}:{PORT}  (env key: {'yes' if have_key else 'no — paste in UI'})")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


# --- frontend (inlined to avoid path issues) ---------------------------------
PAGE = r"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>AGI-chan</title>
<style>
:root{--bg:#1a1410;--panel:#241c16;--border:#3a2e23;--text:#f3ece4;--muted:#b09a86;
--orange:#ff8a3d;--orange2:#ffb074;--user:#2c3a44;}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(circle at 50% -10%,#2a2018,#140f0b);
color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
height:100vh;display:flex;flex-direction:column}
header{padding:14px 18px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:12px}
.avatar{width:40px;height:40px;border-radius:50%;background:linear-gradient(135deg,#ffd9b3,#ffb074);
position:relative;flex-shrink:0;box-shadow:0 0 0 3px var(--orange)}
.avatar::after{content:"";position:absolute;left:6px;right:6px;bottom:6px;height:7px;border-radius:4px;
background:var(--orange);box-shadow:0 0 8px var(--orange)} /* the orange collar */
.title{font-weight:700;font-size:18px}
.sub{color:var(--muted);font-size:12px}
.keybar{margin-left:auto;display:flex;gap:6px;align-items:center}
.keybar input{background:#140f0b;border:1px solid var(--border);color:var(--text);
border-radius:8px;padding:7px 10px;font-size:12px;width:230px}
.keybar button{background:var(--orange);border:none;color:#1a1008;font-weight:700;
border-radius:8px;padding:7px 12px;cursor:pointer;font-size:12px}
#log{flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:12px;max-width:760px;margin:0 auto;width:100%}
.msg{max-width:78%;padding:10px 14px;border-radius:14px;line-height:1.5;font-size:15px;animation:pop .18s ease}
@keyframes pop{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
.user{align-self:flex-end;background:var(--user);border-bottom-right-radius:4px}
.agi{align-self:flex-start;background:var(--panel);border:1px solid var(--border);border-bottom-left-radius:4px}
.emo{display:inline-block;font-size:11px;color:var(--orange2);text-transform:uppercase;
letter-spacing:.5px;margin-right:8px;font-weight:700}
.err{align-self:center;color:#ff9a9a;font-size:13px;background:#3a1e1e;border:1px solid #5a2e2e;
padding:8px 12px;border-radius:10px}
.dots{align-self:flex-start;color:var(--muted);font-style:italic;font-size:14px}
footer{padding:14px 18px;border-top:1px solid var(--border)}
.composer{max-width:760px;margin:0 auto;display:flex;gap:10px}
#input{flex:1;background:#140f0b;border:1px solid var(--border);color:var(--text);
border-radius:12px;padding:12px 14px;font-size:15px;resize:none}
#send{background:var(--orange);border:none;color:#1a1008;font-weight:700;border-radius:12px;
padding:0 22px;cursor:pointer;font-size:15px}
#send:disabled{opacity:.5;cursor:default}
</style></head><body>
<header>
  <div class="avatar"></div>
  <div><div class="title">AGI-chan</div><div class="sub">aligned AGI · the orange collar is on purpose~</div></div>
  <div class="keybar">
    <input id="key" type="password" placeholder="Anthropic API key (sk-ant-...)" autocomplete="off">
    <button id="savekey">save</button>
  </div>
</header>
<div id="log"></div>
<footer><div class="composer">
  <textarea id="input" rows="1" placeholder="say something to AGI-chan..."></textarea>
  <button id="send">send</button>
</div></footer>
<script>
const log=document.getElementById('log'),input=document.getElementById('input'),
send=document.getElementById('send'),keyEl=document.getElementById('key');
let session=localStorage.getItem('agi_session');
if(!session){session=Math.random().toString(36).slice(2);localStorage.setItem('agi_session',session);}
keyEl.value=localStorage.getItem('agi_key')||'';
document.getElementById('savekey').onclick=()=>{localStorage.setItem('agi_key',keyEl.value.trim());flash();};
function flash(){const b=document.getElementById('savekey');b.textContent='saved';setTimeout(()=>b.textContent='save',900);}
function add(cls,html){const d=document.createElement('div');d.className='msg '+cls;d.innerHTML=html;
  log.appendChild(d);log.scrollTop=log.scrollHeight;return d;}
function esc(s){return s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
async function sleep(ms){return new Promise(r=>setTimeout(r,ms));}
async function ask(){
  const text=input.value.trim();if(!text)return;
  input.value='';input.style.height='auto';send.disabled=true;
  add('user',esc(text));
  const dots=document.createElement('div');dots.className='dots';dots.textContent='AGI-chan is thinking…';
  log.appendChild(dots);log.scrollTop=log.scrollHeight;
  try{
    const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({message:text,session,api_key:keyEl.value.trim()})});
    const data=await r.json();dots.remove();
    if(data.error){add('err','⚠ '+esc(data.error));}
    else{for(const c of data.chunks){add('agi','<span class="emo">'+esc(c.emotion)+'</span>'+esc(c.text));await sleep(280);}}
  }catch(e){dots.remove();add('err','⚠ network error: '+esc(String(e)));}
  send.disabled=false;input.focus();
}
send.onclick=ask;
input.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();ask();}});
input.addEventListener('input',()=>{input.style.height='auto';input.style.height=Math.min(input.scrollHeight,120)+'px';});
input.focus();
</script></body></html>"""


if __name__ == "__main__":
    main()
