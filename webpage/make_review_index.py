# -*- coding: utf-8 -*-
"""Generate review/index.html contact sheet, grouped by ITEM, sub-groups per subspot.

Run after fetch_review_candidates.py, and again any time you delete files
(only images still on disk are shown).

    python make_review_index.py
Then open review/index.html in a browser.
"""
import os, json, html, base64
from content import ITEMS, REGIONS

BUILD = os.path.dirname(os.path.abspath(__file__))
REVIEW = os.path.join(BUILD, "review")
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".tif", ".tiff")

def data_uri(path):
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    if ext == "jpg":
        ext = "jpeg"
    if ext not in ("jpeg", "png", "webp", "gif"):
        ext = "jpeg"
    with open(path, "rb") as f:
        b = base64.b64encode(f.read()).decode()
    return f"data:image/{ext};base64,{b}"

def subspot_images(s):
    folder = os.path.join(REVIEW, s["id"])
    if not os.path.isdir(folder):
        return [], {}
    meta = {}
    mp = os.path.join(folder, "metadata.json")
    if os.path.exists(mp):
        try:
            meta = {f["file"]: f for f in json.load(open(mp, encoding="utf-8")).get("files", [])}
        except Exception:
            meta = {}
    files = sorted(f for f in os.listdir(folder) if f.lower().endswith(IMG_EXT))
    return files, meta

def main():
    reg = {r["id"]: r for r in REGIONS}
    sections = []; nav = []; total_imgs = 0

    for it in ITEMS:
        r = reg.get(it["region"], {})
        sub_blocks = []; item_count = 0
        for s in it["subspots"]:
            files, meta = subspot_images(s)
            if not files:
                continue
            item_count += len(files); total_imgs += len(files)
            cards = []
            for fn in files:
                fp = os.path.join(REVIEW, s["id"], fn)
                m = meta.get(fn, {})
                uri = data_uri(fp)
                artist = html.escape(m.get("artist", "") or "?")
                lic = html.escape(m.get("license", "") or "?")
                src = html.escape(m.get("source", "") or "?")
                kw = html.escape(m.get("kw", "") or "")
                foreign = m.get("foreign_url") or m.get("orig", "")
                size_kb = m.get("size_kb", "?")
                cards.append(f"""
                <figure>
                  <a href="{uri}" target="_blank"><img src="{uri}" loading="lazy" alt=""></a>
                  <figcaption>
                    <div class="fn">{html.escape(fn)}</div>
                    <div class="meta"><b>src</b> {src} &nbsp; <b>lic</b> {lic} &nbsp; <b>{size_kb}KB</b></div>
                    <div class="meta" title="{artist}"><b>by</b> {artist[:50]}</div>
                    {('<a class="src" href="'+html.escape(foreign)+'" target="_blank">source</a>') if foreign else ''}
                  </figcaption>
                </figure>""")
            sub_blocks.append(f"""
              <div class="subspot" id="{s['id']}">
                <h3>{html.escape(s['id'])} · {html.escape(s['zh'])}
                    <small>{html.escape(s['en'])}</small>
                    <span class="cnt">{len(files)}</span>
                    <code class="kw">{html.escape(s.get('q',''))}</code></h3>
                <div class="grid">{''.join(cards)}</div>
              </div>""")
        if not sub_blocks:
            continue
        nav.append(f'<a href="#{it["id"]}">{html.escape(it["id"])}</a>')
        sections.append(f"""
        <section class="item" id="{it['id']}">
          <h2><span class="tag">{html.escape(r.get('id',''))}</span> {html.escape(it['id'])} · {html.escape(it['zh'])}
              <small>{html.escape(it['en'])}</small>
              <span class="cnt">{item_count}</span></h2>
          <p class="reg">{html.escape(r.get('name',''))} · {html.escape(it.get('time',''))} · {html.escape(it.get('price','')[:60])}</p>
          {''.join(sub_blocks)}
        </section>""")

    doc = f"""<!doctype html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>选点手册 · 图片审核</title>
<style>
:root{{--bg:#15171c;--card:#1f232b;--txt:#e8e8ea;--mut:#8b909c;--acc:#e8a14a}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--txt);font:14px/1.5 system-ui,"PingFang SC","Microsoft YaHei",sans-serif}}
header{{position:sticky;top:0;z-index:9;background:rgba(21,23,28,.93);backdrop-filter:blur(6px);padding:10px 16px;border-bottom:1px solid #2c313a}}
header h1{{margin:0;font-size:16px;color:var(--acc)}}
header .sub{{color:var(--mut);font-size:12px;margin-top:2px}}
nav{{margin-top:8px;display:flex;flex-wrap:wrap;gap:4px}}
nav a{{color:var(--mut);text-decoration:none;font-size:11px;background:#262b34;padding:2px 7px;border-radius:4px}}
nav a:hover{{color:var(--acc)}}
section{{padding:16px;border-top:1px solid #23272f}}
h2{{margin:0 0 2px;font-size:16px}}
h2 small,.h3 small{{color:var(--mut);font-weight:400;margin-left:6px}}
h2 .tag{{background:var(--acc);color:#1a1a1a;border-radius:3px;padding:0 5px;font-size:12px;margin-right:4px}}
h2 .cnt,h3 .cnt{{background:#2c313a;color:var(--acc);border-radius:10px;padding:0 8px;font-size:12px;margin-left:6px}}
.reg{{color:var(--mut);font-size:12px;margin:2px 0 8px}}
.subspot{{margin:10px 0 16px;padding-top:6px;border-top:1px dashed #2a2f38}}
h3{{margin:0 0 8px;font-size:14px;color:var(--txt)}}
h3 .kw{{background:#262b34;color:var(--mut);padding:1px 6px;border-radius:3px;font-size:11px;margin-left:8px;font-weight:400}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:9px}}
figure{{margin:0;background:var(--card);border-radius:6px;overflow:hidden;border:1px solid #2c313a}}
figure img{{width:100%;height:165px;object-fit:cover;display:block;cursor:zoom-in;background:#0e0f12}}
figure figcaption{{padding:5px 8px;font-size:11px;color:var(--mut)}}
.fn{{color:var(--txt);font-weight:600;word-break:break-all}}
.meta{{margin-top:2px}}
.meta b,.src{{color:var(--acc)}}
.src{{display:inline-block;margin-top:3px;text-decoration:none;font-size:10px}}
.src:hover{{text-decoration:underline}}
</style></head><body>
<header><h1>巴厘岛选点手册 · 候选图审核</h1>
<div class="sub">每个景点 20 张，由其子景点平均分配。共 {total_imgs} 张。在文件夹 review/&lt;编号&gt;/ 里删掉不想要的，保留的我会编入网页。
重跑 <code>python make_review_index.py</code> 可刷新本页。点图看大图。</div>
<nav>{''.join(nav)}</nav></header>
{''.join(sections)}
</body></html>"""
    out = os.path.join(REVIEW, "index.html")
    open(out, "w", encoding="utf-8").write(doc)
    print(f"wrote {out} | {total_imgs} images across {len(sections)} items")

if __name__ == "__main__":
    main()
