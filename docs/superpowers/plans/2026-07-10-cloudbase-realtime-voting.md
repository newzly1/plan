# CloudBase 云数据库实时汇总投票 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 6 人在同一个网页上投票，投票直接写进腾讯云 CloudBase 云数据库，页面实时显示合并后的加权排行，彻底告别复制粘贴人工汇总。

**Architecture:** 附加式改造。保留现有 `localStorage` 本地投票、卡片高亮、「一键复制」兜底；叠加一个云端连接层（匿名登录 + 数据库读写）与一个「实时汇总」面板。汇总算分抽成纯函数 `tally.js`，浏览器与 Node 测试共用。CloudBase Web SDK 以同源静态文件随站点部署，不依赖第三方 CDN 运行。

**Tech Stack:** 原生 ES5 JS（`app.js` 现有 IIFE 风格）、CloudBase JS SDK v1.7.2（UMD 全局 `cloudbase`）、Python 标准库 `build.py`、`node:test`（零依赖单测，Node v24）、CloudBase 云数据库 + 匿名登录 + 静态托管。

设计依据：`docs/superpowers/specs/2026-07-10-cloudbase-realtime-voting-design.md`

## Global Constraints

- **不引入构建依赖**：`build.py` 只用 Python 标准库。
- **联网工具**：装 npm 包一律加 `--registry=https://registry.npmmirror.com`；`urllib` 会卡，脚本联网用 `curl`（走本地代理）。
- **测试**：用零依赖 `node --test`（本机 Node v24.15.0，`node:test` 可用），不装任何测试框架。
- **JS 风格**：沿用 `app.js` 的 ES5 IIFE 风格（`var`、`function`，不用箭头函数/`let`/`const`），保证老浏览器兼容。
- **CloudBase 常量**：环境 id `plan-d0gstt7r6507aa319`；集合名 `votes`；托管域名 `plan-d0gstt7r6507aa319-1451599494.tcloudbaseapp.com`。
- **SDK**：`https://static.cloudbase.net/cloudbase-js-sdk/1.7.2/cloudbase.full.js`（UMD 全局 `cloudbase`，约 330 KB），vendored 到 `webpage/cloudbase.js` 同源部署。
- **保留兜底**：现有本地投票与「一键复制」不删，SDK/网络失败时静默降级。
- **部署命令**：`tcb hosting deploy <local> <remote> -e plan-d0gstt7r6507aa319`。
- **Git**：提交信息用中文；作者沿用仓库局部配置 `zly1`；先在当前 `master` 分支提交（本仓库默认分支即 master）。

---

### Task 1: 纯汇总算法 `tally.js`（TDD）

抽出与网络/DOM 无关的加权算分逻辑，浏览器与 Node 测试共用。这是全计划唯一能纯单测的单元，先做。

**Files:**
- Create: `webpage/tally.js`
- Test: `webpage/test/tally.test.js`

**Interfaces:**
- Produces: `computeTally(docs, items, combos)` — 纯函数。
  - `docs`: `Array<{ name?, picks?: {[spotId]: "must"|"maybe"}, combo?: string }>`
  - `items`: `Array<{ id: string, zh: string }>`（来自 `ITEMS_JS`）
  - `combos`: `{ [no: string]: string }`（来自 `COMBOS_JS`，值是「组N 名称」）
  - 返回 `{ voterCount: number, spots: Array<{id, zh, must, maybe, score}>, combos: Array<{no, label, count}> }`
  - 计分：`score = must*2 + maybe*1`；`spots` 按 `score` 降序、`must` 降序、`id` 升序；只含有票的景点。`combos` 按 `count` 降序、`no` 升序；只含有票的线路。
- 双导出：Node 下 `module.exports = { computeTally }`；浏览器下挂 `self.TallyLib = { computeTally }`。

- [ ] **Step 1: 写失败测试**

Create `webpage/test/tally.test.js`:

```js
"use strict";
const test = require("node:test");
const assert = require("node:assert");
const { computeTally } = require("../tally.js");

const ITEMS = [
  { id: "A1", zh: "巴厘岛门户" },
  { id: "B2", zh: "乌布梯田" },
  { id: "C3", zh: "蓝梦岛" }
];
const COMBOS = { "1": "组1 环岛", "2": "组2 东巴厘" };

test("空输入：0 人参与，列表为空", () => {
  const r = computeTally([], ITEMS, COMBOS);
  assert.strictEqual(r.voterCount, 0);
  assert.deepStrictEqual(r.spots, []);
  assert.deepStrictEqual(r.combos, []);
});

test("加权计分 must=2 maybe=1，按分数降序、必去数降序", () => {
  const docs = [
    { picks: { A1: "must", B2: "maybe" }, combo: "1" },
    { picks: { A1: "must", B2: "must" }, combo: "1" },
    { picks: { B2: "maybe", C3: "maybe" }, combo: "2" }
  ];
  const r = computeTally(docs, ITEMS, COMBOS);
  assert.strictEqual(r.voterCount, 3);
  assert.deepStrictEqual(r.spots, [
    { id: "A1", zh: "巴厘岛门户", must: 2, maybe: 0, score: 4 },
    { id: "B2", zh: "乌布梯田", must: 1, maybe: 2, score: 4 },
    { id: "C3", zh: "蓝梦岛", must: 0, maybe: 1, score: 1 }
  ]);
  assert.deepStrictEqual(r.combos, [
    { no: "1", label: "组1 环岛", count: 2 },
    { no: "2", label: "组2 东巴厘", count: 1 }
  ]);
});

test("忽略非法票值，未知景点用 id 兜底名", () => {
  const r = computeTally([{ picks: { X9: "must", A1: "weird" } }], ITEMS, COMBOS);
  assert.strictEqual(r.voterCount, 1);
  assert.deepStrictEqual(r.spots, [{ id: "X9", zh: "X9", must: 1, maybe: 0, score: 2 }]);
  assert.deepStrictEqual(r.combos, []);
});

test("组合票数相同按线路号升序", () => {
  const docs = [{ combo: "2" }, { combo: "1" }];
  const r = computeTally(docs, ITEMS, COMBOS);
  assert.deepStrictEqual(r.combos, [
    { no: "1", label: "组1 环岛", count: 1 },
    { no: "2", label: "组2 东巴厘", count: 1 }
  ]);
});
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `node --test webpage/test/tally.test.js`
Expected: FAIL — `Cannot find module '../tally.js'`。

- [ ] **Step 3: 写实现**

Create `webpage/tally.js`:

```js
// webpage/tally.js — 纯投票汇总算法，浏览器（build 内联）与 Node 测试共用。
(function (root) {
  "use strict";
  function has(o, k) { return Object.prototype.hasOwnProperty.call(o, k); }

  function computeTally(docs, items, combos) {
    docs = docs || []; items = items || []; combos = combos || {};
    var zh = {}, i;
    for (i = 0; i < items.length; i++) zh[items[i].id] = items[i].zh;

    var acc = {}, comboCount = {}, voterCount = 0, d, id, cno;
    for (d = 0; d < docs.length; d++) {
      var doc = docs[d] || {};
      voterCount++;
      var picks = doc.picks || {};
      for (id in picks) {
        if (!has(picks, id)) continue;
        var v = picks[id];
        if (v !== "must" && v !== "maybe") continue;
        if (!acc[id]) acc[id] = { must: 0, maybe: 0 };
        acc[id][v]++;
      }
      if (doc.combo != null && doc.combo !== "") {
        var c = String(doc.combo);
        comboCount[c] = (comboCount[c] || 0) + 1;
      }
    }

    var spots = [];
    for (id in acc) {
      if (!has(acc, id)) continue;
      var m = acc[id];
      spots.push({ id: id, zh: zh[id] || id, must: m.must, maybe: m.maybe, score: m.must * 2 + m.maybe });
    }
    spots.sort(function (a, b) {
      return b.score - a.score || b.must - a.must || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0);
    });

    var comboList = [];
    for (cno in comboCount) {
      if (!has(comboCount, cno)) continue;
      comboList.push({ no: cno, label: combos[cno] || ("组" + cno), count: comboCount[cno] });
    }
    comboList.sort(function (a, b) {
      return b.count - a.count || (a.no < b.no ? -1 : a.no > b.no ? 1 : 0);
    });

    return { voterCount: voterCount, spots: spots, combos: comboList };
  }

  if (typeof module !== "undefined" && module.exports) module.exports = { computeTally: computeTally };
  else root.TallyLib = { computeTally: computeTally };
})(typeof self !== "undefined" ? self : this);
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `node --test webpage/test/tally.test.js`
Expected: PASS — 4 tests pass, 0 fail。

- [ ] **Step 5: 提交**

```bash
git add webpage/tally.js webpage/test/tally.test.js
git commit -m "投票汇总：新增纯函数 tally.js（加权计分/排序）+ node:test 单测"
```

---

### Task 2: `app.js` 云端连接层 + 汇总渲染 + 同步挂钩

在现有 IIFE 内加：云连接模块（匿名登录、防抖 upsert、拉全量）、汇总面板渲染、三处投票挂钩。引用 Task 1 的 `TallyLib`、运行时全局 `cloudbase`、Task 3 会加的 DOM（`#tallyBody` / `#tallyRefresh` / `#tally`）。本任务只改 JS，用 `node --check` 语法校验 + 复跑 Task 1 单测保证不回归。

**Files:**
- Modify: `webpage/app.js`（现有行号：投票挂钩 `:30-31`；改名 `:85`；改组合 `:87`；`openSheet` `:75-80`）

**Interfaces:**
- Consumes: `TallyLib.computeTally`（Task 1）；全局 `cloudbase`（Task 3 同源脚本）；`votes`/`sheet`/`esc`/`ITEMS`/`COMBOS`（现有 `app.js` 作用域内已定义）。
- Produces: 全局函数 `refreshTally()`；`cloud.syncMine()` / `cloud.fetchAll()` / `cloud.offline()`。

- [ ] **Step 1: 加云端连接模块**

在 `app.js` 中 `function save(){...}`（现第 11 行）之后插入：

```js
  // ---- cloud sync (CloudBase) ----
  var ENV_ID = "plan-d0gstt7r6507aa319";
  var COLL = "votes";
  var DOCID_KEY = "bali_docid";
  var cloud = (function(){
    var db = null, docId = null, failed = false;
    function currentState(){
      return {
        name: (localStorage.getItem(K.name)||"").trim(),
        picks: votes,
        combo: localStorage.getItem(K.combo) || "",
        updatedAt: Date.now()
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
          auth.anonymousAuthProvider().signIn().then(function(){
            db = app.database();
            docId = localStorage.getItem(DOCID_KEY) || null;
            resolve();
          }).catch(reject);
        } catch(e){ reject(e); }
      });
    }
    readyP.catch(function(){ failed = true; });

    function addNew(data, cb){
      db.collection(COLL).add(data).then(function(res){
        docId = (res && (res.id || res._id)) || null;
        if (docId) localStorage.setItem(DOCID_KEY, docId);
        if (cb) cb();
      }).catch(function(){});
    }
    var syncT = null;
    function syncMine(){
      if (failed) return;
      clearTimeout(syncT);
      syncT = setTimeout(function(){
        readyP.then(function(){
          var data = currentState();
          function done(){ if (sheet && !sheet.hasAttribute("hidden")) refreshTally(); }
          if (docId){
            db.collection(COLL).doc(docId).update(data).then(done).catch(function(){
              docId = null; localStorage.removeItem(DOCID_KEY); addNew(data, done);
            });
          } else { addNew(data, done); }
        }).catch(function(){});
      }, 800);
    }
    function fetchAll(){
      return readyP.then(function(){
        return db.collection(COLL).limit(50).get().then(function(res){ return (res && res.data) || []; });
      });
    }
    return { syncMine: syncMine, fetchAll: fetchAll, offline: function(){ return failed; } };
  })();
```

- [ ] **Step 2: 加汇总渲染 + 刷新**

在 `app.js` 的 `function esc(...)`（现第 102 行）之后插入（用函数声明，保证被上面 `syncMine`/后面 `openSheet` 引用时已提升）：

```js
  // ---- live tally ----
  function renderTally(t){
    if (!t.voterCount) return '<p class="tally-empty">还没有人投票。你投的票会实时汇总到这里。</p>';
    var h = '<div class="tally-n">已 '+t.voterCount+' 人参与</div>';
    if (t.spots.length){
      h += '<ol class="tally-rank">';
      t.spots.forEach(function(s){
        h += '<li><span class="tr-id">'+esc(s.id)+'</span><span class="tr-zh">'+esc(s.zh)+'</span>'
           + '<span class="tr-score">'+s.score+' 分</span>'
           + '<span class="tr-sub">必去'+s.must+' · 可去'+s.maybe+'</span></li>';
      });
      h += '</ol>';
    }
    if (t.combos.length){
      h += '<div class="tally-combo"><div class="tc-h">组合线路</div>';
      t.combos.forEach(function(c){ h += '<div class="tc-row"><span>'+esc(c.label)+'</span><b>'+c.count+' 票</b></div>'; });
      h += '</div>';
    }
    return h;
  }
  function refreshTally(){
    var body = $("#tallyBody");
    if (!body) return;
    if (cloud.offline()){ body.innerHTML = '<p class="tally-empty">云同步暂不可用，可用下方「一键复制」发到群里。</p>'; return; }
    body.innerHTML = '<p class="tally-empty">加载中…</p>';
    cloud.fetchAll().then(function(docs){
      body.innerHTML = renderTally(TallyLib.computeTally(docs, ITEMS, COMBOS));
    }).catch(function(){
      body.innerHTML = '<p class="tally-empty">暂时加载不到，稍后点「刷新」。</p>';
    });
  }
```

- [ ] **Step 3: 挂三处同步 + 打开面板刷新 + 刷新按钮**

四处小改（保留原有语句，追加调用）：

1. 投票点击（现第 31 行 `save(); paintSpot(art); ...`）——在该行 `save();` 后追加 `cloud.syncMine();`：

```js
      if(votes[id]===v){ delete votes[id]; } else { votes[id]=v; }
      save(); cloud.syncMine(); paintSpot(art); updateCount(); if(!$("#sheet").hasAttribute("hidden")) renderPicks();
```

2. 改名（现第 85 行）：

```js
  $("#nameIn").addEventListener("input", function(){ localStorage.setItem(K.name, this.value); cloud.syncMine(); });
```

3. 改组合线路（现第 87 行）：

```js
    r.addEventListener("change", function(){ if(r.checked){ localStorage.setItem(K.combo, r.value); cloud.syncMine(); } });
```

4. `openSheet`（现第 79 行 `renderPicks(); sheet.removeAttribute...`）——在 `renderPicks();` 后追加 `refreshTally();`：

```js
    renderPicks(); refreshTally(); sheet.removeAttribute("hidden"); document.body.style.overflow="hidden";
```

5. 在 Step 2 插入的 `refreshTally` 之后，加刷新按钮监听：

```js
  (function(){ var rb = $("#tallyRefresh"); if (rb) rb.addEventListener("click", refreshTally); })();
```

- [ ] **Step 4: 语法校验 + 单测不回归**

`app.js` 内的 `/*__ITEMS__*/` / `/*__COMBOS__*/` 是合法注释，可直接 `node --check`：

Run: `node --check webpage/app.js`
Expected: 无输出（语法通过）。

Run: `node --test webpage/test/tally.test.js`
Expected: PASS（Task 1 单测仍全绿）。

- [ ] **Step 5: 提交**

```bash
git add webpage/app.js
git commit -m "投票云同步：app.js 加匿名登录连接层、实时汇总渲染与三处同步挂钩（失败静默降级）"
```

---

### Task 3: 构建集成 —— vendored SDK + `build.py` DOM/脚本 + 样式 + 本地冒烟

把 SDK 下载进仓库、`build.py` 注入面板 DOM 与脚本、加样式，重建后本地打开验证：离线时优雅降级、现有投票不受影响。这是第一个可在浏览器里验证的交付物。

**Files:**
- Create: `webpage/cloudbase.js`（vendored，curl 下载）
- Modify: `webpage/build.py`（`mylist()` 加面板 DOM；组装处内联 `tally.js`、加 `<script src="cloudbase.js">`）
- Modify: `webpage/style.css`（`.tally` 系列样式，追加到文件末尾）

**Interfaces:**
- Consumes: `webpage/tally.js`（Task 1）、改后的 `webpage/app.js`（Task 2）。
- Produces: `webpage/index.html` 中含 `<script src="cloudbase.js"></script>`、内联的 `TallyLib` 与新增 `#tally`/`#tallyBody`/`#tallyRefresh` DOM。

- [ ] **Step 1: 下载 vendored SDK 并校验**

Run（走本地代理，遵循「urllib 会卡，用 curl」）:

```bash
curl -sSL -m 60 -o webpage/cloudbase.js \
  "https://static.cloudbase.net/cloudbase-js-sdk/1.7.2/cloudbase.full.js"
wc -c webpage/cloudbase.js
grep -c "signInAnonymously" webpage/cloudbase.js
```

Expected: 文件约 330000 字节（`wc -c` 输出 > 300000）；`grep -c` ≥ 1（含匿名登录）。
若下载失败（0 字节/超时），备用镜像：`https://cdn.jsdelivr.net/npm/@cloudbase/js-sdk@1.7.2/dist/cloudbase.full.js`；下载后仍按上面两条校验（字节数 > 300000、含 `signInAnonymously`），且用浏览器打开一张只含 `<script src="cloudbase.js"></script>` 的测试页确认 `window.cloudbase && cloudbase.init` 存在。

- [ ] **Step 2: `build.py` 注入面板 DOM**

在 `webpage/build.py` 的 `mylist()` 里，把这一行（现第 235 行）：

```python
    <div class="picks" id="picks"></div>
```

替换为：

```python
    <div class="picks" id="picks"></div>
    <div class="tally" id="tally">
      <div class="tally-head"><b>大家的选择 · 实时汇总</b><button type="button" class="tally-refresh" id="tallyRefresh">刷新</button></div>
      <div class="tally-body" id="tallyBody"><p class="tally-empty">加载中…</p></div>
    </div>
```

- [ ] **Step 3: `build.py` 内联 tally.js + 引 SDK 脚本**

在 `webpage/build.py` 组装段，把（现第 252-253 行）：

```python
SCRIPT = open(os.path.join(BUILD,"app.js"), encoding="utf-8").read()
SCRIPT = SCRIPT.replace("/*__ITEMS__*/", ITEMS_JS).replace("/*__COMBOS__*/", COMBOS_JS)
```

改为：

```python
TALLY = open(os.path.join(BUILD,"tally.js"), encoding="utf-8").read()
SCRIPT = open(os.path.join(BUILD,"app.js"), encoding="utf-8").read()
SCRIPT = SCRIPT.replace("/*__ITEMS__*/", ITEMS_JS).replace("/*__COMBOS__*/", COMBOS_JS)
```

再把 OUT 模板里的（现第 267-269 行）：

```python
<script>
{SCRIPT}
</script>
```

改为（先加载同源 SDK，再内联 tally.js，最后内联 app.js）：

```python
<script src="cloudbase.js"></script>
<script>
{TALLY}
{SCRIPT}
</script>
```

- [ ] **Step 4: `style.css` 加面板样式**

在 `webpage/style.css` 末尾追加（配色沿用现有变量，若变量名不同则改成对应值）：

```css
/* ---- live tally 实时汇总 ---- */
.tally{margin:14px 0 4px;padding-top:12px;border-top:1px solid rgba(128,128,128,.25)}
.tally-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px}
.tally-head b{font-size:15px}
.tally-refresh{font:inherit;font-size:13px;padding:4px 12px;border:1px solid rgba(128,128,128,.4);border-radius:999px;background:transparent;color:inherit;cursor:pointer}
.tally-refresh:active{opacity:.6}
.tally-empty{font-size:13px;opacity:.7;margin:6px 0}
.tally-n{font-size:13px;opacity:.75;margin-bottom:8px}
.tally-rank{list-style:none;margin:0 0 10px;padding:0;counter-reset:tr}
.tally-rank li{counter-increment:tr;display:grid;grid-template-columns:auto auto 1fr auto;align-items:baseline;gap:8px;padding:6px 0;border-bottom:1px dashed rgba(128,128,128,.2)}
.tally-rank li::before{content:counter(tr);font-weight:700;opacity:.5;min-width:1.4em}
.tr-id{font-weight:700;font-size:13px;opacity:.8}
.tr-zh{font-size:14px}
.tr-score{font-weight:700}
.tr-sub{font-size:12px;opacity:.6;text-align:right}
.tally-combo .tc-h{font-size:13px;opacity:.75;margin:4px 0 6px}
.tc-row{display:flex;justify-content:space-between;font-size:13px;padding:3px 0}
```

- [ ] **Step 5: 重建并校验产物**

Run:

```bash
cd webpage && python3 build.py
```

Expected: 打印 `wrote index.html : ... KB` 与 `wrote images/ : ... files`，无异常。

Run（校验注入到位）:

```bash
grep -c 'src="cloudbase.js"' webpage/index.html
grep -c 'TallyLib' webpage/index.html
grep -c 'id="tallyBody"' webpage/index.html
```

Expected: 三条均 ≥ 1。

- [ ] **Step 6: 浏览器冒烟（离线优雅降级）**

在浏览器打开本地 `webpage/index.html`（`cloudbase.js` 同目录会被加载；匿名登录因未配控制台/本地环境会失败）。用 Playwright MCP 或手动确认：
- 页面无致命 JS 报错，正常渲染。
- 点几个景点「必去/可去」高亮照常、「我的清单」计数照常。
- 打开「我的清单」→ 出现「大家的选择 · 实时汇总」区块，内容为 `云同步暂不可用，可用下方「一键复制」发到群里。`（`cloud.offline()===true` 的降级文案）。
- 「一键复制」仍能复制。

（用 Playwright：`browser_navigate` 到 `file:///.../webpage/index.html` → `browser_console_messages` 查无 error → `browser_click` 投票与打开清单 → `browser_snapshot` 确认降级文案。）

- [ ] **Step 7: 提交**

```bash
git add webpage/cloudbase.js webpage/build.py webpage/style.css webpage/index.html webpage/images
git commit -m "投票实时汇总：vendored CloudBase SDK、build 注入面板与脚本、样式，重建产物"
```

---

### Task 4: CloudBase 控制台一次性配置 + 部署 + 双端真机验证

代码就绪后，开通云端能力并上线，用两个浏览器会话验证真实合并与安全规则。控制台四步需用户在腾讯云操作，其余由 CLI/自动化完成。

**Files:**
- 无代码改动（配置 + 部署 + 验证）。

- [ ] **Step 1: 用户在 CloudBase 控制台完成四步配置**

给用户这份清单（控制台 https://console.cloud.tencent.com/tcb ，环境 `plan-d0gstt7r6507aa319`）：
1. **开启匿名登录**：左侧「身份与授权」→「登录方式/登录授权」→ 打开「匿名登录」。
2. **建集合**：「云数据库」→「集合管理」→ 新建集合，名称填 `votes`。
3. **设安全规则**：选中 `votes` →「权限设置」→「自定义安全规则」，粘贴：
   ```json
   { "read": true, "write": "doc._openid == auth.openid" }
   ```
   （所有人可读用于汇总；仅本人可写自己那条。若控制台提示 `auth.openid` 不适用于匿名身份，改用 `auth.uid == doc._openid` 并在 Step 4 回归验证。）
4. **加 Web 安全域名**：「环境」→「安全配置」→「Web 安全域名」，加入 `plan-d0gstt7r6507aa319-1451599494.tcloudbaseapp.com`（否则浏览器端 SDK 认证被拒）。

等用户确认四步完成后再继续。

- [ ] **Step 2: 部署 SDK 与页面**

Run（先传 SDK，再传页面，避免页面一度引用不存在的脚本）:

```bash
cd webpage
tcb hosting deploy cloudbase.js cloudbase.js -e plan-d0gstt7r6507aa319
tcb hosting deploy index.html index.html -e plan-d0gstt7r6507aa319
```

Expected: 两条均提示部署成功（CDN 数分钟内刷新）。

- [ ] **Step 3: 双端真实汇总验证**

在线址 `https://plan-d0gstt7r6507aa319-1451599494.tcloudbaseapp.com`。用两个独立会话（两台设备 / 一个正常一个隐身窗，或 Playwright 两个 context）：
- 会话 A：填名字「甲」，标 A1=必去、B2=可去，选组合线路 1。
- 会话 B：填名字「乙」，标 A1=必去、C…=可去，选组合线路 2。
- 各自打开「我的清单」点「刷新」（或投票后自动刷新）：应看到「已 2 人参与」，A1 排在前列、分数按 `must*2+maybe*1` 正确，组合线路 1、2 各 1 票。

Expected: 两端都能看到彼此的票合并后的排行，数字与手算一致。

- [ ] **Step 4: 安全规则验证（防改别人票）**

在会话 A 的浏览器控制台执行（`OTHER_ID` 用会话 B 的文档 id，可在数据库控制台或 B 的 `localStorage.bali_docid` 里看到）:

```js
const app = cloudbase.init({ env: "plan-d0gstt7r6507aa319" });
await app.auth({ persistence: "local" }).anonymousAuthProvider().signIn();
app.database().collection("votes").doc("OTHER_ID").update({ name: "hacked" })
  .then(r => console.log("BAD: 竟然改成功了", r))
  .catch(e => console.log("OK: 被安全规则拦下", e && e.code));
```

Expected: 打印 `OK: 被安全规则拦下`（权限错误），别人那条不被篡改。

- [ ] **Step 5: 断网降级复验**

会话 A 断网后：投票仍能点、「一键复制」仍可用、汇总区显示降级文案、控制台无未捕获异常。恢复网络后点「刷新」恢复正常。

（本任务无提交；如验证中发现问题回到对应 Task 修复。）

---

### Task 5: 更新文档（README + CLAUDE.md）

把新增的云数据库依赖、控制台配置、部署目标与兜底说明写进项目文档，方便日后维护与续期。

**Files:**
- Modify: `webpage/README.md`
- Modify: `CLAUDE.md`

**Interfaces:**
- 无代码接口，纯文档。

- [ ] **Step 1: 更新 `webpage/README.md`**

在「改哪个文件」表补一行说明汇总逻辑位置，并新增一小节「投票实时汇总（CloudBase 云数据库）」，内容涵盖：
- 数据流：匿名登录 → 每票 upsert 自己那条 `votes` 文档 → 汇总面板读全量算加权分。
- 依赖文件：`tally.js`（纯算法）、`app.js` 的 `cloud` 模块、`cloudbase.js`（vendored SDK，同源部署）。
- 新增部署目标：`tcb hosting deploy cloudbase.js cloudbase.js -e plan-d0gstt7r6507aa319`（SDK 变更时才需，一般一次即可）。
- 控制台一次性配置四步（匿名登录 / 建 `votes` 集合 / 安全规则 / Web 安全域名），附 Task 4 Step 1 的清单。
- 单测：`node --test webpage/test/tally.test.js`。
- 兜底：SDK/网络失败时本地投票与「一键复制」仍可用。

- [ ] **Step 2: 更新 `CLAUDE.md`**

在「构建与部署」补充：
- 投票已接入 CloudBase 云数据库实时汇总（集合 `votes`，匿名登录），改汇总算法看 `webpage/tally.js`，改同步/渲染看 `webpage/app.js` 的 `cloud` 模块。
- 部署多一个目标 `cloudbase.js`（SDK 变更时 `tcb hosting deploy cloudbase.js cloudbase.js -e plan-d0gstt7r6507aa319`）。
- 首次启用需控制台配置四步（见 `webpage/README.md`）。
- 单测：`node --test webpage/test/tally.test.js`（零依赖）。

- [ ] **Step 3: 提交**

```bash
git add webpage/README.md CLAUDE.md
git commit -m "文档：补充 CloudBase 实时汇总投票的数据流、控制台配置与新增部署目标"
```

---

## Self-Review

**1. Spec coverage**（对照 `2026-07-10-cloudbase-realtime-voting-design.md`）：
- 附加式改造、保留本地投票+复制兜底 → Task 2 挂钩保留原语句、Task 3 Step 6 / Task 4 Step 5 验证兜底。✅
- 数据模型 `votes`（`_openid/name/picks/combo/updatedAt`）→ Task 2 `currentState()` + `add/update`。✅
- 安全规则「人人可读、仅写自己」→ Task 4 Step 1 配置 + Step 4 验证。✅
- 单元 A 云连接层（ready/syncMine/fetchAll）→ Task 2 Step 1。✅
- 单元 B 三处同步挂钩（投票/改名/改组合）→ Task 2 Step 3。✅
- 单元 C 汇总面板（加权分排序、组合汇总、已N人参与、打开/投完/刷新三时机）→ Task 1 算法 + Task 2 渲染/刷新 + Task 3 DOM。✅
- 单元 D 兜底（offline 文案）→ Task 2 `refreshTally` + Task 3 Step 6。✅
- 构建：SDK 同源部署、build 打包、`index.html` 照旧生成 → Task 3。✅
- 一次性控制台配置四步 → Task 4 Step 1。✅
- 测试策略（纯函数单测 + 端到端手测/安全规则/断网）→ Task 1 单测、Task 4 Step 3-5。✅
- 非目标（不做账号体系/字段级合并/后台/watch）→ 计划未纳入。✅

**2. Placeholder scan**：无 TBD/TODO；代码步骤均给出完整代码；下载与安全规则含明确校验与备用路径（非占位，是外部资产的必要兜底）。✅

**3. Type consistency**：`computeTally(docs, items, combos)` 返回 `{voterCount, spots:[{id,zh,must,maybe,score}], combos:[{no,label,count}]}` 在 Task 1 定义、Task 2 `renderTally` 消费字段一致（`s.id/s.zh/s.score/s.must/s.maybe`、`c.label/c.count`）；`cloud.syncMine/fetchAll/offline` 在 Task 2 定义并被 Task 2/3 调用；DOM id `#tallyBody/#tallyRefresh/#tally` 在 Task 2 引用、Task 3 生成一致；`bali_docid`（`DOCID_KEY`）、`votes` 集合名全篇一致。✅
