# -*- coding: utf-8 -*-
"""Apply user-curated review images into media.json + credits.json.

For each subspot with kept images in review/<id>/, pick the lowest-numbered kept
file (user did NOT delete it = acceptable; lowest rank = best match), encode to
high-quality WebP (1280px, q82), write into media.json + credits.json.
Subspots with 0 kept keep their existing (old) image. Preserves vid:* covers.

    python apply_review.py
"""
import os, json, base64, io
from PIL import Image, ImageFile, ImageOps
ImageFile.LOAD_TRUNCATED_IMAGES = True
from content import ITEMS

BUILD = os.path.dirname(os.path.abspath(__file__))
REVIEW = os.path.join(BUILD, "review")
MEDIA_P = os.path.join(BUILD, "media.json")
CRED_P = os.path.join(BUILD, "credits.json")
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".tif", ".tiff")

media = json.load(open(MEDIA_P, encoding="utf-8"))
creds = json.load(open(CRED_P, encoding="utf-8"))

def webp(path, maxw=1280, maxh=1280, q=82):
    im = Image.open(path)
    try:
        im = ImageOps.exif_transpose(im)
    except Exception:
        pass
    if im.mode != "RGB":
        im = im.convert("RGB")
    im.thumbnail((maxw, maxh))
    buf = io.BytesIO(); im.save(buf, "WEBP", quality=q, method=6)
    return buf.getvalue()

def uri(b):
    return "data:image/webp;base64," + base64.b64encode(b).decode()

subspots = [s for it in ITEMS for s in it["subspots"]]
updated, kept_old, no_folder = [], [], []
for s in subspots:
    sid = s["id"]
    fd = os.path.join(REVIEW, sid)
    if not os.path.isdir(fd):
        no_folder.append(sid); continue
    imgs = sorted(f for f in os.listdir(fd) if f.lower().endswith(IMG_EXT))
    if not imgs:
        kept_old.append(sid); continue
    chosen = imgs[0]
    meta = {}
    mp = os.path.join(fd, "metadata.json")
    if os.path.exists(mp):
        try:
            meta = {f["file"]: f for f in json.load(open(mp, encoding="utf-8")).get("files", [])}
        except Exception:
            meta = {}
    m = meta.get(chosen, {})
    try:
        b = webp(os.path.join(fd, chosen))
        media[sid] = uri(b)
    except Exception as e:
        print("ENC ERR", sid, chosen, e); kept_old.append(sid); continue
    artist = (m.get("artist", "") or "").strip() or m.get("source", "")
    lic = (m.get("license", "") or "").strip()
    src = m.get("source", "")
    url = m.get("foreign_url", "") or m.get("orig", "")
    creds[sid] = {"artist": artist, "license": lic, "source": src, "url": url}
    updated.append((sid, chosen, src, artist, len(b)//1024))

json.dump(media, open(MEDIA_P, "w", encoding="utf-8"))
json.dump(creds, open(CRED_P, "w", encoding="utf-8"), ensure_ascii=False)

print(f"\n=== updated {len(updated)} subspots with new images ===")
for sid, fn, src, art, kb in updated:
    print(f"  {sid}: {fn} [{src}] {art[:32]} ({kb}KB webp)")
print(f"\nkept OLD image (0 kept by user): {kept_old}")
print(f"no review folder: {no_folder}")
