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
    idx = "".join(f'<a class="idx" href="#region-{r["id"]}"><b>{r["id"]}</b><span>{esc(r["name"].split(" (")[0])}</span></a>' for r in C.REGIONS)
    return f'''<header class="hero">
  <div class="masthead"><span class="mast-l">INDONESIA</span><span class="mast-r">FIELD NOTES · 2026</span></div>
  <div class="hero-title">
    <span class="rule" aria-hidden="true"></span>
    <h1>{esc(m["title"])}</h1>
    <p class="sub">{esc(m["subtitle"])}</p>
    <div class="facts"><span>10.2 – 10.11</span><span>9–10 天</span><span>6 人</span><span>基地 DPS</span></div>
  </div>
  <figure class="hero-media">
    {img_tag("B1a","hero-img","佩尼达 Kelingking 霸王龙海滩",lazy=False)}
    <figcaption class="cap-line"><span>Kelingking · Nusa Penida</span><span>Fig. 01</span></figcaption>
  </figure>
  <div class="hero-foot">
    <p class="howto">{esc(m["howto"])}</p>
    <nav class="index" aria-label="分区导航"><a class="idx idx-star" href="#highlights"><b>★</b><span>精选</span></a>{idx}</nav>
  </div>
</header>'''

def highlights():
    cards = ""
    for h in C.HIGHLIGHTS:
        cards += f'''<a class="hl" href="#{h['item']}">
      {img_tag(h['img'],'hl-img',h['title'])}
      <figcaption class="hl-cap"><b>{esc(h['title'])}</b><span class="hl-sub">{esc(h['blurb'])}</span></figcaption></a>'''
    return f'''<section class="shelf" id="highlights">
  <div class="chap-eyebrow"><span class="k">精华速览</span>大多数人必去 · 先看这一屏</div>
  <div class="shelf-scroll">{cards}</div>
  <p class="shelf-note">以上 + 佩尼达跳岛 = 6 人不会踩雷的「稳妥核心盘」；差异化项目再从下面 A–E 里挑。</p>
</section>'''

def gallery(item):
    figs = ""
    for s in item["subspots"]:
        figs += f'''<figure class="shot">{img_tag(s['id'],'shot-img',s['zh'])}
        <figcaption><b>{esc(s['zh'])}</b><span>{esc(s['en'])}</span></figcaption></figure>'''
    return f'<div class="gallery">{figs}</div>'

def video_plate(item):
    v = VIDEOS.get(item["id"])
    if not v: return ""
    cover = img_uri("vid:"+item["id"])
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
    <button type="button" class="v v-no" data-v="no">无所谓</button>
  </div>
</article>'''

def region(r):
    items = [it for it in C.ITEMS if it["region"] == r["id"]]
    body = "".join(spot(it) for it in items)
    return f'''<section class="chapter" id="region-{r['id']}">
  <div class="chap-head">
    <div class="chap-meta"><h2>{esc(r['name'])}</h2><span class="chap-region">Region {r['id']}</span></div>
    <div class="chap-data"><span>{esc(r['tag'])}</span><i></i><span>{esc(r['days'])}</span><i></i><span>{esc(r['budget'])}</span></div>
  </div>
  <p class="chap-desc">{esc(r['desc'])}</p>
  {body}
</section>'''

def combos():
    cards = ""
    for c in C.COMBOS:
        cards += f'''<div class="combo">
      <div class="combo-no">{c['no']}</div>
      <div class="combo-b"><h3>{esc(c['name'])}</h3>
        <div class="combo-row"><span><i>区域</i>{esc(c['content'])}</span><span><i>跨岛</i>{esc(c['cross'])}</span></div>
        <div class="combo-row"><span><i>天数</i>{esc(c['days'])}</span><span><i>人均</i>{esc(c['budget'])}</span></div>
        <p>{esc(c['note'])}</p></div></div>'''
    return f'''<section class="chapter combos-sec" id="combos">
  <div class="chap-head">
    <div class="chap-meta"><h2>组合建议 · 主线①–④</h2><span class="chap-region">Routes</span></div>
    <div class="chap-data"><span>9–10 天 · 二选一即可</span></div>
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
    <p class="disc">价格/时间为 2026-07-07 粗略估算，随季节、汇率与政策浮动，具体以出行前官方渠道为准。本页为 6 人出行投票参考，非商业用途。</p>
    <p class="made">巴厘岛及周边 · 选点手册 · 为 6 人出行制作</p></footer>'''

def mylist():
    combo_opts = "".join(f'<label class="cr"><input type="radio" name="combo" value="{c["no"]}"><span>组{c["no"]} {esc(c["name"])}</span></label>' for c in C.COMBOS)
    return f'''<button type="button" class="bar" id="bar"><span class="bar-l"><span class="bar-dot"></span>我的清单 · MY LIST</span><span class="bar-n" id="barN">0</span></button>
<div class="sheet" id="sheet" hidden>
  <div class="sheet-card" role="dialog" aria-label="我的清单" aria-modal="true">
    <div class="sheet-head"><b>我的清单</b><button type="button" class="x" id="sheetX" aria-label="关闭">×</button></div>
    <label class="fld"><span>你的名字</span><input type="text" id="nameIn" placeholder="填个名字，方便群里对号" maxlength="16"></label>
    <div class="fld"><span>主线偏好</span><div class="crs">{combo_opts}</div></div>
    <div class="picks" id="picks"></div>
    <div class="sheet-act"><button type="button" class="copy" id="copyBtn">一键复制汇总</button><button type="button" class="reset" id="resetBtn">清空</button></div>
  </div>
</div>
<div class="lb" id="lb" hidden><img id="lbImg" src="" alt=""><button type="button" class="lb-x" aria-label="关闭">×</button></div>
<div class="toast" id="toast" hidden></div>'''

# expose to JS
ITEMS_JS = json.dumps([{"id":it["id"],"zh":it["zh"]} for it in C.ITEMS], ensure_ascii=False)
COMBOS_JS = json.dumps({c["no"]: f'组{c["no"]} {c["name"]}' for c in C.COMBOS}, ensure_ascii=False)

BODY = (hero() + highlights() + '<main>' + "".join(region(r) for r in C.REGIONS)
        + combos() + prices() + notes_sec() + footer() + '</main>' + mylist())
N_IMAGES = write_images()   # BODY 里所有 img_uri 已调用完，USED_KEYS 就绪，此时才落盘

# ---------- assemble ----------
STYLE = open(os.path.join(BUILD,"style.css"), encoding="utf-8").read()
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
<script>
{SCRIPT}
</script>
</body>
</html>'''

open(os.path.join(BUILD,"index.html"),"w",encoding="utf-8").write(OUT)
kb = len(OUT.encode("utf-8"))/1024
print(f"wrote index.html : {kb:.0f} KB  (media keys: {len(MEDIA)}, videos: {len(VIDEOS)})")
print(f"wrote images/     : {N_IMAGES} files")
