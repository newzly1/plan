# 选点手册「安缦杂志风」高端化改版 · 设计定稿

- 日期：2026-07-08
- 背景：用户希望投票页更「高端」。已用真实内容与图片制作三方向可交互样例（安缦杂志 / Apple 产品页 / Linear 暗色科技），提案页：https://claude.ai/code/artifact/24a84bc0-c4ce-499e-9604-56aaf964d637
- 决议：**采用方向 A「安缦杂志风」**（参照 Aman Resorts 官网、Kinfolk 杂志的编辑式版式）。

## 目标 / 非目标

**目标**：把 `webpage/index.html` 的视觉语言整体升级为高端旅行杂志质感——宋体标题、大留白、细线分层、方角无投影、照片全宽出血、图注体系。

**非目标**：
- 不改 `content.py` 的内容数据（模板性装饰文本如图注 `Fig.`、masthead 小注写在 `build.py`）。
- 不改投票/清单/复制/灯箱/视频逻辑与 `localStorage` 键——`app.js` 零改动。
- 不动媒体管线（`media.json` / `videos.json` / 抓取脚本）。
- 线上部署方式与链接不变。

## 视觉系统

### 色板（CSS tokens 全量替换）

| token | 浅色（骨白纸） | 深色（墨纸夜读） | 用途 |
|---|---|---|---|
| `--ground` | `#FAF8F2` | `#16140F` | 页面底 |
| `--surface` | `#F4F1E8` | `#1D1A14` | 输入框/面板 |
| `--ink` | `#1B1815` | `#EDE7DA` | 正文墨字 |
| `--ink-soft` | `#575147` | `#B3AA97` | 次级文字 |
| `--ink-faint` | `#8A8272` | `#857C69` | 注记 |
| `--line` | `#E5E0D4` | `#2E2A22` | 细分隔线 |
| `--line-strong` | `#1B1815` | `#EDE7DA` | 章节级粗线（1px 墨线） |
| `--pine` | `#1E4D44` | `#4E9A8A` | 主点缀：必去/选中/链接 |
| `--brass` | `#9C7C3C` | `#C29A54` | 次点缀：编号/图注/小注 |

- 投影 token 全部删除；层次只靠细线与留白。圆角 `--rad: 0`（弹层顶部允许 ≤2px 防锯齿）。
- 双主题机制不变：`prefers-color-scheme` + `:root[data-theme]` 覆盖，三处 token 同步。

### 字体

- **标题衬线**：内嵌思源宋体（Source Han Serif SC）**SemiBold 单权重**子集，`@font-face` data URI。作用域：hero 主标题、章节 h2、景点 h3、组合 h3、精选卡标题、清单弹层标题、盖章文字。
- **回退栈**：`"Source Han Serif SC","Songti SC","STSong","Noto Serif CJK SC","SimSun",serif`——字体文件缺失时页面仍成立（iOS 有 Songti SC；低端安卓退化为黑体，可接受）。
- **正文**保留现有黑体栈；**英文注记/编号/数据**保留现有等宽栈（全大写 + 宽字距，延续「田野笔记」基因）。
- **子集管线**：新增一次性脚本 `webpage/fetch_font.py`——
  1. 程序化收集标题域用字：`content.py` 的 `zh/name/title/no` 字段 + `build.py` 标题字面量 + 「必去可去」等盖章字；
  2. `curl`（走本地代理）下载思源宋体 SemiBold OTF；
  3. `pyftsubset` 出 woff2（`pip install fonttools brotli` 需用国内镜像源）；
  4. base64 写入 `font.json`。
- `build.py` 读 `font.json`：存在则注入 `@font-face`，缺失则跳过（优雅降级），构建永不因字体失败。
- 体积预算：子集约 300–500 字 → woff2 ≈ 100–200KB，`index.html` 总体 ≤ 5.9MB。

### 版式原则

方角、无投影；1px 细线分层（章节用墨色粗线）；标题衬线 + 收紧行高 + 适度字距（`.06em`）；英文小注全大写 + `.2em+` 字距；每张主图配图注行（左：地名英文，右：`Fig.` 编号/景点编号，黄铜色）；正文行距 1.85–1.95；留白显著加大（章节间距 ≥ 56px）。

## 组件改造清单（保持 app.js 钩子：id、`data-*`、`.v/.spot/.idx/.shot-img/.vid/.hl/.combo`）

1. **Hero**（`build.py` 重构模板）：图上叠字 → 杂志封面式。顶部 masthead 行（`INDONESIA · FIELD NOTES · 2026`）→ 居中短墨线 → 宋体大标题（clamp 34–44px）→ 副题字距拉开 → small-caps facts 行 → 全宽出血封面照（B1a，去圆角）→ 图注行 → `howto` 段 → 索引导航：胶囊 `.idx` 改为上下细线包夹的文字目录行（class 与 href 不变，锚点滚动逻辑复用）。
2. **精华速览**：眉题改黄铜 small-caps 标签；`.hl` 卡去圆角/投影/文字压图，改「图上 + 图注下（细线收尾）」，横滑与 reveal 保留。
3. **章节头**：删除字母方块 `.chap-letter`，改「墨色粗线顶边 + 宋体章节名 + 右侧 `Region X` 黄铜小注」，data 行改 small-caps。
4. **景点卡 `.spot`**：去卡片感（无边框/圆角/投影），改文章式区块、区块间细线分隔。图集 `.gallery` 保留横滑，图片去圆角、figcaption 改「中文名 + small-caps 英文」图注式；编号 `A1` 移入图注行；标题改宋体 h3；`.tag` 胶囊改松绿 small-caps 文字（`·` 分隔）；视频板 `.vid` 去圆角、徽标改黄铜（bvid 播放逻辑不动）；meta 行细线顶边；`details.notes` 保留，summary 改 small-caps。
5. **投票钮 `.v`**：方角、1px 墨线、字距 `.3em`；选中态：必去 = 松绿填充/骨白字，可去 = 墨色填充，无所谓 = 浅灰填充；`aria-pressed`/`data-v` 不变。
6. **盖章 `.stamp`**：保留元素、触发与动画，改「钢印」式——单色 1.5px 实线圆环 + 宋体字，必去松绿/可去墨色，去双线描边。
7. **组合 `.combo`**：编号改宋体大字黄铜色；卡片改细线分隔的列表式（无框）。
8. **价格/贴士折叠 `.fold`**：细线包围，标题 small-caps 黄铜；表格数字右对齐 + `tabular-nums`（沿用）。
9. **底栏 `#bar`**：黑色悬浮胶囊 → 全宽 fixed 底条：骨白底 + 墨色顶线，左「我的清单」small-caps、右计数 `#barN`（黄铜）；点击行为不变。
10. **清单弹层 `.sheet`**：方角（顶部 ≤2px）、细线、输入框方角；`.pick .pc` 徽标改方角小签（必去松绿/可去墨色）。
11. **灯箱/Toast**：沿用交互，视觉对齐（方角、墨底）。
12. **页脚**：small-caps `made` 行，署名段落沿用。

## 构建与文件变更

| 文件 | 变更 |
|---|---|
| `style.css` | 全量重写（token + 全部组件皮肤） |
| `build.py` | hero/章节头/图注行等模板结构调整；读 `font.json` 注入 `@font-face`；**所有 id 与 `data-*` 原样保留** |
| `fetch_font.py` | 新增（一次性字体子集管线，见上） |
| `font.json` | 新增（woff2 base64，入库以便离线重建） |
| `app.js` | 零改动 |

## 验收清单

1. `python3 build.py` 成功，体积 ≤ 5.9MB；`font.json` 缺失时也能成功构建（降级栈）。
2. Playwright 截图：浅/深两主题 × 手机（390px）/桌面（1200px）四张，对照提案样例核对气质。
3. 交互回归：投票三态互斥与取消 → 钢印出现/消失 → `#barN` 计数 → 清单弹层（姓名/主线单选持久化）→ 一键复制文案 → 清空确认；图片灯箱开关；B 站视频原地播放且同时仅一个；索引锚点平滑滚动；两个折叠面板。
4. `prefers-reduced-motion` 下无 reveal/动画。
5. 部署 CloudBase 后线上链接内容更新、功能同 3。

## 风险与对策

- **字体下载失败**（GitHub release 需代理）：先以系统宋体栈上线，字体后补——`build.py` 的降级设计保证随时可发布。
- **fonttools 安装卡顿**：pip 用国内镜像（如清华源）。
- **低端安卓无衬线中文**：降级为黑体，版式仍成立（留白/细线/字距承担高级感）。
- **深色主题下照片偏亮**：如刺眼，对图片统一 `filter:brightness(.94)`（实现时目测定夺）。
