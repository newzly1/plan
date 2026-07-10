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
| 实时汇总的算分/排序逻辑 | `tally.js`（纯函数，浏览器与 `node --test` 共用） |
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
| `content.py` / `style.css` / `app.js` / `tally.js` | 只需 `index.html`（构建时会内联进去） |
| 换同一 key 下的图（如替换 `raw/B1a.img`） | **只需那一张图**，`index.html` 文本不变，例：`tcb hosting deploy images/B1a.webp images/B1a.webp -e plan-d0gstt7r6507aa319` |
| 新增景点/视频（新 key） | `images/`（新文件）+ `index.html`（新增引用） |
| `cloudbase.js`（vendored CloudBase SDK，一般只在升级 SDK 时改） | `tcb hosting deploy cloudbase.js cloudbase.js -e plan-d0gstt7r6507aa319` |

首次上线或不确定改了什么时，两条命令都跑一遍最保险（建议先传 `images`，避免线上 `index.html` 一度引用还不存在的图片路径）。

- **环境 ID**：`plan-d0gstt7r6507aa319`（腾讯云 CloudBase 免费体验版）。
- **首次配置**：`npm i -g @cloudbase/cli --registry=https://registry.npmmirror.com`（本机默认 npm 源会卡，故用国内镜像），再 `tcb login --flow device` 扫码登录。
- ⚠️ **续期**：免费环境 **2027-01-08 到期**，到期前需在 [CloudBase 控制台](https://console.cloud.tencent.com/tcb) 手动续 6 个月，否则环境销毁、链接失效（不支持自动续费）。

---

## 投票实时汇总（CloudBase 云数据库）

6 人投票现在会实时汇总：每人投票/改名/改组合线路后，浏览器把自己那条记录同步到云数据库，
「我的清单」浮层里的「大家的选择 · 实时汇总」面板拉取全部记录、按加权分排行展示。本地
`localStorage` 投票与「一键复制」原样保留，作为 SDK 未加载 / 断网时的兜底。

**数据流**：打开页面即匿名登录（CloudBase 匿名登录，身份跨会话稳定）→ 每次投票/改名/改组合，
防抖后把自己那条文档 upsert 进云数据库集合 `votes`（文档 id 存在 `localStorage` 的 `bali_docid`，
更新失败时保留 docId 供下次重试，只有服务端明确返回 `updated:0`——即该文档已不存在——才会重新
创建）→「实时汇总」面板拉取全部文档，用加权分（必去 ×2 + 可去 ×1）给景点排行，组合线路单独统计，
顶部显示「已 N 人参与」。

**涉及文件**：
- `tally.js` — 纯汇总算法（算分/排序），不依赖网络，浏览器与 `node --test` 共用。
- `app.js` 的 `cloud` 模块 — 匿名登录、`syncMine()` 防抖同步、`fetchAll()` 拉取全量；以及
  `renderTally` / `refreshTally` 负责面板渲染和三个刷新时机（打开浮层 / 投完票 / 点「刷新」）。
- `cloudbase.js` — vendored 的 CloudBase Web SDK（UMD，全局变量 `cloudbase`），随站点同源部署，
  不依赖第三方 CDN。

**构建变化**：`build.py` 现在还会把 `tally.js` 内联进页面，并在 `index.html` 里加一行
`<script src="cloudbase.js"></script>`（在内联脚本之前加载）。构建命令不变，仍是 `python3 build.py`。

**新增部署目标**：SDK 变更时（一般首次上线跑一次即可，之后基本不变）：
```bash
tcb hosting deploy cloudbase.js cloudbase.js -e plan-d0gstt7r6507aa319
```
文字/样式/交互（含 `tally.js`）改动仍只需重新部署 `index.html`。

**一次性 CloudBase 控制台配置**（首次启用需在 [CloudBase 控制台](https://console.cloud.tencent.com/tcb)
环境 `plan-d0gstt7r6507aa319` 手动点一遍，此后无需重复）：

1. **开启匿名登录**：「登录授权」→ 开启「匿名登录」。
2. **建集合**：「云数据库」→ 新建集合 `votes`。
3. **设安全规则**：集合 `votes` →「权限设置」→ 自定义安全规则，填入：
   ```json
   { "read": true, "write": "doc._openid == auth.openid" }
   ```
   （所有人可读，用于汇总；仅本人可写自己那条，防止误改/删别人的票。）
4. **加 Web 安全域名**：「环境」→「安全配置」→「Web 安全域名」，加入
   `plan-d0gstt7r6507aa319-1451599494.tcloudbaseapp.com`（否则浏览器端 SDK 认证会被拒）。

**单测**：
```bash
node --test webpage/test/tally.test.js   # 零依赖，Node 内置测试框架
```

**兜底**：SDK 未加载或断网时，本地投票、「我的清单」与「一键复制」照常可用；「实时汇总」面板会
显示「云同步暂不可用，可用下方『一键复制』发到群里」，不影响其余功能。

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
- `fetch_candidates.py` → `candidates.json`：按 `content.py` 里的 `q` 去 Wikimedia Commons 找候选图（需梯子）。
- `fetch_review_candidates.py` → `review/<子点id>/`：批量收集候选图，支持两种模式（详见下方「收集图片」一节）。
- `fetch_media.py`：把 `raw/*.img` 编码成 WebP 存进 `media.json`，并抓哔哩哔哩封面（走 bilibili API、按 `bvid`）、收集署名。
- `apply_review.py`：从 `review/<子点id>/` 中选最佳图，编码为 WebP 写入 `media.json` + `credits.json`。
- `raw/`（47 张原图）、`vraw/`（14 张视频封面原图）— **保留的原始素材**，可离线重新压缩/换质量，省得再联网下载。
- `image_sourcing/keywords.md` — 每个子点的 4 组搜图关键词（主名/航拍/日落细节/别称活动），供外部工具搜图参考。
- 一次性辅助脚本：`fix_options.py`、`finalize_fixes.py`、`patch_media.py`、`make_contactsheet.py`、`opt.json`、`api.json`（历史构建过程留存，改内容用不到）。
- `screenshot.py` / `screenshot2.py` — 用 Playwright 给 `index.html` 截图做验收（需另装 Playwright chromium）。

---

## 构建管线

```
content.py  ─┐
review/<id>/ ──→ apply_review.py ──→ media.json ──┐  ← 方式一（首选，国内直连）
raw/*.img ──→ fetch_media.py ──────────────────┤  ← 方式二（备选，需梯子）
videos.json ─┘                    credits.json┤
                                  style.css   ├─→ build.py ──→ index.html（壳）+ images/*.webp
                                  app.js      ┘
```

改文字/样式/交互 → 只需 `build.py`。
换图/重抓 → 首选方式一：`fetch_review_candidates.py` + `apply_review.py`（Unsplash/Pixabay，国内直连）；次选方式二：`fetch_candidates.py` + `fetch_media.py`（Commons，需梯子）。再 `build.py`。

## 收集图片

页面有 **两套图片收集流程**，两者最终都写入 `media.json`，再由 `build.py` 生成 `images/*.webp`。**优先使用方式一**（国内可直连），方式二作为备选。

### 方式一（首选）：Review 候选图收集（国内直连，无需梯子）

先批量收集多个候选到 `review/` 目录，人工筛选后编入页面。通过 Unsplash + Pixabay API 抓图，**国内可直连**。

```bash
pip install Pillow

# ── 设置 API key（二选一或都设，设了就走国内直连模式） ──
# Unsplash：https://unsplash.com/developers 注册免费应用获取 Access Key
$env:UNSPLASH_KEY="Ds9PwsNBJDLtZ3ecWwEneDTZIeRY_v6x8pug8qlsxpI"
# Pixabay：https://pixabay.com/api/docs 注册获取 API Key
$env:PIXABAY_KEY="56614242-5c904b8b8af5334b2d209bc5e"

python3 fetch_review_candidates.py              # 全部子点，每景点 ~20 张候选
python3 fetch_review_candidates.py --only D1    # 只抓指定景点（如布罗莫）
# → review/<子点id>/ 目录，含多张候选图 + metadata.json（来源/作者/许可）

# ── 人工筛选：删掉不满意的，保留的最低编号图即为选中 ──

python3 apply_review.py     # review/ 中保留的图 → media.json + credits.json（WebP 1280px q82）
python3 build.py           # → index.html + images/*.webp
```

- 优点：**Unsplash + Pixabay 国内可直连，无需梯子**；图片质量高、可人工筛选；多角度关键词（见 `image_sourcing/keywords.md`）覆盖航拍/日落/活动等不同视角。
- 缺点：需注册 API key（免费）；多一步人工筛选。
- 模式说明：设置了 `UNSPLASH_KEY` 或 `PIXABAY_KEY` → **DIRECT 模式**（Unsplash + Pixabay，不走代理）；未设置 → **PROXY 模式**（Wikimedia Commons + Openverse，走 `REVIEW_PROXY` 默认 `http://127.0.0.1:7897`）。

### 方式二（备选）：Wikimedia Commons 直接抓取（需梯子）

最早的管线，当前页面上已有的 45 张景点图均由此抓取。按 `content.py` 中每个子点的 `q`（英文搜索词）去 Wikimedia Commons 找候选、自动下载 top-1。

```bash
pip install Pillow
python3 fetch_candidates.py   # → candidates.json + raw/*.img（按 q 搜 Commons，下载最佳候选原图）
python3 fetch_media.py        # raw/*.img → media.json（WebP 编码）+ 哔哩哔哩封面 + Commons 署名
python3 build.py              # → index.html + images/*.webp
```

- 优点：全自动、一步到位，署名信息完整。
- 缺点：**Wikimedia Commons 国内访问需梯子**；图片质量参差不齐，无法人工筛选。
- 适用：批量初始化、替换同一 key 下的单张图（把新原图放进 `raw/<子点id>.img` 再跑 `fetch_media.py`）。

### 换图速查

| 场景 | 操作 |
|---|---|
| 换同一 key 的一张图（方式一） | 把新原图放 `raw/<子点id>.img` → `fetch_media.py` → `build.py` |
| 补充缺失图片（方式二，如 D1 布罗莫） | 设 API key → `fetch_review_candidates.py --only D1` → 筛选 → `apply_review.py` → `build.py` |
| 全部重抓 | 方式一：`fetch_candidates.py` + `fetch_media.py`；方式二：`fetch_review_candidates.py` + `apply_review.py` |

> 环境注意：本机联网只能走本地代理的 `curl`（`urllib`/`npm` 会卡住）；脚本里已用 `curl` 抓取。PROXY 模式默认走 `http://127.0.0.1:7897`，可用 `REVIEW_PROXY` 环境变量覆盖。

---

## 说明
- 内容源文档里的「本次不纳入」部分是刻意不放进页面的；C2 林贾尼、D2 船宿保留在册。
- 价格/时间为 2026 年粗估，随季节汇率浮动，仅作 6 人出行投票参考、非商业用途；图片来自 Wikimedia Commons、Unsplash、Pixabay 等公开来源，版权归原作者，依各自许可使用。
