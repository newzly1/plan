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
            db.collection(COLL).doc(docId).update(data).then(function(res){
              if (res && res.updated === 0){ // 文档已不存在（被删），重建
                docId = null; localStorage.removeItem(DOCID_KEY); addNew(data, done);
              } else { done(); }
            }).catch(function(){ /* 瞬时错误：保留 docId，下次同步再试，避免重复建档 */ });
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

  function paintSpot(art){
    var id = art.getAttribute("data-id"), st = votes[id];
    if(st){ art.setAttribute("data-vote", st); } else { art.removeAttribute("data-vote"); }
    $$(".v", art).forEach(function(b){
      b.setAttribute("aria-pressed", b.getAttribute("data-v")===st ? "true":"false");
    });
  }
  function paintAll(){ $$(".spot").forEach(paintSpot); updateCount(); }

  function pickCount(){ return Object.keys(votes).filter(function(k){ return votes[k]==="must"||votes[k]==="maybe"; }).length; }
  function updateCount(){ var n=$("#barN"); if(n) n.textContent = pickCount(); }

  // ---- voting (event delegation) ----
  document.addEventListener("click", function(e){
    var vb = e.target.closest(".v");
    if(vb){
      var art = vb.closest(".spot"), id = art.getAttribute("data-id"), v = vb.getAttribute("data-v");
      if(votes[id]===v){ delete votes[id]; } else { votes[id]=v; }
      save(); cloud.syncMine(); paintSpot(art); updateCount(); if(!$("#sheet").hasAttribute("hidden")) renderPicks();
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
    renderPicks(); refreshTally(); sheet.removeAttribute("hidden"); document.body.style.overflow="hidden";
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
  (function(){ var rb = $("#tallyRefresh"); if (rb) rb.addEventListener("click", refreshTally); })();

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

  paintAll();
})();
