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
