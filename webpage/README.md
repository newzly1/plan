# 巴厘岛及周边 · 6 人选点手册 — 网页源码

这是投票参考网页的**完整生成源码**。一条命令即可从源码重新生成自包含的 `index.html`（约 5.4 MB，图片/视频封面全部内嵌，无需联网即可打开）。

- **在线版（Artifact）**：https://claude.ai/code/artifact/b157e3f4-4102-4bbe-8004-d67ce5f0332c
  修改后让 Claude 用 Artifact 工具把新的 `index.html` **重新发布到同一个 URL**（覆盖更新，链接不变）。
- **内容源头**：`../印尼旅行项目投票清单.md`（所有文字由此转写进 `content.py`）
- **设计说明**：`../docs/superpowers/specs/2026-07-07-bali-trip-voting-webpage-design.md`

---

## 快速修改（最常用）

改内容/样式/交互，然后重新构建即可：

```bash
cd webpage
python3 build.py          # 读 content.py + *.json + style.css + app.js → 写 index.html
```

`build.py` 只用 Python 标准库，**不需要装任何东西**。构建成功会打印：
`wrote index.html : 5496 KB (media keys: 60, videos: 14)`。

| 想改什么 | 改哪个文件 |
|---|---|
| 景点文字、价格、注意事项、组合线路、精华速览 | `content.py`（唯一内容源） |
| 配色、排版、卡片样式、深浅色主题 | `style.css` |
| 投票逻辑、「我的清单」、一键复制、灯箱 | `app.js` |
| 换/加/删一张景点图或视频封面 | 见下方「重新抓取媒体」 |

改完 `content.py` / `style.css` / `app.js` 后跑一次 `python3 build.py`，`index.html` 就更新了。

---

## 文件说明

**源码（手改这些）**
- `content.py` — 全部内容数据：`META / REGIONS / ITEMS / HIGHLIGHTS / COMBOS / PRICES / NOTES`。每个景点含子点 `subspots`（带英文 Commons 检索词 `q`）和视频检索词 `video_q`。
- `style.css` — 全部样式（"印尼群岛 · 选点手册"田野图鉴风格，火山深色 / 石灰岩浅色双主题）。
- `app.js` — 前端交互：护照盖章式投票（必去/可去）、本地「我的清单」、一键复制汇总、图片灯箱。纯 `localStorage`，无后端。
- `build.py` — 渲染器：把上面几样拼成自包含 `index.html`。

**媒体数据（`build.py` 读取，通常不用手改）**
- `media.json` — 所有图片和视频封面，已编码成 WebP `data:` URI（约 4.5 MB，页面体积主要来自它）。
- `videos.json` — 每个景点的 YouTube 视频 `{yt_id, title, author}`。
- `credits.json` — Wikimedia Commons 图片的作者与许可（页脚署名用）。

**抓取管线（只有要换图/重抓时才用，需联网 + Pillow）**
- `fetch_candidates.py` → `candidates.json`：按 `content.py` 里的 `q` 去 Commons 找候选图。
- `fetch_media.py`：把 `raw/*.img` 编码成 WebP 存进 `media.json`，并抓 YouTube 封面、收集署名。
- `raw/`（47 张原图）、`vraw/`（14 张视频封面原图）— **保留的原始素材**，可离线重新压缩/换质量，省得再联网下载。
- 一次性辅助脚本：`fix_options.py`、`finalize_fixes.py`、`patch_media.py`、`make_contactsheet.py`、`opt.json`、`api.json`（历史构建过程留存，改内容用不到）。
- `screenshot.py` / `screenshot2.py` — 用 Playwright 给 `index.html` 截图做验收（需另装 Playwright chromium）。

---

## 构建管线

```
content.py  ─┐
raw/*.img ──→ fetch_media.py ──→ media.json ─┐
videos.json ─┘                    credits.json┤
                                  style.css   ├─→ build.py ──→ index.html（自包含）
                                  app.js      ┘
```

改文字/样式/交互 → 只需 `build.py`。
换图/重抓 → 先 `fetch_media.py`（要 `pip install Pillow`，且能联网），再 `build.py`。

## 重新抓取媒体（进阶）

```bash
pip install Pillow
python3 fetch_candidates.py   # 可选：刷新 Commons 候选（改了 content.py 的 q 时）
python3 fetch_media.py        # raw/ + vraw/ → media.json + credits.json
python3 build.py              # 重新生成 index.html
```

> 环境注意：本机 Bash 联网只能走本地代理的 `curl`（`urllib`/`npm` 会卡住）；脚本里已用 `curl` 抓取。要换某张图，把新原图放进 `raw/<子点id>.img`（如 `raw/B1a.img`）再跑 `fetch_media.py` 即可。

---

## 说明
- 内容源文档里的「本次不纳入」部分是刻意不放进页面的；C2 林贾尼、D2 船宿保留在册。
- 价格/时间为 2026 年粗估，随季节汇率浮动，仅作 6 人出行投票参考、非商业用途；图片来自 Wikimedia Commons 等公开来源，版权归原作者。
