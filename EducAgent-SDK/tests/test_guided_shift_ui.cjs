"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");
const ts = require("typescript");

const source = fs.readFileSync(path.join(__dirname, "../web/src/App.tsx"), "utf8");
const parsed = ts.createSourceFile("App.tsx", source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
const declaration = name => parsed.statements.find(node => ts.isFunctionDeclaration(node) && node.name?.text === name);
const element = (type, props, ...children) => ({type, props:props || {}, children:children.flat()});
const nodes = (tree, predicate) => Array.isArray(tree) ? tree.flatMap(item=>nodes(item,predicate))
  : tree && typeof tree === "object" && "type" in tree
    ? [...(predicate(tree) ? [tree] : []), ...tree.children.flatMap(child=>nodes(child,predicate))] : [];
const text = tree => Array.isArray(tree) ? tree.map(text).join(" ")
  : tree && typeof tree === "object" ? text(tree.children ?? []) : tree == null ? "" : String(tree);

function snapshot(parameterId = "cue_accuracy_pct", overrides = {}) {
  const parameters = [
    {parameter_id:"cue_accuracy_pct",label:"Old broad wording",kind:"range",value:90,min:0,max:100,step:10,unit:"%"},
    {parameter_id:"flip_cue",label:"Another broad wording",kind:"toggle",value:false},
    {parameter_id:"measurement_error_pct",label:"Measurement error",kind:"range",value:10,min:0,max:50,step:10,unit:"%"},
    {parameter_id:"generator",label:"Generator",kind:"choice",value:"measured",options:[
      {option_id:"measured",label:"Write from the measurement"},{option_id:"withhold",label:"Withhold without context"}]},
  ];
  const config = {kind:"shift",cue_accuracy_pct:90,flip_cue:false,measurement_error_pct:10,generator:"measured",fixed:"keep this"};
  return {experiment_id:`guided.${parameterId}`,title:"A familiar rule in a new setting",instruction:"Legacy technical instructions.",
    phase:"configure",revision:0,config,parameters,prediction:null,reflection:null,runs:[],result:null,
    legal_actions:["commit_prediction"],can_submit_check:false,min_distinct_runs:2,distinct_runs:0,
    guide:{story:"A warehouse uses a label to predict damaged parcels.",goal:"Find whether the label rule travels to a new warehouse.",
      section:parameterId === "generator" ? "generation" : "prediction",parameter_id:parameterId,
      parameter_label:`Friendly ${parameterId}`,parameter_description:"Change only this setting. Other conditions stay fixed.",
      prediction_prompt:"What do you expect this test to show?",comparison_prompt:"What changed between the tests?",
      metrics:[{metric_label:"prediction accuracy",label:"Correct parcel predictions"}]},...overrides};
}
function effectSnapshot(parameterId = "analysis", profile = "general", overrides = {}) {
  const config={kind:"effect",assignment:"self_selected",target_high_pct:50,analysis:"pooled"};
  return {...snapshot(),experiment_id:`effect.${parameterId}`,title:"Compare two programme setups",config,
    parameters:[
      {parameter_id:"assignment",label:"Assignment",kind:"choice",value:"self_selected",options:[
        {option_id:"self_selected",label:"People choose their programme"},{option_id:"randomized",label:"Balanced random assignment"}]},
      {parameter_id:"target_high_pct",label:"Target population",kind:"range",value:50,min:0,max:100,step:10,unit:"%"},
      {parameter_id:"analysis",label:"Analysis",kind:"choice",value:"pooled",options:[
        {option_id:"pooled",label:"Compare the selected groups"},{option_id:"standardized",label:"Use the same population weights"}]},
    ],guide:{story:profile === "medical" ? "A rehabilitation service compares programmes for eligible patients." : "A college compares study-support programmes for eligible students.",
      goal:"Compare two setups while keeping other conditions fixed.",section:"intervention",parameter_id:parameterId,
      parameter_label:`Change ${parameterId}`,parameter_description:"Change just this setting and make a prediction.",
      prediction_prompt:"How will this programme comparison change?",comparison_prompt:"What did your two tests show?",
      metrics:[{metric_label:"Selected analysis contrast",label:"Programme A minus B"}]},...overrides};
}
const result = value => ({title:"A result",summary:"Do not mix report-generation discussion into prediction.",
  metrics:[{label:"prediction accuracy",value,display_value:`${value}%`},{label:"irrelevant",value:1,display_value:"1%"}],
  bars:[],tables:[],cases:[{case_id:1,source_text:"A source record.",generated_text:"A generated draft.",
    target:1,prediction:1,cue:1,measurement:1}]});
const run = (id,config,value=80) => ({run_id:id,config,prediction:`Prediction for ${id}`,result:result(value)});

function harness(initial, options = {}) {
  const layoutDeps = [],store=options.store ?? {draft:null};
  let layoutIndex = 0,effects = [],dirty = false;
  const actions = [], focus = [];
  const schedule = (store, callback, deps, index) => {
    if (!store[index] || deps.some((value,key)=>value !== store[index][key])) {
      store[index] = [...deps]; effects.push(callback);
    }
  };
  const context = vm.createContext({React:{createElement:element},READING_WIDTH:"68ch",SCRIPT_FOCUS_STYLE:{outline:"none"},
    CONTAINED_TABLE_STYLE:{overflowX:"auto"}, proportional:n=>n,
    ...Object.fromEntries(["VStack","HStack","Text","Heading","Button","Slider","CheckboxInput","Selector","TextArea","Collapsible","Table","ComparisonWorkbenchCanvas"].map(name=>[name,name])),
    useRef:()=>({current:{focus:value=>focus.push(value)}}),
    useLayoutEffect:(callback,deps)=>schedule(layoutDeps,callback,deps,layoutIndex++),
  });
  vm.runInContext(ts.transpileModule(`${declaration("guidedPracticeDraft").getText(parsed)}\n${declaration("GuidedExperimentWorkbench").getText(parsed)}`,{
    compilerOptions:{jsx:ts.JsxEmit.React,target:ts.ScriptTarget.ES2022},
  }).outputText,context);
  let current=initial, tree;
  const page = {actions,focus,store,render(next=current) {current=next;
    for (let tries=0;tries<4;tries++) {
      layoutIndex=0;effects=[];dirty=false;
      const scope=options.scope ?? `test.general.${current.experiment_id}`;
      tree=context.GuidedExperimentWorkbench({snapshot:current,draftState:context.guidedPracticeDraft(current,scope,store.draft),
        onDraftChange:changes=>{store.draft={...context.guidedPracticeDraft(current,scope,store.draft),...changes};dirty=true;},
        isWorking:false,isFrozen:false,
        onAction:action=>actions.push(JSON.parse(JSON.stringify(action))),...options});
      effects.forEach(effect=>effect());
      if (!dirty) break;
    }
    page.tree=tree; return page;
  }};
  return page.render();
}
const button = (page,label) => nodes(page.tree,node=>node.type === "Button" && node.props.label === label)[0];
const controls = page => nodes(page.tree,node=>["Slider","CheckboxInput","Selector"].includes(node.type));

test("the novice sees a complete story and task before any configuration or result", () => {
  for (const profile of ["general","medical"]) {
    const current=snapshot();current.guide.story=`The ${profile} story.`;
    const page=harness(current);
    assert.match(text(page.tree),new RegExp(`The ${profile} story`));
    assert.match(text(page.tree),/Your task:/);
    assert.equal(controls(page).length,0);
    assert.equal(nodes(page.tree,node=>node.type === "TextArea" || node.type === "Table").length,0);
    assert.ok(button(page,"Start practice"));
    assert.doesNotMatch(text(page.tree),/Legacy technical|generated draft|prediction accuracy/);
    button(page,"Start practice").props.onClick();page.render();
    assert.equal(controls(page).length,1);
    assert.equal(nodes(page.tree,node=>node.type === "TextArea")[0].props.label,current.guide.prediction_prompt);
    assert.equal(page.tree.props.width,"100%");assert.equal(page.tree.props.maxWidth,"68ch");
    assert.equal(nodes(page.tree,node=>node.type === "Heading" && node.props.level === 1).length,1,"the deferred question does not leave practice without a main heading");
    assert.equal(nodes(page.tree,node=>node.type === "Heading" && node.props.tabIndex === -1)[0].props.level,2);
    assert.ok(nodes(page.tree,node=>node.type === "Heading" && node.props.tabIndex === -1).length);
    assert.ok(page.focus.length,"opening a step provides a programmatic heading focus target");
  }
});

test("each practice exposes only its authored control while keeping other saved configuration intact", () => {
  for (const id of ["cue_accuracy_pct","flip_cue","measurement_error_pct","generator"]) {
    const current=snapshot(id),page=harness(current);
    button(page,"Start practice").props.onClick();page.render();
    const control=controls(page)[0];assert.equal(controls(page).length,1);
    assert.equal(control.props.label,current.guide.parameter_label);
    const next=id === "flip_cue" ? true : id === "generator" ? "withhold" : 20;
    control.props.onChange(next);page.render();
    nodes(page.tree,node=>node.type === "TextArea")[0].props.onChange("My first prediction");page.render();
    button(page,"Save my prediction").props.onClick();
    assert.deepEqual(page.actions,[{kind:"commit_prediction",config:{...current.config,[id]:next},prediction:"My first prediction"}]);
    assert.equal(button(page,"Run this test"),undefined,"unsaved prediction never exposes a runnable action");
    assert.equal(nodes(page.tree,node=>node.type === "Slider")[0]?.props.width ?? "100%","100%");
  }
});

test("all four Effect practices show one authored control and preserve the other settings in both profiles", () => {
  const setups=[{parameter:"analysis",config:{kind:"effect",assignment:"self_selected",target_high_pct:50,analysis:"pooled"}},
    {parameter:"assignment",config:{kind:"effect",assignment:"randomized",target_high_pct:50,analysis:"pooled"}},
    {parameter:"target_high_pct",config:{kind:"effect",assignment:"randomized",target_high_pct:20,analysis:"standardized"}},
    {parameter:"assignment",config:{kind:"effect",assignment:"self_selected",target_high_pct:80,analysis:"standardized"}}];
  for (const profile of ["general","medical"]) for (const [index,setup] of setups.entries()) {
    const current=effectSnapshot(setup.parameter,profile,{config:setup.config,experiment_id:`effect.practice.${index+1}`}),page=harness(current);
    assert.match(text(page.tree),/Intervention practice/);
    assert.doesNotMatch(text(page.tree),/Part 1|Part 2|Generation|Reference prediction accuracy|report/);
    assert.equal(controls(page).length,0);
    button(page,"Start practice").props.onClick();page.render();
    assert.equal(controls(page).length,1);assert.equal(controls(page)[0].props.label,current.guide.parameter_label);
    const next=setup.parameter === "target_high_pct" ? 80 : setup.parameter === "analysis" ? "standardized"
      : setup.config.assignment === "randomized" ? "self_selected" : "randomized";
    controls(page)[0].props.onChange(next);page.render();
    nodes(page.tree,node=>node.type === "TextArea")[0].props.onChange(`My ${profile} prediction for practice ${index+1}`);page.render();
    button(page,"Save my prediction").props.onClick();
    assert.deepEqual(page.actions,[{kind:"commit_prediction",config:{...setup.config,[setup.parameter]:next},
      prediction:`My ${profile} prediction for practice ${index+1}`}]);
    assert.equal(button(page,"Run this test"),undefined,"an unsaved Effect setup must not be runnable");
    page.render({...current,revision:1,phase:"predicted",config:page.actions[0].config,prediction:page.actions[0].prediction,
      legal_actions:["commit_prediction","run"]});
    assert.equal(controls(page).length,0);assert.equal(button(page,"Run this test").props.isDisabled,false);
    button(page,"Run this test").props.onClick();assert.deepEqual(page.actions[1],{kind:"run"});
  }
});

test("Effect results compare only the relevant supplied contrast and keep reflection separate from scoring", () => {
  for (const profile of ["general","medical"]) {
    const current=effectSnapshot("analysis",profile),first=run(1,current.config),second=run(2,{...current.config,analysis:"standardized"});
    first.result.metrics=[{label:"Selected analysis contrast",value:-6,display_value:"-6 pp"}];
    second.result.metrics=[{label:"Selected analysis contrast",value:15,display_value:"15 pp"}];
    const page=harness({...current,revision:4,phase:"result",config:second.config,prediction:second.prediction,result:second.result,
      runs:[first,second],distinct_runs:2,legal_actions:["commit_prediction","reflect"]});
    const comparison=nodes(page.tree,node=>node.type === "Table")[0];
    assert.equal(comparison.props.data.length,2);assert.equal(comparison.props.data[1].measure,"Programme A minus B");
    assert.equal(comparison.props.data[1].first,"-6 pp");assert.equal(comparison.props.data[1].second,"15 pp");
    assert.equal((text(page.tree).match(/pp means percentage points/g) ?? []).length,1,
      "the compact unit is explained once without widening the comparison table");
    assert.doesNotMatch(text(page.tree),/generated|source record|Part 1|Part 2/);
    assert.equal(nodes(page.tree,node=>["ExperimentPlot","ExperimentCaseInspector","AnswerCommitment"].includes(node.type)).length,0);
    nodes(page.tree,node=>node.type === "TextArea")[0].props.onChange("The new contrast uses the same population weights.");page.render();
    button(page,"Record my comparison").props.onClick();
    assert.deepEqual(page.actions,[{kind:"reflect",reflection:"The new contrast uses the same population weights."}]);
    const accepted=harness({...current,revision:5,phase:"reflected",config:second.config,result:second.result,runs:[first,second],
      reflection:"My recorded comparison",distinct_runs:2,can_submit_check:true,legal_actions:[]},{isFrozen:true});
    assert.equal(button(accepted,"Change one setting and test again"),undefined);
    assert.equal(button(accepted,"Record my comparison"),undefined);
    assert.match(text(accepted.tree),/saved tests are read-only/);
  }
});

test("comparison copy preserves meaningful capitals in the authored setting label", () => {
  const current=effectSnapshot("assignment"),first=run(1,current.config),second=run(2,{...current.config,assignment:"randomized"});
  current.guide.parameter_label="How people enter programmes A and B";
  const page=harness({...current,phase:"result",config:second.config,prediction:second.prediction,result:second.result,
    runs:[first,second],distinct_runs:2,legal_actions:["commit_prediction","reflect"]});
  assert.match(text(page.tree),/Only this setting changed: How people enter programmes A and B\./);
  assert.doesNotMatch(text(page.tree),/programmes a and b/);
});

test("Effect exposes compact starting-group counts for each compared run only after running", () => {
  const table=(aLow,aHigh,bLow,bHigh)=>({table_id:"source-groups",label:"Starting groups",
    columns:["Starting group","Programme A count","Programme B count"],
    rows:[["Lower starting difficulty",String(aLow),String(bLow)],["Higher starting difficulty",String(aHigh),String(bHigh)]]});
  const tableContext=vm.createContext({React:{createElement:element},CONTAINED_TABLE_STYLE:{overflowX:"auto"},proportional:value=>value,
    ...Object.fromEntries(["VStack","HStack","Button","Text","Table"].map(name=>[name,name])),
    useState:initial=>[initial,()=>{}],useEffect:()=>{}});
  vm.runInContext(ts.transpileModule(declaration("ComparisonWorkbenchCanvas").getText(parsed),{
    compilerOptions:{jsx:ts.JsxEmit.React,target:ts.ScriptTarget.ES2022},
  }).outputText,tableContext);
  for (const profile of ["general","medical"]) {
    const current=effectSnapshot("assignment",profile),first=run(1,current.config),second=run(2,{...current.config,assignment:"randomized"});
    first.result.tables=[table(20,80,80,20)];second.result.tables=[table(50,50,50,50)];
    const firstResult={...current,revision:2,phase:"result",prediction:first.prediction,result:first.result,runs:[first],distinct_runs:1};
    const one=harness(firstResult);
    assert.equal(nodes(one.tree,node=>node.type === "ComparisonWorkbenchCanvas").length,1);
    const comparison=harness({...current,revision:4,phase:"result",config:second.config,prediction:second.prediction,result:second.result,
      runs:[first,second],distinct_runs:2,legal_actions:["commit_prediction","reflect"]});
    const views=nodes(comparison.tree,node=>node.type === "ComparisonWorkbenchCanvas");assert.equal(views.length,2);
    views.forEach((view,index)=>{
      assert.equal(view.props.padding,0,"embedded tables keep the form's existing content line");
      assert.equal(view.props.workbench.tables.length,1);
      assert.equal(JSON.stringify(view.props.workbench.tables[0].rows),JSON.stringify([first,second][index].result.tables[0].rows));
      assert.equal(view.props.workbench.tables[0].columns[1],"Programme A count");
      assert.match(view.props.workbench.tables[0].label,new RegExp(`Test ${index+1}`));
      assert.equal(view.props.workbench.tables[0].rows.length,2,"the view does not invent a total row or outcome rates");
      const rendered=tableContext.ComparisonWorkbenchCanvas(view.props),actual=nodes(rendered,node=>node.type === "Table")[0];
      assert.deepEqual(actual.props.data.map(row=>[row.column0,row.column1,row.column2]),view.props.workbench.tables[0].rows,
        "the shared renderer actually places both A/B counts in the visible table cells");
      assert.equal(rendered.props.padding,0);
    });
    const predicted=harness({...firstResult,revision:3,phase:"predicted",result:null,config:second.config,
      prediction:second.prediction,legal_actions:["commit_prediction","run"]});
    assert.equal(nodes(predicted.tree,node=>node.type === "ComparisonWorkbenchCanvas").length,0,
      "a previous run does not reveal table results while the next setup is waiting to run");
    assert.equal(nodes(harness(current).tree,node=>node.type === "ComparisonWorkbenchCanvas").length,0);
    const shift=snapshot("flip_cue",{phase:"result",result:second.result,runs:[first,second],distinct_runs:2});
    assert.equal(nodes(harness(shift).tree,node=>node.type === "ComparisonWorkbenchCanvas").length,0,
      "Shift practices do not gain unrelated intervention tables");
  }
});

test("saved predictions resume with an explicit run action and editable setup", () => {
  const current=snapshot("flip_cue",{phase:"predicted",prediction:"The label rule will fail",legal_actions:["commit_prediction","run"]});
  const page=harness(current);
  assert.equal(button(page,"Start practice"),undefined);
  assert.equal(controls(page).length,0);
  assert.match(text(page.tree),/The label rule will fail/);
  button(page,"Run this test").props.onClick();assert.deepEqual(page.actions,[{kind:"run"}]);
  button(page,"Edit my setup or prediction").props.onClick();page.render();
  assert.equal(controls(page).length,1);
  assert.equal(nodes(page.tree,node=>node.type === "TextArea")[0].props.value,current.prediction);
  assert.equal(button(page,"Run this test"),undefined);
});

test("prediction results show only friendly relevant measures, not generated reports or large result boards", () => {
  const current=snapshot(),recorded=run(1,current.config,80);
  const page=harness({...current,phase:"result",prediction:recorded.prediction,result:recorded.result,runs:[recorded],distinct_runs:1});
  assert.match(text(page.tree),/Correct parcel predictions\s*:/);
  assert.doesNotMatch(text(page.tree),/generated draft|source record|report-generation|irrelevant|80%.*1%/);
  assert.equal(nodes(page.tree,node=>["ExperimentPlot","ExperimentCaseInspector","ComparisonWorkbenchCanvas"].includes(node.type)).length,0);
  assert.equal(nodes(page.tree,node=>node.type === "Table").length,0);
  assert.equal(nodes(page.tree,node=>node.type === "Collapsible")[0].props.defaultIsOpen,false);
  button(page,"Change one setting and test again").props.onClick();page.render();
  assert.equal(controls(page).length,1);
  assert.equal(nodes(page.tree,node=>node.type === "TextArea")[0].props.value,"");
  assert.ok(button(page,"Back to the recorded result"));
});

test("different saved runs compare one setting and only the relevant outcome before reflection", () => {
  const current=snapshot(),first=run(1,current.config,90),second=run(2,{...current.config,cue_accuracy_pct:20},20);
  const page=harness({...current,phase:"result",revision:4,config:second.config,prediction:second.prediction,result:second.result,
    runs:[first,second],distinct_runs:2,legal_actions:["commit_prediction","reflect"]});
  const table=nodes(page.tree,node=>node.type === "Table")[0];
  assert.equal(table.props["aria-label"],"Compare the two tests");assert.equal(table.props.data.length,2);
  assert.equal(table.props.data[1].first,"90%");assert.equal(table.props.data[1].second,"20%");
  const input=nodes(page.tree,node=>node.type === "TextArea")[0];assert.equal(input.props.label,current.guide.comparison_prompt);
  input.props.onChange("The same label rule worked less well after its agreement changed.");page.render();
  button(page,"Record my comparison").props.onClick();
  assert.deepEqual(page.actions,[{kind:"reflect",reflection:"The same label rule worked less well after its agreement changed."}]);
  const saved={...current,phase:"reflected",revision:5,config:second.config,prediction:second.prediction,result:second.result,
    reflection:"My comparison",runs:[first,second],distinct_runs:2,can_submit_check:true};
  page.render(saved);assert.match(text(page.tree),/Check your interpretation below/);
  assert.equal(nodes(page.tree,node=>node.type === "TextArea").length,0);
});

test("generation has its own later section and shows a source alongside the generated draft", () => {
  const current=snapshot("generator"),recorded=run(1,current.config);
  const page=harness({...current,phase:"result",prediction:recorded.prediction,result:recorded.result,runs:[recorded],distinct_runs:1});
  assert.match(text(page.tree),/Part 2 · Generation/);assert.match(text(page.tree),/One source record/);
  assert.match(text(page.tree),/A source record/);assert.match(text(page.tree),/A generated draft/);
});

test("generation compares the same missing-context record rather than an easy known-context first case", () => {
  const current=snapshot("generator"),first=run(1,current.config),second=run(2,{...current.config,generator:"withhold"});
  first.result.cases=[{case_id:1,metadata_known:true,source_text:"Easy known-context source",generated_text:"Identical easy draft"},
    {case_id:25,metadata_known:false,source_text:"The measured flag is present. Context is not recorded.",generated_text:"Invented missing context."}];
  second.result.cases=[{case_id:1,metadata_known:true,source_text:"Easy known-context source",generated_text:"Identical easy draft"},
    {case_id:25,metadata_known:false,source_text:"The measured flag is present. Context is not recorded.",generated_text:"Full report withheld because context is missing."}];
  const page=harness({...current,phase:"result",config:second.config,prediction:second.prediction,result:second.result,
    runs:[first,second],distinct_runs:2,legal_actions:["commit_prediction","reflect"]});
  assert.match(text(page.tree),/Example case\s+25/);assert.match(text(page.tree),/Required context is missing/);
  assert.match(text(page.tree),/Invented missing context/);assert.match(text(page.tree),/Full report withheld/);
  assert.doesNotMatch(text(page.tree),/Easy known-context source|Identical easy draft/);
  assert.equal((text(page.tree).match(/The measured flag is present/g) ?? []).length,1,"the same source is shown once for the two rules");
});

test("label-flip evidence follows one matched case without changing the simulated condition or exposing generation", () => {
  const current=snapshot("flip_cue"),first=run(1,current.config),second=run(2,{...current.config,flip_cue:true});
  first.result.cases=[{case_id:1,target:1,measurement:1,cue:1,prediction:1}];
  second.result.cases=[{case_id:1,target:1,measurement:1,cue:0,prediction:0}];
  const page=harness({...current,phase:"result",config:second.config,prediction:second.prediction,result:second.result,
    runs:[first,second],distinct_runs:2,legal_actions:["commit_prediction","reflect"]});
  assert.match(text(page.tree),/Follow the same example/);assert.match(text(page.tree),/simulated condition was\s+present\s+in both/);
  assert.match(text(page.tree),/Marker value:\s+1\s+→\s+0/);
  assert.match(text(page.tree),/Predicted condition:\s+present\s+→\s+absent/);
  assert.doesNotMatch(text(page.tree),/source record|generated draft|Reference|Cue/);
  const otherStage=harness({...current,guide:{...current.guide,parameter_id:"measurement_error_pct"},phase:"result",result:second.result,
    runs:[first,second],distinct_runs:2});
  assert.doesNotMatch(text(otherStage.tree),/Follow the same example/);
});

test("comparison finds a different recorded setup, and never claims other conditions were fixed when they were not", () => {
  const current=snapshot(),first=run(1,current.config,90),second=run(2,{...current.config,cue_accuracy_pct:20},20);
  const repeated=run(3,second.config,20);
  const page=harness({...current,phase:"result",config:repeated.config,prediction:repeated.prediction,result:repeated.result,
    runs:[first,second,repeated],distinct_runs:2,legal_actions:["commit_prediction","reflect"]});
  const table=nodes(page.tree,node=>node.type === "Table")[0];
  assert.equal(table.props.columns[1].header,"Test 1");assert.equal(table.props.columns[2].header,"Test 3");
  const otherChange=run(4,{...second.config,fixed:"a different condition"});
  page.render({...current,phase:"result",revision:5,config:otherChange.config,prediction:otherChange.prediction,result:otherChange.result,
    runs:[first,otherChange],distinct_runs:2,legal_actions:["commit_prediction","reflect"]});
  assert.match(text(page.tree),/also differ in other conditions/);
  assert.doesNotMatch(text(page.tree),/Only friendly/);
});

test("busy and accepted practice cannot run, edit, or change saved evidence", () => {
  const current=snapshot("flip_cue",{phase:"predicted",prediction:"A guess",legal_actions:["commit_prediction","run"]});
  for (const options of [{isWorking:true},{isFrozen:true}]) {
    const page=harness(current,options);
    assert.equal(button(page,"Run this test").props.isDisabled,true);
    assert.equal(button(page,"Edit my setup or prediction").props.isDisabled,true);
  }
  const initial=harness(snapshot(),{isWorking:true});assert.equal(button(initial,"Start practice").props.isDisabled,true);
});

test("step focus follows presentation changes, not typing, chat or unchanged result refreshes", () => {
  const page=harness(snapshot());button(page,"Start practice").props.onClick();page.render();
  const count=page.focus.length;
  nodes(page.tree,node=>node.type === "TextArea")[0].props.onChange("A draft kept during chat");page.render();
  page.render({...snapshot()});assert.equal(page.focus.length,count);
  assert.equal(nodes(page.tree,node=>node.type === "TextArea")[0].props.value,"A draft kept during chat");
});

test("responsive remount and introduction exit keep the active editing step, prediction, and setting in their parent", () => {
  const current=snapshot(),desktop=harness(current);
  button(desktop,"Start practice").props.onClick();desktop.render();
  controls(desktop)[0].props.onChange(30);desktop.render();
  nodes(desktop.tree,node=>node.type === "TextArea")[0].props.onChange("My unsaved desktop prediction");desktop.render();
  const mobile=harness(current,{store:desktop.store});
  assert.equal(button(mobile,"Start practice"),undefined);
  assert.equal(controls(mobile)[0].props.value,30);
  assert.equal(nodes(mobile.tree,node=>node.type === "TextArea")[0].props.value,"My unsaved desktop prediction");
  const returnedFromIntroduction=harness(current,{store:desktop.store});
  assert.equal(controls(returnedFromIntroduction)[0].props.value,30);
  assert.equal(nodes(returnedFromIntroduction.tree,node=>node.type === "TextArea")[0].props.value,"My unsaved desktop prediction");
  const anotherProfile=harness(current,{store:desktop.store,scope:"test.medical.another-attempt"});
  assert.ok(button(anotherProfile,"Start practice"),"another attempt never inherits this draft");
  const saved={...current,revision:1,phase:"predicted",prediction:"A server-recorded prediction",legal_actions:["commit_prediction","run"]};
  mobile.render(saved);assert.ok(button(mobile,"Run this test"));
  assert.match(text(mobile.tree),/A server-recorded prediction/);assert.doesNotMatch(text(mobile.tree),/unsaved desktop/);
  const screen=declaration("LearningScreen").getText(parsed);
  assert.match(declaration("App").getText(parsed),/const \[guidedDraft,setGuidedDraft\] = useState<GuidedPracticeDraft\|null>\(null\)/);
  assert.doesNotMatch(screen,/useState<GuidedPracticeDraft/);
  assert.match(screen,/state\.learning_pack_version.*state\.attempt_id.*state\.experiment\?\.experiment_id/);
  assert.match(screen,/draftState=\{guidedPracticeDraft\(state\.experiment,guidedScope,guidedDraft\)\}/);
});

test("the real App retains Shift and both Effect profiles across PageFrame remounts, with revision and reload boundaries", () => {
  for (const variant of [{current:snapshot(),module:"m1_shift",profile:"general"},
    {current:effectSnapshot("target_high_pct","general"),module:"m1_effect",profile:"general"},
    {current:effectSnapshot("target_high_pct","medical"),module:"m1_effect",profile:"medical"}]) {
  const current=variant.current,state={status:"active",diagnostic:null,active_module_id:variant.module,profile_id:variant.profile,
    learning_pack_id:`${variant.module}.${variant.profile}`,learning_pack_version:"1.3.0",attempt_id:"attempt.1",activity_id:"practice.1",
    modules:[],concepts:[],conversation:[],question:"Which interpretation fits?",experiment:current,
    course_introduction:{title:"The course",profile_id:variant.profile},course_title:"The current course",tutor_status:"ready"};
  const hookValues={App:[state],LearningScreen:[]};
  let owner="App",cursor=0,isWide=true,lastWidth;
  const names=["App","PageFrame","LearningScreen","guidedPracticeDraft","GuidedExperimentWorkbench"];
  const code=names.map(name=>declaration(name).getText(parsed)).join("\n");
  const components=[...new Set([...code.matchAll(/<([A-Z][A-Za-z0-9]*)\b/g)].map(match=>match[1]))];
  const context=vm.createContext({exports:{},React:{Fragment:"Fragment",createElement:(type,props,...children)=>element(typeof type === "function" ? type.name : type,props,...children)},
    ...Object.fromEntries(components.map(name=>[name,name])),
    useState(initial) {const values=hookValues[owner],slot=cursor++;
      if (!(slot in values)) values[slot]=initial;
      return [values[slot],value=>{values[slot]=typeof value === "function" ? value(values[slot]) : value;}];},
    useRef:()=>({current:null}),useEffect:()=>{},useLayoutEffect:()=>{},useCallback:callback=>callback,useMediaQuery:()=>isWide,
    moduleConcepts:()=>[],conceptForActivity:()=>null,conceptsWithRouteCredit:()=>[],conceptsWithPractice:()=>[],
    READING_WIDTH:"68ch",SCENARIO_WIDTH:"120ch",WIDE_WORKSPACE_QUERY:"(min-width: 1100px)",
    SCRIPT_FOCUS_STYLE:{outline:"none"},ENTRY_ROUTE_PANEL_STYLE:{},CONTAINED_TABLE_STYLE:{overflowX:"auto"},
    proportional:value=>value,window:{scrollX:0,scrollY:0},
  });
  vm.runInContext(ts.transpileModule(code,{
    compilerOptions:{jsx:ts.JsxEmit.React,target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS},
  }).outputText,context);
  const walk=(tree,predicate)=>Array.isArray(tree) ? tree.flatMap(item=>walk(item,predicate))
    : tree && typeof tree === "object" && "type" in tree
      ? [...(predicate(tree) ? [tree] : []),...tree.children.flatMap(child=>walk(child,predicate)),
        ...Object.values(tree.props).flatMap(slot=>walk(slot,predicate))] : [];
  const render=()=>{
    owner="App";cursor=0;const app=context.App();
    const frame=context.PageFrame({children:app.children});
    assert.equal(frame.type,isWide ? "VStack" : "Fragment","exercise PageFrame's actual different parent trees");
    if (lastWidth !== isWide) hookValues.LearningScreen=[];
    lastWidth=isWide;
    owner="LearningScreen";cursor=0;
    const props=walk(frame,node=>node.type === "LearningScreen")[0].props;
    const screen=context.LearningScreen(props);
    const guided=walk(screen,node=>node.type === "GuidedExperimentWorkbench")[0];
    return {screen,practice:context.GuidedExperimentWorkbench(guided.props)};
  };
  let page=render();
  nodes(page.practice,node=>node.type === "Button" && node.props.label === "Start practice")[0].props.onClick();page=render();
  nodes(page.practice,node=>node.type === "Slider")[0].props.onChange(30);page=render();
  nodes(page.practice,node=>node.type === "TextArea")[0].props.onChange("My unsaved responsive prediction");page=render();
  for (const wide of [false,true]) {
    isWide=wide;page=render();
    assert.equal(nodes(page.practice,node=>node.type === "Slider")[0].props.value,30);
    assert.equal(nodes(page.practice,node=>node.type === "TextArea")[0].props.value,"My unsaved responsive prediction");
    assert.equal(nodes(page.practice,node=>node.type === "Button" && node.props.label === "Start practice").length,0);
  }
  walk(page.screen,node=>node.type === "Button" && node.props.label === "Leave practice")[0].props.onClick();page=render();
  assert.ok(walk(page.screen,node=>node.type === "CourseIntroductionCanvas")[0]);
  for (const wide of [false,true]) {
    isWide=wide;page=render();
    assert.ok(walk(page.screen,node=>node.type === "CourseIntroductionCanvas")[0],"resizing while on the introduction must not return to the practice");
  }
  walk(page.screen,node=>node.type === "CourseIntroductionCanvas")[0].props.onContinue();page=render();
  assert.equal(walk(page.screen,node=>node.type === "CourseIntroductionCanvas").length,0);
  assert.equal(nodes(page.practice,node=>node.type === "TextArea")[0].props.value,"My unsaved responsive prediction");
  assert.equal(nodes(page.practice,node=>node.type === "Slider")[0].props.value,30);
  for (const changedScope of [{attempt_id:"another-attempt"},{learning_pack_version:"another-version"},
    {profile_id:variant.profile === "medical" ? "general" : "medical"},{active_module_id:"another-course"}]) {
    hookValues.App[0]={...state,...changedScope};page=render();
    assert.ok(nodes(page.practice,node=>node.type === "Button" && node.props.label === "Start practice")[0],
      "a different course, profile, version, or attempt never inherits an unsaved practice draft");
  }
  const savedState={...state,experiment:{...current,revision:1,phase:"predicted",config:{...current.config,[current.guide.parameter_id]:20},
    prediction:"My explicitly saved prediction",legal_actions:["commit_prediction","run"]}};
  hookValues.App[0]=savedState;page=render();
  assert.ok(nodes(page.practice,node=>node.type === "Button" && node.props.label === "Run this test")[0]);
  assert.match(text(page.practice),/My explicitly saved prediction/);
  assert.doesNotMatch(text(page.practice),/My unsaved responsive prediction/);
  hookValues.App=[state];hookValues.LearningScreen=[];page=render();
  assert.ok(nodes(page.practice,node=>node.type === "Button" && node.props.label === "Start practice")[0],
    "a full App reload does not pretend that local-only edits were saved");
  hookValues.App=[savedState];hookValues.LearningScreen=[];page=render();
  assert.ok(nodes(page.practice,node=>node.type === "Button" && node.props.label === "Run this test")[0],
    "explicitly saved runtime prediction survives a full App reload");
  assert.match(text(page.practice),/My explicitly saved prediction/);
  const firstRun=run(1,current.config),secondRun=run(2,{...current.config,[current.guide.parameter_id]:30});
  const resultState={...state,experiment:{...current,revision:4,phase:"result",config:secondRun.config,prediction:secondRun.prediction,
    result:secondRun.result,runs:[firstRun,secondRun],distinct_runs:2,legal_actions:["commit_prediction","reflect"]}};
  hookValues.App=[resultState];hookValues.LearningScreen=[];page=render();
  nodes(page.practice,node=>node.type === "TextArea")[0].props.onChange("My unsaved reflection");page=render();
  for (const wide of [false,true]) {
    isWide=wide;page=render();
    assert.equal(nodes(page.practice,node=>node.type === "TextArea")[0].props.value,"My unsaved reflection");
  }
  hookValues.App=[resultState];hookValues.LearningScreen=[];page=render();
  assert.equal(nodes(page.practice,node=>node.type === "TextArea")[0].props.value,"","unsaved reflection is not persisted across a full reload");
  hookValues.App=[{...resultState,experiment:{...resultState.experiment,revision:5,phase:"reflected",reflection:"An explicitly saved reflection",can_submit_check:true}}];
  hookValues.LearningScreen=[];page=render();assert.match(text(page.practice),/An explicitly saved reflection/);
  const appSource=declaration("App").getText(parsed),screenSource=declaration("LearningScreen").getText(parsed);
  assert.match(appSource,/const \[isIntroductionOpen,setIsIntroductionOpen\] = useState\(false\)/);
  assert.match(appSource,/useEffect\(\(\) => setIsIntroductionOpen\(false\), \[state\?\.profile_id,state\?\.active_module_id\]\)/);
  assert.doesNotMatch(screenSource,/useState\(false\)[\s\S]{0,80}isIntroductionOpen/);
  }
});

test("guided interpretation waits for runtime readiness and exiting hides rather than resets the current activity", () => {
  const canvasCode=ts.transpileModule(declaration("InvestigationCanvas").getText(parsed),{
    compilerOptions:{jsx:ts.JsxEmit.React,target:ts.ScriptTarget.ES2022},
  }).outputText;
  const context=vm.createContext({React:{createElement:element},READING_WIDTH:"68ch",SCENARIO_WIDTH:"120ch",
    ...Object.fromEntries(["VStack","Text","QuestionPrompt","Card","Heading","InlineMarkup","QuestionIllustration","ComparisonWorkbenchCanvas","Grid"].map(name=>[name,name]))});
  vm.runInContext(canvasCode,context);
  for (const ready of [false,true]) {
    const tree=context.InvestigationCanvas({deferQuestion:true,image:null,recordText:"The interpretation question",conceptId:null,
      concepts:[],experiment:element("GuidedExperimentWorkbench"),commitment:ready ? element("AnswerCommitment") : undefined});
    assert.equal(nodes(tree,node=>node.type === "QuestionPrompt").length,ready ? 1 : 0);
    assert.equal(nodes(tree,node=>node.type === "AnswerCommitment").length,ready ? 1 : 0);
    if (ready) assert.equal(nodes(tree,node=>node.type === "QuestionPrompt")[0].props.headingLevel,2);
    const order=tree.children.filter(Boolean).map(node=>node.type);
    if (ready) assert.ok(order.indexOf("GuidedExperimentWorkbench") < order.indexOf("QuestionPrompt"));
  }
  const screen=declaration("LearningScreen").getText(parsed);
  assert.match(screen,/guidedExperiment && !state\.experiment\?\.can_submit_check \? undefined/);
  assert.match(screen,/label=\{guidedExperiment \? "Leave practice" : "Course introduction"\}/);
  assert.match(screen,/style=\{showIntroduction \? \{display:"none"\} : undefined\} onClick=\{openIntroduction\}/);
  assert.match(screen,/id="learning-activity"[\s\S]{0,180}display:"none"/);
  const exit=screen.slice(screen.indexOf("const openIntroduction"),screen.indexOf("const concepts"));
  assert.match(exit,/setIsIntroductionOpen\(true\)/);
  assert.doesNotMatch(exit,/onRun|reset|select-profile|continue/);
  assert.match(screen,/\? <GuidedExperimentWorkbench/);
  assert.match(screen,/: <ExperimentWorkbench/);
  const intro=declaration("CourseIntroductionCanvas").getText(parsed);
  assert.match(intro,/!hideCaption && introduction\.image_caption &&/);
  assert.match(screen,/hideCaption=\{state\.active_module_id === "m1_shift"\}/);

  vm.runInContext(ts.transpileModule(`${declaration("splitQuestion").getText(parsed)}\n${declaration("questionGraphNodes").getText(parsed)}\n${declaration("QuestionPrompt").getText(parsed)}`,{
    compilerOptions:{jsx:ts.JsxEmit.React,target:ts.ScriptTarget.ES2022},
  }).outputText,context);
  for (const prompt of ["Which interpretation fits?","Two settings gave different results. Which interpretation fits?"]) {
    const check=context.QuestionPrompt({text:prompt,headingLevel:2});
    const practice=harness(snapshot()).tree;
    assert.equal(nodes([practice,check],node=>node.type === "Heading" && node.props.level === 1).length,1,
      "revealing an interpretation under a practice title retains exactly one H1");
    assert.equal(nodes(check,node=>node.type === "Heading" && node.props.level === 2).length,1);
    const ordinary=context.QuestionPrompt({text:prompt});
    assert.equal(nodes(ordinary,node=>node.type === "Heading" && node.props.level === 1).length,1,
      "ordinary question pages keep their existing H1");
  }
});

test("M1 explanations use authored headings without the mechanical numbering used by Foundations", () => {
  const lesson=declaration("LessonCanvas").getText(parsed);
  assert.match(lesson,/state\.active_module_id === "m1_shift" \|\| state\.active_module_id === "m1_effect" \? step\.title : `\$\{index\+1\}\. \$\{step\.title\}`/);
  const intro=declaration("CourseIntroductionCanvas").getText(parsed);
  assert.match(intro,/hideCaption = false/);
  assert.match(intro,/<img src=\{`\/\$\{introduction\.scenario_image\.path\}`\} alt=\{introduction\.scenario_image\.alt_text\}/);
});

test("current Umbrella instructions describe the action naturally instead of assigning a variable to yes", () => {
  const dynamic=declaration("DynamicUmbrellaWorkbench").getText(parsed);
  assert.match(dynamic,/Give everyone an umbrella in both models/);
  assert.doesNotMatch(dynamic,/Set umbrella carrying to yes/);
  const learning=declaration("LearningScreen").getText(parsed);
  assert.match(learning,/const guidedExperiment = !!state\.experiment\?\.guide;/);
  assert.match(learning,/guidedExperiment \? <GuidedExperimentWorkbench/);
  assert.match(learning,/: <ExperimentWorkbench/,
    "historical Effect and Shift packs without a guide retain their existing presentation");
});
