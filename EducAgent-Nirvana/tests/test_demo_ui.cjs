// Provider-independent UI-state regressions. Run: node --test tests/test_demo_ui.cjs
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const test = require("node:test");

// A small DOM seam for this worksheet's selectors/events, not a layout/browser test.
test("Literature examples use dedicated specs through AI draft, review, and handoff", async () => {
  const demo = path.join(__dirname, "..", "demo");
  const document = parseDocument(fs.readFileSync(path.join(demo, "index.html"), "utf8"));
  let response, requestBody;
  const context = vm.createContext({
    document, AbortController, setTimeout, clearTimeout, TextEncoder,
    window: { location: { hostname: "127.0.0.1" }, scrollTo() {} },
    navigator: { clipboard: { async writeText() {} } },
    fetch: async (_url, options) => { requestBody = JSON.parse(options.body); return {ok: true, json: async () => response}; },
  });
  vm.runInContext(fs.readFileSync(path.join(demo, "markdown.js"), "utf8"), context);
  vm.runInContext(fs.readFileSync(path.join(demo, "guidance.js"), "utf8"), context);
  vm.runInContext(fs.readFileSync(path.join(demo, "destinations.js"), "utf8"), context);
  vm.runInContext(fs.readFileSync(path.join(demo, "worked-examples.js"), "utf8"), context);
  vm.runInContext(fs.readFileSync(path.join(demo, "app.js"), "utf8"), context);
  const $ = (selector) => document.querySelector(selector);
  const examples = vm.runInContext("literatureExamples", context);
  const exampleOrder = document.querySelectorAll(".example-button").map((node) => node.dataset.example);
  const taskOrder = document.querySelectorAll(".choice").map((node) => node.dataset.task).filter((id) => id !== "other");
  assert.deepEqual(exampleOrder.slice(0, 8).map((id) => examples[id].task), taskOrder);
  assert.equal(exampleOrder[8], "ctpa");
  const sourceHtml = fs.readFileSync(path.join(demo, "index.html"), "utf8");
  assert.equal($("#agent-messages").parent, $("#chat-scroll"));
  assert.equal($("#brief-proposals").parent, $("#chat-scroll"));
  assert.equal($("#brief-check").parent, $("#chat-scroll"));
  assert.doesNotMatch(fs.readFileSync(path.join(demo, "app.js"), "utf8"), /children\.at\(/);
  assert.ok(sourceHtml.indexOf('id="route-summary"') < sourceHtml.indexOf('id="route-tools"'));
  assert.equal($("#discuss-reasoning").parent, $("#framing-next").parent);
  assert.doesNotMatch(sourceHtml, /Sends your reasoning and current Brief to ELM for feedback/);
  exampleOrder.forEach((id, index) => assert.ok(sourceHtml.includes(`data-example="${id}" aria-pressed="false"><b>Example ${index + 1}</b>`)));
  for (const [id, example] of Object.entries(examples)) {
    await $(`[data-example="${id}"]`).fire("click");
    assert.equal($("#problem").value, example.problem);
    assert.equal(vm.runInContext("task", context), null);
    assert.match($("#example-source").children[0].getAttribute("href"), /^https:/);
    const fields = vm.runInContext(`taskFields["${example.task}"]`, context);
    response = {task: example.task, reason: "Requested output determines this task.", tags: [],
      fields: Object.fromEntries(fields.map(([field]) => [field, "Unknown"])), reply: "Let's review these specs.",
      concepts: [{title: id + " concept", definition: "A specific definition", relevance: example.problem.slice(0, 80)}]};
    await $("#generate-brief").fire("click");
    assert.equal($('[data-step="2"]').getAttribute("aria-current"), "step");
    await $("#task-next").fire("click");
    assert.equal(vm.runInContext("problemConcepts[0].title", context), id + " concept");
    assert.ok($("#framing-lesson").children.some(node => node.tag === "blockquote"));
    for (const [field] of fields) {
      assert.ok(example.fields[field]?.length > 20, `Worked spec missing: ${field}`);
      assert.equal($("#" + field).value, example.fields[field]);
    }
    assert.ok(example.provenance.length >= 2);
    response.fields = {...example.fields};
    $("#reasoning-note").value = "Does random assignment mean everyone received treatment?";
    await $("#discuss-reasoning").fire("click");
    assert.match(requestBody.message, /Does random assignment/);
    assert.match(requestBody.context, /Does random assignment/);
    assert.equal(vm.runInContext("proposals.length", context), 0);
    for (const [field] of fields) assert.equal($("#" + field).value, example.fields[field]);
    if (example.task === "policy") assert.match(vm.runInContext("recommendDestination().title", context), /Dynamic-treatment/);
    if (example.task === "mediation") assert.match(vm.runInContext("recommendDestination().title", context), /Mediation specialist/);
    const firstSpec = fields[0][0];
    $("#" + firstSpec).value = "Unknown";
    assert.match(vm.runInContext("recommendDestination().title", context), /ChatGPT/);
    $("#" + firstSpec).value = example.fields[firstSpec];
    assert.equal($('[data-step="2.5"]').getAttribute("aria-current"), "step");
    await $("#framing-next").fire("click");
    assert.match($("#check-question").textContent, /Item 1\//);
    await $("#check-pause").fire("click");
    await $("#check-confirm").fire("click");
    assert.equal(vm.runInContext("briefCheck.index", context), 0);
    await $("#check-pause").fire("click");
    for (const [field] of fields) {
      assert.ok(vm.runInContext(`NirvanaGuidance.help["${field}"]`, context).length > 50);
      await $("#check-skip").fire("click");
    }
    assert.match($("#check-question").textContent, /Review pass finished/);
    await $("#check-confirm").fire("click");
    assert.equal(vm.runInContext("briefCheck.index", context), fields.length);
    assert.equal($("#check-start").disabled, false);
    assert.doesNotMatch($(`#${example.task}-fields`).className, /hidden/);
    await $('[data-next="4"]').fire("click");
    assert.match($("#route-tools").innerHTML, /Inputs needed:|Inputs needed/);
    assert.match($("#route-tools").innerHTML, /ChatGPT or Claude/);
    const destinations = vm.runInContext(`NirvanaDestinations["${example.task}"]`, context);
    assert.ok(!destinations.some(item => item.name === vm.runInContext("recommendDestination().title", context)));
    if (["descriptive", "prediction"].includes(example.task)) assert.equal($("#route-summary-title").textContent, "Is causality needed here?");
    for (const destination of destinations) {
      assert.ok($("#route-tools").innerHTML.includes(destination.url));
      for (const field of destination.fields) assert.ok(fields.some(([id]) => id === field));
    }
    for (const [field] of fields) assert.ok(vm.runInContext("currentHandoff()", context).includes(example.fields[field]));
    assert.match(vm.runInContext("currentHandoff()", context), /Suggested next workspace:/);
    assert.equal($("#copy-handoff").disabled, false);
    assert.ok($("#route-summary").textContent.length > 50);
    assert.equal($(example.task === "effect" ? "#cf-target" : "#exposure").value, "");
    // Resolve a multi-field batch out of review order, editing before Accept.
    await $("#check-start").fire("click");
    const [first, second] = fields;
    response = {...response, review: {field_id: fields.at(-1)[0], question: "Which uncertainty should we examine next?"}, fields: {...response.fields,
      [first[0]]: "Proposed first", [second[0]]: "Proposed second"}};
    $("#agent-message").value = "Please refine these two specifications.";
    await $("#agent-form").fire("submit");
    assert.match($("#check-question").textContent, /proposed edits above first/);
    const firstCard = $("#brief-proposals").children[0];
    const editor = firstCard.children.find(node => node.tag === "textarea");
    editor.value = 'User edited "exact" value';
    await editor.fire("input");
    assert.equal($("#" + first[0]).value, example.fields[first[0]]);
    await firstCard.children.find(node => node.textContent === "Accept").fire("click");
    assert.equal($("#" + first[0]).value, 'User edited "exact" value');
    assert.equal(vm.runInContext("briefCheck.index", context), 0);
    await $("#brief-proposals").children[0].children.find(node => node.textContent === "Reject").fire("click");
    assert.equal($("#" + second[0]).value, example.fields[second[0]]);
    assert.equal(vm.runInContext("briefCheck.index", context), fields.length - 1);
    assert.match($("#check-question").textContent, /Which uncertainty should we examine next/);
    await $("#check-confirm").fire("click");
    assert.equal(vm.runInContext("briefCheck.index", context), 2);
    for (let index = 2; index < fields.length - 1; index++) await $("#check-skip").fire("click");
    assert.match($("#check-question").textContent, /Review pass finished/);
  }
});

class Element {
  constructor(tag = "root", attributes = {}) {
    this.tag = tag;
    this.attributes = attributes;
    this.children = [];
    this.listeners = {};
    this.dataset = {};
    this.style = {};
    this.value = attributes.value || "";
    this.textContent = "";
    this.innerHTML = "";
    this.disabled = "disabled" in attributes;
    Object.entries(attributes).forEach(([key, value]) => {
      if (key.startsWith("data-")) this.dataset[key.slice(5)] = value;
    });
    this.className = attributes.class || "";
    this.classList = {
      toggle: (name, enabled) => {
        const names = new Set(this.className.split(/\s+/).filter(Boolean));
        if (enabled) names.add(name); else names.delete(name);
        this.className = [...names].join(" ");
      },
      add: (name) => this.classList.toggle(name, true),
      remove: (name) => this.classList.toggle(name, false),
    };
  }
  append(...children) { children.forEach((child) => { child.parent = this; this.children.push(child); }); }
  replaceChildren() { this.children = []; }
  setAttribute(key, value) { this.attributes[key] = value; }
  getAttribute(key) { return this.attributes[key] ?? null; }
  removeAttribute(key) { delete this.attributes[key]; }
  addEventListener(event, handler) { (this.listeners[event] ||= []).push(handler); }
  async fire(event, details = {}) { for (const handler of this.listeners[event] || []) await handler({ preventDefault() {}, ...details }); }
  focus() {}
}

function parseDocument(html) {
  const root = new Element();
  const stack = [root];
  for (const token of html.match(/<[^>]+>|[^<]+/g)) {
    if (token.startsWith("<!")) continue;
    if (token.startsWith("</")) { stack.pop(); continue; }
    if (!token.startsWith("<")) {
      const parent = stack.at(-1);
      if (parent.tag === "textarea") parent.value += token;
      continue;
    }
    const tag = token.match(/^<(\w+)/)?.[1];
    if (!tag) continue;
    const attrs = {};
    for (const match of token.matchAll(/([\w-]+)="([^"]*)"/g)) attrs[match[1]] = match[2];
    if (/\sdisabled(?:\s|>)/.test(token)) attrs.disabled = "";
    const node = new Element(tag, attrs);
    stack.at(-1).append(node);
    if (!["meta", "link", "input", "br", "hr"].includes(tag)) stack.push(node);
  }
  const descendants = (node) => node.children.flatMap((child) => [child, ...descendants(child)]);
  const matches = (node, selector) => {
    const id = selector.match(/^#([\w-]+)/)?.[1];
    const cls = selector.replace(/\[[^\]]*\]/g, "").match(/\.([\w-]+)/)?.[1];
    const tag = selector.match(/^[a-z]+/)?.[0];
    const attrs = [...selector.matchAll(/\[([\w-]+)(?:="([^"]*)")?\]/g)];
    return (!id || node.attributes.id === id) && (!cls || node.className.split(/\s+/).includes(cls)) &&
      (!tag || node.tag === tag) && attrs.every(([, key, value]) => {
        const actual = key.startsWith("data-") ? node.dataset[key.slice(5)] : node.attributes[key];
        return value === undefined ? actual !== undefined : actual === value;
      });
  };
  root.querySelectorAll = (selector) => selector.split(",").flatMap((part) => {
    const steps = part.trim().split(/\s+/);
    return steps.reduce((parents, step) => parents.flatMap(descendants).filter((node) => matches(node, step)), [root]);
  });
  root.querySelector = (selector) => root.querySelectorAll(selector)[0] || null;
  root.createElement = (tag) => new Element(tag);
  return root;
}

test("API configuration preserves the local demo and supports same-origin deployment", async () => {
  const demo = path.join(__dirname, "..", "demo");
  const html = fs.readFileSync(path.join(demo, "index.html"), "utf8");
  assert.ok(html.indexOf('src="config.js"') < html.indexOf('src="app.js"'));
  for (const configuration of [undefined, "", "/nirvana/api", "https://unexpected.invalid/api"]) {
    const document = parseDocument(html);
    const requests = [];
    const context = vm.createContext({
      document, AbortController, setTimeout, clearTimeout, TextEncoder,
      window: { location: { hostname: "demo.example", protocol: "https:", port: "9090" }, scrollTo() {} },
      navigator: { clipboard: { async writeText() {} } },
      fetch: async (url) => {
        requests.push(url);
        return {ok: true, json: async () => ({task: "effect", reason: "Test", fields: {}, reply: "Ready", concepts: []})};
      },
    });
    for (const script of ["markdown.js", "guidance.js", "destinations.js", "worked-examples.js", "config.js"]) {
      vm.runInContext(fs.readFileSync(path.join(demo, script), "utf8"), context);
    }
    assert.equal(context.window.NIRVANA_API_BASE, "");
    context.window.NIRVANA_API_BASE = configuration;
    vm.runInContext(fs.readFileSync(path.join(demo, "app.js"), "utf8"), context);
    document.querySelector("#problem").value = "Would study support improve learning?";
    await document.querySelector("#generate-brief").fire("click");
    if (configuration === "https://unexpected.invalid/api") {
      assert.deepEqual(requests, []);
      assert.match(document.querySelector("#generation-status").textContent, /NIRVANA_API_BASE must be/);
      assert.equal(document.querySelector("#generate-brief").disabled, false);
      continue;
    }
    document.querySelector("#agent-message").value = "Please explain the comparator.";
    await document.querySelector("#agent-form").fire("submit");
    const base = configuration || "http://demo.example:8011/api";
    assert.deepEqual(requests, [`${base}/classify`, `${base}/frame`, `${base}/frame`]);
  }
});

test("Brief state, synthetic isolation, confirmation and in-flight chat reset", async () => {
  const demo = path.join(__dirname, "..", "demo");
  const document = parseDocument(fs.readFileSync(path.join(demo, "index.html"), "utf8"));
  const copied = [];
  let resolveReply;
  let requestOptions;
  const context = vm.createContext({
    document, AbortController, setTimeout, clearTimeout, TextEncoder,
    window: { innerWidth: 1200, innerHeight: 900, location: { hostname: "127.0.0.1" }, scrollTo() {} },
    navigator: { clipboard: { async writeText(text) { copied.push(text); } } },
    fetch: (_url, options) => { requestOptions = options; return new Promise((resolve) => { resolveReply = resolve; }); },
  });
  vm.runInContext(fs.readFileSync(path.join(demo, "markdown.js"), "utf8"), context);
  vm.runInContext(fs.readFileSync(path.join(demo, "guidance.js"), "utf8"), context);
  vm.runInContext(fs.readFileSync(path.join(demo, "destinations.js"), "utf8"), context);
  vm.runInContext(fs.readFileSync(path.join(demo, "worked-examples.js"), "utf8"), context);
  vm.runInContext(fs.readFileSync(path.join(demo, "app.js"), "utf8"), context);
  const $ = (selector) => document.querySelector(selector);
  vm.runInContext("resizeChat(600, 500)", context);
  assert.equal($("#framing-chat").style.width, "600px");
  assert.equal($("#framing-chat").style.height, "500px");
  vm.runInContext("resizeChat(9000, 9000)", context);
  assert.equal($("#framing-chat").style.width, "1152px");
  assert.equal($("#framing-chat").style.height, "788px");
  vm.runInContext("resizeChat(1, 1)", context);
  assert.equal($("#framing-chat").style.width, "300px");
  assert.equal($("#framing-chat").style.height, "320px");
  const preview = () => $("#route-content").innerHTML;
  const change = async (selector, value) => { $(selector).value = value; await $(selector).fire("input"); };
  // Legacy synthetic worksheet fixtures exercise state transitions independently
  // of the published examples, which now all load question-only.
  const loadFixture = (task) => vm.runInContext(`
    startOwnQuestion();
    $("#problem").value = "Synthetic ${task} test question";
    updateTask("${task}");
    taskFields[task].forEach(([id]) => { $("#" + id).value = initialValues.get(id); });
    fieldsProblem = $("#problem").value;
    selectedExample = "test-fixture";
    briefChanged();
    renderBrief();
    framingReviewed = true;
  `, context);

  const markdownProblem = "## Research question\n\nCan **causality** help?\n\n- Scanner shifts\n- Demographics";
  await change("#problem", markdownProblem);
  await $("#problem-preview-toggle").fire("click");
  assert.match($("#problem-preview").innerHTML, /<h2>Research question<\/h2>/);
  assert.match($("#problem-preview").innerHTML, /<strong>causality<\/strong>/);
  assert.match($("#problem").className, /hidden/);
  assert.equal($("#problem").value, markdownProblem);
  await $("#problem-edit").fire("click");
  assert.equal($("#problem").value, markdownProblem);
  assert.match($("#problem-preview").className, /hidden/);
  await $('[data-action="reset"]').fire("click");

  assert.equal($("#problem").value, "");
  assert.equal($("#chat-toggle").getAttribute("aria-expanded"), "false");
  await $("#chat-toggle").fire("click");
  assert.equal($("#chat-toggle").getAttribute("aria-expanded"), "true");
  assert.doesNotMatch($("#framing-chat").className, /hidden/);
  assert.equal($("#chat-expand"), null);
  await $("#chat-close").fire("click");
  assert.match($("#framing-chat").className, /hidden/);
  assert.equal($("#assumptions").value, "");
  assert.equal($("#confirm-brief").disabled, true);
  await $('[data-step="4"]').fire("click");
  assert.equal($('[data-step="2"]').attributes["aria-current"], "step");

  loadFixture("effect");
  assert.match($("#outcome").value, /readmission/);
  assert.equal($("#prediction-target").value, "");
  await $('[data-step="4"]').fire("click");
  assert.match(preview(), /Draft: not yet reviewed/);
  assert.equal($("#copy-handoff").disabled, false);
  await $("#copy-handoff").fire("click");
  assert.equal(copied.length, 1);
  assert.match(copied[0], /Draft: not yet reviewed/);

  // The sidebar and main editor must use the same state transition.
  await change('[data-bind="problem"]', "Do free bus passes increase weekly journeys?");
  assert.equal($("#outcome").value, "");
  assert.equal($('[data-bind="assumptions"]').value, "");
  assert.doesNotMatch(preview(), /RapidTrack|readmission|No unmeasured confounding/);
  await change('[data-bind="outcome"]', "Weekly bus journeys <not admissions>");
  assert.match(preview(), /Weekly bus journeys &lt;not admissions&gt;/);
  await $("#confirm-brief").fire("click");
  assert.equal($("#copy-handoff").disabled, false);
  await $("#copy-handoff").fire("click");
  const previewText = preview().match(/<div class="prompt-preview">([\s\S]*?)<\/div>/)[1]
    .replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&");
  assert.equal(copied[1], previewText);
  assert.match(copied[1], /User reviewed this Brief/);
  await change("#outcome", "Monthly journeys");
  assert.equal($("#copy-handoff").disabled, false);
  assert.match(preview(), /Monthly journeys/);
  assert.match($("#brief-status").textContent, /^DRAFT/);

  await $("#confirm-brief").fire("click");
  await $('[data-task="shift"]').fire("click");
  assert.equal($("#problem").value, "Do free bus passes increase weekly journeys?");
  assert.equal($("#outcome").value, "");
  assert.equal($("#prediction-target").value, "");
  assert.equal($("#copy-handoff").disabled, false);
  assert.match($("#route-tools").innerHTML, /href="https:\/\/chai-uk.github.io\/domain-generalization-copilot\/"/);
  assert.match(preview(), /no automatic import or prompt-paste integration/);

  loadFixture("shift");
  $("#agent-message").value = "Explain scanner changes.";
  const pending = $("#agent-form").fire("submit");
  assert.match(requestOptions.body, /Scanner A/);
  loadFixture("mediation");
  assert.equal(requestOptions.signal.aborted, true);
  resolveReply({ ok: true, async json() { return { reply: "Old scanner response" }; } });
  await pending;
  assert.equal($("#agent-messages").children.length, 1);
  const welcome = $("#agent-messages").children[0];
  assert.equal(welcome.className, "agent-message assistant");
  assert.equal(welcome.children[0].src, "assets/nirvana-mascot.png");
  assert.match(welcome.children[2].innerHTML, /Hi, I'm Nirvana!/);
  assert.match(welcome.children[2].innerHTML, /field in your Brief/);
  assert.equal(vm.runInContext("chat.length", context), 0);
  assert.equal($("#agent-message").disabled, false);
  assert.equal($("#prediction-target").value, "");
  assert.match($("#mediator").value, /adherence/);

  loadFixture("descriptive");
  assert.equal($("#mediator").value, "");
  assert.match(preview(), /Descriptive analysis brief/);
  await $('[data-action="reset"]').fire("click");
  assert.equal($("#problem").value, "");
  assert.equal($("#descriptive-purpose").value, "");
  assert.equal($("#copy-handoff").disabled, true);
  // New natural-language input calls extraction without leaking example context.
  await change("#problem", "Can free bus passes increase weekly bus journeys?");
  const generation = $("#generate-brief").fire("click");
  assert.equal($('[data-step="2"]').attributes["aria-current"], "step");
  assert.equal($("#task-next").disabled, true);
  assert.match($("#task-status").textContent, /Nirvana is categorising/);
  assert.equal($("#chat-toggle").getAttribute("aria-expanded"), "false");
  assert.match(requestOptions.body, /Classify this new question/);
  assert.doesNotMatch(requestOptions.body, /RapidTrack|Scanner A/);
  resolveReply({ok: true, async json() { return {task: "effect", reason: "An intervention contrast."}; }});
  await new Promise(setImmediate);
  assert.equal($("#task-next").disabled, false);
  assert.match($("#draft-status").textContent, /Preparing Brief/);
  assert.equal(JSON.parse(requestOptions.body).selected_task, "effect");
  resolveReply({ ok: true, async json() { return {
    task: "effect", fields: { exposure: "Free bus passes", outcome: "Weekly bus journeys" }, reply: "What is the comparison?"
  }; } });
  await generation;
  assert.equal($("#chat-toggle").getAttribute("aria-expanded"), "false");
  assert.equal($('[data-step="2"]').attributes["aria-current"], "step");
  assert.equal($('[data-task="effect"]').style.order, "-1");
  assert.equal($("#task-next").disabled, false);
  await $('[data-step="3"]').fire("click");
  assert.equal($('[data-step="2"]').attributes["aria-current"], "step");
  await $("#task-next").fire("click");
  assert.equal($('[data-step="2.5"]').attributes["aria-current"], "step");
  await $('[data-step="4"]').fire("click");
  assert.equal($('[data-step="2.5"]').attributes["aria-current"], "step");
  await $("#framing-next").fire("click");
  assert.equal($('[data-step="3"]').attributes["aria-current"], "step");
  assert.doesNotMatch(preview(), /revision|R\d/);
  assert.equal($("#brief-status").textContent, "DRAFT");
  assert.equal($("#outcome").value, "Weekly bus journeys");
  const temporaryShift = $('[data-task="shift"]').fire("click");
  const temporaryShiftReply = resolveReply;
  assert.equal($("#outcome").value, "");
  await $('[data-task="effect"]').fire("click");
  temporaryShiftReply({ok: true, async json() { return {task: "shift", fields: {}, reply: "Obsolete"}; }});
  await temporaryShift;
  assert.equal($("#outcome").value, "Weekly bus journeys");
  assert.equal($("#comparator").value, "");
  assert.match(preview(), /Weekly bus journeys/);
  assert.equal($("#copy-handoff").disabled, false);
  $("#agent-message").value = "Full-price passes";
  const previousRequest = requestOptions;
  for (const details of [{key: "Enter"}, {key: "Enter", shiftKey: true}, {key: "Enter", ctrlKey: true, isComposing: true}]) {
    await $("#agent-message").fire("keydown", {...details, preventDefault() { assert.fail("Native newline/composition must be preserved"); }});
    assert.equal(requestOptions, previousRequest);
  }
  const followup = $("#agent-message").fire("keydown", {key: "Enter", ctrlKey: true});
  assert.notEqual(requestOptions, previousRequest);
  assert.match(requestOptions.body, /Weekly bus journeys/);
  resolveReply({ ok: true, async json() { return {
    task: "effect", fields: { exposure: "Free bus passes", outcome: "Weekly bus journeys", comparator: "Full-price passes", population: "[unknown / not provided]" }, reply: "Suggested comparison below."
  }; } });
  await followup;
  assert.equal($("#brief-proposals").children.length, 1);
  const proposalRequest = requestOptions;
  await $("#agent-message").fire("keydown", {key: "Enter", ctrlKey: true});
  assert.equal(requestOptions, proposalRequest);
  assert.equal($("#comparator").value, "");
  assert.doesNotMatch(preview(), /Full-price passes/);
  await $("#copy-handoff").fire("click");
  assert.doesNotMatch(copied.at(-1), /Full-price passes/);
  const editableProposal = $("#brief-proposals").children[0].children.find((node) => node.tag === "textarea");
  assert.equal(editableProposal.maxLength, 2000);
  editableProposal.value = "Full-price passes (usual care)";
  await editableProposal.fire("input");
  assert.equal($("#comparator").value, "");
  editableProposal.value = "Full-price passes";
  await editableProposal.fire("input");
  await $("#brief-proposals").children[0].children.find((node) => node.textContent === "Accept").fire("click");
  assert.equal($("#comparator").value, "Full-price passes");
  assert.equal($("#agent-messages").children.length, 3);
  const acceptedNotice = $("#agent-messages").children.at(-1);
  assert.equal(acceptedNotice.className, "chat-decision");
  assert.match(acceptedNotice.textContent, /Accepted · Comparator/);
  assert.match(acceptedNotice.textContent, /Still to clarify:/);
  assert.doesNotMatch(acceptedNotice.textContent, /JSON|Keep this field|Full-price passes/);
  assert.equal($("#agent-messages").children.at(-2).className, "agent-message assistant");
  await $("#chat-close").fire("click");
  await $("#chat-toggle").fire("click");
  assert.equal($("#agent-messages").children.length, 3);
  assert.match(preview(), /Full-price passes/);
  $("#agent-message").value = "What about a different outcome?";
  const suggestion = $("#agent-form").fire("submit");
  const decisionHistory = JSON.parse(requestOptions.body).history.at(-1);
  assert.equal(decisionHistory.role, "user");
  assert.match(decisionHistory.text, /Keep this field exactly as this JSON string: "Full-price passes"/);
  assert.equal(decisionHistory.displayText, undefined);
  resolveReply({ok: true, async json() { return {task: "effect", fields: {exposure: "Free bus passes", outcome: "Monthly journeys", comparator: "Full-price passes"}, reply: "One possible change is below."}; }});
  await suggestion;
  await $("#brief-proposals").children[0].children.find((node) => node.textContent === "Reject").fire("click");
  assert.equal($("#outcome").value, "Weekly bus journeys");
  assert.equal($("#brief-proposals").children.length, 0);
  const rejectedNotice = $("#agent-messages").children.at(-1);
  assert.equal(rejectedNotice.className, "chat-decision");
  assert.match(rejectedNotice.textContent, /Rejected · Outcome \(original kept\)/);
  assert.doesNotMatch(rejectedNotice.textContent, /JSON|Monthly journeys/);
  $("#agent-message").value = "Keep the existing comparison.";
  const beforeFailedChat = vm.runInContext("chat.length", context);
  const failed = $("#agent-form").fire("submit");
  resolveReply({ ok: false, async json() { return { error: "ELM unavailable" }; } });
  await failed;
  assert.equal($("#comparator").value, "Full-price passes");
  assert.equal($("#agent-message").value, "Keep the existing comparison.");
  assert.match($("#agent-status").textContent, /ELM unavailable/);
  assert.equal($("#generate-brief").disabled, false);
  assert.equal(vm.runInContext("chat.length", context), beforeFailedChat);
  const retainedFields = vm.runInContext("Object.fromEntries(taskFields[task].map(([id]) => [id, $('#'+id).value]))", context);
  const retried = $("#agent-form").fire("submit");
  const retriedBody = JSON.parse(requestOptions.body);
  assert.equal(retriedBody.message, "Keep the existing comparison.");
  assert.ok(!retriedBody.history.some(entry => entry.role === "user" && entry.text === retriedBody.message));
  resolveReply({ok: true, async json() { return {task: "effect", fields: retainedFields, reply: "Your comparison is retained."}; }});
  await retried;
  assert.equal(vm.runInContext("chat.length", context), beforeFailedChat + 2);
  const beforeExample = requestOptions;
  await $('[data-example="ctpa"]').fire("click");
  assert.match($("#problem").value, /synthesize the non-contrast CTPA from the contrast CTPA/);
  assert.equal($("#prediction-target").value, "");
  assert.equal($("#outcome").value, "");
  assert.equal($("#task-next").disabled, true);
  assert.equal($("#source-status"), null);
  assert.equal(requestOptions, beforeExample);
  $("#problem").value = "Help me plan a literature search about hospital staffing.";
  await $("#problem").fire("input");
  await $('[data-task="other"]').fire("click");
  await $("#task-next").fire("click");
  assert.equal($('[data-step="4"]').getAttribute("aria-current"), "step");
  assert.equal($("#route-summary-title").textContent, "Scope and next steps");
  assert.match($("#route-tools").innerHTML, /domain expert.*ChatGPT \/ Claude/);
  assert.doesNotMatch($("#route-tools").innerHTML, /Other workspaces|DAGitty|DoWhy|Copilot/);
  assert.equal($("#copy-handoff").disabled, false);
  await $("#copy-handoff").fire("click");
  assert.match(copied.at(-1), /Help me plan a literature search about hospital staffing/);
  assert.match(copied.at(-1), /Do not force the question into a causal task/);
  assert.doesNotMatch(copied.at(-1), /Full-price passes|Medicaid|CTPA/);
  await $('[data-task="effect"]').fire("click");
  assert.equal($("#route-summary-title").textContent, "Where causality can be applied");
  assert.doesNotMatch($("#route-guidance").className, /hidden/);
  // Task confirmation is independent of a delayed draft; stale replies cannot
  // overwrite a newly selected task, and a draft failure has its own retry.
  await change("#problem", "Will this model transfer to a different hospital?");
  const splitGeneration = $("#generate-brief").fire("click");
  resolveReply({ok: true, async json() { return {task: "effect", reason: "Test initial classification"}; }});
  await new Promise(setImmediate);
  const oldDraftReply = resolveReply;
  const oldDraftRequest = requestOptions;
  assert.equal($("#task-next").disabled, false);
  await $("#task-next").fire("click");
  assert.equal($('[data-step="2.5"]').getAttribute("aria-current"), "step");
  const replacement = $('[data-task="shift"]').fire("click");
  assert.equal(oldDraftRequest.signal.aborted, true);
  assert.equal(JSON.parse(requestOptions.body).selected_task, "shift");
  oldDraftReply({ok: true, async json() { return {task: "effect", fields: {outcome: "STALE"}, reply: "Old result"}; }});
  await splitGeneration;
  assert.equal(vm.runInContext("task", context), "shift");
  assert.equal($("#outcome").value, "");
  resolveReply({ok: false, async json() { return {error: "Draft service unavailable"}; }});
  await replacement;
  assert.equal(vm.runInContext("draftState", context), "error");
  assert.equal(vm.runInContext("task", context), "shift");
  const retryDraft = $("#retry-draft").fire("click");
  assert.equal(JSON.parse(requestOptions.body).selected_task, "shift");
  resolveReply({ok: true, async json() { return {task: "shift", fields: {"prediction-target": "Hospital outcome"}, reply: "Ready", concepts: []}; }});
  await retryDraft;
  assert.equal(vm.runInContext("draftState", context), "ready");
  assert.equal($('[data-step="2.5"]').getAttribute("aria-current"), "step");
  assert.equal($("#prediction-target").value, "Hospital outcome");
  await $('[data-action="reset"]').fire("click");
});

test("Field and aggregate limits preserve drafts and budget only sent history", async () => {
  const demo = path.join(__dirname, "..", "demo");
  const document = parseDocument(fs.readFileSync(path.join(demo, "index.html"), "utf8"));
  const requests = [];
  const context = vm.createContext({
    document, AbortController, setTimeout, clearTimeout, TextEncoder,
    window: {location: {hostname: "127.0.0.1"}, scrollTo() {}},
    navigator: {clipboard: {async writeText() {}}},
    fetch: async (_url, options) => {
      requests.push(JSON.parse(options.body));
      return {ok: true, json: async () => ({task: "effect", fields: {}, reply: "A short conceptual reply."})};
    },
  });
  for (const name of ["markdown.js", "guidance.js", "destinations.js", "worked-examples.js", "app.js"]) {
    vm.runInContext(fs.readFileSync(path.join(demo, name), "utf8"), context);
  }
  const $ = selector => document.querySelector(selector);
  $("#problem").value = "A fictional study-support question.";
  vm.runInContext('updateTask("effect")', context);
  for (const id of ["problem", "outcome", "assumptions"]) {
    assert.equal($("#" + id).maxLength, 2000);
    assert.equal($(`[data-bind="${id}"]`).maxLength, 2000);
  }
  assert.ok($("#brief-field-limit"));
  const fields = vm.runInContext("taskFields[task].map(([id]) => id)", context);
  async function send() {
    $("#agent-message").value = "Please explain the idea.";
    await $("#agent-form").fire("submit");
    assert.equal($("#agent-message").disabled, false);
  }
  // Imported/programmatic content can exceed native maxlength. Never cut it.
  $("#assumptions").value = "x".repeat(2001);
  await send();
  assert.equal(requests.length, 0);
  assert.equal($("#assumptions").value.length, 2001);
  assert.equal($("#agent-message").value, "Please explain the idea.");
  assert.match($("#agent-status").textContent, /2,000-character field limit/);
  assert.equal(vm.runInContext("chat.length", context), 0);

  fields.forEach(id => { $("#" + id).value = "x".repeat(2000); });
  $("#reasoning-note").value = "r".repeat(2000);
  await send();
  assert.equal(requests.length, 0);
  assert.match($("#agent-status").textContent, /16,000-character context limit/);
  assert.match($("#agent-status").textContent, /Your draft is unchanged/);
  assert.equal($("#reasoning-note").value.length, 2000);
  fields.forEach(id => assert.equal($("#" + id).value.length, 2000));

  $("#reasoning-note").value = "";
  fields.forEach(id => { $("#" + id).value = "文".repeat(2000); });
  await send();
  assert.equal(requests.length, 0);
  assert.match($("#agent-status").textContent, /32 KB request limit/);
  assert.match($("#agent-status").textContent, /Your draft is unchanged/);
  fields.forEach(id => assert.equal($("#" + id).value, "文".repeat(2000)));

  fields.forEach(id => { $("#" + id).value = ""; });
  vm.runInContext('for (let index = 0; index < 12; index++) chat.push({role: index % 2 ? "assistant" : "user", text: String(index) + "x".repeat(3990)})', context);
  await send();
  assert.equal(requests.length, 1);
  assert.ok(requests[0].history.length < 12);
  assert.ok(new TextEncoder().encode(JSON.stringify(requests[0])).length <= 32768);
  assert.equal(vm.runInContext("chat.length", context), 14);
  assert.match($("#agent-status").textContent, /Earlier discussion messages were omitted/);
  assert.match($("#agent-status").textContent, /full on-screen discussion are unchanged/);
});

test("Plain field help preserves environment and same-case distinctions", () => {
  const {help} = require("../demo/guidance.js");
  assert.match(help["training-environment"], /not your GPU, Python environment, operating system or training framework/);
  assert.match(help["deployment-environment"], /not the server hosting the model/);
  assert.match(help["cf-target"], /same case/);
  assert.doesNotMatch([help["training-environment"], help["deployment-environment"], help["cf-target"]].join(" "), /\b(?:DATA|NOT|SAME)\b/);
});
