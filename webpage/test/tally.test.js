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

test("恶意 __proto__ 键不污染 Object.prototype", () => {
  const before = Object.prototype.must;
  const r = computeTally([{ picks: { "__proto__": "must", A1: "must" } }], ITEMS, COMBOS);
  assert.strictEqual(Object.prototype.must, before); // 未被污染（仍为 undefined）
  assert.strictEqual(({}).must, undefined);
  assert.strictEqual(r.voterCount, 1);
  // A1 正常计入；__proto__ 作为普通字符串键存在，不影响真实景点
  const a1 = r.spots.find(s => s.id === "A1");
  assert.deepStrictEqual(a1, { id: "A1", zh: "巴厘岛门户", must: 1, maybe: 0, score: 2 });
});

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
