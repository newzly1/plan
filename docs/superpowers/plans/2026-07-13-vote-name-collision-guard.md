# 投票撞名防护 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 提交投票时若用户名在云端已被他人占用，弹窗让用户确认「那是不是我」，避免同名抢写同一条云文档导致的静默丢票 / 静默继承他人选票。

**Architecture:** 把「本机首次绑定到某名字的云文档」从连续自动同步里挪出、收拢到点「提交」那一刻；提交时先 `getDoc` 探测该名字是否已有他人选票，撞名则弹自定义弹窗（合并 / 换名）。判定用纯函数放进 `identity.js`（可 `node --test` 覆盖），DOM/弹窗留在 `app.js`。

**Tech Stack:** 原生 ES5 风格 JS（浏览器）、CloudBase Web SDK v2.31.0（全局 `cloudbase`）、Python 标准库构建（`build.py`）、Node 内置测试框架（`node --test`）。

## Global Constraints

- 只用 Node 内置测试框架：`node --test`，零第三方依赖。
- `identity.js` / `tally.js` 为纯函数模块，浏览器（build 内联）与 Node 测试共用；判定逻辑放这里，DOM 留在 `app.js`。
- `app.js` 沿用现有 ES5 风格（`var`、`function`、无箭头/模板串），与文件其余部分一致。
- 弹窗文案为定稿「引导版」，逐字使用：标题 `「<名字>」这个名字已经有人投过票了`；按钮 `就是我，找回旧票` / `不是我，换个名字`。
- 云 SDK 必须 v2.31.0、登录用 `auth.signInAnonymously()`；安全规则 `{ "read": true, "write": "auth.uid != null" }`——本任务不改这三项。
- 构建：`cd webpage && python3 build.py`（只用 Python 标准库，自动内联 `identity.js`/`app.js`/`style.css`）。
- 部署：只重部署 `index.html`（`tcb hosting deploy index.html index.html -e plan-d0gstt7r6507aa319`），`cloudbase.js` 不动。
- **提交与部署需用户点头**（项目规矩）：计划中的 commit / deploy 步骤在获授权后执行；提交作者沿用 `zly1`、信息用中文。

---

### Task 1: `identity.js` 纯判定逻辑（`countDecided` + `classifyBind`）

**Files:**
- Modify: `webpage/identity.js`
- Test: `webpage/test/identity.test.js`

**Interfaces:**
- Consumes: 现有 `RANK`（`{ must:3, maybe:2, skip:1 }`，`identity.js` 顶部已定义）。
- Produces（供 Task 3 使用）：
  - `countDecided(picks) → number`：统计 `picks` 中值为 must/maybe/skip 的键数；忽略非法值与 `__proto__`；`null/undefined` 返回 `0`。
  - `classifyBind(syncedId, newId, existing) → "noname" | "self" | "free" | "occupied"`。

- [ ] **Step 1: 写失败测试**（追加到 `webpage/test/identity.test.js`）

先把第 4 行的解构补上两个新导出：

```js
const { normalizeName, deriveDocId, mergePicks, mergeState, countDecided, classifyBind } = require("../identity.js");
```

在文件末尾追加：

```js
test("countDecided: 统计 must/maybe/skip，忽略非法值与空", () => {
  assert.strictEqual(countDecided({ A1: "must", B1: "maybe", C1: "skip" }), 3);
  assert.strictEqual(countDecided({ A1: "must", B1: "no", C1: "weird" }), 1);
  assert.strictEqual(countDecided({}), 0);
  assert.strictEqual(countDecided(null), 0);
  assert.strictEqual(countDecided(undefined), 0);
});

test("countDecided: 忽略 __proto__ 键", () => {
  const evil = JSON.parse('{"__proto__":{"x":1},"A1":"must"}');
  assert.strictEqual(countDecided(evil), 1);
});

test("classifyBind: noname / self / free / occupied", () => {
  assert.strictEqual(classifyBind("", "", null), "noname");
  assert.strictEqual(classifyBind("u_a", "", null), "noname");
  assert.strictEqual(classifyBind("u_a", "u_a", { picks: { A1: "must" } }), "self");
  assert.strictEqual(classifyBind("", "u_a", null), "free");
  assert.strictEqual(classifyBind("", "u_a", { picks: {} }), "free");
  assert.strictEqual(classifyBind("", "u_a", { picks: { A1: "no" } }), "free");
  assert.strictEqual(classifyBind("", "u_a", { picks: { A1: "must" } }), "occupied");
  assert.strictEqual(classifyBind("u_b", "u_a", { picks: { A1: "maybe" } }), "occupied");
});
```

- [ ] **Step 2: 运行测试确认失败**

Run: `node --test webpage/test/identity.test.js`
Expected: FAIL —— `countDecided is not a function` / `classifyBind is not a function`（新用例报错，原 7 个仍通过）。

- [ ] **Step 3: 实现两个纯函数**（`webpage/identity.js`）

在 `mergeState` 函数之后、`var api = {...}` 之前插入：

```js
  function countDecided(picks) {
    picks = picks || {};
    var n = 0, k;
    for (k in picks) {
      if (!Object.prototype.hasOwnProperty.call(picks, k) || k === "__proto__") continue;
      if (RANK[picks[k]]) n++;
    }
    return n;
  }

  function classifyBind(syncedId, newId, existing) {
    if (!newId) return "noname";
    if (newId === syncedId) return "self";
    if (existing && countDecided(existing.picks) > 0) return "occupied";
    return "free";
  }
```

把导出行改为（追加两个键）：

```js
  var api = { normalizeName: normalizeName, deriveDocId: deriveDocId, mergePicks: mergePicks, mergeState: mergeState, countDecided: countDecided, classifyBind: classifyBind };
```

- [ ] **Step 4: 运行测试确认通过**

Run: `node --test webpage/test/identity.test.js`
Expected: PASS —— `pass 10 / fail 0`（原 7 + 新 3）。

- [ ] **Step 5: 提交（获授权后）**

```bash
git add webpage/identity.js webpage/test/identity.test.js
git commit -m "投票撞名防护：identity.js 新增 countDecided/classifyBind 纯判定 + 单测

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: 撞名弹窗的 markup 与样式

**Files:**
- Modify: `webpage/build.py`（`mylist()` 返回的 HTML，`#sheet` 之后、`#lb` 之前，约第 245–246 行之间）
- Modify: `webpage/style.css`（`.reset` 规则之后、`/* lightbox */` 之前，约第 280–282 行之间）

**Interfaces:**
- Produces（供 Task 3 使用）：DOM 元素 id —— `#dup`（遮罩容器，默认 `hidden`）、`#dupName`（标题里的名字 span）、`#dupMeta`（标记数+时间行）、`#dupMerge`（「就是我」按钮）、`#dupRename`（「换个名字」按钮）。

- [ ] **Step 1: 加弹窗 markup**（`webpage/build.py`）

在 `mylist()` 返回串里，`#sheet` 的 `</div>\n</div>` 之后、`<div class="lb" id="lb"` 之前，插入：

```html
<div class="dup" id="dup" hidden>
  <div class="dup-card" role="dialog" aria-modal="true" aria-labelledby="dupTitle">
    <p class="dup-title" id="dupTitle">「<span id="dupName"></span>」这个名字已经有人投过票了</p>
    <p class="dup-sub">云端有一份用这个名字投的选择<br><span class="dup-meta" id="dupMeta"></span></p>
    <ul class="dup-guide">
      <li>如果那是你本人（换了手机或浏览器），选「就是我」把旧票找回来一起算。</li>
      <li>如果不是你，继续会盖掉对方的票——请「换个名字」。</li>
    </ul>
    <div class="dup-act">
      <button type="button" class="dup-yes" id="dupMerge">就是我，找回旧票</button>
      <button type="button" class="dup-no" id="dupRename">不是我，换个名字</button>
    </div>
  </div>
</div>
```

- [ ] **Step 2: 加弹窗样式**（`webpage/style.css`，`.reset{...}` 那条规则之后）

```css
/* 撞名弹窗 */
.dup{position:fixed;inset:0;z-index:65;display:flex;align-items:center;justify-content:center;
  background:rgba(15,12,8,.62);backdrop-filter:blur(3px);padding:20px}
.dup[hidden]{display:none}
.dup-card{width:100%;max-width:400px;background:var(--ground);border:1.5px solid var(--line-strong);
  box-shadow:var(--shadow-lg);padding:22px 22px calc(20px + env(safe-area-inset-bottom))}
.dup-title{font-size:16px;font-weight:700;line-height:1.5;margin-bottom:10px}
.dup-sub{font-size:13.5px;color:var(--ink-soft);line-height:1.7;margin-bottom:12px}
.dup-meta{color:var(--ink-faint);font-size:12.5px}
.dup-guide{list-style:none;margin:0 0 18px;padding:0;display:flex;flex-direction:column;gap:8px}
.dup-guide li{position:relative;padding-left:16px;font-size:13.5px;color:var(--ink);line-height:1.65}
.dup-guide li::before{content:"·";position:absolute;left:4px;color:var(--brass);font-weight:700}
.dup-act{display:flex;flex-direction:column;gap:9px}
.dup-yes{padding:14px;border:1px solid var(--pine);background:var(--pine);color:#F6F3EA;
  font-size:13px;font-weight:700;letter-spacing:.06em;cursor:pointer;border-radius:0}
.dup-yes:disabled{opacity:.5;cursor:default}
.dup-no{padding:13px;border:1px solid var(--line-2);background:transparent;color:var(--ink-soft);
  font-size:12.5px;letter-spacing:.04em;cursor:pointer;border-radius:0}
```

- [ ] **Step 3: 构建并确认 markup 落进页面**

Run: `cd webpage && python3 build.py`
Expected: 打印 `wrote index.html ...`，无报错。

Run: `grep -c 'id="dup"' webpage/index.html`
Expected: `1`

Run: `grep -c 'dup-yes\|dupMerge\|dupRename' webpage/index.html`
Expected: 非 0（弹窗按钮已内联）。

- [ ] **Step 4: 目测弹窗样式（devtools）**

在浏览器打开 `webpage/index.html`，DevTools 里对 `#dup` 去掉 `hidden` 属性、给 `#dupName` 填「王」、`#dupMeta` 填「5 个标记 · 上次提交：今天 14:30」，确认弹窗居中、深浅色主题下都可读、两个按钮上下排列清晰。看完把 `hidden` 加回。

- [ ] **Step 5: 提交（获授权后）**

```bash
git add webpage/build.py webpage/style.css webpage/index.html
git commit -m "投票撞名防护：新增撞名确认弹窗 markup 与样式

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: `app.js` —— 提交时绑定 + 撞名探测 + 弹窗接线

**Files:**
- Modify: `webpage/app.js`（`cloud` 模块，约第 19–121 行；submit 按钮处理，约第 305–319 行；Escape 键处理，约第 334–336 行；新增撞名弹窗接线块）

**Interfaces:**
- Consumes: Task 1 的 `IdentityLib.classifyBind`、`IdentityLib.countDecided`；Task 2 的 `#dup`/`#dupName`/`#dupMeta`/`#dupMerge`/`#dupRename`；现有 `IdentityLib.deriveDocId`、`IdentityLib.mergeState`、`adoptLocal`、`updateViews`、`sheetOpen`、`openSheet`、`toast`。
- Produces: `cloud.syncMine()`（已绑定才写云）、`cloud.submit()`、`cloud.mergeAdopt()`、`cloud.clearPending()`；模块内 `showDupModal(info)` / `hideDup()`。移除旧的 `cloud.syncNow` 与 `doSync`。

- [ ] **Step 1: 整体替换 `cloud` 模块**（`webpage/app.js` 第 19 行 `var cloud = (function(){` 到第 121 行 `})();` 之间的整块，替换为下面内容）

```js
  var cloud = (function(){
    var db = null, failed = false, groupTally = null, syncT = null;
    var pendingExisting = null; // 撞名时暂存云端已有文档，供“合并”复用，避免二次读取竞态
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
    function plainState(st){ return { name: st.name, picks: st.picks, combo: st.combo }; }
    function writeSet(docId, data){
      data.updatedAt = Date.now();
      return coll().doc(docId).set(data);
    }

    // 已绑定当前名字时的自动同步：只覆盖“自己”那条文档；未绑定/改名未提交 → 只本机
    function syncMine(){
      if (failed) return;
      clearTimeout(syncT);
      syncT = setTimeout(function(){
        readyP.then(function(){
          var st = currentState();
          var newId = IdentityLib.deriveDocId(st.name);
          var syncedId = localStorage.getItem(SYNCED_KEY) || "";
          if (newId && newId === syncedId){
            return writeSet(newId, plainState(st)).then(function(){ refreshGroup(); });
          }
          if (!newId && syncedId){ // 已绑定后清空名字：撤下自己那条、退回本机（只动自己的文档）
            return coll().doc(syncedId).remove().catch(function(){}).then(function(){
              localStorage.removeItem(SYNCED_KEY); refreshGroup();
            });
          }
          refreshGroup(); // 未绑定 / 改名但未提交：只存本机
        }).catch(function(){});
      }, 800);
    }

    // 落定绑定并写入云端；existingForMerge 非空时把云端已有选票并入本机
    function commitBind(newId, syncedId, st, existingForMerge){
      var data = existingForMerge ? IdentityLib.mergeState(st, existingForMerge) : plainState(st);
      return writeSet(newId, data).then(function(){
        localStorage.setItem(SYNCED_KEY, newId);
        if (syncedId && syncedId !== newId) coll().doc(syncedId).remove().catch(function(){});
        if (existingForMerge) adoptLocal(data);
        return refreshGroup().then(function(){ return { status: existingForMerge ? "merged" : "bound" }; });
      });
    }

    // 点“提交”：首次绑定/改名在此发生，并做撞名探测（清名撤档由 syncMine 负责，此处只处理有名字的提交）
    function submit(){
      return readyP.then(function(){
        var st = currentState();
        var newId = IdentityLib.deriveDocId(st.name);
        var syncedId = localStorage.getItem(SYNCED_KEY) || "";
        if (!newId){ return refreshGroup().then(function(){ return { status: "noname" }; }); } // 保险：调用方（提交按钮）已挡空名
        if (newId === syncedId){ // 已是自己：正常覆盖
          return writeSet(newId, plainState(st)).then(function(){
            return refreshGroup().then(function(){ return { status: "self" }; });
          });
        }
        return getDoc(newId).then(function(existing){ // 首次绑定/改名：先探测
          if (IdentityLib.classifyBind(syncedId, newId, existing) === "occupied"){
            pendingExisting = existing;
            return { status: "collision", name: st.name,
                     count: IdentityLib.countDecided(existing.picks),
                     updatedAt: existing.updatedAt || 0 };
          }
          return commitBind(newId, syncedId, st, null);
        });
      });
    }

    // 撞名后用户点“就是我，找回旧票”
    function mergeAdopt(){
      return readyP.then(function(){
        var st = currentState();
        var newId = IdentityLib.deriveDocId(st.name);
        var syncedId = localStorage.getItem(SYNCED_KEY) || "";
        return commitBind(newId, syncedId, st, pendingExisting || {});
      });
    }

    function fetchAll(){
      return readyP.then(function(){
        return coll().limit(50).get().then(function(res){ return (res && res.data) || []; });
      });
    }
    function refreshGroup(){
      if (failed){ groupTally = null; updateViews(); return Promise.resolve(); }
      return fetchAll().then(function(docs){
        groupTally = TallyLib.computeTally(docs, ITEMS, COMBOS);
        updateViews();
      }).catch(function(){ updateViews(); });
    }
    return {
      syncMine: syncMine,
      submit: submit,
      mergeAdopt: mergeAdopt,
      clearPending: function(){ pendingExisting = null; },
      refreshGroup: refreshGroup,
      group: function(){ return groupTally; },
      offline: function(){ return failed; }
    };
  })();
```

- [ ] **Step 2: 替换 submit 按钮处理**（`webpage/app.js` 第 305–319 行整块 `$("#submitBtn").addEventListener(...)` 替换为）

```js
  $("#submitBtn").addEventListener("click", function(){
    if (cloud.offline()){ toast("云同步暂不可用，无法提交"); return; }
    var name = (localStorage.getItem(K.name)||"").trim();
    if (!name){ toast("请先填名字再提交"); var n=$("#nameIn"); if(n) n.focus(); return; }
    var decided = decidedCount();
    var btn = this, orig = btn.textContent;
    btn.disabled = true; btn.textContent = "提交中…";
    cloud.submit().then(function(res){
      btn.disabled = false; btn.textContent = orig;
      if (res && res.status === "collision"){ showDupModal(res); return; }
      toast(decided > 0 ? "已提交！"+name+" 的选择已同步到群汇总" : "已提交！当前无标记，已退出群汇总");
    }).catch(function(){
      btn.disabled = false; btn.textContent = orig;
      toast("提交失败，请检查网络后重试");
    });
  });
```

- [ ] **Step 3: 新增撞名弹窗接线块**（`webpage/app.js`，在 `// ---- lightbox ----` 注释那一行之前插入）

```js
  // ---- 撞名弹窗 ----
  var dup = $("#dup");
  function fmtTime(ts){
    if(!ts) return "";
    var d=new Date(ts), now=new Date();
    var hh=("0"+d.getHours()).slice(-2), mm=("0"+d.getMinutes()).slice(-2);
    var sameDay = d.getFullYear()===now.getFullYear() && d.getMonth()===now.getMonth() && d.getDate()===now.getDate();
    return (sameDay ? "今天 " : (d.getMonth()+1)+"月"+d.getDate()+"日 ") + hh + ":" + mm;
  }
  function showDupModal(info){
    var t = fmtTime(info.updatedAt);
    $("#dupName").textContent = info.name;
    $("#dupMeta").textContent = info.count + " 个标记" + (t ? " · 上次提交：" + t : "");
    dup.removeAttribute("hidden"); document.body.style.overflow="hidden";
    var yes=$("#dupMerge"); if(yes) yes.focus();
  }
  function hideDup(){
    dup.setAttribute("hidden",""); cloud.clearPending();
    document.body.style.overflow = sheetOpen() ? "hidden" : "";
  }
  $("#dupMerge").addEventListener("click", function(){
    var btn=this, orig=btn.textContent; btn.disabled=true; btn.textContent="合并中…";
    cloud.mergeAdopt().then(function(){
      btn.disabled=false; btn.textContent=orig; hideDup();
      toast("已合并，你的选择已同步到群汇总");
    }).catch(function(){
      btn.disabled=false; btn.textContent=orig;
      toast("合并失败，请检查网络后重试");
    });
  });
  $("#dupRename").addEventListener("click", function(){
    hideDup();
    if(!sheetOpen()) openSheet();
    var n=$("#nameIn"); if(n){ n.focus(); n.select(); }
    toast("这个名字已被占用，换一个再提交");
  });
  dup.addEventListener("click", function(e){ if(e.target===dup) hideDup(); });
```

- [ ] **Step 4: Escape 键先关弹窗**（`webpage/app.js` 第 334–336 行的 Escape 处理块替换为）

```js
  document.addEventListener("keydown", function(e){
    if(e.key==="Escape"){
      if(!dup.hasAttribute("hidden")){ hideDup(); return; }
      if(!lb.hasAttribute("hidden")) closeLB();
      else if(!sheet.hasAttribute("hidden")) closeSheet();
    }
  });
```

- [ ] **Step 5: 构建 + 回归单测**

Run: `cd webpage && python3 build.py`
Expected: `wrote index.html ...`，无报错。

Run: `node --test webpage/test/*.test.js`
Expected: 全部 PASS（identity 10 个 + tally 原有），`fail 0`。

Run: `grep -c 'cloud.syncNow\|function doSync' webpage/index.html`
Expected: `0`（旧接口已彻底移除，无残留调用）。

- [ ] **Step 6: 手动验收（两浏览器/无痕窗口，需在线）**

打开 `index.html`（本地或已部署链接），按下列勾验：

1. 甲窗口：填名「王」+ 标几个点 → 点「提交」→ toast「已提交」；面板「群 1/6」。
2. 乙窗口（无痕）：填**同名**「王」+ 标不同点 → 点「提交」→ **弹出撞名弹窗**，显示「王」「N 个标记 · 上次提交…」。
   - 点「不是我，换个名字」→ 弹窗关、名字框聚焦选中、toast 提示；改名「李」再提交 → 云端两条、面板「群 2/6」，甲的选票未被覆盖。
3. 甲换一个浏览器：填「王」提交 → 弹窗；点「就是我，找回旧票」→ toast「已合并」，之前标的点被拉回本机、仍是同一条、群人数不增。
4. 提交前：在任一窗口标点但**不点提交** → 另一窗口刷新，群人数/汇总**不含**未提交的票（确认「提交才计入」）。

- [ ] **Step 7: 提交（获授权后）**

```bash
git add webpage/app.js webpage/index.html
git commit -m "投票撞名防护：提交时绑定+撞名探测，弹窗合并/换名，自动同步仅限已绑定

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: 上线部署（获授权后）

**Files:** 无代码改动，仅发布 `webpage/index.html`。

- [ ] **Step 1: 确认已构建最新 index.html**

Run: `cd webpage && python3 build.py`
Expected: `wrote index.html ...`。

- [ ] **Step 2: 部署 index.html（outward-facing，需用户明确同意后执行）**

Run: `cd webpage && tcb hosting deploy index.html index.html -e plan-d0gstt7r6507aa319`
Expected: 部署成功；`cloudbase.js` 无需重传。

- [ ] **Step 3: 线上冒烟**

打开 https://plan-d0gstt7r6507aa319-1451599494.tcloudbaseapp.com ，重跑 Task 3 Step 6 的两浏览器验收关键项（撞名弹窗出现、换名后独立成两条、合并可找回）。

---

## 附：本计划对既有行为的取舍

- **提交才写云**：提交前投票只存本机、不进群汇总；提交后照旧自动同步（`syncMine` 仅在 `newId === syncedId` 时写自己那条）。这与页面已有的「提交我的选择」按钮语义一致。
- **合并需显式点按**：旧的「换设备输同名 → 静默把他人选票拉下来」改为必须点「就是我，找回旧票」。
- **存量用户无影响**：已绑定者 `newId === syncedId` 走 `self` 分支，无需迁移。
- **安全默认**：撞名弹窗遮罩点击 / Esc 等同「换个名字」，绝不覆盖他人。
- **保留“清名即退出”**：已绑定后清空名字，`syncMine` 会删掉自己那条云文档并清 `SYNCED_KEY`（沿用旧行为，避免遗留孤儿文档虚增“群 N/6”）；这是对自己文档的操作，不涉及撞名。
