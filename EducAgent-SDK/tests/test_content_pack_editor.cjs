"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const test = require("node:test");

const root = path.resolve(__dirname, "..");
const html = fs.readFileSync(path.join(root, "web/tools/content-pack-editor.html"), "utf8");
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const copy = value => JSON.parse(JSON.stringify(value));

function createEditor() {
  const elements = new Map();
  const documentEvents = new Map();
  const context = {
    location: { protocol: "file:" },
    document: {
      addEventListener(name, handler) { documentEvents.set(name, handler); },
      getElementById(id) {
        if (!elements.has(id)) elements.set(id, {
          handlers: new Map(),
          addEventListener(name, handler) { this.handlers.set(name, handler); }
        });
        return elements.get(id);
      }
    }
  };
  vm.createContext(context);
  // Run the real import, edit, validation and export logic. Replace only DOM
  // rendering/download side effects; no browser package is needed for this test.
  const testHooks = `
    globalThis.editor = {
      get state() { return state; }, populateFromPack, buildExportObject,
      validatePack, validateWithSdk, example: EXAMPLE_PACK
    };
    function renderAll() {}
    function renderActivities() {}
    function showErrors(messages) { globalThis.lastErrors = messages; }
    function showSuccess(message) { globalThis.lastSuccess = message; }
    function downloadJson(pack, filename) { globalThis.downloaded = { pack, filename }; }
  `;
  vm.runInContext(script.replace(/\}\)\(\);\s*$/, testHooks + "})();"), context);
  return {
    context,
    editor: context.editor,
    click(id) { return elements.get(id).handlers.get("click")(); },
    input(list, index, field, value, sublist, subindex) {
      const attributes = { "data-list": list, "data-idx": String(index) };
      if (sublist) Object.assign(attributes, { "data-sublist": sublist, "data-subidx": String(subindex) });
      documentEvents.get("input")({ target: {
        type: "text", value,
        matches(selector) { return selector === "[data-field]"; },
        getAttribute() { return field; },
        closest() { return { getAttribute(name) { return attributes[name] || null; } }; }
      } });
    }
  };
}

function issues(editor, pack = editor.buildExportObject()) {
  const errors = [];
  editor.validatePack(pack, errors);
  return errors;
}

test("import/export preserves complete authored packs including omitted defaults", () => {
  const { editor } = createEditor();
  for (const name of ["causality_m0_full", "causality_m0_episode", "fractions_m0",
    "m1_effect_of_an_intervention", "m1_robust_prediction_or_generation"]) {
    const pack = JSON.parse(fs.readFileSync(path.join(root, "content", name + ".json"), "utf8"));
    editor.populateFromPack(pack);
    assert.deepEqual(copy(editor.buildExportObject()), pack, name);
    assert.deepEqual(issues(editor), [], name + " passes local authoring checks");
  }
});

test("editing one text/reference/choice keeps all other source and scene fields intact", () => {
  const runtime = createEditor();
  const pack = JSON.parse(fs.readFileSync(path.join(root, "content/causality_m0_full.json"), "utf8"));
  const expected = copy(pack);
  runtime.editor.populateFromPack(pack);
  runtime.input("resources", 0, "text", "  Revised scenario wording.  ");
  expected.resources[0].text = "Revised scenario wording.";
  const claimIndex = pack.claims.findIndex(claim => claim.source_refs && claim.source_refs.length);
  runtime.input("claims", claimIndex, "locator", "A precise revised locator", "source_refs", 0);
  expected.claims[claimIndex].source_refs[0].locator = "A precise revised locator";
  const activityIndex = pack.activities.findIndex(activity => activity.choices && activity.choices.length);
  runtime.input("activities", activityIndex, "text", "Revised option wording", "choices", 0);
  expected.activities[activityIndex].choices[0].text = "Revised option wording";
  assert.deepEqual(copy(runtime.editor.buildExportObject()), expected);
  assert.notDeepEqual(pack.resources[0].text, expected.resources[0].text, "input object was not mutated");
});

test("comparison workbenches and every registered profile pack survive text editing", () => {
  const runtime = createEditor();
  const registry = JSON.parse(fs.readFileSync(path.join(root, "content/modules.json"), "utf8"));
  const paths = registry.modules.flatMap(module => Object.values(module.profile_pack_paths || {}));
  const seed = JSON.parse(fs.readFileSync(path.join(root, "content/causality_m0_full.json"), "utf8"));
  seed.activities[0].workbench = {
    title: "Compare the groups", introduction: "Inspect the observations.",
    scenario_id: "comparison.example", stage: "investigate", tables: [{
      table_id: "comparison.records", label: "Recorded groups", columns: ["Group", "Count"],
      rows: [["A", "12"], ["B", "9"]], note: "No assignment was imposed."
    }]
  };
  for (const pack of [seed, ...paths.map(file => JSON.parse(fs.readFileSync(path.join(root, file), "utf8")))]) {
    runtime.editor.populateFromPack(pack);
    const expected = copy(pack);
    expected.resources[0].text = "Revised teaching text.";
    runtime.input("resources", 0, "text", expected.resources[0].text);
    assert.deepEqual(copy(runtime.editor.buildExportObject()), expected, pack.pack_id);
  }
});

test("failed nested import retains the previously loaded work", () => {
  const { editor } = createEditor();
  editor.populateFromPack(editor.example);
  const previous = copy(editor.buildExportObject());
  for (const [change, message] of [
    [pack => { pack.activities[0].choices = "not an array"; }, /choices must be an array/],
    [pack => { pack.activities[0].choices[0].correct = "false"; }, /must be true or false/],
    [pack => { pack.resources[0].claim_ids = [1]; }, /must contain text IDs/]
  ]) {
    const invalid = copy(editor.example);
    change(invalid);
    assert.throws(() => editor.populateFromPack(invalid), message);
    assert.deepEqual(copy(editor.buildExportObject()), previous);
  }
});

test("choice/classification feedback and curriculum requirements match SDK invariants", () => {
  const { editor } = createEditor();
  const check = (change, expected) => {
    const pack = copy(editor.example);
    change(pack);
    assert.ok(issues(editor, pack).some(message => expected.test(message)), String(expected));
  };
  check(pack => { pack.activities[0].choices[1].correct = true; }, /exactly one correct/);
  check(pack => { pack.activities[0].choices.pop(); }, /at least two choices/);
  check(pack => { pack.activities[0].choices[1].hint_resource_ids = []; }, /incorrect choices require/);
  check(pack => { pack.activities[0].choices[0].hint_resource_ids = ["not-causation.hint"]; }, /correct choices must have no/);
  check(pack => { pack.activities[0].requires_revision = true; }, /only classification/);
  check(pack => { pack.activities[0].explanation_resource_id = "not-causation.hint"; }, /must reference a explanation/);
  check(pack => { pack.concepts[0].completion_activity_ids = ["missing.activity"]; }, /unknown completion activity/);
  check(pack => { pack.concepts[0].m1_ready_activity_ids = pack.concepts[0].completion_activity_ids; }, /must be declared as a transfer/);
  check(pack => { pack.claims[0].source_refs = []; }, /exactly one provenance route/);
  check(pack => {
    const activity = copy(pack.activities[0]);
    activity.activity_id += ".second";
    pack.activities.push(activity);
    pack.concepts[0].completion_activity_ids.push(activity.activity_id);
  }, /duplicate option id.*in this pack/);
  const classification = copy(editor.example);
  classification.activities[0].activity_type = "classification";
  classification.activities[0].requires_revision = true;
  assert.deepEqual(issues(editor, classification), []);
});

test("HTTP export asks the SDK validator and blocks structurally invalid downloads", async () => {
  const runtime = createEditor();
  runtime.editor.populateFromPack(runtime.editor.example);
  runtime.context.location.protocol = "http:";
  let submitted;
  runtime.context.fetch = async (url, request) => {
    submitted = { url, request, pack: JSON.parse(request.body).pack };
    return { ok: true, json: async () => ({ valid: false, releasable: false,
      issues: [{ path: "/activities/0", message: "SDK-specific structural error" }] }) };
  };
  await runtime.click("btn-export");
  assert.equal(submitted.url, "/api/validate-content-pack");
  assert.deepEqual(submitted.pack, copy(runtime.editor.example));
  assert.equal(runtime.context.downloaded, undefined);
  assert.match(runtime.context.lastErrors[0], /activities\/0.*SDK-specific structural error/);
  runtime.context.fetch = async () => ({ ok: true, json: async () => ({
    valid: true, releasable: false, issues: [{ path: "/sources/0", message: "Source is a draft" }]
  }) });
  await runtime.click("btn-export");
  assert.deepEqual(copy(runtime.context.downloaded.pack), copy(runtime.editor.example));
  assert.match(runtime.context.lastSuccess, /draft still needs release review/);
});
