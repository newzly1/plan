# 巴厘岛及周边 · 6 人选点手册 — 网页源码

这是投票参考网页的**完整生成源码**。一条命令即可从源码重新生成页面：`index.html`（外壳，约 160 KB）+ `images/`（约 60 张 WebP 图片/视频封面，共约 7 MB）。两者需放在同一目录下打开/部署，仍然全离线可用，无需请求 CDN 之外的任何东西。

- **在线版 · 国内可直连（腾讯云 CloudBase）**：https://plan-d0gstt7r6507aa319-1451599494.tcloudbaseapp.com
  发给 6 人投票用的正式链接，**无需梯子**。改完内容重新构建后，用下方「重新部署到 CloudBase」一节的命令覆盖上线，链接不变。
- **在线版（Claude Artifact，需梯子）**：https://claude.ai/code/artifact/b157e3f4-4102-4bbe-8004-d67ce5f0332c
  ⚠️ **图片拆分为 `images/` 后此链接会失效**：Artifact 只能发布单个自包含文件，且有严格 CSP、无法加载外部 `images/` 目录，重新发布只会看到裂图的壳。以 CloudBase 链接为准；如果还需要这条 Artifact 备用链接，需要另外想办法（比如临时把图片重新内联成一份专供 Artifact 用的 `index.html`），本次未处理。
- **内容源头**：`../印尼旅行项目投票清单.md`（所有文字由此转写进 `content.py`）
- **设计说明**：`../docs/superpowers/specs/2026-07-07-bali-trip-voting-webpage-design.md`
- **项目速览（给 Claude）**：`../CLAUDE.md`（构建、CloudBase 部署与续期、环境要点）

---

## 快速修改（最常用）

改内容/样式/交互，然后重新构建即可：

```bash
cd webpage
python3 build.py          # 读 content.py + *.json + style.css + app.js → 写 index.html + images/*.webp
```

`build.py` 只用 Python 标准库，**不需要装任何东西**。构建成功会打印：
```
wrote index.html : 162 KB  (media keys: 60, videos: 14)
wrote images/     : 60 files
```

| 想改什么 | 改哪个文件 |
|---|---|
| 景点文字、价格、注意事项、组合线路、精华速览 | `content.py`（唯一内容源） |
| 配色、排版、卡片样式、深浅色主题 | `style.css` |
| 投票逻辑、「我的清单」、一键复制、灯箱 | `app.js` |
| 换同一景点/视频下的一张图（key 不变） | 见下方「重新抓取媒体」——只需重新部署那一张图，`index.html` 不用动 |
| 新增/删除景点或视频（key 变化） | 见下方「重新抓取媒体」，之后 `images/` 和 `index.html` 都要重新部署 |

改完 `content.py` / `style.css` / `app.js` 后跑一次 `python3 build.py`，`index.html` 就更新了（`images/` 内容不受影响，因为图片路径只取决于景点 key，不取决于文字/样式）。

---

## 重新部署到 CloudBase（让线上链接也更新）

投票链接 https://plan-d0gstt7r6507aa319-1451599494.tcloudbaseapp.com 托管在腾讯云 CloudBase 静态托管（国内可直连）。页面现在是 `index.html` + `images/` 两个部署目标，改完内容重新构建后按下表挑一条或两条命令覆盖上线，链接不变：

```bash
cd webpage
python3 build.py                                                    # 先重新生成 index.html + images/
tcb hosting deploy images images -e plan-d0gstt7r6507aa319          # 图片文件夹变化时才需要
tcb hosting deploy index.html index.html -e plan-d0gstt7r6507aa319  # 文字/样式/交互变化时才需要（CDN 数分钟内刷新）
```

| 改了什么 | 需要重新部署 |
|---|---|
| `content.py` / `style.css` / `app.js` | 只需 `index.html` |
| 换同一 key 下的图（如替换 `raw/B1a.img`） | **只需那一张图**，`index.html` 文本不变，例：`tcb hosting deploy images/B1a.webp images/B1a.webp -e plan-d0gstt7r6507aa319` |
| 新增景点/视频（新 key） | `images/`（新文件）+ `index.html`（新增引用） |

首次上线或不确定改了什么时，两条命令都跑一遍最保险（建议先传 `images`，避免线上 `index.html` 一度引用还不存在的图片路径）。

- **环境 ID**：`plan-d0gstt7r6507aa319`（腾讯云 CloudBase 免费体验版）。
- **首次配置**：`npm i -g @cloudbase/cli --registry=https://registry.npmmirror.com`（本机默认 npm 源会卡，故用国内镜像），再 `tcb login --flow device` 扫码登录。
- ⚠️ **续期**：免费环境 **2027-01-08 到期**，到期前需在 [CloudBase 控制台](https://console.cloud.tencent.com/tcb) 手动续 6 个月，否则环境销毁、链接失效（不支持自动续费）。

---

## 文件说明

**源码（手改这些）**
- `content.py` — 全部内容数据：`META / REGIONS / ITEMS / HIGHLIGHTS / COMBOS / PRICES / NOTES`。每个景点含子点 `subspots`（带英文 Commons 检索词 `q`）和视频检索词 `video_q`。
- `style.css` — 全部样式（"印尼群岛 · 选点手册"田野图鉴风格，火山深色 / 石灰岩浅色双主题）。
- `app.js` — 前端交互：护照盖章式投票（必去/可去）、本地「我的清单」、一键复制汇总、图片灯箱。纯 `localStorage`，无后端。
- `build.py` — 渲染器：把上面几样拼成自包含 `index.html`。

**媒体数据（`build.py` 读取，通常不用手改）**
- `media.json` — 所有图片和视频封面，已编码成 WebP base64（约 8.85 MB）。
- `images/` — `build.py` 从 `media.json` 解码生成的约 60 个 `.webp` 文件，`index.html` 里的 `<img src>` 指向这里（如 `images/A1a.webp`）；每次 `python3 build.py` 都会覆盖生成，随 `index.html` 一起提交/部署。换同一 key 下的图时文件名不变，无需重新部署 `index.html`。
- `videos.json` — 每个景点的哔哩哔哩视频 `{bvid, title, author}`。
- `credits.json` — Wikimedia Commons 图片的作者与许可（页脚署名用）。

**抓取管线（只有要换图/重抓时才用，需联网 + Pillow）**
- `fetch_candidates.py` → `candidates.json`：按 `content.py` 里的 `q` 去 Commons 找候选图。
- `fetch_media.py`：把 `raw/*.img` 编码成 WebP 存进 `media.json`，并抓哔哩哔哩封面（走 bilibili API、按 `bvid`）、收集署名。
- `raw/`（47 张原图）、`vraw/`（14 张视频封面原图）— **保留的原始素材**，可离线重新压缩/换质量，省得再联网下载。
- 一次性辅助脚本：`fix_options.py`、`finalize_fixes.py`、`patch_media.py`、`make_contactsheet.py`、`opt.json`、`api.json`（历史构建过程留存，改内容用不到）。
- `screenshot.py` / `screenshot2.py` — 用 Playwright 给 `index.html` 截图做验收（需另装 Playwright chromium）。

---

## 构建管线

```
content.py  ─┐
raw/*.img ──→ fetch_media.py ──→ media.json ─┐
videos.json ─┘                    credits.json┤
                                  style.css   ├─→ build.py ──→ index.html（壳）+ images/*.webp
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
