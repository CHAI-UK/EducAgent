"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");
const ts = require("typescript");

const source = fs.readFileSync(path.join(__dirname, "../web/src/portal-url.ts"), "utf8");
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS } });
const context = { exports: {}, URL };
vm.runInNewContext(compiled.outputText, context);
const { moduleLocation, previewLocation } = context.exports;

test("explicit preview entry preserves the selected module and other URL state", () => {
  const initial = "http://127.0.0.1:4173/portal/?module=m1_effect&activity=example&custom=keep#introduction";
  const entered = new URL(previewLocation(initial, true));
  assert.equal(entered.searchParams.get("preview"), "1");
  assert.equal(entered.searchParams.get("module"), "m1_effect");
  assert.equal(entered.searchParams.get("activity"), "example");
  assert.equal(entered.searchParams.get("custom"), "keep");
  assert.equal(entered.hash, "#introduction");
  assert.equal(previewLocation(entered.href, true), entered.href);
});

test("returning to normal learning removes preview so reload cannot re-enter it", () => {
  const initial = "http://127.0.0.1:4173/portal/?preview=1&module=m1_shift&preview=1&lesson=medical#practice";
  const returned = new URL(previewLocation(initial, false));
  assert.equal(returned.searchParams.has("preview"), false);
  assert.equal(returned.searchParams.get("module"), "m1_shift");
  assert.equal(returned.searchParams.get("lesson"), "medical");
  assert.equal(returned.hash, "#practice");
  assert.notEqual(new URL(returned.href).searchParams.get("preview"), "1");
  assert.equal(previewLocation(returned.href, false), returned.href);
});

test("successful module selection replaces stale module routing without losing URL state", () => {
  const initial = "http://127.0.0.1:4173/portal/?module=m1_effect&module=m0&preview=1&custom=keep#practice";
  const selected = new URL(moduleLocation(initial, "m1_shift"));
  assert.deepEqual(selected.searchParams.getAll("module"), ["m1_shift"]);
  assert.equal(selected.searchParams.get("preview"), "1");
  assert.equal(selected.searchParams.get("custom"), "keep");
  assert.equal(selected.hash, "#practice");
  assert.equal(moduleLocation(selected.href, "m1_shift"), selected.href);
});

test("leaving a different preview module restores the normal module in reload routing", () => {
  const initial = "http://127.0.0.1:4173/portal/?module=m1_shift&preview=1&custom=keep";
  const returned = new URL(moduleLocation(previewLocation(initial, false), "m1_effect"));
  assert.equal(returned.searchParams.has("preview"), false);
  assert.equal(returned.searchParams.get("module"), "m1_effect");
  assert.equal(returned.searchParams.get("custom"), "keep");
});
