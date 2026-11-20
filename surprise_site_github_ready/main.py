# -*- coding: utf-8 -*-
"""
✨ Just for Sneha — a little surprise website (Streamlit)

Run:
    pip install -r requirements.txt
    python -m streamlit run main.py

Photos: five personal gallery photos are included in assets/photos/. Flower and Cupid scenes use enhanced semi-realistic 2.5D SVG characters.
Eyes photo: assets/eyes.jpg
Edit the CONFIG block below to change names, texts and the song.
"""
import base64
import glob
import io
import json
import os

import streamlit as st
import streamlit.components.v1 as components

# ═══════════════════════════════════════════════════════════════════
# ⚙️  CONFIG — edit these to make it yours
# ═══════════════════════════════════════════════════════════════════
HER_NAME = "SNEHA"                  # her name (leave "" to hide it)
YOUR_NAME = "Someone who wishes you well"      # signature at the end of the note, e.g. "Rahul"
SHOW_ASK = True                     # True = show the "cup of tea?" surprise at the end

YOUTUBE_ID = "M47Bgb4kNUo"          # the part after youtu.be/
SONG_TITLE = "Our Song"                # put the real song name here
SONG_ARTIST = "Just for you"          # artist name, or any short line

EYES_IMAGE = "assets/eyes.jpg"
PHOTO_DIR = "assets/photos"

# Note lines (each one is a separate paragraph)
NOTE_LINES = [
    "Hey Sneha,",
    "I hope this little surprise brings a smile to your face. You have a lovely way of making ordinary moments feel a little brighter.",
    "I just wanted to put together something thoughtful for you — a small reminder that the little things about you are appreciated.",
    "Keep being your cheerful, genuine self. I hope life gives you plenty of reasons to smile, today and always. 🌷",
    "Have a lovely day, and take care. ✨",
]

# Photo captions: (label under the photo, text on the back) — in photo order
PHOTO_CAPTIONS = [
    ("That Smile", "A warm little café glow, an easy smile, and a moment that feels effortlessly bright. Some frames have their own sunshine."),
    ("Golden Hour", "The sky was busy painting everything gold, while a fluffy little friend made the moment even warmer. A lovely kind of togetherness."),
    ("Little Magic", "A gentle kiss for a very lucky best friend. Pure affection, soft moments, and the kind of magic that needs no words."),
    ("Timeless Grace", "A little tradition, a little elegance, and confidence in every detail. Some looks carry their own quiet poetry."),
    ("My Favorite Frame", "A calm smile, beautiful details, and a moment that feels naturally memorable. Sometimes the simplest frames stay with us the longest."),
]

# Original upload names are included as fallbacks as well as the tidy filenames
# used in the ZIP. This prevents blank Polaroids when files were copied without
# being renamed.
PHOTO_FILES = [
    ("01_cafe_moment.jpg", "IMG_2602.PNG"),
    ("02_sunset_with_dog.jpg", "IMG_2601.PNG"),
    ("03_little_dog_kiss.jpg", "IMG_2598.PNG"),
    ("04_traditional_look.jpg", "IMG_2600.PNG"),
    ("05_colourful_smile.jpg", "IMG_2599.PNG"),
]

# Answers for the "Why are you special?" button
REASONS = [
    "Your smile changes the mood of a whole day, effortlessly.",
    "Your eyes — every look seems to carry a story.",
    "The way you push your hair back — I forget what I was about to say, every single time.",
    "You're exactly yourself, and that's the most beautiful thing.",
    "Time disappears when I talk to you.",
    "You're a little different, and that's the best kind of different.",
    "Even your tiny 'hmm' makes me happy.",
    "Because of you, ordinary days feel a bit extraordinary.",
]

# ═══════════════════════════════════════════════════════════════════
# 🖼️  Helpers
# ═══════════════════════════════════════════════════════════════════
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _abs(p):
    return p if os.path.isabs(p) else os.path.join(BASE_DIR, p)


def _to_data_uri(path, max_w=900, quality=84):
    """Resize a photo and return a base64 data URI safe for the HTML iframes."""
    from PIL import Image, ImageOps

    with Image.open(path) as original:
        im = ImageOps.exif_transpose(original).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, int(im.height * max_w / im.width)), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def _photo_search_dirs():
    """Look beside main.py first, then common nested project folders."""
    cwd = os.getcwd()
    candidates = [
        os.path.join(BASE_DIR, "assets", "photos"),
        os.path.join(BASE_DIR, "photos"),
        os.path.join(BASE_DIR, "assets"),
        BASE_DIR,
        os.path.join(BASE_DIR, "surprise_site", "assets", "photos"),
        os.path.join(os.path.dirname(BASE_DIR), "assets", "photos"),
        os.path.join(os.path.dirname(BASE_DIR), "surprise_site", "assets", "photos"),
        os.path.join(cwd, "assets", "photos"),
        os.path.join(cwd, "photos"),
        os.path.join(cwd, "surprise_site", "assets", "photos"),
    ]
    result, seen = [], set()
    for path in candidates:
        norm = os.path.normcase(os.path.abspath(path))
        if norm not in seen and os.path.isdir(path):
            seen.add(norm)
            result.append(path)
    return result


def _find_photo(index):
    expected, original_upload = PHOTO_FILES[index]
    wanted = {expected.casefold(), original_upload.casefold()}
    # Fast path: check the likely locations directly (also case-insensitive).
    for folder in _photo_search_dirs():
        try:
            names = {name.casefold(): name for name in os.listdir(folder)}
        except OSError:
            continue
        for name in wanted:
            actual = names.get(name)
            if actual:
                candidate = os.path.join(folder, actual)
                if os.path.isfile(candidate):
                    return candidate

    # Last-resort search handles users who extracted the ZIP into one extra
    # nested folder. Ignore virtual environments and version-control folders.
    roots = [BASE_DIR, os.getcwd()]
    visited = set()
    for root in roots:
        root = os.path.abspath(root)
        if root in visited or not os.path.isdir(root):
            continue
        visited.add(root)
        root_depth = root.rstrip(os.sep).count(os.sep)
        for current, dirs, files in os.walk(root):
            depth = current.rstrip(os.sep).count(os.sep) - root_depth
            dirs[:] = [d for d in dirs if d not in {".venv", "venv", ".git", "__pycache__", "node_modules"}]
            if depth > 4:
                dirs[:] = []
                continue
            lookup = {name.casefold(): name for name in files}
            for name in wanted:
                actual = lookup.get(name)
                if actual:
                    candidate = os.path.join(current, actual)
                    if os.path.isfile(candidate):
                        return candidate
    return None


@st.cache_data(show_spinner=False)
def load_eyes():
    p = _abs(EYES_IMAGE)
    return _to_data_uri(p, 1400, 88) if os.path.isfile(p) else ""


def load_photos():
    """Load the five named photos every run; avoid stale cached empty placeholders."""
    out = []
    for i, cap in enumerate(PHOTO_CAPTIONS):
        path = _find_photo(i)
        try:
            src = _to_data_uri(path, 780, 86) if path else ""
        except Exception:
            src = ""
        out.append({"src": src, "label": cap[0], "back": cap[1], "filename": path or PHOTO_FILES[i][0]})
    return out


def missing_gallery_photos():
    return [PHOTO_FILES[i][0] for i in range(len(PHOTO_FILES)) if not _find_photo(i)]


# ═══════════════════════════════════════════════════════════════════
# 🎨  Shared CSS / JS (injected into every section iframe)
# ═══════════════════════════════════════════════════════════════════
FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,600;1,500;1,600'
    '&family=Tiro+Bangla:ital@0;1&family=Hind+Siliguri:wght@400;500;600'
    '&family=DM+Sans:wght@400;500;600&family=Caveat:wght@500;600&display=swap" rel="stylesheet">'
)

COMMON_CSS = """
:root{--rose:#e0245e;--rose2:#ff6b92;--blush:#ffdbe3;--gold:#f6c58f;--ink:#fbeaee;--muted:#c9a9b2;
--serif:'Playfair Display','Playfair Display','Noto Serif Bengali',Georgia,serif;
--hand:'Caveat','Segoe Script',cursive;
--sans:'DM Sans','Inter',system-ui,-apple-system,sans-serif}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:transparent;color:var(--ink);font-family:var(--sans);overflow-x:hidden;-webkit-font-smoothing:antialiased}
.sec{position:relative;overflow:hidden;padding:90px 6vw 140px;min-height:__MINH__px}
.sec>.in{position:relative;z-index:2;max-width:1120px;margin:0 auto}
.wave{position:absolute;left:0;right:0;bottom:-1px;width:100%;height:70px;display:block;z-index:3;pointer-events:none}
.eyebrow{display:flex;align-items:center;gap:9px;letter-spacing:.26em;font-size:11.5px;text-transform:uppercase;color:var(--rose2);font-weight:600}
.eyebrow:before{content:"♥";font-size:11px}
h2.title{font-family:var(--serif);font-weight:500;font-size:clamp(32px,5vw,54px);line-height:1.18;margin:14px 0 14px}
h2.title em{font-style:italic;color:var(--rose2)}
p.sub{color:var(--muted);line-height:1.8;font-size:15.5px;max-width:520px}
.btn{display:inline-flex;align-items:center;gap:14px;border:0;cursor:pointer;color:#fff;font:600 15px var(--sans);
 padding:10px 10px 10px 26px;border-radius:999px;background:linear-gradient(135deg,#f0356d,#c81650);
 box-shadow:0 10px 30px -8px rgba(224,36,94,.7);transition:transform .25s,box-shadow .25s}
.btn i{display:grid;place-items:center;width:36px;height:36px;border-radius:50%;background:#fff;color:var(--rose);font-style:normal;font-size:17px}
.btn:hover{transform:translateY(-2px) scale(1.02);box-shadow:0 16px 36px -8px rgba(224,36,94,.9)}
.btn:active{transform:scale(.97)}
.toast{position:fixed;left:50%;bottom:24px;transform:translate(-50%,40px);opacity:0;background:rgba(20,8,12,.92);border:1px solid rgba(255,107,146,.4);
 color:#fff;padding:12px 20px;border-radius:14px;font-size:14.5px;z-index:99;transition:.45s;backdrop-filter:blur(8px);max-width:88vw;text-align:center}
.toast.show{transform:translate(-50%,0);opacity:1}
@keyframes fadeUp{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:none}}
@keyframes floaty{0%,100%{transform:translateY(0)}50%{transform:translateY(-9px)}}
@media (max-width:640px){.sec{padding:70px 22px 130px}}
"""

COMMON_JS = """
function fit(){try{var s=document.querySelector('.sec');var h=Math.ceil(s.getBoundingClientRect().height);
 var f=window.frameElement;if(f){f.style.height=h+'px';f.setAttribute('height',h);}}catch(e){}}
try{new ResizeObserver(fit).observe(document.querySelector('.sec'));}catch(e){}
window.addEventListener('load',function(){fit();setTimeout(fit,400);setTimeout(fit,1500)});
function toast(t,ms){var el=document.getElementById('toast');if(!el)return;el.textContent=t;el.classList.add('show');
 clearTimeout(el._t);el._t=setTimeout(function(){el.classList.remove('show')},ms||2600)}
function hostCtx(){try{var d=window.parent.document;void d.body;return {doc:d,win:window.parent}}catch(e){return {doc:document,win:window}}}
function scrollNext(){try{var f=window.frameElement;var c=f.closest('[data-testid="stElementContainer"]')||f;
 var n=c.nextElementSibling;if(n)n.scrollIntoView({behavior:'smooth',block:'start'})}catch(e){}}
function graphemes(s){try{return Array.from(new Intl.Segmenter('bn',{granularity:'grapheme'}).segment(s),function(x){return x.segment})}catch(e){return Array.from(s)}}
"""

WAVE = (
    '<svg class="wave" viewBox="0 0 1440 80" preserveAspectRatio="none">'
    '<path fill="__NEXT__" d="M0,42 C180,86 360,4 600,36 C840,68 1040,6 1240,34 C1330,46 1400,52 1440,42 L1440,80 L0,80 Z"/></svg>'
)


def page(body, css="", js="", bg="#0a0608", nxt="#1f0d15", min_h=600, wave=True):
    html = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        + FONTS
        + "<style>"
        + COMMON_CSS.replace("__MINH__", str(min_h))
        + ".sec{background-color:%s}" % bg
        + css
        + "</style></head><body><div class='sec'>"
        + body
        + (WAVE.replace("__NEXT__", nxt) if wave else "")
        + "</div><div class='toast' id='toast'></div><script>"
        + COMMON_JS
        + js
        + "</script></body></html>"
    )
    return html


def esc(s):
    return json.dumps(s, ensure_ascii=False)


# ═══════════════════════════════════════════════════════════════════
# 1️⃣  HERO — starts with the eyes (eyelids open)
# ═══════════════════════════════════════════════════════════════════
def hero_html():
    eyes = load_eyes()
    greet = f"{HER_NAME}, " if HER_NAME else ""
    body = f"""
<canvas id="sp" style="position:absolute;inset:0;width:100%;height:100%;z-index:1;pointer-events:none"></canvas>
<div class="glow"></div>
<div class="in">
  <div class="eyewrap" id="eyes" title="👀">
     <img src="{eyes}" alt="">
     <div class="lid t"></div><div class="lid b"></div>
  </div>
  <div class="copy">
    <div class="eyebrow" style="justify-content:center">A little surprise, just for you</div>
    <h1>A little corner<br><em>of happiness</em></h1>
    <div class="opening-quote">
      <p>Not every surprise needs a special occasion. Sometimes, it's just about making someone's ordinary day a little brighter.</p>
      <p>So, here's a tiny corner of happiness, filled with little things, warm thoughts, and a few unexpected smiles.</p>
      <p>Take your time, explore, and enjoy this little surprise made just for you. 🌸</p>
    </div>
    <button class="btn" onclick="scrollNext()">Let's unwrap the surprise <i>→</i></button>
  </div>
</div>
"""
    css = """
.sec{padding-top:46px;text-align:center}
.glow{position:absolute;left:50%;top:150px;width:900px;height:420px;transform:translateX(-50%);z-index:0;
 background:radial-gradient(closest-side,rgba(224,36,94,.28),transparent);filter:blur(30px);animation:pulse 6s ease-in-out infinite}
@keyframes pulse{50%{opacity:.55;transform:translateX(-50%) scale(1.08)}}
.eyewrap{position:relative;width:min(1000px,100%);margin:0 auto;aspect-ratio:826/297;overflow:hidden;cursor:pointer;
 -webkit-mask-image:radial-gradient(ellipse closest-side at 50% 50%,#000 62%,transparent 100%);mask-image:radial-gradient(ellipse closest-side at 50% 50%,#000 62%,transparent 100%)}
.eyewrap img{width:100%;height:100%;object-fit:cover;display:block;filter:contrast(1.06) saturate(1.1);animation:kb 22s ease-in-out infinite alternate;transform-origin:50% 45%}
@keyframes kb{to{transform:scale(1.09)}}
.lid{position:absolute;left:0;right:0;height:51%;background:#0a0608;z-index:2}
.lid.t{top:0;animation:lt 2.6s .5s cubic-bezier(.7,0,.2,1) forwards}
.lid.b{bottom:0;animation:lb 2.6s .5s cubic-bezier(.7,0,.2,1) forwards}
@keyframes lt{0%{transform:none}60%{transform:translateY(-100%)}100%{transform:translateY(-100%)}}
@keyframes lb{0%{transform:none}60%{transform:translateY(100%)}100%{transform:translateY(100%)}}
.copy{margin-top:22px;animation:fadeUp 1.4s 2.4s both}
h1{font-family:var(--serif);font-weight:500;font-size:clamp(40px,7vw,82px);line-height:1.12;margin:14px 0 18px;letter-spacing:-.01em}
h1 em{font-style:italic;color:var(--rose2);text-shadow:0 0 40px rgba(255,107,146,.45)}
.opening-quote{max-width:720px;margin:0 auto 30px;padding:22px 28px;border:1px solid rgba(255,255,255,.11);border-radius:22px;
 background:linear-gradient(145deg,rgba(255,255,255,.065),rgba(255,255,255,.018));box-shadow:0 18px 48px rgba(0,0,0,.18);backdrop-filter:blur(10px)}
.opening-quote p{color:#e8cbd4;font-size:clamp(14px,1.5vw,16px);line-height:1.85;margin:0 0 9px}
.opening-quote p:last-child{margin-bottom:0;color:#ffd1dc}
@media(max-width:640px){.opening-quote{padding:18px 18px;margin-bottom:24px}.opening-quote p{line-height:1.75}}
"""
    js = """
(function(){
 var c=document.getElementById('sp'),x=c.getContext('2d'),W,H,P=[];
 function rs(){W=c.width=c.offsetWidth;H=c.height=c.offsetHeight;}rs();addEventListener('resize',rs);
 for(var i=0;i<46;i++)P.push({x:Math.random(),y:Math.random(),r:Math.random()*1.8+.4,s:Math.random()*.0004+.00008,a:Math.random()*6.28,g:Math.random()<.4});
 function f(t){x.clearRect(0,0,W,H);P.forEach(function(p){p.y-=p.s*16;if(p.y<-.02){p.y=1.02;p.x=Math.random()}
  var o=.25+.35*Math.sin(t/900+p.a);x.beginPath();x.arc(p.x*W+Math.sin(t/2200+p.a)*12,p.y*H,p.r,0,6.28);
  x.fillStyle=(p.g?'rgba(246,197,143,':'rgba(255,107,146,')+o+')';x.fill()});requestAnimationFrame(f)}
 requestAnimationFrame(f);
 var n=0,msgs=['Caught you looking 👀','Oh! Our eyes met 😳','Staring that long makes me shy 🙈'];
 document.getElementById('eyes').addEventListener('click',function(){n++;if(n%3===0)toast(msgs[(n/3-1)%msgs.length],2800)});
})();
"""
    return page(body, css, js, bg="#0a0608", nxt="#1f0d15", min_h=760)


# ═══════════════════════════════════════════════════════════════════
# 2️⃣  NOTE — open the envelope, the letter types itself out
# ═══════════════════════════════════════════════════════════════════
def note_html():
    body = """
<div class="petals"></div>
<div class="in grid">
  <div class="left">
    <div class="eyebrow">A little letter</div>
    <h2 class="title">A few small words,<br><em>sincerely meant</em></h2>
    <p class="sub">Open the envelope. There are a few lines inside, just for you.</p>
    <div class="env" id="env" onclick="openEnv()">
      <div class="back"></div>
      <div class="paper"><span>For you ✉️</span></div>
      <div class="front"></div>
      <div class="flap"></div>
      <div class="seal">✿</div>
    </div>
    <div class="hint" id="hint">↑ Tap the envelope</div>
  </div>
  <div class="right">
    <div class="note" id="note"><div class="tape"></div><div class="lines" id="lines"></div></div>
  </div>
</div>
"""
    css = """
.sec{background-image:radial-gradient(700px 400px at 85% 30%,rgba(224,36,94,.16),transparent),radial-gradient(500px 300px at 5% 90%,rgba(246,197,143,.08),transparent)}
.grid{display:grid;grid-template-columns:1fr 1.15fr;gap:60px;align-items:center}
@media(max-width:820px){.grid{grid-template-columns:1fr;gap:36px}}
.env{position:relative;width:310px;height:210px;margin-top:38px;cursor:pointer;perspective:900px;transition:transform .3s}
.env:hover{transform:translateY(-4px) rotate(-1deg)}
.env .back{position:absolute;inset:0;background:#c81c52;border-radius:8px;box-shadow:0 24px 40px -12px rgba(0,0,0,.6)}
.env .front{position:absolute;inset:0;z-index:3;border-radius:8px;background:#ee3f76;clip-path:polygon(0 0,50% 50%,100% 0,100% 100%,0 100%)}
.env .front:after{content:"";position:absolute;inset:0;background:linear-gradient(to top,#d92c5f,#f25785);clip-path:polygon(0 100%,50% 40%,100% 100%)}
.env .flap{position:absolute;left:0;right:0;top:0;height:62%;z-index:4;background:#ff5c8a;clip-path:polygon(0 0,100% 0,50% 100%);transform-origin:top;transition:transform .7s ease .1s,z-index 0s .35s;border-radius:8px 8px 0 0}
.env .seal{position:absolute;left:50%;top:44%;transform:translate(-50%,-50%);z-index:5;width:40px;height:40px;border-radius:50%;background:#ffe3a8;color:#b8315c;display:grid;place-items:center;font-size:20px;box-shadow:0 4px 10px rgba(0,0,0,.35);transition:.4s}
.env .paper{position:absolute;left:22px;right:22px;top:100px;height:104px;z-index:2;background:#fff5ee;border-radius:5px;display:grid;place-items:center;color:#8a3a52;
 font-family:var(--hand);font-size:26px;transition:transform .8s ease .45s;animation:floaty 3.6s ease-in-out infinite}
.env.open .flap{transform:rotateX(180deg);z-index:1;opacity:0;transition:transform .7s ease .1s,opacity .4s ease .35s,z-index 0s .35s}
.env.open .seal{opacity:0;transform:translate(-50%,-50%) scale(.2)}
.env.open .paper{transform:translateY(-120px)}
.hint{margin-top:30px;color:var(--rose2);font-family:var(--hand);font-size:24px;animation:floaty 2.4s infinite}
.right{display:grid;place-items:center}
.note{position:relative;width:100%;max-width:520px;padding:44px 40px 40px;border-radius:6px;transform:rotate(1.4deg) translateY(30px);opacity:0;
 background:repeating-linear-gradient(#fff6ef 0 33px,#f3d7d6 33px 34px);background-position:0 18px;color:#58283a;box-shadow:0 30px 60px -20px rgba(0,0,0,.8);
 transition:opacity .8s,transform .9s cubic-bezier(.2,.9,.3,1.2);min-height:300px}
.note.show{opacity:1;transform:rotate(-1.2deg)}
.tape{position:absolute;top:-14px;left:50%;width:120px;height:30px;transform:translateX(-50%) rotate(-3deg);background:rgba(255,200,215,.7);backdrop-filter:blur(2px)}
.lines p{font-family:var(--hand);font-size:25px;line-height:34px;margin:0 0 0;min-height:34px}
.lines p.sig{margin-top:12px;text-align:right;color:#b8315c;font-size:27px}
.caret:after{content:"▍";color:#b8315c;animation:bl .8s steps(1) infinite}
@keyframes bl{50%{opacity:0}}
.petals{position:absolute;inset:0;pointer-events:none;z-index:1}
.petals i{position:absolute;top:-30px;width:12px;height:16px;border-radius:70% 0 70% 0;background:linear-gradient(135deg,#ff6b92,#c81650);opacity:.5;animation:fall linear infinite}
@keyframes fall{to{transform:translate(60px,900px) rotate(540deg)}}
@media(max-width:640px){.note{padding:38px 24px 30px}.lines p{font-size:22px;line-height:32px}.env{width:270px;height:185px}}
"""
    js = f"""
var LINES={esc(NOTE_LINES)},SIG={esc('— ' + YOUR_NAME)};
(function(){{var p=document.querySelector('.petals');for(var i=0;i<14;i++){{var e=document.createElement('i');e.style.left=Math.random()*100+'%';
 e.style.animationDuration=(9+Math.random()*9)+'s';e.style.animationDelay=(-Math.random()*14)+'s';p.appendChild(e)}}}})();
var opened=false;
function openEnv(){{
 if(opened)return;opened=true;document.getElementById('env').classList.add('open');document.getElementById('hint').style.opacity=0;
 setTimeout(function(){{document.getElementById('note').classList.add('show');type()}},900);
}}
function type(){{
 var box=document.getElementById('lines');var all=LINES.concat([SIG]);var li=0;
 function next(){{
  if(li>=all.length)return;
  var p=document.createElement('p');if(li===all.length-1)p.className='sig';box.appendChild(p);
  var g=graphemes(all[li]),i=0;p.classList.add('caret');
  (function step(){{ if(i<g.length){{p.textContent=g.slice(0,++i).join('');setTimeout(step,li===0?70:26)}}
   else{{p.classList.remove('caret');li++;setTimeout(next,380)}} }})();
 }}
 next();
}}
"""
    return page(body, css, js, bg="#1f0d15", nxt="#0a0608", min_h=720)


# ═══════════════════════════════════════════════════════════════════
# 3️⃣  ROPE GALLERY — polaroids on a rope + fairy lights, notes on the back
# ═══════════════════════════════════════════════════════════════════
def rope_html():
    photos = load_photos()
    body = """
<div class="in" style="margin-bottom:20px">
  <div class="eyebrow">A few frames, a few stories</div>
  <h2 class="title">Moments <em>on a rope</em></h2>
  <p class="sub">Five little frames, each with a tiny story waiting on the back. Tap a Polaroid to turn it over. ✨</p>
</div>
<div class="scroller" id="scroller"><div class="scene" id="scene"></div></div>
<div class="swipe" id="swipe">← Swipe to see more →</div>
"""
    css = """
.sec{background-image:radial-gradient(800px 380px at 50% 30%,rgba(246,197,143,.10),transparent),radial-gradient(600px 400px at 90% 100%,rgba(224,36,94,.12),transparent);padding-left:0;padding-right:0}
.sec>.in{padding:0 6vw}
.scroller{overflow-x:auto;overflow-y:hidden;position:relative;z-index:2;scrollbar-width:none;padding-bottom:10px}
.scroller::-webkit-scrollbar{display:none}
.scene{position:relative;height:470px;margin:0 auto}
.scene svg{position:absolute;left:0;top:0;pointer-events:none}
.bulb{animation:tw 2.4s ease-in-out infinite}
@keyframes tw{0%,100%{opacity:.35}50%{opacity:1}}
.pol{position:absolute;width:196px;height:262px;transform-origin:50% 0;animation:sway 4.6s ease-in-out infinite alternate;cursor:pointer;z-index:3;filter:drop-shadow(0 18px 20px rgba(0,0,0,.55))}
@keyframes sway{from{transform:rotate(var(--a))}to{transform:rotate(calc(var(--a) * -0.7))}}
.pol:hover{animation-play-state:paused;z-index:5}
.card{position:relative;width:100%;height:100%;transform-style:preserve-3d;transition:transform .85s cubic-bezier(.3,.8,.3,1)}
.pol.flip .card{transform:rotateY(180deg)}
.pol:hover .card{transform:scale(1.04)}
.pol.flip:hover .card{transform:rotateY(180deg) scale(1.04)}
.face{position:absolute;inset:0;backface-visibility:hidden;-webkit-backface-visibility:hidden;border-radius:4px;background:#fffaf5}
.front{padding:11px 11px 0}
.front .ph{width:100%;height:196px;border-radius:2px;overflow:hidden;background:#222;display:grid;place-items:center}
.front .ph img{width:100%;height:100%;object-fit:cover;display:block}
.front .lbl{font-family:var(--hand);font-size:25px;font-weight:600;letter-spacing:.01em;text-align:center;color:#4a2630;margin-top:8px;line-height:1.15}
.back{transform:rotateY(180deg);padding:20px 18px;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;
 background:repeating-linear-gradient(#fff6ef 0 27px,#f1d6d6 27px 28px);color:#5a2a3c}
.back .kicker{font-size:9px;letter-spacing:.22em;text-transform:uppercase;color:#b76a80;font-weight:700;margin-bottom:12px}
.back .t{font-family:var(--hand);font-size:19px;line-height:1.22;color:#5a2a3c}
.back .d{margin-top:14px;font-size:20px;color:#d8386a}
.pin{position:absolute;left:50%;top:-14px;transform:translateX(-50%);width:16px;height:40px;z-index:6;pointer-events:none}
.pin:before{content:"";position:absolute;inset:0;border-radius:4px;background:linear-gradient(90deg,#d9a46b,#f4cf9e,#c08850);box-shadow:0 2px 4px rgba(0,0,0,.5)}
.pin:after{content:"";position:absolute;left:5px;top:6px;width:3px;height:22px;background:rgba(0,0,0,.25);border-radius:2px}
.ph.empty{background:linear-gradient(135deg,#3a1223,#7a2447 55%,#e0245e);color:#ffd9e3;font-family:var(--hand);font-size:24px;text-align:center;line-height:1.1}
.swipe{display:none;text-align:center;color:var(--muted);font-size:13px;margin-top:6px;position:relative;z-index:2}
@media(max-width:900px){.swipe{display:block}}
"""
    js = f"""
var PH={esc(photos)};
(function(){{
 var sc=document.getElementById('scroller'),scene=document.getElementById('scene');
 var N=PH.length,PW=196,GAP=30;
 function build(){{
  scene.innerHTML='';
  var W=Math.max(sc.clientWidth,N*(PW+GAP)+GAP+40);scene.style.width=W+'px';
  var ropeY=118,sag=44,lightY=34,lsag=26;
  var svg='<svg width="'+W+'" height="260" viewBox="0 0 '+W+' 260">';
  svg+='<path d="M-10,'+ropeY+' Q'+(W/2)+','+(ropeY+2*sag)+' '+(W+10)+','+ropeY+'" fill="none" stroke="#caa57a" stroke-width="4" stroke-linecap="round"/>';
  svg+='<path d="M-10,'+ropeY+' Q'+(W/2)+','+(ropeY+2*sag)+' '+(W+10)+','+ropeY+'" fill="none" stroke="#6b4a2c" stroke-width="1.2" stroke-dasharray="3 6" opacity=".7"/>';
  svg+='<path d="M-10,'+lightY+' Q'+(W/2)+','+(lightY+2*lsag)+' '+(W+10)+','+lightY+'" fill="none" stroke="#2a1a1f" stroke-width="2"/>';
  var nb=Math.floor(W/46),cols=['#ffd27a','#ff7aa2','#ffe6b0','#ff9ec0'];
  for(var i=1;i<nb;i++){{var t=i/nb,x=W*t,y=lightY+4*lsag*t*(1-t)+3,c=cols[i%4];
   svg+='<g class="bulb" style="animation-delay:'+(i%6)*0.38+'s"><circle cx="'+x+'" cy="'+(y+8)+'" r="11" fill="'+c+'" opacity=".16"/><circle cx="'+x+'" cy="'+(y+7)+'" r="4.6" fill="'+c+'"/></g>'}}
  svg+='</svg>';scene.insertAdjacentHTML('beforeend',svg);
  PH.forEach(function(p,i){{
   var t=(i+.5)/N,cx=W*t,y=ropeY+4*sag*t*(1-t);
   var el=document.createElement('div');el.className='pol';
   el.style.left=(cx-PW/2)+'px';el.style.top=(y+4)+'px';
   var a=((i%2?1:-1)*(1.6+(i*37%25)/10));el.style.setProperty('--a',a+'deg');el.style.animationDelay=(-i*0.9)+'s';
   var ph=p.src?'<div class="ph"><img src="'+p.src+'"></div>':'<div class="ph empty">Your photo<br>goes here<br>📷</div>';
   el.innerHTML='<div class="pin"></div><div class="card"><div class="face front">'+ph+'<div class="lbl">'+p.label+'</div></div>'+
     '<div class="face back"><div class="kicker">A tiny story</div><div class="t">'+p.back+'</div><div class="d">✿</div></div></div>';
   el.addEventListener('click',function(){{el.classList.toggle('flip')}});
   scene.appendChild(el);
  }});
 }}
 build();var to;addEventListener('resize',function(){{clearTimeout(to);to=setTimeout(build,200)}});
}})();
"""
    return page(body, css, js, bg="#0a0608", nxt="#2b0d1b", min_h=780)


# ═══════════════════════════════════════════════════════════════════
# 4️⃣  FLOWER DELIVERY — a cartoon boy runs in from far away with flowers for Sneha
# ═══════════════════════════════════════════════════════════════════
def flower_html():
    body = """
<canvas id="bg" style="position:absolute;inset:0;width:100%;height:100%;z-index:1;pointer-events:none"></canvas>
<div class="in c">
  <div class="eyebrow" style="justify-content:center">A little surprise</div>
  <h2 class="title">Someone is on his way<br><em>with something for you</em></h2>
  <p class="sub" style="text-align:center;margin:0 auto">A little bouquet is on its way. Tap below to send it. 💐</p>

  <svg id="stage" viewBox="0 0 900 400" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="sk" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4a1630"/><stop offset=".65" stop-color="#9b2c52"/><stop offset="1" stop-color="#f08a6b"/></linearGradient>
      <linearGradient id="gr" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2c0e1b"/><stop offset="1" stop-color="#14070d"/></linearGradient>
      <radialGradient id="skinTone" cx=".34" cy=".24" r=".8"><stop offset="0" stop-color="#ffe0c5"/><stop offset=".7" stop-color="#f1c19b"/><stop offset="1" stop-color="#c98d72"/></radialGradient>
      <linearGradient id="dressTone" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#c91d55"/><stop offset=".48" stop-color="#f04a7c"/><stop offset="1" stop-color="#a91549"/></linearGradient>
      <linearGradient id="shirtTone" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#294d88"/><stop offset=".5" stop-color="#568bd0"/><stop offset="1" stop-color="#294d88"/></linearGradient>
      <linearGradient id="runnerShirt" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6e9edb"/><stop offset=".48" stop-color="#3f6fb5"/><stop offset="1" stop-color="#213d70"/></linearGradient>
      <linearGradient id="runnerPants" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#182238"/><stop offset=".52" stop-color="#35425e"/><stop offset="1" stop-color="#111a2a"/></linearGradient>
      <linearGradient id="shoeTone" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#45404a"/><stop offset="1" stop-color="#14131a"/></linearGradient>
      <radialGradient id="faceTone" cx=".34" cy=".22" r=".82"><stop offset="0" stop-color="#ffe4cf"/><stop offset=".62" stop-color="#f1c19f"/><stop offset="1" stop-color="#bd8069"/></radialGradient>
      <linearGradient id="hairTone" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#493027"/><stop offset=".45" stop-color="#211713"/><stop offset="1" stop-color="#0d0a0b"/></linearGradient>
      <linearGradient id="girlDressTone" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#a91448"/><stop offset=".5" stop-color="#ef5683"/><stop offset="1" stop-color="#9b1645"/></linearGradient>
      <radialGradient id="sn" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#fff0c4"/><stop offset="1" stop-color="#ffd18a" stop-opacity="0"/></radialGradient>
    </defs>
    <rect width="900" height="400" rx="28" fill="url(#sk)"/>
    <circle cx="450" cy="300" r="150" fill="url(#sn)" opacity=".7"/>
    <circle cx="450" cy="300" r="46" fill="#fff0c4" opacity=".95"/>
    <path d="M0,300 Q200,280 450,296 T900,292 L900,400 L0,400Z" fill="#3a1226" opacity=".55"/>
    <path d="M0,330 Q450,310 900,332 L900,400 L0,400Z" fill="url(#gr)"/>
    <g id="fx"></g>

    <!-- ===== recipient: softly shaded, more natural proportions ===== -->
    <g id="girl" style="transform:translate(740px,352px)">
      <ellipse cx="0" cy="3" rx="38" ry="6" fill="#000" opacity=".28"/>
      <path d="M-27,-169 Q-37,-140 -31,-105 Q-29,-78 -19,-66 L19,-66 Q31,-83 31,-119 Q36,-158 24,-177Z" fill="url(#hairTone)"/>
      <path d="M-12,-59 L-10,-4 Q-8,2 0,2 Q8,2 10,-4 L12,-59Z" fill="url(#faceTone)"/>
      <path d="M-14,-132 L14,-132 L36,-48 Q0,-39 -36,-48Z" fill="url(#girlDressTone)"/>
      <path d="M-14,-132 L14,-132 L18,-117 L-18,-117Z" fill="#ff9ab5" opacity=".75"/>
      <path d="M-25,-121 Q-17,-105 -19,-82 M25,-121 Q17,-105 19,-82" stroke="#ffb5c7" stroke-width="2" opacity=".28" fill="none"/>
      <path d="M-14,-46 Q-4,-42 0,-44 Q8,-42 14,-46" stroke="#ffb5c7" stroke-width="1.7" opacity=".55" fill="none"/>
      <path d="M-17,-57 L-15,-5 Q-14,1 -6,1 L-7,-57Z" fill="url(#faceTone)"/>
      <path d="M5,-57 L7,-5 Q8,1 16,1 L17,-57Z" fill="url(#faceTone)"/>
      <ellipse cx="-10" cy="1" rx="12" ry="4.5" fill="#7c3144"/><ellipse cx="10" cy="1" rx="12" ry="4.5" fill="#7c3144"/>
      <g id="armsDown">
        <path d="M-27,-123 Q-39,-104 -34,-77" stroke="url(#faceTone)" stroke-width="10" stroke-linecap="round" fill="none"/>
        <path d="M27,-123 Q39,-104 34,-77" stroke="url(#faceTone)" stroke-width="10" stroke-linecap="round" fill="none"/>
        <ellipse cx="-34" cy="-72" rx="5.5" ry="7" fill="url(#faceTone)"/><ellipse cx="34" cy="-72" rx="5.5" ry="7" fill="url(#faceTone)"/>
      </g>
      <g id="armsUp" style="display:none">
        <path d="M-27,-123 Q-42,-106 -27,-91" stroke="url(#faceTone)" stroke-width="10" stroke-linecap="round" fill="none"/>
        <path d="M27,-123 Q25,-92 -11,-89" stroke="url(#faceTone)" stroke-width="10" stroke-linecap="round" fill="none"/>
        <ellipse cx="-25" cy="-88" rx="5.5" ry="7" fill="url(#faceTone)"/><ellipse cx="-12" cy="-89" rx="5.5" ry="7" fill="url(#faceTone)"/>
      </g>
      <path d="M-12,-185 Q-1,-198 16,-184 Q31,-171 27,-151 Q26,-137 16,-130 L-19,-130 Q-31,-145 -28,-164 Q-26,-179 -12,-185Z" fill="url(#faceTone)"/>
      <path d="M-29,-165 Q-34,-197 -8,-202 Q18,-208 30,-184 Q35,-169 25,-153 Q21,-174 5,-179 Q-10,-181 -21,-164 Q-24,-153 -29,-145Z" fill="url(#hairTone)"/>
      <path d="M-23,-166 Q-28,-128 -15,-115 M23,-170 Q31,-143 20,-119" stroke="#6b4234" stroke-width="5" stroke-linecap="round" fill="none" opacity=".62"/>
      <path d="M-17,-163 Q-11,-167 -6,-163 M7,-163 Q13,-167 18,-163" stroke="#4a2c25" stroke-width="2.2" fill="none" stroke-linecap="round"/>
      <path d="M-18,-169 Q-11,-173 -5,-169 M6,-169 Q13,-173 19,-169" stroke="#34211e" stroke-width="1.7" fill="none" stroke-linecap="round"/>
      <path d="M-21,-154 Q-15,-150 -10,-152 M10,-152 Q16,-150 21,-154" stroke="#fff0e4" stroke-width="1.4" fill="none" opacity=".55"/>
      <path d="M-5,-151 Q0,-146 5,-151" stroke="#9f5a50" stroke-width="1.8" fill="none" stroke-linecap="round"/>
      <g id="gEyesN"><ellipse cx="-11" cy="-157" rx="3.1" ry="4.1" fill="#241713"/><ellipse cx="11" cy="-157" rx="3.1" ry="4.1" fill="#241713"/><circle cx="-10" cy="-159" r="1" fill="#fff"/><circle cx="12" cy="-159" r="1" fill="#fff"/><path d="M-4,-148 Q0,-145 4,-148" stroke="#a96b5b" stroke-width="1.6" fill="none"/></g>
      <g id="gEyesH" style="display:none"><path d="M-17,-158 q6,-8 12,0 q-6,8 -12,0 M5,-158 q6,-8 12,0 q-6,8 -12,0" fill="#ff3b6b"/><path d="M-8,-146 Q0,-139 8,-146" stroke="#a94b5d" stroke-width="2.3" fill="none" stroke-linecap="round"/></g>
      <path d="M-3,-151 Q0,-148 3,-151" stroke="#bf826b" stroke-width="1.4" fill="none"/>
      <circle id="blL" cx="-20" cy="-148" r="5.5" fill="#ed8b91" opacity="0"/><circle id="blR" cx="20" cy="-148" r="5.5" fill="#ed8b91" opacity="0"/>
    </g>

    <!-- ===== flower runner: proportionate 2.5D storybook character ===== -->
    <g id="runner" style="transform-origin:0 0;transform:translate(40px,302px) scale(.3)">
      <g class="lean">
        <ellipse cx="0" cy="3" rx="31" ry="6" fill="#000" opacity=".3"/>
        <g class="bob">
          <g class="lL">
            <path d="M-15,-66 Q-15,-43 -14,-7 Q-12,1 -5,1 L-1,-4 L-3,-66Z" fill="url(#runnerPants)"/>
            <path d="M-14,-7 Q-22,-2 -21,3 Q-19,7 -3,6 Q3,5 1,0 L-4,-4Z" fill="url(#shoeTone)"/>
            <path d="M-13,-60 L-5,-12" stroke="#8e9bb0" stroke-width="1.1" opacity=".28"/>
          </g>
          <g class="lR">
            <path d="M3,-66 L15,-66 Q16,-40 17,-7 Q15,1 8,1 L4,-4Z" fill="url(#runnerPants)"/>
            <path d="M7,-7 Q1,-2 3,3 Q5,7 21,6 Q27,5 23,0 L16,-4Z" fill="url(#shoeTone)"/>
            <path d="M8,-60 L15,-12" stroke="#8e9bb0" stroke-width="1.1" opacity=".25"/>
          </g>
          <g class="aL">
            <path d="M-27,-126 Q-39,-113 -42,-88 L-37,-81 Q-30,-80 -26,-91 L-17,-116Z" fill="url(#runnerShirt)"/>
            <path d="M-39,-87 Q-44,-78 -38,-72 Q-33,-68 -28,-76 L-29,-84Z" fill="url(#faceTone)"/>
            <path d="M-38,-83 l5,2 M-36,-78 l5,1" stroke="#b77c67" stroke-width="1" opacity=".55"/>
          </g>
          <path d="M-25,-137 Q-5,-143 22,-135 L29,-62 Q4,-53 -27,-62Z" fill="url(#runnerShirt)"/>
          <path d="M-8,-136 L0,-122 L9,-136" fill="#e6edf7" opacity=".9"/>
          <path d="M0,-122 L2,-64" stroke="#18365f" stroke-width="1.5" opacity=".5"/>
          <circle cx="2" cy="-111" r="1.8" fill="#f6dba5"/><circle cx="2" cy="-96" r="1.8" fill="#f6dba5"/>
          <path d="M-20,-128 Q-4,-119 20,-128" stroke="#a8c7ed" stroke-width="1.4" fill="none" opacity=".42"/>
          <path d="M-18,-112 Q-6,-104 18,-110 M-16,-89 Q-4,-84 18,-90" stroke="#a8c7ed" stroke-width="1.1" fill="none" opacity=".24"/>
          <path d="M-5,-145 L5,-145 L7,-132 L-7,-132Z" fill="url(#faceTone)"/>
          <g id="runnerHead">
            <path d="M-23,-176 Q-25,-196 -7,-202 Q12,-207 24,-191 Q29,-178 24,-158 Q20,-145 4,-143 Q-16,-144 -22,-160Z" fill="url(#faceTone)"/>
            <ellipse cx="-23" cy="-174" rx="4.2" ry="7" fill="#d79a7d"/><ellipse cx="23" cy="-174" rx="4.2" ry="7" fill="#c88a70"/>
            <path d="M-25,-177 Q-28,-199 -9,-207 Q10,-213 24,-196 Q29,-187 25,-174 Q15,-187 2,-189 Q-12,-191 -25,-177Z" fill="url(#hairTone)"/>
            <path d="M-19,-190 Q-6,-205 9,-199" stroke="#8d6550" stroke-width="2.2" fill="none" opacity=".62" stroke-linecap="round"/>
            <path d="M-22,-184 Q-12,-198 -1,-199 M-15,-181 Q-4,-193 7,-194 M4,-186 Q15,-194 22,-184" stroke="#6e4938" stroke-width="1.3" fill="none" opacity=".48" stroke-linecap="round"/>
            <path d="M-17,-174 Q-11,-178 -6,-174 M7,-174 Q13,-178 18,-174" stroke="#4b3027" stroke-width="2" fill="none" stroke-linecap="round"/>
            <ellipse cx="-11" cy="-171" rx="2.3" ry="3.1" fill="#241713"/><ellipse cx="12" cy="-171" rx="2.3" ry="3.1" fill="#241713"/>
            <circle cx="-10" cy="-172" r=".9" fill="#fff"/><circle cx="13" cy="-172" r=".9" fill="#fff"/>
            <path d="M0,-168 Q-3,-161 1,-160" stroke="#be856e" stroke-width="1.4" fill="none" stroke-linecap="round"/>
            <path d="M-7,-153 Q1,-147 9,-153" stroke="#9a4d46" stroke-width="2.2" fill="none" stroke-linecap="round"/>
            <path d="M-3,-152 Q1,-149 5,-152" stroke="#f4c1b0" stroke-width=".9" fill="none" opacity=".9"/>
            <ellipse cx="-17" cy="-159" rx="4" ry="2.5" fill="#e78e86" opacity=".28"/><ellipse cx="18" cy="-159" rx="4" ry="2.5" fill="#e78e86" opacity=".28"/>
          </g>
          <g class="aR" style="transform:rotate(-72deg);transform-origin:24px -119px">
            <path d="M20,-128 Q35,-120 40,-96 L36,-83 Q30,-78 25,-88 L13,-115Z" fill="url(#runnerShirt)"/>
            <path d="M35,-91 Q43,-82 39,-74 Q35,-69 29,-76 L29,-84Z" fill="url(#faceTone)"/>
          </g>
          <g id="bq" transform="translate(80,-100)">
            <path d="M-5,-4 L-10,-26 M5,-4 L10,-26" stroke="#3f9b5b" stroke-width="3"/>
            <path d="M-17,-18 L17,-18 L6,26 L-6,26Z" fill="#fff3e0"/><path d="M-17,-18 L17,-18 L14,-8 L-14,-8Z" fill="#ffd9e3"/><rect x="-7" y="-4" width="14" height="5" rx="2" fill="url(#girlDressTone)"/>
            <path d="M-18,-28 q-12,-6 -6,-16 q10,4 6,16z M18,-28 q12,-6 6,-16 q-10,4 -6,16z" fill="#2f8a50"/>
            <g><circle cx="-12" cy="-34" r="10" fill="#ff5c8a"/><circle cx="-12" cy="-34" r="3.5" fill="#ffe08a"/>
              <circle cx="11" cy="-36" r="10" fill="#ffc2d1"/><circle cx="11" cy="-36" r="3.5" fill="#ffe08a"/>
              <circle cx="0" cy="-46" r="11" fill="#e64b73"/><circle cx="0" cy="-46" r="3.8" fill="#ffe08a"/>
              <circle cx="-2" cy="-28" r="9" fill="#fff0f3"/><circle cx="-2" cy="-28" r="3.2" fill="#ffd36e"/></g>
          </g>
        </g>
      </g>
    </g>
    <text id="name" x="740" y="140" text-anchor="middle" font-size="22" fill="#ffe6ee" style="opacity:0;font-family:Caveat,cursive;font-size:30px">for __NAME__ 💐</text>
  </svg>

  <div class="cap" id="cap">&nbsp;</div>
  <button class="btn" id="go" onclick="deliver()"><span id="gl">Send the flowers</span> <i>💐</i></button>
</div>
"""
    body = body.replace("__NAME__", HER_NAME or "you")
    css = """
.sec{background-image:radial-gradient(700px 420px at 50% 55%,rgba(224,36,94,.22),transparent),radial-gradient(500px 300px at 10% 0%,rgba(255,170,190,.08),transparent);text-align:center;padding-top:100px}
.c{display:flex;flex-direction:column;align-items:center;text-align:center}\n#go{position:relative;z-index:5;margin:8px auto 18px;min-height:54px;padding:10px 12px 10px 26px;font-size:16px;box-shadow:0 12px 34px rgba(224,36,94,.42),0 0 0 1px rgba(255,255,255,.14) inset}\n#go i{width:40px;height:40px;font-size:20px}
#stage{width:min(820px,100%);height:auto;margin:18px 0 4px;filter:drop-shadow(0 30px 40px rgba(0,0,0,.5))}
.cap{min-height:36px;font-family:var(--hand);font-size:30px;color:var(--gold);margin:2px 0 10px;opacity:0;transition:opacity .8s}
.cap.show{opacity:1}
.lean{transform:rotate(2deg);transform-origin:0 0}
.running .bob{animation:bob .22s ease-in-out infinite alternate}
.running .lL{animation:leg .38s ease-in-out infinite alternate;transform-origin:-8px -62px}
.running .lR{animation:leg .38s ease-in-out infinite alternate-reverse;transform-origin:10px -62px}
.running .aL{animation:armRun .38s ease-in-out infinite alternate-reverse;transform-origin:-25px -120px}
.running .aR{animation:armRun .38s ease-in-out infinite alternate;transform-origin:24px -119px}
@keyframes leg{from{transform:rotate(27deg)}to{transform:rotate(-27deg)}}
@keyframes armRun{from{transform:rotate(23deg)}to{transform:rotate(-23deg)}}
@keyframes bob{from{transform:translateY(1px)}to{transform:translateY(-4px)}}
@media(max-width:600px){.cap{font-size:25px}}
"""
    js = """
(function(){var c=document.getElementById('bg'),x=c.getContext('2d'),W,H,P=[];
 function rs(){W=c.width=c.offsetWidth;H=c.height=c.offsetHeight}rs();addEventListener('resize',rs);
 for(var i=0;i<22;i++)P.push({x:Math.random(),y:Math.random(),s:Math.random()*.5+.2,r:Math.random()*5+4,a:Math.random()*6.28});
 (function f(t){x.clearRect(0,0,W,H);P.forEach(function(p){p.y+=p.s*.0009*16;p.a+=.01;if(p.y>1.05){p.y=-.05;p.x=Math.random()}
  x.save();x.translate(p.x*W+Math.sin(t/1500+p.a)*18,p.y*H);x.rotate(p.a);x.fillStyle='rgba(255,107,146,.4)';
  x.beginPath();x.ellipse(0,0,p.r,p.r*.62,0,0,6.28);x.fill();x.restore()});requestAnimationFrame(f)})(0)})();

var NS='http://www.w3.org/2000/svg';
var stage=document.getElementById('stage'),runner=document.getElementById('runner'),bq=document.getElementById('bq'),girl=document.getElementById('girl'),
 fx=document.getElementById('fx'),cap=document.getElementById('cap'),nm=document.getElementById('name'),busy=false,anims=[],timer=null;
var START='translate(40px,302px) scale(.3)',END='translate(560px,352px) scale(1)';
function A(el,k,o){var a=el.animate(k,o);anims.push(a);return a}
function reset(){
 anims.forEach(function(a){try{a.cancel()}catch(e){}});anims=[];clearInterval(timer);
 if(bq.parentNode!==runner.querySelector('.bob')){runner.querySelector('.bob').appendChild(bq)}
 bq.setAttribute('transform','translate(80,-100)');bq.style.transform='';
 runner.classList.remove('running');runner.style.transform=START;runner.style.opacity=1;
 girl.style.transform='translate(740px,352px)';
 document.getElementById('gEyesN').style.display='';document.getElementById('gEyesH').style.display='none';
 document.getElementById('armsDown').style.display='';document.getElementById('armsUp').style.display='none';
 document.getElementById('blL').style.opacity=0;document.getElementById('blR').style.opacity=0;
 fx.innerHTML='';cap.classList.remove('show');nm.style.opacity=0}
function puff(){
 var m=new DOMMatrix(getComputedStyle(runner).transform);var d=document.createElementNS(NS,'circle');
 d.setAttribute('cx',m.e-14*m.a);d.setAttribute('cy',m.f-4*m.a);d.setAttribute('r',7*m.a+2);d.setAttribute('fill','#e9c9b4');d.setAttribute('opacity','.5');fx.appendChild(d);
 A(d,[{transform:'translate(0,0) scale(1)',opacity:.5},{transform:'translate(-22px,-12px) scale(2)',opacity:0}],{duration:650,fill:'forwards'})}
function icon(x,y,txt,delay,dist){
 var t=document.createElementNS(NS,'text');t.textContent=txt;t.setAttribute('x',x);t.setAttribute('y',y);t.setAttribute('font-size',16+Math.random()*16);fx.appendChild(t);
 A(t,[{transform:'translate(0,0)',opacity:1},{transform:'translate('+(Math.random()*90-45)+'px,'+(-(dist||110)-Math.random()*60)+'px)',opacity:0}],{duration:1500+Math.random()*700,delay:delay,fill:'forwards'})}
function shower(){
 var E=['🌸','🌷','🌺','💮','🌹','✨'];
 for(var i=0;i<34;i++){var t=document.createElementNS(NS,'text');t.textContent=E[i%E.length];t.setAttribute('x',Math.random()*880+10);t.setAttribute('y',-10);t.setAttribute('font-size',18+Math.random()*18);fx.appendChild(t);
  A(t,[{transform:'translate(0,0) rotate(0deg)',opacity:1},{transform:'translate('+(Math.random()*80-40)+'px,420px) rotate('+(Math.random()*500-250)+'deg)',opacity:.9}],{duration:2600+Math.random()*1800,delay:Math.random()*1800,fill:'forwards'})}}
function deliver(){
 if(busy)return;busy=true;reset();
 var btn=document.getElementById('go');btn.style.opacity=.55;
 runner.classList.add('running');timer=setInterval(puff,230);
 var run=A(runner,[{transform:START},{transform:END}],{duration:4600,easing:'cubic-bezier(.3,.1,.55,1)',fill:'forwards'});
 run.onfinish=arrive}
function arrive(){
 clearInterval(timer);runner.classList.remove('running');
 // hand the bouquet over: move it out of the boy's group into the scene
 var gx=560+80,gy=352-100;
 stage.insertBefore(bq,document.getElementById('runner').nextSibling);
 bq.setAttribute('transform','');bq.style.transform='translate('+gx+'px,'+gy+'px)';
 var fl=A(bq,[{transform:'translate('+gx+'px,'+gy+'px)'},{transform:'translate('+(gx+30)+'px,'+(gy-34)+'px)',offset:.5},{transform:'translate(708px,262px)'}],{duration:800,easing:'ease-in-out',fill:'forwards'});
 fl.onfinish=function(){
  document.getElementById('gEyesN').style.display='none';document.getElementById('gEyesH').style.display='';
  document.getElementById('armsDown').style.display='none';document.getElementById('armsUp').style.display='';
  document.getElementById('blL').style.opacity=.75;document.getElementById('blR').style.opacity=.75;
  A(girl,[{transform:'translate(740px,352px)'},{transform:'translate(740px,330px)'},{transform:'translate(740px,352px)'},{transform:'translate(740px,336px)'},{transform:'translate(740px,352px)'}],{duration:900});
  A(bq,[{transform:'translate(708px,262px)'},{transform:'translate(708px,240px)'},{transform:'translate(708px,262px)'},{transform:'translate(708px,246px)'},{transform:'translate(708px,262px)'}],{duration:900,fill:'forwards'});
  A(runner,[{transform:END},{transform:'translate(560px,326px) scale(1)'},{transform:END},{transform:'translate(560px,336px) scale(1)'},{transform:END}],{duration:900,fill:'forwards'});
  for(var i=0;i<12;i++){icon(730+Math.random()*30-15,200,['💘','♥','✨','💖'][i%4],i*110,120)}
  for(var j=0;j<6;j++){icon(570+Math.random()*30-15,210,['♥','✨'][j%2],j*160,100)}
  nm.style.transition='opacity 1s';nm.style.opacity=1;
  setTimeout(shower,500);
  cap.innerHTML='Flowers for __NAME__ 💐 — just because it\\'s you.';cap.classList.add('show');
  document.getElementById('gl').textContent='Send them again';btn.style.opacity=1;busy=false;
 }}
var btn=document.getElementById('go');
""".replace("__NAME__", HER_NAME or "you")
    return page(body, css, js, bg="#2b0d1b", nxt="#0f0709", min_h=760)


# ═══════════════════════════════════════════════════════════════════
# 5️⃣  CUPID — the arrow hits, the boy falls 😵‍💫
# ═══════════════════════════════════════════════════════════════════
def cupid_html():
    body = """
<div class="in c">
  <div class="eyebrow" style="justify-content:center">A little story</div>
  <h2 class="title">Cupid's <em>aim</em></h2>
  <p class="sub" style="text-align:center;margin:0 auto">Pull the bow and see what happens.</p>

  <svg id="stage" viewBox="0 0 900 400" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="gd" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3b1226"/><stop offset="1" stop-color="#14070d"/></linearGradient>
      <radialGradient id="mn" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#fff3d1"/><stop offset="1" stop-color="#ffd596" stop-opacity="0"/></radialGradient>
      <radialGradient id="cSkin" cx=".32" cy=".2" r=".85"><stop offset="0" stop-color="#ffe8d5"/><stop offset=".62" stop-color="#f2c5a5"/><stop offset="1" stop-color="#b87563"/></radialGradient>
      <linearGradient id="cHair" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#d9ad62"/><stop offset=".45" stop-color="#a87838"/><stop offset="1" stop-color="#684321"/></linearGradient>
      <linearGradient id="cTunic" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff1d6"/><stop offset=".52" stop-color="#eacb9d"/><stop offset="1" stop-color="#b98b62"/></linearGradient>
      <linearGradient id="cBlue" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6d9bdd"/><stop offset=".5" stop-color="#3f6fb5"/><stop offset="1" stop-color="#203d70"/></linearGradient>
      <linearGradient id="cPants" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#172238"/><stop offset=".5" stop-color="#39445c"/><stop offset="1" stop-color="#101827"/></linearGradient>
      <linearGradient id="cArrowWood" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff0c8"/><stop offset="1" stop-color="#c58c4c"/></linearGradient>
    </defs>
    <rect width="900" height="400" rx="28" fill="url(#gd)"/>
    <circle cx="780" cy="70" r="70" fill="url(#mn)" opacity=".55"/><circle cx="780" cy="70" r="26" fill="#fff3d1"/>
    <g fill="#fff" id="stars"></g>
    <path d="M0,352 Q450,330 900,352 L900,400 L0,400Z" fill="#1d0b13"/>
    <!-- Cupid: a softly shaded, more natural storybook angel -->
    <g id="cupid" style="transform-origin:140px 160px">
      <g class="hover">
        <g id="wingL" class="angel-wing">
          <path d="M119,145 Q76,123 72,151 Q73,174 111,184 Q124,177 128,163Z" fill="#fff8f3" stroke="#e7ced0" stroke-width="1.5"/>
          <path d="M113,151 Q86,134 82,153 Q88,168 115,174 M118,160 Q98,151 94,165" fill="none" stroke="#dfc2c8" stroke-width="2" opacity=".8"/>
          <path d="M111,167 Q95,161 91,171" fill="none" stroke="#fff" stroke-width="2" opacity=".8"/>
          <path d="M119,151 Q98,139 87,148 M122,158 Q101,151 94,160 M119,167 Q104,164 101,173" fill="none" stroke="#d6b9c0" stroke-width="1.2" opacity=".8"/>
        </g>
        <g id="wingR" class="angel-wing">
          <path d="M157,145 Q199,121 207,149 Q211,170 170,184 Q157,176 153,162Z" fill="#fff8f3" stroke="#e7ced0" stroke-width="1.5"/>
          <path d="M164,151 Q191,133 198,151 Q191,168 164,174 M160,161 Q180,150 185,165" fill="none" stroke="#dfc2c8" stroke-width="2" opacity=".8"/>
          <path d="M169,168 Q187,159 191,170" fill="none" stroke="#fff" stroke-width="2" opacity=".8"/>
          <path d="M159,151 Q181,138 198,148 M157,159 Q181,150 200,160 M163,168 Q181,163 190,174" fill="none" stroke="#d6b9c0" stroke-width="1.2" opacity=".8"/>
        </g>
        <path d="M124,141 Q112,153 117,177 L128,197 Q142,204 157,196 L166,176 Q168,153 154,141Z" fill="url(#cTunic)" stroke="#c59b70" stroke-width="1.2"/>
        <path d="M128,147 Q141,156 154,147" stroke="#fff8e8" stroke-width="3" fill="none" opacity=".8"/>
        <path d="M141,151 L141,194" stroke="#b78b62" stroke-width="1.5" opacity=".55"/>
        <circle cx="141" cy="171" r="2" fill="#d0a15d"/><circle cx="141" cy="183" r="2" fill="#d0a15d"/>
        <path d="M129,192 L128,221 Q134,226 139,222 L141,194Z" fill="#f0d8b6"/>
        <path d="M145,194 L146,222 Q152,226 157,220 L153,192Z" fill="#dfc098"/>
        <path d="M127,219 Q120,230 130,232 L141,230 L139,222Z" fill="#9f6c4d"/><path d="M147,221 Q146,232 158,231 L165,227 L157,218Z" fill="#9f6c4d"/>
        <path d="M117,151 Q105,161 111,179 L120,184 Q125,180 123,171 L130,157Z" fill="url(#cSkin)" stroke="#c88e75" stroke-width="1"/>
        <path d="M158,153 Q170,159 177,170 L173,179 Q167,182 163,173 L151,163Z" fill="url(#cSkin)" stroke="#c88e75" stroke-width="1"/>
        <path d="M119,110 Q115,89 136,84 Q159,81 166,103 Q171,126 157,143 Q143,155 126,140 Q116,130 119,110Z" fill="url(#cSkin)"/>
        <path d="M117,111 Q112,88 132,79 Q153,73 167,91 Q174,102 165,116 Q156,99 143,98 Q129,98 119,116Z" fill="url(#cHair)"/>
        <path d="M120,104 Q131,85 148,88" stroke="#f2d18c" stroke-width="2.4" fill="none" stroke-linecap="round" opacity=".75"/>
        <path d="M121,111 Q131,94 143,94 M147,91 Q159,96 163,108" stroke="#8f6337" stroke-width="1.2" fill="none" opacity=".6"/>
        <path d="M125,116 Q131,112 136,116 M148,115 Q154,111 159,115" stroke="#563a2b" stroke-width="2" fill="none" stroke-linecap="round"/>
        <ellipse cx="131" cy="120" rx="2.5" ry="3.4" fill="#281915"/><ellipse cx="153" cy="119" rx="2.5" ry="3.4" fill="#281915"/>
        <circle cx="132" cy="119" r=".9" fill="#fff"/><circle cx="154" cy="118" r=".9" fill="#fff"/>
        <path d="M140,121 Q137,128 141,129" stroke="#bd866e" stroke-width="1.3" fill="none"/>
        <path d="M134,135 Q142,140 150,134" stroke="#a94d5b" stroke-width="2.3" fill="none" stroke-linecap="round"/>
        <ellipse cx="124" cy="130" rx="4.5" ry="2.8" fill="#ee9998" opacity=".38"/><ellipse cx="159" cy="129" rx="4.5" ry="2.8" fill="#ee9998" opacity=".38"/>
        <path d="M180,98 Q238,168 180,238" stroke="#b9823e" stroke-width="7" fill="none" stroke-linecap="round"/>
        <path d="M180,98 Q238,168 180,238" stroke="#f4d49a" stroke-width="3" fill="none" stroke-linecap="round"/>
        <g id="bow"><path d="M180,98 Q238,168 180,238" stroke="#e2b46b" stroke-width="2" fill="none" stroke-linecap="round" opacity=".01"/>
          <path id="str" d="M180,98 L180,238" stroke="#fff1d2" stroke-width="1.7" fill="none"/></g>
        <path d="M164,166 Q175,166 184,168" stroke="url(#cSkin)" stroke-width="8" stroke-linecap="round" fill="none"/>
        <ellipse cx="184" cy="168" rx="5" ry="4" fill="url(#cSkin)"/>
      </g>
    </g>
    <!-- Recipient of Cupid's arrow: natural proportions and shaded clothing -->
    <g id="boy" style="transform-origin:600px 352px">
      <g transform="translate(600,352)">
        <path d="M-17,-66 L-16,-5 Q-14,2 -6,1 L-2,-5 L-3,-66Z" fill="url(#cPants)"/>
        <path d="M3,-66 L16,-66 L18,-6 Q16,1 8,1 L4,-4Z" fill="url(#cPants)"/>
        <path d="M-16,-4 Q-25,1 -21,7 L-2,7 Q3,5 0,0 L-5,-5Z" fill="#292630"/>
        <path d="M7,-4 Q0,1 4,7 L23,7 Q28,4 23,0 L16,-5Z" fill="#292630"/>
        <path d="M-12,-59 L-5,-12 M10,-59 L15,-12" stroke="#8994aa" stroke-width="1.4" opacity=".28"/>
        <path d="M-28,-137 Q0,-146 28,-137 L31,-60 Q0,-53 -31,-60Z" fill="url(#cBlue)" stroke="#244574" stroke-width="1.2"/>
        <path d="M-22,-126 Q-12,-110 -16,-83 M22,-124 Q12,-105 16,-81" stroke="#a9c5ec" stroke-width="1.1" opacity=".24" fill="none"/>
        <path d="M-19,-71 Q0,-65 20,-71" stroke="#122d54" stroke-width="1.2" opacity=".45" fill="none"/>
        <path d="M-10,-137 L0,-124 L10,-137" fill="#dce8f8"/>
        <path d="M0,-124 L1,-61" stroke="#274b7b" stroke-width="1.3" opacity=".55"/>
        <path d="M-21,-128 Q-12,-116 -14,-93 M22,-128 Q14,-108 17,-88" stroke="#9ab9e5" stroke-width="1.6" opacity=".32" fill="none"/>
        <circle cx="1" cy="-109" r="2" fill="#f6dba5"/><circle cx="1" cy="-95" r="2" fill="#f6dba5"/>
        <path d="M-28,-127 Q-44,-117 -45,-91 L-40,-82 Q-34,-80 -30,-90 L-17,-115Z" fill="url(#cBlue)"/>
        <path d="M28,-127 Q44,-117 45,-91 L40,-82 Q34,-80 30,-90 L17,-115Z" fill="url(#cBlue)"/>
        <path d="M-43,-88 Q-48,-79 -40,-73 Q-34,-69 -30,-78 L-33,-86Z" fill="url(#cSkin)"/>
        <path d="M43,-88 Q48,-79 40,-73 Q34,-69 30,-78 L33,-86Z" fill="url(#cSkin)"/>
        <path d="M-6,-147 L6,-147 L8,-132 L-8,-132Z" fill="url(#cSkin)"/>
        <path d="M-23,-179 Q-25,-197 -9,-207 Q12,-212 24,-193 Q29,-177 22,-158 Q16,-145 0,-144 Q-18,-146 -23,-162Z" fill="url(#cSkin)"/>
        <ellipse cx="-23" cy="-178" rx="4" ry="6.5" fill="#d99b7f"/><ellipse cx="23" cy="-178" rx="4" ry="6.5" fill="#c98770"/>
        <path d="M-25,-177 Q-29,-203 -8,-211 Q13,-216 26,-196 Q30,-185 24,-174 Q13,-190 0,-191 Q-13,-191 -25,-177Z" fill="url(#cHair)"/>
        <path d="M-20,-191 Q-6,-205 11,-199" stroke="#78513c" stroke-width="2.5" fill="none" opacity=".65" stroke-linecap="round"/>
        <path d="M-23,-187 Q-12,-203 -1,-204 M2,-202 Q14,-205 22,-189" stroke="#674630" stroke-width="1.2" fill="none" opacity=".62"/>
        <path d="M-17,-177 Q-11,-181 -6,-177 M7,-177 Q13,-181 18,-177" stroke="#503329" stroke-width="2.2" fill="none" stroke-linecap="round"/>
        <g id="eyesN"><ellipse cx="-11" cy="-173" rx="2.7" ry="3.8" fill="#211613"/><ellipse cx="11" cy="-173" rx="2.7" ry="3.8" fill="#211613"/><circle cx="-10" cy="-174" r=".9" fill="#fff"/><circle cx="12" cy="-174" r=".9" fill="#fff"/>
          <path id="mouthN" d="M-8,-158 Q0,-152 8,-158" stroke="#9c534b" stroke-width="2.3" fill="none" stroke-linecap="round"/></g>
        <g id="eyesH" style="display:none"><path d="M-19,-174 q8,-10 16,0 q-8,10 -16,0 M3,-174 q8,-10 16,0 q-8,10 -16,0" fill="#ff3b6b"/>
          <ellipse cx="0" cy="-153" rx="6" ry="4" fill="#a24a3a"/></g>
        <path d="M-2,-167 Q-4,-161 0,-161" stroke="#c58c72" stroke-width="1.4" fill="none"/>
        <ellipse cx="-18" cy="-160" rx="4.5" ry="2.7" fill="#e88f8b" opacity=".3"/><ellipse cx="18" cy="-160" rx="4.5" ry="2.7" fill="#e88f8b" opacity=".3"/>
      </g>
    </g>
    <!-- arrow -->
    <g id="arrow" style="transform-origin:0 0;opacity:0">
      <line x1="-92" y1="0" x2="-4" y2="0" stroke="url(#cArrowWood)" stroke-width="3.5" stroke-linecap="round"/>
      <line x1="-87" y1="-1" x2="-8" y2="-1" stroke="#fff6df" stroke-width=".8" opacity=".75"/>
      <path d="M0,0 L-15,-7 L-10,0 L-15,7Z" fill="#b8c7d8" stroke="#71849b" stroke-width=".8"/>
      <path d="M-92,0 Q-106,-12 -111,-9 Q-107,0 -111,9 Q-103,10 -92,0Z" fill="#e98ba5" stroke="#bd5878" stroke-width=".8"/><path d="M-80,0 Q-91,-10 -97,-8 Q-93,0 -97,8 Q-88,9 -80,0Z" fill="#fff0e7" stroke="#d6a8a2" stroke-width=".7"/>
    </g>
    <g id="fx"></g>
    <text id="dizzy" x="0" y="0" text-anchor="middle" font-size="26" style="opacity:0">💫 ⭐ 💫</text>
  </svg>

  <div class="cap" id="cap">&nbsp;</div>
  <button class="btn" id="shoot" onclick="play()"><span id="sl">Shoot the arrow</span> <i>🏹</i></button>
</div>
"""
    css = """
.sec{background-image:radial-gradient(700px 350px at 50% 60%,rgba(224,36,94,.14),transparent)}
.c{display:flex;flex-direction:column;align-items:center;text-align:center}\n#go{position:relative;z-index:5;margin:8px auto 18px;min-height:54px;padding:10px 12px 10px 26px;font-size:16px;box-shadow:0 12px 34px rgba(224,36,94,.42),0 0 0 1px rgba(255,255,255,.14) inset}\n#go i{width:40px;height:40px;font-size:20px}
#stage{width:min(820px,100%);height:auto;margin:18px 0 4px;filter:drop-shadow(0 30px 40px rgba(0,0,0,.5))}
.hover{animation:floaty 2.6s ease-in-out infinite}
.angel-wing{transform-box:fill-box;transform-origin:50% 50%;animation:wingBeat 2.1s ease-in-out infinite alternate}
#wingR{animation-delay:.12s}
@keyframes wingBeat{from{transform:rotate(-2deg)}to{transform:rotate(5deg)}}
#boy [transform="translate(600,352)"]{filter:drop-shadow(0 4px 4px rgba(0,0,0,.18))}
.cap{min-height:30px;font-family:var(--hand);font-size:28px;color:var(--gold);margin:2px 0 8px;opacity:0;transition:opacity .8s}\n#shoot{position:relative;z-index:5;margin:8px auto 18px;min-height:54px;padding:10px 12px 10px 26px;font-size:16px}
.cap.show{opacity:1}
@media(max-width:600px){.cap{font-size:24px}}
"""
    js = """
var S=document.getElementById('stars');
for(var i=0;i<40;i++){var c=document.createElementNS('http://www.w3.org/2000/svg','circle');c.setAttribute('cx',Math.random()*900);c.setAttribute('cy',Math.random()*260);
 c.setAttribute('r',Math.random()*1.5+.4);c.setAttribute('opacity',Math.random()*.7+.2);S.appendChild(c)}
var arrow=document.getElementById('arrow'),boy=document.getElementById('boy'),fx=document.getElementById('fx'),cap=document.getElementById('cap'),
 dz=document.getElementById('dizzy'),playing=false,played=false,anims=[];
var X0=250,Y0=168,X1=596,Y1=262,ANG=Math.atan2(Y1-Y0,X1-X0)*180/Math.PI;
function A(el,k,o){var a=el.animate(k,o);anims.push(a);return a}
function reset(){anims.forEach(function(a){try{a.cancel()}catch(e){}});anims=[];
 if(arrow.parentNode!==document.getElementById('stage'))document.getElementById('stage').appendChild(arrow);
 arrow.style.opacity=0;arrow.style.transform='';fx.innerHTML='';dz.style.opacity=0;
 document.getElementById('eyesN').style.display='';document.getElementById('eyesH').style.display='none';cap.classList.remove('show');
 document.getElementById('str').setAttribute('d','M180,98 L180,238')}
function heart(x,y,d){var t=document.createElementNS('http://www.w3.org/2000/svg','text');t.textContent=['💘','♥','✨','💖'][Math.floor(Math.random()*4)];
 t.setAttribute('x',x);t.setAttribute('y',y);t.setAttribute('font-size',16+Math.random()*16);fx.appendChild(t);
 A(t,[{transform:'translate(0,0)',opacity:1},{transform:'translate('+(Math.random()*80-40)+'px,'+(-90-Math.random()*60)+'px)',opacity:0}],{duration:1400+Math.random()*600,delay:d,fill:'forwards'})}
function play(){
 if(playing)return;playing=true;played=true;reset();
 var btn=document.getElementById('shoot');btn.style.opacity=.55;
 // pull the bowstring
 document.getElementById('str').setAttribute('d','M180,98 L152,168 L180,238');
 arrow.style.opacity=1;
 A(arrow,[{transform:'translate(262px,168px) rotate(0deg)'},{transform:'translate(244px,168px) rotate(0deg)'}],{duration:700,fill:'forwards'});
 setTimeout(function(){
  document.getElementById('str').setAttribute('d','M180,98 L180,238');
  var fl=A(arrow,[{transform:'translate('+X0+'px,'+Y0+'px) rotate('+ANG+'deg)'},{transform:'translate('+X1+'px,'+Y1+'px) rotate('+ANG+'deg)'}],{duration:820,easing:'cubic-bezier(.28,.05,.62,1)',fill:'forwards'});
  fl.onfinish=hit;
 },760);
}
function hit(){
 // the arrow sticks into the boy
 var m=document.getElementById('stage');boy.appendChild(arrow);
 arrow.style.transform='translate('+(X1-2)+'px,'+(Y1)+'px) rotate('+ANG+'deg)';
 // sparkle at his chest
 for(var i=0;i<9;i++)heart(600+Math.random()*30-15,250+Math.random()*20,i*60);
 document.getElementById('eyesN').style.display='none';document.getElementById('eyesH').style.display='';
 A(boy,[{transform:'translateX(0)'},{transform:'translateX(-14px)'},{transform:'translateX(8px)'},{transform:'translateX(-5px)'},{transform:'translateX(0)'}],{duration:420});
 setTimeout(function(){
  var f=A(boy,[{transform:'rotate(0deg)'},{transform:'rotate(98deg)',offset:.62},{transform:'rotate(84deg)',offset:.8},{transform:'rotate(92deg)'}],{duration:1450,easing:'cubic-bezier(.3,.05,.65,1)',fill:'forwards'});
  f.onfinish=function(){
    dz.style.opacity=1;A(dz,[{transform:'translate(740px,300px)'},{transform:'translate(740px,290px)'},{transform:'translate(740px,300px)'}],{duration:1600,iterations:Infinity});
    cap.innerHTML='I fell… for the arrow, or for someone\\'s smile? 😵‍💫';cap.classList.add('show');
    document.getElementById('sl').textContent='Watch again';document.getElementById('shoot').style.opacity=1;playing=false;
    for(var i=0;i<10;i++)heart(740+Math.random()*40-20,320,i*140);
  };
 },520);
}
try{var io=new IntersectionObserver(function(e){if(e[0].isIntersecting&&!played){setTimeout(function(){if(!played)play()},700)}},{threshold:.7});io.observe(document.getElementById('stage'))}catch(e){}
"""
    return page(body, css, js, bg="#0f0709", nxt="#1b0c10", min_h=760)


# ═══════════════════════════════════════════════════════════════════
# 6️⃣  SONG — vinyl + YouTube player
# ═══════════════════════════════════════════════════════════════════
def song_html():
    body = f"""
<div class="in grid">
  <div>
    <div class="eyebrow">A song</div>
    <h2 class="title">The song that makes me<br><em>think of you</em></h2>
    <p class="sub">Some songs are like some people — you hear them and you smile. Put on your headphones and press play. 🎧</p>
    <div style="margin-top:28px"><button class="btn" onclick="playSong()"><span id="pl">Play the song</span> <i>▶</i></button></div>
  </div>
  <div class="stagewrap">
    <div class="vinyl" id="vinyl"><div class="lab">♪</div></div>
    <div class="player">
      <div class="vid" id="vid">
        <img id="th" src="https://i.ytimg.com/vi/{YOUTUBE_ID}/hqdefault.jpg" onerror="this.style.display='none'" alt="">
        <button class="pb" onclick="playSong()">▶</button>
      </div>
      <div class="meta"><div><div class="st">{SONG_TITLE}</div><div class="sa">{SONG_ARTIST}</div></div>
        <div class="eq" id="eq"><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div></div>
      <a class="yt" href="https://youtu.be/{YOUTUBE_ID}" target="_blank" rel="noopener">Not playing? Open it on YouTube ↗</a>
    </div>
  </div>
</div>
"""
    css = """
.sec{background-image:radial-gradient(900px 420px at 70% 100%,rgba(255,140,90,.26),transparent),radial-gradient(600px 350px at 0% 0%,rgba(224,36,94,.16),transparent)}
.grid{display:grid;grid-template-columns:1fr 1.1fr;gap:56px;align-items:center}
@media(max-width:860px){.grid{grid-template-columns:1fr;gap:40px}}
.stagewrap{position:relative;padding:20px 0 20px 40px}
.vinyl{position:absolute;right:-26px;top:50%;width:250px;height:250px;margin-top:-125px;border-radius:50%;z-index:0;
 background:repeating-radial-gradient(circle,#0c0c0e 0 3px,#17171b 3px 5px);box-shadow:0 10px 40px rgba(0,0,0,.6);animation:spin 5s linear infinite paused}
.vinyl:before{content:"";position:absolute;inset:0;border-radius:50%;background:conic-gradient(from 20deg,transparent,rgba(255,255,255,.12),transparent 30%,rgba(255,255,255,.08),transparent 70%)}
.vinyl .lab{position:absolute;inset:36%;border-radius:50%;background:radial-gradient(#ff7da0,#c81650);display:grid;place-items:center;color:#fff;font-size:26px}
.vinyl.on{animation-play-state:running}
@keyframes spin{to{transform:rotate(360deg)}}
.player{position:relative;z-index:2;width:calc(100% - 70px);padding:16px;border-radius:26px;background:rgba(30,14,20,.72);border:1px solid rgba(255,255,255,.1);
 backdrop-filter:blur(14px);box-shadow:0 30px 60px -20px rgba(0,0,0,.8)}
.vid{position:relative;aspect-ratio:16/9;border-radius:16px;overflow:hidden;background:linear-gradient(135deg,#3b1226,#c81650 70%,#ff9e6b)}
.vid img,.vid iframe{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;border:0}
.pb{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:66px;height:66px;border-radius:50%;border:0;background:rgba(224,36,94,.92);color:#fff;font-size:24px;cursor:pointer;
 box-shadow:0 0 0 8px rgba(224,36,94,.25);transition:.25s;padding-left:4px}
.pb:hover{transform:translate(-50%,-50%) scale(1.1)}
.meta{display:flex;justify-content:space-between;align-items:center;margin:16px 4px 4px}
.st{font-weight:600;font-size:17px}.sa{color:var(--muted);font-size:13.5px;margin-top:2px}
.eq{display:flex;align-items:flex-end;gap:3px;height:30px}
.eq i{width:4px;height:6px;border-radius:3px;background:var(--rose2);transition:height .3s}
.eq.on i{animation:eq 1s ease-in-out infinite}
.eq i:nth-child(2n){animation-delay:.2s!important}.eq i:nth-child(3n){animation-delay:.45s!important}.eq i:nth-child(5n){animation-delay:.1s!important}
@keyframes eq{0%,100%{height:6px}50%{height:28px}}
.yt{display:block;margin:10px 4px 2px;color:var(--muted);font-size:12.5px;text-decoration:none}.yt:hover{color:var(--rose2)}
@media(max-width:860px){.stagewrap{padding-left:0}.vinyl{right:-10px;width:190px;height:190px;margin-top:-95px}.player{width:calc(100% - 40px)}}
"""
    js = f"""
var started=false;
function playSong(){{
 if(started)return;started=true;
 var v=document.getElementById('vid');
 v.innerHTML='<iframe src="https://www.youtube-nocookie.com/embed/{YOUTUBE_ID}?autoplay=1&rel=0&playsinline=1" title="song" allow="autoplay; encrypted-media; picture-in-picture; fullscreen" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>';
 document.getElementById('vinyl').classList.add('on');document.getElementById('eq').classList.add('on');
 document.getElementById('pl').textContent='Now playing… 🎶';
}}
"""
    return page(body, css, js, bg="#1b0c10", nxt="#0a0608", min_h=620)


# ═══════════════════════════════════════════════════════════════════
# 🎁  GIFT BOX — unbox a box full of Kinder Joy treats
# ═══════════════════════════════════════════════════════════════════
def gift_html():
    body = """
<div class="in gift-in">
  <div class="eyebrow" style="justify-content:center">A box full of happy little surprises</div>
  <h2 class="title" style="text-align:center">A little box of <em>sweet joy</em></h2>
  <p class="sub gift-sub">Some surprises are even sweeter when you open them. Ready? 🎀</p>

  <div class="gift-stage" id="giftStage">
    <div class="gift-aura"></div>
    <div class="joy-egg" style="--dx:clamp(-320px,-34vw,-100px);--dy:-175px;--rot:-23deg;--delay:.02s"><span>KINDER<br><b>JOY</b></span></div>
    <div class="joy-egg" style="--dx:clamp(-290px,-28vw,-88px);--dy:-260px;--rot:-15deg;--delay:.10s"><span>KINDER<br><b>JOY</b></span></div>
    <div class="joy-egg" style="--dx:clamp(-205px,-20vw,-65px);--dy:-315px;--rot:14deg;--delay:.18s"><span>KINDER<br><b>JOY</b></span></div>
    <div class="joy-egg" style="--dx:clamp(-105px,-10vw,-42px);--dy:-245px;--rot:-9deg;--delay:.26s"><span>KINDER<br><b>JOY</b></span></div>
    <div class="joy-egg" style="--dx:clamp(42px,10vw,105px);--dy:-305px;--rot:17deg;--delay:.34s"><span>KINDER<br><b>JOY</b></span></div>
    <div class="joy-egg" style="--dx:clamp(65px,20vw,205px);--dy:-255px;--rot:24deg;--delay:.42s"><span>KINDER<br><b>JOY</b></span></div>
    <div class="joy-egg" style="--dx:clamp(88px,28vw,290px);--dy:-170px;--rot:13deg;--delay:.50s"><span>KINDER<br><b>JOY</b></span></div>
    <div class="joy-egg" style="--dx:clamp(100px,34vw,320px);--dy:-75px;--rot:-18deg;--delay:.58s"><span>KINDER<br><b>JOY</b></span></div>
    <div class="joy-egg" style="--dx:clamp(-230px,-23vw,-70px);--dy:-70px;--rot:20deg;--delay:.66s"><span>KINDER<br><b>JOY</b></span></div>
    <div class="joy-egg" style="--dx:clamp(-65px,-7vw,-35px);--dy:-125px;--rot:-12deg;--delay:.74s"><span>KINDER<br><b>JOY</b></span></div>

    <div class="gift-box" id="giftBox" aria-label="A wrapped present">
      <div class="gift-shadow"></div>
      <div class="gift-body"><div class="gift-ribbon-v"></div><div class="gift-ribbon-h"></div><div class="gift-front-shine"></div></div>
      <div class="gift-lid"><div class="lid-ribbon"></div></div>
      <div class="gift-bow"><i></i><i></i><span></span></div>
    </div>
    <div class="gift-sparkle sparkle-a">✦</div><div class="gift-sparkle sparkle-b">✧</div>
    <div class="gift-sparkle sparkle-c">✦</div><div class="gift-sparkle sparkle-d">✧</div>
  </div>

  <button class="btn gift-open-btn" id="giftOpenBtn" onclick="openGiftBox()">Unwrap the little surprise <i>🎀</i></button>
  <div class="gift-message" id="giftMessage">A whole bunch of Kinder Joy for a whole bunch of smiles. 🍫✨</div>
</div>
"""
    css = """
.sec{padding-top:86px;padding-bottom:115px;text-align:center;background-image:radial-gradient(600px 360px at 50% 42%,rgba(224,36,94,.16),transparent),radial-gradient(400px 260px at 8% 80%,rgba(246,197,143,.09),transparent)}
.gift-in{display:flex;flex-direction:column;align-items:center}
.gift-sub{margin:0 auto;text-align:center}
.gift-stage{position:relative;width:min(900px,100%);height:420px;margin:22px auto 0;isolation:isolate}
.gift-aura{position:absolute;left:50%;top:57%;width:290px;height:260px;transform:translate(-50%,-50%);border-radius:50%;background:radial-gradient(closest-side,rgba(255,177,125,.24),rgba(224,36,94,.1) 55%,transparent 100%);filter:blur(12px);transition:transform .8s,opacity .8s}
.gift-box{position:absolute;left:50%;top:58%;width:220px;height:205px;transform:translate(-50%,-50%);z-index:5;filter:drop-shadow(0 24px 24px rgba(0,0,0,.38))}
.gift-shadow{position:absolute;left:-22px;right:-22px;bottom:-12px;height:28px;border-radius:50%;background:rgba(0,0,0,.35);filter:blur(10px)}
.gift-body{position:absolute;left:15px;right:15px;bottom:0;height:142px;border-radius:12px 12px 18px 18px;overflow:hidden;border:1px solid rgba(255,235,211,.45);background:linear-gradient(140deg,#f45d83 0%,#d52a63 46%,#a9144b 100%);box-shadow:inset 0 3px 8px rgba(255,255,255,.25),inset 0 -14px 24px rgba(72,0,28,.18)}
.gift-ribbon-v{position:absolute;left:50%;top:0;bottom:0;width:35px;transform:translateX(-50%);background:linear-gradient(90deg,#f4bd70,#fff0c5 48%,#d99b52);box-shadow:0 0 14px rgba(255,225,166,.22)}
.gift-ribbon-h{position:absolute;left:0;right:0;top:48px;height:25px;background:linear-gradient(180deg,#fff0c5,#dfaa61 55%,#f6d18d);box-shadow:0 2px 6px rgba(89,28,35,.25)}
.gift-front-shine{position:absolute;inset:0;background:linear-gradient(115deg,rgba(255,255,255,.22),transparent 35% 70%,rgba(255,255,255,.06));pointer-events:none}
.gift-lid{position:absolute;left:0;right:0;top:39px;height:49px;border-radius:10px;background:linear-gradient(145deg,#ff88a5,#e93d70 58%,#bd2058);border:1px solid rgba(255,228,216,.65);box-shadow:inset 0 3px 7px rgba(255,255,255,.28),0 8px 15px rgba(0,0,0,.2);z-index:7;transform-origin:12% 85%;transition:transform .85s cubic-bezier(.2,.85,.25,1),opacity .5s}
.lid-ribbon{position:absolute;left:50%;top:-1px;bottom:-1px;width:35px;transform:translateX(-50%);background:linear-gradient(90deg,#f4bd70,#fff0c5 48%,#d99b52)}
.gift-bow{position:absolute;left:50%;top:0;width:100px;height:65px;transform:translateX(-50%);z-index:8;transition:transform .75s cubic-bezier(.2,.85,.25,1),opacity .45s}
.gift-bow i{position:absolute;top:4px;width:43px;height:31px;border:9px solid #ffe8b4;border-radius:85% 85% 18% 85%;background:linear-gradient(135deg,#f6d28b,#d99a4e);box-shadow:0 4px 8px rgba(0,0,0,.2)}
.gift-bow i:first-child{left:7px;transform:rotate(28deg)}.gift-bow i:nth-child(2){right:7px;transform:scaleX(-1) rotate(28deg)}
.gift-bow span{position:absolute;left:40px;top:20px;width:20px;height:20px;border-radius:50%;background:radial-gradient(circle at 35% 30%,#fff1c9,#df9b4b);box-shadow:0 3px 6px rgba(0,0,0,.25)}
.joy-egg{position:absolute;left:50%;top:58%;width:66px;height:96px;margin-left:-33px;z-index:6;opacity:0;display:flex;align-items:center;justify-content:center;border-radius:49% 49% 45% 45% / 43% 43% 56% 56%;border:2px solid rgba(255,255,255,.82);background:linear-gradient(180deg,#fffdf5 0%,#fff9e9 48%,#ffc078 49%,#f58d4b 100%);box-shadow:0 12px 24px rgba(0,0,0,.28),inset -5px 0 9px rgba(255,255,255,.3),inset 5px 0 10px rgba(140,70,25,.08);transform:translate(-50%,20px) scale(.12);transform-origin:center bottom}
.joy-egg:before{content:"";position:absolute;left:10px;top:12px;width:13px;height:27px;border-radius:50%;background:rgba(255,255,255,.82);filter:blur(2px);transform:rotate(18deg)}
.joy-egg:after{content:"";position:absolute;left:0;right:0;top:47%;height:2px;background:rgba(209,132,72,.22)}
.joy-egg span{position:relative;z-index:1;margin-top:1px;text-align:center;color:#d54836;font:800 8px/1.03 Arial,sans-serif;letter-spacing:-.4px;text-shadow:0 1px rgba(255,255,255,.6)}
.joy-egg span b{font-size:13px;letter-spacing:.4px;color:#e96c27}
.gift-stage.opened .gift-aura{transform:translate(-50%,-50%) scale(1.45);opacity:1}
.gift-stage.opened .gift-lid{transform:translate(-28px,-112px) rotate(-19deg);opacity:.98}
.gift-stage.opened .gift-bow{transform:translate(-50%,-145px) rotate(-18deg);opacity:0}
.gift-stage.opened .gift-body{animation:boxJiggle .5s .1s ease both}
.gift-stage.opened .joy-egg{animation:joyBurst 1.2s var(--delay) cubic-bezier(.13,.78,.2,1) forwards}
@keyframes joyBurst{0%{opacity:0;transform:translate(-50%,20px) scale(.12) rotate(0)}16%{opacity:1}72%{opacity:1;transform:translate(calc(-50% + var(--dx)),calc(var(--dy) - 20px)) scale(1.08) rotate(var(--rot))}100%{opacity:1;transform:translate(calc(-50% + var(--dx)),var(--dy)) scale(1) rotate(var(--rot))}}
@keyframes boxJiggle{0%,100%{transform:translateY(0)}25%{transform:translateY(-8px) rotate(-2deg)}50%{transform:translateY(3px) rotate(2deg)}75%{transform:translateY(-4px) rotate(-1deg)}}
.gift-sparkle{position:absolute;z-index:9;color:#ffe1a2;font-size:28px;opacity:0;filter:drop-shadow(0 0 10px rgba(255,218,142,.8))}
.sparkle-a{left:21%;top:28%}.sparkle-b{right:22%;top:22%;font-size:36px}.sparkle-c{left:32%;top:67%}.sparkle-d{right:32%;top:67%;font-size:34px}
.gift-stage.opened .gift-sparkle{animation:twinkle .9s ease-in-out infinite alternate}
@keyframes twinkle{from{opacity:.25;transform:scale(.7) rotate(0)}to{opacity:1;transform:scale(1.25) rotate(28deg)}}
.gift-open-btn{margin-top:0;position:relative;z-index:10}
.gift-message{min-height:34px;margin-top:12px;color:#ffd6df;font:500 22px var(--hand);opacity:0;transform:translateY(8px);transition:all .6s}
.gift-message.show{opacity:1;transform:none}
@media(max-width:640px){.sec{padding-top:72px;padding-bottom:95px}.gift-stage{height:370px;margin-top:16px}.gift-box{transform:translate(-50%,-50%) scale(.82)}.joy-egg{width:55px;height:82px;margin-left:-27.5px}.joy-egg span{font-size:7px}.joy-egg span b{font-size:11px}.gift-message{font-size:20px;padding:0 8px}.gift-open-btn{font-size:14px}}
@media(prefers-reduced-motion:reduce){.gift-stage.opened .joy-egg,.gift-stage.opened .gift-sparkle,.gift-stage.opened .gift-body{animation-duration:.01ms!important;animation-iteration-count:1!important}}
"""
    js = """
var giftOpened=false;
function openGiftBox(){
  var stage=document.getElementById('giftStage');
  var btn=document.getElementById('giftOpenBtn');
  var msg=document.getElementById('giftMessage');
  if(!stage||!btn||!msg)return;
  if(giftOpened){
    stage.classList.remove('opened');msg.classList.remove('show');giftOpened=false;
    btn.innerHTML='Unwrap the little surprise <i>🎀</i>';
    return;
  }
  // Restart CSS animations cleanly if the visitor opens the box again.
  stage.classList.remove('opened');void stage.offsetWidth;stage.classList.add('opened');
  giftOpened=true;btn.innerHTML='That was a sweet surprise! <i>✨</i>';
  setTimeout(function(){msg.classList.add('show')},680);
  var symbols=['✦','✧','♥','✨','✦','✧'];
  for(var i=0;i<24;i++){
    var p=document.createElement('span');p.textContent=symbols[i%symbols.length];p.className='gift-pop';
    p.style.left=(15+Math.random()*70)+'%';p.style.top=(28+Math.random()*48)+'%';
    p.style.setProperty('--sx',(Math.random()*100-50)+'px');p.style.setProperty('--sy',(-70-Math.random()*150)+'px');
    stage.appendChild(p);setTimeout((function(el){return function(){el.remove()}})(p),1500);
  }
}
"""
    css += """
.gift-pop{position:absolute;z-index:12;color:#ffdfa5;font-size:18px;pointer-events:none;animation:giftPop 1.35s ease-out forwards;filter:drop-shadow(0 0 7px rgba(255,218,142,.8))}
@keyframes giftPop{0%{opacity:0;transform:translate(0,0) scale(.4)}15%{opacity:1}100%{opacity:0;transform:translate(var(--sx),var(--sy)) scale(1.35) rotate(35deg)}}
"""
    return page(body, css, js, bg="#1b0a12", nxt="#0a0608", min_h=700)


# ═══════════════════════════════════════════════════════════════════
# 7️⃣  SURPRISES — little hidden things
# ═══════════════════════════════════════════════════════════════════
def surprise_html():
    body = """
<div class="in">
  <div class="eyebrow">More surprises</div>
  <h2 class="title">Little things <em>hidden in my pocket</em></h2>
  <p class="sub" style="margin-bottom:38px">Every card hides something. Tap around to find it. 🔍</p>
  <div class="cards">

    <div class="cd">
      <div class="num">01</div><h3>Why are you special?</h3>
      <div class="reason" id="reason">Press the button to find out one reason…</div>
      <button class="mini" onclick="nextReason()">Tell me a reason ✨</button>
    </div>

    <div class="cd">
      <div class="num">02</div><h3>A little plot twist</h3>
      <div class="drawer" id="drawer">
        <div class="slip" id="slip">Plot twist: you deserve a little extra happiness today. 🌼<br><small>Consider this your tiny reminder to smile.</small></div>
        <div class="box" onclick="toggleDrawer()"><div class="handle"></div></div>
      </div>
      <div class="tiny" id="dh">Slide the little box open ↑</div>
    </div>

    <div class="cd">
      <div class="num">03</div><h3>How's your mood today?</h3>
      <div class="moods" id="moods">
        <button data-i="0">😊</button><button data-i="1">😴</button><button data-i="2">😤</button><button data-i="3">🥺</button><button data-i="4">🤩</button>
      </div>
      <div class="reason" id="moodr" style="min-height:70px">Pick an emoji…</div>
    </div>

  </div>
</div>
"""
    css = """
.sec{background-image:radial-gradient(700px 350px at 20% 0%,rgba(224,36,94,.14),transparent),radial-gradient(500px 300px at 100% 100%,rgba(246,197,143,.10),transparent)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(255px,1fr));gap:22px}
.cd{position:relative;padding:26px 24px 26px;border-radius:24px;background:linear-gradient(160deg,rgba(255,255,255,.07),rgba(255,255,255,.02));border:1px solid rgba(255,255,255,.1);
 backdrop-filter:blur(8px);display:flex;flex-direction:column;gap:16px;min-height:290px;transition:transform .3s,border-color .3s}
.cd:hover{transform:translateY(-6px);border-color:rgba(255,107,146,.5)}
.num{font-family:var(--serif);font-style:italic;color:var(--rose2);font-size:15px}
.cd h3{font-family:var(--serif);font-weight:500;font-size:24px;line-height:1.25}
.reason{flex:1;color:#f4dde3;line-height:1.75;font-size:16px;animation:none}
.reason.pop{animation:fadeUp .6s both}
.mini{align-self:flex-start;border:0;cursor:pointer;color:#fff;font:600 14px var(--sans);padding:11px 20px;border-radius:999px;background:linear-gradient(135deg,#f0356d,#c81650);box-shadow:0 8px 22px -8px rgba(224,36,94,.8);transition:.25s}
.mini:hover{transform:translateY(-2px)}
.drawer{position:relative;height:196px;margin-top:6px}
.box{position:absolute;left:0;right:0;bottom:0;height:80px;border-radius:12px;background:linear-gradient(#8a4a2e,#6b3720);box-shadow:inset 0 3px 0 rgba(255,255,255,.14),0 12px 20px rgba(0,0,0,.5);cursor:pointer;z-index:3;transition:transform .6s cubic-bezier(.3,1.3,.5,1)}
.handle{position:absolute;left:50%;top:50%;width:62px;height:14px;margin:-7px 0 0 -31px;border-radius:8px;background:linear-gradient(#f6d49a,#b98a45);box-shadow:0 3px 6px rgba(0,0,0,.5)}
.slip{position:absolute;left:12px;right:12px;bottom:40px;padding:14px 14px 56px;border-radius:8px;background:#fff6ef;color:#5a2a3c;font-family:var(--hand);font-size:21px;line-height:1.2;z-index:2;transform:translateY(60px);opacity:0;transition:all .7s ease .15s;text-align:center}
.slip small{font-size:15px;color:#b8315c}
.drawer.open .box{transform:translateY(34px)}
.drawer.open .slip{transform:translateY(-22px);opacity:1}
.tiny{color:var(--muted);font-size:13px;margin-top:20px}
.moods{display:flex;gap:8px;flex-wrap:wrap}
.moods button{font-size:28px;width:52px;height:52px;border-radius:16px;border:1px solid rgba(255,255,255,.12);background:rgba(255,255,255,.05);cursor:pointer;transition:.25s}
.moods button:hover{transform:translateY(-4px) scale(1.1);background:rgba(224,36,94,.25)}
.moods button.sel{background:rgba(224,36,94,.4);border-color:var(--rose2);transform:scale(1.1)}
"""
    js = f"""
var R={esc(REASONS)},ri=-1;
function nextReason(){{var n;do{{n=Math.floor(Math.random()*R.length)}}while(n===ri&&R.length>1);ri=n;
 var el=document.getElementById('reason');el.classList.remove('pop');void el.offsetWidth;el.textContent='"'+R[n]+'"';el.classList.add('pop')}}
function toggleDrawer(){{var d=document.getElementById('drawer');d.classList.toggle('open');document.getElementById('dh').style.opacity=d.classList.contains('open')?0:1}}
var MOOD=['Then the day is already a success. Keep that smile! 😄','Go ahead and sleep. And when you wake up, have a cup of tea — on me. ☕','Who made you angry? Tell me their name… I will say sorry on their behalf. 🙇','If you feel low, remember — you are doing better than you think. 🤍','Wow! Then today is yours. Go do whatever you want! 🎉'];
document.querySelectorAll('#moods button').forEach(function(b){{b.addEventListener('click',function(){{
 document.querySelectorAll('#moods button').forEach(function(x){{x.classList.remove('sel')}});b.classList.add('sel');
 var el=document.getElementById('moodr');el.classList.remove('pop');void el.offsetWidth;el.textContent=MOOD[+b.dataset.i];el.classList.add('pop')}})}});
"""
    return page(body, css, js, bg="#0a0608", nxt="#2a1018", min_h=640)


# ═══════════════════════════════════════════════════════════════════
# 8️⃣  ENDING — closing words (+ a button that runs away)
# ═══════════════════════════════════════════════════════════════════
def ending_html():
    ask = ""
    if SHOW_ASK:
        ask = """
  <div class="ask" id="ask">
    <button class="btn" id="go" onclick="showQ()">Can I ask you something? <i>?</i></button>
    <div id="q" style="display:none">
      <div class="qq">Would you like to grab a cup of tea (or coffee) with me one day? ☕</div>
      <div class="row">
        <button class="btn" onclick="yes()">Yes, why not! <i>☕</i></button>
        <button class="ghost" id="no" onmouseover="dodge()" ontouchstart="dodge(event)" onclick="dodge()">Let me think…</button>
      </div>
    </div>
    <div id="ok" class="okmsg" style="display:none">Awesome! It's a plan. 🎉<br><span>Now you pick the time — I'll be waiting.</span></div>
  </div>"""
    body = f"""
<canvas id="cf" style="position:absolute;inset:0;width:100%;height:100%;z-index:4;pointer-events:none"></canvas>
<div class="sunset"></div>
<div class="in c">
  <div class="mini-heart">❀</div>
  <div class="eyebrow" style="justify-content:center;margin-top:8px">One last little surprise</div>
  <div class="quote">“I hope you found<br><em>a reason to smile.”</em></div>
  <div class="closing-copy">
    <p>And just like that, you've reached the end of this little journey.</p>
    <p>I hope somewhere along the way, you found a reason to smile. Maybe it was a song, a little note, a flower, or simply the thought behind it all.</p>
    <p>Life is made of little moments like these. Keep collecting beautiful ones, keep being yourself, and never forget to smile.</p>
    <p>Wishing you countless happy little moments ahead. 🌷✨</p>
  </div>
  {ask}
  <div class="foot">Made with ☕ & a little care — {YOUR_NAME}</div>
</div>
"""
    css = """
.sec{padding-bottom:70px;text-align:center}
.sunset{position:absolute;inset:0;background:radial-gradient(900px 420px at 50% 115%,rgba(255,140,90,.5),rgba(224,36,94,.25) 45%,transparent 70%)}
.c{display:flex;flex-direction:column;align-items:center}
.mini-heart{color:var(--rose2);font-size:26px;animation:floaty 3s infinite}
.quote{font-family:var(--serif);font-size:clamp(30px,5.4vw,60px);line-height:1.25;font-weight:500;margin-top:12px}
.quote em{color:var(--gold);font-style:italic;text-shadow:0 0 40px rgba(246,197,143,.5)}
.closing-copy{width:min(760px,100%);margin:22px auto 34px;padding:24px 30px;border:1px solid rgba(255,255,255,.10);border-radius:22px;
 background:linear-gradient(145deg,rgba(255,255,255,.065),rgba(255,255,255,.018));backdrop-filter:blur(10px);box-shadow:0 18px 48px rgba(0,0,0,.16)}
.closing-copy p{color:#e8cbd4;font-size:15px;line-height:1.9;margin:0 0 12px}
.closing-copy p:last-child{margin-bottom:0;color:#ffd1dc}
@media(max-width:640px){.closing-copy{padding:20px 18px}.closing-copy p{font-size:14px;line-height:1.8}}
.ask{min-height:170px;position:relative;width:100%}
.qq{font-family:var(--serif);font-size:clamp(22px,3.6vw,32px);margin-bottom:26px;animation:fadeUp .7s both}
.row{display:flex;gap:18px;justify-content:center;align-items:center;flex-wrap:wrap;min-height:70px;position:relative}
.ghost{border:1px solid rgba(255,255,255,.3);background:rgba(255,255,255,.06);color:#fff;font:500 15px var(--sans);padding:14px 26px;border-radius:999px;cursor:pointer;transition:left .25s,top .25s}
.okmsg{font-family:var(--serif);font-size:clamp(24px,4vw,36px);animation:fadeUp .8s both;line-height:1.5}
.okmsg span{font-family:var(--sans);font-size:16px;color:var(--muted)}
.foot{margin-top:70px;color:var(--muted);font-size:13px;letter-spacing:.04em}
"""
    js = """
function showQ(){document.getElementById('go').style.display='none';document.getElementById('q').style.display='block'}
var dd=0;
function dodge(e){
 var b=document.getElementById('no');
 if(dd>=7){b.textContent='Okay, no rush 🙂';b.style.position='static';b.onmouseover=null;b.onclick=function(){toast('No pressure — whenever you feel like it. 😊',3000)};return}
 dd++;var row=b.parentNode;var rw=row.clientWidth-b.offsetWidth-10,rh=100;
 b.style.position='absolute';b.style.left=Math.max(0,Math.random()*rw)+'px';b.style.top=(Math.random()*rh-20)+'px';
 if(dd===3)toast('Can not catch me 😜',1800)}
function yes(){
 document.getElementById('q').style.display='none';document.getElementById('ok').style.display='block';confetti()}
function confetti(){
 var c=document.getElementById('cf'),x=c.getContext('2d');c.width=c.offsetWidth;c.height=c.offsetHeight;var W=c.width,H=c.height,P=[];
 var col=['#ff6b92','#f6c58f','#fff','#e0245e','#ffd9e3','#ffb18a'];
 for(var i=0;i<180;i++)P.push({x:W/2+(Math.random()-.5)*200,y:H*.55,vx:(Math.random()-.5)*14,vy:-Math.random()*16-4,r:Math.random()*6+3,c:col[i%6],a:Math.random()*6,w:Math.random()*.3-.15});
 var t0=performance.now();
 (function f(t){x.clearRect(0,0,W,H);P.forEach(function(p){p.vy+=.35;p.x+=p.vx;p.y+=p.vy;p.vx*=.992;p.a+=p.w;
  x.save();x.translate(p.x,p.y);x.rotate(p.a);x.fillStyle=p.c;x.fillRect(-p.r,-p.r/2,p.r*2,p.r);x.restore()});
  if(t-t0<4500)requestAnimationFrame(f);else x.clearRect(0,0,W,H)})(t0)}
"""
    return page(body, css, js, bg="#2a1018", nxt="#2a1018", min_h=620, wave=False)


# ═══════════════════════════════════════════════════════════════════
# 🚀  Streamlit page
# ═══════════════════════════════════════════════════════════════════
BASE_PAGE_CSS = """
<style>
html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{background:#000!important}
header,footer,#MainMenu,[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stHeader"],[data-testid="stStatusWidget"]{display:none!important;visibility:hidden!important}
.block-container,[data-testid="stMainBlockContainer"]{padding:0!important;max-width:100%!important}
[data-testid="stVerticalBlock"]{gap:0!important}
[data-testid="stElementContainer"]{margin:0!important}
iframe{display:block;border:0;width:100%}
html{scroll-behavior:smooth}
</style>
"""

INTRO_CSS = """
<style>
.dark-hint{position:fixed;left:0;right:0;top:calc(50vh - 190px);text-align:center;color:#e2bdc8;
  font-family:'DM Sans',system-ui,sans-serif;letter-spacing:.08em;font-size:15px;pointer-events:none}
[data-testid="stButton"]{position:fixed!important;left:0;right:0;top:50vh;transform:translateY(-50%);
  display:flex!important;justify-content:center!important;z-index:50!important}
[data-testid="stButton"] button{position:relative!important;overflow:visible!important;width:270px!important;height:205px!important;
  padding:116px 18px 20px!important;border:1px solid rgba(255,231,201,.72)!important;border-radius:17px 17px 22px 22px!important;
  color:#fff8f0!important;font:700 13px 'DM Sans',sans-serif!important;letter-spacing:.12em!important;text-transform:uppercase!important;
  background:linear-gradient(90deg,transparent 43%,#ffe9b8 43% 57%,transparent 57%),
    linear-gradient(180deg,transparent 0 66%,rgba(95,9,43,.12) 66% 100%),
    linear-gradient(145deg,#f45f88 0%,#d52d65 52%,#9e174c 100%)!important;
  box-shadow:0 34px 75px rgba(224,36,94,.28),inset 0 2px 2px rgba(255,255,255,.24),inset 0 -18px 28px rgba(65,0,24,.16)!important;
  transition:transform .35s,box-shadow .35s!important}
/* Gift-box lid */
[data-testid="stButton"] button:before{content:"";position:absolute;left:50%;top:-18px;transform:translateX(-50%);
  width:294px;height:48px;border-radius:11px;background:linear-gradient(90deg,transparent 43%,#f7d28e 43% 57%,transparent 57%),
  linear-gradient(145deg,#ff9ab4,#e84679 60%,#c52660);border:1px solid rgba(255,231,201,.75);
  box-shadow:0 8px 15px rgba(0,0,0,.22),inset 0 3px 4px rgba(255,255,255,.28);transform-origin:16% 90%;
  transition:transform .45s cubic-bezier(.2,.85,.25,1)}
/* Satin bow */
[data-testid="stButton"] button:after{content:"🎀";position:absolute;left:50%;top:-76px;transform:translateX(-50%);
  font-size:68px;line-height:1;filter:drop-shadow(0 7px 7px rgba(0,0,0,.22));transform-origin:50% 80%;transition:transform .4s}
[data-testid="stButton"] button:hover{transform:translateY(-7px) scale(1.025)!important;
  box-shadow:0 42px 85px rgba(224,36,94,.38),inset 0 2px 2px rgba(255,255,255,.26)!important}
[data-testid="stButton"] button:hover:before{transform:translate(-44%,-8px) rotate(-3deg)}
[data-testid="stButton"] button:hover:after{transform:translate(-50%,-12px) rotate(9deg)}
[data-testid="stButton"] button:active{transform:translateY(2px) scale(.985)!important}
[data-testid="stButton"] button:active:before{transform:translate(-42%,-24px) rotate(-8deg)}
[data-testid="stButton"] button:active:after{transform:translate(-50%,-24px) rotate(16deg)}
@media(max-width:520px){[data-testid="stButton"] button{width:230px!important;height:182px!important;padding-top:104px!important;font-size:11px!important}
 [data-testid="stButton"] button:before{width:250px;height:42px;top:-16px}[data-testid="stButton"] button:after{font-size:58px;top:-66px}}
</style>
"""

REVEAL_CSS = """
<style>
[data-testid="stMainBlockContainer"],.block-container{animation:lightsOn 2.2s ease-out both}
@keyframes lightsOn{0%{opacity:0;filter:brightness(.2)}35%{opacity:.7;filter:brightness(.5)}50%{opacity:.4}100%{opacity:1;filter:none}}
</style>
"""


def _turn_on():
    st.session_state["lights_on"] = True


def main():
    st.set_page_config(page_title="Just for you ✨", page_icon="🌹", layout="wide", initial_sidebar_state="collapsed")
    st.markdown(BASE_PAGE_CSS, unsafe_allow_html=True)

    if not st.session_state.get("lights_on"):
        # ⚫ black screen + one switch
        st.markdown(INTRO_CSS, unsafe_allow_html=True)
        st.markdown('<div class="dark-hint">A little gift is waiting for you. Untie the ribbon to begin ✨</div>', unsafe_allow_html=True)
        if st.button("Unwrap your little surprise", key="unwrap"):
            _turn_on()
            st.rerun()
        return

    # 💡 lights on — the full website
    st.markdown(REVEAL_CSS, unsafe_allow_html=True)
    missing_photos = missing_gallery_photos()
    if missing_photos:
        expected = os.path.join(BASE_DIR, "assets", "photos")
        st.error(
            "The gallery images were not found. Put the five photo files inside "
            f"`{expected}`. Missing: " + ", ".join(missing_photos) +
            ". The downloaded ZIP already contains this assets/photos folder; "
            "merge it beside main.py and requirements.txt."
        )
    sections = [
        (hero_html, 880),
        (note_html, 720),
        (rope_html, 780),
        (flower_html, 820),
        (gift_html, 790),
        (cupid_html, 820),
        (song_html, 620),
        (surprise_html, 640),
        (ending_html, 780),
    ]
    for fn, h in sections:
        components.html(fn(), height=h + 90, scrolling=False)


if __name__ == "__main__":
    main()

