# -*- coding: utf-8 -*-
"""Build labeled contact sheets from downloaded candidate images for visual verification."""
import os, json, math
from PIL import Image, ImageDraw, ImageFont, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
from content import ITEMS

BUILD = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BUILD, "raw")
OUT = os.path.join(BUILD, "sheets")
os.makedirs(OUT, exist_ok=True)
cand = json.load(open(os.path.join(BUILD, "candidates.json"))) if os.path.exists(os.path.join(BUILD,"candidates.json")) else {}

FONT = None
for fp in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
    if os.path.exists(fp):
        FONT = fp; break
def font(sz):
    try: return ImageFont.truetype(FONT, sz)
    except Exception: return ImageFont.load_default()

CELL_W, IMG_H, LBL_H, COLS, PER = 380, 250, 48, 3, 12
subspots = [s for it in ITEMS for s in it["subspots"]]

def load_thumb(sid):
    p = os.path.join(RAW, sid + ".img")
    if not os.path.exists(p) or os.path.getsize(p) < 2000: return None
    try:
        im = Image.open(p).convert("RGB"); im.thumbnail((CELL_W - 12, IMG_H - 12)); return im
    except Exception: return None

pages = [subspots[i:i + PER] for i in range(0, len(subspots), PER)]
for pi, group in enumerate(pages, 1):
    rows = math.ceil(len(group) / COLS)
    sheet = Image.new("RGB", (COLS * CELL_W, rows * (IMG_H + LBL_H)), (22, 22, 26))
    d = ImageDraw.Draw(sheet)
    for k, s in enumerate(group):
        r, c = divmod(k, COLS)
        x0, y0 = c * CELL_W, r * (IMG_H + LBL_H)
        im = load_thumb(s["id"])
        cinfo = cand.get(s["id"], {}).get("cands") or []
        ctitle = (cinfo[0].get("title", "NONE") if cinfo else "NONE").replace("File:", "")
        if im:
            sheet.paste(im, (x0 + (CELL_W - im.width) // 2, y0 + (IMG_H - im.height) // 2))
        else:
            d.rectangle([x0 + 6, y0 + 6, x0 + CELL_W - 6, y0 + IMG_H - 6], outline=(200, 80, 80), width=2)
            d.text((x0 + 20, y0 + IMG_H // 2 - 10), "NO IMAGE", font=font(20), fill=(230, 120, 120))
        d.text((x0 + 8, y0 + IMG_H + 3), f"{s['id']}  {s['en']}", font=font(19), fill=(255, 232, 140))
        d.text((x0 + 8, y0 + IMG_H + 26), ctitle[:56], font=font(13), fill=(175, 175, 188))
    out = os.path.join(OUT, f"sheet_{pi}.jpg")
    sheet.save(out, "JPEG", quality=82)
    print("wrote", out, sheet.size)
