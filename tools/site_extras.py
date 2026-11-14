"""C5 add-on for publish.py: everything driven by Website/_site.json on the NAS.
  * style  -> site-settings.css (colors, fonts, text sizes), loaded on every page after style.css
  * text   -> site-text.js (homepage intro, About, Now, Contact, Journal, footer, logo), applied on every page
  * cover  -> index.html becomes a public cover page with a rotating photo carousel (photos from Website/_cover, or all
              website photos); the portfolio home lives at work.html. With the cover off, index.html is the portfolio again.
Past Life never appears: publish.py skips any folder or file with "past life" in its name."""
import base64, html, json, re
from datetime import datetime
from pathlib import Path

DEFAULT_STYLE = {"background": "#f6f4f0", "text": "#1b1a18", "muted": "#77736b", "lines": "#dcd7ce",
                 "heading_font": "Cormorant Garamond", "body_font": "Inter", "text_size": 16, "heading_size": 100}
FONT_RE = re.compile(r"^[A-Za-z0-9 ]{2,40}$")
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
INC_CSS = '<link rel="stylesheet" href="site-settings.css">'
INC_JS = '<script src="site-text.js"></script>'


def esc(s):
    return html.escape(str(s or ""), quote=True)


def css(style):
    s = dict(DEFAULT_STYLE, **{k: v for k, v in (style or {}).items() if v not in (None, "")})
    for k in ("background", "text", "muted", "lines"):
        if not HEX.match(str(s[k])):
            s[k] = DEFAULT_STYLE[k]
    for k in ("heading_font", "body_font"):
        if not FONT_RE.match(str(s[k])):
            s[k] = DEFAULT_STYLE[k]
    try:
        size = max(13, min(22, float(s["text_size"])))
    except (TypeError, ValueError):
        size = 16
    try:
        hs = max(60, min(160, float(s["heading_size"]))) / 100
    except (TypeError, ValueError):
        hs = 1
    fams = [f for f in (s["heading_font"], s["body_font"]) if f not in ("Cormorant Garamond", "Inter")]
    imp = ""
    if fams:
        q = "&".join("family=" + f.replace(" ", "+") + ":ital,wght@0,300;0,400;0,500;0,600;1,400" for f in dict.fromkeys(fams))
        imp = f'@import url("https://fonts.googleapis.com/css2?{q}&display=swap");\n'
    return (f"/* GENERATED from Website/_site.json on the NAS. Edit that file, not this one. Built {datetime.now():%Y-%m-%d %H:%M} */\n{imp}"
            f':root{{--bg:{s["background"]};--ink:{s["text"]};--muted:{s["muted"]};--line:{s["lines"]};'
            f'--serif:"{s["heading_font"]}", Georgia, serif;--sans:"{s["body_font"]}", system-ui, -apple-system, sans-serif;--hs:{hs}}}\n'
            f"body{{font-size:{size}px}}.split .body p{{font-size:{size}px}}\n"
            ".page-head h1{font-size:calc(clamp(40px,6vw,72px) * var(--hs))}.intro p{font-size:calc(clamp(24px,3vw,34px) * var(--hs))}"
            ".set-over h3{font-size:calc(clamp(40px,4.4vw,60px) * var(--hs))}.post h3{font-size:calc(26px * var(--hs))}"
            ".contact-line{font-size:calc(clamp(24px,4vw,36px) * var(--hs))}\n")


TEXT_JS = r"""
(function(){
  var T = window.SITE_TEXT || {}, page = document.body.dataset.page;
  function e(s){ return String(s == null ? "" : s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
  function md(s){ return e(s).replace(/\*\*(.+?)\*\*/g,"<strong>$1</strong>").replace(/\*(.+?)\*/g,"<em>$1</em>"); }
  function has(k){ return T[k] != null && T[k] !== "" && !(Array.isArray(T[k]) && !T[k].length); }
  function set(sel, k){ if(!has(k)) return; var el = document.querySelector(sel); if(el) el.innerHTML = md(T[k]); }
  function paras(sel, k){ if(!has(k)) return; var box = document.querySelector(sel); if(!box) return;
    var ps = Array.prototype.filter.call(box.children, function(c){ return c.tagName === "P" && !c.classList.contains("note"); });
    var at = ps.length ? ps[0] : box.firstChild; var list = Array.isArray(T[k]) ? T[k] : [T[k]];
    list.forEach(function(t){ var p = document.createElement("p"); p.innerHTML = md(t); box.insertBefore(p, at); });
    ps.forEach(function(p){ p.remove(); });
    Array.prototype.forEach.call(box.querySelectorAll("p.note"), function(n){ n.remove(); }); }
  if(has("logo")){ var l = document.querySelector(".logo"); if(l && l.firstChild && l.firstChild.nodeType === 3) l.firstChild.nodeValue = T.logo; }
  set(".logo span", "logo_small"); set(".foot-sub p", "footer_subscribe");
  if(page === "home") set(".intro p", "home_intro");
  if(page === "about"){ set(".page-head h1", "about_title"); paras(".split .body", "about"); }
  if(page === "now"){ set(".page-head h1", "now_title"); set(".page-head p", "now_intro"); paras(".split .body", "now"); }
  if(page === "journal"){ set(".page-head h1", "journal_title"); set(".page-head p", "journal_intro"); }
  if(page === "contact"){ set(".page-head h1", "contact_title"); set(".page-head p", "contact_intro");
    if(has("email")){ var c = document.querySelector(".contact-line"); if(c){ c.textContent = T.email; c.href = "mailto:" + T.email; } }
    if(has("based_in")) Array.prototype.forEach.call(document.querySelectorAll(".contact-list div"), function(d){
      if(d.firstElementChild && /based in/i.test(d.firstElementChild.textContent) && d.lastElementChild) d.lastElementChild.textContent = T.based_in; }); }
})();
"""


def text_js(text):
    clean = {k: v for k, v in (text or {}).items() if isinstance(v, (str, list)) and not k.startswith("_")}
    return ("/* GENERATED from Website/_site.json on the NAS. Edit that file, not this one. */\n"
            f"window.SITE_TEXT = {json.dumps(clean, ensure_ascii=False)};\n" + TEXT_JS)


def cover_html(c, pool, site_url, repo):
    pics = []
    for p in pool[:24]:
        pics.append({"s": p.get("srcSmall") or p["src"], "l": p["src"], "t": p.get("title", ""), "p": p.get("place", ""), "f": p.get("focus") or "50% 50%"})
    try:
        fav = "data:image/svg+xml;base64," + base64.b64encode((repo / "favicon.svg").read_bytes()).decode()
    except OSError:
        fav = ""
    title, tag, enter = esc(c.get("title") or "Nduwimana Claude"), esc(c.get("tagline") or "Photography"), esc(c.get("enter") or "View the work")
    secs = max(3, min(20, int(c.get("seconds") or 6)))
    links = "".join(f'<a href="{esc(u)}" rel="noopener">{esc(n)}</a>' for n, u in (c.get("links") or {}).items()
                    if isinstance(u, str) and re.match(r"^(https://|mailto:)", u))
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · {tag}</title><meta name="description" content="{tag} by {title}.">
<meta property="og:type" content="website"><meta property="og:title" content="{title} · {tag}"><meta property="og:image" content="{site_url}/photos/og.jpg">
<meta name="twitter:card" content="summary_large_image">{f'<link rel="icon" href="{fav}">' if fav else ""}
<!-- generated cover page (Website/_site.json "cover"). Self-contained so it works while the rest of the site needs a sign-in. -->
<style>
*{{box-sizing:border-box;margin:0;padding:0}}html,body{{height:100%;background:#0d0c0b;color:#f3efe8;font-family:system-ui,-apple-system,"Helvetica Neue",sans-serif;overflow:hidden}}
.cv{{position:fixed;inset:0}}.cv img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0;transition:opacity 1.6s ease;transform:scale(1.04)}}
.cv img.on{{opacity:1;animation:kb {secs + 2}s ease-out forwards}}@keyframes kb{{from{{transform:scale(1.04)}}to{{transform:scale(1.10)}}}}
.shade{{position:fixed;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.35),rgba(0,0,0,.05) 35%,rgba(0,0,0,.15) 65%,rgba(0,0,0,.6))}}
.top{{position:fixed;top:0;left:0;right:0;padding:28px 32px;display:flex;justify-content:space-between;align-items:center;gap:16px}}
.name{{font-family:"Cormorant Garamond",Georgia,serif;font-size:28px;font-weight:500;letter-spacing:.01em}}.name span{{font-style:italic;opacity:.75;font-size:21px;margin-left:8px}}
.links{{display:flex;gap:20px;font-size:12px;letter-spacing:.16em;text-transform:uppercase}}.links a{{color:inherit;text-decoration:none;opacity:.85}}
.mid{{position:fixed;left:0;right:0;bottom:84px;text-align:center;padding:0 24px}}
.enter{{display:inline-block;color:#f3efe8;text-decoration:none;border:1px solid rgba(243,239,232,.8);padding:14px 26px;font-size:12px;letter-spacing:.18em;text-transform:uppercase;backdrop-filter:blur(4px);background:rgba(0,0,0,.15)}}
.enter:hover{{background:#f3efe8;color:#111}}.cap{{position:fixed;left:32px;bottom:28px;font-size:12px;letter-spacing:.04em;opacity:.85}}.cap b{{font-weight:500}}
.dots{{position:fixed;right:32px;bottom:30px;display:flex;gap:6px}}.dots i{{width:6px;height:6px;border-radius:50%;background:rgba(243,239,232,.4)}}.dots i.on{{background:#f3efe8}}
@media(max-width:640px){{.top{{padding:20px}}.name{{font-size:23px}}.links{{display:none}}.cap{{left:20px;right:20px;bottom:20px;text-align:center}}.dots{{display:none}}.mid{{bottom:70px}}}}
@media(prefers-reduced-motion:reduce){{.cv img.on{{animation:none}}}}
</style></head><body>
<div class="cv" id="cv"></div><div class="shade"></div>
<div class="top"><div class="name">{title}<span>{tag}</span></div><div class="links">{links}</div></div>
<div class="mid"><a class="enter" href="work.html">{enter}</a></div><div class="cap" id="cap"></div><div class="dots" id="dots"></div>
<script>
(function(){{var P={json.dumps(pics, ensure_ascii=False)},S={secs}*1000,cv=document.getElementById("cv"),cap=document.getElementById("cap"),dots=document.getElementById("dots"),i=0,big=innerWidth>900;
if(!P.length){{cv.style.background="#222";return;}}
function e(s){{return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;")}}
P.forEach(function(p,k){{var im=new Image();im.alt=p.t;im.decoding="async";if(k>1)im.loading="lazy";im.src=big?p.l:p.s;im.style.objectPosition=p.f;cv.appendChild(im);dots.insertAdjacentHTML("beforeend","<i></i>");}});
function show(n){{var ims=cv.children,ds=dots.children;for(var k=0;k<ims.length;k++){{ims[k].classList.toggle("on",k===n);if(ds[k])ds[k].classList.toggle("on",k===n);}}
 cap.innerHTML=P[n].t?("<b>"+e(P[n].t)+"</b>"+(P[n].p?" &middot; "+e(P[n].p):"")):"";}}
show(0);if(P.length>1)setInterval(function(){{i=(i+1)%P.length;show(i);}},S);
}})();
</script></body></html>
"""


def ensure_includes(repo, skip=()):
    """Add the two include lines to every page that loads style.css / site.js (once)."""
    n = 0
    for f in repo.glob("*.html"):
        if f.name in skip:
            continue
        s = f.read_text(); o = s
        if INC_CSS not in s and '<link rel="stylesheet" href="style.css">' in s:
            s = s.replace('<link rel="stylesheet" href="style.css">', '<link rel="stylesheet" href="style.css">\n' + INC_CSS, 1)
        if INC_JS not in s and "</body>" in s and ('<script src="site.js"></script>' in s or '<script src="content.js"></script>' in s):
            s = s.replace("</body>", INC_JS + "\n</body>", 1)
        if s != o:
            f.write_text(s); n += 1
    return n


def write_site_extras(repo, site, photos, cover_pool, site_url, log):
    site = site if isinstance(site, dict) else {}
    (repo / "site-settings.css").write_text(css(site.get("style")))
    (repo / "site-text.js").write_text(text_js(site.get("text")))
    work, index = repo / "work.html", repo / "index.html"
    c = site.get("cover") or {}
    if c.get("on"):
        index.write_text(cover_html(c, [p for p in cover_pool if p.get("src")], site_url, repo))
        mode = f"cover on ({min(24, len(cover_pool))} photos)"
    elif work.exists():
        index.write_text(work.read_text()); mode = "cover off (index.html = portfolio)"
    else:
        mode = "cover off"
    n = ensure_includes(repo, skip=("index.html",) if c.get("on") else ())
    log(f"  site settings: style + text written, {mode}" + (f", includes added to {n} pages" if n else ""))
