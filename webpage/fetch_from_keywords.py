# -*- coding: utf-8 -*-
"""Fetch images from Unsplash + Pixabay using keywords parsed from keywords.md.

Strategy (matches keywords.md rules):
  - For each subspot, FIRST search the 纯地名 (pure name) keyword on BOTH sources.
    Filter by keyword relevance. Download up to 2 matching images.
  - THEN search 补充关键词 (extra angle keywords) on Pixabay only (save Unsplash quota).
  - MAX 4 images per subspot total.
  - Images with low keyword match (0 distinctive words in tags/desc) are NOT downloaded.
  - Resumable: subspots that already have enough images are skipped.
  - Unsplash rate-limit aware: stops the whole run when limit hit, so you can
    swap the API key and re-run to continue from where it left off.

Environment:
  $env:UNSPLASH_KEY="your_key"
  $env:PIXABAY_KEY="your_key"

Usage:
  python fetch_from_keywords.py              # all subspots (resume-safe)
  python fetch_from_keywords.py --only A1a   # single subspot
  python fetch_from_keywords.py --dry-run    # show plan without downloading
"""
import os, sys, json, re, time, argparse, subprocess, urllib.parse

BUILD = os.path.dirname(os.path.abspath(__file__))
REVIEW = os.path.join(BUILD, "review")
KW_MD = os.path.join(BUILD, "image_sourcing", "keywords.md")
UA = "BaliTripPlanner/1.0 (personal trip research; mail2hangly@gmail.com)"
UNSPLASH_KEY = os.environ.get("UNSPLASH_KEY", "").strip()
PIXABAY_KEY = os.environ.get("PIXABAY_KEY", "").strip()

MAX_TOTAL = 4           # max images per subspot
PURE_NAME_TARGET = 2    # min images from pure name keyword

# ---- curl helpers ------------------------------------------------------------
def curl_bytes(url, timeout=30):
    cmd = ["curl.exe", "-s", "--max-time", str(timeout), "-A", UA, "-L", url]
    r = subprocess.run(cmd, capture_output=True)
    return r.stdout

def curl_download(url, out, timeout=60):
    if os.path.exists(out) and os.path.getsize(out) > 3000:
        return True
    cmd = ["curl.exe", "-s", "--max-time", str(timeout), "-A", UA, "-L",
           "--retry", "2", "-o", out, url]
    r = subprocess.run(cmd)
    return r.returncode == 0 and os.path.exists(out) and os.path.getsize(out) > 3000

# ---- utils -------------------------------------------------------------------
def ext_from_url(url, default=".jpg"):
    m = re.search(r"\.(jpe?g|png|webp)(?:\?|$)", url, re.I)
    return "." + m.group(1).lower().replace("jpeg", "jpg") if m else default

def count_images(folder):
    """Count existing image files (>3KB) in a subspot folder."""
    if not os.path.isdir(folder):
        return 0
    n = 0
    for f in os.listdir(folder):
        p = os.path.join(folder, f)
        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')) and os.path.getsize(p) > 3000:
            n += 1
    return n

# ---- keyword matching --------------------------------------------------------
STOP_WORDS = {
    'bali', 'island', 'beach', 'temple', 'waterfall', 'lake', 'mountain',
    'volcano', 'rice', 'terrace', 'forest', 'sea', 'ocean', 'bay', 'coast',
    'view', 'landscape', 'nature', 'scenic', 'travel', 'tourism', 'destination',
    'indonesia', 'asian', 'asia', 'tropical', 'paradise', 'beautiful', 'scenery',
    'outdoor', 'adventure', 'trip', 'vacation', 'holiday', 'summer',
    'green', 'blue', 'sky', 'cloud', 'water', 'river', 'hill', 'peak',
    'crater', 'national', 'park', 'coral', 'fish', 'underwater',
    'boat', 'ship', 'traditional', 'culture', 'hindu', 'statue',
    'gate', 'entrance', 'path', 'road', 'trail', 'trekking', 'hiking',
    'morning', 'evening', 'night', 'day', 'golden', 'hour',
    'aerial', 'drone', 'sunset', 'sunrise', 'panorama', 'panoramic',
    'photo', 'image', 'picture',
    'the', 'a', 'an', 'of', 'in', 'on', 'at', 'and', 'or', 'with',
    'point', 'lookout', 'viewpoint', 'observation',
    'caldera', 'summit', 'slope', 'ridge', 'valley', 'canyon', 'cliff',
    'sand', 'rock', 'stone', 'tree', 'plant', 'flower', 'leaf', 'grass',
    'clear', 'turquoise', 'deep', 'shallow', 'wave', 'tide',
    'swim', 'swimming', 'float', 'floating',
    'dance', 'performance', 'ceremony', 'ritual', 'prayer',
    'shrine', 'altar', 'offering',
    'dawn', 'dusk', 'twilight',
    'wallpaper', 'background', 'stock', 'free',
    'mount', 'mt',
}

def distinctive_words(keyword):
    """Extract distinctive (non-generic) words from a keyword string."""
    words = re.findall(r'[a-zA-Z]+', keyword.lower())
    return [w for w in words if w not in STOP_WORDS and len(w) >= 3]

def match_score(result, keyword):
    """Return number of distinctive keyword words found in result text. 0 = no match."""
    dist = distinctive_words(keyword)
    if not dist:
        return 1
    parts = [result.get('title', ''), result.get('tags', ''), result.get('alt_desc', '')]
    text = ' '.join(p for p in parts if p).lower()
    return sum(1 for w in dist if w in text)

def is_relevant(result, keyword):
    return match_score(result, keyword) > 0

# ---- rate-limit exception ----------------------------------------------------
class RateLimitError(Exception):
    """Raised when Unsplash returns 'Rate Limit Exceeded'. Stops the entire run."""
    pass

# ---- source APIs -------------------------------------------------------------
def unsplash_search(term, per_page=8):
    """Search Unsplash. Raises RateLimitError if rate-limited."""
    if not UNSPLASH_KEY:
        return []
    q = {"query": term, "per_page": str(min(per_page, 30)), "client_id": UNSPLASH_KEY,
         "content_filter": "high", "orientation": "landscape"}
    url = "https://api.unsplash.com/search/photos?" + urllib.parse.urlencode(q)
    raw = curl_bytes(url)
    # Detect rate limit (Unsplash returns plain text "Rate Limit Exceeded")
    if b"Rate Limit Exceeded" in raw or b"rate limit" in raw.lower():
        raise RateLimitError("Unsplash rate limit exceeded — please update UNSPLASH_KEY and re-run")
    try:
        data = json.loads(raw)
    except Exception as e:
        print(f"  UNSPLASH ERR '{term}': {e}")
        return []
    if isinstance(data, dict) and data.get("errors"):
        print(f"  UNSPLASH API error: {data['errors']}")
        return []
    results = []
    for r in data.get("results", []):
        urls = r.get("urls", {})
        orig = urls.get("regular") or urls.get("full", "")
        if not orig:
            continue
        if "w=1080" in orig:
            orig = orig.replace("w=1080", "w=1600")
        alt = r.get("alt_description", "") or ""
        desc = r.get("description", "") or ""
        results.append({
            "title": alt or term, "url": orig,
            "thumb": urls.get("thumb", ""),
            "artist": (r.get("user") or {}).get("name", ""),
            "license": "Unsplash License", "source": "unsplash",
            "foreign_url": (r.get("links") or {}).get("html", ""),
            "kw": term, "tags": "",
            "alt_desc": (alt + " " + desc).strip(),
        })
    return results

def pixabay_search(term, per_page=8):
    if not PIXABAY_KEY:
        return []
    per_page = max(per_page, 3)
    q = {"key": PIXABAY_KEY, "q": term, "image_type": "photo",
         "orientation": "horizontal", "per_page": str(min(per_page, 200)),
         "safesearch": "true", "lang": "en"}
    url = "https://pixabay.com/api/?" + urllib.parse.urlencode(q)
    try:
        data = json.loads(curl_bytes(url))
    except Exception as e:
        print(f"  PIXABAY ERR '{term}': {e}")
        return []
    results = []
    for r in data.get("hits", []):
        orig = r.get("largeImageURL") or r.get("webformatURL", "")
        if not orig:
            continue
        tags = r.get("tags", "") or ""
        results.append({
            "title": tags or term, "url": orig,
            "thumb": r.get("previewURL", ""),
            "artist": r.get("user", ""),
            "license": "Pixabay License", "source": "pixabay",
            "foreign_url": r.get("pageURL", ""),
            "kw": term, "tags": tags, "alt_desc": "",
        })
    return results

# ---- parse keywords.md -------------------------------------------------------
def parse_keywords_md(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    entries = {}
    row_pat = re.compile(
        r'^\|\s*(A[1-5][a-e]|B[1-3][a-e]|C[1-2][a-d]|D1[ab]|E1[ab]|F[1-3][a-c])\s*\|'
        r'\s*[^|]+\|'
        r'\s*\*\*`([^`]+)`\*\*\s*\|'
        r'\s*(.+?)\s*\|',
        re.MULTILINE
    )
    for m in row_pat.finditer(text):
        sid = m.group(1)
        pure = m.group(2).strip()
        extra_raw = m.group(3).strip()
        extras = [] if extra_raw in ("—", "-", "") else re.findall(r'`([^`]+)`', extra_raw)
        entries[sid] = {"pure_name": pure, "extras": extras}
    return entries

# ---- per-subspot fetch -------------------------------------------------------
def fetch_subspot(sid, keywords):
    """Download images for one subspot. Max MAX_TOTAL, filtered by keyword relevance.

    Returns (downloaded_pure, downloaded_extra).  Raises RateLimitError if Unsplash
    is rate-limited (caller should stop the run).
    """
    folder = os.path.join(REVIEW, sid)
    os.makedirs(folder, exist_ok=True)

    # ── Resume check: skip if already has enough images ──
    existing = count_images(folder)
    if existing >= MAX_TOTAL:
        print(f"  [{sid}] 已有 {existing} 张，跳过", flush=True)
        return 0, 0

    pure = keywords["pure_name"]
    extras = keywords["extras"]
    dist_pure = distinctive_words(pure)

    all_meta = []
    seen_urls = set()
    fnum = existing + 1   # continue numbering after existing files

    # ── Phase 1: pure name keyword (Unsplash + Pixabay, target PURE_NAME_TARGET) ──
    print(f"  [{sid}] 纯地名: \"{pure}\"  特征词={dist_pure}", flush=True)
    candidates = []
    # Unsplash (may raise RateLimitError — stops the whole run)
    candidates += unsplash_search(pure, per_page=8)
    time.sleep(0.3)
    candidates += pixabay_search(pure, per_page=8)
    time.sleep(0.3)

    matching = [r for r in candidates if is_relevant(r, pure)]
    matching.sort(key=lambda r: match_score(r, pure), reverse=True)
    skipped = len(candidates) - len(matching)
    if skipped:
        print(f"    关键词过滤: 候选 {len(candidates)} -> 匹配 {len(matching)} (跳过 {skipped} 张低相关)", flush=True)

    # Fallback: if strict match yields 0 but API returned results, use top API
    # results (API search itself is keyword-matched; niche places may lack
    # the place name in tags even though the image is correct).
    if not matching and candidates:
        print(f"    严格匹配 0 张，回退到 API 原始排序 (tags 可能不含地名)", flush=True)
        matching = list(candidates)

    # If we have existing images, we still need (PURE_NAME_TARGET) pure-name images total
    # but don't re-download what's already there — just fill remaining slots
    pure_needed = max(0, PURE_NAME_TARGET - existing)
    downloaded_pure = 0
    for r in matching:
        if downloaded_pure >= pure_needed:
            break
        if r["url"] in seen_urls:
            continue
        ext = ext_from_url(r["url"])
        fn = f"{fnum:02d}_{r['source']}{ext}"
        fpath = os.path.join(folder, fn)
        # skip if this exact filename already exists (resume safety)
        if os.path.exists(fpath) and os.path.getsize(fpath) > 3000:
            fnum += 1
            downloaded_pure += 1
            seen_urls.add(r["url"])
            continue
        print(f"    -> {fn}", end="", flush=True)
        if curl_download(r["url"], fpath):
            print(f" OK ({os.path.getsize(fpath)//1024}KB)", flush=True)
            seen_urls.add(r["url"])
            meta = {k: r[k] for k in ["title","artist","license","source","foreign_url","url","kw","tags"]}
            all_meta.append({"file": fn, **meta})
            fnum += 1
            downloaded_pure += 1
            time.sleep(0.1)
        else:
            print(" FAIL", flush=True)
    print(f"    纯地名下载: {downloaded_pure} 张 (本次)", flush=True)

    # ── Phase 2: extra angle keywords — Pixabay ONLY (save Unsplash quota) ──
    current_total = existing + downloaded_pure
    extra_slots = MAX_TOTAL - current_total
    downloaded_extra = 0
    if extras and extra_slots > 0:
        for ekw in extras:
            if extra_slots <= 0:
                break
            dist_ekw = distinctive_words(ekw)
            print(f"  [{sid}] 补充(Pixabay): \"{ekw}\"  特征词={dist_ekw}", flush=True)
            extra_candidates = pixabay_search(ekw, per_page=5)
            time.sleep(0.3)

            extra_matching = [r for r in extra_candidates
                              if is_relevant(r, ekw) and r["url"] not in seen_urls]
            extra_matching.sort(key=lambda r: match_score(r, ekw), reverse=True)
            rel_skipped = len(extra_candidates) - len(extra_matching)
            if rel_skipped > 0:
                print(f"    关键词过滤: 跳过 {rel_skipped} 张低相关", flush=True)

            # Fallback for extras too
            if not extra_matching and extra_candidates:
                extra_matching = [r for r in extra_candidates if r["url"] not in seen_urls]
                print(f"    严格匹配 0 张，回退到 API 原始排序", flush=True)

            for r in extra_matching[:1]:
                ext = ext_from_url(r["url"])
                fn = f"{fnum:02d}_{r['source']}{ext}"
                fpath = os.path.join(folder, fn)
                if os.path.exists(fpath) and os.path.getsize(fpath) > 3000:
                    fnum += 1; extra_slots -= 1; downloaded_extra += 1
                    seen_urls.add(r["url"])
                    continue
                print(f"    -> {fn}", end="", flush=True)
                if curl_download(r["url"], fpath):
                    print(f" OK ({os.path.getsize(fpath)//1024}KB)", flush=True)
                    seen_urls.add(r["url"])
                    meta = {k: r[k] for k in ["title","artist","license","source","foreign_url","url","kw","tags"]}
                    all_meta.append({"file": fn, **meta})
                    fnum += 1; extra_slots -= 1; downloaded_extra += 1
                    time.sleep(0.1)
                else:
                    print(" FAIL", flush=True)
        print(f"    补充下载: {downloaded_extra} 张 (本次)", flush=True)

    # ── update metadata.json (merge with existing if present) ──
    meta_path = os.path.join(folder, "metadata.json")
    old_meta = {}
    if os.path.exists(meta_path):
        try:
            old_meta = json.load(open(meta_path, encoding="utf-8"))
        except Exception:
            pass
    old_files = old_meta.get("files", [])
    # merge: keep old files not overwritten by new, then add new
    old_by_file = {f["file"]: f for f in old_files}
    for nf in all_meta:
        old_by_file[nf["file"]] = nf
    merged_files = list(old_by_file.values())
    merged_files.sort(key=lambda x: x["file"])

    ss_zh = old_meta.get("zh", "")
    if not ss_zh:
        try:
            from content import ITEMS
            for it in ITEMS:
                for s in it.get("subspots", []):
                    if s["id"] == sid:
                        ss_zh = s.get("zh", ""); break
                if ss_zh: break
        except Exception:
            pass

    json.dump({
        "id": sid, "zh": ss_zh,
        "pure_name": pure, "extra_keywords": extras,
        "files": merged_files,
    }, open(meta_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    return downloaded_pure, downloaded_extra

# ---- main --------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="comma-separated subspot IDs (A1a,B1a..)")
    ap.add_argument("--dry-run", action="store_true", help="print plan without downloading")
    args = ap.parse_args()

    if not UNSPLASH_KEY and not PIXABAY_KEY:
        print("ERROR: set UNSPLASH_KEY and/or PIXABAY_KEY environment variables")
        sys.exit(1)

    entries = parse_keywords_md(KW_MD)
    only = set(x.strip() for x in args.only.split(",") if x.strip())
    targets = {k: v for k, v in entries.items() if not only or k in only}

    total_extras = sum(len(v["extras"]) for v in targets.values())
    print(f"子点数: {len(targets)} | 纯地名查询: {len(targets)} | 补充关键词: {total_extras}")
    print(f"来源: 纯地名=Unsplash+Pixabay | 补充=Pixabay only (节省Unsplash额度)")
    print(f"策略: 每点最多 {MAX_TOTAL} 张 (纯地名≥{PURE_NAME_TARGET} + 补充), 关键词低相关不下载")
    print(f"断点续传: 已有≥{MAX_TOTAL}张的子点自动跳过, Unsplash限流时停止运行")
    print()

    if args.dry_run:
        for sid, kw in targets.items():
            dist = distinctive_words(kw['pure_name'])
            existing = count_images(os.path.join(REVIEW, sid))
            print(f"  {sid}: 纯='{kw['pure_name']}'  特征词={dist}  补充={kw['extras']}  已有={existing}")
        return

    t0 = time.time()
    total_pure, total_extra = 0, 0
    completed = []
    try:
        for sid, kw in targets.items():
            print(f"=== {sid} ===", flush=True)
            p, e = fetch_subspot(sid, kw)
            total_pure += p
            total_extra += e
            completed.append(sid)
    except RateLimitError as e:
        print(f"\n{'!'*50}")
        print(f"UNSPLASH 限流! 已完成 {len(completed)} 个子点: {','.join(completed)}")
        print(f"请更新 UNSPLASH_KEY 后重新运行脚本，已有图片不会被重复下载。")
        print(f"{'!'*50}")
        sys.exit(2)

    elapsed = time.time() - t0
    print(f"\n{'='*50}")
    print(f"完成! 纯地名图片: {total_pure} 张 | 补充图片: {total_extra} 张 | 总耗时 {elapsed:.0f}s")
    print(f"输出目录: {REVIEW}/")
    print(f"\n下一步: 检查 review/ 目录，删除不满意的图片 → python apply_review.py → python build.py")

if __name__ == "__main__":
    main()
