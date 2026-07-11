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
          }).catch(function(){});
        }).catch(function(){});
      }, 800);
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

  // 刷新依赖群体数据的视图
  function updateViews(){ renderBar(); if (sheetOpen()) renderSheetTally(); }

  function paintSpot(art){
    var id = art.getAttribute("data-id"), st = votes[id];
    if(st){ art.setAttribute("data-vote", st); } else { art.removeAttribute("data-vote"); }
    $$(".v", art).forEach(function(b){
      b.setAttribute("aria-pressed", b.getAttribute("data-v")===st ? "true":"false");
    });
  }
  function paintAll(){ $$(".spot").forEach(paintSpot); renderBar(); }

  function pickCount(){ return Object.keys(votes).filter(function(k){ return votes[k]==="must"||votes[k]==="maybe"; }).length; }
  function decidedCount(){ return Object.keys(votes).filter(function(k){ var v=votes[k]; return v==="must"||v==="maybe"||v==="skip"; }).length; }

  // ---- voting (event delegation) ----
  document.addEventListener("click", function(e){
    var vb = e.target.closest(".v");
    if(vb){
      var art = vb.closest(".spot"), id = art.getAttribute("data-id"), v = vb.getAttribute("data-v");
      if(votes[id]===v){ delete votes[id]; } else { votes[id]=v; }
      save(); cloud.syncMine(); paintSpot(art); renderBar(); if(!$("#sheet").hasAttribute("hidden")) renderPicks();
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
    var c = localStorage.getItem(K.combo);
    $$('input[name="combo"]').forEach(function(r){ r.checked = (r.value===c); });
    renderPicks(); renderSheetTally(); cloud.refreshGroup(); sheet.removeAttribute("hidden"); document.body.style.overflow="hidden";
  }
  function closeSheet(){ sheet.setAttribute("hidden",""); document.body.style.overflow=""; }
  $("#bar").addEventListener("click", openSheet);
  $("#sheetX").addEventListener("click", closeSheet);
  sheet.addEventListener("click", function(e){ if(e.target===sheet) closeSheet(); });
  $("#nameIn").addEventListener("input", function(){ localStorage.setItem(K.name, this.value); cloud.syncMine(); });
  $$('input[name="combo"]').forEach(function(r){
    r.addEventListener("change", function(){ if(r.checked){ localStorage.setItem(K.combo, r.value); cloud.syncMine(); } });
  });

  function labelOf(id){ for(var i=0;i<ITEMS.length;i++){ if(ITEMS[i].id===id) return ITEMS[i].id+" "+ITEMS[i].zh; } return id; }
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
    if (cloud.offline()){ body.innerHTML = '<p class="tally-empty">云同步暂不可用，可用下方「一键复制」发到群里。</p>'; return; }
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

  function summary(){
    var name = (localStorage.getItem(K.name)||"").trim() || "匿名";
    var must=[], maybe=[];
    ITEMS.forEach(function(it){ if(votes[it.id]==="must") must.push(labelOf(it.id)); else if(votes[it.id]==="maybe") maybe.push(labelOf(it.id)); });
    var c = localStorage.getItem(K.combo);
    var combo = (c && COMBOS[c]) ? COMBOS[c] : "未选";
    return "【我的印尼投票】@"+name+"\n"
      + "必去："+(must.length?must.join("、"):"—")+"\n"
      + "可去："+(maybe.length?maybe.join("、"):"—")+"\n"
      + "主线偏好："+combo;
  }
  $("#copyBtn").addEventListener("click", function(){
    var text = summary();
    function ok(){ toast("已复制，去微信群粘贴吧"); }
    if(navigator.clipboard && navigator.clipboard.writeText){
      navigator.clipboard.writeText(text).then(ok).catch(function(){ legacy(text); });
    } else { legacy(text); }
    function legacy(t){
      var ta=document.createElement("textarea"); ta.value=t; ta.style.position="fixed"; ta.style.opacity="0";
      document.body.appendChild(ta); ta.select();
      try{ document.execCommand("copy"); ok(); }catch(e){ toast("复制失败，请长按选择"); }
      document.body.removeChild(ta);
    }
  });
  $("#resetBtn").addEventListener("click", function(){
    if(!pickCount() || confirm("清空你标记的所有必去/可去？")){ votes={}; save(); paintAll(); renderPicks(); }
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
  function toast(msg){ toEl.textContent=msg; toEl.removeAttribute("hidden");
    requestAnimationFrame(function(){ toEl.classList.add("show"); });
    clearTimeout(toT); toT=setTimeout(function(){ toEl.classList.remove("show");
      setTimeout(function(){ toEl.setAttribute("hidden",""); },220); }, 1900); }

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
