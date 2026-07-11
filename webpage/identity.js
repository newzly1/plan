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
