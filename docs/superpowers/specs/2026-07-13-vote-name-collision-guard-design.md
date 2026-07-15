# 投票撞名防护 · 设计文档（Spec）

- **日期**：2026-07-13
- **相关文件**：`webpage/app.js`（cloud 模块）、`webpage/identity.js`、`webpage/build.py`、`webpage/style.css`、`webpage/test/identity.test.js`
- **上线目标**：`https://plan-d0gstt7r6507aa319-1451599494.tcloudbaseapp.com`（CloudBase 静态托管）

---

## 1. 背景与问题

投票身份采用「用户名即账号」：文档 id 由用户名派生（`identity.js` 的 `deriveDocId`，
`u_ + base64url(归一化名字)`）。**两台机器输入相同用户名 → 派生出同一个 docId → 抢写同一条云文档。**

匿名登录那层拦不住：每台机器各拿一个匿名 `uid`，安全规则只要求 `auth.uid != null`，
没有「仅本人可改」约束，`writeSet` 是 `doc(id).set(data)`（整篇覆盖、无事务/版本号）。

由此产生两条**静默**失败路径：

1. **稳态互相覆盖（last-write-wins 丢票）**：合并只在首次绑定时发生一次；绑定后每次投票走
   `doSync` 的「常态」分支，用本机 state 整篇 `set` 覆盖，两台同名机器永久发散、来回清空对方选票。
2. **后来者继承前者选票**：不同的人后输同名时，首次同步静默 `getDoc` + `mergeState` + `adoptLocal`，
   把前者的整份选票当成自己的拉到本机，随后一改即覆盖前者。

附带：`已 N 人参与` = 文档数，两个同名的人被算作 1 人，汇总少一票且偏向后投者。

## 2. 目标与成功标准

**目标**：当用户提交时若其用户名在云端已有他人选票，明确弹窗让用户自己判断「那是不是我」，
避免静默覆盖 / 静默继承。

**成功标准**：
- 两个不同的人先后用同一名字投票：第二个人**提交时弹窗**，选「换个名字」后各自独立成两条文档，
  群人数正确 +1，双方选票互不覆盖。
- 同一个人换设备输同名：提交时弹窗，选「就是我」把旧票合并找回（沿用现有 `mergeState`）。
- 存量已绑定用户不受影响、无需迁移。

**非目标（YAGNI）**：不做服务端「仅本人可改」安全规则改造、不做乐观锁/事务、不做实时协同合并。
6 人熟人私链场景下，提交时一次撞名确认已足够。

## 3. 行为变化（关键）

把「本机首次绑定到某名字的云文档」从连续自动同步里挪出来，**收拢到点「提交」的那一刻**：

- **提交前**：投票、改名、选主线都只存本机 `localStorage`，**不写云端**，群汇总里暂时看不到自己
  —— 直到点「提交我的选择」。
- **提交后**：与现状一致，后续每次投票自动同步到自己那条已绑定文档（已绑定，不会再撞）。
- 顺带关闭旧的「换设备输同名 → 静默拉取他人选票」隐患：现在必须用户亲手点「合并」才会拉。

## 4. 同步模型（`app.js` 的 `cloud` 模块）

| 触发 | 现在 | 改后 |
|---|---|---|
| 投票 / 改名 / 选主线（`syncMine`，防抖） | 写云（会首次绑定） | 仅当**已绑定到当前名字**（`newId === syncedId`）才写自己的文档；否则只存本机、不写云 |
| 点「提交」（`submit`，即时） | 立即写云 | 计算 `newId` → 与已绑定 `syncedId` 不同（首次绑定/改名）→ 先 `getDoc` 探测 → 撞名弹窗，否则绑定写入 |

`syncMine` 判定规则：**只有 `newId && newId === syncedId` 才写云**；其余（无名、首次绑定、改名到新 id）
一律推迟到提交，本机照常 `save()` + 刷新视图。

`submit` 流程（在线时；离线保持现有「云同步暂不可用，无法提交」）：
1. `newId` 为空（清空了名字）→ 删旧文档、清 `SYNCED_KEY`、只本机。
2. `newId === syncedId`（重复提交/自己）→ 正常覆盖自己的文档。
3. `newId !== syncedId`（首次绑定或改名）→ `getDoc(newId)`：
   - 分类为 `free`（无此文档或该文档无有效标记）→ 直接绑定写入（若是改名，写入成功后删旧名文档）。
   - 分类为 `occupied`（已有非空选票且不是自己）→ **不写入**，返回撞名信号交给 UI 弹窗；
     并把探到的 `existing` 文档暂存，供「合并」分支复用（避免二次 `getDoc` 竞态）。

## 5. 纯判定逻辑（`identity.js`，可被 `node --test` 覆盖）

与 `tally.js`/`mergeState` 一致，判定放进 `identity.js` 纯函数，DOM/弹窗留在 `app.js`：

```
countDecided(picks) → number
  // 统计 must/maybe/skip 的个数；忽略非法值与 __proto__（复用 RANK 表）

classifyBind(syncedId, newId, existingDoc) → string
  "noname"    // newId 为空
  "self"      // newId === syncedId → 正常覆盖
  "free"      // existingDoc 缺失、或 countDecided(existingDoc.picks) === 0 → 直接绑定
  "occupied"  // existingDoc 有非空选票且 newId !== syncedId → 撞名，弹窗
```

`app.js` 据 `classifyBind` 结果分派；`countDecided(existing.picks)` 的数值 + `existing.updatedAt`
用于弹窗文案（标记数、上次提交时间）。

## 6. 撞名弹窗（自定义弹层，不用原生 `confirm`）

原生 `confirm` 按钮只有「确定/取消」，分不清哪个是合并哪个是换名——正是要消除的困惑，故用自定义弹层。
markup 加在 `build.py` 的 sheet 区（`#sheet` 内、约 234–243 行附近），样式加进 `style.css`，复用现有遮罩/卡片风格。
提交按钮在 sheet 内，弹层叠在打开的 sheet 之上。

**文案（引导版，最终定稿）**：

```
「王」这个名字已经有人投过票了

云端有一份用「王」投的选择
（5 个标记 · 上次提交：今天 14:30）

· 如果那是你本人（换了手机或浏览器），
  选「就是我」把旧票找回来一起算
· 如果不是你，继续会盖掉对方的票
  ——请「换个名字」

   [ 就是我，找回旧票 ]   [ 不是我，换个名字 ]
```

- 名字（`「王」`）、标记数（`5 个标记`）、时间（`上次提交：今天 14:30`）为动态填充。
  时间由 `existing.updatedAt` 格式化：今天显示「今天 HH:MM」，否则「M月D日 HH:MM」；缺失则整段省略。
- **「就是我，找回旧票」** → 复用暂存的 `existing` 走 `mergeState`（按 must>maybe>skip 取高）写回
  + `adoptLocal` 把并集拉到本机 + 记 `SYNCED_KEY` + 若是改名则删旧名文档 → toast「已合并，你的选择已同步到群汇总」。
- **「不是我，换个名字」** → 不写任何云端；聚焦并选中名字输入框让用户改，toast「这个名字已被占用，换一个再提交」；
  本机选票不动，`SYNCED_KEY` 不变。
- 点遮罩 / Esc = 等同「换个名字」（安全默认：绝不覆盖别人）。

## 7. 涉及文件

- `identity.js` — 新增 `countDecided`、`classifyBind`（纯函数，导出到 `IdentityLib`）。
- `app.js` — 改 `cloud` 模块的 `syncMine`/提交逻辑（拆分「已绑定才自动同步」与「提交时绑定+撞名探测」）；
  submit 按钮处理撞名弹窗回调；新增 `showDupModal` 及其两个分支处理。
- `build.py` — sheet 区新增弹层 markup。
- `style.css` — 弹层样式（复用遮罩/卡片/按钮变量）。
- `test/identity.test.js` — 补 `countDecided`、`classifyBind` 单测。

## 8. 测试

- **单测**：`node --test webpage/test/identity.test.js`
  - `countDecided`：统计 must/maybe/skip；忽略非法值；忽略 `__proto__`；空 picks 返回 0。
  - `classifyBind`：`noname`（newId 空）、`self`（相等）、`free`（existing 缺失 / picks 全空 / 仅非法键）、
    `occupied`（existing 有效非空且 id 不同）。
- **手动验收**（两浏览器/无痕窗口）：
  1. 甲用「王」投票并提交 → 云端 1 条、群 1/6。
  2. 乙也输「王」投票并提交 → **弹窗**；选「换个名字」改成「李」再提交 → 云端 2 条、群 2/6，甲乙选票互不覆盖。
  3. 甲换个浏览器再输「王」提交 → 弹窗；选「就是我」→ 旧票合并回来、仍是同一条、群人数不增。

## 9. 构建与上线

- **构建**：`cd webpage && python3 build.py`（自动内联 `identity.js`/`app.js`/`style.css` 进 `index.html`）。
- **部署**：`tcb hosting deploy index.html index.html -e plan-d0gstt7r6507aa319`
  （仅 `index.html` 变化；`cloudbase.js` 不动，无需重新部署 SDK）。
- **兼容**：存量已绑定用户 `syncedId === newId` 走 `self` 分支，行为不变，无需数据迁移。
