# -*- coding: utf-8 -*-
"""Fetch review candidates: 20 images per ITEM, evenly split across its subspots.

Two source modes (auto-selected):
  - DIRECT (China, no proxy, high quality): Unsplash + Pixabay
        active when env UNSPLASH_KEY and/or PIXABAY_KEY is set.
  - PROXY (needs Clash etc.): Wikimedia Commons + Openverse
        active when no direct key is set (uses REVIEW_PROXY, default 7897).

Each item gets `--total` (20) images distributed evenly across its subspots
(remainder to first subspots). Subspots needing >=7 images get extra angle
keywords (drone/aerial, sunset/panorama) round-robined for variety.

Resumable (skips existing files >3KB). Outputs review/<subspot_id>/ + metadata.json.

Usage:
    python fetch_review_candidates.py
    python fetch_review_candidates.py --only A5,B1
    set UNSPLASH_KEY=xxx       # -> direct mode (Unsplash)
    set PIXABAY_KEY=yyy        # -> direct mode (Pixabay)
    set REVIEW_PROXY=http://127.0.0.1:7897
"""
import os, json, subprocess, urllib.parse, time, re, argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from content import ITEMS

BUILD = os.path.dirname(os.path.abspath(__file__))
REVIEW = os.path.join(BUILD, "review")
PROXY = os.environ.get("REVIEW_PROXY", "http://127.0.0.1:7897")
UA = "BaliTripPlanner/1.0 (personal trip research; mail2hangly@gmail.com)"
UNSPLASH_KEY = os.environ.get("UNSPLASH_KEY", "").strip()
PIXABAY_KEY = os.environ.get("PIXABAY_KEY", "").strip()
DIRECT_MODE = bool(UNSPLASH_KEY or PIXABAY_KEY)
os.makedirs(REVIEW, exist_ok=True)

# ---- curl helpers ----------------------------------------------------------
def curl_bytes(url, timeout=40, use_proxy=True):
    cmd = ["curl.exe", "-s", "--max-time", str(timeout), "-A", UA, "-L", url]
    if use_proxy and PROXY:
        cmd[1:1] = ["-x", PROXY]
    r = subprocess.run(cmd, capture_output=True)
    return r.stdout

def curl_download(url, out, timeout=90, use_proxy=True):
    if os.path.exists(out) and os.path.getsize(out) > 3000:
        return True
    cmd = ["curl.exe", "-s", "--max-time", str(timeout), "-A", UA, "-L", "--retry", "2", "-o", out, url]
    if use_proxy and PROXY:
        cmd[1:1] = ["-x", PROXY]
    r = subprocess.run(cmd)
    return r.returncode == 0 and os.path.exists(out) and os.path.getsize(out) > 3000

# ---- utils -----------------------------------------------------------------
def strip_html(s):
    return re.sub(r"<[^>]+>", "", s or "").replace("\n", " ").strip()

def ext_from_url(url, default=".jpg"):
    m = re.search(r"\.(jpe?g|png|webp|gif|tiff?)(?:\?|$)", url, re.I)
    return "." + m.group(1).lower().replace("jpeg", "jpg") if m else default

def dedup_key(url):
    b = url.split("/")[-1].split("?")[0]
    try:
        b = urllib.parse.unquote(b)
    except Exception:
        pass
    b = re.sub(r"^\d+px-", "", b)
    return b.lower()

BAD = ("map", "locator", "location map", "diagram", "flag", "coat of arms",
       "svg", "logo", "icon", "label", "signage", "stamp", "collage")
def looks_bad(title):
    t = (title or "").lower()
    return t.endswith(".svg") or t.endswith(".gif") or any(b in t for b in BAD)

# ---- PROXY sources: Commons + Openverse ------------------------------------
def commons_search(term, n=15, w=1280):
    q = {"action": "query", "generator": "search", "gsrsearch": term,
         "gsrnamespace": "6", "gsrlimit": str(n), "prop": "imageinfo",
         "iiprop": "url|mime|extmetadata", "iiurlwidth": str(w), "format": "json"}
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(q)
    try:
        data = json.loads(curl_bytes(url))
    except Exception as e:
        print("  COMMONS ERR", term, e, flush=True); return []
    out = []
    for p in data.get("query", {}).get("pages", {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        mime = ii.get("mime", "")
        if not mime.startswith("image") or mime in ("image/svg+xml", "image/gif"):
            continue
        title = p.get("title", "")
        if looks_bad(title):
            continue
        em = ii.get("extmetadata") or {}
        out.append({"title": title, "thumb": ii.get("thumburl"), "orig": ii.get("url"),
                    "artist": strip_html(em.get("Artist", {}).get("value", "")),
                    "license": strip_html(em.get("LicenseShortName", {}).get("value", "")),
                    "desc": strip_html(em.get("ImageDescription", {}).get("value", "")),
                    "source": "commons", "kw": term, "_use_proxy": True})
    out.sort(key=lambda x: x.get("index", 99))
    return out

def openverse_search(term, n=12):
    q = {"q": term, "page_size": str(n), "mature": "false"}
    url = "https://api.openverse.org/v1/images/?" + urllib.parse.urlencode(q)
    try:
        data = json.loads(curl_bytes(url))
    except Exception as e:
        print("  OPENVERSE ERR", term, e, flush=True); return []
    out = []
    for r in data.get("results", []):
        orig = r.get("url") or ""
        if not orig:
            continue
        lic = r.get("license", "")
        if lic in ("", "sampling+"):
            continue
        out.append({"title": r.get("title", ""), "thumb": r.get("thumbnail"), "orig": orig,
                    "artist": r.get("creator", "") or "",
                    "license": ("%s %s" % (lic, r.get("license_version", ""))).strip(),
                    "desc": r.get("title", ""), "source": r.get("provider", "openverse"),
                    "foreign_url": r.get("foreign_landing_url", ""), "kw": term, "_use_proxy": True})
    return out

# ---- DIRECT sources: Unsplash + Pixabay (China, no proxy) -------------------
def unsplash_search(term, n=15):
    if not UNSPLASH_KEY:
        return []
    q = {"query": term, "per_page": str(min(n, 30)), "client_id": UNSPLASH_KEY,
         "content_filter": "high", "orientation": "landscape"}
    url = "https://api.unsplash.com/search/photos?" + urllib.parse.urlencode(q)
    try:
        data = json.loads(curl_bytes(url, use_proxy=False))
    except Exception as e:
        print("  UNSPLASH ERR", term, e, flush=True); return []
    out = []
    for r in data.get("results", []):
        urls = r.get("urls", {})
        orig = urls.get("regular") or urls.get("full") or urls.get("raw", "")
        if not orig:
            continue
        # bump regular (1080) to 1600 for better review quality
        if "w=1080" in orig:
            orig = orig.replace("w=1080", "w=1600")
        out.append({"title": r.get("alt_description", "") or term,
                    "thumb": urls.get("thumb", ""), "orig": orig,
                    "artist": (r.get("user") or {}).get("name", ""),
                    "license": "Unsplash License", "desc": r.get("alt_description", "") or "",
                    "source": "unsplash",
                    "foreign_url": (r.get("links") or {}).get("html", ""),
                    "kw": term, "_use_proxy": False})
    return out

def pixabay_search(term, n=15):
    if not PIXABAY_KEY:
        return []
    q = {"key": PIXABAY_KEY, "q": term, "image_type": "photo", "orientation": "horizontal",
         "per_page": str(min(n, 30)), "safesearch": "true", "lang": "en"}
    url = "https://pixabay.com/api/?" + urllib.parse.urlencode(q)
    try:
        data = json.loads(curl_bytes(url, use_proxy=False))
    except Exception as e:
        print("  PIXABAY ERR", term, e, flush=True); return []
    out = []
    for r in data.get("hits", []):
        orig = r.get("largeImageURL") or r.get("webformatURL") or ""
        if not orig:
            continue
        out.append({"title": r.get("tags", "") or term, "thumb": r.get("previewURL", ""),
                    "orig": orig, "artist": r.get("user", ""),
                    "license": "Pixabay License", "desc": r.get("tags", "") or "",
                    "source": "pixabay", "foreign_url": r.get("pageURL", ""),
                    "kw": term, "_use_proxy": False})
    return out

# ---- source selection ------------------------------------------------------
def source_funcs():
    if DIRECT_MODE:
        fs = []
        if UNSPLASH_KEY: fs.append(unsplash_search)
        if PIXABAY_KEY: fs.append(pixabay_search)
        return fs
    return [commons_search, openverse_search]

# ---- keyword variety + round-robin pick ------------------------------------
def subspot_keywords(s, k):
    q = s["q"]
    kws = [q]
    if k >= 7:
        kws.append(q + " drone aerial")
        kws.append(q + " sunset panorama")
    return kws

def gather_pool(kws):
    """For each keyword, merge results from all active sources into per-keyword list."""
    funcs = source_funcs()
    per_kw = []
    for kw in kws:
        cl = []
        for f in funcs:
            cl += f(kw)
            time.sleep(0.2)
        per_kw.append(cl)
    return per_kw

def round_robin_pick(per_kw, k):
    chosen, seen = [], set()
    idx = [0] * len(per_kw)
    while len(chosen) < k:
        progressed = False
        for ki, cl in enumerate(per_kw):
            while idx[ki] < len(cl):
                c = cl[idx[ki]]; idx[ki] += 1
                key = dedup_key(c["orig"] or c.get("thumb", ""))
                if key in seen:
                    continue
                seen.add(key); chosen.append(c); progressed = True
                break
            if len(chosen) >= k:
                break
        if not progressed:
            break
    return chosen

# ---- per-subspot fetch -----------------------------------------------------
def dl_url(c):
    if c["source"] == "commons":
        return c["thumb"] or c["orig"]
    return c["orig"]

def fetch_subspot(s, it, k):
    sid = s["id"]; folder = os.path.join(REVIEW, sid)
    os.makedirs(folder, exist_ok=True)
    kws = subspot_keywords(s, k)
    per_kw = gather_pool(kws)
    chosen = round_robin_pick(per_kw, k)
    pool_n = sum(len(x) for x in per_kw)
    print(f"  [{sid}] {s['zh']}: need={k} pool={pool_n} -> picked {len(chosen)}", flush=True)

    if not chosen:
        json.dump({"id": sid, "zh": s["zh"], "q": s["q"], "item": it["zh"], "files": []},
                  open(os.path.join(folder, "metadata.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        return sid, 0

    tasks = []
    for i, c in enumerate(chosen, 1):
        u = dl_url(c)
        if not u:
            continue
        fn = f"{i:02d}_{c['source']}{ext_from_url(u)}"
        tasks.append((c, u, os.path.join(folder, fn), fn))

    def worker(t):
        c, u, out, fn = t
        return (c, u, out, fn, curl_download(u, out, use_proxy=c.get("_use_proxy", DIRECT_MODE is False)))

    got = 0; meta = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = [ex.submit(worker, t) for t in tasks]
        for f in as_completed(futs):
            c, u, out, fn, ok = f.result()
            if ok:
                got += 1
                meta.append({"file": fn, "source": c["source"], "title": c.get("title", ""),
                             "artist": c.get("artist", ""), "license": c.get("license", ""),
                             "desc": c.get("desc", ""), "orig": c.get("orig", ""),
                             "thumb": c.get("thumb", ""), "foreign_url": c.get("foreign_url", ""),
                             "kw": c.get("kw", ""), "size_kb": round(os.path.getsize(out) / 1024, 1)})
            else:
                try:
                    if os.path.exists(out) and os.path.getsize(out) < 3000:
                        os.remove(out)
                except Exception:
                    pass
    meta.sort(key=lambda x: x["file"])
    json.dump({"id": sid, "zh": s["zh"], "en": s["en"], "q": s["q"], "item": it["zh"],
               "alloc": k, "files": meta},
              open(os.path.join(folder, "metadata.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    return sid, got

# ---- main ------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="comma-separated ITEM ids (A1,B1..)")
    ap.add_argument("--total", type=int, default=20, help="images per item")
    args = ap.parse_args()

    only = set(x.strip() for x in args.only.split(",") if x.strip())
    items = [it for it in ITEMS if it["id"] in only] if only else ITEMS
    mode = "DIRECT(unsplash+pixabay, no proxy)" if DIRECT_MODE else "PROXY(commons+openverse)"
    srcs = ", ".join(f.__name__ for f in source_funcs())
    print(f"MODE={mode} | sources=[{srcs}] | items={len(items)} | {args.total}/item", flush=True)

    t0 = time.time(); total = 0
    for it in items:
        subs = it["subspots"]; n = len(subs)
        base = args.total // n; extra = args.total % n
        alloc = [base + (1 if i < extra else 0) for i in range(n)]
        print(f"\n=== {it['id']} {it['zh']} | {n} subspots -> {alloc} (sum {sum(alloc)}) ===", flush=True)
        for s, k in zip(subs, alloc):
            if k <= 0:
                continue
            _, got = fetch_subspot(s, it, k)
            total += got
    print(f"\nDONE. total downloaded={total} in {time.time()-t0:.0f}s", flush=True)

if __name__ == "__main__":
    main()
