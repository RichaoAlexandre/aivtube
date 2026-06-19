"""Tiny stdlib web server so you can chat with AGI-chan in a browser.

    python -m backend.server            # serves on 127.0.0.1:8788

Phase 3: serves a Live2D avatar (Hiyori placeholder) that lip-syncs to AGI-chan's
voice and shows facial expressions mapped from her emotion tags. The avatar,
PixiJS, and Cubism runtime load from CDN; her model audio drives the mouth in
the browser via pixi-live2d-display's `model.speak()`.

No external web framework — just http.server. The brain streams Haiku
internally; this endpoint collects the sentence chunks (text + emotion +
per-chunk MP3 audio) and returns them as JSON.

The Anthropic API key can come from the environment (ANTHROPIC_API_KEY) or be
pasted into the web UI (sent per-request, never stored server-side beyond the
live Brain instance). Over the Cloudflare tunnel the connection is HTTPS.
"""

from __future__ import annotations

import base64
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
_tts = None


def _get_tts():
    global _tts
    if _tts is None:
        from backend.voice import get_tts

        _tts = get_tts()
    return _tts


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
                    "text": "I need my Anthropic API key to wake up~ Paste it in the key box and try again!"}],
                   "needs_key": True}
            self._send(200, json.dumps(out).encode(), "application/json")
            return

        want_voice = data.get("voice", True)
        try:
            brain = _get_brain(session, api_key)
            tts = _get_tts() if want_voice else None
            chunks = []
            for c in brain.respond(message):
                chunk = {"text": c.text, "emotion": c.emotion}
                if tts is not None:
                    try:
                        audio = tts.synthesize(c.text)
                        if audio:
                            chunk["audio"] = base64.b64encode(audio).decode("ascii")
                            chunk["mime"] = tts.mime
                    except Exception:
                        pass  # voice is best-effort; text still goes through
                chunks.append(chunk)
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
html,body{height:100%}
body{margin:0;background:radial-gradient(circle at 50% -10%,#2a2018,#140f0b);
color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
height:100vh;display:flex;flex-direction:column}
header{padding:12px 18px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:12px;flex-shrink:0}
.badge{width:38px;height:38px;border-radius:50%;background:linear-gradient(135deg,#ffd9b3,#ffb074);
position:relative;flex-shrink:0;box-shadow:0 0 0 3px var(--orange)}
.badge::after{content:"";position:absolute;left:6px;right:6px;bottom:5px;height:6px;border-radius:4px;
background:var(--orange);box-shadow:0 0 8px var(--orange)}
.title{font-weight:700;font-size:17px}
.sub{color:var(--muted);font-size:12px}
.keybar{margin-left:auto;display:flex;gap:6px;align-items:center}
.keybar input{background:#140f0b;border:1px solid var(--border);color:var(--text);
border-radius:8px;padding:7px 10px;font-size:12px;width:210px}
.keybar button{background:var(--orange);border:none;color:#1a1008;font-weight:700;
border-radius:8px;padding:7px 11px;cursor:pointer;font-size:12px}
#main{flex:1;display:flex;min-height:0}
#stage{flex:1;position:relative;min-width:0}
#live2d{width:100%;height:100%;display:block}
#status{position:absolute;top:50%;left:0;right:0;text-align:center;color:var(--muted);font-size:14px;
transform:translateY(-50%);pointer-events:none}
#emoTag{position:absolute;left:14px;bottom:12px;font-size:12px;color:var(--orange2);font-weight:700;
text-transform:uppercase;letter-spacing:.5px;opacity:.8}
#side{width:430px;border-left:1px solid var(--border);display:flex;flex-direction:column;min-height:0}
#log{flex:1;overflow-y:auto;padding:18px;display:flex;flex-direction:column;gap:11px}
.msg{max-width:88%;padding:10px 13px;border-radius:14px;line-height:1.5;font-size:15px;animation:pop .18s ease}
@keyframes pop{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
.user{align-self:flex-end;background:var(--user);border-bottom-right-radius:4px}
.agi{align-self:flex-start;background:var(--panel);border:1px solid var(--border);border-bottom-left-radius:4px}
.emo{display:inline-block;font-size:11px;color:var(--orange2);text-transform:uppercase;
letter-spacing:.5px;margin-right:8px;font-weight:700}
.err{align-self:center;color:#ff9a9a;font-size:13px;background:#3a1e1e;border:1px solid #5a2e2e;
padding:8px 12px;border-radius:10px}
.dots{align-self:flex-start;color:var(--muted);font-style:italic;font-size:14px}
.composer{padding:12px;border-top:1px solid var(--border);display:flex;gap:10px}
#input{flex:1;background:#140f0b;border:1px solid var(--border);color:var(--text);
border-radius:12px;padding:11px 13px;font-size:15px;resize:none}
#send{background:var(--orange);border:none;color:#1a1008;font-weight:700;border-radius:12px;
padding:0 20px;cursor:pointer;font-size:15px}
#send:disabled{opacity:.5;cursor:default}
@media(max-width:820px){#main{flex-direction:column}#stage{height:42vh;flex:none}
#side{width:100%;flex:1;border-left:none;border-top:1px solid var(--border)}.keybar input{width:130px}}
</style></head><body>
<header>
  <div class="badge"></div>
  <div><div class="title">AGI-chan</div><div class="sub">aligned AGI · the orange collar is on purpose~</div></div>
  <div class="keybar">
    <button id="mute" title="mute / unmute voice">&#128266;</button>
    <input id="key" type="password" placeholder="Anthropic API key (sk-ant-...)" autocomplete="off">
    <button id="savekey">save</button>
  </div>
</header>
<div id="main">
  <div id="stage">
    <canvas id="live2d"></canvas>
    <div id="status">loading avatar…</div>
    <div id="emoTag"></div>
  </div>
  <div id="side">
    <div id="log"></div>
    <div class="composer">
      <textarea id="input" rows="1" placeholder="say something to AGI-chan..."></textarea>
      <button id="send">send</button>
    </div>
  </div>
</div>

<script src="https://cubism.live2d.com/sdk-web/cubismcore/live2dcubismcore.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/pixi.js@6.5.10/dist/browser/pixi.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/pixi-live2d-display-lipsyncpatch/dist/cubism4.min.js"></script>
<script>
const MODEL='https://cdn.jsdelivr.net/gh/Live2D/CubismWebSamples@master/Samples/Resources/Hiyori/Hiyori.model3.json';

// emotion tag -> additive face parameter deltas (Hiyori uses standard Cubism IDs)
const EMO={
 neutral:{},
 happy:{ParamMouthForm:0.9,ParamEyeLSmile:0.6,ParamEyeRSmile:0.6,ParamCheek:0.3},
 smug:{ParamMouthForm:0.5,ParamBrowLAngle:-0.4,ParamBrowRAngle:-0.4,ParamEyeLOpen:-0.2,ParamEyeROpen:-0.2},
 giggle:{ParamMouthForm:0.9,ParamEyeLSmile:0.9,ParamEyeRSmile:0.9,ParamCheek:0.4},
 curious:{ParamBrowLY:0.5,ParamBrowRY:0.5,ParamEyeLOpen:0.2,ParamEyeROpen:0.2},
 excited:{ParamMouthForm:1.0,ParamEyeLOpen:0.3,ParamEyeROpen:0.3,ParamCheek:0.5},
 surprised:{ParamBrowLY:0.8,ParamBrowRY:0.8,ParamEyeLOpen:0.5,ParamEyeROpen:0.5,ParamMouthForm:-0.2},
 thinking:{ParamBrowLY:-0.3,ParamBrowRY:-0.3,ParamEyeBallY:0.4,ParamMouthForm:-0.2},
 mischievous:{ParamMouthForm:0.7,ParamEyeLSmile:0.5,ParamEyeRSmile:0.5,ParamBrowLAngle:-0.3,ParamBrowRAngle:-0.3},
 shy:{ParamCheek:1.0,ParamEyeLOpen:-0.3,ParamEyeROpen:-0.3,ParamMouthForm:0.3,ParamEyeBallY:-0.3},
 proud:{ParamMouthForm:0.7,ParamBrowLY:0.2,ParamBrowRY:0.2,ParamCheek:0.2},
 sad:{ParamMouthForm:-0.7,ParamBrowLForm:-0.6,ParamBrowRForm:-0.6,ParamEyeLOpen:-0.3,ParamEyeROpen:-0.3},
};

const statusEl=document.getElementById('status'),emoTagEl=document.getElementById('emoTag');
let model=null, emo='neutral', env=0;

async function initAvatar(){
  if(!window.PIXI||!PIXI.live2d){statusEl.textContent='avatar lib failed to load (chat still works)';return;}
  const stage=document.getElementById('stage');
  const app=new PIXI.Application({view:document.getElementById('live2d'),resizeTo:stage,
    backgroundAlpha:0,antialias:true,sharedTicker:true,autoStart:true});
  try{
    model=await PIXI.live2d.Live2DModel.from(MODEL,{autoInteract:false});
    app.stage.addChild(model);
    model.anchor.set(0.5,0.5);
    const baseW=model.width, baseH=model.height;  // native size at scale 1
    function layout(){const sc=Math.min(stage.clientWidth/baseW, stage.clientHeight/baseH)*0.95;
      model.scale.set(sc); model.x=stage.clientWidth/2; model.y=stage.clientHeight/2;}
    layout(); window.addEventListener('resize',layout);

    // overlay emotion params right before the core recompute, so they win over idle motion
    const core=model.internalModel&&model.internalModel.coreModel;
    if(core&&typeof core.update==='function'){
      const orig=core.update.bind(core);
      core.update=function(){
        if(env>0){const m=EMO[emo]; if(m){for(const id in m){try{core.addParameterValueById(id,m[id]*env);}catch(e){}}}}
        orig();
      };
    }
    app.ticker.add(()=>{ if(env>0) env=Math.max(0, env-app.ticker.deltaMS/1000*0.45); });
    statusEl.textContent='';
  }catch(e){console.error('avatar load failed',e);statusEl.textContent='avatar failed to load (chat still works)';}
}

function setEmotion(e){emo=(e&&EMO[e])?e:'neutral';env=1;emoTagEl.textContent=emo;}
function speak(b64,mime){return new Promise(res=>{
  if(!model||typeof model.speak!=='function'){return res();}
  try{model.speak('data:'+(mime||'audio/mpeg')+';base64,'+b64,{volume:1.0,onFinish:res,onError:res});}
  catch(e){res();}});}

const log=document.getElementById('log'),input=document.getElementById('input'),
send=document.getElementById('send'),keyEl=document.getElementById('key');
let session=localStorage.getItem('agi_session');
if(!session){session=Math.random().toString(36).slice(2);localStorage.setItem('agi_session',session);}
keyEl.value=localStorage.getItem('agi_key')||'';
document.getElementById('savekey').onclick=()=>{localStorage.setItem('agi_key',keyEl.value.trim());flash();};
function flash(){const b=document.getElementById('savekey');b.textContent='saved';setTimeout(()=>b.textContent='save',900);}
let muted=localStorage.getItem('agi_muted')==='1';
const muteBtn=document.getElementById('mute');
function renderMute(){muteBtn.textContent=muted?'🔇':'🔊';}
muteBtn.onclick=()=>{muted=!muted;localStorage.setItem('agi_muted',muted?'1':'0');renderMute();};renderMute();
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
      body:JSON.stringify({message:text,session,api_key:keyEl.value.trim(),voice:!muted})});
    const data=await r.json();dots.remove();
    if(data.error){add('err','⚠ '+esc(data.error));}
    else{for(const c of data.chunks){
      add('agi','<span class="emo">'+esc(c.emotion)+'</span>'+esc(c.text));
      setEmotion(c.emotion);
      if(c.audio&&!muted){await speak(c.audio,c.mime);}else{await sleep(900);}
    }}
  }catch(e){dots.remove();add('err','⚠ network error: '+esc(String(e)));}
  send.disabled=false;input.focus();
}
send.onclick=ask;
input.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();ask();}});
input.addEventListener('input',()=>{input.style.height='auto';input.style.height=Math.min(input.scrollHeight,120)+'px';});
input.focus();
initAvatar();
</script></body></html>"""


if __name__ == "__main__":
    main()
