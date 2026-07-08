# -*- coding: utf-8 -*-
"""Encode downloaded raw images -> WebP data URIs; fetch+encode YouTube covers; collect Commons credits.
Outputs media.json + credits.json."""
import os, json, base64, io, subprocess, urllib.parse, re
from PIL import Image, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
import content as C

BUILD = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BUILD, "raw")
VRAW = os.path.join(BUILD, "vraw"); os.makedirs(VRAW, exist_ok=True)
UA = "BaliTripPlanner/1.0 (personal trip research; mail2zhangly@gmail.com)"
cand = json.load(open(os.path.join(BUILD, "candidates.json")))
videos = json.load(open(os.path.join(BUILD, "videos.json")))

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

for iid, v in videos.items():
    yid = v["yt_id"]; out = os.path.join(VRAW, iid + ".jpg")
    ok = curl(f"https://img.youtube.com/vi/{yid}/maxresdefault.jpg", out)
    if not ok or os.path.getsize(out) < 9000:
        ok = curl(f"https://img.youtube.com/vi/{yid}/hqdefault.jpg", out)
    if ok:
        try:
            b = webp(out, 640, 640, 66); media["vid:"+iid] = uri(b); sizes["vid:"+iid] = len(b)
        except Exception as e: print("VID ERR", iid, e)
    else: print("VID MISS", iid)

json.dump(media, open(os.path.join(BUILD, "media.json"), "w"))

# credits: one batched Commons call for chosen titles
def strip(x): return re.sub("<[^>]+>", "", x or "").replace("\n"," ").strip()
titles = {}
for s in subspots:
    cs = cand.get(s["id"], {}).get("cands") or []
    if cs and s["id"] in media: titles[s["id"]] = cs[0]["title"]
creds = {}; tl = list(titles.items())
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
json.dump(creds, open(os.path.join(BUILD, "credits.json"), "w"), ensure_ascii=False)

tot = sum(sizes.values())
print(f"media: {len(media)} items | webp {tot/1024:.0f} KB | ~b64 {tot*1.34/1024:.0f} KB | credits {len(creds)}")
print("MISSING images:", miss)
print("largest:", [(k, f"{v//1024}KB") for k, v in sorted(sizes.items(), key=lambda x:-x[1])[:6]])
