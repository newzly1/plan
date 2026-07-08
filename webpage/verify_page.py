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
