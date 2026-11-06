"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");
const ts = require("typescript");

const source = fs.readFileSync(path.join(__dirname, "../web/src/App.tsx"), "utf8");
const parsed = ts.createSourceFile("App.tsx", source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
const element = (type, props, ...children) => ({type, props:props || {}, children:children.flat()});
const edgeKey = edge => `${edge.parent_id}->${edge.child_id}`;
const graph = [{parent_id:"rain", child_id:"umbrella"}, {parent_id:"rain", child_id:"wet"}];
const observation = [{umbrella_carried:"yes", pavement_wet:"yes", arrivals:72},
  {umbrella_carried:"no", pavement_wet:"no", arrivals:144}];
const hypothesisRecords = [{umbrella_carried:"yes", pavement_wet:"yes", arrivals:240}];
const referenceRecords = [{umbrella_carried:"yes", pavement_wet:"yes", arrivals:96},
  {umbrella_carried:"yes", pavement_wet:"no", arrivals:144}];

function scene(phase = "records", overrides = {}) {
  const simulation = {kind:"umbrella_scm", model_version:"1.0.0", selected_hypothesis_id:null,
    hypotheses:[
      {hypothesis_id:"common", label:"A common cause", mechanism:"An explicit common-cause mechanism.", edges:graph},
      {hypothesis_id:"direct", label:"Umbrellas influence pavement", mechanism:"An explicit direct mechanism.", edges:[graph[0]]},
      {hypothesis_id:"reverse", label:"Pavement influences umbrellas", mechanism:"An explicit reverse mechanism.", edges:[graph[1]]},
    ], runs:[], minimum_hypotheses:2, distinct_hypotheses_tried:0, ready_for_revision:false,
    reference_assumptions:null, reference_edges:null, ...overrides.simulation};
  return {scene_id:"umbrella", title:"An umbrella experiment", phase, revision:0, graph_edges:[],
    prediction_id:null, intervention_action_id:null, reflection:null, evidence_status:null,
    nodes:[{node_id:"rain", label:"Rain"}, {node_id:"umbrella", label:"Umbrella carrying"}, {node_id:"wet", label:"Wet pavement"}],
    permitted_edges:graph, observed_records:observation,
    predictions:[{prediction_id:"same", label:"The wet count stays the same"}, {prediction_id:"more", label:"More pavement is wet"}],
    intervention:{action_id:"do-umbrella", variable_id:"umbrella", value:"yes", result_records:[]},
    resources:{hook:"What could explain the pattern?", records:"Recorded arrivals."},
    legal_action_kinds:["select_hypothesis"], ...overrides, simulation};
}

function render(current, {values = {}, canContinue = false, isWorking = false, share = async()=>true} = {}) {
  const declaration = parsed.statements.find(node => ts.isFunctionDeclaration(node) && node.name?.text === "DynamicUmbrellaWorkbench");
  const output = ts.transpileModule(declaration.getText(parsed), {
    compilerOptions:{jsx:ts.JsxEmit.React, module:ts.ModuleKind.CommonJS, target:ts.ScriptTarget.ES2022},
  });
  const actions = [], changes = [], checks = [], continuations = [];
  let cursor = 0;
  const context = vm.createContext({React:{createElement:element}, edgeKey, labelFromConceptId:id=>id,
    useState(initial) {const slot = cursor++; return [slot in values ? values[slot] : initial, value=>changes.push({slot,value})];},
    useEffect:()=>{}, CONTAINED_TABLE_STYLE:{}, proportional:n=>n,
    ...Object.fromEntries(["VStack", "HStack", "Text", "Heading", "Button", "RadioList", "RadioListItem",
      "SceneModelGraph", "SceneRecordsTable", "Collapsible", "Grid", "Table", "TextArea", "Banner", "CommitBar",
      "CheckboxList", "CheckboxListItem"].map(name=>[name,name])),
  });
  vm.runInContext(output.outputText, context);
  const tree = context.DynamicUmbrellaWorkbench({scene:current, simulation:current.simulation, isWorking, canContinue,
    onShareHypothesis:share, onSceneAction:value=>actions.push(value), onSubmitEvidence:()=>checks.push(true),
    onContinue:()=>continuations.push(true)});
  return {tree, actions, changes, checks, continuations};
}

function nodes(tree, predicate) {
  if (Array.isArray(tree)) return tree.flatMap(item=>nodes(item,predicate));
  if (!tree || typeof tree !== "object" || !("type" in tree)) return [];
  const slots = Object.values(tree.props).filter(value=>value && typeof value === "object");
  return [...(predicate(tree) ? [tree] : []), ...tree.children.flatMap(child=>nodes(child,predicate)),
    ...slots.flatMap(slot=>nodes(slot,predicate))];
}
const button = (page, label) => nodes(page.tree, node=>node.type === "Button" && node.props.label === label)[0];
const text = tree => !tree ? "" : Array.isArray(tree) ? tree.map(text).join(" ")
  : typeof tree === "object" ? text(tree.children || []) : String(tree);
const run = (id = 1) => ({run_id:id, hypothesis_id:"direct", hypothesis_label:"Umbrellas influence pavement",
  prediction_id:"more", hypothesis_edges:[graph[0]], hypothesis_result_records:hypothesisRecords,
  reference_result_records:referenceRecords, hypothesis_wet_pct:100, reference_wet_pct:40});

test("hypothesis selection has no assumed-correct default and saves only the declared hypothesis ID", () => {
  const initial = render(scene());
  assert.equal(nodes(initial.tree, node=>node.type === "RadioList")[0].props.value, "");
  assert.equal(button(initial,"Save hypothesis").props.isDisabled, true);
  assert.equal(nodes(initial.tree, node=>node.type === "SceneRecordsTable").length, 1);
  assert.doesNotMatch(text(initial.tree), /The reference-world assumptions/);
  const chosen = render(scene(), {values:{0:"reverse"}});
  assert.equal(button(chosen,"Save hypothesis").props.isDisabled, false);
  button(chosen,"Save hypothesis").props.onClick();
  assert.equal(JSON.stringify(chosen.actions), JSON.stringify([{kind:"select_hypothesis", hypothesis_id:"reverse"}]));
});

test("saving each prediction precedes running, and an unsaved hypothesis cannot use an old prediction", () => {
  const current = scene("model", {graph_edges:graph, legal_action_kinds:["select_hypothesis", "submit_prediction"],
    simulation:{selected_hypothesis_id:"common"}});
  const empty = render(current);
  assert.equal(button(empty,"Record my prediction").props.isDisabled,true);
  const guessed = render(current, {values:{1:"same"}});
  button(guessed,"Record my prediction").props.onClick();
  assert.equal(JSON.stringify(guessed.actions), JSON.stringify([{kind:"submit_prediction", prediction_id:"same"}]));
  const ready = scene("prediction", {prediction_id:"same", graph_edges:graph, legal_action_kinds:["run_intervention", "select_hypothesis"],
    simulation:{selected_hypothesis_id:"common"}});
  const changed = render(ready, {values:{0:"direct"}});
  assert.equal(button(changed,"Run intervention").props.isDisabled,true);
  const committed = render(ready);
  button(committed,"Run intervention").props.onClick();
  assert.equal(JSON.stringify(committed.actions), JSON.stringify([{kind:"run_intervention", intervention_action_id:"do-umbrella"}]));
});

test("calculated hypothesis and fixed reference records remain distinct and do not award completion", () => {
  const page = render(scene("comparison", {simulation:{selected_hypothesis_id:"direct", runs:[run()], distinct_hypotheses_tried:1}}));
  const tables = nodes(page.tree, node=>node.type === "SceneRecordsTable");
  assert.equal(tables.find(item=>item.props.label === "Calculated result from your hypothesis model").props.records,hypothesisRecords);
  assert.equal(tables.find(item=>item.props.label === "Calculated result from the independent reference world").props.records,referenceRecords);
  assert.match(text(page.tree), /Your hypothesis model/);
  assert.match(text(page.tree), /Independent reference world/);
  assert.match(text(page.tree).replace(/\s+/g," "), /1 hypothesis tested · at least 2 required/);
  assert.equal(button(page,"Record my explanation"),undefined);
  assert.equal(button(page,"Check my graph"),undefined);
});

test("server readiness and legal actions gate reconstruction while saved run history remains inspectable", () => {
  const ready = scene("comparison", {graph_edges:graph, legal_action_kinds:["select_hypothesis", "submit_revision"],
    simulation:{runs:[run(1),run(2)], distinct_hypotheses_tried:2, ready_for_revision:true,
      reference_assumptions:"Rain drives both variables in this supplied world.", reference_edges:graph}});
  const page = render(ready, {values:{3:"The reference stayed fixed while the hypothesis outcome changed."}});
  assert.match(text(page.tree), /The reference-world assumptions/);
  assert.equal(nodes(page.tree,node=>node.type === "Table")[0].props.data.length,2);
  button(page,"Record my explanation").props.onClick();
  assert.equal(page.actions[0].kind,"submit_revision");
  assert.equal(JSON.stringify(page.actions[0].edges),JSON.stringify(graph));
  assert.match(page.actions[0].reflection,/reference stayed fixed/);
  const denied = render({...ready, legal_action_kinds:["select_hypothesis"]});
  assert.equal(button(denied,"Record my explanation"),undefined);
});

test("the original evaluator and Continue retain final authority after dynamic practice", () => {
  const current = scene("revision", {graph_edges:graph, reflection:"The reference rules were supplied independently.", legal_action_kinds:["submit_revision"],
    simulation:{ready_for_revision:true, runs:[run(1),run(2)], distinct_hypotheses_tried:2,
      reference_assumptions:"Supplied rules.", reference_edges:graph}});
  const unchecked = render(current);
  button(unchecked,"Check my graph").props.onClick();
  assert.equal(unchecked.checks.length,1);
  assert.equal(unchecked.actions.length,0);
  const rejected = render({...current,evidence_status:"rejected"}, {values:{3:""}});
  assert.ok(button(rejected,"Save revised graph"));
  assert.equal(button(rejected,"Save revised graph").props.isDisabled,false);
  button(rejected,"Save revised graph").props.onClick();
  assert.equal(rejected.actions[0].reflection,current.reflection);
  const accepted = render(current,{canContinue:true});
  const continueBar = nodes(accepted.tree,node=>node.type === "CommitBar")[0];
  continueBar.props.onContinue();
  assert.equal(accepted.continuations.length,1);
  assert.equal(button(accepted,"Check my graph"),undefined);
});

test("pending actions stay above collapsed observations, prior runs and optional extra hypotheses", () => {
  const model = render(scene("model", {graph_edges:graph, legal_action_kinds:["select_hypothesis", "submit_prediction"],
    simulation:{selected_hypothesis_id:"common", runs:[run()]}}));
  for (const title of ["Review earlier run", "Review observed records"]) {
    const disclosure = nodes(model.tree,node=>node.type === "Collapsible" && text(node.props.trigger) === title)[0];
    assert.ok(disclosure,title);
    assert.equal(disclosure.props.defaultIsOpen,false);
  }
  const ready = render(scene("comparison", {legal_action_kinds:["select_hypothesis", "submit_revision"],
    simulation:{runs:[run(1),run(2),run(3)], distinct_hypotheses_tried:3, ready_for_revision:true,
      reference_assumptions:"Supplied rules.",reference_edges:graph}}));
  assert.match(text(ready.tree).replace(/\s+/g," "),/3 hypotheses tested · at least 2 required/);
  const chooser = nodes(ready.tree,node=>node.type === "Collapsible" && text(node.props.trigger) === "Try another hypothesis")[0];
  assert.equal(chooser.props.defaultIsOpen,false);
  assert.ok(button(ready,"Record my explanation"));
});

test("failed free-text sharing preserves the dynamic scene draft without a dialogue quota", async () => {
  const page = render(scene("hook", {legal_action_kinds:["open_records"]}),
    {values:{4:"Perhaps weather explains the two."},share:async()=>false});
  await button(page,"Discuss my idea with EducAgent").props.onClick();
  assert.equal(page.changes.length,0);
  assert.equal(button(page,"Discuss my idea with EducAgent").props.isDisabled,false);
});
