# 工程结构整理 · 按功能分目录（设计）

- 日期：2026-07-13
- 状态：已批准，执行中
- 范围：仓库根 + `webpage/` 全量目录重构（用户明确选择"彻底重构"），不改任何运行时行为，构建产物须逐字节一致。

## 背景与目标

`webpage/` 平铺了约 30 个文件：手改构建源、JSON 数据、抓图流水线脚本、原始素材、部署产物混在一层，难以一眼看清职责。本次按**数据流水线**分目录：

```
assets/（原始素材）→ tools/（加工）→ data/（编码 JSON）→ src/（构建）→ dist/（部署）
```

同时整理仓库根：散落的 research 文档归入 `docs/research/`；已与 `content.py` 严重错位、且当前被删（未提交）的 `印尼旅行项目投票清单.md` 从 git 恢复后归档到 `docs/archive/`，并把文档里"内容源头"的说法改指向 `content.py`（主从关系已反转，content.py 才是事实源头）。

## 目标目录结构

```
Travalplan/
├── CLAUDE.md · CODEBUDDY.md · .gitignore
├── docs/
│   ├── superpowers/specs · superpowers/plans        （不动）
│   ├── 网页UI布局说明.md 等                            （不动）
│   ├── research/    ← research_plan_*.md、research_report_*.md
│   └── archive/     ← 印尼旅行项目投票清单.md（恢复 + 冻结说明头）
└── webpage/
    ├── src/    build.py content.py style.css app.js tally.js identity.js
    ├── data/   media.json videos.json credits.json font.json
    ├── tools/  fetch_candidates.py fetch_media.py fetch_review_candidates.py
    │           apply_review.py make_review_index.py fetch_font.py
    │           screenshot.py screenshot2.py
    ├── assets/ raw/ vraw/ review/ image_sourcing/ candidates.json
    ├── test/   tally.test.js identity.test.js
    ├── dist/   index.html cloudbase.js images/*.webp
    └── README.md
```

取舍点（已与用户确认）：
1. `dist/` 同时装"生成物"（index.html/images，build 每次覆盖）与"vendored"（cloudbase.js，稳定）。好处：部署目标一目了然；代价：不能整个 `rm -rf dist`（会误删 cloudbase.js）——README 注明。
2. `印尼旅行项目投票清单.md` 归档为历史快照，不再假装是活的内容源头。
3. 目录名用 `dist/`（非 `public/`）。

## 每个文件的改动

### 移动（纯 git mv，全部已跟踪）
- src/：build.py content.py style.css app.js tally.js identity.js
- data/：media.json videos.json credits.json font.json
- tools/：fetch_*.py（4）apply_review.py make_review_index.py fetch_font.py screenshot.py screenshot2.py
- assets/：raw/ vraw/ review/ image_sourcing/ candidates.json
- dist/：index.html cloudbase.js images/

### 代码改动
- **src/build.py**：`SRC=脚本目录`；新增 `ROOT=os.path.dirname(SRC)`、`DATA=ROOT/data`、`DIST=ROOT/dist`。
  - `import content` 同在 src/，Python 自动把脚本目录加进 sys.path[0]，无需改。
  - media/videos/credits/font.json 从 `DATA` 读；style/tally/identity/app 从 `SRC` 读。
  - `IMAGES_DIR=DIST/images`；index.html 写到 `DIST`。
  - 输出 HTML 里 `<script src="cloudbase.js">` 是相对路径，index.html 与 cloudbase.js 同在 dist/，**不改**。
- **tools/ 每个 .py**：顶部（在 `from content import …` 之前）插入
  ```python
  ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
  sys.path.insert(0, os.path.join(ROOT, "src"))
  ```
  （`sys` 缺的脚本补 import。）路径基准：`DATA=ROOT/data`、`ASSETS=ROOT/assets`。
  - fetch_candidates：raw→ASSETS，candidates.json→ASSETS
  - fetch_media：raw/vraw/candidates.json→ASSETS，videos/media/credits.json→DATA
  - fetch_review_candidates：review→ASSETS
  - apply_review：review→ASSETS，media/credits.json→DATA
  - make_review_index：review→ASSETS（含输出的 review/index.html）
  - fetch_font：font.json→DATA
  - screenshot/screenshot2：URL 指向 `ROOT/dist/index.html`（截图 PNG 仍落 CWD，gitignore 覆盖）
- **test/*.js**：`require("../tally.js")`→`require("../src/tally.js")`；identity 同理。`node --test webpage/test/…` 命令不变。

### 文档改动
- **CLAUDE.md**：构建命令 `python3 src/build.py`；部署命令 `dist/index.html`、`dist/images`、`dist/cloudbase.js`、单图 `dist/images/<key>.webp`；改哪个文件表加 `src/` 前缀；"内容源头"改为 `content.py`（清单归档于 `docs/archive/`）；项目结构段更新。
- **webpage/README.md**：全量更新构建/部署/文件说明/抓取管线/构建管线图路径；注明 `dist/` 混装、勿整目录删。
- **CODEBUDDY.md**：同步 CLAUDE.md 的路径改动。

## 验证（正确性证明）
1. `cd webpage && python src/build.py` 成功打印 `wrote index.html / wrote images/`。
2. 重建后 `git diff` 对 `dist/index.html` 与 `dist/images/*.webp` **无内容变化**（纯重命名）——证明构建确定性未受影响。基线 index.html sha256=`5e8af5e5…5cce6f`，images 组合 sha256=`8c746866…84b1`。
3. `node --test webpage/test/tally.test.js webpage/test/identity.test.js` → 18 passing。
4. 导入冒烟测试：从 `webpage/` 跑 `python -c "import sys; sys.path.insert(0,'src'); import content"` 通过；每个 tools 脚本 `python -m py_compile` 通过。

## 非目标
- 不改任何投票/构建/汇总逻辑，不动图片内容，不升级 SDK。
- 不移动 `印尼旅行项目投票清单.md` 之外的根级内容源，不重排 docs/ 已有的 specs/plans。
