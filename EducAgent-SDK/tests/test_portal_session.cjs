"use strict";

const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");
const ts = require("typescript");

const source = fs.readFileSync(path.join(__dirname, "../web/src/App.tsx"), "utf8");
const parsed = ts.createSourceFile("App.tsx", source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);

test("Portal preferences are server-owned, not restored from legacy Web Storage", () => {
  assert.doesNotMatch(source, /\blocalStorage\b|\bsessionStorage\b|educagent\.courseProfile|educagent\.lastModuleId/);
  // Explicit module and preview links remain available independently of saved preferences.
  assert.match(source, /parameters\.get\("module"\)/);
  assert.match(source, /parameters\.get\("preview"\)/);
  assert.match(source, /api\("\/api\/select-profile",\s*\{profile_id:profileId\}\)/);
});

test("Portal state and command requests carry only the same-origin session cookie", async () => {
  const declarations = parsed.statements.filter(node =>
    (ts.isFunctionDeclaration(node) && ["api", "requestId"].includes(node.name?.text)) ||
    (ts.isClassDeclaration(node) && node.name?.text === "ApiFailure"));
  assert.equal(declarations.length, 3);
  const compiled = ts.transpileModule(declarations.map(node => node.getText(parsed)).join("\n"), {
    compilerOptions: {module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022},
  });
  const requests = [];
  const context = vm.createContext({
    AbortController, DOMException, crypto,
    window: {setTimeout, clearTimeout},
    fetch: async (url, options) => {
      requests.push({url, options});
      return {ok: true, json: async () => ({profile_required: true})};
    },
  });
  vm.runInContext(compiled.outputText, context);
  assert.equal((await context.api("/api/state")).profile_required, true);
  await context.api("/api/select-profile", {profile_id: "medical"});
  assert.deepEqual(requests.map(({url, options}) => [url, options.method, options.credentials]), [
    ["/api/state", "GET", "same-origin"],
    ["/api/select-profile", "POST", "same-origin"],
  ]);
  assert.equal(requests[0].options.body, undefined);
  assert.equal(JSON.parse(requests[1].options.body).profile_id, "medical");
  assert.match(JSON.parse(requests[1].options.body).request_id, /^web\.command\./);
});
