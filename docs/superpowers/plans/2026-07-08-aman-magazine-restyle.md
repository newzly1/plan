# 选点手册「安缦杂志风」高端化改版 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把自包含投票网页 `webpage/index.html` 的视觉语言整体升级为高端旅行杂志质感（宋体标题 / 大留白 / 细线分层 / 方角无投影 / 全宽出血照片 / 图注体系），交互与线上链接零改动。

**Architecture:** 内容与交互不变，只重写「渲染层」。`content.py`（内容）、`app.js`（交互）**零改动**；`style.css`（皮肤）与 `build.py`（HTML 结构模板）按页面区块逐块迁移。新增两个验证工具（`check_hooks.py` 结构守卫 + `verify_page.py` Playwright 截图与交互断言）在每个任务后把关，最后一次性内嵌思源宋体子集并部署。

**Tech Stack:** Python 3 标准库（`build.py`/`check_hooks.py`）、Playwright（`verify_page.py`，已装 chromium 可用）、fonttools 4.63（字体子集）、CloudBase CLI `tcb`（部署）。

## Global Constraints

以下为全程铁律，每个任务隐含遵守：

- **`app.js` 零改动**，`content.py` 零改动（模板性装饰文字写在 `build.py`）。
- **保留所有 app.js DOM 钩子**：元素 `id`（`bar barN sheet sheetX nameIn picks copyBtn resetBtn lb lbImg toast`）、`data-id` / `data-v(must|maybe|no)` / `data-bvid` / `data-vote` / `data-playing`、类名 `.v .spot .idx .shot-img .vid .hl .combo .stamp .bar-n`、锚点 `id="region-A..E"`、`input[name="combo"]` 单选。数量基线：spot=14、vote 按钮=42、gallery 图=46、video=14、highlight=7、combo=4、region=5、上述 id 各 1。
- **纯前端**：无后端、无网络字体 URL（CSP/离线要求）；字体必须内嵌为 `@font-face` data URI 或降级系统栈。
- **双主题**：`prefers-color-scheme` + `:root[data-theme="light|dark"]` 覆盖，三处 token 同步。
- **构建**：`cd webpage && python3 build.py`，只用标准库，成功打印 `wrote index.html : <KB> KB (media keys: 60, videos: 14)`；体积 ≤ 5.9MB。
- **降级永不阻断构建**：`font.json` 缺失时 `build.py` 跳过 `@font-face`，用系统宋体栈；`media.json` 缺键时降级占位。
- **serif 字体栈（唯一权威定义，Task 2 起全程一致）**：
  `--serif:"Trip Serif","Source Han Serif SC","Noto Serif CJK SC","Songti SC","STSong","SimSun",serif;`
  （`Trip Serif`=Task 8 内嵌子集；`Noto Serif CJK SC`=本机 Playwright 验证用，与内嵌思源宋体同一字型）。
- **提交**：中文提交信息；作者沿用仓库局部配置 `zly1`；每个任务结束提交一次。
- **参照样例**：安缦杂志风提案 https://claude.ai/code/artifact/24a84bc0-c4ce-499e-9604-56aaf964d637 ，spec：`docs/superpowers/specs/2026-07-08-aman-magazine-restyle-design.md`。

---

## File Structure

| 文件 | 职责 | 本计划变更 |
|---|---|---|
| `webpage/content.py` | 内容唯一源 | **不改** |
| `webpage/app.js` | 交互（投票/清单/复制/灯箱/视频） | **不改** |
| `webpage/style.css` | 全部样式（token + 各区块皮肤） | 逐块重写（Task 2–7） |
| `webpage/build.py` | 渲染器：拼装自包含 index.html | hero/章节头/图注结构调整 + `@font-face` 注入（Task 2–7）；**保留全部钩子** |
| `webpage/check_hooks.py` | 结构守卫：断言钩子数量（stdlib） | **新增**（Task 1） |
| `webpage/verify_page.py` | Playwright 截图 + 交互断言 | **新增**（Task 1） |
| `webpage/fetch_font.py` | 一次性：思源宋体子集 → font.json | **新增**（Task 8） |
| `webpage/font.json` | 内嵌 woff2/woff base64 | **新增**（Task 8，入库以便离线重建） |

**验证约定（所有任务通用）**：
- 结构门（自动，必过）：`python3 build.py` 成功 + `python3 check_hooks.py` 打印 `OK`。
- 视觉/交互门（自动截图 + 人工看图）：`SHOTS=<scratchpad>/shots python3 verify_page.py`，断言全 PASS 且退出码 0；生成的 PNG 由评审在任务间人工核对气质。
- `<scratchpad>` = 本会话临时目录 `/tmp/claude-1000/-mnt-hgfs-sharedFile-claudePlan/8f84825a-1e9d-4d8f-a460-bbb58432d7a0/scratchpad`。

---

### Task 1: 验证工具（结构守卫 + Playwright 截图/断言）

先立「回归网」：一个 stdlib 结构守卫，一个 Playwright 交互+截图工具。都在**当前未改动的 index.html** 上跑成基线绿，锁定契约。

**Files:**
- Create: `webpage/check_hooks.py`
- Create: `webpage/verify_page.py`
- Test: 对现有 `webpage/index.html` 运行两者（基线）

**Interfaces:**
- Produces: 命令 `python3 check_hooks.py`（退出码 0=通过）；命令 `SHOTS=<dir> python3 verify_page.py`（退出码 0=通过，PNG 落 `<dir>`）。后续每个任务都调用这两者。

- [ ] **Step 1: 写结构守卫 `check_hooks.py`**

```python
# -*- coding: utf-8 -*-
"""结构守卫：断言 app.js 依赖的 DOM 钩子在构建产物里数量正确。
只数 HTML 属性写法（id="x" / class="x" / data-x="），CSS(.x{) 与内联 JS(.closest) 文本不会误命中。
期望值从 content.py + videos.json 推导，内容或渲染漂移都会被抓到。仅用标准库。
用法：python3 check_hooks.py  → 打印 OK 或 FAILED，退出码 0/1。"""
import json, os, sys
import content as C

BUILD = os.path.dirname(os.path.abspath(__file__))
def load(n):
    p = os.path.join(BUILD, n)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
VIDEOS = load("videos.json")

html = open(os.path.join(BUILD, "index.html"), encoding="utf-8").read()
body = html.split("<script>")[0]  # 去掉内联 app.js，避免其选择器字符串干扰计数

items      = len(C.ITEMS)
subspots   = sum(len(it["subspots"]) for it in C.ITEMS)
vids       = sum(1 for it in C.ITEMS if VIDEOS.get(it["id"]))
combos     = len(C.COMBOS)
highlights = len(C.HIGHLIGHTS)
regions    = len(C.REGIONS)

expect = {
    'id="barN"':1, 'id="bar"':1, 'id="sheet"':1, 'id="sheetX"':1, 'id="nameIn"':1,
    'id="picks"':1, 'id="copyBtn"':1, 'id="resetBtn"':1, 'id="lb"':1, 'id="lbImg"':1, 'id="toast"':1,
    'class="spot"':items, 'data-id="':items, 'class="stamp"':items,
    'data-v="must"':items, 'data-v="maybe"':items, 'data-v="no"':items,
    'class="shot"':subspots, 'data-bvid="':vids,
    'class="hl"':highlights, 'class="combo"':combos, 'name="combo"':combos,
    'class="idx':regions + 1,   # 5 区 + 1 精选
}
fails = []
for pat, n in expect.items():
    got = body.count(pat)
    if got != n:
        fails.append(f"  {pat!r}: expected {n}, got {got}")
for r in C.REGIONS:
    if f'id="region-{r["id"]}"' not in body:
        fails.append(f'  missing anchor id="region-{r["id"]}"')

if fails:
    print("HOOK GUARD FAILED:")
    print("\n".join(fails))
    sys.exit(1)
print(f"OK: all hooks present (spot={items} vote={items*3} shot={subspots} "
      f"vid={vids} hl={highlights} combo={combos} region={regions})")
```

- [ ] **Step 2: 跑守卫，确认对当前 index.html 通过（基线）**

Run: `cd webpage && python3 check_hooks.py`
Expected: `OK: all hooks present (spot=14 vote=42 shot=46 vid=14 hl=7 combo=4 region=5)`

- [ ] **Step 3: 写 Playwright 工具 `verify_page.py`**

```python
# -*- coding: utf-8 -*-
"""Playwright 验收：对 index.html 跑交互断言 + 出框选截图（浅/深 × 手机/桌面）。
用法：SHOTS=/path/to/dir python3 verify_page.py
退出码 0=全部断言 PASS。截图 PNG 落 SHOTS 目录，供人工核对气质。"""
import os, sys, pathlib
from playwright.sync_api import sync_playwright

BUILD = pathlib.Path(__file__).resolve().parent
URL = (BUILD / "index.html").as_uri()
SHOTS = pathlib.Path(os.environ.get("SHOTS", BUILD / "_shots"))
SHOTS.mkdir(parents=True, exist_ok=True)

fails = []
def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond: fails.append(msg)

def clip_of(page, sel):
    box = page.locator(sel).first.bounding_box()
    if not box: return None
    return {"x":box["x"], "y":box["y"], "width":box["width"], "height":min(box["height"],2200)}

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ---------- 交互断言（浅色手机）----------
    ctx = browser.new_context(viewport={"width":390,"height":844}, color_scheme="light")
    page = ctx.new_page(); page.goto(URL); page.wait_for_timeout(400)

    must = page.locator('.spot#A1 .v[data-v="must"]')
    must.click(); page.wait_for_timeout(150)
    check(page.locator('.spot#A1').get_attribute("data-vote")=="must", "投票必去 → data-vote=must")
    check(must.get_attribute("aria-pressed")=="true", "必去按钮 aria-pressed=true")
    check(page.locator('.spot#A1 .stamp').is_visible(), "必去盖章可见")
    check(page.locator('#barN').inner_text().strip()=="1", "底栏计数 #barN=1")
    must.click(); page.wait_for_timeout(120)
    check(page.locator('.spot#A1').get_attribute("data-vote") in (None,""), "再点必去 → 取消")
    check(page.locator('#barN').inner_text().strip()=="0", "取消后 #barN=0")

    page.locator('#bar').click(); page.wait_for_timeout(200)
    check(page.locator('#sheet').is_visible(), "点底栏 → 清单弹层打开")
    check(page.locator('#copyBtn').count()==1 and page.locator('#nameIn').count()==1, "弹层含复制按钮与姓名输入")
    page.locator('#sheetX').click(); page.wait_for_timeout(200)
    check(not page.locator('#sheet').is_visible(), "关闭清单弹层")

    img = page.locator('.shot-img').first
    if img.get_attribute("src"):
        img.click(); page.wait_for_timeout(200)
        check(page.locator('#lb').is_visible(), "点图 → 灯箱打开")
        page.locator('#lb').click(); page.wait_for_timeout(150)
        check(not page.locator('#lb').is_visible(), "关闭灯箱")

    check(page.locator('.idx').count()>=6, "索引导航 .idx ≥ 6")
    ctx.close()

    # ---------- 框选截图（浅/深 × 手机）----------
    for scheme in ("light","dark"):
        ctx = browser.new_context(viewport={"width":390,"height":844}, color_scheme=scheme)
        page = ctx.new_page(); page.goto(URL); page.wait_for_timeout(400)
        page.screenshot(path=str(SHOTS/f"m-hero-{scheme}.png"))  # 顶部一屏
        for sel, name in [('.spot#A1',"spot"), ('#combos',"combos")]:
            if page.locator(sel).count():
                page.locator(sel).first.scroll_into_view_if_needed(); page.wait_for_timeout(200)
                clip = clip_of(page, sel)
                if clip: page.screenshot(path=str(SHOTS/f"m-{name}-{scheme}.png"), clip=clip)
        page.locator('#bar').click(); page.wait_for_timeout(250)   # 清单弹层
        page.screenshot(path=str(SHOTS/f"m-sheet-{scheme}.png"))
        ctx.close()

    # ---------- 桌面顶部（浅色）----------
    ctx = browser.new_context(viewport={"width":1200,"height":900}, color_scheme="light")
    page = ctx.new_page(); page.goto(URL); page.wait_for_timeout(400)
    page.screenshot(path=str(SHOTS/"d-hero-light.png"))
    ctx.close()
    browser.close()

print(f"\nshots → {SHOTS}")
if fails:
    print(f"{len(fails)} FAIL"); sys.exit(1)
print("ALL PASS"); sys.exit(0)
```

- [ ] **Step 4: 跑 Playwright 工具，确认对当前 index.html 全 PASS（基线 + before 截图）**

Run: `cd webpage && SHOTS=<scratchpad>/shots/before python3 verify_page.py`
Expected: 末尾 `ALL PASS`，退出码 0；`<scratchpad>/shots/before/` 下生成 `m-hero-*.png` 等。评审人可看到「改版前」样貌存档。

- [ ] **Step 5: 提交**

```bash
cd /mnt/hgfs/sharedFile/claudePlan
git add webpage/check_hooks.py webpage/verify_page.py
git commit -m "新增改版验证工具：结构守卫 check_hooks 与 Playwright 截图/断言 verify_page"
```

---

### Task 2: 设计基座（token + 字体注入 + 排版基础）

替换 `style.css` 顶部所有 `:root` token 块为新调色板（骨白纸 / 墨 / 松绿 / 黄铜），保留旧 token 名作别名以便未迁移区块继续工作；把方角/去投影/衬线栈接上；`build.py` 加 `@font-face` 注入槽（读 `font.json`，缺失则跳过）。此步全站立即换色变方，是一个连贯可交付的中间态。

**Files:**
- Modify: `webpage/style.css`（第 1–61 行区间：token 三块 + 基础层）
- Modify: `webpage/build.py`（`load()` 增读 font.json；新增 `font_face()`；`OUT` 的 `<style>` 注入）

**Interfaces:**
- Consumes: Task 1 的 `check_hooks.py` / `verify_page.py`。
- Produces: CSS 变量 `--ground --surface --ink --ink-soft --ink-faint --line --line-2 --line-strong --pine --pine-soft --brass --brass-bright --brass-soft --serif --font-cjk --font-mono --rad --maxw`，及别名 `--gold --gold-bright --gold-soft --sea --sea-soft`（指向新值）；`build.py` 的 `font_face()`（font.json 有则返回 `@font-face{...}` 字符串，无则返回 `""`）。

- [ ] **Step 1: 替换 `style.css` 顶部 token + 基础层（第 1–61 行）**

把文件开头到 `.facts,.chap-data,...{font-family:var(--font-mono)}`（含）整段替换为：

```css
/* ===== 印尼群岛 · 选点手册 — 安缦杂志风 identity ===== */
*,*::before,*::after{box-sizing:border-box}
:root{
  /* 权威调色板：骨白纸 / 墨 / 松绿 / 黄铜 */
  --ground:#FAF8F2; --ground-2:#F1EEE4; --surface:#F4F1E8; --surface-2:#FCFAF3;
  --ink:#1B1815; --ink-soft:#575147; --ink-faint:#8A8272;
  --line:#E5E0D4; --line-2:#D8D2C4; --line-strong:#1B1815;
  --pine:#1E4D44; --pine-soft:rgba(30,77,68,.10);
  --brass:#9C7C3C; --brass-bright:#B08A3F; --brass-soft:rgba(156,124,60,.12);
  /* 向后兼容别名（未迁移区块读这些，指向新值，迁移完可清理） */
  --gold:var(--brass); --gold-bright:var(--brass-bright); --gold-soft:var(--brass-soft);
  --sea:var(--pine); --sea-soft:var(--pine-soft);
  --shadow:none; --shadow-lg:0 14px 44px rgba(27,24,21,.16);
  --font-cjk:"PingFang SC","Hiragino Sans GB","Microsoft YaHei","Noto Sans SC",system-ui,-apple-system,"Segoe UI",sans-serif;
  --serif:"Trip Serif","Source Han Serif SC","Noto Serif CJK SC","Songti SC","STSong","SimSun",serif;
  --font-mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;
  --rad:0px; --maxw:760px;
}
@media (prefers-color-scheme:dark){:root{
  --ground:#16140F; --ground-2:#1D1A14; --surface:#1D1A14; --surface-2:#221E17;
  --ink:#EDE7DA; --ink-soft:#B3AA97; --ink-faint:#857C69;
  --line:#2E2A22; --line-2:#3C382F; --line-strong:#EDE7DA;
  --pine:#4E9A8A; --pine-soft:rgba(78,154,138,.15);
  --brass:#C29A54; --brass-bright:#C29A54; --brass-soft:rgba(194,154,84,.15);
  --shadow:none; --shadow-lg:0 16px 48px rgba(0,0,0,.5);
}}
:root[data-theme="light"]{
  --ground:#FAF8F2; --ground-2:#F1EEE4; --surface:#F4F1E8; --surface-2:#FCFAF3;
  --ink:#1B1815; --ink-soft:#575147; --ink-faint:#8A8272;
  --line:#E5E0D4; --line-2:#D8D2C4; --line-strong:#1B1815;
  --pine:#1E4D44; --pine-soft:rgba(30,77,68,.10);
  --brass:#9C7C3C; --brass-bright:#B08A3F; --brass-soft:rgba(156,124,60,.12);
  --shadow:none; --shadow-lg:0 14px 44px rgba(27,24,21,.16);
}
:root[data-theme="dark"]{
  --ground:#16140F; --ground-2:#1D1A14; --surface:#1D1A14; --surface-2:#221E17;
  --ink:#EDE7DA; --ink-soft:#B3AA97; --ink-faint:#857C69;
  --line:#2E2A22; --line-2:#3C382F; --line-strong:#EDE7DA;
  --pine:#4E9A8A; --pine-soft:rgba(78,154,138,.15);
  --brass:#C29A54; --brass-bright:#C29A54; --brass-soft:rgba(194,154,84,.15);
  --shadow:none; --shadow-lg:0 16px 48px rgba(0,0,0,.5);
}

html{-webkit-text-size-adjust:100%}
body{margin:0}
.hero,.shelf,main,.bar,.sheet,.lb,.toast{font-family:var(--font-cjk)}
body,.hero{background:var(--ground);color:var(--ink)}
img{display:block;max-width:100%}
h1,h2,h3,h4,p{margin:0}
a{color:inherit;text-decoration:none}
button{font-family:inherit;cursor:pointer}
:focus-visible{outline:2.5px solid var(--pine);outline-offset:2px;border-radius:2px}

/* 衬线标题域：仅这些标题走宋体，正文与数据保持黑体/等宽 */
.hero h1,.chap-meta h2,.spot-title h3,.combo-b h3,.hl-cap b,.sheet-head b,.stamp::after{
  font-family:var(--serif);font-weight:600;letter-spacing:.03em}

/* placeholders while media loads */
.ph{background:
  repeating-linear-gradient(135deg,var(--ground-2),var(--ground-2) 10px,var(--surface) 10px,var(--surface) 20px);
  display:grid;place-items:center;color:var(--ink-faint);font-family:var(--font-mono);font-size:12px;text-align:center;padding:8px}
.ph span{opacity:.8}

/* mono 字段标签 helper */
.facts,.chap-data,.combo-row i,.mt i,.code,.en,.tag,.hl-code,.vid-badge,.idx b,.bar-n,.num,.note-k,.tip-k,.cap-line,.mast-l,.mast-r,.chap-region{
  font-family:var(--font-mono)}
```

- [ ] **Step 2: `build.py` 增读 font.json 与注入槽**

在 `build.py` 第 13 行 `CREDITS = load("credits.json")` 之后新增一行：

```python
FONT = load("font.json")         # {"serif_woff2": "<b64>"} 或 {"serif_woff": "<b64>"}；缺失则降级系统宋体栈
```

在 `build.py` 的 `esc()`/`img_uri()` 附近（第 16 行后）新增函数：

```python
def font_face():
    """有内嵌子集则输出 @font-face（'Trip Serif'）；否则空串，降级到系统宋体栈。"""
    if FONT.get("serif_woff2"):
        return ("@font-face{font-family:'Trip Serif';font-style:normal;font-weight:600;font-display:swap;"
                "src:url(data:font/woff2;base64,%s) format('woff2')}\n" % FONT["serif_woff2"])
    if FONT.get("serif_woff"):
        return ("@font-face{font-family:'Trip Serif';font-style:normal;font-weight:600;font-display:swap;"
                "src:url(data:font/woff;base64,%s) format('woff')}\n" % FONT["serif_woff"])
    return ""
```

把 `OUT` 模板里的 `<style>\n{STYLE}\n</style>`（第 192–194 行）改为：

```python
<style>
{font_face()}{STYLE}
</style>
```

- [ ] **Step 3: 构建 + 结构门**

Run: `cd webpage && python3 build.py && python3 check_hooks.py`
Expected: `wrote index.html : ~5500 KB (media keys: 60, videos: 14)` 且 `OK: all hooks present (...)`（font.json 尚不存在，`font_face()` 返回空，正常降级）。

- [ ] **Step 4: 视觉/交互门**

Run: `cd webpage && SHOTS=<scratchpad>/shots/t2 python3 verify_page.py`
Expected: `ALL PASS`。人工看 `m-hero-light.png` / `m-hero-dark.png`：整页应变为骨白纸底、方角、无卡片投影，标题呈**衬线宋体**（本机 Noto Serif CJK SC 生效），点缀色转为松绿/黄铜；深色为「墨纸夜读」。此时仍是旧布局、仅换色换字，属预期中间态。

- [ ] **Step 5: 提交**

```bash
cd /mnt/hgfs/sharedFile/claudePlan
git add webpage/style.css webpage/build.py
git commit -m "改版基座：安缦杂志风 token 与衬线栈，build 接入 @font-face 注入槽（缺字体自动降级）"
```

---

### Task 3: Hero 封面 + 报头 + 索引导航

Hero 从「图上叠字」改为杂志封面式：报头小注 → 居中短墨线 → 宋体大标题 → 宽字距副题 → small-caps facts → 全宽出血封面照 + 图注行 → howto → 细线包夹的文字目录。

**Files:**
- Modify: `webpage/build.py`（`hero()`，第 26–44 行整函数）
- Modify: `webpage/style.css`（HERO 区块，原 `/* ====== HERO ====== */` 到 `.idx-star b{...}` 整段）

**Interfaces:**
- Consumes: `--serif --brass --pine --line --line-strong --ink-faint` 等 token。
- Produces: hero 新类 `.masthead .mast-l .mast-r .hero-title .rule .cap-line`；保留 `.hero .hero-media .hero-img .facts .hero-foot .howto .index .idx .idx b .idx span .idx-star`（钩子/锚点不变）。

- [ ] **Step 1: 替换 `build.py` 的 `hero()`（第 26–44 行）**

```python
def hero():
    m = C.META
    idx = "".join(f'<a class="idx" href="#region-{r["id"]}"><b>{r["id"]}</b><span>{esc(r["name"].split(" (")[0])}</span></a>' for r in C.REGIONS)
    return f'''<header class="hero">
  <div class="masthead"><span class="mast-l">INDONESIA · 巴厘岛及周边</span><span class="mast-r">FIELD NOTES · 2026</span></div>
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
```

- [ ] **Step 2: 替换 `style.css` 的 HERO 区块**

把 `/* ============ HERO ============ */` 到 `.idx-star b{color:var(--gold-bright)}`（含）整段替换为：

```css
/* ============ HERO（杂志封面式）============ */
.hero{max-width:var(--maxw);margin:0 auto}
.masthead{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:18px 20px 0;
  font-size:10.5px;letter-spacing:.24em;text-transform:uppercase;color:var(--ink-faint)}
.hero-title{padding:36px 22px 24px;text-align:center}
.hero-title .rule{display:block;width:36px;height:1px;background:var(--line-strong);margin:0 auto 22px}
.hero h1{font-size:clamp(30px,7vw,44px);line-height:1.3;color:var(--ink);text-wrap:balance}
.hero .sub{margin-top:15px;font-size:13px;letter-spacing:.26em;color:var(--ink-soft)}
.facts{display:flex;flex-wrap:wrap;justify-content:center;gap:9px 18px;margin-top:22px;
  font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--ink-faint)}
.hero-media{position:relative;margin:0;isolation:isolate}
.hero-img{width:100%;aspect-ratio:4/4.4;object-fit:cover;object-position:center 35%;filter:saturate(1.03)}
@media (prefers-color-scheme:dark){.hero-img{filter:saturate(1.03) brightness(.94)}}
:root[data-theme="dark"] .hero-img{filter:saturate(1.03) brightness(.94)}
.cap-line{display:flex;justify-content:space-between;gap:12px;padding:11px 22px 0;
  font-size:9.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--ink-faint)}
.cap-line span:last-child{color:var(--brass)}
.hero-foot{padding:28px 22px 8px}
.howto{font-size:13.5px;line-height:1.85;color:var(--ink-soft);max-width:58ch;margin:0 auto;text-align:center}
.index{display:flex;flex-wrap:wrap;margin-top:26px;border-top:1px solid var(--line-strong);border-bottom:1px solid var(--line-strong)}
.idx{flex:1 0 30%;display:flex;align-items:center;justify-content:center;gap:8px;padding:13px 12px;
  border-right:1px solid var(--line);border-top:1px solid var(--line);white-space:nowrap}
.idx b{color:var(--brass);font-size:11px;font-weight:700}
.idx span{font-size:12.5px;color:var(--ink)}
.idx-star b{color:var(--pine)}
```

- [ ] **Step 3: 构建 + 结构门**

Run: `cd webpage && python3 build.py && python3 check_hooks.py`
Expected: 构建成功；`OK: all hooks present (...)`（`.idx` 仍为 6）。

- [ ] **Step 4: 视觉/交互门**

Run: `cd webpage && SHOTS=<scratchpad>/shots/t3 python3 verify_page.py`
Expected: `ALL PASS`。看 `m-hero-light/dark.png` 与 `d-hero-light.png`：报头小注在顶、居中短线、宋体大标题、宽字距副题、facts 一行 small-caps、其下全宽封面照带 `Kelingking · Nusa Penida / Fig. 01` 图注、底部文字目录被上下墨线包夹。

- [ ] **Step 5: 提交**

```bash
cd /mnt/hgfs/sharedFile/claudePlan
git add webpage/build.py webpage/style.css
git commit -m "Hero 改杂志封面式：报头+宋体大标题+全宽出血封面+图注+细线文字目录"
```

---

### Task 4: 精华速览货架

`.hl` 卡从「文字压图」改为「图上 + 细线图注下」，宋体小标题 + 黑体一句话；眉题改黄铜 small-caps。

**Files:**
- Modify: `webpage/build.py`（`highlights()`，第 46–56 行）
- Modify: `webpage/style.css`（HIGHLIGHTS shelf 区块 + `.chap-eyebrow` 两处）

**Interfaces:**
- Consumes: `--serif --brass --line --ink-soft`。
- Produces: `.hl-cap`（改为静态图注）、`.hl-sub`；保留 `.shelf .shelf-scroll .hl .hl-img .shelf-note .chap-eyebrow .chap-eyebrow .k`（`.hl` 钩子不变）。

- [ ] **Step 1: 替换 `build.py` 的 `highlights()`（第 46–56 行）**

```python
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
```

- [ ] **Step 2: 替换 `style.css` 的共享 `.chap-eyebrow`（原第 90–93 行）与 HIGHLIGHTS 区块**

先把 `/* ============ shared chapter bits ============ */` 下的 `.chap-eyebrow{...}` 与 `.chap-eyebrow .k{...}` 两条替换为：

```css
/* ============ shared chapter bits ============ */
.chap-eyebrow{font-size:10px;letter-spacing:.3em;text-transform:uppercase;color:var(--brass);margin:0 4px 16px}
.chap-eyebrow .k{color:var(--brass);margin-right:10px;letter-spacing:.3em}
```

再把 `/* ============ HIGHLIGHTS shelf ============ */` 到 `.shelf-note{...}`（含）整段替换为：

```css
/* ============ HIGHLIGHTS shelf（图上·图注下）============ */
.shelf{max-width:var(--maxw);margin:0 auto;padding:38px 0 10px}
.shelf .chap-eyebrow{padding:0 22px}
.shelf-scroll{display:flex;gap:16px;overflow-x:auto;padding:6px 22px 18px;scroll-snap-type:x mandatory;
  -webkit-overflow-scrolling:touch;scrollbar-width:none}
.shelf-scroll::-webkit-scrollbar{display:none}
.hl{flex:0 0 60%;max-width:250px;scroll-snap-align:start;background:transparent;overflow:visible}
.hl-img{width:100%;aspect-ratio:3/3.7;object-fit:cover}
.hl-cap{padding:11px 0 13px;border-bottom:1px solid var(--line);display:flex;flex-direction:column;gap:4px}
.hl-cap b{font-size:15.5px;color:var(--ink)}
.hl-sub{font-size:11.5px;line-height:1.55;color:var(--ink-soft)}
.shelf-note{padding:4px 22px 0;font-size:12.5px;color:var(--ink-faint);line-height:1.65;max-width:600px}
```

- [ ] **Step 3: 构建 + 结构门**

Run: `cd webpage && python3 build.py && python3 check_hooks.py`
Expected: 成功；`OK`（`.hl` 仍为 7）。

- [ ] **Step 4: 视觉/交互门**

Run: `cd webpage && SHOTS=<scratchpad>/shots/t4 python3 verify_page.py`
Expected: `ALL PASS`。看 `m-hero-*.png`（货架在 hero 下方一屏内）：横滑卡为「竖图 + 图下细线图注（宋体标题 + 黑体一句话）」，眉题黄铜 small-caps。

- [ ] **Step 5: 提交**

```bash
cd /mnt/hgfs/sharedFile/claudePlan
git add webpage/build.py webpage/style.css
git commit -m "精华速览改杂志图注式：竖图+细线图注（宋体标题），眉题黄铜 small-caps"
```

---

### Task 5: 章节头 + 景点卡（含投票与盖章）

页面主体。章节头去掉字母方块、改「墨色粗线顶边 + 宋体章节名 + 右侧 Region 黄铜小注」；景点卡去卡片感（无框/无圆角/无投影）改文章式区块，图集图注化、标签松绿 small-caps、视频板去圆角黄铜徽标、meta 细线顶边；投票钮改方角字距钮，盖章改单色钢印。

**Files:**
- Modify: `webpage/build.py`（`gallery()` 第 58–63；`video_plate()` 第 65–74；`spot()` 第 76–99；`region()` 第 101–113）
- Modify: `webpage/style.css`（CHAPTER + SPOT card + gallery + video + meta + notes + VOTE+STAMP 各区块）

**Interfaces:**
- Consumes: `--serif --pine --pine-soft --brass --brass-soft --line --line-2 --line-strong --ink --ink-soft --ink-faint`。
- Produces: 章节头新类 `.chap-region`；景点卡沿用全部钩子类。**保留**：`.chapter #region-X .chap-head .chap-meta h2 .chap-data .chap-desc .spot[data-id] .stamp .spot-head .code .spot-title h3 .en .pick-star .tags .tag .gallery .shot .shot-img figcaption .vid[data-bvid] .vid-img .vid-play .vid-badge .vid-cap .vid-frame .spot-meta .mt details.notes summary .chev .note .note-k .vote .v[data-v]`。

- [ ] **Step 1: 替换 `build.py` 的 `region()`（第 101–113 行）——章节头去字母方块**

```python
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
```

- [ ] **Step 2: 替换 `build.py` 的 `spot()`（第 76–99 行）——编号进图注行、结构微调（钩子不变）**

```python
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
```

> 注：`spot()`/`gallery()`/`video_plate()` 的 HTML 结构与原版保持一致（钩子零风险），本任务外观全部由 CSS 完成。`gallery()`（第 58–63）、`video_plate()`（第 65–74）**不改**。

- [ ] **Step 3: 替换 `style.css` 的 CHAPTER 区块（原第 113–125 行）**

把 `/* ============ CHAPTER ============ */` 到 `.chap-desc{...}`（含）整段替换为：

```css
/* ============ CHAPTER（墨线顶边 + 宋体章名 + Region 小注）============ */
.chapter{padding:44px 0 8px;scroll-margin-top:12px}
.chap-head{border-top:1.5px solid var(--line-strong);padding-top:16px}
.chap-meta{display:flex;align-items:baseline;justify-content:space-between;gap:12px}
.chap-meta h2{font-size:clamp(21px,4.6vw,26px);line-height:1.3;text-wrap:balance}
.chap-region{flex:0 0 auto;font-size:10.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--brass)}
.chap-data{display:flex;flex-wrap:wrap;align-items:center;gap:9px;margin-top:10px;font-size:10.5px;
  letter-spacing:.1em;text-transform:uppercase;color:var(--ink-faint)}
.chap-data i{width:3px;height:3px;border-radius:50%;background:var(--line-2)}
.chap-desc{margin:16px 2px 24px;font-size:13.5px;line-height:1.85;color:var(--ink-soft);max-width:64ch}
```

- [ ] **Step 4: 替换 `style.css` 的 SPOT card 区块（原第 127–149 行：`.spot` 到 `.shot figcaption span`）**

```css
/* ============ SPOT（文章式，无卡片感）============ */
.spot{position:relative;background:transparent;border:0;border-top:1px solid var(--line);
  border-radius:0;padding:26px 0 24px;margin:0;box-shadow:none;scroll-margin-top:12px}
.spot:first-of-type{border-top:0}
.spot-head{display:flex;align-items:baseline;gap:12px}
.code{flex:0 0 auto;font-size:11px;font-weight:700;letter-spacing:.1em;color:var(--brass);
  border:0;border-radius:0;padding:0;background:none}
.spot-title{min-width:0}
.spot-title h3{font-size:19px;line-height:1.28;display:flex;align-items:baseline;gap:8px}
.pick-star{color:var(--pine);font-size:12px}
.en{display:block;font-size:10.5px;letter-spacing:.16em;color:var(--ink-faint);margin-top:4px;text-transform:uppercase}
.tags{display:flex;flex-wrap:wrap;gap:6px 14px;margin:12px 0 2px}
.tag{font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--pine);background:none;padding:0;border-radius:0}
.tag::before{content:"· "}

/* gallery（去圆角 + 图注式）*/
.gallery{display:flex;gap:12px;overflow-x:auto;margin:14px 0 0;padding:4px 0 12px;
  scroll-snap-type:x mandatory;-webkit-overflow-scrolling:touch;scrollbar-width:none}
.gallery::-webkit-scrollbar{display:none}
.shot{margin:0;flex:0 0 76%;max-width:340px;scroll-snap-align:start}
.shot-img{width:100%;aspect-ratio:4/3;object-fit:cover;border-radius:0;background:var(--ground-2);cursor:zoom-in}
.shot-img.ph{aspect-ratio:4/3;cursor:default}
.shot figcaption{display:flex;flex-direction:column;gap:2px;margin-top:9px;padding-bottom:10px;border-bottom:1px solid var(--line)}
.shot figcaption b{font-size:13px;font-weight:600}
.shot figcaption span{font-size:9.5px;letter-spacing:.16em;color:var(--ink-faint);text-transform:uppercase}
@media (prefers-color-scheme:dark){.shot-img{filter:brightness(.95)}}
:root[data-theme="dark"] .shot-img{filter:brightness(.95)}
```

- [ ] **Step 5: 替换 `style.css` 的 video plate 区块（原第 151–168 行）**

```css
/* video plate（去圆角 + 黄铜徽标）*/
.vid{position:relative;display:block;margin-top:16px;border-radius:0;overflow:hidden;aspect-ratio:16/9;
  background:#0c0a08;isolation:isolate;cursor:pointer}
.vid-img{width:100%;height:100%;object-fit:cover;opacity:.94;transition:opacity .2s,transform .3s}
.vid:hover .vid-img{opacity:1;transform:scale(1.02)}
.vid-play{position:absolute;top:50%;left:50%;width:56px;height:56px;transform:translate(-50%,-50%);
  border-radius:50%;background:rgba(20,14,8,.5);backdrop-filter:blur(2px);border:1.5px solid rgba(255,255,255,.9)}
.vid-play::after{content:"";position:absolute;top:50%;left:54%;transform:translate(-50%,-50%);
  border-style:solid;border-width:9px 0 9px 15px;border-color:transparent transparent transparent #fff}
.vid-badge{position:absolute;top:12px;left:12px;font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;
  color:var(--ink);background:var(--brass-bright);padding:4px 9px;border-radius:0}
.vid-cap{position:absolute;inset:auto 0 0 0;padding:28px 14px 12px;color:#fff;font-size:12.5px;line-height:1.4;font-weight:600;
  background:linear-gradient(0deg,rgba(6,4,2,.9),transparent);display:flex;flex-direction:column;gap:3px}
.vid-cap i{font-style:normal;font-size:9.5px;font-weight:400;letter-spacing:.1em;text-transform:uppercase;color:#cdbfa8;font-family:var(--font-mono)}
.vid[data-playing]{background:#000;cursor:default}
.vid-frame{width:100%;height:100%;border:0;display:block}
.vid[data-playing] .vid-img,.vid[data-playing] .vid-play,.vid[data-playing] .vid-badge,.vid[data-playing] .vid-cap{display:none}
```

- [ ] **Step 6: 替换 `style.css` 的 meta + notes 区块（原第 170–185 行）**

```css
/* meta（细线顶边）*/
.spot-meta{display:flex;flex-wrap:wrap;gap:10px 28px;margin-top:18px;padding-top:14px;border-top:1px solid var(--line)}
.mt{font-size:12.5px;line-height:1.55;color:var(--ink)}
.mt i{display:block;font-style:normal;font-size:9px;letter-spacing:.18em;text-transform:uppercase;color:var(--ink-faint);margin-bottom:3px}

/* notes fold */
details.notes{margin-top:6px;border-top:1px solid var(--line);padding-top:2px}
details.notes summary,.fold summary{list-style:none;display:flex;align-items:center;justify-content:space-between;
  gap:10px;padding:12px 0;cursor:pointer;font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--ink-soft)}
details.notes summary::-webkit-details-marker,.fold summary::-webkit-details-marker{display:none}
.chev{width:8px;height:8px;border-right:1.5px solid var(--ink-faint);border-bottom:1.5px solid var(--ink-faint);
  transform:rotate(45deg);transition:transform .2s}
details[open]>summary .chev{transform:rotate(-135deg)}
.note{display:flex;gap:12px;padding:8px 0}
.note-k{flex:0 0 auto;font-size:9.5px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--brass);padding-top:3px;width:34px}
.note p{font-size:13px;line-height:1.8;color:var(--ink-soft)}
```

- [ ] **Step 7: 替换 `style.css` 的 VOTE + STAMP 区块（原第 187–208 行）**

```css
/* ===== VOTE + STAMP（方角文字钮 + 单色钢印）===== */
.vote{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:20px}
.v{padding:13px 6px;border-radius:0;border:1px solid var(--line-strong);background:transparent;color:var(--ink);
  font-size:12px;font-weight:600;letter-spacing:.28em;text-indent:.28em;
  transition:background .15s,color .15s,border-color .15s}
.v-no{border-color:var(--line-2);color:var(--ink-soft)}
.v:active{transform:translateY(1px)}
.v-must[aria-pressed="true"]{background:var(--pine);border-color:var(--pine);color:#F6F3EA}
.v-maybe[aria-pressed="true"]{background:var(--ink);border-color:var(--ink);color:var(--ground)}
.v-no[aria-pressed="true"]{background:var(--ground-2);border-color:var(--line-2);color:var(--ink-soft)}

.stamp{position:absolute;top:20px;right:0;z-index:3;width:74px;height:74px;border-radius:50%;
  display:none;place-items:center;transform:rotate(-13deg);pointer-events:none;
  font-size:19px;font-weight:600;letter-spacing:.08em;opacity:.92;
  animation:stampin .28s cubic-bezier(.2,1.4,.4,1)}
.spot[data-vote="must"] .stamp{display:grid;color:var(--pine);border:1.5px solid var(--pine)}
.spot[data-vote="must"] .stamp::after{content:"必去"}
.spot[data-vote="maybe"] .stamp{display:grid;color:var(--ink);border:1.5px solid var(--ink)}
.spot[data-vote="maybe"] .stamp::after{content:"可去"}
@keyframes stampin{0%{opacity:0;transform:rotate(-13deg) scale(1.6)}100%{opacity:.92;transform:rotate(-13deg) scale(1)}}
```

- [ ] **Step 8: 构建 + 结构门**

Run: `cd webpage && python3 build.py && python3 check_hooks.py`
Expected: 成功；`OK: all hooks present (spot=14 vote=42 shot=46 vid=14 ...)`。

- [ ] **Step 9: 视觉/交互门**

Run: `cd webpage && SHOTS=<scratchpad>/shots/t5 python3 verify_page.py`
Expected: `ALL PASS`（含投票→盖章→计数、灯箱断言）。看 `m-spot-light/dark.png`：景点为文章式细线分隔区块，编号黄铜、标题宋体、标签松绿 `· 海滩` small-caps、图集图注化、视频黄铜徽标、投票为方角宽字距钮；触发必去后右上角出现松绿钢印圆章。

- [ ] **Step 10: 提交**

```bash
cd /mnt/hgfs/sharedFile/claudePlan
git add webpage/build.py webpage/style.css
git commit -m "章节头与景点卡改杂志式：墨线章名+文章式区块+图注图集+松绿标签+方角投票钮+单色钢印"
```

---

### Task 6: 后记区块（组合建议 + 价格/贴士折叠 + 页脚）

组合改细线列表（宋体大编号黄铜色，去框）；价格/贴士折叠改细线包围、标题黄铜 small-caps、表格数字 tabular-nums；页脚 small-caps。同时把 combos 的章节头也切到 Task 5 的新样式（去掉 `.chap-letter`）。

**Files:**
- Modify: `webpage/build.py`（`combos()` 第 115–128）
- Modify: `webpage/style.css`（COMBOS + FOLDS + FOOTER 区块；删除已无用的 `.chap-letter` 规则）

**Interfaces:**
- Consumes: `--serif --brass --pine --line --line-2 --ink --ink-soft --ink-faint`。
- Produces: 保留 `.combos .combo .combo-no .combo-b h3 .combo-row .fold .fold-note .ptable .num .tips .tip .tip-k .foot .made`；combos 章节头复用 `.chap-head .chap-meta .chap-region`。

- [ ] **Step 1: 替换 `build.py` 的 `combos()`（第 115–128 行）——章节头去字母方块，与 region 对齐**

```python
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
```

- [ ] **Step 2: 删除 `style.css` 里已无用的 `.chap-letter` 两条规则（原第 116–119 行）**

删除 `.chap-letter{...}` 与 `.chap-letter.alt{...}`（region/combos 都已不再产出该元素）。删除后 `.chap-meta{padding-top:1px}`（原第 120 行）若与 Task 5 新 `.chap-meta` 冲突，一并删除该旧行。

- [ ] **Step 3: 替换 `style.css` 的 COMBOS 区块（原第 210–220 行）**

```css
/* ============ COMBOS（细线列表 + 宋体大编号）============ */
.combos{display:flex;flex-direction:column;margin-top:8px}
.combo{display:flex;gap:16px;background:transparent;border:0;border-top:1px solid var(--line);
  border-radius:0;padding:18px 0;box-shadow:none}
.combo:first-child{border-top:0}
.combo-no{flex:0 0 auto;font-family:var(--serif);font-size:30px;font-weight:600;color:var(--brass);line-height:1}
.combo-b{min-width:0}
.combo-b h3{font-size:16.5px;margin-bottom:11px;text-wrap:balance}
.combo-row{display:flex;flex-wrap:wrap;gap:6px 22px;margin-bottom:6px}
.combo-row span{font-size:12.5px;color:var(--ink)}
.combo-row i{font-style:normal;font-size:9px;letter-spacing:.16em;text-transform:uppercase;color:var(--ink-faint);margin-right:7px}
.combo-b p{font-size:12.5px;line-height:1.75;color:var(--ink-soft);margin-top:8px}
```

- [ ] **Step 4: 替换 `style.css` 的 FOLDS 区块（原第 222–237 行）**

```css
/* ============ FOLDS: prices + tips（细线包围）============ */
.fold{max-width:var(--maxw);margin:18px auto 0;background:transparent;border:1px solid var(--line-strong);
  border-radius:0;padding:2px 18px;box-shadow:none}
.fold>summary{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--ink);padding:16px 0}
.fold-note{font-size:12px;color:var(--ink-faint);line-height:1.65;padding:0 0 12px}
.ptable{margin:8px 0 16px}
.ptable h4{font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:var(--brass);margin-bottom:9px}
.tw{overflow-x:auto}
.ptable table{width:100%;border-collapse:collapse;font-size:13px}
.ptable td{padding:9px 4px;border-bottom:1px solid var(--line);vertical-align:top}
.ptable td.num{text-align:right;color:var(--ink-soft);font-family:var(--font-mono);white-space:nowrap;font-variant-numeric:tabular-nums}
.tips{display:flex;flex-direction:column;padding-bottom:14px}
.tip{display:flex;gap:14px;padding:11px 0;border-bottom:1px solid var(--line)}
.tip:last-child{border-bottom:none}
.tip-k{flex:0 0 auto;width:46px;font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--pine)}
.tip p{font-size:13px;line-height:1.75;color:var(--ink-soft)}
```

- [ ] **Step 5: 替换 `style.css` 的 FOOTER 区块（原第 239–242 行）**

```css
/* ============ FOOTER ============ */
.foot{max-width:var(--maxw);margin:34px auto 0;padding:24px 0 130px;border-top:1.5px solid var(--line-strong)}
.foot p{font-size:11px;line-height:1.75;color:var(--ink-faint);margin-bottom:9px}
.foot .made{font-family:var(--font-mono);letter-spacing:.16em;text-transform:uppercase;color:var(--ink-soft);margin-top:14px}
```

- [ ] **Step 6: 构建 + 结构门**

Run: `cd webpage && python3 build.py && python3 check_hooks.py`
Expected: 成功；`OK`（`.combo` 仍为 4）。

- [ ] **Step 7: 视觉/交互门**

Run: `cd webpage && SHOTS=<scratchpad>/shots/t6 python3 verify_page.py`
Expected: `ALL PASS`。看 `m-combos-light/dark.png`：组合为细线分隔列表、左侧宋体大编号黄铜色；展开价格折叠（可另跑一次手动看）应为细线表格、数字右对齐等宽。

- [ ] **Step 8: 提交**

```bash
cd /mnt/hgfs/sharedFile/claudePlan
git add webpage/build.py webpage/style.css
git commit -m "后记区块改版：组合细线列表+宋体大编号、价格/贴士细线折叠、页脚 small-caps，清理无用 chap-letter"
```

---

### Task 7: 应用外壳（底栏 + 清单弹层 + 灯箱 + Toast）

底栏从黑色悬浮胶囊改为全宽细线底条（骨白底 + 墨色顶线 + 黄铜计数）；弹层方角细线、输入框方角、pick 小签方角（必去松绿/可去墨色）；灯箱/Toast 视觉对齐。交互与 id 全不动。

**Files:**
- Modify: `webpage/build.py`（`mylist()` 第 159–172，仅结构微调，id 不变）
- Modify: `webpage/style.css`（MY LIST bar + sheet + lightbox + toast 区块）

**Interfaces:**
- Consumes: `--serif --pine --brass --line --line-strong --ink --ground --surface`。
- Produces: 保留全部 id 与 `.bar .bar-l .bar-dot .bar-n .sheet .sheet-card .sheet-head .x .fld .crs .cr .picks .picks-grp .pick .pc .picks-empty .sheet-act .copy .reset .lb .lb-x .toast`。

- [ ] **Step 1: `build.py` 的 `mylist()`（第 161 行底栏）微调结构（id 不变）**

把第 161 行底栏按钮：

```python
    return f'''<button type="button" class="bar" id="bar"><span class="bar-l"><span class="bar-dot"></span>我的清单</span><span class="bar-n" id="barN">0</span></button>
```

替换为（加一个 small-caps 提示，仍是同一个 `#bar` 按钮、`#barN` 计数）：

```python
    return f'''<button type="button" class="bar" id="bar"><span class="bar-l"><span class="bar-dot"></span>我的清单 · MY LIST</span><span class="bar-n" id="barN">0</span></button>
```

其余（`#sheet #sheetX #nameIn #picks #copyBtn #resetBtn #lb #lbImg #toast`）**不改**。

- [ ] **Step 2: 替换 `style.css` 的 MY LIST bar + sheet 区块（原第 244–286 行）**

```css
/* ============ MY LIST bar（全宽细线底条）============ */
.bar{position:fixed;left:0;right:0;bottom:0;transform:none;z-index:40;display:flex;align-items:center;justify-content:space-between;
  gap:12px;max-width:var(--maxw);margin:0 auto;padding:16px 22px;border-radius:0;
  border:0;border-top:1.5px solid var(--line-strong);background:var(--ground);color:var(--ink);
  box-shadow:0 -8px 24px rgba(27,24,21,.06);font-size:11px;letter-spacing:.16em;text-transform:uppercase;font-weight:600;transition:none}
.bar:active{background:var(--ground-2)}
.bar-l{display:flex;align-items:center;gap:11px}
.bar-dot{width:7px;height:7px;border-radius:50%;background:var(--pine)}
.bar-n{min-width:24px;height:24px;padding:0 7px;border-radius:0;border:1px solid var(--brass);background:transparent;color:var(--brass);
  display:grid;place-items:center;font-size:12px;font-weight:700;letter-spacing:0}

.sheet{position:fixed;inset:0;z-index:50;display:flex;align-items:flex-end;justify-content:center;
  background:rgba(15,12,8,.5);backdrop-filter:blur(3px)}
.sheet[hidden]{display:none}
.sheet-card{width:100%;max-width:var(--maxw);max-height:86vh;overflow-y:auto;background:var(--ground);
  border-radius:2px 2px 0 0;border-top:1.5px solid var(--line-strong);padding:8px 22px calc(24px + env(safe-area-inset-bottom));
  box-shadow:var(--shadow-lg);animation:up .26s cubic-bezier(.2,.9,.3,1)}
@keyframes up{from{transform:translateY(100%)}to{transform:translateY(0)}}
.sheet-head{display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;background:var(--ground);
  padding:16px 0 13px;border-bottom:1px solid var(--line);z-index:2}
.sheet-head b{font-size:18px}
.x{width:34px;height:34px;border-radius:0;border:1px solid var(--line-2);background:transparent;color:var(--ink);
  font-size:20px;line-height:1;display:grid;place-items:center}
.fld{display:block;margin:14px 0 18px}
.fld>span{display:block;font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:var(--ink-faint);margin-bottom:9px}
#nameIn{width:100%;padding:13px 14px;border-radius:0;border:1px solid var(--line-strong);background:var(--surface-2);
  color:var(--ink);font-size:15px;font-family:inherit}
.crs{display:flex;flex-direction:column;gap:8px}
.cr{display:flex;align-items:center;gap:11px;padding:12px 13px;border:1px solid var(--line);border-radius:0;
  background:transparent;font-size:13.5px}
.cr:has(input:checked){border-color:var(--pine);background:var(--pine-soft)}
.cr input{accent-color:var(--pine);width:18px;height:18px;flex:0 0 auto}
.picks{display:flex;flex-direction:column;gap:8px;margin-bottom:18px}
.picks-grp{font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:var(--ink-faint);margin:8px 0 2px}
.pick{display:flex;align-items:center;gap:10px;font-size:14px;padding:3px 0}
.pick .pc{font-family:var(--font-mono);font-size:10.5px;font-weight:700;padding:2px 7px;border-radius:0}
.pick.must .pc{color:#F6F3EA;background:var(--pine)}
.pick.maybe .pc{color:var(--ground);background:var(--ink)}
.picks-empty{font-size:13.5px;color:var(--ink-faint);line-height:1.7;padding:8px 0}
.sheet-act{display:flex;gap:10px;position:sticky;bottom:0;background:var(--ground);padding:14px 0 4px;border-top:1px solid var(--line)}
.copy{flex:1;padding:15px;border-radius:0;border:1px solid var(--pine);background:var(--pine);color:#F6F3EA;
  font-size:12px;font-weight:700;letter-spacing:.16em;text-transform:uppercase}
.reset{flex:0 0 auto;padding:15px 18px;border-radius:0;border:1px solid var(--line-2);background:transparent;color:var(--ink-soft);
  font-size:11px;letter-spacing:.12em;text-transform:uppercase}
```

- [ ] **Step 3: 替换 `style.css` 的 lightbox + toast 区块（原第 288–300 行）**

```css
/* lightbox */
.lb{position:fixed;inset:0;z-index:60;display:grid;place-items:center;background:rgba(15,12,8,.94);padding:20px}
.lb[hidden]{display:none}
.lb img{max-width:100%;max-height:90vh;border-radius:0;object-fit:contain}
.lb-x{position:absolute;top:16px;right:16px;width:42px;height:42px;border-radius:0;border:1px solid rgba(255,255,255,.4);
  background:rgba(0,0,0,.4);color:#fff;font-size:24px;line-height:1}

/* toast */
.toast{position:fixed;left:50%;bottom:96px;transform:translateX(-50%) translateY(10px);z-index:70;
  background:var(--ink);color:var(--ground);padding:12px 22px;border-radius:0;font-size:12px;font-weight:600;letter-spacing:.1em;
  box-shadow:var(--shadow-lg);opacity:0;transition:opacity .2s,transform .2s;pointer-events:none}
.toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
.toast[hidden]{display:none}
```

- [ ] **Step 4: 构建 + 结构门**

Run: `cd webpage && python3 build.py && python3 check_hooks.py`
Expected: 成功；`OK`（11 个 id 各 1）。

- [ ] **Step 5: 视觉/交互门**

Run: `cd webpage && SHOTS=<scratchpad>/shots/t7 python3 verify_page.py`
Expected: `ALL PASS`（含底栏点击→弹层打开→关闭断言）。看 `m-sheet-light/dark.png`：底栏为全宽细线条（黄铜方框计数）；弹层方角、细线、pick 小签方角（必去松绿/可去墨）。

- [ ] **Step 6: 提交**

```bash
cd /mnt/hgfs/sharedFile/claudePlan
git add webpage/build.py webpage/style.css
git commit -m "应用外壳改版：全宽细线底栏+方角清单弹层/灯箱/Toast，交互与 id 不变"
```

---

### Task 8: 内嵌思源宋体子集（设备无关的衬线保证）

生成标题域子集 woff2 存入 `font.json`，`build.py` 已有的 `font_face()` 会自动内嵌为 `'Trip Serif'`。这样低端安卓/无宋体设备也呈现与本机 Noto Serif CJK 一致的衬线（思源宋体与 Noto Serif CJK 同源）。下载走 curl（已验证可达 11.2MB 源），子集走 fonttools（已装）；woff2 需 brotli，缺则装镜像或退 woff。

**Files:**
- Create: `webpage/fetch_font.py`
- Create: `webpage/font.json`（由脚本产出，入库）

**Interfaces:**
- Consumes: `content.py`（收集标题域用字）。
- Produces: `font.json` = `{"serif_woff2": "<b64>"}`（或退化键 `"serif_woff"`）；被 `build.py` 的 `font_face()`（Task 2）读取。

- [ ] **Step 1: 确认 brotli（woff2 需要），缺则装镜像；装不上则脚本自动退 woff**

Run: `python3 -c "import brotli" 2>/dev/null && echo has-brotli || pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple brotli`
Expected: 打印 `has-brotli`，或镜像装成功。装不上也不阻塞——Step 2 脚本会自动退回 woff（无需 brotli）。

- [ ] **Step 2: 写 `fetch_font.py`**

```python
# -*- coding: utf-8 -*-
"""一次性：把思源宋体 SemiBold 子集到标题域用字，写 webpage/font.json。
build.py 的 font_face() 会内嵌为 @font-face 'Trip Serif'。
依赖 fonttools（已装）；woff2 需 brotli，缺则自动退 woff。下载走 curl（本机 urllib 会卡）。
用法：python3 fetch_font.py"""
import os, sys, json, base64, subprocess, tempfile, io
import content as C

BUILD = os.path.dirname(os.path.abspath(__file__))
OTF_URL = "https://github.com/adobe-fonts/source-han-serif/raw/release/SubsetOTF/CN/SourceHanSerifCN-SemiBold.otf"

def title_glyphs():
    chars = set()
    def add(s):
        for ch in str(s): chars.add(ch)
    add(C.META["title"]); add(C.META["subtitle"])
    for r in C.REGIONS: add(r["name"])
    for it in C.ITEMS:
        add(it["zh"]); add(it["en"])
        for s in it["subspots"]: add(s["zh"])
    for h in C.HIGHLIGHTS: add(h["title"])
    for c in C.COMBOS: add(c["name"]); add(c["no"])
    # build.py 里的标题域字面量 + 盖章字 + 组合/区块标题 + 拉丁与数字
    add("巴厘岛及周边选点手册印尼群岛精华速览组合建议主线单项参考价人民币粗估全程通用注意事项必去可去无所谓我的清单")
    add("ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz 0123456789 ·—–.&/()②①③④")
    return "".join(sorted(chars))

def main():
    glyphs = title_glyphs()
    print(f"glyphs: {len(glyphs)} unique")
    tmp = tempfile.mkdtemp(); otf = os.path.join(tmp, "src.otf")
    print("curl 下载思源宋体 SemiBold ...")
    r = subprocess.run(["curl","-fsSL","-o",otf,OTF_URL])
    if r.returncode != 0 or not os.path.exists(otf) or os.path.getsize(otf) < 100000:
        print("ERROR: 字体下载失败（需代理）。跳过；build 将降级系统宋体栈。"); sys.exit(1)

    try:
        import brotli  # noqa
        flavor, key = "woff2", "serif_woff2"
    except ImportError:
        flavor, key = "woff", "serif_woff"
        print("提示：未装 brotli，改用 woff（体积略大，功能等价）。")

    from fontTools.subset import Subsetter, Options
    from fontTools.ttLib import TTFont
    opts = Options(); opts.flavor = flavor; opts.desubroutinize = True
    opts.layout_features = []            # 标题无需 OT 特性
    opts.name_IDs = []; opts.notdef_outline = True
    opts.recalc_bounds = True; opts.drop_tables = ["FFTM"]
    font = TTFont(otf, fontNumber=0)
    ss = Subsetter(options=opts); ss.populate(text=glyphs); ss.subset(font)
    buf = io.BytesIO(); font.save(buf); data = buf.getvalue()

    b64 = base64.b64encode(data).decode()
    json.dump({key: b64}, open(os.path.join(BUILD, "font.json"), "w"))
    print(f"wrote font.json : {flavor} {len(data)//1024} KB, base64 {len(b64)//1024} KB (key={key})")

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: 运行子集脚本**

Run: `cd webpage && python3 fetch_font.py`
Expected: 打印 `glyphs: <N> unique` 与 `wrote font.json : woff2 <~120> KB ...`（或 `woff ...`）。若打印下载失败——按 CLAUDE.md 确认本地代理后重试；仍失败则跳过本任务，页面以系统 Noto/Songti 衬线上线（Task 2 已保证降级）。

- [ ] **Step 4: 重新构建 + 结构门**

Run: `cd webpage && python3 build.py && python3 check_hooks.py`
Expected: `wrote index.html : <≤5900> KB ...`（含内嵌字体）；`OK: all hooks present`。

- [ ] **Step 5: 视觉门（确认 'Trip Serif' 生效且体积达标）**

Run: `cd webpage && SHOTS=<scratchpad>/shots/t8 python3 verify_page.py`
Expected: `ALL PASS`；标题衬线与 Task 5 一致（内嵌思源宋体 = 本机 Noto Serif CJK 同源，视觉持平），差异在于现在**任何设备**都拿到该字型。核对 `index.html` ≤ 5.9MB。

- [ ] **Step 6: 提交**

```bash
cd /mnt/hgfs/sharedFile/claudePlan
git add webpage/fetch_font.py webpage/font.json webpage/index.html
git commit -m "内嵌思源宋体 SemiBold 标题子集：设备无关的衬线保证，build 自动降级仍可用"
```

---

### Task 9: 全量回归 + 上线部署

跑齐四张主题×尺寸截图人工验收，交互断言全绿，然后覆盖部署到 CloudBase，最后线上抽验。

**Files:**
- Modify: `webpage/index.html`（最终构建产物）
- Update: `webpage/README.md`（如需，注明「安缦杂志风」皮肤与 `fetch_font.py`）

**Interfaces:**
- Consumes: 前 8 个任务的全部产物。

- [ ] **Step 1: 干净重建 + 双门全绿**

Run: `cd webpage && python3 build.py && python3 check_hooks.py && SHOTS=<scratchpad>/shots/final python3 verify_page.py`
Expected: 构建成功（≤5.9MB）；`OK: all hooks present`；`ALL PASS`。

- [ ] **Step 2: 人工验收四图**

看 `<scratchpad>/shots/final/` 下 `m-hero-{light,dark}.png`、`m-spot-{light,dark}.png`、`m-combos-{light,dark}.png`、`m-sheet-{light,dark}.png`、`d-hero-light.png`。核对：整体呈安缦杂志气质（宋体标题 / 大留白 / 细线 / 方角 / 全宽照片 / 图注）；深浅两主题都清晰、点缀色（松绿/黄铜）在两底色上都可读；无横向溢出、无元素重叠。

- [ ] **Step 3: 交互回归复查（手动跑一遍关键路径）**

用浏览器打开 `webpage/index.html`（或 `python3 -m http.server` 后访问），确认：投票三态互斥与取消→钢印出现/消失→底栏计数；清单弹层姓名/主线单选持久化（刷新保留）；一键复制文案格式；清空确认；图片灯箱开关；B 站视频点击原地播放且同时仅一个；索引锚点平滑滚动；两个折叠面板；`prefers-reduced-motion` 下无 reveal 动画。

- [ ] **Step 4: 部署到 CloudBase（覆盖上线，链接不变）**

Run: `cd webpage && tcb hosting deploy index.html index.html -e plan-d0gstt7r6507aa319`
Expected: 部署成功回执（CDN 数分钟刷新）。若提示未登录：`tcb login --flow device` 扫码后重试。

- [ ] **Step 5: 线上抽验**

打开 https://plan-d0gstt7r6507aa319-1451599494.tcloudbaseapp.com （CDN 刷新后），确认新皮肤已上线、投票与复制可用。

- [ ] **Step 6: 提交（如改了 README）**

```bash
cd /mnt/hgfs/sharedFile/claudePlan
git add webpage/index.html webpage/README.md
git commit -m "安缦杂志风改版定稿：全量回归通过并部署 CloudBase"
```

---

## Self-Review

**1. Spec coverage（逐条对照 spec）**

- 色板（骨白/墨/松绿/黄铜，双主题）→ Task 2 ✓
- 字体（内嵌思源宋体 SemiBold 子集 + 系统回退栈 + build 降级）→ Task 2（栈+注入槽/降级）、Task 8（子集）✓
- 版式（方角/去投影/细线/宋体标题/图注/大留白）→ Task 2–7 各区块 ✓
- 12 项组件改造清单：Hero(T3)、精华速览(T4)、章节头(T5)、景点卡(T5)、投票钮(T5)、盖章(T5)、组合(T6)、折叠(T6)、底栏(T7)、弹层(T7)、灯箱/Toast(T7)、页脚(T6) ✓
- 文件变更表（style.css 重写 / build.py 结构+字体注入 / fetch_font.py / font.json / app.js 零改）→ File Structure + 各任务 ✓
- 验收清单（构建≤5.9MB / 四主题尺寸截图 / 交互回归 / reduced-motion / 部署）→ Task 9 + 各任务 verify_page ✓
- 风险与对策（字体下载失败降级 / fonttools 镜像 / 低端安卓 / 深色照片偏亮）→ Task 8 降级路径、Task 3/5 深色 `brightness()` ✓

**2. Placeholder scan**：无 TBD/TODO；每个改代码步骤给出完整可粘贴代码；命令均含预期输出。✓

**3. Type/契约一致性**：
- token 名全程一致（`--pine/--brass/--line-strong/--serif` + 别名 `--gold/--sea`），Task 2 定义、后续引用一致。
- `font_face()` 键名 `serif_woff2`/`serif_woff` 在 Task 2（读）与 Task 8（写）一致。
- 钩子基线（spot=14 vote=42 shot=46 vid=14 hl=7 combo=4 region=5、11 个 id）在 `check_hooks.py` 与 Global Constraints 一致。
- `verify_page.py` 断言的选择器（`.spot#A1 .v[data-v="must"]`、`#bar`、`#sheet`、`.shot-img`、`.idx`）均为保留钩子。
- `.chap-letter` 生命周期已处理：Task 5 起 region 不再产出，Task 6 combos 亦切换并删除其 CSS——无悬挂引用。

修正记录：将字体子集从「late/optional」提前明确为 Task 8 并接入本机 Noto Serif CJK 验证链路（因 Playwright 在 Linux 上需显式衬线字型才能忠实预览）；Task 2 提前铺设 `@font-face` 注入与降级，确保任何一步都能独立构建、部署。

---

## Execution Handoff

计划已保存到 `docs/superpowers/plans/2026-07-08-aman-magazine-restyle.md`。两种执行方式：

1. **Subagent-Driven（推荐）** — 每个任务派新子代理执行、任务间我来审（含看截图），迭代快、上下文干净。
2. **Inline Execution** — 本会话内按 executing-plans 分批执行，设检查点复核。

选哪种？
