# 投票体验优化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把投票页从「本地三态打卡」升级为「去摩擦 + 轻共识」：`略过` 计入进度、底部 bar 常驻 `你 N/14 · 群 N/6` + 群体最爱、实时汇总自动新鲜、并把身份从「机器」改为「用户名即账号」。

**Architecture:** 纯逻辑（名字归一化、docId 派生、投票合并）抽进新的 UMD 小库 `identity.js`（浏览器内联 + Node 单测），与既有 `tally.js` 同构；有网络副作用的 CloudBase 读写胶水留在 `app.js` 的 `cloud` 模块，只调用纯库 + SDK。UI（两行 bar、灰章、提示）在 `style.css` / `build.py` / `app.js`。

**Tech Stack:** 原生 ES5 风格 JS（无框架、无打包）、CloudBase Web SDK v2.31.0（全局 `cloudbase`）、Python 3 标准库构建（`build.py`）、Node 内置 `node:test`。

## Global Constraints

- **进度分母**：用 `ITEMS.length` 计算，**绝不写死**（当前 14）。
- **群分母**：写死 `6`。
- **第三态**：文案 `略过`、内部值 `skip`、榜单**中性**（`tally.js` 已忽略非 must/maybe）、**计入进度**、盖弱化灰章。
- **身份**：`docId` 由归一化名字派生；**无名字 = 只本机、不写云**；匿名登录仅作**写权限门票**；**CloudBase 安全规则不变** `{ "read": true, "write": "auth.uid != null" }`。
- **SDK**：必须 v2.31.0（全局 `cloudbase`），登录用 `auth.signInAnonymously()`。
- **构建/部署**：`cd webpage && python3 build.py`；线上仅需 `tcb hosting deploy index.html index.html -e plan-d0gstt7r6507aa319`（`tally.js`/`identity.js` 均内联进 `index.html`）。
- **依赖**：只用 Python 标准库与 Node 内置测试；不新增 npm 包。
- **语言**：所有面向用户文案与 commit message 用中文。

---

### Task 1: 纯身份/合并库 `identity.js` + 单测

**Files:**
- Create: `webpage/identity.js`
- Test: `webpage/test/identity.test.js`

**Interfaces:**
- Produces（供 Task 4 的 `app.js` `cloud` 模块使用）：
  - `IdentityLib.normalizeName(name: string): string` — 去首尾空白 + 内部空白折叠 + 小写。
  - `IdentityLib.deriveDocId(name: string): string` — 归一化名字→`"u_"+base64url(utf8)`；空名返回 `""`。
  - `IdentityLib.mergePicks(a: object, b: object): object` — 并集，冲突取更高优先级 `must>maybe>skip`，丢弃非法值。
  - `IdentityLib.mergeState(local, cloud): {name, picks, combo}` — name 取本机、picks 并集、combo 本机优先否则云端。
  - Node: `module.exports = 上述 4 个函数`；浏览器：挂到 `self.IdentityLib`。

- [ ] **Step 1: 写失败测试**

Create `webpage/test/identity.test.js`:

```javascript
"use strict";
const test = require("node:test");
const assert = require("node:assert");
const { normalizeName, deriveDocId, mergePicks, mergeState } = require("../identity.js");

test("normalizeName: 去空白+折叠+小写", () => {
  assert.strictEqual(normalizeName("  Bob  "), "bob");
  assert.strictEqual(normalizeName("小  李"), "小 李");
  assert.strictEqual(normalizeName("ALICE"), "alice");
  assert.strictEqual(normalizeName(null), "");
  assert.strictEqual(normalizeName(undefined), "");
});

test("deriveDocId: 同名同 id、异名异 id、空名空串、大小写/空白不敏感", () => {
  assert.strictEqual(deriveDocId(""), "");
  assert.strictEqual(deriveDocId("   "), "");
  assert.strictEqual(deriveDocId("小李"), deriveDocId("小李"));
  assert.strictEqual(deriveDocId("Bob"), deriveDocId(" bob "));
  assert.notStrictEqual(deriveDocId("小李"), deriveDocId("小李子"));
  assert.match(deriveDocId("小李"), /^u_[A-Za-z0-9_-]+$/);
});

test("mergePicks: 并集 + 冲突取更高优先级 must>maybe>skip", () => {
  assert.deepStrictEqual(
    mergePicks({ A1: "maybe" }, { A1: "must", B1: "skip" }),
    { A1: "must", B1: "skip" }
  );
  assert.deepStrictEqual(mergePicks({ A1: "must" }, { A1: "skip" }), { A1: "must" });
  assert.deepStrictEqual(mergePicks({ A1: "skip" }, { A1: "maybe" }), { A1: "maybe" });
});

test("mergePicks: 丢弃非法/遗留值（如旧的 no）", () => {
  assert.deepStrictEqual(mergePicks({ A1: "no" }, {}), {});
  assert.deepStrictEqual(mergePicks({ A1: "must", B1: "weird" }, {}), { A1: "must" });
});

test("mergeState: name 本机、picks 并集、combo 本机优先否则云端", () => {
  const local = { name: "小李", picks: { A1: "maybe" }, combo: "" };
  const cloud = { name: "旧名", picks: { A1: "must", B1: "skip" }, combo: "2" };
  assert.deepStrictEqual(mergeState(local, cloud), {
    name: "小李",
    picks: { A1: "must", B1: "skip" },
    combo: "2"
  });
  assert.deepStrictEqual(mergeState({ combo: "1" }, { combo: "2" }).combo, "1");
});
```

- [ ] **Step 2: 运行测试确认失败**

Run: `node --test webpage/test/identity.test.js`
Expected: FAIL —`Cannot find module '../identity.js'`。

- [ ] **Step 3: 写最小实现**

Create `webpage/identity.js`:

```javascript
// webpage/identity.js — 纯身份/合并逻辑，浏览器（build 内联）与 Node 测试共用。
(function (root) {
  "use strict";
  var RANK = { must: 3, maybe: 2, skip: 1 };

  function normalizeName(name) {
    return String(name == null ? "" : name).trim().replace(/\s+/g, " ").toLowerCase();
  }

  function b64url(str) {
    var b64;
    if (typeof Buffer !== "undefined" && Buffer.from) b64 = Buffer.from(str, "utf8").toString("base64");
    else b64 = btoa(unescape(encodeURIComponent(str)));
    return b64.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  }

  function deriveDocId(name) {
    var n = normalizeName(name);
    return n ? "u_" + b64url(n) : "";
  }

  function mergePicks(a, b) {
    a = a || {}; b = b || {};
    var out = {}, k;
    for (k in a) if (Object.prototype.hasOwnProperty.call(a, k)) out[k] = a[k];
    for (k in b) {
      if (!Object.prototype.hasOwnProperty.call(b, k)) continue;
      if (!out[k] || (RANK[b[k]] || 0) > (RANK[out[k]] || 0)) out[k] = b[k];
    }
    for (k in out) if (Object.prototype.hasOwnProperty.call(out, k) && !RANK[out[k]]) delete out[k];
    return out;
  }

  function mergeState(local, cloud) {
    local = local || {}; cloud = cloud || {};
    var hasLocalCombo = local.combo != null && local.combo !== "";
    return {
      name: local.name || cloud.name || "",
      picks: mergePicks(local.picks, cloud.picks),
      combo: hasLocalCombo ? local.combo : (cloud.combo || "")
    };
  }

  var api = { normalizeName: normalizeName, deriveDocId: deriveDocId, mergePicks: mergePicks, mergeState: mergeState };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.IdentityLib = api;
})(typeof self !== "undefined" ? self : this);
```

- [ ] **Step 4: 运行测试确认通过**

Run: `node --test webpage/test/identity.test.js`
Expected: PASS（5 个 test 全绿）。

- [ ] **Step 5: 提交**

```bash
git add webpage/identity.js webpage/test/identity.test.js
git commit -m "投票优化：新增纯身份/合并库 identity.js（名字归一化、docId 派生、投票合并）+ 单测"
```

---

### Task 2: `tally.js` 的 `skip` 回归测试

**Files:**
- Test: `webpage/test/tally.test.js`（追加一条）

**Interfaces:**
- Consumes: `computeTally(docs, items, combos)`（既有，无改动）。

- [ ] **Step 1: 写失败测试（追加到文件末尾）**

在 `webpage/test/tally.test.js` 末尾追加：

```javascript
test("skip 值计入参与人数但不计分、不进榜单", () => {
  const docs = [
    { picks: { A1: "must", B2: "skip" } },
    { picks: { A1: "skip", C3: "skip" } }
  ];
  const r = computeTally(docs, ITEMS, COMBOS);
  assert.strictEqual(r.voterCount, 2);              // 两人都算参与
  assert.deepStrictEqual(r.spots, [                 // 只有 A1 因一票 must 上榜；skip 全部被忽略
    { id: "A1", zh: "巴厘岛门户", must: 1, maybe: 0, score: 2 }
  ]);
});
```

- [ ] **Step 2: 运行测试确认通过（回归保护，应直接通过）**

Run: `node --test webpage/test/tally.test.js`
Expected: PASS（新用例通过，证明 `skip` 天然被忽略）。若失败则说明 `tally.js` 行为已变，需回看。

- [ ] **Step 3: 提交**

```bash
git add webpage/test/tally.test.js
git commit -m "投票优化：补 skip 被榜单忽略的回归测试"
```

---

### Task 3: 投票模型改造——`略过`/`skip` + 灰章 + hero「6 人同行」

**Files:**
- Modify: `webpage/build.py`（`spot()` 第三个按钮；`hero()` 事实条）
- Modify: `webpage/style.css`（`.v-no`→`.v-skip`；新增 skip 灰章）
- Modify: `webpage/app.js`（新增 `decidedCount()`）

**Interfaces:**
- Produces: `decidedCount(): number` — 统计 `votes` 中值为 `must`/`maybe`/`skip` 的键数（供 Task 4 的 `renderBar` 用）。

- [ ] **Step 1: build.py 改第三个按钮（文案 + class + data-v）**

在 `webpage/build.py` 的 `spot()` 中，把：

```python
    <button type="button" class="v v-no" data-v="no">无所谓</button>
```

改为：

```python
    <button type="button" class="v v-skip" data-v="skip">略过</button>
```

- [ ] **Step 2: build.py 改 hero 事实条**

在 `webpage/build.py` 的 `hero()` 中，把：

```python
    <div class="facts"><span>10.2 – 10.11</span><span>9–10 天</span><span>多人同行</span><span>起止 DPS</span></div>
```

改为：

```python
    <div class="facts"><span>10.2 – 10.11</span><span>9–10 天</span><span>6 人同行</span><span>起止 DPS</span></div>
```

- [ ] **Step 3: style.css 改按钮类名 + 新增 skip 灰章**

在 `webpage/style.css`，把两处 `.v-no` 改名（第 202、206 行附近）：

```css
.v-skip{border-color:var(--line-2);color:var(--ink-soft)}
```
```css
.v-skip[aria-pressed="true"]{background:var(--ground-2);border-color:var(--line-2);color:var(--ink-soft)}
```

在 stamp 区块（`@keyframes stampin` 上一行，第 215 行后）追加 skip 灰章：

```css
.spot[data-vote="skip"] .stamp{display:grid;color:var(--ink-faint);border:1.5px solid var(--ink-faint)}
.spot[data-vote="skip"] .stamp::after{content:"略过"}
```

- [ ] **Step 4: app.js 新增 `decidedCount()`**

在 `webpage/app.js` 中，`pickCount` 函数（约第 89 行）之后追加：

```javascript
  function decidedCount(){ return Object.keys(votes).filter(function(k){ var v=votes[k]; return v==="must"||v==="maybe"||v==="skip"; }).length; }
```

- [ ] **Step 5: 重新构建**

Run: `cd webpage && python3 build.py`
Expected: 打印 `wrote index.html : ... KB` 与 `wrote images/ : ... files`，无报错。

- [ ] **Step 6: 手动验收**

在浏览器打开 `webpage/index.html`：
- 每张卡第三个按钮显示 **「略过」**；点它 → 卡片右上出现**灰色「略过」钢印**，按钮呈选中态。
- hero 顶部事实条显示 **「6 人同行」**。
- 点 必去/可去 仍分别是绿章/墨章（未回归）。

- [ ] **Step 7: 运行既有单测确认未回归**

Run: `node --test webpage/test/tally.test.js webpage/test/identity.test.js`
Expected: PASS。

- [ ] **Step 8: 提交**

```bash
git add webpage/build.py webpage/style.css webpage/app.js webpage/index.html webpage/images
git commit -m "投票优化：无所谓→略过（skip，计入进度、盖灰章），hero 改 6 人同行"
```

---

### Task 4: 身份即用户名 + 实时汇总自动新鲜（`cloud` 模块重写）

**Files:**
- Modify: `webpage/app.js`（`cloud` 模块整体重写；`openSheet`/`nameIn`/`combo`/刷新按钮接线；`renderTally` 文案；新增 `sheetOpen`/`renderSheetTally`/`adoptLocal`/`updateViews`；加载即拉 + 可见性轮询）
- Modify: `webpage/build.py`（内联 `identity.js`）

**Interfaces:**
- Consumes: `IdentityLib.deriveDocId` / `IdentityLib.mergeState`（Task 1）；`decidedCount`（Task 3）；`TallyLib.computeTally`（既有）。
- Produces（供 Task 5）：
  - `cloud.group(): tally|null` — 最近一次汇总结果（`TallyLib.computeTally` 的返回或 `null`）。
  - `cloud.refreshGroup(): Promise` — 拉全量、算汇总、缓存、刷新视图。
  - `cloud.offline(): boolean`、`cloud.syncMine(): void`（保持）。
  - `updateViews(): void` — 刷新依赖群体数据的视图（本任务内只刷新浮层榜单；Task 5 会追加 `renderBar()`）。
  - `sheetOpen(): boolean`。

- [ ] **Step 1: build.py 内联 identity.js**

在 `webpage/build.py` 组装区（读 `TALLY` 那几行附近），在 `TALLY = ...` 之后追加：

```python
IDENTITY = open(os.path.join(BUILD,"identity.js"), encoding="utf-8").read()
```

并把 `OUT` 模板里的脚本块：

```python
<script>
{TALLY}
{SCRIPT}
</script>
```

改为（在 `SCRIPT` 之前多内联一份 `IDENTITY`）：

```python
<script>
{TALLY}
{IDENTITY}
{SCRIPT}
</script>
```

- [ ] **Step 2: app.js 重写 `cloud` 模块**

在 `webpage/app.js` 中，用下面整段**替换**现有的 `cloud` 模块（从 `var ENV_ID = ...` 到该 IIFE 结束的 `})();`，即约第 13–78 行的 `// ---- cloud sync (CloudBase) ----` 整块）：

```javascript
  // ---- cloud sync (CloudBase)：身份 = 用户名 ----
  var ENV_ID = "plan-d0gstt7r6507aa319";
  var COLL = "votes";
  var SYNCED_KEY = "bali_synced_docid"; // 上次写入云端的 docId，用于改名/清名时删除旧档
  function sheetOpen(){ return sheet && !sheet.hasAttribute("hidden"); }

  var cloud = (function(){
    var db = null, failed = false, groupTally = null;
    function currentState(){
      return {
        name: (localStorage.getItem(K.name)||"").trim(),
        picks: votes,
        combo: localStorage.getItem(K.combo) || ""
      };
    }
    var readyP;
    if (typeof cloudbase === "undefined" || !cloudbase.init){
      failed = true; readyP = Promise.reject(new Error("no sdk"));
    } else {
      readyP = new Promise(function(resolve, reject){
        try {
          var app = cloudbase.init({ env: ENV_ID });
          var auth = app.auth({ persistence: "local" });
          auth.signInAnonymously().then(function(res){
            if (res && res.error){ reject(res.error); return; }
            db = app.database();
            resolve();
          }).catch(reject);
        } catch(e){ reject(e); }
      });
    }
    readyP.catch(function(){ failed = true; updateViews(); });

    function coll(){ return db.collection(COLL); }
    function getDoc(docId){
      return coll().doc(docId).get().then(function(res){
        var d = res && res.data;
        return Array.isArray(d) ? (d[0] || null) : (d || null);
      });
    }
    function writeSet(docId, data){
      data.updatedAt = Date.now();
      return coll().doc(docId).set(data);
    }

    var syncT = null;
    function syncMine(){
      if (failed) return;
      clearTimeout(syncT);
      syncT = setTimeout(function(){
        readyP.then(function(){
          var st = currentState();
          var newId = IdentityLib.deriveDocId(st.name);
          var syncedId = localStorage.getItem(SYNCED_KEY) || "";
          var delP = (syncedId && syncedId !== newId)
            ? coll().doc(syncedId).remove().catch(function(){})  // 改名/清名：删旧档
            : Promise.resolve();
          delP.then(function(){
            if (!newId){ localStorage.removeItem(SYNCED_KEY); refreshGroup(); return; } // 没名字：只本机
            if (syncedId !== newId){
              // 采纳并合并（换设备/撞名/首次绑定），防丢票
              getDoc(newId).then(function(existing){
                var merged = IdentityLib.mergeState(st, existing || {});
                writeSet(newId, merged).then(function(){
                  localStorage.setItem(SYNCED_KEY, newId);
                  adoptLocal(merged);
                  refreshGroup();
                }).catch(function(){});
              }).catch(function(){
                writeSet(newId, { name: st.name, picks: st.picks, combo: st.combo }).then(function(){
                  localStorage.setItem(SYNCED_KEY, newId); refreshGroup();
                }).catch(function(){});
              });
            } else {
              // 常态：覆盖自己的文档，本机为准
              writeSet(newId, { name: st.name, picks: st.picks, combo: st.combo })
                .then(function(){ refreshGroup(); }).catch(function(){});
            }
          });
        }).catch(function(){});
      }, 800);
    }

    function fetchAll(){
      return readyP.then(function(){
        return coll().limit(50).get().then(function(res){ return (res && res.data) || []; });
      });
    }
    function refreshGroup(){
      if (failed){ groupTally = null; updateViews(); return; }
      return fetchAll().then(function(docs){
        groupTally = TallyLib.computeTally(docs, ITEMS, COMBOS);
        updateViews();
      }).catch(function(){ updateViews(); });
    }
    return {
      syncMine: syncMine,
      refreshGroup: refreshGroup,
      group: function(){ return groupTally; },
      offline: function(){ return failed; }
    };
  })();

  // 把云端合并结果写回本机并重绘（换设备输同名时把先前的票“拉下来”）
  function adoptLocal(merged){
    votes = merged.picks || {};
    save();
    if (merged.combo) localStorage.setItem(K.combo, merged.combo);
    paintAll();
    if (sheetOpen()){
      var c = localStorage.getItem(K.combo);
      $$('input[name="combo"]').forEach(function(r){ r.checked = (r.value===c); });
      renderPicks();
    }
  }

  // 刷新依赖群体数据的视图（Task 5 会在此追加 renderBar()）
  function updateViews(){ if (sheetOpen()) renderSheetTally(); }
```

> ⚠️ 注意：`adoptLocal` 把 `votes` 整体重新赋值，因此 `app.js` 顶部 `var votes = getVotes();` 保持为 `var`（可重新赋值），不要改成 `const`。

- [ ] **Step 3: app.js 用缓存渲染浮层榜单（替换 refreshTally + 改文案）**

把现有的 `refreshTally` 函数（约第 191–201 行）**替换**为 `renderSheetTally`（从缓存渲染，不自拉数据）：

```javascript
  function renderSheetTally(){
    var body = $("#tallyBody");
    if (!body) return;
    if (cloud.offline()){ body.innerHTML = '<p class="tally-empty">云同步暂不可用，可用下方「一键复制」发到群里。</p>'; return; }
    var t = cloud.group();
    if (!t){ body.innerHTML = '<p class="tally-empty">加载中…</p>'; return; }
    body.innerHTML = renderTally(t);
  }
```

把 `renderTally(t)` 里的参与人数文案（约第 173 行）从：

```javascript
    var h = '<div class="tally-n">已 '+t.voterCount+' 人参与</div>';
```

改为：

```javascript
    var h = '<div class="tally-n">群 '+t.voterCount+'/6 已投</div>';
```

- [ ] **Step 4: app.js 接线（刷新按钮 / 开浮层 / 加载 + 轮询）**

把刷新按钮绑定（约第 202 行）：

```javascript
  (function(){ var rb = $("#tallyRefresh"); if (rb) rb.addEventListener("click", refreshTally); })();
```

改为：

```javascript
  (function(){ var rb = $("#tallyRefresh"); if (rb) rb.addEventListener("click", function(){ cloud.refreshGroup(); }); })();
```

把 `openSheet` 里（约第 146 行）：

```javascript
    renderPicks(); refreshTally(); sheet.removeAttribute("hidden"); document.body.style.overflow="hidden";
```

改为（先用缓存即时渲染，再拉新）：

```javascript
    renderPicks(); renderSheetTally(); cloud.refreshGroup(); sheet.removeAttribute("hidden"); document.body.style.overflow="hidden";
```

在 `app.js` 末尾 `paintAll();` **之前**追加「加载即拉 + 可见性轮询」：

```javascript
  cloud.refreshGroup();
  document.addEventListener("visibilitychange", function(){ if (document.visibilityState === "visible") cloud.refreshGroup(); });
  setInterval(function(){ if (document.visibilityState === "visible") cloud.refreshGroup(); }, 45000);
```

- [ ] **Step 5: 重新构建**

Run: `cd webpage && python3 build.py`
Expected: 无报错；`index.html` 体积略增（多内联 `identity.js`）。

- [ ] **Step 6: 冒烟验证「自定义 docId 的 set/remove」是否被平台允许（关键）**

打开 `webpage/index.html`（需联网），在 DevTools Console 观察：投票并在浮层填名字后，Network 里对 `votes` 的写入返回成功、无 `DATABASE_PERMISSION_DENIED`；到 [CloudBase 控制台](https://console.cloud.tencent.com/tcb) 云数据库看到集合 `votes` 里出现一条 `_id` 形如 `u_...` 的文档。
- ✅ 成功 → 继续 Step 7。
- ❌ 若自定义 `_id` 的 `set` 被拒（平台不允许客户端指定 `_id`）→ 启用兜底：把 `writeSet`/`getDoc`/删旧档改为「按 `name` 查找或新建」。兜底完整代码：

```javascript
    // 兜底：不指定 _id，用 name 字段查找或新建（docId 存 SYNCED_KEY 映射真实 _id）
    function getDoc(docId){ // 这里 docId 实为归一化 name 键，改查 name 字段
      return coll().where({ nameKey: docId }).limit(1).get().then(function(res){
        return (res && res.data && res.data[0]) || null;
      });
    }
    function writeSet(docId, data){
      data.updatedAt = Date.now(); data.nameKey = docId;
      var realId = localStorage.getItem("bali_realid_"+docId) || "";
      if (realId) return coll().doc(realId).update(data);
      return coll().add(data).then(function(res){
        var id = res && (res.id || res._id);
        if (id) localStorage.setItem("bali_realid_"+docId, id);
      });
    }
    // 删旧档：coll().where({nameKey: syncedId}).get() 后逐条 remove()
```
（兜底同样满足「按名字判定」；`nameKey` 即 `deriveDocId` 的输出，仍以名字为准。选用兜底后同步更新 §7.3 记录。）

- [ ] **Step 7: 手动验收「用户名即账号」**

1. **同名去重**：浏览器 A（普通窗）填名「小李」投几票；浏览器 B（隐身窗）也填名「小李」投另外几票。→ 两边浮层榜单顶部都显示 **`群 1/6 已投`**（同名算一人，不是 2）；B 的票与 A 的票**并集**出现（换设备续投、不丢票）。
2. **异名计数**：B 改名「小王」。→ 榜单变 **`群 2/6 已投`**，且原「小李」不残留第 3 条幽灵行。
3. **无名只本机**：浏览器 C（隐身）不填名投票。→ C 能投票、能一键复制，但榜单人数**不因 C 增加**。
4. **清名退出**：A 把名字清空。→ 榜单人数减一，A 那条被删。
5. **加载即拉 / 轮询**：A 关掉浮层，B 新投一票；≤45s 后（或 A 切后台再切回前台）A 打开浮层，榜单已含 B 的新票。

- [ ] **Step 8: 运行单测确认未回归**

Run: `node --test webpage/test/tally.test.js webpage/test/identity.test.js`
Expected: PASS。

- [ ] **Step 9: 提交**

```bash
git add webpage/app.js webpage/build.py webpage/index.html
git commit -m "投票优化：身份改为用户名即账号（名字派生 docId、无名只本机、采纳合并防丢票、改名/清名清档）+ 汇总加载即拉与可见性轮询"
```

---

### Task 5: 两行 bar——`你 N/14 · 群 N/6` + 群体最爱 + 状态位

**Files:**
- Modify: `webpage/build.py`（`mylist()` 的 bar DOM）
- Modify: `webpage/style.css`（`.bar` 两行布局 + 状态样式；移除死用的 `.bar-n`）
- Modify: `webpage/app.js`（新增 `renderBar`；`updateViews` 追加 `renderBar()`；`updateCount`→`renderBar`）

**Interfaces:**
- Consumes: `cloud.group()`/`cloud.offline()`（Task 4）；`decidedCount()`（Task 3）；`ITEMS`（既有全局）。
- Produces: `renderBar(): void` — 按四状态渲染底部 bar。

- [ ] **Step 1: build.py 改 bar DOM 为两行**

在 `webpage/build.py` 的 `mylist()` 中，把首行 bar 按钮：

```python
    return f'''<button type="button" class="bar" id="bar"><span class="bar-l"><span class="bar-dot"></span>我的清单 · MY LIST</span><span class="bar-n" id="barN">0</span></button>
```

改为（`{len(C.ITEMS)}` 作为初始分母占位，加载后由 `renderBar` 覆盖）：

```python
    return f'''<button type="button" class="bar" id="bar">
  <span class="bar-top"><span class="bar-l"><span class="bar-dot"></span>我的清单 ›</span><span class="bar-stat" id="barStat">你 0/{len(C.ITEMS)}</span></span>
  <span class="bar-sub" id="barSub">还没人投票 · 你可以抢先标记</span>
</button>
```

- [ ] **Step 2: style.css 改 `.bar` 为两行 + 状态样式**

把现有 `.bar` 规则（约第 254–262 行，含 `.bar-l`/`.bar-dot`/`.bar-n`）**替换**为：

```css
.bar{position:fixed;left:0;right:0;bottom:0;z-index:40;display:flex;flex-direction:column;gap:5px;
  max-width:var(--maxw);margin:0 auto;padding:12px 22px calc(12px + env(safe-area-inset-bottom));
  border:0;border-top:1.5px solid var(--line-strong);background:var(--ground);color:var(--ink);
  text-align:left;box-shadow:0 -8px 24px rgba(27,24,21,.06)}
.bar:active{background:var(--ground-2)}
.bar-top{display:flex;align-items:center;justify-content:space-between;gap:12px;width:100%}
.bar-l{display:flex;align-items:center;gap:9px;font-size:11px;letter-spacing:.16em;text-transform:uppercase;font-weight:600}
.bar-dot{width:7px;height:7px;border-radius:50%;background:var(--pine);flex:0 0 auto}
.bar-stat{font-family:var(--font-mono);font-size:12px;font-weight:700;letter-spacing:.02em;color:var(--brass);white-space:nowrap}
.bar-sub{width:100%;font-size:11.5px;letter-spacing:.01em;color:var(--ink-soft);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bar-sub.warn{color:var(--brass)}
```

- [ ] **Step 3: app.js 新增 `renderBar` 并接入 `updateViews`**

在 `webpage/app.js` 中，`updateViews` 函数体改为同时刷新 bar：

```javascript
  function updateViews(){ renderBar(); if (sheetOpen()) renderSheetTally(); }
```

在 `renderSheetTally` 附近新增 `renderBar`：

```javascript
  function shortZh(zh){ return (String(zh).split("·")[0] || "").trim(); }
  function renderBar(){
    var statEl = $("#barStat"), subEl = $("#barSub");
    if (!statEl || !subEl) return;
    var total = ITEMS.length, decided = decidedCount();
    var name = (localStorage.getItem(K.name)||"").trim();
    if (cloud.offline()){
      statEl.textContent = "你 " + decided + "/" + total;
      subEl.textContent = "云同步暂不可用 · 可用「一键复制」发群里";
      subEl.className = "bar-sub warn"; return;
    }
    var g = cloud.group();
    var voters = g ? g.voterCount : 0;
    statEl.textContent = "你 " + decided + "/" + total + " · 群 " + voters + "/6";
    if (decided > 0 && !name){
      subEl.textContent = "⚠ 填个名字才能加入大家的汇总 →";
      subEl.className = "bar-sub warn";
    } else if (!g || !g.voterCount){
      subEl.textContent = "还没人投票 · 你可以抢先标记";
      subEl.className = "bar-sub";
    } else {
      var top = g.spots.slice(0,3).map(function(s){ return s.id + " " + shortZh(s.zh); });
      subEl.textContent = "群体最爱 · " + top.join("   ");
      subEl.className = "bar-sub";
    }
  }
```

- [ ] **Step 4: app.js 用 `renderBar` 取代旧的 `updateCount`/`#barN`**

删除旧的 `updateCount` 函数（约第 90 行 `function updateCount(){ var n=$("#barN"); if(n) n.textContent = pickCount(); }`）。

把 `paintAll`（约第 87 行）里的 `updateCount()` 改为 `renderBar()`：

```javascript
  function paintAll(){ $$(".spot").forEach(paintSpot); renderBar(); }
```

把投票点击处理里（约第 98 行）的 `updateCount();` 改为 `renderBar();`：

```javascript
      save(); cloud.syncMine(); paintSpot(art); renderBar(); if(!$("#sheet").hasAttribute("hidden")) renderPicks();
```

> 说明：`pickCount()` 仍保留（`#resetBtn` 用它判断是否需要确认清空）；只删 `updateCount`。

- [ ] **Step 5: 重新构建**

Run: `cd webpage && python3 build.py`
Expected: 无报错。

- [ ] **Step 6: 手动验收四状态**

打开 `webpage/index.html`：
- **还没人投票**：全新会话，bar 第二行「还没人投票 · 你可以抢先标记」，第一行 `你 0/14 · 群 0/6`。
- **有票没名字**：投几票、不填名 → 第二行变 `⚠ 填个名字才能加入大家的汇总 →`（brass 色），第一行 `你 3/14 · 群 N/6`。
- **常态**：填名后（或已有他人投票）→ 第二行 `群体最爱 · A1 乌布   B1 佩尼达   ...`（Top3）。
- **云同步不可用**：断网/无 SDK 打开本地文件 → 第一行仅 `你 N/14`，第二行降级文案；投票、清单、一键复制仍可用。
- bar 两行不遮挡页脚内容（滚到底检查 `footer` 留白足够）。

- [ ] **Step 7: 运行单测确认未回归**

Run: `node --test webpage/test/tally.test.js webpage/test/identity.test.js`
Expected: PASS。

- [ ] **Step 8: 提交**

```bash
git add webpage/build.py webpage/style.css webpage/app.js webpage/index.html
git commit -m "投票优化：底部 bar 升级为两行状态台（你 N/14 · 群 N/6 + 群体最爱/填名提醒/降级四状态）"
```

---

### Task 6: 首次投票 → 轻提示填名字（一次性 toast）

**Files:**
- Modify: `webpage/app.js`（投票处理加首投判定；新增可点击 nudge toast）

**Interfaces:**
- Consumes: `decidedCount()`（Task 3）；`openSheet()`（既有）；`toast` 元素与 `#nameIn`（既有）。

- [ ] **Step 1: app.js 投票处理加「首投」判定**

把投票点击处理块（约第 95–100 行，`var vb = e.target.closest(".v");` 起）改为在改动前记录是否为「零决定」，并在改动后触发提示：

```javascript
    var vb = e.target.closest(".v");
    if(vb){
      var art = vb.closest(".spot"), id = art.getAttribute("data-id"), v = vb.getAttribute("data-v");
      var wasZero = decidedCount()===0;
      if(votes[id]===v){ delete votes[id]; } else { votes[id]=v; }
      save(); cloud.syncMine(); paintSpot(art); renderBar(); if(!$("#sheet").hasAttribute("hidden")) renderPicks();
      maybeNudgeName(wasZero);
      return;
    }
```

- [ ] **Step 2: app.js 新增 `maybeNudgeName` + 可点击 nudge toast**

在 `toast` 函数（约第 243 行）附近新增：

```javascript
  var NUDGE_KEY = "bali_nudged";
  function maybeNudgeName(wasZero){
    if (!wasZero) return;                                   // 只在第一次“从 0 到有”时
    if (localStorage.getItem(NUDGE_KEY)) return;            // 只提示一次
    if ((localStorage.getItem(K.name)||"").trim()) return;  // 已有名字则不提示
    localStorage.setItem(NUDGE_KEY, "1");
    nudgeToast("给自己起个名字，才能加入大家的汇总 →");
  }
  var nudgeT;
  function nudgeToast(msg){
    toEl.textContent = msg;
    toEl.className = "toast nudge";
    toEl.removeAttribute("hidden");
    requestAnimationFrame(function(){ toEl.classList.add("show"); });
    clearTimeout(nudgeT);
    nudgeT = setTimeout(function(){ hideToast(); }, 4200);
    toEl.onclick = function(){ hideToast(); openSheet(); setTimeout(function(){ var n=$("#nameIn"); if(n) n.focus(); }, 120); };
  }
  function hideToast(){ toEl.classList.remove("show"); toEl.onclick=null;
    setTimeout(function(){ toEl.setAttribute("hidden",""); toEl.className="toast"; }, 220); }
```

> 说明：复用既有 `#toast` 元素与 `toEl` 变量（约第 242 行 `var toEl=$("#toast"), toT;`）。普通 `toast()` 不设 `onclick`；`nudgeToast` 额外挂点击打开浮层并聚焦名字框。

- [ ] **Step 3: style.css 给可点击 nudge toast 一点可点感**

在 toast 区块（约第 310 行 `.toast[hidden]` 后）追加：

```css
.toast.nudge{pointer-events:auto;cursor:pointer;background:var(--pine);color:#F6F3EA}
```

- [ ] **Step 4: 重新构建**

Run: `cd webpage && python3 build.py`
Expected: 无报错。

- [ ] **Step 5: 手动验收**

打开 `webpage/index.html`（清掉 localStorage 或用新隐身窗）：
- 第一次点任意 必去/可去/略过 且未填名 → 底部弹出**绿色可点** toast「给自己起个名字，才能加入大家的汇总 →」；点它 → 打开「我的清单」浮层并聚焦名字框。
- 再投票**不再**弹（`bali_nudged` 已置）。
- 若一开始就先填了名字，投票时**不**弹。

- [ ] **Step 6: 运行单测确认未回归**

Run: `node --test webpage/test/tally.test.js webpage/test/identity.test.js`
Expected: PASS。

- [ ] **Step 7: 提交**

```bash
git add webpage/app.js webpage/style.css webpage/index.html
git commit -m "投票优化：首次投票且未填名时一次性轻提示填名字（可点击打开浮层）"
```

---

### Task 7: 整合验收 + 上线

**Files:**
- 无新代码；整页构建与验收。

- [ ] **Step 1: 全量构建**

Run: `cd webpage && python3 build.py`
Expected: `wrote index.html : ... KB (media keys: ..., videos: ...)` 与 `wrote images/ : ... files`，无报错。

- [ ] **Step 2: 跑全部单测**

Run: `node --test webpage/test/tally.test.js webpage/test/identity.test.js`
Expected: 全 PASS。

- [ ] **Step 3: 对照验收清单逐条过（对应 spec §11）**

打开 `webpage/index.html` + 联网，逐条确认：
- [ ] 「略过」灰章 + 计入 `你 N/14`，不影响榜单分数。
- [ ] bar 两行、四状态正确。
- [ ] 加载即显示群体最爱与 `群 N/6`；≤45s 轮询到他人新票；切后台停、切回立即刷新。
- [ ] 榜单顶部 `群 N/6 已投`。
- [ ] 首投未填名弹一次提示、点击聚焦名字框、只弹一次。
- [ ] 同名同一条、换设备输同名拉回旧票不丢；无名不进汇总；改名/清名不留幽灵行。
- [ ] 断网/无 SDK 全降级不报错。

- [ ] **Step 4: 正式发人前清空测试脏数据**

到 [CloudBase 控制台](https://console.cloud.tencent.com/tcb) → 云数据库 → 集合 `votes` → 清空测试期造的文档（使 `群 N/6` 从干净起点开始）。

- [ ] **Step 5: 部署上线（仅 index.html）**

Run: `cd webpage && tcb hosting deploy index.html index.html -e plan-d0gstt7r6507aa319`
Expected: 部署成功；数分钟后 https://plan-d0gstt7r6507aa319-1451599494.tcloudbaseapp.com 生效。
（`identity.js`/`tally.js` 均已内联进 `index.html`，**无需**单独部署；`cloudbase.js` 未变，无需重部。）

- [ ] **Step 6: 线上冒烟**

手机/浏览器打开正式链接：投票→填名→看 `群 N/6` 与群体最爱刷新正常；换一个浏览器输同名验证同一条。

---

## Self-Review

**Spec coverage（逐节对照）：**
- §3 投票模型（略过/skip/灰章/进度分母）→ Task 3（+ Task 2 回归）。✅
- §4 两行 bar 四状态 → Task 5。✅
- §5 实时汇总加载即拉 + 轮询 + `群 N/6 已投` → Task 4。✅
- §6 首投提示填名 → Task 6。✅
- §7 身份=用户名（派生 docId、gating、采纳合并、改名/清名清档、匿名仅写门票、规则不变）→ Task 4；纯逻辑 → Task 1。✅
- §7.3 平台可行性 + 兜底 → Task 4 Step 6。✅
- §9 hero「6 人同行」→ Task 3 Step 2。✅
- §10 文件与测试（identity 单测、tally skip 回归、构建、仅部署 index.html）→ Task 1/2/7。✅
- §11 验收 → Task 7 Step 3。✅

**Placeholder scan:** 无 TBD/TODO；兜底代码为「验证失败时启用」的完整实分支，非占位。✅

**Type consistency:** `deriveDocId`/`mergeState`/`mergePicks`/`normalizeName` 命名在 Task 1 定义、Task 4 消费一致；`decidedCount`（T3）→ `renderBar`（T5）一致；`cloud.group()`/`cloud.refreshGroup()`/`updateViews()`/`sheetOpen()`/`renderSheetTally()`/`renderBar()`/`adoptLocal()` 跨 Task 4/5 命名一致；`updateViews` 在 T4 只刷新浮层、T5 追加 `renderBar()` —— 已在 T5 Step 3 明确改函数体，非重复定义。✅
