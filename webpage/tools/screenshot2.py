# -*- coding: utf-8 -*-
import os
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); URL = "file://" + os.path.join(ROOT, "dist", "index.html")
with sync_playwright() as p:
    b = p.chromium.launch()
    for theme in ["light", "dark"]:
        pg = b.new_page(viewport={"width": 390, "height": 850}, device_scale_factor=2)
        pg.goto(URL, wait_until="load"); pg.wait_for_timeout(500)
        pg.evaluate("t=>document.documentElement.setAttribute('data-theme',t)", theme); pg.wait_for_timeout(300)
        sw = pg.evaluate("document.body.scrollWidth"); cw = pg.evaluate("document.documentElement.clientWidth")
        print(f"[{theme}] hscroll={'OVERFLOW' if sw>cw+1 else 'ok'}")
        pg.screenshot(path=f"t_{theme}_hero.png")
        if theme == "light":
            pg.evaluate("document.getElementById('highlights').scrollIntoView()"); pg.wait_for_timeout(400)
            pg.screenshot(path="t_highlights.png")
            pg.evaluate("document.getElementById('combos').scrollIntoView()"); pg.wait_for_timeout(400)
            pg.screenshot(path="t_combos.png")
            pg.evaluate("document.getElementById('prices').setAttribute('open',''); document.getElementById('prices').scrollIntoView()"); pg.wait_for_timeout(300)
            pg.screenshot(path="t_prices.png")
            pg.evaluate("window.scrollTo(0, document.body.scrollHeight)"); pg.wait_for_timeout(400)
            pg.screenshot(path="t_footer.png")
        pg.close()
    b.close()
print("done")
