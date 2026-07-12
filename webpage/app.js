(function(){
  "use strict";
  var ITEMS = /*__ITEMS__*/;
  var COMBOS = /*__COMBOS__*/;
  var K = { votes:"bali_votes", name:"bali_name", combo:"bali_combo" };
  var $ = function(s,r){ return (r||document).querySelector(s); };
  var $$ = function(s,r){ return Array.prototype.slice.call((r||document).querySelectorAll(s)); };

  function getVotes(){ try{ return JSON.parse(localStorage.getItem(K.votes))||{}; }catch(e){ return {}; } }
  var votes = getVotes();
  function save(){ try{ localStorage.setItem(K.votes, JSON.stringify(votes)); }catch(e){} }

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

    function doSync(){
      return readyP.then(function(){
        var st = currentState();
        var newId = IdentityLib.deriveDocId(st.name);
        var syncedId = localStorage.getItem(SYNCED_KEY) || "";
        var delP = (syncedId && syncedId !== newId)
          ? coll().doc(syncedId).remove().catch(function(){})  // 改名/清名：删旧档
          : Promise.resolve();
        return delP.then(function(){
          if (!newId){ localStorage.removeItem(SYNCED_KEY); refreshGroup(); return; } // 没名字：只本机
          if (syncedId !== newId){
            // 采纳并合并（换设备/撞名/首次绑定），防丢票
            return getDoc(newId).then(function(existing){
              var merged = IdentityLib.mergeState(st, existing || {});
              return writeSet(newId, merged).then(function(){
                localStorage.setItem(SYNCED_KEY, newId);
                adoptLocal(merged);
                refreshGroup();
              });
            }).catch(function(){
              return writeSet(newId, { name: st.name, picks: st.picks, combo: st.combo }).then(function(){
                localStorage.setItem(SYNCED_KEY, newId); refreshGroup();
              });
            });
          } else {
            // 常态：覆盖自己的文档，本机为准
            return writeSet(newId, { name: st.name, picks: st.picks, combo: st.combo })
              .then(function(){ refreshGroup(); });
          }
        });
      });
    }
    var syncT = null;
    function syncMine(){
      if (failed) return;
      clearTimeout(syncT);
      syncT = setTimeout(function(){ doSync().catch(function(){}); }, 800);
    }
    function syncNow(){
      if (failed) return Promise.reject(new Error("offline"));
      clearTimeout(syncT);
      return doSync();
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
      syncNow: syncNow,
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
    if (sheetOpen()){ renderPicks(); }
  }

  // 刷新依赖群体数据的视图
  function updateViews(){ renderBar(); if (sheetOpen()) renderSheetTally(); }

  function paintSpot(art){
    var id = art.getAttribute("data-id"), st = votes[id];
    if(st){ art.setAttribute("data-vote", st); } else { art.removeAttribute("data-vote"); }
    $$(".v", art).forEach(function(b){
      b.setAttribute("aria-pressed", b.getAttribute("data-v")===st ? "true":"false");
    });
  }
  function paintCombos(){
    var c = localStorage.getItem(K.combo) || "";
    $$(".combo").forEach(function(el){
      var pick = $(".combo-pick", el);
      if (el.getAttribute("data-no") === c) {
        el.setAttribute("data-selected","");
        if (pick) pick.textContent = "✓ 已选为主线";
      } else {
        el.removeAttribute("data-selected");
        if (pick) pick.textContent = "选为我的主线";
      }
    });
  }
  function paintAll(){ $$(".spot").forEach(paintSpot); paintCombos(); renderBar(); }

  function decidedCount(){ return Object.keys(votes).filter(function(k){ var v=votes[k]; return v==="must"||v==="maybe"||v==="skip"; }).length; }

  // ---- voting (event delegation) ----
  document.addEventListener("click", function(e){
    var vb = e.target.closest(".v");
    if(vb){
      var art = vb.closest(".spot"), id = art.getAttribute("data-id"), v = vb.getAttribute("data-v");
      var wasZero = decidedCount()===0;
      if(votes[id]===v){ delete votes[id]; } else { votes[id]=v; }
      save(); cloud.syncMine(); paintSpot(art); renderBar(); if(!$("#sheet").hasAttribute("hidden")) renderPicks();
      maybeNudgeName(wasZero);
      return;
    }
    var idx = e.target.closest(".idx");
    if(idx && idx.getAttribute("href").charAt(0)==="#"){
      e.preventDefault();
      var t = document.getElementById(idx.getAttribute("href").slice(1));
      if(t) t.scrollIntoView({behavior: reduce()?"auto":"smooth", block:"start"});
      return;
    }
    var shot = e.target.closest(".shot-img");
    if(shot && shot.tagName==="IMG" && shot.src){ openLB(shot.src, shot.alt); return; }
    var vid = e.target.closest(".vid");
    if(vid && !vid.hasAttribute("data-playing")){ playVid(vid); return; }
    var comboEl = e.target.closest(".combo");
    if(comboEl){
      var no = comboEl.getAttribute("data-no");
      var cur = localStorage.getItem(K.combo) || "";
      if (cur === no){ localStorage.removeItem(K.combo); }
      else { localStorage.setItem(K.combo, no); }
      cloud.syncMine(); paintCombos();
      return;
    }
  });
  document.addEventListener("keydown", function(e){
    if((e.key==="Enter"||e.key===" ")){
      var vid = e.target.closest && e.target.closest(".vid");
      if(vid && !vid.hasAttribute("data-playing")){ e.preventDefault(); playVid(vid); }
    }
  });

  // ---- video inline playback (one at a time) ----
  function vidFrame(bvid){
    return '<iframe class="vid-frame" src="//player.bilibili.com/player.html?bvid='+bvid+'&page=1&high_quality=1&autoplay=1&as_wide=1" allowfullscreen="true" scrolling="no" border="0" frameborder="no" framespacing="0" sandbox="allow-scripts allow-same-origin allow-popups allow-presentation"></iframe>';
  }
  var vidOrig = new WeakMap();
  function playVid(vid){
    var bvid = vid.getAttribute("data-bvid");
    if(!bvid) return;
    $$(".vid[data-playing]").forEach(function(other){ if(other!==vid) closeVid(other); });
    vidOrig.set(vid, vid.innerHTML);
    vid.setAttribute("data-playing","");
    vid.innerHTML = vidFrame(bvid);
  }
  function closeVid(vid){
    if(!vid.hasAttribute("data-playing")) return;
    var orig = vidOrig.get(vid);
    if(orig){ vid.innerHTML = orig; vidOrig.delete(vid); }
    vid.removeAttribute("data-playing");
  }

  // ---- my-list sheet ----
  var sheet = $("#sheet");
  function openSheet(){
    $("#nameIn").value = localStorage.getItem(K.name)||"";
    renderPicks(); renderSheetTally(); cloud.refreshGroup(); sheet.removeAttribute("hidden"); document.body.style.overflow="hidden";
  }
  function closeSheet(){ sheet.setAttribute("hidden",""); document.body.style.overflow=""; }
  $("#bar").addEventListener("click", openSheet);
  $("#sheetX").addEventListener("click", closeSheet);
  sheet.addEventListener("click", function(e){ if(e.target===sheet) closeSheet(); });
  $("#nameIn").addEventListener("input", function(){ localStorage.setItem(K.name, this.value); cloud.syncMine(); });



  function renderPicks(){
    var box = $("#picks"), must=[], maybe=[];
    ITEMS.forEach(function(it){ if(votes[it.id]==="must") must.push(it); else if(votes[it.id]==="maybe") maybe.push(it); });
    if(!must.length && !maybe.length){ box.innerHTML = '<p class="picks-empty">还没标记。滑动页面，在每个景点点「必去 / 可去」，这里会自动汇总。</p>'; return; }
    var h="";
    if(must.length){ h+='<div class="picks-grp">必去 · '+must.length+'</div>';
      must.forEach(function(it){ h+='<div class="pick must"><span class="pc">'+it.id+'</span>'+esc(it.zh)+'</div>'; }); }
    if(maybe.length){ h+='<div class="picks-grp">可去 · '+maybe.length+'</div>';
      maybe.forEach(function(it){ h+='<div class="pick maybe"><span class="pc">'+it.id+'</span>'+esc(it.zh)+'</div>'; }); }
    box.innerHTML = h;
  }
  function esc(s){ return String(s).replace(/[&<>]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;"}[c];}); }

  // ---- live tally ----
  function renderTally(t){
    if (!t.voterCount) return '<p class="tally-empty">还没有人投票。你投的票会实时汇总到这里。</p>';
    var h = '<div class="tally-n">群 '+t.voterCount+'/6 已投</div>';
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
  function renderSheetTally(){
    var body = $("#tallyBody");
    if (!body) return;
    if (cloud.offline()){ body.innerHTML = '<p class="tally-empty">云同步暂不可用，你的选择已保存在本机。</p>'; return; }
    var t = cloud.group();
    if (!t){ body.innerHTML = '<p class="tally-empty">加载中…</p>'; return; }
    body.innerHTML = renderTally(t);
  }
  (function(){ var rb = $("#tallyRefresh"); if (rb) rb.addEventListener("click", function(){ cloud.refreshGroup(); }); })();

  function shortZh(zh){ return (String(zh).split("·")[0] || "").trim(); }
  function renderBar(){
    var statEl = $("#barStat"), subEl = $("#barSub");
    if (!statEl || !subEl) return;
    var total = ITEMS.length, decided = decidedCount();
    var name = (localStorage.getItem(K.name)||"").trim();
    if (cloud.offline()){
      statEl.textContent = "你选 " + decided + "/" + total;
      subEl.textContent = "云同步暂不可用 · 你的选择已保存在本机";
      subEl.className = "bar-sub warn"; return;
    }
    var g = cloud.group();
    var voters = g ? g.voterCount : 0;
    statEl.textContent = "你选 " + decided + "/" + total + " · 群 " + voters + "/6 已投";
    if (decided > 0 && !name){
      subEl.textContent = "⚠ 填个名字才能加入大家的汇总 →";
      subEl.className = "bar-sub warn";
    } else if (!g || !g.voterCount){
      subEl.textContent = "还没人投票 · 你可以抢先标记";
      subEl.className = "bar-sub";
    } else if (!g.spots.length){
      subEl.textContent = "还没有大家想去的点 · 你可以抢先标记";
      subEl.className = "bar-sub";
    } else {
      var top = g.spots.slice(0,3).map(function(s){ return s.id + " " + shortZh(s.zh); });
      subEl.textContent = "群体最爱 · " + top.join("   ");
      subEl.className = "bar-sub";
    }
  }

  $("#submitBtn").addEventListener("click", function(){
    if (cloud.offline()){ toast("云同步暂不可用，无法提交"); return; }
    var name = (localStorage.getItem(K.name)||"").trim();
    if (!name){ toast("请先填名字再提交"); var n=$("#nameIn"); if(n) n.focus(); return; }
    var decided = decidedCount();
    var btn = this, orig = btn.textContent;
    btn.disabled = true; btn.textContent = "提交中…";
    cloud.syncNow().then(function(){
      btn.disabled = false; btn.textContent = orig;
      toast(decided > 0 ? "已提交！"+name+" 的选择已同步到群汇总" : "已提交！当前无标记，已退出群汇总");
    }).catch(function(){
      btn.disabled = false; btn.textContent = orig;
      toast("提交失败，请检查网络后重试");
    });
  });
  $("#resetBtn").addEventListener("click", function(){
    if(!decidedCount() || confirm("清空所有标记与主线偏好？")){
      votes={}; save();
      localStorage.removeItem(K.combo);
      cloud.syncMine(); paintAll(); renderPicks();
      toast("已清空");
    }
  });

  // ---- lightbox ----
  var lb=$("#lb"), lbImg=$("#lbImg");
  function openLB(src,alt){ lbImg.src=src; lbImg.alt=alt||""; lb.removeAttribute("hidden"); document.body.style.overflow="hidden"; }
  function closeLB(){ lb.setAttribute("hidden",""); lbImg.src=""; if(sheet.hasAttribute("hidden")) document.body.style.overflow=""; }
  lb.addEventListener("click", closeLB);
  document.addEventListener("keydown", function(e){
    if(e.key==="Escape"){ if(!lb.hasAttribute("hidden")) closeLB(); else if(!sheet.hasAttribute("hidden")) closeSheet(); }
  });

  // ---- toast ----
  var toEl=$("#toast"), toT;
  function toast(msg){ clearTimeout(nudgeT); toEl.onclick=null; toEl.className="toast"; toEl.textContent=msg; toEl.removeAttribute("hidden");
    requestAnimationFrame(function(){ toEl.classList.add("show"); });
    clearTimeout(toT); toT=setTimeout(function(){ toEl.classList.remove("show");
      setTimeout(function(){ toEl.setAttribute("hidden",""); },220); }, 1900); }
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

  // ---- reveal ----
  function reduce(){ return window.matchMedia("(prefers-reduced-motion:reduce)").matches; }
  if("IntersectionObserver" in window && !reduce()){
    var io=new IntersectionObserver(function(es){ es.forEach(function(en){ if(en.isIntersecting){ en.target.classList.add("in"); io.unobserve(en.target); } }); }, {rootMargin:"0px 0px -8% 0px"});
    $$(".spot,.combo,.hl").forEach(function(el){ io.observe(el); });
  }

  cloud.refreshGroup();
  document.addEventListener("visibilitychange", function(){ if (document.visibilityState === "visible") cloud.refreshGroup(); });
  setInterval(function(){ if (document.visibilityState === "visible") cloud.refreshGroup(); }, 45000);

  paintAll();
})();
