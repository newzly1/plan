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
