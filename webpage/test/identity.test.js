"use strict";
const test = require("node:test");
const assert = require("node:assert");
const { normalizeName, deriveDocId, mergePicks, mergeState, countDecided, classifyBind } = require("../identity.js");

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

test("mergePicks: 防原型污染（__proto__ 键不替换返回对象原型、不污染全局）", () => {
  const evil = JSON.parse('{"__proto__":{"polluted":1},"A1":"must"}');
  const r = mergePicks(evil, { B1: "maybe" });
  assert.deepStrictEqual(r, { A1: "must", B1: "maybe" });
  assert.strictEqual(Object.getPrototypeOf(r), Object.prototype);
  assert.strictEqual({}.polluted, undefined);
});

test("deriveDocId: 浏览器 btoa 路径与 Node Buffer 路径派生一致（跨端确定性）", () => {
  const names = ["小李", "Bob", "小 李"];
  const viaBuffer = names.map(deriveDocId);        // Node 默认走 Buffer 分支
  const saved = global.Buffer;
  try {
    global.Buffer = undefined;                     // 强制走 btoa(unescape(encodeURIComponent(...))) 分支（浏览器路径）
    names.forEach((n, i) => assert.strictEqual(deriveDocId(n), viaBuffer[i]));
  } finally {
    global.Buffer = saved;
  }
});

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

test("countDecided: 忽略与 Object.prototype 同名的伪值（toString/constructor 等）", () => {
  assert.strictEqual(countDecided({ A1: "toString", B1: "constructor", C1: "hasOwnProperty" }), 0);
  assert.strictEqual(countDecided({ A1: "must", B1: "toString" }), 1);
});

test("classifyBind: existing 里全是伪值应视为 free 而非 occupied", () => {
  assert.strictEqual(classifyBind("", "u_a", { picks: { A1: "toString" } }), "free");
});
