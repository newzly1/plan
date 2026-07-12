# CODEBUDDY.md This file provides guidance to CodeBuddy when working with code in this repository.

印尼（巴厘岛及周边）6 人旅行选点投票项目。核心产物是 `webpage/index.html`（外壳）+ `webpage/images/*.webp`（约 60 张图），两者须同目录部署。纯 `localStorage` 投票 + CloudBase 云数据库做实时汇总，无自建后端。

## 常用命令

**重新构建（改内容/样式/交互后必跑）**
```bash
cd webpage && python3 build.py
```
只用 Python 标准库，零依赖。读 `content.py` + `*.json` + `style.css` + `app.js`/`tally.js`/`identity.js` → 写 `index.html` + `images/*.webp`。Windows 下若 `python3` 不识别用 `python`。

**单测（零依赖，Node 内置测试框架）**
```bash
node --test webpage/test/tally.test.js      # 汇总算法
node --test webpage/test/identity.test.js   # 身份派生/合并
node --test webpage/test/                   # 跑全部
```

**部署到 CloudBase（环境 ID `plan-d0gstt7r6507aa319`，国内可直连，链接不变）**
```bash
cd webpage
tcb hosting deploy index.html index.html -e plan-d0gstt7r6507aa319   # 文字/样式/交互变化
tcb hosting deploy images images -e plan-d0gstt7r6507aa319           # 图片文件夹变化
tcb hosting deploy images/<key>.webp images/<key>.webp -e plan-d0gstt7r6507aa319  # 换单张图（index.html 不用动）
tcb hosting deploy cloudbase.js cloudbase.js -e plan-d0gstt7r6507aa319  # vendored SDK 变更（一般首次一次）
```
先传 `images` 再传 `index.html` 最保险。正式链接：https://plan-d0gstt7r6507aa319-1451599494.tcloudbaseapp.com

**换图/重抓媒体（需联网，日常改内容用不到）**
```bash
pip install Pillow
# 方式一（首选，国内直连）：Unsplash + Pixabay
$env:UNSPLASH_KEY="..."; $env:PIXABAY_KEY="..."
python3 fetch_review_candidates.py            # → review/<子点id>/ 候选图
python3 apply_review.py                       # 筛选后 → media.json + credits.json
# 方式二（备选，需梯子）：Wikimedia Commons
python3 fetch_candidates.py                   # → candidates.json + raw/*.img
python3 fetch_media.py                        # → media.json + 哔哩哔哩封面 + 署名
python3 build.py                              # 最后都要 build
```

## 架构

### 构建生成式静态站点（核心模式）

这是一套**手写的静态站点生成器**：`webpage/build.py` 把分离的内容/样式/交互源码组装成一个自包含的 `index.html`，并从 `media.json` 解码出 `images/*.webp`。

```
content.py（内容唯一源）─┐
style.css（样式）         │
app.js（交互）            ├─→ build.py ─→ index.html（壳，CSS/JS 全内联）
tally.js（汇总算法）      │              + images/*.webp（从 media.json 解码）
identity.js（身份/合并）  ┘
media.json / videos.json / credits.json / font.json（媒体与素材数据）
```

关键约定：
- `build.py` **只用 Python 标准库**，`python3 build.py` 一条命令重新生成全部产物。
- CSS 与三个 JS（`tally.js`、`identity.js`、`app.js`）全部**内联**进 `<style>`/`<script>`；只有 `cloudbase.js`（vendored CloudBase Web SDK）作为独立 `<script src>` 引用。`app.js` 里的 `/*__ITEMS__*/` / `/*__COMBOS__*/` 占位符在构建时被 `build.py` 替换成景点/组合 JSON。
- `images/` 每次 build **全量重写**（先清空再写被引用的 key），自动清除改名/删除后的陈旧文件；文件名碰撞会直接报错退出。
- 图片路径只取决于景点 key（如 `images/A1a.webp`），不受文字/样式改动影响——换同一 key 的图只需重部署那一张，`index.html` 不用动。
- 媒体缺失时降级为带文字的占位 `<div>`，页面永远能构建成功。

### 内容数据模型（`webpage/content.py`）

全部文字的**唯一来源**（从根目录 `印尼旅行项目投票清单.md` 转写），结构化为 Python dict/list：

| 变量 | 内容 |
|---|---|
| `META` | 标题、副题、使用说明、汇率注记 |
| `REGIONS` | 6 个地区 A–F（巴厘本岛/佩尼达三岛/科莫多/布罗莫/宜珍/龙目+吉利） |
| `ITEMS` | 14 个景点。每个含 `id, region, zh/en, tags, time, price, feature/caution/coupling, video_q, subspots[]` |
| `HIGHLIGHTS` | 第一章「最热门景点」成员的 item id（有序，4 个） |
| `COMBOS` | 组合线路 ①–⑦（①–④ 全程 9–10 天，⑤–⑦ 精简 6 天，均含佩尼达） |
| `PRICES` / `NOTES` | 参考价格表 / 全程注意事项 |

章节渲染逻辑（`spot_chapters()`）：**第一章＝`HIGHLIGHTS` 最热门景点**，其后为 `REGIONS` 中仍有非热门景点的地区按原顺序成章；整区景点全为热门的地区（科莫多/布罗莫）不成章。Hero 导航与正文共用 `spot_chapters()`，保证一一对应。**组合建议**紧跟景点章之后，章号＝`len(spot_chapters())+1`（当前第六章），也进 Hero 导航。

### 前端交互层（`webpage/app.js`）

纯 `localStorage` 的 IIFE，无框架。核心模块：
- **投票** — 事件委托处理 `.v` 按钮（必去/可去/略过），存 `localStorage[bali_votes]`，投票后右上角出现旋转钢印动画，并触发 `cloud.syncMine()`。
- **`cloud` 模块** — CloudBase 匿名登录 → 防抖 800ms 把自己那条文档 upsert 进集合 `votes` → 拉取全量 → `TallyLib.computeTally()` 算分排行。`syncNow()` 供「提交」按钮立即同步（清除防抖、返回 Promise）。
- **底部状态栏 + 「我的清单」半屏浮层** — 名字输入、个人清单、实时汇总面板、**提交我的选择**（强制同步到云端）、清空所有标记。主线偏好在正文「组合建议」区点击选择。
- 兜底：SDK 未加载/断网时，汇总面板降级为「云同步暂不可用」，本地投票照常可用（数据保存在本机，联网后自动同步）。

### 云同步与身份层

- `cloudbase.js` — vendored CloudBase Web SDK **v2.31.0**（UMD，全局 `cloudbase`），同源部署不依赖 CDN。⚠️ **必须 2.0+**：本环境已停用 v1.x 旧匿名登录（会报 `ACCESS_TOKEN_DISABLED`），登录用 `auth.signInAnonymously()`。
- `identity.js` — 把名字归一化（trim + 小写 + 折叠空白）后派生 docId（`u_<base64url>`）。换设备/撞名时把本地与云端 **merge**（按 `must>maybe>skip` 取更强的一方，防丢票）。纯函数，浏览器与 `node --test` 共用。
- `tally.js` — 纯汇总算法。**加权分 = 必去×2 + 可去×1**，景点按分降序、同分按必去数、再按 id；组合线路单独统计。纯函数，浏览器与 `node --test` 共用。
- 集合 `votes` 安全规则：`{ "read": true, "write": "auth.uid != null" }`（人人可读、匿名登录即可写）。⚠️ **勿用 `doc._openid == auth.openid`**：匿名用户无可用 openid，会全拒。
- 汇总刷新时机：打开浮层 / 投完票 / 点「刷新」/ 标签页重新可见 / 每 45 秒。

### 媒体抓取管线（仅换图时用）

两套流程，最终都写入 `media.json`，再由 `build.py` 生成 `images/*.webp`：
- **方式一（首选）**：`fetch_review_candidates.py`（Unsplash + Pixabay，国内直连）→ `review/<id>/` 人工筛选 → `apply_review.py` → `media.json` + `credits.json`。设 `UNSPLASH_KEY`/`PIXABAY_KEY` 走 DIRECT 模式；未设走 PROXY 模式（Commons + Openverse，默认代理 `http://127.0.0.1:7897`，可用 `REVIEW_PROXY` 覆盖）。
- **方式二（备选）**：`fetch_candidates.py`（Wikimedia Commons，需梯子）→ `raw/*.img` → `fetch_media.py` → `media.json` + 哔哩哔哩封面 + 署名。
- `raw/`、`vraw/` 保留原始素材，可离线重新压缩。`image_sourcing/keywords.md` 是每子点的 4 组搜图关键词。

### 部署

腾讯云 CloudBase 静态托管（免费体验环境）。`tcb hosting deploy` 按改动范围分别部署 `index.html` / `images` / `cloudbase.js`，链接不变。⚠️ 免费环境 **2027-01-08 到期**，到期前须在 [CloudBase 控制台](https://console.cloud.tencent.com/tcb) 手动续 6 个月，否则环境销毁、链接失效（不支持自动续费）。

## 环境与注意事项

- **npm 会卡**：本机默认源 `registry.npmjs.org` 联网卡住；装包一律加 `--registry=https://registry.npmmirror.com`。同理 `urllib` 也卡，脚本联网抓取用 `curl`（走本地代理）。
- **CloudBase CLI**：`@cloudbase/cli`（命令 `tcb`）已全局安装；登录用 `tcb login --flow device`（设备码，扫码授权，不需交密钥）。
- **Git**：远端 `git@github.com:newzly1/plan.git`（SSH）；本机未配全局身份，提交作者沿用仓库局部配置 `zly1 <10994824+zly21@user.noreply.gitee.com>`；提交信息用中文。
- 改哪个文件：内容 → `content.py`；样式 → `style.css`；投票/交互 → `app.js`；汇总算分 → `tally.js`；身份/合并 → `identity.js`；换图 → 见上方「媒体抓取管线」。
- 设计说明在 `docs/`（`网页整体结构说明.md` 讲架构与数据流，`网页UI布局说明.md` 讲视觉版式）。
