# 行程景点地图 + 路线图（SVG）实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 手写一张自包含静态 SVG（`docs/itinerary/景点路线图.svg`），把方案三全程画成"景点地图 + 每日路线图"，并在 `路线与游玩地点.md` 顶部引用。

**Architecture:** 单个手写 SVG，`viewBox="0 0 1200 820"`。左右两大 panel（巴厘 / 科摩多），中下部一条跨两 panel 的 10.7 虚线飞行弧，底部一条 9 天图例带。全程用一个 scratchpad 校验脚本做红→绿驱动（well-formed XML + 无外链 + 必含全部景点名/日期），最后用 Playwright 打开 `file://` 截图做视觉验收。校验脚本不提交，最终产物只有 SVG + 一处 md 引用。

**Tech Stack:** 纯手写 SVG（基础图元，零外链/脚本/字体外引）；Python 标准库（`xml.dom.minidom`）做结构校验；Playwright MCP 做渲染视觉验收。

## Global Constraints

- 只画**方案三（现行）**；不画方案一/二、不画群岛定位带、不画 LJ 接法分支、不画北部环线/火山。
- **零外部依赖**：SVG 内不得出现 `http`、`<script`、`<image`、外部 `xlink:href`、`@import`、`url(http`；中文字体只用系统回退 `font-family="PingFang SC, Microsoft YaHei, Noto Sans CJK SC, sans-serif"`。
- `viewBox="0 0 1200 820"`，不写死 width/height 像素（用 `width="100%"`）以便自适应缩放。
- 事实源头 = `docs/itinerary/路线与游玩地点.md` 方案三主表；文案不臆造。
- 每天一色，9 天固定调色板（sea+sand 冷暖对比）：

  | 日期 | 含义 | 颜色 |
  |---|---|---|
  | 10.2 | 南部落地·金巴兰日落 | `#E8843C` 珊瑚橙 |
  | 10.3 | 佩尼达一日→移住乌布 | `#1E88C7` 海蓝 |
  | 10.4 | 乌布观光（梯田/圣泉） | `#3FA34D` 翠绿 |
  | 10.5 | 乌布松弛 | `#8E6BB0` 藕紫 |
  | 10.6 | 乌鲁瓦图/海神庙+南部 | `#D64545` 落日红 |
  | 10.7 | ✈ DPS→LBJ（飞行弧，虚线） | `#F2B705` 醒目金 |
  | 10.8 | 出海①经典线 | `#0E6BA8` 深海蓝 |
  | 10.9 | 出海②浮潜线 | `#16A0A0` 青绿 |
  | 10.10 | 镇上收尾→回国 | `#6B7F99` 灰蓝 |

- Panel 底/框：巴厘暖陆 `#FBF6EC` / 框 `#D8C9A8`；科摩多海域冷蓝 `#EAF4FA` / 框 `#A9CFE3`。
- 布局分区（x=0..600 巴厘，x=600..1200 科摩多，y=0..70 标题带，y=70..690 内容，y=690..820 图例）。

### 景点坐标分配（近似真实方位，SVG 坐标 y 向下）

**巴厘 panel（左，x 30..570 / y 90..660，南在下）：**

| 景点 | 符号 | (x, y) |
|---|---|---|
| 德格拉朗梯田 + 圣泉寺 Tirta Empul | ● | (250, 150) |
| 乌布 Ubud（大本营） | ●大 | (250, 250) |
| 海神庙 Tanah Lot | ● | (95, 300) |
| Sanur 码头 | ▷ | (330, 360) |
| 金巴兰 / DPS 机场 | ●+✈ | (215, 500) |
| 乌鲁瓦图 Uluwatu | ● | (140, 560) |
| 努沙佩尼达 Nusa Penida（Kelingking/Broken Beach/Crystal Bay） | ◆ | (470, 470) |

**科摩多 panel（右，x 630..1170 / y 90..660，LBJ 在右、群岛在西=左）：**

| 景点 | 符号 | (x, y) |
|---|---|---|
| 拉布安巴焦 LBJ（镇+机场，出海母港） | ●+✈ | (1090, 380) |
| 镇上：Bukit Cinta / Kampung Ujung 夜市 / 镜石洞 Batu Cermin | 小字 | 环 (1090, 380) 周边 |
| 飞狐岛 Kalong | ● | (990, 300) |
| Kelor | ● | (940, 250) |
| Kanawa | ● | (860, 200) |
| Taka Makassar 白沙洲 | ~ | (780, 210) |
| Manta Point | ◇ | (830, 360) |
| 帕达尔岛 Padar | ▲ | (770, 450) |
| 科莫多龙岛 Komodo | ● | (680, 470) |
| 粉沙滩 Pink Beach | ~ | (740, 520) |

坐标可在实现时 ±20 微调避免文字叠压，方位关系（谁在谁的哪个方向）不得变。

---

## Task 1: SVG 骨架 + 校验脚本（红态基线）

**Files:**
- Create: `docs/itinerary/景点路线图.svg`
- Create（不提交，仅构建期用）: `<SCRATCHPAD>/validate_map.py`
  （`<SCRATCHPAD>` = `C:\Users\ADMINI~1\AppData\Local\Temp\claude\c--Users-Administrator-Desktop-workFiles-Travalplan\89fa5fab-1d95-45e4-92c7-bbee6aac3876\scratchpad`）

**Interfaces:**
- Produces: SVG 根元素 `<svg viewBox="0 0 1200 820">`，含标题带两块标题（`巴厘岛 Bali 10.2–10.6` / `科摩多 Komodo 10.7–10.10`）、两 panel 背景框、分区参考。校验脚本 `validate_map.py` 供后续每个 Task 复用。

- [ ] **Step 1: 写校验脚本（全量断言，先失败）**

写入 `<SCRATCHPAD>/validate_map.py`（Python 标准库；一次性列全所有必含项，后续 Task 逐步转绿）：

```python
import sys, xml.dom.minidom as M
SVG = r"c:\Users\Administrator\Desktop\workFiles\Travalplan\docs\itinerary\景点路线图.svg"
txt = open(SVG, encoding="utf-8").read()

# 1) well-formed XML
try:
    M.parseString(txt.encode("utf-8"))
except Exception as e:
    print("FAIL xml not well-formed:", e); sys.exit(1)

# 2) 无外部依赖
banned = ["http", "<script", "<image", "xlink:href", "@import", "url(http"]
bad = [b for b in banned if b in txt]
if bad:
    print("FAIL external refs:", bad); sys.exit(1)

# 3) 标题带
titles = ["巴厘岛", "科摩多"]
# 4) 巴厘景点
bali = ["德格拉朗", "圣泉寺", "乌布", "海神庙", "Sanur", "金巴兰", "DPS",
        "乌鲁瓦图", "佩尼达", "Kelingking"]
# 5) 科摩多景点
komodo = ["拉布安巴焦", "LBJ", "Bukit Cinta", "Kampung Ujung", "镜石洞",
          "飞狐", "Kelor", "Kanawa", "Taka Makassar", "Manta", "帕达尔",
          "科莫多龙", "粉沙滩"]
# 6) 9 天日期
dates = ["10.2", "10.3", "10.4", "10.5", "10.6", "10.7", "10.8", "10.9", "10.10"]
# 7) 图例活动关键词（每天一句里的锚词）
legend = ["金巴兰日落", "佩尼达", "梯田", "松弛", "乌鲁瓦图", "飞", "经典线",
          "浮潜", "回国"]

missing = {}
for name, items in [("titles",titles),("bali",bali),("komodo",komodo),
                    ("dates",dates),("legend",legend)]:
    miss = [i for i in items if i not in txt]
    if miss: missing[name] = miss

if missing:
    print("MISSING:", missing); sys.exit(2)
print("OK all checks passed"); sys.exit(0)
```

- [ ] **Step 2: 写 SVG 骨架**

写入 `docs/itinerary/景点路线图.svg`（只到骨架层：根、样式、标题带、两 panel 框；景点/路线/图例后续 Task 填）：

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 820" width="100%"
     font-family="PingFang SC, Microsoft YaHei, Noto Sans CJK SC, sans-serif">
  <!-- 背景 -->
  <rect x="0" y="0" width="1200" height="820" fill="#ffffff"/>
  <!-- 巴厘 panel 背景（暖陆） -->
  <rect x="12" y="76" width="576" height="608" rx="10" fill="#FBF6EC" stroke="#D8C9A8" stroke-width="1.5"/>
  <!-- 科摩多 panel 背景（冷海） -->
  <rect x="612" y="76" width="576" height="608" rx="10" fill="#EAF4FA" stroke="#A9CFE3" stroke-width="1.5"/>
  <!-- 标题带 -->
  <text x="300" y="48" text-anchor="middle" font-size="26" font-weight="700" fill="#3A3A3A">巴厘岛 Bali · 10.2–10.6</text>
  <text x="900" y="48" text-anchor="middle" font-size="26" font-weight="700" fill="#3A3A3A">科摩多 Komodo · 10.7–10.10</text>
  <!-- 巴厘组 --> <g id="bali"></g>
  <!-- 科摩多组 --> <g id="komodo"></g>
  <!-- 飞行弧组 --> <g id="flight"></g>
  <!-- 路线组 --> <g id="routes"></g>
  <!-- 图例组 --> <g id="legend"></g>
</svg>
```

> 注：SVG 命名空间声明 `xmlns="http://www.w3.org/2000/svg"` 是 SVG 必需属性，是唯一允许的 `http` 出现处 —— 因此校验脚本 Step 1 的 banned 列表用裸串 `"http"` 会误报。**修正**：把 banned 里的 `"http"` 改为只查外链协议 `"http://"` 与 `"https://"`，并在检测前先剔除命名空间声明行。见下方 Step 3。

- [ ] **Step 3: 修正校验脚本，排除合法命名空间**

编辑 `<SCRATCHPAD>/validate_map.py`，把外链检测改为忽略 `xmlns` 命名空间：

```python
# 2) 无外部依赖（允许 SVG/xlink 命名空间声明，其余一律禁止）
import re
scan = re.sub(r'xmlns(:\w+)?="[^"]*"', '', txt)   # 去掉命名空间声明再查
banned = ["http://", "https://", "<script", "<image", "@import", "url(http"]
bad = [b for b in banned if b in scan]
if bad:
    print("FAIL external refs:", bad); sys.exit(1)
```

- [ ] **Step 4: 运行校验，确认"标题过、景点/日期/图例仍缺失"的红态**

Run: `python "<SCRATCHPAD>/validate_map.py"`
Expected: 打印 `MISSING: {...}`，其中 `titles` 不在缺失里（已过），`bali`/`komodo`/`dates`/`legend` 仍列为缺失；退出码 2。

- [ ] **Step 5: 提交骨架**

```bash
git add docs/itinerary/景点路线图.svg
git commit -m "行程图：SVG 骨架——画布/两 panel 框/标题带（景点路线待填）"
```

---

## Task 2: 巴厘 panel 景点

**Files:**
- Modify: `docs/itinerary/景点路线图.svg`（填充 `<g id="bali">`）

**Interfaces:**
- Consumes: Task 1 的 `<g id="bali">` 空组、Global Constraints 巴厘坐标表。
- Produces: 巴厘 7 组景点（符号 + 中文名 + 必要英文小字），供 Task 4 路线连线锚定这些坐标。

- [ ] **Step 1: 填充巴厘景点**

在 `<g id="bali">` 内按坐标表放 7 个景点。用一个可复用书写模式（符号 + label），示例（乌布、金巴兰机场、佩尼达离岛、Sanur 码头）：

```svg
<!-- 乌布 大本营 -->
<circle cx="250" cy="250" r="8" fill="#6B4F2A"/>
<text x="264" y="255" font-size="17" font-weight="600" fill="#3A3A3A">乌布 Ubud</text>
<!-- 德格拉朗梯田 + 圣泉寺 -->
<circle cx="250" cy="150" r="6" fill="#6B4F2A"/>
<text x="264" y="155" font-size="14" fill="#3A3A3A">德格拉朗梯田 · 圣泉寺 Tirta Empul</text>
<!-- 海神庙 -->
<circle cx="95" cy="300" r="6" fill="#6B4F2A"/>
<text x="60" y="288" font-size="14" fill="#3A3A3A">海神庙 Tanah Lot</text>
<!-- Sanur 码头（三角形＝▷ 码头） -->
<polygon points="322,354 322,368 336,361" fill="#1E88C7"/>
<text x="300" y="386" font-size="13" fill="#3A3A3A">Sanur 码头</text>
<!-- 金巴兰 / DPS 机场（点 + ✈） -->
<circle cx="215" cy="500" r="7" fill="#6B4F2A"/>
<text x="205" y="497" font-size="14">✈</text>
<text x="150" y="524" font-size="14" fill="#3A3A3A">金巴兰 · DPS 机场</text>
<!-- 乌鲁瓦图 -->
<circle cx="140" cy="560" r="6" fill="#6B4F2A"/>
<text x="70" y="565" font-size="14" fill="#3A3A3A">乌鲁瓦图 Uluwatu</text>
<!-- 努沙佩尼达 离岛（◆） -->
<polygon points="470,456 484,470 470,484 456,470" fill="#2E7D9A"/>
<text x="392" y="505" font-size="14" fill="#3A3A3A">努沙佩尼达</text>
<text x="382" y="522" font-size="11" fill="#5A5A5A">Kelingking · Broken Beach · Crystal Bay</text>
```

（英文小字 `Kelingking` 必须出现，供校验命中。）

- [ ] **Step 2: 运行校验，确认巴厘转绿**

Run: `python "<SCRATCHPAD>/validate_map.py"`
Expected: `MISSING` 里不再包含 `bali`（仍会列 `komodo`/`dates`/`legend`），退出码 2。

- [ ] **Step 3: 提交**

```bash
git add docs/itinerary/景点路线图.svg
git commit -m "行程图：巴厘 panel 七处景点（乌布/梯田圣泉/海神庙/Sanur/金巴兰DPS/乌鲁瓦图/佩尼达）"
```

---

## Task 3: 科摩多 panel 景点

**Files:**
- Modify: `docs/itinerary/景点路线图.svg`（填充 `<g id="komodo">`）

**Interfaces:**
- Consumes: Task 1 的 `<g id="komodo">` 空组、科摩多坐标表。
- Produces: 科摩多 LBJ + 群岛景点 + 镇上活动小字，供 Task 4 两条出海环线锚定。

- [ ] **Step 1: 填充科摩多景点**

在 `<g id="komodo">` 内按坐标表放景点，符号约定：`▲`帕达尔登顶、`~`沙滩/沙洲、`◇`Manta 潜点、`●`其余、LBJ 挂 `✈`。示例：

```svg
<!-- LBJ 镇+机场 母港 -->
<circle cx="1090" cy="380" r="9" fill="#154360"/>
<text x="1078" y="376" font-size="14">✈</text>
<text x="1000" y="404" font-size="17" font-weight="600" fill="#3A3A3A">拉布安巴焦 LBJ</text>
<text x="985" y="422" font-size="11" fill="#5A5A5A">镇上：Bukit Cinta · Kampung Ujung 夜市 · 镜石洞 Batu Cermin</text>
<!-- 飞狐岛 -->
<circle cx="990" cy="300" r="5" fill="#154360"/>
<text x="1000" y="304" font-size="12" fill="#3A3A3A">飞狐岛 Kalong</text>
<!-- Kelor / Kanawa -->
<circle cx="940" cy="250" r="5" fill="#154360"/>
<text x="950" y="254" font-size="12" fill="#3A3A3A">Kelor</text>
<circle cx="860" cy="200" r="5" fill="#154360"/>
<text x="870" y="204" font-size="12" fill="#3A3A3A">Kanawa</text>
<!-- Taka Makassar 白沙洲（~） -->
<text x="762" y="206" font-size="16" fill="#C9A24B">〜</text>
<text x="700" y="196" font-size="12" fill="#3A3A3A">Taka Makassar 白沙洲</text>
<!-- Manta Point（◇） -->
<polygon points="830,350 840,360 830,370 820,360" fill="none" stroke="#154360" stroke-width="1.5"/>
<text x="838" y="356" font-size="12" fill="#3A3A3A">Manta Point</text>
<!-- 帕达尔 登顶（▲） -->
<polygon points="770,438 782,458 758,458" fill="#8A6D3B"/>
<text x="700" y="470" font-size="14" font-weight="600" fill="#3A3A3A">帕达尔岛 Padar</text>
<!-- 科莫多龙岛 -->
<circle cx="680" cy="470" r="6" fill="#154360"/>
<text x="640" y="458" font-size="13" fill="#3A3A3A">科莫多龙岛</text>
<!-- 粉沙滩（~） -->
<text x="726" y="524" font-size="16" fill="#E39AA8">〜</text>
<text x="700" y="542" font-size="12" fill="#3A3A3A">粉沙滩 Pink Beach</text>
```

- [ ] **Step 2: 运行校验，确认科摩多转绿**

Run: `python "<SCRATCHPAD>/validate_map.py"`
Expected: `MISSING` 里不再包含 `komodo`（仍会列 `dates`/`legend`），退出码 2。

- [ ] **Step 3: 提交**

```bash
git add docs/itinerary/景点路线图.svg
git commit -m "行程图：科摩多 panel 景点（LBJ 母港+镇上/帕达尔/科莫多龙/粉沙滩/Manta/Kelor/Kanawa/Taka）"
```

---

## Task 4: 每日路线 + 10.7 飞行弧

**Files:**
- Modify: `docs/itinerary/景点路线图.svg`（填充 `<g id="routes">` 与 `<g id="flight">`）

**Interfaces:**
- Consumes: Task 2/3 景点坐标、Global Constraints 调色板。
- Produces: 巴厘 10.2–10.6 开放路线、科摩多 10.7 镇上/10.8·10.9 闭合出海环/10.10 离港、跨 panel 10.7 虚线飞行弧；每条线用当天颜色，路径起点带日期文字标签（供 `dates` 校验命中）。

- [ ] **Step 1: 画巴厘每日路线（10.2–10.6）**

在 `<g id="routes">` 内，用 `stroke` = 当天色、`fill="none"`、末端 `marker` 箭头或线尾加短三角。每条线起点附近放当天日期标签。示例（10.3 佩尼达跨海→移住乌布、10.6 含海神庙二选一虚线支线）：

```svg
<defs>
  <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
    <path d="M0,0 L6,3 L0,6 Z" fill="#555"/>
  </marker>
</defs>
<!-- 10.2 南部→金巴兰 -->
<path d="M215,500 L215,500" stroke="#E8843C" stroke-width="3"/>
<text x="150" y="490" font-size="12" fill="#E8843C" font-weight="700">10.2</text>
<!-- 10.3 Sanur→佩尼达→回→乌布 -->
<path d="M330,360 L470,470" stroke="#1E88C7" stroke-width="3" stroke-dasharray="2 3" marker-end="url(#arrow)"/>
<path d="M470,470 C420,380 320,300 250,258" stroke="#1E88C7" stroke-width="3" marker-end="url(#arrow)"/>
<text x="345" y="352" font-size="12" fill="#1E88C7" font-weight="700">10.3</text>
<!-- 10.4 乌布→梯田/圣泉→乌布 -->
<path d="M250,250 L250,158 M250,158 L250,242" stroke="#3FA34D" stroke-width="3" marker-end="url(#arrow)"/>
<text x="264" y="205" font-size="12" fill="#3FA34D" font-weight="700">10.4</text>
<!-- 10.5 乌布松弛（就地小圈） -->
<circle cx="250" cy="250" r="20" fill="none" stroke="#8E6BB0" stroke-width="2.5" stroke-dasharray="4 3"/>
<text x="276" y="235" font-size="12" fill="#8E6BB0" font-weight="700">10.5</text>
<!-- 10.6 乌布→乌鲁瓦图→金巴兰；海神庙作二选一虚线支线 -->
<path d="M250,258 L140,552 L215,508" stroke="#D64545" stroke-width="3" marker-end="url(#arrow)"/>
<path d="M250,258 L100,300" stroke="#D64545" stroke-width="2" stroke-dasharray="5 4"/>
<text x="185" y="410" font-size="12" fill="#D64545" font-weight="700">10.6</text>
<text x="118" y="322" font-size="10" fill="#D64545">（海神庙二选一）</text>
```

- [ ] **Step 2: 画 10.7 跨 panel 飞行弧**

在 `<g id="flight">` 内，从巴厘 DPS(215,500) 到科摩多 LBJ(1090,380) 画一条大弧虚线，中点上方标 `✈ 10.7 DPS→LBJ`：

```svg
<path d="M230,520 Q640,760 1080,398" fill="none" stroke="#F2B705" stroke-width="3.5" stroke-dasharray="10 7"/>
<text x="600" y="742" text-anchor="middle" font-size="16" font-weight="700" fill="#C98A00">✈ 10.7　DPS → LBJ　AirAsia 11:25→12:40</text>
```

- [ ] **Step 3: 画科摩多路线（10.7 镇上 / 10.8·10.9 出海闭合环 / 10.10 离港）**

```svg
<!-- 10.7 抵港→镇上 -->
<circle cx="1090" cy="380" r="26" fill="none" stroke="#F2B705" stroke-width="2.5" stroke-dasharray="4 3"/>
<text x="1120" y="352" font-size="12" fill="#C98A00" font-weight="700">10.7 镇上</text>
<!-- 10.8 出海①经典线 闭合环：LBJ→帕达尔→科莫多龙→粉沙滩→Manta→LBJ -->
<path d="M1090,380 L770,450 L680,470 L740,520 L830,360 Z" fill="none" stroke="#0E6BA8" stroke-width="3"/>
<text x="1030" y="470" font-size="12" fill="#0E6BA8" font-weight="700">10.8 出海①经典线</text>
<!-- 10.9 出海②浮潜线 闭合环：LBJ→Kelor→Kanawa→Taka→LBJ -->
<path d="M1090,380 L940,250 L860,200 L780,210 Z" fill="none" stroke="#16A0A0" stroke-width="3" stroke-dasharray="7 4"/>
<text x="1035" y="300" font-size="12" fill="#16A0A0" font-weight="700">10.9 出海②浮潜线</text>
<!-- 10.10 镇上收尾→离港 -->
<path d="M1090,380 L1150,360" stroke="#6B7F99" stroke-width="3" marker-end="url(#arrow)"/>
<text x="1096" y="352" font-size="13">✈</text>
<text x="1040" y="430" font-size="12" fill="#6B7F99" font-weight="700">10.10 收尾 · 15:00 联程回国</text>
```

- [ ] **Step 4: 运行校验，确认日期全绿**

Run: `python "<SCRATCHPAD>/validate_map.py"`
Expected: `MISSING` 里不再包含 `dates`（仅剩 `legend`），退出码 2。

- [ ] **Step 5: 提交**

```bash
git add docs/itinerary/景点路线图.svg
git commit -m "行程图：每日路线连线 10.2–10.10（含 10.7 跨区飞行弧、科摩多两次出海闭合环）"
```

---

## Task 5: 底部图例带

**Files:**
- Modify: `docs/itinerary/景点路线图.svg`（填充 `<g id="legend">`）

**Interfaces:**
- Consumes: Global Constraints 调色板与含义列。
- Produces: 9 行图例（色块 + 日期 + 当天主活动一句），令校验全绿。

- [ ] **Step 1: 画图例（9 项，两列排布，y 700..810）**

每项 = 一个色块 `rect` + 文本 `日期（周几）＋活动`。文案锚词须含校验 `legend` 列（`金巴兰日落/佩尼达/梯田/松弛/乌鲁瓦图/飞/经典线/浮潜/回国`）。示例前三行 + 关键行：

```svg
<rect x="20" y="700" width="18" height="18" fill="#E8843C"/>
<text x="46" y="714" font-size="13" fill="#3A3A3A">10.2 (五) 南部落地 · 傍晚金巴兰日落海鲜</text>
<rect x="20" y="726" width="18" height="18" fill="#1E88C7"/>
<text x="46" y="740" font-size="13" fill="#3A3A3A">10.3 (六) 佩尼达一日（全员）→ 移住乌布</text>
<rect x="20" y="752" width="18" height="18" fill="#3FA34D"/>
<text x="46" y="766" font-size="13" fill="#3A3A3A">10.4 (日) 乌布观光：德格拉朗梯田 · 圣泉寺</text>
<rect x="20" y="778" width="18" height="18" fill="#8E6BB0"/>
<text x="46" y="792" font-size="13" fill="#3A3A3A">10.5 (一) 乌布松弛：SPA · 圣猴森林 · 山脊步道</text>
<!-- 右列 10.6–10.10 -->
<rect x="620" y="700" width="18" height="18" fill="#D64545"/>
<text x="646" y="714" font-size="13" fill="#3A3A3A">10.6 (二) 乌鲁瓦图断崖庙+火舞（或海神庙）</text>
<rect x="620" y="726" width="18" height="18" fill="#F2B705"/>
<text x="646" y="740" font-size="13" fill="#3A3A3A">10.7 (三) 飞 DPS→LBJ · 傍晚 Bukit Cinta 日落</text>
<rect x="620" y="752" width="18" height="18" fill="#0E6BA8"/>
<text x="646" y="766" font-size="13" fill="#3A3A3A">10.8 (四) 出海①经典线：帕达尔·龙·粉沙滩·Manta</text>
<rect x="620" y="778" width="18" height="18" fill="#16A0A0"/>
<text x="646" y="792" font-size="13" fill="#3A3A3A">10.9 (五) 出海②浮潜线：Kelor·Kanawa·Taka 白沙洲</text>
<rect x="620" y="804" width="18" height="18" fill="#6B7F99"/>
<text x="646" y="818" font-size="13" fill="#3A3A3A">10.10 (六) 镇上收尾 · 15:00 联程回国</text>
```

（注意最后一行 y 到 818，若贴边可整体上移或把画布 viewBox 高度留足 820；已在 Global Constraints 设 820。）

- [ ] **Step 2: 运行校验，确认全绿**

Run: `python "<SCRATCHPAD>/validate_map.py"`
Expected: `OK all checks passed`，退出码 0。

- [ ] **Step 3: 提交**

```bash
git add docs/itinerary/景点路线图.svg
git commit -m "行程图：底部 9 天图例带（日期+每日主活动）"
```

---

## Task 6: md 引用 + 视觉验收

**Files:**
- Modify: `docs/itinerary/路线与游玩地点.md`（标题下方加图片引用）

**Interfaces:**
- Consumes: 成品 `景点路线图.svg`。
- Produces: md 顶部一行 `![景点与路线图](景点路线图.svg)`；一次 Playwright 渲染截图验收。

- [ ] **Step 1: 在 md 里引用图**

编辑 `docs/itinerary/路线与游玩地点.md`，在首个标题行 `# 路线与游玩地点` 与下一段之间插入：

```markdown
# 路线与游玩地点

![印尼行程景点与路线图（方案三）](景点路线图.svg)

记录巴厘岛及周边（含科莫多岛等）的行程路线规划、各地点游玩方式。
```

- [ ] **Step 2: 视觉验收——Playwright 打开 SVG 截图**

用 Playwright MCP 打开本地文件并截图，人工核对：两 panel 分区清晰、中文不乱码、景点不叠压、9 天线各自成色、飞行弧跨区、图例齐全。

Run（工具调用）：
- `browser_navigate` → `file:///c:/Users/Administrator/Desktop/workFiles/Travalplan/docs/itinerary/景点路线图.svg`
- `browser_take_screenshot`（full page）

Expected: 截图与方案三一致；若发现文字叠压/越界，回到对应 Task 微调坐标（±20）后重截。

- [ ] **Step 3: 终检校验脚本仍全绿**

Run: `python "<SCRATCHPAD>/validate_map.py"`
Expected: `OK all checks passed`。

- [ ] **Step 4: 提交**

```bash
git add docs/itinerary/路线与游玩地点.md
git commit -m "行程：路线文档顶部引用景点路线图 SVG"
```

---

## Self-Review

**Spec coverage（逐条对 spec 验收标准）：**
1. 渲染正常/中文不乱码/无外链 → Task 1 校验(无外链) + Task 6 Playwright 视觉验收 ✓
2. 含全部关键景点、两 panel 分区、10.7 飞行弧跨区 → Task 2/3 景点 + Task 4 飞行弧 ✓
3. 9 天各自成色、与图例一一对应、两次出海闭合环 → Task 4 路线 + Task 5 图例 ✓
4. 无 LJ 分支/无方案一二/无群岛带 → 计划全程未出现，Global Constraints 明列 ✓
5. md 成功引用 → Task 6 ✓

**Placeholder scan:** 无 TBD/TODO；每个改代码的 Step 均给出真实 SVG 片段与坐标；校验脚本给全码。✓

**Type/命名一致性:** 组 id（`bali`/`komodo`/`flight`/`routes`/`legend`）Task 1 定义、后续 Task 逐一填充，名称一致；`#arrow` marker 在 Task 4 Step 1 定义后于同组复用；调色板 hex 全程与 Global Constraints 一致。✓

**已知取舍:** 校验脚本放 scratchpad 不提交（静态 doc 资产不引入测试文件）；10.2 是南部内极短线，用短 path + 日期标签保证 `10.2` 命中校验并在图例出现。
