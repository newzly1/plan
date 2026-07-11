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
