# -*- coding: utf-8 -*-
"""Query Wikimedia Commons for each subspot, store top candidates, download top-1 original.
Uses curl (urllib hangs through the local proxy)."""
import json, subprocess, urllib.parse, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # webpage/
sys.path.insert(0, os.path.join(ROOT, "src"))
from content import ITEMS

UA = "BaliTripPlanner/1.0 (personal trip research; mail2zhangly@gmail.com)"
ASSETS = os.path.join(ROOT, "assets")
RAW = os.path.join(ASSETS, "raw")
os.makedirs(RAW, exist_ok=True)

def curl_bytes(url, timeout=40):
    r = subprocess.run(["curl","-s","--max-time",str(timeout),"-A",UA,"-L",url], capture_output=True)
    return r.stdout

def curl_download(url, out, timeout=45):
    r = subprocess.run(["curl","-s","--max-time",str(timeout),"-A",UA,"-L","--retry","2","-o",out,url])
    return r.returncode == 0 and os.path.exists(out) and os.path.getsize(out) > 2000

BAD = ("map", "locator", "location", "diagram", "flag", "coat of arms", "svg", "logo")
def looks_bad(title):
    t = title.lower()
    return t.endswith(".svg") or any(b in t for b in BAD)

def commons_search(term, n=5, w=1000):
    q = {"action":"query","generator":"search","gsrsearch":term,"gsrnamespace":"6",
         "gsrlimit":str(n),"prop":"imageinfo","iiprop":"url|mime","iiurlwidth":str(w),"format":"json"}
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(q)
    try:
        data = json.loads(curl_bytes(url))
    except Exception as e:
        print("  API ERR", term, e, flush=True); return []
    pages = data.get("query", {}).get("pages", {})
    out = []
    for p in pages.values():
        ii = (p.get("imageinfo") or [{}])[0]
        mime = ii.get("mime", "")
        if not mime.startswith("image"): continue
        if mime in ("image/svg+xml", "image/gif"): continue
        title = p.get("title", "")
        if looks_bad(title): continue
        out.append({"title": title, "thumb": ii.get("thumburl"), "index": p.get("index", 99)})
    out.sort(key=lambda x: x["index"])
    return out

subspots = [(s, it) for it in ITEMS for s in it["subspots"]]
cand = {}
ok = fail = 0
for i, (s, it) in enumerate(subspots, 1):
    res = commons_search(s["q"])
    cand[s["id"]] = {"zh": s["zh"], "en": s["en"], "q": s["q"], "cands": res}
    title = res[0]["title"] if res else "NONE"
    got = False
    if res and res[0]["thumb"]:
        got = curl_download(res[0]["thumb"], os.path.join(RAW, s["id"] + ".img"))
    ok += got; fail += (not got)
    print(f"[{i:2}/{len(subspots)}] {s['id']:4} {s['en']:22} -> {'OK ' if got else 'MISS'} {title}", flush=True)
    json.dump(cand, open(os.path.join(ASSETS, "candidates.json"), "w"), ensure_ascii=False, indent=1)

print(f"\nDONE. downloaded {ok}, missed {fail}", flush=True)
