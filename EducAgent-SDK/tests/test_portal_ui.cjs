"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");
const { webcrypto } = require("node:crypto");
const ts = require("typescript");

const source = fs.readFileSync(path.join(__dirname, "../web/src/App.tsx"), "utf8");
const parsed = ts.createSourceFile("App.tsx", source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
const element = (type, props, ...children) => ({type, props: props || {}, children:children.flat()});

function component(name, extra = {}) {
  const declaration = parsed.statements.find(node => ts.isFunctionDeclaration(node) && node.name?.text === name);
  assert.ok(declaration, name);
  const output = ts.transpileModule(declaration.getText(parsed), {
    compilerOptions: {jsx:ts.JsxEmit.React, module:ts.ModuleKind.CommonJS, target:ts.ScriptTarget.ES2022},
  });
  const context = vm.createContext({
    exports:{}, React:{createElement:element},
    ...Object.fromEntries(["VStack", "HStack", "TextArea", "Text", "Button", "PageFrame", "LearningScreen",
      "ProfileDialog", "DiagnosticScreen", "LoadingScreen", "StatusDot", "MessageTurn", "PlainComposer",
      "Collapsible", "RouteList", "List", "ListItem", "Heading", "Token", "TutorAvatar", "RichText",
      "ExampleRolesLegend", "QuestionIllustration", "AspectRatio", "Grid", "AnswerFeedbackNotice",
      "AnswerCommitment", "CommitBar", "Card", "ComparisonWorkbenchCanvas", "Eyebrow", "Divider", "QuestionPrompt",
      "InlineMarkup", "Code", "QuestionCausalGraph"].map(id => [id,id])),
    useRef:()=>({current:null}), useEffect:()=>{}, useLayoutEffect:()=>{}, useCallback:fn=>fn,
    useMediaQuery:()=>false, WIDE_WORKSPACE_QUERY:"(min-width: 1100px)", EDUCAGENT_AVATAR_SRC:"/avatar.png",
    READING_WIDTH:"68ch", SCENARIO_WIDTH:"120ch", SCRIPT_FOCUS_STYLE:{outline:"none"},
    INLINE_CODE_STYLE:{background:"var(--color-background-teal)"},
    ...extra,
  });
  vm.runInContext(output.outputText, context);
  return context[name] || context.exports[name];
}

test("verified textbook replies render real blockquotes and safe source links, including saved plain text", async () => {
  const React = require("react");
  const {renderToStaticMarkup} = require("react-dom/server");
  const {default:ReactMarkdown} = await import("react-markdown");
  const {default:remarkMath} = await import("remark-math");
  const {default:rehypeKatex} = await import("rehype-katex");
  const format = component("tutorMarkdown");
  const RichText = component("RichText", {
    React, ReactMarkdown, remarkMath, rehypeKatex, tutorMarkdown:format,
    VStack:({as:Tag="section", children, style})=>React.createElement(Tag,{style},children),
  });
  const saved = 'Textbook quotation (mathematical notation transcribed):\n\n"A verified quotation."\n\nSource: Appendix A.1, p. 213. https://mitpress.mit.edu/9780262037310/elements-of-causal-inference/';
  for (const text of [saved, format(saved)]) {
    const html = renderToStaticMarkup(React.createElement(RichText,{text}));
    assert.match(html, /<blockquote[^>]*>/);
    assert.match(html, /border-inline-start:/);
    assert.match(html, /href="https:\/\/mitpress\.mit\.edu\/9780262037310\/elements-of-causal-inference\/">Publisher source<\/a>/);
    assert.match(html, /p\. 213/);
    assert.match(html, /overflow-wrap:anywhere/);
    assert.equal(format(format(text)),format(text));
  }
  const unsafe = renderToStaticMarkup(React.createElement(RichText,{text:'<script>alert(1)</script>\n\n![external](https://example.org/image.png)\n\n[bad](javascript:alert(1))'}));
  assert.doesNotMatch(unsafe, /<script|<img|href="javascript:/);
  assert.equal(format("Ordinary learner text > is unchanged"),"Ordinary learner text > is unchanged");
});

test("request IDs retain the native UUID path when available", () => {
  let calls = 0;
  const crypto = {randomUUID() {
    assert.equal(this, crypto);
    calls++;
    return "12345678-1234-4123-8123-123456789abc";
  }, getRandomValues() {throw new Error("native UUID must not use the fallback");}};
  const requestId = component("requestId", {crypto});
  assert.equal(requestId("message"), "web.message.12345678-1234-4123-8123-123456789abc");
  assert.equal(calls, 1);
});

test("HTTP request IDs use 16 secure random bytes, UUIDv4 bits and distinct prefixed values", () => {
  const lengths = [];
  const crypto = {getRandomValues(bytes) {
    lengths.push(bytes.length);
    return webcrypto.getRandomValues(bytes);
  }};
  const requestId = component("requestId", {crypto, isSecureContext:false});
  const ids = Array.from({length:256}, () => requestId("command"));
  assert.equal(new Set(ids).size, ids.length);
  assert.ok(lengths.every(length => length === 16));
  assert.equal(lengths.length, ids.length);
  ids.forEach(id => assert.match(id, /^web\.command\.[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/));
  const fixed = component("requestId", {crypto:{getRandomValues:bytes => bytes.fill(255)}});
  assert.equal(fixed("answer"), "web.answer.ffffffff-ffff-4fff-bfff-ffffffffffff");
  assert.doesNotMatch(source.match(/function requestId[\s\S]*?\n\}/)[0], /Math\.random/);
});

test("HTTP profile selection reaches fetch through the real App and API with a UUID request ID", async () => {
  const requestId = component("requestId", {crypto:{getRandomValues:bytes => webcrypto.getRandomValues(bytes)}});
  const calls = [], state = {active_module_id:"causality_m0", profile_id:null, profile_required:true,
    course_profiles:["general", "medical"], diagnostic:null, status:"not_started"};
  const next = {...state, profile_id:"general", profile_required:false};
  const api = component("api", {requestId, AbortController, DOMException,
    window:{setTimeout:()=>1, clearTimeout:()=>{}},
    fetch:async (url, options) => {calls.push({url, options}); return {ok:true, json:async () => next};},
  });
  const values = [state];
  let cursor = 0;
  const App = component("App", {api, requestId, useState(initial) {
    const slot = cursor++;
    if (!(slot in values)) values[slot] = initial;
    return [values[slot], value => {values[slot] = typeof value === "function" ? value(values[slot]) : value;}];
  }});
  const dialog = nodes(App(), node => node.type === "ProfileDialog")[0];
  await dialog.props.onSelect("general");
  assert.equal(calls.length, 1);
  assert.equal(calls[0].url, "/api/select-profile");
  assert.equal(calls[0].options.method, "POST");
  assert.equal(calls[0].options.credentials, "same-origin");
  const body = JSON.parse(calls[0].options.body);
  assert.equal(body.profile_id, "general");
  assert.match(body.request_id, /^web\.command\.[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
  assert.equal(values[0], next);
  assert.equal(values[2], null, "profile submission should not become a misleading network error");
});

const isElement = value => value != null && typeof value === "object" && !Array.isArray(value)
  && "type" in value && Array.isArray(value.children);

// Layout slots such as lead/aside/rest pass elements as props, so search them too.
function nodes(tree, predicate) {
  if (Array.isArray(tree)) return tree.flatMap(item => nodes(item, predicate));
  if (!isElement(tree)) return [];
  const slots = Object.values(tree.props).filter(value => isElement(value) || Array.isArray(value));
  return [...(predicate(tree) ? [tree] : []), ...tree.children.flatMap(child => nodes(child, predicate)),
    ...slots.flatMap(slot => nodes(slot, predicate))];
}

test("Foundations entry actions share a visible style and retain their handlers and busy state", () => {
  const QuizIntro = component("QuizIntro");
  const called = [];
  for (const isWorking of [false, true]) {
    const tree = QuizIntro({isWorking, onSkip:()=>called.push("basics"),
      onStart:()=>called.push("quiz"), onStartScene:()=>called.push("exercise")});
    const options = nodes(tree, node=>node.props["aria-label"] === "Learning entry options")[0];
    assert.equal(options.props.role, "group");
    const buttons = nodes(options, node=>node.type === "Button");
    assert.deepEqual(buttons.map(button=>button.props.label),
      ["Start from the basics", "Take the optional quiz", "Try an exercise"]);
    buttons.forEach(button=>{
      assert.equal(button.props.variant, "secondary");
      assert.equal(button.props.size, "lg");
      assert.equal(button.props.isDisabled, isWorking);
      if (!isWorking) button.props.onClick();
    });
  }
  assert.deepEqual(called, ["basics", "quiz", "exercise"]);
  const single = QuizIntro({isWorking:false, onStart:()=>{}, diagnostic:false, title:"Another course"});
  assert.equal(nodes(single, node=>node.type === "Button")[0].props.variant, "primary");
});

function composer(value, disabled = false) {
  const sent = [], drafts = [];
  const render = component("PlainComposer");
  const tree = render({value, isDisabled:disabled, onSubmit:async text=>{sent.push(text); return true;}, onChange:text=>drafts.push(text)});
  return {tree, sent, drafts, input:nodes(tree, node=>node.type === "TextArea")[0],
    button:nodes(tree, node=>node.type === "Button")[0]};
}

async function enter(input, overrides = {}) {
  let prevented = false;
  await input.props.onKeyDown({key:"Enter", shiftKey:false, keyCode:13, nativeEvent:{isComposing:false},
    preventDefault(){ prevented = true; }, ...overrides});
  return prevented;
}

test("IME confirmation and Shift+Enter do not send or erase a Portal draft", async () => {
  for (const event of [{nativeEvent:{isComposing:true}}, {keyCode:229}, {shiftKey:true}]) {
    const current = composer("中文候选");
    assert.equal(await enter(current.input, event), false);
    assert.deepEqual(current.sent, []);
    assert.deepEqual(current.drafts, []);
  }
  const current = composer("  Explain this idea.  ");
  assert.equal(await enter(current.input), true);
  assert.deepEqual(current.sent, ["Explain this idea."]);
  assert.deepEqual(current.drafts, [""]);
});

test("the existing 1000-code-point bound is visible and over-limit text is preserved", async () => {
  const oversized = composer("x".repeat(1001));
  assert.equal(oversized.button.props.isDisabled, true);
  assert.match(oversized.input.props.status.message, /1,000.*text is kept/);
  await enter(oversized.input);
  await oversized.button.props.onClick();
  assert.deepEqual(oversized.sent, []);
  assert.deepEqual(oversized.drafts, []);
  const unicode = composer("😀".repeat(1000));
  assert.equal(unicode.button.props.isDisabled, false);
  await unicode.button.props.onClick();
  assert.equal(Array.from(unicode.sent[0]).length, 1000);
  assert.equal(composer("Question", true).button.props.isDisabled, true);
  assert.ok(composer("Question").input.props.label, "the composer has a persistent accessible name");
});

test("a request rejected before recording keeps the editable message", async () => {
  const changes = [], render = component("PlainComposer");
  const tree = render({value:"My unsaved explanation", isDisabled:false,
    onSubmit:async()=>false, onChange:text=>changes.push(text)});
  await nodes(tree, node=>node.type === "Button")[0].props.onClick();
  assert.deepEqual(changes, []);
});

test("a scene explanation rejected before recording is not erased either", async () => {
  const values = [[], "", "", "My original explanation"], changes = [];
  let cursor = 0;
  const render = component("CausalSceneWorkbench", {edgeKey:()=>"", useState() {
    const slot = cursor++;
    return [values[slot], value=>changes.push({slot,value})];
  }});
  const tree = render({scene:{phase:"hook",title:"Umbrellas",graph_edges:[],permitted_edges:[],nodes:[],resources:{hook:"An example"}},
    isWorking:false, canContinue:false, onShareHypothesis:async()=>false});
  await nodes(tree, node=>node.type === "Button" && node.props.label === "Discuss my idea with EducAgent")[0].props.onClick();
  assert.deepEqual(changes, []);
});

test("drafts belong to each course/profile/version/attempt, not a responsive composer instance", () => {
  const values = [], makeState = (module, profile, attempt = "attempt.1", version = "1.2.0") => ({
    active_module_id:module, profile_id:profile, attempt_id:attempt,
    learning_pack_id:`${module}.${profile}`, learning_pack_version:version,
    diagnostic:null, status:"active", course_profiles:["general", "medical"],
  });
  let cursor = 0;
  const App = component("App", {useState(initial) {
    const slot = cursor++;
    if (!(slot in values)) values[slot] = initial;
    return [values[slot], next => { values[slot] = typeof next === "function" ? next(values[slot]) : next; }];
  }});
  const render = state => {
    values[0] = state;
    cursor = 0;
    return nodes(App(), node=>node.type === "LearningScreen")[0].props;
  };
  const states = ["causality_m0", "m1_effect", "m1_shift"].flatMap(module =>
    ["general", "medical"].map(profile=>makeState(module, profile)));
  states.forEach((state, index) => {
    const page = render(state);
    assert.equal(page.messageDraft, "");
    page.onMessageDraftChange(`Draft ${index}`);
  });
  states.forEach((state, index) => assert.equal(render(state).messageDraft, `Draft ${index}`));
  assert.equal(render(makeState("m1_shift", "medical", "attempt.2")).messageDraft, "");
  assert.equal(render(makeState("m1_shift", "medical", "attempt.1", "1.3.0")).messageDraft, "");
  assert.equal(render(states[5]).messageDraft, "Draft 5");
});

test("the real App send path keeps a stale-request draft but clears a retained retry message", async () => {
  for (const retryable of [false, true]) {
    class Failure extends Error { constructor(){super("Test request failure"); this.retryable=retryable; this.code="state_conflict";} }
    const values = [], state = {active_module_id:"m1_effect", profile_id:"general", learning_pack_id:"effect.general",
      learning_pack_version:"1.2.0", attempt_id:"attempt.1", activity_id:"topic.quiz", activity_concept_id:"topic",
      status:"active", diagnostic:null, conversation:[]};
    let cursor = 0;
    const App = component("App", {ApiFailure:Failure, requestId:()=>"test.message", api:async path=>{
      if (path === "/api/message") throw new Failure();
      assert.equal(path, "/api/state");
      return state;
    }, useState(initial) {
      const slot = cursor++;
      if (!(slot in values)) values[slot] = initial;
      return [values[slot], next=>{values[slot]=typeof next === "function" ? next(values[slot]) : next;}];
    }});
    const render = () => {cursor=0; return nodes(App(), node=>node.type === "LearningScreen")[0].props;};
    values[0] = state;
    render().onMessageDraftChange("Keep this explanation");
    const page = render();
    const tree = component("PlainComposer")({value:page.messageDraft, isDisabled:false,
      onSubmit:page.onSendMessage, onChange:page.onMessageDraftChange});
    await nodes(tree, node=>node.type === "Button")[0].props.onClick();
    assert.equal(render().messageDraft, retryable ? "" : "Keep this explanation");
  }
});

test("only a successful reset or start closes a deliberately opened course introduction", async () => {
  for (const command of ["/api/reset","/api/start"]) {
    const values=[],initial={active_module_id:"m1_effect",profile_id:"medical",learning_pack_id:"effect.medical",
      learning_pack_version:"1.3.0",attempt_id:"attempt.1",status:"active",diagnostic:null,course_profiles:["general","medical"]};
    let cursor=0,fail=true;
    const calls=[];
    const App=component("App",{api:async(path,body)=>{
      calls.push({path,body});
      if (fail) throw new Error("The local test request failed.");
      return {...initial,status:command === "/api/reset" ? "not_started" : "active"};
    },useState(initialValue){const slot=cursor++;
      if (!(slot in values)) values[slot]=initialValue;
      return [values[slot],next=>{values[slot]=typeof next === "function" ? next(values[slot]) : next;}];}});
    const render=()=>{cursor=0;return nodes(App(),node=>node.type === "LearningScreen")[0].props;};
    values[0]=initial;
    render().onIntroductionOpenChange(true);assert.equal(render().isIntroductionOpen,true);
    await render().onRun(command);
    assert.equal(render().isIntroductionOpen,true,"a failed request must preserve the learner's current introduction view");
    assert.equal(render().state.status,"active");
    fail=false;await render().onRun(command);
    assert.equal(render().isIntroductionOpen,false,"successful reset/start must not leave a stale introduction flag behind");
    assert.deepEqual(calls.map(call=>call.path),[command,command]);
  }
});

test("the mobile Tutor has a finite frame, internal transcript and bounded footer", () => {
  const props = {messageDraft:"Unsaved", onMessageDraftChange:()=>{}, messages:Array.from({length:1000}, (_,i)=>({text:String(i)})),
    concepts:[], completed:[], started:[], diagnosticStatuses:[], isWorking:false, canExplain:true, canSend:true,
    onExplain:()=>{}, onNavigate:()=>{}, onSend:()=>{}};
  const mobile = component("TutorPanel")(props);
  assert.equal(mobile.props.height, "min(44rem, 75dvh)");
  assert.equal(mobile.props.style.overflow, "hidden");
  assert.equal(mobile.props.id, "educagent-tutor");
  const log = nodes(mobile, node=>node.props.role === "log")[0];
  assert.equal(log.props.isScrollable, true);
  assert.equal(log.props.style.minHeight, 0);
  assert.equal(log.props.tabIndex, 0);
  const footer = nodes(mobile, node=>node.props.style?.maxHeight === "65%")[0];
  assert.ok(footer && !footer.props.isScrollable, "the footer is bounded but does not scroll as a whole");
  assert.ok(nodes(footer, node=>node.type === "PlainComposer").length, "the composer stays in the fixed part");
  const tools = nodes(footer, node=>node.props.isScrollable)[0];
  assert.equal(tools.props.style.minHeight, 0);
  assert.deepEqual(nodes(tools, node=>node.type === "PlainComposer"), [], "only the concept tools and topics scroll");
  assert.ok(nodes(tools, node=>node.type === "Collapsible").length);
  const desktop = component("TutorPanel", {useMediaQuery:()=>true})(props);
  assert.equal(desktop.props.height, "100%");
  assert.equal(nodes(mobile, node=>node.type === "Collapsible")[0].props.defaultIsOpen, false);
  assert.equal(nodes(desktop, node=>node.type === "Collapsible")[0].props.defaultIsOpen, true);
});

test("mobile navigation uses native fragment links to focusable targets inside the scrolling canvas", () => {
  assert.match(source, /label="Go to Tutor"[\s\S]*?href="#educagent-tutor"/);
  assert.match(source, /id="learning-activity" role="region" aria-label="Learning activity" tabIndex=\{-1\}/);
  const tree = component("TutorPanel")({showBackToActivity:true, messageDraft:"", onMessageDraftChange:()=>{},
    messages:[], concepts:[], completed:[], started:[], diagnosticStatuses:[], isWorking:false,
    canExplain:true, canSend:true, onExplain:()=>{}, onNavigate:()=>{}, onSend:()=>{}});
  assert.equal(tree.props.id, "educagent-tutor");
  assert.equal(tree.props.tabIndex, -1);
  const back = nodes(tree, node=>node.type === "Button" && node.props.label === "Back to activity")[0];
  assert.equal(back.props.href, "#learning-activity");
  assert.equal(back.props.onClick, undefined, "native anchor navigation does not depend on an optional ref");
});

test("desktop keeps the current Final check row visible by scrolling only its topic tools", () => {
  for (const [isWide,isCurrent] of [[true,true],[false,true],[true,false]]) {
    const effects=[],scrolls=[]; let refIndex=0;
    const tools={scrollTop:200,scrollTo:value=>scrolls.push({top:value.top}),getBoundingClientRect:()=>({bottom:300}),
      querySelector:selector=>{assert.equal(selector,"li:last-child"); return {
        getClientRects:()=>[{}],getBoundingClientRect:()=>({bottom:360})};}};
    const render=component("TutorPanel",{useMediaQuery:()=>isWide,useLayoutEffect:effect=>effects.push(effect),
      useRef:()=>({current:refIndex++ === 0 ? null : tools})});
    render({messageDraft:"",onMessageDraftChange:()=>{},messages:[],concepts:[],completed:[],started:[],
      diagnosticStatuses:[],isWorking:false,finalCheck:{is_current:isCurrent,completed_count:2},
      canExplain:true,canSend:true,onExplain:()=>{},onNavigate:()=>{},onSend:()=>{}});
    effects.forEach(effect=>effect());
    assert.deepEqual(scrolls,isWide && isCurrent ? [{top:260}] : [],
      "mobile must retain the question/introduction position");
  }
});

test("shared busy feedback does not label local experiment or scoring requests as Tutor thinking", () => {
  const tree = component("TutorPanel")({messageDraft:"", onMessageDraftChange:()=>{}, messages:[], concepts:[],
    completed:[], started:[], diagnosticStatuses:[], isWorking:true, canExplain:true, canSend:true,
    onExplain:()=>{}, onNavigate:()=>{}, onSend:()=>{}});
  const status = nodes(tree, node=>node.type === "StatusDot")[0];
  assert.equal(status.props.label, "Request in progress");
  const text = nodes(tree, node=>node.type === "Text").map(node=>node.children.join("")).join(" ");
  assert.match(text, /Updating your session/);
  assert.doesNotMatch(text, /thinking/i);
});

test("a completed-route trace cannot keep an invalid concept after switching courses", () => {
  const render = component("RouteCompleteSummary", {
    useState:()=>["previous-course-concept", ()=>{}], useMediaQuery:()=>false,
    moduleConcepts:()=>[{id:"current-concept", label:"Current concept"}], conceptForActivity:()=>null,
  });
  const tree = render({state:{conversation:[],modules:[],active_module_id:"m1_shift"}, isReviewing:true,
    onReviewChange:()=>{}, isWorking:false, onSelectModule:()=>{}});
  const heading = nodes(tree, node=>node.type === "Heading")[0];
  assert.deepEqual(heading.children, ["Current concept"]);
});

test("six course/profile traces keep all final dialogue in a separate bottom section", () => {
  const registry=JSON.parse(fs.readFileSync(path.join(__dirname,"../content/modules.json"),"utf8"));
  for (const entry of registry.modules) for (const [profile,packPath] of Object.entries(entry.profile_pack_paths)) {
    const pack=JSON.parse(fs.readFileSync(path.join(__dirname,"..",packPath),"utf8"));
    const concepts=pack.concepts.map(item=>({id:item.concept_id,label:item.concept_id}));
    const finals=pack.activities.filter(item=>item.workbench?.stage === "capstone");
    const finalIds=finals.map(item=>item.activity_id);
    assert.ok(finalIds.length);
    const topics=concepts.map((concept,index)=>({role:"tutor",kind:"message",attempt_id:`topic.${index}`,
      activity_id:`${concept.id}.practice`,concept_id:concept.id,text:`Topic-only note ${index}`}));
    const finalMessages=finals.map((activity,index)=>({role:index%2 ? "learner" : "tutor",kind:"message",
      activity_id:activity.activity_id,attempt_id:`final.${index}`,concept_id:activity.concept_id,text:`Final-only note ${index}`}));
    delete finalMessages[0].concept_id;
    let selection;
    const render=component("RouteCompleteSummary",{moduleConcepts:()=>concepts,useMediaQuery:()=>false,
      conceptForActivity:(id,list)=>list.find(item=>id?.startsWith(`${item.id}.`))?.id ?? null,
      useState:initial=>{if (selection === undefined) selection=initial;return [selection,next=>{selection=next;}];}});
    const props={state:{active_module_id:entry.module_id,profile_id:profile,modules:[],
      final_check_activity_ids:finalIds,conversation:[...topics,...finalMessages]},
      isReviewing:true,onReviewChange:()=>{},isWorking:false,onSelectModule:()=>{}};
    const traceMessages=tree=>nodes(tree,node=>node.type === "MessageTurn").map(node=>node.props.message);
    let tree=render(props);
    assert.equal(nodes(tree,node=>node.type === "Heading")[0].children.join(""),"Final check");
    assert.deepEqual(traceMessages(tree).map(message=>message.activity_id),finalIds);
    const menu=nodes(tree,node=>node.type === "Button").filter(node=>node.props.label !== "Back to completion");
    assert.deepEqual(menu.map(node=>node.props.label),[...concepts.map(item=>item.label),"Final check"]);
    assert.equal(menu.at(-1).props.variant,"secondary");
    assert.ok(nodes(tree,node=>node.type === "Text").some(node=>node.children.join("") === "Course final check"));
    for (const concept of concepts) {
      nodes(tree,node=>node.type === "Button" && node.props.label === concept.label)[0].props.onClick();
      tree=render(props);
      assert.deepEqual(traceMessages(tree).map(message=>message.text),[topics.find(item=>item.concept_id === concept.id).text]);
      assert.ok(traceMessages(tree).every(message=>!finalIds.includes(message.activity_id)));
    }
    nodes(tree,node=>node.type === "Button" && node.props.label === "Final check")[0].props.onClick();
    assert.deepEqual(traceMessages(render(props)).map(message=>message.activity_id),finalIds);
  }
});

test("trace sections distinguish an empty final from historical packs without a final", () => {
  for (const finalIds of [[],["authored-final.01"]]) {
    const render=component("RouteCompleteSummary",{moduleConcepts:()=>[{id:"topic-a",label:"Topic A"}],
      conceptForActivity:()=>null,useState:()=>[finalIds.length ? "$final-check" : "topic-a",()=>{}]});
    const tree=render({state:{modules:[],conversation:[],final_check_activity_ids:finalIds},isReviewing:true,
      onReviewChange:()=>{},isWorking:false,onSelectModule:()=>{}});
    assert.equal(nodes(tree,node=>node.type === "Button" && node.props.label === "Final check").length,
      finalIds.length ? 1 : 0);
    assert.equal(nodes(tree,node=>node.type === "Heading")[0].children.join(""),finalIds.length ? "Final check" : "Topic A");
    assert.equal(nodes(tree,node=>node.type === "Token")[0].props.label,"No dialogue recorded");
    assert.equal(nodes(tree,node=>node.props.role === "log")[0].props.isScrollable,true);
  }
});

test("the Foundations entry exposes course switching outside the desktop-only rail", () => {
  const declaration = parsed.statements.find(node => ts.isFunctionDeclaration(node) && node.name?.text === "DiagnosticScreen");
  const text = declaration.getText(parsed);
  assert.match(text, /<ModuleSwitcher modules=\{state\.modules\}/);
  const header = text.slice(text.indexOf("header={"), text.indexOf("content={"));
  assert.match(header, /onSelectModule=\{onSelectModule\}/);
});

test("optional example metadata is validated before rendering its readable legend", () => {
  const read = component("readExampleRoles");
  const roles = {treatment:"watering", outcome:"growth", common_cause:"plant type", target_population:"garden plants"};
  assert.equal(JSON.stringify(read(roles)), JSON.stringify(roles));
  for (const invalid of [null, undefined, [], "roles", {...roles,common_cause:" "}, {...roles,outcome:12},
    {treatment:roles.treatment, outcome:roles.outcome, common_cause:roles.common_cause}]) assert.equal(read(invalid), null);
  const Message = component("MessageTurn", {readExampleRoles:read});
  const first = Message({message:{role:"tutor",kind:"message",text:"Suppose we compare plants.",example_roles:roles}, concepts:[]});
  assert.equal(nodes(first, node=>node.type === "ExampleRolesLegend").length, 1);
  const later = Message({message:{role:"tutor",kind:"message",text:"Keep plant type fixed."}, concepts:[]});
  assert.equal(nodes(later, node=>node.type === "ExampleRolesLegend").length, 0);
  assert.equal(nodes(first, node=>node.type === "RichText")[0].props.text, "Suppose we compare plants.");
});

test("the shared message legend is initially visible, accessible and uses plain-language labels", () => {
  const roles = {treatment:"watering", outcome:"growth", common_cause:"plant type", target_population:"garden plants"};
  const tree = component("ExampleRolesLegend")({roles});
  assert.equal(tree.props.defaultIsOpen, true);
  assert.equal(nodes(tree, node=>node.props.role === "note")[0].props["aria-label"], "Variables in this example");
  const text = nodes(tree, node=>node.type === "Text").map(node=>node.children.join("")).join(" ");
  for (const value of Object.values(roles)) assert.ok(text.includes(value));
  assert.match(text, /Shared cause before the action/);
  assert.equal((source.match(/<MessageTurn\b/g) || []).length, 2, "live chat and trace share MessageTurn");
});

test("new activity navigation restores the canvas and focus without reacting to chat or experiment refreshes", () => {
  const screen = parsed.statements.find(node=>ts.isFunctionDeclaration(node) && node.name?.text === "LearningScreen");
  const effect = screen.body.statements.filter(ts.isExpressionStatement).map(node=>node.expression)
    .find(node=>ts.isCallExpression(node) && node.expression.getText(parsed) === "useLayoutEffect"
      && node.arguments[1]?.getText(parsed).includes("state.activity_id"));
  assert.ok(effect);
  const code = ts.transpileModule(`function navigationEffect() {
    return {run:${effect.arguments[0].getText(parsed)}, deps:${effect.arguments[1].getText(parsed)}};
  }`, {compilerOptions:{target:ts.ScriptTarget.ES2022}}).outputText;
  const moves = [], state = {status:"active", active_module_id:"m1_shift", profile_id:"medical",
    attempt_id:"attempt.4", activity_id:"distribution-shift.quiz", experiment:{revision:3}, conversation:[]};
  const context = vm.createContext({state, showIntroduction:false, showFinalCheckIntroduction:false,
    finalCheckTitleRef:{current:{focus:value=>moves.push(["final-intro-focus",JSON.stringify(value)])}},
    contentRef:{current:{scrollTo:value=>moves.push(["scroll",JSON.stringify(value)])}},
    document:{getElementById:id=>{assert.equal(id,"learning-activity"); return {focus:value=>moves.push(["focus",JSON.stringify(value)])};}},
  });
  vm.runInContext(code, context);
  const initial = context.navigationEffect();
  initial.run();
  assert.deepEqual(moves, [["scroll",'{"top":0,"left":0}'], ["focus",'{"preventScroll":true}']]);
  state.conversation.push({text:"A new reply"});
  state.experiment.revision++;
  assert.deepEqual([...context.navigationEffect().deps],[...initial.deps], "no repeated focus or draft remount on same activity updates");
  state.activity_id = "distribution-shift.challenge";
  assert.notDeepEqual([...context.navigationEffect().deps],[...initial.deps]);
  moves.length=0;
  context.showFinalCheckIntroduction=true;
  context.navigationEffect().run();
  assert.deepEqual(moves,[["scroll",'{"top":0,"left":0}'],["final-intro-focus",'{"preventScroll":true}']]);
  moves.length=0;
  context.showFinalCheckIntroduction=false;
  context.navigationEffect().run();
  assert.deepEqual(moves,[["scroll",'{"top":0,"left":0}'],["focus",'{"preventScroll":true}']],
    "starting the same final attempt focuses its question even without an activity change");
  for (const overrides of [{showIntroduction:true}, {state:{...state,status:"completed"}},
    {state:{...state,profile_required:true,preview_mode:false}}]) {
    moves.length = 0;
    const previous = {state:context.state,showIntroduction:context.showIntroduction};
    Object.assign(context, overrides);
    context.navigationEffect().run();
    assert.deepEqual(moves, []);
    Object.assign(context,previous);
  }
});

test("a completed topic keeps its checkmark during review without fabricating full-course credit", () => {
  const concepts = [{id:"topic-a",label:"First topic"},{id:"topic-b",label:"Second topic"},{id:"topic-c",label:"Third topic"}];
  const tree = component("RouteList")({concepts,completed:[],topicCompleted:["topic-a"],started:["topic-a","topic-b"],
    current:"topic-a", diagnosticStatuses:[{concept_id:"topic-c",status:"correct"}]});
  const rows = nodes(tree,node=>node.type === "ListItem");
  const text = row=>nodes(row.props.endContent,node=>node.type === "Text").map(node=>node.children.join("")).join(" ");
  assert.equal(text(rows[0]), "✓ Completed");
  assert.equal(rows[0].props.isSelected, true);
  assert.equal(text(rows[1]), "In progress");
  assert.equal(text(rows[2]), "Entry check correct");
  const routeCredit = component("conceptsWithRouteCredit")({topic_practice_completed_concept_ids:["topic-a"]});
  assert.deepEqual([...routeCredit], []);
  const pending = component("RouteList")({concepts,current:"topic-a",completed:[],topicCompleted:[]});
  assert.equal(text(nodes(pending,node=>node.type === "ListItem")[0]), "? Learning");
});

test("entry and Tutor directories receive the server-owned topic completion separately from final credit", () => {
  const concepts = [{id:"topic-a",label:"First topic"}];
  const state = {diagnostic:null,modules:[],completed_concept_ids:[],topic_practice_completed_concept_ids:["topic-a"]};
  const entry = component("EntryRouteRail", {moduleConcepts:()=>concepts,conceptsWithPractice:()=>[],
    conceptsWithRouteCredit:component("conceptsWithRouteCredit")})({state,isWorking:false,onSelectModule:()=>{}});
  const route = nodes(entry,node=>node.type === "RouteList")[0];
  assert.deepEqual([...route.props.completed], []);
  assert.deepEqual([...route.props.topicCompleted], ["topic-a"]);
  const tutor = component("TutorPanel")({messageDraft:"",onMessageDraftChange:()=>{},messages:[],concepts,completed:[],
    topicCompleted:["topic-a"],started:[],diagnosticStatuses:[],isWorking:false,canSend:true,
    canExplain:true,onExplain:()=>{},onNavigate:()=>{},onSend:()=>{}});
  const trigger = nodes(tutor,node=>node.type === "Collapsible")[0].props.trigger;
  assert.equal(trigger.children.join(""), "Topics completed · 1 of 1");
  const text = nodes(tutor,node=>node.type === "Text").map(node=>node.children.join("")).join(" ");
  assert.match(text, /final assessment and full course are separate/);
});

test("Final check is the last independent navigation row and never selects its tested topic", () => {
  const concepts = [{id:"topic-a",label:"First topic"},{id:"topic-b",label:"Second topic"}];
  const clicked = [];
  const render = finalCheck => component("RouteList")({concepts, current:"topic-a",
    topicCompleted:concepts.map(item=>item.id), finalCheck, onFinalCheck:()=>clicked.push("final"),
    onNavigate:id=>clicked.push(id)});
  const final = {status:"in_progress",is_current:true,completed_count:0,total_count:2};
  const rows = nodes(render(final),node=>node.type === "ListItem");
  assert.deepEqual(rows.map(row=>row.props.label),["First topic","Second topic","Final check"]);
  assert.deepEqual(rows.map(row=>row.props.isSelected),[false,false,true]);
  const text = row=>nodes(row.props.endContent,node=>node.type === "Text").map(node=>node.children.join("")).join(" ");
  assert.equal(text(rows[0]),"✓ Completed");
  assert.equal(text(rows[2]),"In progress","completed topics do not complete the final");
  rows[2].props.onClick();
  assert.deepEqual(clicked,["final"]);
  for (const [status,label] of [["not_started","Later"],["completed","✓ Completed"]]) {
    const row = nodes(render({...final,status,is_current:false}),node=>node.type === "ListItem").at(-1);
    assert.equal(text(row),label);
    assert.equal(row.props.isSelected,false);
  }
  const quiz = component("RouteList")({concepts,quizMode:true,finalCheck:final,current:"topic-a"});
  assert.equal(nodes(quiz,node=>node.type === "ListItem").length,concepts.length,"entry quiz is separate");
});

test("all course profiles label and navigate Final check without changing the scoring concept", async () => {
  const declaration = parsed.statements.find(node=>ts.isFunctionDeclaration(node) && node.name?.text === "LearningScreen");
  const jsxNames = [...new Set([...declaration.getText(parsed).matchAll(/<([A-Z][A-Za-z0-9]*)\b/g)].map(match=>match[1]))];
  for (const isWide of [true,false]) for (const moduleId of ["causality_m0","m1_effect","m1_shift"])
    for (const profileId of ["general","medical"]) {
      const calls = [], concepts=[{id:"topic-a",label:"First topic"}];
      const render = component("LearningScreen", {
        ...Object.fromEntries(jsxNames.map(name=>[name,name])),
        useState:initial=>[initial,()=>{}],useLayoutEffect:()=>{},useMediaQuery:()=>isWide,
        moduleConcepts:()=>concepts,conceptForActivity:()=>"topic-a",conceptsWithPractice:()=>[],
        conceptsWithRouteCredit:()=>[],requestId:prefix=>`test.${prefix}`,ENTRY_ROUTE_PANEL_STYLE:{},
      });
      const state={status:"active",title:"Course",course_title:"Course",profile_id:profileId,
        active_module_id:moduleId,activity_concept_id:"topic-a",activity_id:"final.1",attempt_id:"attempt.1",
        learning_pack_id:"test-pack",learning_pack_version:"test-version",
        question:"Which conclusion follows?",modules:[],diagnostic:null,tutor_status:"ready",
        final_check:{status:"in_progress",is_current:true,completed_count:0,total_count:1},
        workbench:{stage:"capstone"},can_send_message:true};
      const props={state,isWorking:false,error:null,isIntroductionOpen:false,onIntroductionOpenChange:()=>{},
        messageDraft:"",onMessageDraftChange:()=>{},onRun:async (...args)=>calls.push(args),onChangeProfile:()=>{}};
      const tree=render(props);
      assert.ok(nodes(tree,node=>node.type === "Text").some(node=>node.children.join("") === "Course · Final check"));
      const tutor=nodes(tree,node=>node.type === "TutorPanel")[0];
      assert.equal(tutor.props.finalCheck,state.final_check);
      assert.equal(tutor.props.conceptId,"topic-a","Tutor and scoring keep the tested concept");
      const opening={role:"tutor",kind:"elicit",attempt_id:state.attempt_id,activity_id:state.activity_id,text:"Automatic opening"};
      const noQuestion=render({...props,state:{...state,conversation:[opening]}});
      assert.equal(nodes(noQuestion,node=>node.type === "TutorPanel")[0].props.messages.length,0);
      for (const kind of ["message","support_request"]) {
        const request={role:"learner",kind,attempt_id:state.attempt_id,activity_id:state.activity_id,text:"Help me understand"};
        const reply={...opening,kind:"hint",text:"Here is a separate example"};
        const discussion=render({...props,state:{...state,conversation:[opening,request,reply]}});
        const panel=nodes(discussion,node=>node.type === "TutorPanel")[0];
        assert.deepEqual([...panel.props.messages],[request,reply],"intro chat and Explain replies remain visible");
        assert.equal(panel.props.canSend,true);
        assert.equal(panel.props.canExplain,true);
        assert.equal(nodes(discussion,node=>node.props.id === "learning-activity")[0].props.style.display,"none",
          "discussion does not start or reveal the final question");
      }
      await tutor.props.onFinalCheck();
      assert.equal(calls[0][0],"/api/final-check");
      assert.equal(calls[0][1].request_id,"test.final-check");
      const topic=render({...props,state:{...state,final_check:{...state.final_check,is_current:false}}});
      assert.ok(nodes(topic,node=>node.type === "Text").some(node=>node.children.join("") === "Course · First topic"));
      const complete=render({...props,state:{...state,status:"completed"}});
      const trace=nodes(complete,node=>node.type === "RouteCompleteSummary")[0];
      assert.equal(trace.props.key,`${moduleId}.${profileId}.test-pack.test-version`,
        "trace selection remounts for each module/profile/pack version");
      const nextVersion=render({...props,state:{...state,status:"completed",learning_pack_version:"next-version"}});
      assert.notEqual(nodes(nextVersion,node=>node.type === "RouteCompleteSummary")[0].props.key,trace.props.key);
      for (const isolated of [{preview_mode:true},{lesson_is_sample:true}]) {
        const isolatedTree=render({...props,state:{...state,...isolated}});
        assert.equal(nodes(isolatedTree,node=>node.type === "TutorPanel")[0].props.finalCheck,null,
          "isolated previews cannot call normal final navigation");
      }
    }
});

test("Final check opens with an honest optional transition and begins without scoring or navigation", () => {
  const declaration = parsed.statements.find(node=>ts.isFunctionDeclaration(node) && node.name?.text === "LearningScreen");
  const jsxNames = [...new Set([...declaration.getText(parsed).matchAll(/<([A-Z][A-Za-z0-9]*)\b/g)].map(match=>match[1]))];
  const values=[], calls=[]; let cursor=0;
  const render = component("LearningScreen", {
    ...Object.fromEntries(jsxNames.map(name=>[name,name])),
    useState(initial) {const slot=cursor++; if (!(slot in values)) values[slot]=initial;
      return [values[slot],value=>{values[slot]=value;}];},
    useLayoutEffect:()=>{},moduleConcepts:()=>[{id:"topic-a",label:"First topic"}],
    conceptForActivity:()=>"topic-a",conceptsWithPractice:()=>[],conceptsWithRouteCredit:()=>[],
    ENTRY_ROUTE_PANEL_STYLE:{},
  });
  const state={status:"active",title:"Course",profile_id:"general",active_module_id:"causality_m0",
    learning_pack_version:"1.8.0",attempt_id:"final.1",activity_id:"final.01",activity_concept_id:"topic-a",
    question:"Which conclusion follows?",modules:[],diagnostic:null,tutor_status:"ready",
    final_check:{status:"in_progress",is_current:true,completed_count:0,total_count:9}};
  const screen=(changes={})=>{cursor=0; return render({state:{...state,...changes},isWorking:false,error:null,
    isIntroductionOpen:false,onIntroductionOpenChange:()=>{},onRun:(...args)=>calls.push(args)});};
  const intro=tree=>nodes(tree,node=>node.type === "FinalCheckIntroduction")[0];
  let tree=screen();
  assert.equal(intro(tree).props.topicsComplete,false,"an early jump cannot congratulate unfinished topics");
  assert.equal(intro(tree).props.questionCount,9);
  assert.equal(nodes(tree,node=>node.props.id === "learning-activity")[0].props.style.display,"none");
  assert.equal(nodes(tree,node=>node.type === "TutorPanel")[0].props.showBackToActivity,false,
    "mobile must not link to a hidden question before the learner begins");
  assert.equal(intro(screen({topic_practice_completed_concept_ids:["topic-a"]})).props.topicsComplete,true);
  intro(tree).props.onStart();
  assert.deepEqual(calls,[],"Begin only confirms the existing attempt, without Start/Continue/grade requests");
  tree=screen();
  assert.equal(intro(tree),undefined);
  assert.equal(nodes(tree,node=>node.props.id === "learning-activity")[0].props.style.display,undefined);
  for (const changed of [{profile_id:"medical"},{active_module_id:"m1_effect"},
    {learning_pack_version:"next-version"},{attempt_id:"another-final"}]) assert.ok(intro(screen(changed)));
  values[1]=null;
  for (const resumed of [{final_check:{...state.final_check,completed_count:1}}, {assessment_submitted:true},
    {assessment_accepted:true},{can_continue:true},{review_mode:true},{preview_mode:true},{lesson_is_sample:true}]) {
    assert.equal(intro(screen(resumed)),undefined,"existing answers and review/preview routes resume directly");
  }
  const text = complete=>nodes(component("FinalCheckIntroduction")({courseTitle:"Course",topicCount:9,
    questionCount:9,topicsComplete:complete,isWorking:false}),node=>node.type === "Heading" || node.type === "Text")
    .map(node=>node.children.join("")).join(" ");
  assert.match(text(true),/Congratulations!.*completed all 9 topics/);
  assert.doesNotMatch(text(false),/Congratulations|completed all/);
  assert.match(text(false),/Ready for the final check/);
});

test("Quiz and Challenge use only their explicitly projected picture; Explanation keeps its own visible image", () => {
  const questionImage = {path:"media/questions/new-case.png",alt_text:"The current question setting."};
  const explanationImage = {path:"media/lessons/example.png",alt_text:"The worked example setting."};
  const lesson = {concept_id:"topic-a",profile_id:"general",challenge_activity_id:"topic-a.challenge",title:"An explanation",
    definition:"A definition",hook:"A concrete example",worked_steps:[],sources:[],scenario_image:explanationImage};
  const render = reading=>component("LessonCanvas", {useState:()=>[reading,()=>{}],moduleConcepts:()=>[{id:"topic-a",label:"Topic"}],
    labelFromConceptId:id=>id});
  for (const isChallenge of [false,true]) {
    const state = {activity_id:isChallenge ? "topic-a.challenge" : "topic-a.quiz",activity_is_transfer:isChallenge,
      assessment_submitted:false,can_continue:false,scenario_image:questionImage,question:"What do the records show?",choices:[]};
    const tree = render(false)({lesson,state,isWorking:false,onRun:()=>{}});
    assert.equal(nodes(tree,node=>node.type === "QuestionPrompt")[0].props.image,questionImage);
    const noPicture = render(false)({lesson,state:{...state,scenario_image:null},isWorking:false,onRun:()=>{}});
    assert.equal(nodes(noPicture,node=>node.type === "QuestionPrompt")[0].props.image,null,
      "a different lesson illustration is not silently reused for the question");
  }
  const explanation = render(true)({lesson,state:{question:"Question",choices:[]},isWorking:false,onRun:()=>{}});
  assert.equal(nodes(explanation,node=>node.type === "QuestionIllustration")[0].props.image,explanationImage);
  assert.equal(nodes(explanation,node=>node.type === "Collapsible")[0].props.defaultIsOpen,false,
    "detailed text remains optional, not the example image");
});

test("a rejected quiz stays on its answers and opens the explanation only on request", () => {
  const lesson = {concept_id:"topic-a",profile_id:"general",challenge_activity_id:"topic-a.challenge",title:"An explanation",
    definition:"A definition",hook:"A concrete example",worked_steps:[],sources:[],scenario_image:null};
  const feedback = {accepted:false,option_id:"topic-a.wrong",text:"Not yet. Compare the two variables."};
  const state = {activity_id:"topic-a.quiz",activity_is_transfer:false,assessment_submitted:true,assessment_accepted:false,
    can_continue:false,answer_feedback:feedback,question:"Which statement fits?",choices:[{option_id:"topic-a.wrong",text:"Wrong"}]};
  const render = (reading, opened) => component("LessonCanvas", {useState:()=>[reading,value=>opened.push(value)],
    useEffect:effect=>effect(), moduleConcepts:()=>[{id:"topic-a",label:"Topic"}], labelFromConceptId:id=>id});
  for (const accepted of [false,true]) {
    const opened = [];
    render(false, opened)({lesson,state:{...state,assessment_accepted:accepted,can_continue:accepted,
      answer_feedback:{...feedback,accepted}},isWorking:false,onRun:()=>{}});
    assert.deepEqual(opened,[accepted]);
  }
  const answering = render(false, [])({lesson,state,isWorking:false,onRun:()=>{}});
    const topic = nodes(answering,node=>node.type === "Heading" && node.children.includes("Topic"))[0];
    assert.equal(topic.props.level,2);
    const topicStack = answering.children[0].children[0];
    assert.equal(topicStack.type,"VStack", "topic sequence belongs below its heading");
    assert.equal(topicStack.children[0],topic);
  assert.equal(nodes(answering,node=>node.type === "AnswerCommitment").length,1);
  assert.equal(nodes(answering,node=>node.type === "AnswerFeedbackNotice")[0].props.feedback,feedback);
  assert.ok(nodes(answering,node=>node.type === "Button" && node.props.label === "Show the explanation").length);
  const reading = render(true, [])({lesson,state,isWorking:false,onRun:()=>{}});
    const definition = nodes(reading,node=>node.props.as === "blockquote")[0];
    assert.equal(definition.props["aria-label"],"Course definition");
    assert.equal(nodes(definition,node=>node.type === "InlineMarkup")[0].props.text,lesson.definition);
    assert.ok(nodes(definition,node=>node.type === "a" && node.props.href === "/sources.html").length);
  const retries = nodes(reading,node=>node.type === "Button" && /try/i.test(node.props.label ?? ""));
  assert.deepEqual(retries.map(node=>node.props.label),["Try the quiz again"]);
  const notice = component("AnswerFeedbackNotice", {Banner:"Banner"})({feedback,choices:state.choices});
  assert.equal(nodes(notice,node=>node.type === "Banner")[0].props.endContent,undefined);
});

test("the asked question is the heading and earlier sentences stay readable context", () => {
  const split = component("splitQuestion");
  assert.deepEqual({...split("A clinic keeps this table. Each row is one patient. Which list names the variables?")},
    {context:"A clinic keeps this table. Each row is one patient.", question:"Which list names the variables?"});
  assert.deepEqual({...split("What does this arrow mean?")}, {context:"", question:"What does this arrow mean?"});
  assert.deepEqual({...split("Pick one. Then explain your reason.")}, {context:"", question:"Pick one. Then explain your reason."});
  assert.deepEqual({...split("The chance is 0.40 under one offer. Which interpretation is correct?")},
    {context:"The chance is 0.40 under one offer.", question:"Which interpretation is correct?"});
  const image = {path:"media/questions/current.png",alt_text:"A neutral study setting."};
  const renderPrompt = component("QuestionPrompt", {splitQuestion:split,questionGraphNodes:component("questionGraphNodes")});
  const prompt = renderPrompt({text:"Records pair two values. Which statement fits?", image});
  assert.equal(nodes(prompt,node=>node.type === "Heading")[0].children[0].props.text,"Records pair two values.",
    "the scenario at the top is the page title");
  assert.equal(nodes(prompt,node=>node.type === "Text")[0].children[0].props.text,"Which statement fits?");
  assert.deepEqual({...nodes(prompt,node=>node.type === "Text")[0].props},{type:"large",weight:"medium"},
    "the question is bold text directly above the answers");
  assert.deepEqual(prompt.children.filter(Boolean).map(child=>child.type),["Heading","QuestionIllustration","Text"],
    "scenario title and picture come first; the question sits last, directly above the answers");
  const workbench = {title:"Example records",introduction:"Each row is one record.",scenario_id:"s",stage:"investigate",tables:[]};
  const card = renderPrompt({text:"Records pair two values. Which statement fits?", image, workbench});
  assert.equal(card.children.at(-1).type,"Text");
  assert.equal(nodes(card.children[0],node=>node.type === "Heading").length,1,
    "the scenario title leads at full reading width, above the card");
  const grid = nodes(card,node=>node.type === "Grid")[0];
  assert.deepEqual(grid.children.map(child=>child.type),["QuestionIllustration","ComparisonWorkbenchCanvas"],
    "with data, the picture and table share one card above the question");
  const stacked = renderPrompt({text:"Records pair two values. Which statement fits?", workbench});
  assert.deepEqual(stacked.children.filter(Boolean).map(child=>child.type),["Heading","QuestionIllustration","ComparisonWorkbenchCanvas","Text"]);
  const single = renderPrompt({text:"What does this arrow mean?", image});
  assert.deepEqual(single.children.filter(Boolean).map(child=>child.type),["QuestionIllustration","Heading"],
    "a one-sentence prompt has no scenario, so the question itself is the title");
});

test("the four authored causal-graph questions draw only their disclosed nodes before the picture", () => {
  const parse = component("questionGraphNodes");
  const prompt = component("QuestionPrompt", {splitQuestion:component("splitQuestion"),questionGraphNodes:parse});
  const expected = {
    general:[["Sleep","Concentration"],["Tutorial","Continued use","Renewed subscription"]],
    medical:[["Drug dose","Symptom score"],["Physiotherapy","Mobility","Discharge readiness"]],
  };
  for (const [profile, pairs] of Object.entries(expected)) {
    const pack = JSON.parse(fs.readFileSync(path.join(__dirname,`../content/foundation_${profile}_course_1_8_0.json`),"utf8"));
    for (const [index, stage] of ["practice","transfer"].entries()) {
      const activity = pack.activities.find(item=>item.activity_id === `basic-dag-language.${stage}`);
      const text = pack.resources.find(item=>item.resource_id === activity.question_resource_id).text;
      const image = {path:"media/current-case.png",alt_text:"Current case"};
      const tree = prompt({text,image});
      const children = tree.children.filter(Boolean);
      const graph = children.find(item=>item.type === "QuestionCausalGraph");
      assert.deepEqual([...graph.props.nodes],pairs[index]);
      assert.ok(children.indexOf(graph) < children.findIndex(item=>item.type === "QuestionIllustration"));
      assert.equal(children[0].children[0].props.text,"A proposed causal graph");
      assert.equal(children.at(-1).type,"Text","the asked question still sits above the answer choices");
    }
  }
  for (const text of ["A → B without authored markup", "`A ← B → C`", "`A ↔ B → C`", "`A → A`", "`A → `", "Ordinary question?"])
    assert.equal(parse(text),null,"unsupported or non-authored chains keep their original text");
});

test("question graphs retain labels, direction and accessible edges across narrow and wide layouts", () => {
  const labels = ["Physiotherapy","Mobility","Discharge readiness"];
  for (const wide of [false,true]) {
    const tree = component("QuestionCausalGraph",{useMediaQuery:()=>wide})({nodes:labels});
    assert.equal(tree.props.role,"img");
    assert.match(tree.props["aria-label"],/Arrow from Physiotherapy to Mobility\. Arrow from Mobility to Discharge readiness\./);
    assert.equal(tree.children[0].type,wide ? "HStack" : "VStack");
    assert.deepEqual(nodes(tree,node=>node.type === "Text").map(node=>node.children.join("")),labels);
    const arrows = nodes(tree,node=>node.type === "svg");
    assert.equal(arrows.length,2);
    assert.ok(arrows.every(node=>node.props["aria-hidden"] === "true"));
    assert.ok(nodes(tree,node=>node.type === "path").every(node=>node.props.d ===
      (wide ? "M2 16H28 M21 9L28 16L21 23" : "M16 2V28 M9 21L16 28L23 21")));
    assert.ok(nodes(tree,node=>node.type === "Text").every(node=>node.props.maxLines === undefined),"labels are never truncated");
  }
});

test("script-focused containers keep focus management without a page-wide focus ring", () => {
  assert.match(source, /const SCRIPT_FOCUS_STYLE: CSSProperties = \{outline:"none"\}/);
  assert.match(source, /document\.getElementById\("learning-activity"\)\?\.focus\(\{preventScroll:true\}\)/,
    "new activities still move focus for screen readers and the next Tab");
  assert.match(source, /id="learning-activity"[^>]*tabIndex=\{-1\}[\s\S]{0,120}style=\{showIntroduction \|\| showFinalCheckIntroduction \? \{display:"none"\} : SCRIPT_FOCUS_STYLE\}/);
  assert.match(source, /id="educagent-tutor"[\s\S]{0,200}style=\{\{\.\.\.SCRIPT_FOCUS_STYLE,/);
  assert.match(source, /ref=\{titleRef\} tabIndex=\{-1\}[^>]*style=\{SCRIPT_FOCUS_STYLE\}/);
});

test("the correct-answer bar has no tinted box and aligns with the question", () => {
  const bar = component("CommitBar")({isWorking:false,onContinue:()=>{}});
  assert.equal(bar.type,"VStack");
  assert.deepEqual(nodes(bar,node=>node.type === "Section"),[]);
  assert.ok(nodes(bar,node=>node.type === "Button" && node.props.label === "Continue").length);
});

test("backtick-marked units such as causal-graph chains render as inline code", () => {
  const markup = component("InlineMarkup")({text:"A proposed graph contains `Sleep → Concentration`. What does it mean?"});
  assert.deepEqual(markup.children.map(child=>typeof child === "string" ? child : [child.type, child.children.join("")]),
    ["A proposed graph contains ", ["Code","Sleep → Concentration"], ". What does it mean?"]);
  assert.deepEqual(component("InlineMarkup")({text:"No marked unit."}).children,["No marked unit."]);
  assert.equal(markup.children[1].props.style.background,"var(--color-background-teal)","the chain is highlighted");
});

test("topic tables stay in the lesson flow; only final-check tables use the final canvas", () => {
  assert.match(source, /state\.lesson && !state\.causal_scene && state\.workbench\?\.stage !== "capstone"/);
  assert.match(source, /image=\{diagnostic\.scenario_image\} workbench=\{diagnostic\.workbench\}/);
  assert.doesNotMatch(source, /CanvasColumns|Eyebrow>Scenario context/, "one column; the quiz picture is not repeated in the rail");
  assert.doesNotMatch(source, /fontSize: "1[123]px"/);
});

test("question illustrations use a wide crop capped to the window, carry alt text and never fabricate an absent image", () => {
  const render = component("QuestionIllustration");
  for (const image of [null,undefined]) assert.equal(render({image}), null);
  const image = {path:"media/questions/current.png",alt_text:"A neutral study setting."};
  const tree = render({image});
  assert.equal(tree.props.width,"100%");
  assert.equal(tree.props.maxWidth,"70vh", "a 2:1 picture at most 70vh wide is at most 35vh tall");
  const ratio = nodes(tree,node=>node.type === "AspectRatio")[0];
  assert.equal(ratio.props.ratio,2);
  assert.equal(nodes(tree,node=>node.type === "img")[0].props.alt,image.alt_text);
  assert.equal(nodes(tree,node=>node.type === "img")[0].props.src,"/media/questions/current.png");
  const canvas = component("InvestigationCanvas")({image,recordText:"A question",conceptId:null,concepts:[]});
  assert.equal(nodes(canvas,node=>node.type === "QuestionPrompt")[0].props.image,image);
});

test("entry course actions reserve a right column and use visible buttons across profiles", () => {
  for (const profile of ["general", "medical"]) {
    const modules = [
      {module_id:"causality_m0",title:"Causality foundations",status:"available"},
      {module_id:"m1_effect",title:"Effect of an intervention",status:"available"},
      {module_id:"m1_shift",title:"Robust prediction or generation",status:"completed"},
    ];
    for (const active of modules) {
      const selected = [];
      const render = component("EntryRouteRail", {moduleConcepts:()=>[],conceptsWithRouteCredit:()=>[],conceptsWithPractice:()=>[]});
      const tree = render({state:{profile_id:profile,modules,active_module_id:active.module_id},
        isWorking:false,onSelectModule:id=>selected.push(id)});
      const rows = nodes(tree,node=>node.type === "Grid");
      const alternatives = modules.filter(module=>module.module_id !== active.module_id);
      assert.equal(rows.length,2);
      rows.forEach((row,index)=>{
        const module = alternatives[index];
        assert.equal(row.props.style.gridTemplateColumns,"minmax(0, 1fr) auto");
        assert.equal(row.props.width,"100%");
        assert.equal(row.props.align,"center");
        assert.equal(row.children[0].props.style.minWidth,0,"the title yields width instead of moving its action");
        assert.equal(nodes(row.children[0],node=>node.type === "Text")[0].children[0],module.title);
        const action = nodes(row,node=>node.type === "Button")[0];
        assert.equal(action.props.variant,"secondary");
        assert.equal(action.props.size,"sm");
        assert.equal(action.props.isDisabled,false);
        assert.equal(action.props["aria-label"],`${module.status === "completed" ? "Review" : "Start"} ${module.title}`);
        action.props.onClick();
      });
      assert.deepEqual(selected,alternatives.map(module=>module.module_id));
    }
  }
});

test("entry course buttons retain working and locked restrictions", () => {
  const render = component("EntryRouteRail", {moduleConcepts:()=>[],conceptsWithRouteCredit:()=>[],conceptsWithPractice:()=>[]});
  const modules = [{module_id:"current",title:"Current course",status:"available"},
    {module_id:"locked",title:"A long course title that wraps beside its locked action",status:"locked"}];
  for (const isWorking of [false,true]) {
    const tree = render({state:{modules,active_module_id:"current"},isWorking,onSelectModule:()=>{}});
    const action = nodes(tree,node=>node.type === "Button")[0];
    assert.equal(action.props.label,"Locked");
    assert.equal(action.props.isDisabled,true);
    assert.ok(nodes(tree,node=>node.type === "Text").some(node=>node.children.includes("Complete the foundation first")));
  }
  const tree = render({state:{modules:[modules[0],{...modules[1],status:"available"}],active_module_id:"current"},
    isWorking:true,onSelectModule:()=>{}});
  assert.equal(nodes(tree,node=>node.type === "Button")[0].props.isDisabled,true);
});

test("API failures show only a validated upstream HTTP integer, never a response body or arbitrary status", async () => {
  class ApiFailure extends Error {
    constructor(message,code,retryable) {super(message); this.code=code; this.retryable=retryable;}
  }
  const payload = {error:"Tutor request failed",diagnostic:"ModelHTTPError",code:"tutor_unavailable",retryable:true,
    detail:"Progress is preserved.",recovery:"Reconnect to retry.",request_id:"safe-request",
    body:"PRIVATE_UPSTREAM_BODY",response_body:"PRIVATE_UPSTREAM_RESPONSE"};
  async function failure(status) {
    const api = component("api", {ApiFailure,AbortController,DOMException,
      window:{setTimeout:()=>1,clearTimeout:()=>{}},
      fetch:async()=>({ok:false,status:503,json:async()=>({...payload,upstream_status:status})}),
    });
    let observed;
    await assert.rejects(api("/api/state"),error=>{observed=error; return error instanceof ApiFailure;});
    assert.equal(observed.code,"tutor_unavailable");
    assert.equal(observed.retryable,true);
    assert.match(observed.message,/Progress is preserved.*Reconnect to retry.*safe-request/);
    assert.doesNotMatch(observed.message,/PRIVATE_UPSTREAM/);
    return observed.message;
  }
  for (const status of [100,500,599]) assert.match(await failure(status),new RegExp(`Upstream HTTP ${status}\\.`));
  for (const status of [undefined,null,false,99,600,500.1,NaN,Infinity,"500","500<script>malicious</script>",
    {toString:()=>"malicious",valueOf:()=>500},[500]]) {
    const message = await failure(status);
    assert.doesNotMatch(message,/Upstream HTTP|malicious|script/);
  }
});
