# -*- coding: utf-8 -*-
import os
from playwright.sync_api import sync_playwright
BUILD = os.path.dirname(os.path.abspath(__file__))
URL = "file://" + os.path.join(BUILD, "index.html")

def shots():
    with sync_playwright() as p:
        b = p.chromium.launch()
        for theme in ["light", "dark"]:
            pg = b.new_page(viewport={"width": 390, "height": 850}, device_scale_factor=2)
            pg.goto(URL, wait_until="load"); pg.wait_for_timeout(500)
            pg.evaluate("t=>document.documentElement.setAttribute('data-theme',t)", theme)
            pg.wait_for_timeout(300)
            sw = pg.evaluate("document.body.scrollWidth"); cw = pg.evaluate("document.documentElement.clientWidth")
            print(f"[{theme}] scrollWidth={sw} clientWidth={cw} -> {'OVERFLOW!' if sw>cw+1 else 'no h-scroll ok'}")
            pg.screenshot(path=f"s_{theme}_1hero.png")
            pg.evaluate("document.getElementById('highlights').scrollIntoView()"); pg.wait_for_timeout(400)
            pg.screenshot(path=f"s_{theme}_2highlights.png")
            pg.evaluate("document.getElementById('A2').scrollIntoView({block:'start'})"); pg.wait_for_timeout(400)
            pg.screenshot(path=f"s_{theme}_3card.png")
            if theme == "light":
                # exercise voting -> stamps
                pg.click("#A2 .v-must"); pg.click("#A3 .v-must"); pg.click("#B1 .v-maybe"); pg.click("#A5 .v-maybe")
                pg.wait_for_timeout(300)
                pg.evaluate("document.getElementById('A2').scrollIntoView({block:'start'})"); pg.wait_for_timeout(300)
                pg.screenshot(path="s_light_4stamp.png")
                # open my-list sheet, set name + combo
                pg.click("#bar"); pg.wait_for_timeout(400)
                pg.fill("#nameIn", "小李"); pg.check("input[value='①']"); pg.wait_for_timeout(300)
                pg.screenshot(path="s_light_5sheet.png")
                # verify copy summary via a direct read of picks + name/combo state
                summary = pg.evaluate("""() => {
                    const picks=[...document.querySelectorAll('.pick')].map(x=>x.textContent.trim());
                    return {name: localStorage.getItem('bali_name'), combo: localStorage.getItem('bali_combo'),
                            votes: localStorage.getItem('bali_votes'), picks};
                }""")
                print("STATE:", summary)
            # combos view
            pg.evaluate("document.getElementById('combos').scrollIntoView()"); pg.wait_for_timeout(400)
            pg.screenshot(path=f"s_{theme}_6combos.png")
            pg.close()
        b.close()
    print("shots done")

shots()
