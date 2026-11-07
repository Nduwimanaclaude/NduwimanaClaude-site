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
A date at the front is optional and only used for sorting (never shown):
    "2026-06-13 - Title - Place.jpg"
Prefixes (optional, can be combined, any order, after the date if there is one):
    "hero - ..."   use this photo as the big homepage photo
    "cover - ..."  use this photo as its collection's cover on the homepage
Place format: US = "City, ST"; abroad = "City, Country".

Rules:
  * Deleting a file from a folder removes it from the site.
  * Newest photos show first: date in the name, else the camera's shoot
    date, else the file's modified date.
  * Camera settings (camera, lens, focal length, aperture, shutter, ISO) are
    shown under each photo. GPS and the exact time are never published.
    Hide them for one photo with "hide_specs": ["Title"] in _settings.json.
  * Public copies get a small "Nduwimana Claude" mark in the bottom right
    (WATERMARK=0 in config.env turns it off). Originals are never touched.
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

import io

import base64

from PIL import Image, ImageCms, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageStat

HERE = Path(__file__).resolve().parent


# ---------------------------------------------------------------- config ---
def load_config():
    cfg = {
        "WEBSITE_DIR": "/mnt/nas-website",
        "REPO_DIR": str(Path.home() / "nduwimanaclaude-site"),
        "SITE_URL": "https://nduwimanaclaude.com",
        "MAX_EDGE": "2400",
        "JPEG_QUALITY": "86",
        "GIT_PUSH": "1",
        "WATERMARK": "1",
        "WATERMARK_TEXT": "Nduwimana Claude",
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
MAX_EDGE = int(CFG["MAX_EDGE"])          # full-size (lightbox, big screens)
SMALL_EDGE = int(CFG.get("SMALL_EDGE", "1200"))  # grids, covers, phones
QUALITY = int(CFG["JPEG_QUALITY"])
MAX_BYTES = {"full": 1_500_000, "small": 450_000}  # size guard per file
MIN_QUALITY = 72
PIPELINE_VERSION = "v3"  # bump to re-process every photo with new settings
WATERMARK = CFG["WATERMARK"] == "1"
WM_TEXT = CFG["WATERMARK_TEXT"]
WM_FONT = HERE / "fonts" / "Inter-Medium.otf"
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
DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})(?:[ _](\d{2})(\d{2})(\d{2}))?\s*-\s*")


def parse_date(stem):
    """'2026-06-13 - ...' -> (timestamp, rest). No date -> (None, stem)."""
    m = DATE_RE.match(stem)
    if not m:
        return None, stem
    try:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        hh, mm, ss = (int(m.group(i) or 0) for i in (4, 5, 6))
        return datetime(y, mo, d, hh, mm, ss).timestamp(), stem[m.end():]
    except ValueError:
        return None, stem


def parse_name(stem):
    _, stem = parse_date(stem)
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
SRGB = ImageCms.createProfile("sRGB")
SRGB_ICC = ImageCms.ImageCmsProfile(SRGB).tobytes()


def to_srgb(im):
    """Convert from whatever color space the export used (Display P3, Adobe RGB...)
    to sRGB so colors look the same in every browser."""
    icc = im.info.get("icc_profile")
    if icc:
        try:
            src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
            if im.mode not in ("RGB", "CMYK"):
                im = im.convert("RGB")
            return ImageCms.profileToProfile(im, src, SRGB, outputMode="RGB",
                                             renderingIntent=0)  # 0 = perceptual
        except Exception as e:
            log(f"    (color profile unreadable, assuming sRGB: {e})")
    return im.convert("RGB")


def luminance(im):
    """Average brightness 0..1 (Rec. 709 weights on sRGB values)."""
    r, g, b = ImageStat.Stat(im.convert("RGB")).mean
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255


def watermark(im):
    """Small name in the bottom-right corner; black on bright corners, white on dark."""
    if not WATERMARK or not WM_TEXT:
        return im
    w, h = im.size
    size = max(11, round(max(w, h) * 0.016))
    try:
        font = ImageFont.truetype(str(WM_FONT), size)
    except Exception:
        font = ImageFont.load_default()
    draw0 = ImageDraw.Draw(im)
    l, t, r, b = draw0.textbbox((0, 0), WM_TEXT, font=font)
    tw, th = r - l, b - t
    margin = max(8, round(max(w, h) * 0.018))
    x, y = w - margin - tw, h - margin - th
    if x < 0 or y < 0:
        return im
    corner = im.crop((max(0, x - 6), max(0, y - 6), min(w, x + tw + 6), min(h, y + th + 6)))
    ink = (0, 0, 0) if luminance(corner) > 0.62 else (255, 255, 255)
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((x - l, y - t), WM_TEXT, font=font, fill=ink + (140,))
    return Image.alpha_composite(im.convert("RGBA"), layer).convert("RGB")


def save_sized(im, dest, edge, budget):
    w, h = im.size
    scale = min(1.0, edge / max(w, h))
    out = im.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS) if scale < 1 else im.copy()
    if scale < 1:  # light "sharpen for screen" after downsizing
        out = out.filter(ImageFilter.UnsharpMask(radius=0.6 if edge <= 1400 else 0.8, percent=55, threshold=2))
    out = watermark(out)
    q = QUALITY
    while True:
        buf = io.BytesIO()
        # subsampling=0 keeps full color detail (crisp reds/oranges, signs, sunsets).
        # Only the sRGB profile is embedded; GPS and all other metadata are dropped.
        out.save(buf, "JPEG", quality=q, subsampling=0, optimize=True, progressive=True, icc_profile=SRGB_ICC)
        if buf.tell() <= budget or q <= MIN_QUALITY:
            break
        q -= 3
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(buf.getvalue())
    return out.size


def process_image(src, dest_full, dest_small):
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)          # respect camera rotation
        im = to_srgb(im)
        size = save_sized(im, dest_full, MAX_EDGE, MAX_BYTES["full"])
        save_sized(im, dest_small, SMALL_EDGE, MAX_BYTES["small"])
        return size


def preview_info(path):
    """From a published copy: tiny blurred preview (data URI) for blur-up loading,
    and whether text over its middle should be dark (bright photo) or light."""
    with Image.open(path) as im:
        im = im.convert("RGB")
        w, h = im.size
        tiny = im.copy()
        tiny.thumbnail((20, 20))
        buf = io.BytesIO()
        tiny.save(buf, "JPEG", quality=55)
        lqip = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
        band = im.crop((round(w * 0.15), round(h * 0.38), round(w * 0.85), round(h * 0.72)))
        ink = "dark" if luminance(band) > 0.6 else "light"
    return lqip, ink


# ---------------------------------------------------------- camera info ---
def _num(v):
    try:
        return float(v)
    except Exception:
        return None


def read_exif(src):
    """Shoot time (for sorting only) + public camera settings. Never GPS."""
    try:
        with Image.open(src) as im:
            ex = im.getexif()
            sub = ex.get_ifd(0x8769)
    except Exception:
        return None, {}
    shot = None
    dto = sub.get(0x9003) or ex.get(0x0132)
    if dto:
        try:
            shot = datetime.strptime(str(dto).strip()[:19], "%Y:%m:%d %H:%M:%S").timestamp()
        except ValueError:
            pass
    make = str(ex.get(0x010F) or "").strip()
    model = str(ex.get(0x0110) or "").strip()
    model = re.sub(r"m2$", " Mark II", re.sub(r"m3$", " Mark III", model))
    if make.lower() == "apple":
        camera = model
    elif model and make and not model.lower().startswith(make.split()[0].lower()):
        camera = f"{make} {model}"
    else:
        camera = model
    specs = {}
    if camera:
        specs["camera"] = camera
    lens = str(sub.get(0xA434) or "").strip()
    if lens and model and model.lower() not in lens.lower():
        specs["lens"] = lens
    f35, fl = _num(sub.get(0xA405)), _num(sub.get(0x920A))
    if make.lower() == "apple" and f35:
        specs["focal"] = f"{round(f35)}mm"
    elif fl:
        specs["focal"] = f"{round(fl)}mm"
    fn = _num(sub.get(0x829D))
    if fn:
        specs["aperture"] = f"f/{fn:.1f}".replace(".0", "")
    et = _num(sub.get(0x829A))
    if et:
        specs["shutter"] = f"1/{round(1 / et)}s" if et < 0.5 else f"{et:g}s"
    iso = sub.get(0x8827) or sub.get(0x8832) or sub.get(0x8831)
    if isinstance(iso, (tuple, list)):
        iso = iso[0] if iso else None
    if iso:
        specs["iso"] = f"ISO {int(iso)}"
    return shot, specs


def build(state):
    photos_dir = REPO / "photos"
    photos_dir.mkdir(exist_ok=True)
    focus = state["settings"].get("focus", {})
    blurbs = {**DEFAULT_BLURBS, **state["settings"].get("blurbs", {})}

    hide_specs = set(state["settings"].get("hide_specs", []))
    photos, keep, used = [], set(), set()
    for it in state["items"]:
        named, _ = parse_date(it["path"].stem)
        it["shot"], it["specs"] = read_exif(it["path"])
        it["when"] = named or it["shot"] or it["mtime"]
    items = sorted(state["items"], key=lambda x: (-x["when"], x["path"].name.lower()))
    for it in items:
        title, place, flags = parse_name(it["path"].stem)
        digest = hashlib.sha1(f'{PIPELINE_VERSION}|{MAX_EDGE}|{SMALL_EDGE}|{QUALITY}|{it["path"].relative_to(WEBSITE)}|{it["size"]}|{it["mtime"]}'.encode()).hexdigest()[:8]
        base = f'{slugify(it["set"])}-{slugify(title)}'
        name = f"{base}-{digest}.jpg"
        while name in used:
            name = f"{base}-{digest}{len(used)}.jpg"
        used.add(name)
        small = name[:-4] + "-s.jpg"
        dest, dest_small = photos_dir / name, photos_dir / small
        if not (dest.exists() and dest_small.exists()):
            try:
                w, h = process_image(it["path"], dest, dest_small)
                log(f"  + {it['set']}/{it['path'].name}")
            except Exception as e:
                log(f"  ! skipped {it['path'].name}: {e}")
                continue
        else:
            with Image.open(dest) as im:
                w, h = im.size
        keep.update({name, small})
        p = {"src": f"photos/{name}", "srcSmall": f"photos/{small}", "title": title, "place": place,
             "set": it["set"], "ratio": round(w / h, 3)}
        try:
            p["lqip"], p["ink"] = preview_info(dest_small)
        except Exception as e:
            log(f"    (no preview for {name}: {e})")
        if it["specs"] and title not in hide_specs:
            p["specs"] = it["specs"]
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
    keep.add("og.jpg")
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

    try:
        write_og_image(photos, photos_dir)
    except Exception as e:
        log(f"  (share preview image skipped: {e})")
    write_photos_js(photos, sets, covers, {s: blurbs.get(s, "") for s in sets})
    write_collection_pages(sets, blurbs)
    write_sitemap(sets)
    return True


def write_og_image(photos, photos_dir):
    """1200x630 crop of the homepage photo at a fixed URL, for link previews."""
    hero = next(p for p in photos if p.get("featured"))
    with Image.open(REPO / hero["src"]) as im:
        im = ImageOps.fit(im.convert("RGB"), (1200, 630), Image.LANCZOS)
        im.save(photos_dir / "og.jpg", "JPEG", quality=82, optimize=True, progressive=True, icc_profile=SRGB_ICC)


def write_photos_js(photos, sets, covers, blurbs):
    # "ink" is only needed for collection covers (text sits on top of them)
    cover_ids = {(s, t) for s, t in covers.items()}
    def pub(p):
        d = {k: v for k, v in p.items() if k not in ("cover", "ink")}
        if (p["set"], p["title"]) in cover_ids and "ink" in p:
            d["ink"] = p["ink"]
        return d
    lines = ",\n".join("  " + js(pub(p)) for p in photos)
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
<meta property="og:type" content="website">
<meta property="og:title" content="{name} · Nduwimana Claude">
<meta property="og:description" content="{name} photographs by Nduwimana Claude.">
<meta property="og:image" content="{site}/photos/og.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
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
  <div class="jgrid" id="gallery"></div>
</div>
</main>
<script src="photos.js"></script>
<script src="content.js"></script>
<script src="site.js"></script>
</body>
</html>
"""

RESERVED = {"index", "about", "journal", "contact", "now", "links", "404", "tools", "photos", "content", "site", "style", "sitemap", "robots", "favicon", "apple-touch-icon"}


def write_collection_pages(sets, blurbs):
    manifest_f = REPO / "tools" / ".generated-pages.json"
    old = set(json.loads(manifest_f.read_text())) if manifest_f.exists() else {"places.html", "people.html", "streets.html"}
    new = set()
    for s in sets:
        slug = slugify(s)
        if slug in RESERVED:
            slug = f"{slug}-photos"
        fn = f"{slug}.html"
        (REPO / fn).write_text(PAGE_TMPL.format(name=html_escape(s), slug=slug, blurb=html_escape(blurbs.get(s, "")), site=CFG["SITE_URL"]))
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
    pages = [""] + [slugify(s) if slugify(s) not in RESERVED else slugify(s) + "-photos" for s in sets] + ["about", "journal", "now", "contact", "sitemap"]
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
def self_update():
    """If a newer publisher is on GitHub, switch to it and restart (so code
    updates take effect even when no photos changed)."""
    if CFG["GIT_PUSH"] != "1" or os.environ.get("PUBLISH_UPDATED"):
        return
    if git("fetch", "-q", "origin", check=False).returncode != 0:
        return  # offline; try next run
    remote = git("show", "origin/main:tools/publish.py", check=False)
    if remote.returncode == 0 and remote.stdout != (HERE / "publish.py").read_text():
        log("New publisher version on GitHub; updating.")
        git("reset", "-q", "--hard", "origin/main")
        os.environ["PUBLISH_UPDATED"] = "1"
        os.execv(sys.executable, [sys.executable, str(HERE / "publish.py"), *sys.argv[1:]])


def main():
    lock = open(HERE / ".publish.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return  # another run is still going
    try:
        self_update()
    except Exception as e:
        log(f"(update check skipped: {e})")
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
