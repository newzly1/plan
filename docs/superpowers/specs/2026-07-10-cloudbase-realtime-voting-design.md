# CloudBase 云数据库实时汇总投票 — 设计

日期：2026-07-10
状态：已通过设计评审，待写实现计划

## 背景与目标

投票参考网页 `webpage/index.html` 已部署在腾讯云 CloudBase 静态托管
（`https://plan-d0gstt7r6507aa319-1451599494.tcloudbaseapp.com`，国内直连），
供 6 人投票。当前投票完全是本地的：

- 每人在自己浏览器里点「必去 / 可去」，存在 `localStorage`（`bali_votes`）。
- 填名字（`bali_name`）、选组合线路（`bali_combo`）也存本地。
- 点「一键复制」把自己的投票拼成一段文本，粘到微信群。
- **由某个人把 6 段文本人工汇总**——这是要消除的痛点。

**目标**：6 人仍在同一个网页上投票，但投票直接写进 CloudBase 云数据库，
页面上实时显示合并后的排行/得票，谁都能随时看到结果——彻底不用复制粘贴、不用人工汇总。
链接不变、国内直连、复用现有免费环境。

## 核心决策（已与用户确认）

1. **附加式改造**：本地 `localStorage` 投票、卡片高亮、「一键复制」全部保留，
   云同步与汇总面板叠加在其上。SDK 没加载 / 断网时，本地投票 + 复制作为兜底仍可用。
2. **身份**：每人填名字（可随时改）。用匿名登录的 `_openid` 作为记录主键，
   每个浏览器一条稳定记录；本人能改自己的票，改不了别人的。
3. **汇总内容**：加权得分排序（必去 ×2 + 可去 ×1），组合线路也统计；
   顶部只显示「已 N 人参与」的数字，不点名、不催票，不展开「谁投的 / 还差谁」。

## 架构总览

```
浏览器（现有页面）
  ├─ 本地投票（localStorage，源自现有 app.js，保持不变）
  ├─ CloudBase Web SDK（同源加载，随站点部署）
  │    ├─ 匿名登录 → 稳定 _openid
  │    ├─ 每次投票/改名/改组合：防抖 upsert 自己那条云文档
  │    └─ 打开汇总 / 投完票 / 点刷新：拉取全部文档 → 算分 → 渲染排行
  └─ 「一键复制」兜底（保留）

CloudBase 环境 plan-d0gstt7r6507aa319
  └─ 云数据库集合 votes（每人一条，安全规则：人人可读、仅写自己那条）
```

从「纯离线自包含页面」变为「投票同步需联网」，但线上版本本就在线，且本地兜底仍在，可接受。

## 数据模型

云数据库集合 **`votes`**，每个参与者一条文档：

| 字段 | 类型 | 说明 |
|---|---|---|
| `_id` | string | CloudBase 自动主键 |
| `_openid` | string | 匿名 UID，SDK 自动写入；每个浏览器稳定，用于「只能改自己」 |
| `name` | string | 用户填写的名字（对应现有 `bali_name`） |
| `picks` | object | `{ "<spotId>": "must" \| "maybe" }`，对应现有 `bali_votes` |
| `combo` | string | 组合线路 id（对应现有 `bali_combo`），可为空 |
| `updatedAt` | number | 最后更新时间戳（`Date.now()`） |

**写入语义**：upsert——同一 `_openid` 已有文档则更新，否则创建。
`picks` / `combo` 整体覆盖为本地当前状态（本地即真值来源），不做字段级合并。

**安全规则**（CloudBase 数据库安全规则，自定义 JSON）：

```json
{
  "read": true,
  "write": "doc._openid == auth.openid"
}
```

人人可读（用于汇总）；只能创建/更新/删除 `_openid` 等于自己登录 openid 的那条，
防止误删/篡改别人的票。6 人熟人场景足够。

## 前端组件与数据流

改动集中在 `webpage/app.js`（投票/交互）与 `webpage/build.py`（打包 SDK）、`webpage/content.py` 或
模板（新增汇总面板 DOM），`webpage/style.css`（面板样式）。分为几个独立单元：

### 单元 A：云端连接层（新增，`app.js` 内一个小模块，如 `cloud`）
- 职责：初始化 SDK、匿名登录、暴露 `syncMine(state)` 与 `fetchAll()` 两个方法。
- 依赖：CloudBase Web SDK（同源）、环境 id `plan-d0gstt7r6507aa319`。
- 接口：
  - `cloud.ready` — Promise，登录完成后 resolve；失败则标记为「离线模式」。
  - `cloud.syncMine({name, picks, combo})` — 防抖（约 800ms）upsert 自己那条文档；离线时静默跳过。
  - `cloud.fetchAll()` — 返回全部文档数组；失败返回 `null`（面板显示「暂时无法加载，稍后刷新」）。
- 用 SDK 的 `persistence: 'local'` 让匿名身份跨会话稳定。
- 可测性：连接层与 UI 解耦，可对 `syncMine` / `fetchAll` 打桩单测汇总算法。

### 单元 B：投票同步挂钩（改现有代码）
- 在现有三处「本地保存后」追加一次 `cloud.syncMine(currentState())`：
  - 投票点击：`app.js:30-31`（`save()` 之后）。
  - 改名：`app.js:85`（写 `bali_name` 之后）。
  - 改组合线路：`app.js:87`（写 `bali_combo` 之后）。
- `currentState()` 从 `votes` / `localStorage` 拼出 `{name, picks, combo}`。
- 对用户无感：点击体验与现在一致，同步在后台防抖发生。

### 单元 C：实时汇总面板（新增 DOM + 渲染函数）
- 位置：放在「我的清单」浮层 `#sheet` 内、`#picks`（我的选择）下方，
  新增一块「大家的选择 · 实时汇总」，含一个「刷新」按钮。
- 渲染函数 `renderTally(docs)`（纯函数，输入文档数组，输出 HTML）：
  - 顶部：`已 N 人参与`（N = 文档数）。
  - 景点排行：对每个 `spotId`，`score = 必去人数×2 + 可去人数×1`，按 score 降序；
    每行显示 `id + 中文名 + 分数`（可附「必去 x / 可去 y」小字）。只列有票的景点。
  - 组合线路：统计每个 `combo` 的票数，降序，显示线路名 + 票数。
- 刷新时机：
  1. 打开 `#sheet` 时（`openSheet()` 里调用 `refreshTally()`）。
  2. 自己投完票后（`syncMine` 成功后，若 `#sheet` 可见则 `refreshTally()`）。
  3. 点「刷新」按钮。
  - （可选增强，本期不做）CloudBase 实时推送 `db.collection('votes').watch()`，
    让别人投票时本地自动更新。先用上面三种，最稳、够「实时」感；watch 留待将来。
- `renderTally` 是纯函数，可脱离网络单测。

### 单元 D：兜底
- SDK 加载失败 / 匿名登录失败 / 断网：`cloud.ready` reject，进入「离线模式」——
  同步静默跳过，汇总面板显示「云同步不可用，可用下方『一键复制』发群里」。
- 「一键复制」`app.js:115` 保留原样。

## 构建与部署改动

- **SDK 同源部署**：把 CloudBase Web SDK 的 UMD 打包文件下载进 `webpage/`
  （如 `webpage/vendor/cloudbase.js`），随站点部署，页面同源加载，不依赖第三方 CDN，国内直连最稳。
  用国内镜像 `curl` 下载（遵循 CLAUDE.md：urllib 会卡）。
- **`build.py`**：把 SDK 文件与新版 `app.js`、面板 DOM/样式打进产物；
  产物新增部署目标（SDK 文件）。`index.html` 仍按现有流程生成。
- **部署命令**（README 现有命令基础上）：
  - `tcb hosting deploy index.html index.html -e plan-d0gstt7r6507aa319`（页面/脚本变化）
  - `tcb hosting deploy vendor vendor -e plan-d0gstt7r6507aa319`（首次上传 SDK；之后一般不变）
- 链接不变。

## 一次性 CloudBase 控制台配置（约 5 分钟，需用户在控制台操作）

1. **开启匿名登录**：环境 → 登录授权 → 开启「匿名登录」。
2. **建集合**：云数据库 → 新建集合 `votes`。
3. **设安全规则**：集合 `votes` → 权限设置 → 自定义安全规则，填入上面的 JSON。
4. **加 Web 安全域名**：环境 → 安全配置 → Web 安全域名，加入托管域名
   `plan-d0gstt7r6507aa319-1451599494.tcloudbaseapp.com`
   （否则浏览器端 SDK 认证会被拒）。

（实现阶段会把这 4 步整理成一份带截图路径的清单交给用户执行，代码依赖这些配置就绪。）

## 测试策略

- **纯函数单测**：`renderTally(docs)` 与 `currentState()` 的算分/排序，用构造的文档数组验证
  加权得分排序、组合线路统计、空数据、单人多景点等。
- **端到端手测**：
  - 两个浏览器（或隐身窗）各投不同票 → 互相刷新能看到合并结果、分数正确。
  - 断开网络 → 投票仍能点、复制仍可用、面板提示离线、不报错。
  - 改名后再投 → 云文档 `name` 更新，仍是同一条（`_openid` 不变）。
  - 安全规则：尝试写别人 `_openid` 的文档被拒（可用控制台或第二身份验证）。

## 风险与取舍

- **联网依赖**：投票同步需要网络；本地投票 + 复制兜底仍在，可接受。
- **公开链接可刷票**：匿名 + 链接公开，理论上有人拿链接能投票；6 人熟人低风险，
  安全规则已挡住「删改别人票」。真要防可后续加简单口令，本期不做（YAGNI）。
- **免费环境额度**：6 人、少量文档，读写量极小，远在免费额度内。
- **环境到期**：CloudBase 免费体验环境 2027-01-08 到期，需手动续期（见 CLAUDE.md），与本设计无关但需留意。

## 非目标（YAGNI）

- 真正的账号体系 / 口令防刷。
- 字段级合并、投票历史、审计。
- 管理后台。
- 实时推送 `watch`（本期用刷新触发；留作将来增强）。
