#!/usr/bin/env python3
"""
Drop-folder publisher for nduwimanaclaude.com

Watches a "Website" folder (on the NAS) that has one subfolder per collection:

    Website/
      Places/
      People/
      Streets/
      _settings.json      (optional)

and turns whatever is in there into the site's photo pages, then pushes to
GitHub so Cloudflare Pages publishes it.

File name = caption:
    "Thor's Hammer - Bryce Canyon, UT.jpg"   -> title "Thor's Hammer", place "Bryce Canyon, UT"
    "Blue hour.jpg"                          -> title "Blue hour", no place
Prefixes (optional, can be combined, any order):
    "hero - ..."   use this photo as the big homepage photo
    "cover - ..."  use this photo as its collection's cover on the homepage

Rules:
  * Deleting a file from a folder removes it from the site.
  * Newest files (by modified date) show first in each collection.
  * A new folder becomes a new collection page automatically.
  * Folders starting with "_" or "." are ignored (good for drafts: "_drafts").
  * Safety: if the Website folder is missing or has zero photos (NAS not
    mounted, etc.), nothing is changed.

Run it with no arguments; settings live in config.env next to this file.
"""

import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageOps

HERE = Path(__file__).resolve().parent


# ---------------------------------------------------------------- config ---
def load_config():
    cfg = {
        "WEBSITE_DIR": "/mnt/nas-website",
        "REPO_DIR": str(Path.home() / "nduwimanaclaude-site"),
        "SITE_URL": "https://nduwimanaclaude.com",
        "MAX_EDGE": "2400",
        "JPEG_QUALITY": "82",
        "GIT_PUSH": "1",
    }
    f = HERE / "config.env"
    if f.exists():
        for line in f.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip().strip('"').strip("'")
    for k in list(cfg):  # environment wins (handy for testing)
        if os.environ.get(k):
            cfg[k] = os.environ[k]
    return cfg


CFG = load_config()
WEBSITE = Path(CFG["WEBSITE_DIR"])
REPO = Path(CFG["REPO_DIR"])
MAX_EDGE = int(CFG["MAX_EDGE"])
QUALITY = int(CFG["JPEG_QUALITY"])
IMG_EXT = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}

DEFAULT_ORDER = ["Places", "People", "Streets"]
DEFAULT_BLURBS = {
    "Places": "Landscapes, rivers, parks, and the quiet edges of cities.",
    "People": "Friends, strangers, and the moments in between.",
    "Streets": "Walls, corners, storefronts, and weather.",
}


def log(msg):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}", flush=True)


def slugify(s):
    s = s.lower().replace("'", "").replace("’", "")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "photo"


def js(v):
    return json.dumps(v, ensure_ascii=False)


def html_escape(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


# ------------------------------------------------------------ parse names ---
PREFIX_RE = re.compile(r"^(hero|cover)\s*-\s*", re.I)


def parse_name(stem):
    flags = set()
    while True:
        m = PREFIX_RE.match(stem)
        if not m:
            break
        flags.add(m.group(1).lower())
        stem = stem[m.end():]
    stem = stem.replace("_", " ").strip()
    if " - " in stem:
        title, place = stem.split(" - ", 1)
    else:
        title, place = stem, ""
    return title.strip() or "Untitled", place.strip(), flags


# --------------------------------------------------------------- scanning ---
def scan():
    if not WEBSITE.is_dir():
        log(f"Website folder not found at {WEBSITE}. Is the NAS mounted? Doing nothing.")
        return None
    settings = {}
    sf = WEBSITE / "_settings.json"
    if sf.exists():
        try:
            settings = json.loads(sf.read_text())
        except Exception as e:
            log(f"Couldn't read _settings.json ({e}); ignoring it.")
    cats = [d for d in WEBSITE.iterdir()
            if d.is_dir() and not d.name.startswith(("_", ".", "@", "#"))]
    order = settings.get("order") or DEFAULT_ORDER
    cats.sort(key=lambda d: (order.index(d.name) if d.name in order else len(order), d.name.lower()))
    items = []
    for d in cats:
        for f in d.iterdir():
            if f.is_file() and f.suffix.lower() in IMG_EXT and not f.name.startswith((".", "_")):
                st = f.stat()
                items.append({"path": f, "set": d.name, "mtime": st.st_mtime, "size": st.st_size})
    return {"cats": [d.name for d in cats], "items": items, "settings": settings}


def fingerprint(state):
    h = hashlib.sha256()
    h.update(js(state["settings"]).encode())
    h.update(js(state["cats"]).encode())
    for it in sorted(state["items"], key=lambda x: str(x["path"])):
        h.update(f'{it["path"].relative_to(WEBSITE)}|{it["mtime"]}|{it["size"]}\n'.encode())
    h.update((HERE / "publish.py").read_bytes())
    return h.hexdigest()


# ------------------------------------------------------------ processing ---
def process_image(src, dest):
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)          # respect camera rotation
        im = im.convert("RGB")
        im.thumbnail((MAX_EDGE, MAX_EDGE), Image.LANCZOS)
        dest.parent.mkdir(parents=True, exist_ok=True)
        # No exif/icc passed in -> GPS and all other metadata are stripped.
        im.save(dest, "JPEG", quality=QUALITY, optimize=True, progressive=True)
        return im.size


def build(state):
    photos_dir = REPO / "photos"
    photos_dir.mkdir(exist_ok=True)
    focus = state["settings"].get("focus", {})
    blurbs = {**DEFAULT_BLURBS, **state["settings"].get("blurbs", {})}

    photos, keep, used = [], set(), set()
    items = sorted(state["items"], key=lambda x: (-x["mtime"], x["path"].name.lower()))
    for it in items:
        title, place, flags = parse_name(it["path"].stem)
        digest = hashlib.sha1(f'{it["path"].relative_to(WEBSITE)}|{it["size"]}|{it["mtime"]}'.encode()).hexdigest()[:8]
        base = f'{slugify(it["set"])}-{slugify(title)}'
        name = f"{base}-{digest}.jpg"
        while name in used:
            name = f"{base}-{digest}{len(used)}.jpg"
        used.add(name)
        dest = photos_dir / name
        if not dest.exists():
            try:
                w, h = process_image(it["path"], dest)
                log(f"  + {it['set']}/{it['path'].name}")
            except Exception as e:
                log(f"  ! skipped {it['path'].name}: {e}")
                continue
        else:
            with Image.open(dest) as im:
                w, h = im.size
        keep.add(name)
        p = {"src": f"photos/{name}", "title": title, "place": place,
             "set": it["set"], "ratio": round(w / h, 3)}
        if title in focus:
            p["focus"] = focus[title]
        if "hero" in flags:
            p["featured"] = True
        if "cover" in flags:
            p["cover"] = True
        photos.append(p)

    if not photos:
        log("Found zero photos in the Website folders. Refusing to wipe the site.")
        return False

    # remove photos that are no longer in the folders
    for f in photos_dir.iterdir():
        if f.is_file() and f.name not in keep:
            f.unlink()
            log(f"  - removed {f.name}")

    sets = [c for c in state["cats"] if any(p["set"] == c for p in photos)]
    covers = {}
    for s in sets:
        c = next((p for p in photos if p["set"] == s and p.get("cover")), None) \
            or next(p for p in photos if p["set"] == s)
        covers[s] = c["title"]
    if not any(p.get("featured") for p in photos):
        land = next((p for p in photos if p["ratio"] >= 1.3), photos[0])
        land["featured"] = True
    else:  # only the newest "hero" wins
        seen = False
        for p in photos:
            if p.get("featured"):
                if seen:
                    p.pop("featured")
                seen = True

    write_photos_js(photos, sets, covers, {s: blurbs.get(s, "") for s in sets})
    write_collection_pages(sets, blurbs)
    write_sitemap(sets)
    return True


def write_photos_js(photos, sets, covers, blurbs):
    lines = ",\n".join("  " + js({k: v for k, v in p.items() if k != "cover"}) for p in photos)
    out = f"""/* ============================================================
   GENERATED FILE. Don't edit by hand: it's rebuilt from the
   Website folders on the NAS every few minutes.
   To change photos, add/remove/rename files in those folders.
   Last built: {datetime.now():%Y-%m-%d %H:%M}
   ============================================================ */
const SETS = {js(sets)};
const BLURBS = {js(blurbs)};
const COVERS = {js(covers)};
const PHOTOS = [
{lines}
];
"""
    (REPO / "photos.js").write_text(out)


PAGE_TMPL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name} · Nduwimana Claude</title>
<meta name="description" content="{name} photographs by Nduwimana Claude.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;1,400&family=Inter:wght@300;400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="style.css">
</head>
<body data-page="{slug}">
<!-- generated collection page -->
<main>
<div class="wrap page-head">
  <div class="label">Collection</div>
  <h1>{name}</h1>
  <p>{blurb}</p>
</div>
<div class="wrap">
  <div class="tabs" id="tabs"></div>
  <div class="gallery" id="gallery"></div>
</div>
</main>
<script src="photos.js"></script>
<script src="content.js"></script>
<script src="site.js"></script>
</body>
</html>
"""

RESERVED = {"index", "about", "journal", "contact", "404", "tools", "photos", "content", "site", "style", "sitemap", "robots"}


def write_collection_pages(sets, blurbs):
    manifest_f = REPO / "tools" / ".generated-pages.json"
    old = set(json.loads(manifest_f.read_text())) if manifest_f.exists() else {"places.html", "people.html", "streets.html"}
    new = set()
    for s in sets:
        slug = slugify(s)
        if slug in RESERVED:
            slug = f"{slug}-photos"
        fn = f"{slug}.html"
        (REPO / fn).write_text(PAGE_TMPL.format(name=html_escape(s), slug=slug, blurb=html_escape(blurbs.get(s, ""))))
        new.add(fn)
    for fn in old - new:
        f = REPO / fn
        if f.exists() and ("<!-- generated collection page -->" in f.read_text()
                           or fn in {"places.html", "people.html", "streets.html"}):
            f.unlink()
            log(f"  - removed page {fn}")
    manifest_f.write_text(json.dumps(sorted(new)))


def write_sitemap(sets):
    today = datetime.now().strftime("%Y-%m-%d")
    pages = [""] + [slugify(s) if slugify(s) not in RESERVED else slugify(s) + "-photos" for s in sets] + ["about", "journal", "contact"]
    urls = "\n".join(f"  <url><loc>{CFG['SITE_URL']}/{p}</loc><lastmod>{today}</lastmod></url>" for p in pages)
    (REPO / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>\n')


# ------------------------------------------------------------------- git ---
def git(*args, check=True):
    return subprocess.run(["git", "-C", str(REPO), *args], check=check, capture_output=True, text=True)


def sync_repo():
    if CFG["GIT_PUSH"] != "1":
        return
    git("fetch", "-q", "origin")
    git("reset", "-q", "--hard", "origin/main")  # the folders are the source of truth for photos


def commit_and_push(n):
    git("add", "-A")
    if not git("status", "--porcelain").stdout.strip():
        log("No changes to publish.")
        return
    git("commit", "-q", "-m", f"Update photos from NAS ({n} photos)")
    if CFG["GIT_PUSH"] == "1":
        git("push", "-q", "origin", "HEAD:main")
        log("Pushed. Cloudflare will publish in about a minute.")
    else:
        log("Committed locally (GIT_PUSH=0).")


# ------------------------------------------------------------------ main ---
def main():
    lock = open(HERE / ".publish.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return  # another run is still going
    force = "--force" in sys.argv
    state = scan()
    if state is None:
        return
    stamp_f = HERE / ".last-fingerprint"
    fp = fingerprint(state)
    if not force and stamp_f.exists() and stamp_f.read_text() == fp:
        return  # nothing changed since last run
    # wait for files still being copied (size settling)
    time.sleep(0 if force else 5)
    state2 = scan()
    if state2 is None or fingerprint(state2) != fp:
        log("Files still changing; will try again next run.")
        return
    log(f"Change detected: {len(state['items'])} photos in {len(state['cats'])} folders.")
    sync_repo()
    if build(state):
        commit_and_push(len(state["items"]))
        stamp_f.write_text(fp)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        log(f"git error: {e.stderr.strip() or e}")
        sys.exit(1)
