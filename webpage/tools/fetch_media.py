# -*- coding: utf-8 -*-
"""Encode downloaded raw images -> WebP data URIs; fetch+encode Bilibili covers; collect Commons credits.
Outputs media.json + credits.json."""
import os, sys, json, base64, io, subprocess, urllib.parse, re
from PIL import Image, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # webpage/
sys.path.insert(0, os.path.join(ROOT, "src"))
import content as C

DATA = os.path.join(ROOT, "data")
ASSETS = os.path.join(ROOT, "assets")
RAW = os.path.join(ASSETS, "raw")
VRAW = os.path.join(ASSETS, "vraw"); os.makedirs(VRAW, exist_ok=True)
UA = "BaliTripPlanner/1.0 (personal trip research; mail2zhangly@gmail.com)"
cand = json.load(open(os.path.join(ASSETS, "candidates.json"), encoding="utf-8"))
videos = json.load(open(os.path.join(DATA, "videos.json"), encoding="utf-8"))

def curl(url, out, timeout=45):
    subprocess.run(["curl","-s","--max-time",str(timeout),"-A",UA,"-L","--retry","2","-o",out,url])
    return os.path.exists(out) and os.path.getsize(out) > 2000

def webp(path, maxw=850, maxh=850, q=68):
    im = Image.open(path).convert("RGB")
    im.thumbnail((maxw, maxh))
    buf = io.BytesIO(); im.save(buf, "WEBP", quality=q, method=6)
    return buf.getvalue()

def uri(b): return "data:image/webp;base64," + base64.b64encode(b).decode()

media, sizes = {}, {}
_mediap = os.path.join(DATA, "media.json")
if os.path.exists(_mediap):
    try: media = json.load(open(_mediap, encoding="utf-8"))
    except Exception: media = {}
subspots = [s for it in C.ITEMS for s in it["subspots"]]
miss = []
for s in subspots:
    p = os.path.join(RAW, s["id"] + ".img")
    if os.path.exists(p) and os.path.getsize(p) > 2000:
        try:
            b = webp(p); media[s["id"]] = uri(b); sizes[s["id"]] = len(b)
        except Exception as e:
            print("IMG ERR", s["id"], e); miss.append(s["id"])
    else:
        miss.append(s["id"])

BILI_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
for iid, v in videos.items():
    bvid = v.get("bvid", "")
    out = os.path.join(VRAW, iid + ".jpg")
    if not bvid:
        print("VID NOBVID", iid); continue
    api = "https://api.bilibili.com/x/web-interface/view?bvid=" + bvid
    r = subprocess.run(["curl", "-s", "--max-time", "20", "-A", BILI_UA,
                        "-H", "Referer: https://www.bilibili.com", api], capture_output=True)
    pic = ""
    try:
        dj = json.loads(r.stdout)
        pic = (dj.get("data") or {}).get("pic", "") if dj.get("code") == 0 else ""
    except Exception as e:
        print("VID API ERR", iid, e)
    ok = False
    if pic:
        pic = pic.replace("http://", "https://", 1)
        subprocess.run(["curl", "-s", "--max-time", "30", "-A", BILI_UA,
                        "-H", "Referer: https://www.bilibili.com", "-L", "-o", out, pic])
        ok = os.path.exists(out) and os.path.getsize(out) > 2000
    if ok:
        try:
            b = webp(out, 640, 640, 66); media["vid:"+iid] = uri(b); sizes["vid:"+iid] = len(b)
        except Exception as e: print("VID ERR", iid, e)
    else: print("VID MISS", iid, bvid)

json.dump(media, open(os.path.join(DATA, "media.json"), "w", encoding="utf-8"))

# credits: one batched Commons call for chosen titles
def strip(x): return re.sub("<[^>]+>", "", x or "").replace("\n"," ").strip()
titles = {}
for s in subspots:
    cs = cand.get(s["id"], {}).get("cands") or []
    if cs and s["id"] in media: titles[s["id"]] = cs[0]["title"]
_credp = os.path.join(DATA, "credits.json")
creds = {}
if os.path.exists(_credp):
    try: creds = json.load(open(_credp, encoding="utf-8"))
    except Exception: creds = {}
tl = list(titles.items())
for i in range(0, len(tl), 40):
    grp = tl[i:i+40]
    q = {"action":"query","titles":"|".join(t for _,t in grp),"prop":"imageinfo","iiprop":"extmetadata","format":"json"}
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(q)
    r = subprocess.run(["curl","-s","--max-time","40","-A",UA,url], capture_output=True)
    try:
        pages = json.loads(r.stdout).get("query", {}).get("pages", {})
        by = {p.get("title"): p for p in pages.values()}
        for sid, t in grp:
            p = by.get(t)
            if not p: continue
            em = (p.get("imageinfo", [{}])[0].get("extmetadata") or {})
            creds[sid] = {"artist": strip(em.get("Artist", {}).get("value","")),
                          "license": strip(em.get("LicenseShortName", {}).get("value",""))}
    except Exception as e:
        print("CRED ERR", e)
json.dump(creds, open(_credp, "w", encoding="utf-8"), ensure_ascii=False)

tot = sum(sizes.values())
print(f"media: {len(media)} items | webp {tot/1024:.0f} KB | ~b64 {tot*1.34/1024:.0f} KB | credits {len(creds)}")
print("MISSING images:", miss)
print("largest:", [(k, f"{v//1024}KB") for k, v in sorted(sizes.items(), key=lambda x:-x[1])[:6]])
