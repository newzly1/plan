# -*- coding: utf-8 -*-
"""Render the self-contained index.html from content.py + media.json + videos.json.
Media missing (still fetching) degrades to a labeled placeholder so the page always builds."""
import json, os, html, base64
import content as C

BUILD = os.path.dirname(os.path.abspath(__file__))
def load(name):
    p = os.path.join(BUILD, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
MEDIA = load("media.json")       # {subspotId: dataURI, "vid:A1": dataURI}
VIDEOS = load("videos.json")     # {itemId: {yt_id,title,author}}
CREDITS = load("credits.json")   # {subspotId: {artist,license}}
FONT = load("font.json")         # {"serif_woff2": "<b64>"} 或 {"serif_woff": "<b64>"}；缺失则降级系统宋体栈
HL_IDS = list(C.HIGHLIGHTS)  # 第一章「最热门景点」成员 item id（有序）

IMAGES_DIR = os.path.join(BUILD, "images")
USED_KEYS = set()   # img_uri 记录 index.html 实际引用到的 key，write_images 只写这些
def _fname(key):
    """'A1a' -> 'A1a.webp'；'vid:A1' -> 'vid-A1.webp'（冒号在 Windows 文件名里非法）。"""
    return key.replace(":", "-") + ".webp"

def esc(s): return html.escape(str(s), quote=True)
def img_uri(key):
    if not MEDIA.get(key, ""):
        return ""
    USED_KEYS.add(key)
    return "images/" + _fname(key)

def write_images():
    """把 index.html 实际引用到的 media 解码写成独立 .webp 文件，供页面用相对路径引用。
    只写被引用的 key，跳过 media.json 里的历史遗留孤儿；先清空目录再全量重写，
    顺带删掉改名/删除后残留的陈旧 .webp，保证 images/ 与页面一一对应。
    须在 BODY 组装完（USED_KEYS 填满）之后调用。60 张小图解码+写入毫秒级，不做增量。"""
    os.makedirs(IMAGES_DIR, exist_ok=True)
    for old in os.listdir(IMAGES_DIR):
        if old.lower().endswith(".webp"):
            os.remove(os.path.join(IMAGES_DIR, old))
    seen, n = {}, 0
    for key in sorted(USED_KEYS):
        fname = _fname(key)
        clash = seen.get(fname.lower())
        if clash is not None:
            raise SystemExit(f"images/ filename collision: {key!r} and {clash!r} both map to {fname}")
        seen[fname.lower()] = key
        raw = base64.b64decode(MEDIA[key].split(",", 1)[1])
        with open(os.path.join(IMAGES_DIR, fname), "wb") as f:
            f.write(raw)
        n += 1
    return n

def font_face():
    """有内嵌子集则输出 @font-face（'Trip Serif'）；否则空串，降级到系统宋体栈。"""
    if FONT.get("serif_woff2"):
        return ("@font-face{font-family:'Trip Serif';font-style:normal;font-weight:600;font-display:swap;"
                "src:url(data:font/woff2;base64,%s) format('woff2')}\n" % FONT["serif_woff2"])
    if FONT.get("serif_woff"):
        return ("@font-face{font-family:'Trip Serif';font-style:normal;font-weight:600;font-display:swap;"
                "src:url(data:font/woff;base64,%s) format('woff')}\n" % FONT["serif_woff"])
    return ""

def img_tag(key, cls, alt, lazy=True):
    uri = img_uri(key)
    lz = ' loading="lazy" decoding="async"' if lazy else ''
    if uri:
        return f'<img class="{cls}" src="{uri}" alt="{esc(alt)}"{lz}>'
    return f'<div class="{cls} ph" role="img" aria-label="{esc(alt)}"><span>{esc(alt)}</span></div>'

# ---------- body ----------
def hero():
    m = C.META
    chs = spot_chapters()
    idx = "".join(f'<a class="idx" href="#{ch["anchor"]}"><b>{cn_chapter(i)}</b><span>{esc(ch["nav"])}</span></a>'
                  for i, ch in enumerate(chs, 1))
    idx += f'<a class="idx" href="#combos"><b>{cn_chapter(len(chs)+1)}</b><span>组合建议</span></a>'
    return f'''<header class="hero">
  <div class="masthead"><span class="mast-l">INDONESIA</span><span class="mast-r">FIELD NOTES · 2026</span></div>
  <div class="hero-title">
    <span class="rule" aria-hidden="true"></span>
    <h1>{esc(m["title"])}</h1>
    <p class="sub">{esc(m["subtitle"])}</p>
    <div class="facts"><span>10.2 – 10.11 或 10.2 – 10.7</span><span>6–10 天</span><span>6 人同行</span><span>起止 DPS</span></div>
  </div>
  <figure class="hero-media">
    {img_tag("B1a","hero-img","佩尼达 Kelingking 霸王龙海滩",lazy=False)}
    <figcaption class="cap-line"><span>Kelingking · Nusa Penida</span><span>Fig. 01</span></figcaption>
  </figure>
  <div class="hero-foot">
    <p class="howto">{esc(m["howto"])}</p>
    <nav class="index" aria-label="章节导航">{idx}</nav>
  </div>
</header>'''

def gallery(item):
    figs = ""
    for s in item["subspots"]:
        figs += f'''<figure class="shot">{img_tag(s['id'],'shot-img',s['zh'])}
        <figcaption><b>{esc(s['zh'])}</b><span>{esc(s['en'])}</span></figcaption></figure>'''
    return f'<div class="gallery">{figs}</div>'

def video_plate(item):
    vids = VIDEOS.get(item["id"])
    if not vids: return ""
    # Handle both old format (dict) and new format (list) — only the first video is shown
    if isinstance(vids, dict):
        vids = [vids]
    v = vids[0]
    cover = img_uri(f"vid:{item['id']}_0")
    bvid = v.get("bvid","")
    inner = f'<img class="vid-img" src="{cover}" alt="" loading="lazy">' if cover else '<div class="vid-img ph"></div>'
    return f'''<div class="vid" data-bvid="{esc(bvid)}" role="button" tabindex="0" aria-label="播放影片 {esc(v['title'])}">
      {inner}<span class="vid-play" aria-hidden="true"></span>
      <span class="vid-badge">▶ 点击播放</span>
      <span class="vid-cap">{esc(v["title"])}<i>{esc(v.get("author",""))} · 哔哩哔哩</i></span></div>'''

def spot(item):
    tags = "".join(f'<span class="tag">{esc(t)}</span>' for t in item["tags"])
    star = '<span class="pick-star" title="精华">★</span>' if item.get("highlight") else ''
    notes = ""
    for label, key in (("亮点","feature"),("注意","caution"),("串联","coupling")):
        if item.get(key):
            notes += f'<div class="note"><span class="note-k">{label}</span><p>{esc(item[key])}</p></div>'
    return f'''<article class="spot" id="{item['id']}" data-id="{item['id']}">
  <div class="stamp" aria-hidden="true"></div>
  <div class="spot-head">
    <span class="code">{item['id']}</span>
    <div class="spot-title"><h3>{esc(item['zh'])}{star}</h3><span class="en">{esc(item['en'])}</span></div>
  </div>
  <div class="tags">{tags}</div>
  {gallery(item)}
  {video_plate(item)}
  <div class="spot-meta"><span class="mt"><i>时间</i>{esc(item['time'])}</span><span class="mt"><i>人均</i>{esc(item['price'])}</span></div>
  <details class="notes"><summary><span>亮点 · 注意 · 串联</span><span class="chev"></span></summary>{notes}</details>
  <div class="vote" role="group" aria-label="为 {esc(item['zh'])} 投票">
    <button type="button" class="v v-must" data-v="must">必去</button>
    <button type="button" class="v v-maybe" data-v="maybe">可去</button>
    <button type="button" class="v v-skip" data-v="skip">略过</button>
  </div>
</article>'''

# ---------- 章节：第一章 最热门 + 各非空地区章 ----------
CN_NUM = "一二三四五六七八九十"
def cn_chapter(n):
    """1 -> '第一章'（章数不会超过 10）。"""
    return f"第{CN_NUM[n-1]}章"

def spot_chapters():
    """有序景点章的元数据（不渲染 body，供正文与 hero 导航共用，保证一一对应）。
    第一章＝HIGHLIGHTS（最热门）；其后＝REGIONS 中仍有非热门景点的地区，按原顺序。
    整区景点全为热门的地区（科莫多/布罗莫）items 为空 → 不成章。"""
    chapters = [{
        "anchor": "hl-main", "nav": "最热门", "title": "最热门景点",
        "data": '<span>多数人必去</span>', "desc": "",
        "items": sorted((it for it in C.ITEMS if it["id"] in HL_IDS),
                        key=lambda it: HL_IDS.index(it["id"])),
    }]
    for r in C.REGIONS:
        items = [it for it in C.ITEMS if it["region"] == r["id"] and it["id"] not in HL_IDS]
        if not items:
            continue
        chapters.append({
            "anchor": f'region-{r["id"]}', "nav": r["name"].split(" (")[0], "title": r["name"],
            "data": f'<span>{esc(r["tag"])}</span><i></i><span>{esc(r["days"])}</span><i></i><span>{esc(r["budget"])}</span>',
            "desc": r["desc"], "items": items,
        })
    return chapters

def render_chapter(n, ch):
    desc = f'<p class="chap-desc">{esc(ch["desc"])}</p>' if ch["desc"] else ''
    body = "".join(spot(it) for it in ch["items"])
    return f'''<section class="chapter" id="{ch['anchor']}">
  <div class="chap-head">
    <div class="chap-meta"><h2>{esc(ch['title'])}</h2><span class="chap-region">{cn_chapter(n)}</span></div>
    <div class="chap-data">{ch['data']}</div>
  </div>
  {desc}{body}
</section>'''

def chapters_html():
    return "".join(render_chapter(i, ch) for i, ch in enumerate(spot_chapters(), 1))

def combos():
    combo_n = len(spot_chapters()) + 1
    cards = ""
    for c in C.COMBOS:
        cards += f'''<div class="combo" data-no="{c['no']}">
      <div class="combo-no">{c['no']}</div>
      <div class="combo-b"><h3>{esc(c['name'])}<span class="combo-pick">选为我的主线</span></h3>
        <div class="combo-row"><span><i>区域</i>{esc(c['content'])}</span><span><i>跨岛</i>{esc(c['cross'])}</span></div>
        <div class="combo-row"><span><i>天数</i>{esc(c['days'])}</span><span><i>人均</i>{esc(c['budget'])}</span></div>
        <p>{esc(c['note'])}</p></div></div>'''
    return f'''<section class="chapter combos-sec" id="combos">
  <div class="chap-head">
    <div class="chap-meta"><h2>组合建议 · 主线①–⑦</h2><span class="chap-region">{cn_chapter(combo_n)}</span></div>
    <div class="chap-data"><span>①–④ 全程 9–10 天 · ⑤–⑦ 精简 6 天 · 点击选择你的主线</span></div>
  </div>
  <p class="chap-desc">{esc(C.COMBO_HINT)}</p>
  <div class="combos">{cards}</div></section>'''

def prices():
    blocks = ""
    for title, rows in C.PRICES:
        tr = "".join(f'<tr><td>{esc(a)}</td><td class="num">{esc(b)}</td></tr>' for a,b in rows)
        blocks += f'<div class="ptable"><h4>{esc(title)}</h4><div class="tw"><table>{tr}</table></div></div>'
    return f'''<details class="fold" id="prices"><summary><span>单项参考价 · 人民币粗估</span><span class="chev"></span></summary>
    <p class="fold-note">{esc(C.META["rate"])}</p>{blocks}</details>'''

def notes_sec():
    rows = "".join(f'<div class="tip"><span class="tip-k">{esc(k)}</span><p>{esc(v)}</p></div>' for k,v in C.NOTES)
    return f'''<details class="fold" id="tips"><summary><span>全程通用注意事项</span><span class="chev"></span></summary><div class="tips">{rows}</div></details>'''

def footer():
    creds = ""
    if CREDITS:
        items = []
        for sid, c in CREDITS.items():
            a = c.get("artist","").strip(); l = c.get("license","").strip()
            if a or l: items.append(esc((a or "?") + (" · "+l if l else "")))
        uniq = sorted(set(items))
        if uniq:
            creds = '<p class="cred">图片来源(Unsplash / Pixabay / Wikimedia Commons 等)：' + "；".join(uniq[:60]) + "。版权归原作者，依各自许可使用。</p>"
    if not creds:
        creds = '<p class="cred">景点图片来自 Unsplash / Pixabay / Wikimedia Commons 等公开来源，版权归原作者，依各自许可使用；影片封面与嵌入播放均来自哔哩哔哩，版权归原上传者。</p>'
    return f'''<footer class="foot">
    {creds}
    <p class="disc">价格/时间为 2026-07-07 粗略估算，随季节、汇率与政策浮动，具体以出行前官方渠道为准。本页为同行投票参考，非商业用途。</p>
    <p class="made">巴厘岛及周边 · 选点手册 · 为你此行制作</p></footer>'''

def mylist():
    return f'''<button type="button" class="bar" id="bar">
  <span class="bar-top"><span class="bar-l"><span class="bar-dot"></span>我的清单 ›</span><span class="bar-stat" id="barStat">你选 0/{len(C.ITEMS)}</span></span>
  <span class="bar-sub" id="barSub">还没人投票 · 你可以抢先标记</span>
</button>
<div class="sheet" id="sheet" hidden>
  <div class="sheet-card" role="dialog" aria-label="我的清单" aria-modal="true">
    <div class="sheet-head"><b>我的清单</b><button type="button" class="x" id="sheetX" aria-label="关闭">×</button></div>
    <label class="fld"><span>你的名字</span><input type="text" id="nameIn" placeholder="填个名字，方便群里对号" maxlength="16"></label>
    <div class="picks" id="picks"></div>
    <div class="tally" id="tally">
      <div class="tally-head"><b>大家的选择 · 实时汇总</b><button type="button" class="tally-refresh" id="tallyRefresh">刷新</button></div>
      <div class="tally-body" id="tallyBody"><p class="tally-empty">加载中…</p></div>
    </div>
    <div class="sheet-act"><button type="button" class="submit" id="submitBtn">提交我的选择</button><button type="button" class="reset" id="resetBtn">清空所有标记</button></div>
  </div>
</div>
<div class="lb" id="lb" hidden><img id="lbImg" src="" alt=""><button type="button" class="lb-x" aria-label="关闭">×</button></div>
<div class="toast" id="toast" hidden></div>'''

# expose to JS
ITEMS_JS = json.dumps([{"id":it["id"],"zh":it["zh"]} for it in C.ITEMS], ensure_ascii=False)
COMBOS_JS = json.dumps({c["no"]: f'组{c["no"]} {c["name"]}' for c in C.COMBOS}, ensure_ascii=False)

BODY = (hero() + '<main>' + chapters_html()
        + combos() + prices() + notes_sec() + footer() + '</main>' + mylist())
N_IMAGES = write_images()   # BODY 里所有 img_uri 已调用完，USED_KEYS 就绪，此时才落盘

# ---------- assemble ----------
STYLE = open(os.path.join(BUILD,"style.css"), encoding="utf-8").read()
TALLY = open(os.path.join(BUILD,"tally.js"), encoding="utf-8").read()
IDENTITY = open(os.path.join(BUILD,"identity.js"), encoding="utf-8").read()
SCRIPT = open(os.path.join(BUILD,"app.js"), encoding="utf-8").read()
SCRIPT = SCRIPT.replace("/*__ITEMS__*/", ITEMS_JS).replace("/*__COMBOS__*/", COMBOS_JS)

OUT = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(C.META["title"])}</title>
<style>
{font_face()}{STYLE}
</style>
</head>
<body>
{BODY}
<script src="cloudbase.js"></script>
<script>
{TALLY}
{IDENTITY}
{SCRIPT}
</script>
</body>
</html>'''

open(os.path.join(BUILD,"index.html"),"w",encoding="utf-8").write(OUT)
kb = len(OUT.encode("utf-8"))/1024
print(f"wrote index.html : {kb:.0f} KB  (media keys: {len(MEDIA)}, videos: {len(VIDEOS)})")
print(f"wrote images/     : {N_IMAGES} files")
