# -*- coding: utf-8 -*-
"""一次性：把思源宋体 SemiBold 子集到标题域用字，写 webpage/font.json。
build.py 的 font_face() 会内嵌为 @font-face 'Trip Serif'。
依赖 fonttools（已装）；woff2 需 brotli，缺则自动退 woff。下载走 curl（本机 urllib 会卡）。
用法：python3 fetch_font.py"""
import os, sys, json, base64, subprocess, tempfile, io
import content as C

BUILD = os.path.dirname(os.path.abspath(__file__))
# 主源 + 镜像（github raw 在本地代理下常被限流 429，jsdelivr 走同一 GitHub 仓库/同一文件内容）
OTF_URLS = [
    "https://github.com/adobe-fonts/source-han-serif/raw/release/SubsetOTF/CN/SourceHanSerifCN-SemiBold.otf",
    "https://cdn.jsdelivr.net/gh/adobe-fonts/source-han-serif@release/SubsetOTF/CN/SourceHanSerifCN-SemiBold.otf",
]

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

def download(dest):
    for url in OTF_URLS:
        print(f"curl 下载思源宋体 SemiBold ... {url}")
        r = subprocess.run(["curl", "-fsSL", "--retry", "2", "-o", dest, url])
        if r.returncode == 0 and os.path.exists(dest) and os.path.getsize(dest) >= 100000:
            return True
        print(f"  失败（returncode={r.returncode}），尝试下一个源 ...")
    return False

def main():
    glyphs = title_glyphs()
    print(f"glyphs: {len(glyphs)} unique")
    tmp = tempfile.mkdtemp(); otf = os.path.join(tmp, "src.otf")
    if not download(otf):
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
    font.flavor = flavor  # Subsetter.subset() 不会自动设置；不设的话 save() 仍写出未压缩 OTF(OTTO) 而非 woff2/woff
    buf = io.BytesIO(); font.save(buf); data = buf.getvalue()

    b64 = base64.b64encode(data).decode()
    json.dump({key: b64}, open(os.path.join(BUILD, "font.json"), "w"))
    print(f"wrote font.json : {flavor} {len(data)//1024} KB, base64 {len(b64)//1024} KB (key={key})")

if __name__ == "__main__":
    main()
