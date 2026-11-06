import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import type { CSSProperties, ReactNode, RefObject } from "react";
import ReactMarkdown from "react-markdown";
import rehypeKatex from "rehype-katex";
import remarkMath from "remark-math";
import { AppShell } from "@astryxdesign/core/AppShell";
import { AspectRatio } from "@astryxdesign/core/AspectRatio";
import { Avatar } from "@astryxdesign/core/Avatar";
import { Banner } from "@astryxdesign/core/Banner";
import { Button } from "@astryxdesign/core/Button";
import { Code } from "@astryxdesign/core/Code";
import { Card } from "@astryxdesign/core/Card";
import { CheckboxInput } from "@astryxdesign/core/CheckboxInput";
import { CheckboxList, CheckboxListItem } from "@astryxdesign/core/CheckboxList";
import { Collapsible } from "@astryxdesign/core/Collapsible";
import { Divider } from "@astryxdesign/core/Divider";
import { Dialog, DialogHeader } from "@astryxdesign/core/Dialog";
import { Grid } from "@astryxdesign/core/Grid";
import { Heading } from "@astryxdesign/core/Heading";
import { HStack } from "@astryxdesign/core/HStack";
import {
  Layout,
  LayoutContent,
  LayoutHeader,
  LayoutPanel,
} from "@astryxdesign/core/Layout";
import { List, ListItem } from "@astryxdesign/core/List";
import { Popover } from "@astryxdesign/core/Popover";
import { RadioList, RadioListItem } from "@astryxdesign/core/RadioList";
import { Section } from "@astryxdesign/core/Section";
import { Selector } from "@astryxdesign/core/Selector";
import { Slider } from "@astryxdesign/core/Slider";
import { StatusDot } from "@astryxdesign/core/StatusDot";
import { proportional, Table } from "@astryxdesign/core/Table";
import { Text } from "@astryxdesign/core/Text";
import { TextArea } from "@astryxdesign/core/TextArea";
import { Token } from "@astryxdesign/core/Token";
import { VStack } from "@astryxdesign/core/VStack";
import { useMediaQuery } from "@astryxdesign/core/hooks";
import { moduleLocation, previewLocation } from "./portal-url";

type Choice = { option_id: string; text: string };
type AnswerFeedback = { accepted: boolean; option_id: string; text: string };
type ScenarioImage = { path: string; alt_text: string };
type SceneEdge = { parent_id: string; child_id: string };
type SceneNode = { node_id: string; label: string; initially_visible: boolean };
type SceneRecord = {
  umbrella_carried: "yes" | "no";
  pavement_wet: "yes" | "no";
  arrivals: number;
};
type ExampleRoles = { treatment:string; outcome:string; common_cause:string; target_population:string };
type UmbrellaSimulation = {
  kind: "umbrella_scm";
  model_version: string;
  hypotheses: {hypothesis_id:string; label:string; mechanism:string; edges:SceneEdge[]}[];
  selected_hypothesis_id: string | null;
  runs: {run_id:number; hypothesis_id:string; hypothesis_label:string; prediction_id:string;
    hypothesis_edges:SceneEdge[]; hypothesis_result_records:SceneRecord[]; reference_result_records:SceneRecord[];
    hypothesis_wet_pct:number; reference_wet_pct:number}[];
  minimum_hypotheses: number;
  distinct_hypotheses_tried: number;
  ready_for_revision: boolean;
  reference_assumptions: string | null;
  reference_edges: SceneEdge[] | null;
};
type CausalScene = {
  scene_id: string;
  title: string;
  phase: "hook" | "records" | "model" | "prediction" | "comparison" | "revision";
  revision: number;
  graph_edges: SceneEdge[];
  prediction_id: string | null;
  intervention_action_id: string | null;
  reflection: string | null;
  evidence_status: "accepted" | "rejected" | null;
  next_interaction_focus_label: string | null;
  nodes: SceneNode[];
  permitted_edges: SceneEdge[];
  observed_records: SceneRecord[];
  intervention: {
    action_id: string;
    variable_id: string;
    value: "yes" | "no";
    result_records: SceneRecord[];
  };
  predictions: { prediction_id: string; label: string }[];
  resources: Record<string, string>;
  legal_action_kinds: string[];
  text_alternative: string;
  simulation?: UmbrellaSimulation | null;
};
type Message = {
  role: "learner" | "tutor";
  kind: string;
  activity_id: string;
  attempt_id: string;
  concept_id?: string;
  text: string;
  references?: TutorReference[];
  example_roles?: ExampleRoles;
};
type TutorReference = {
  claim_id: string;
  proposition: string;
  source_id: string;
  citation: string;
  locator: string;
};
type DiagnosticConceptResult = {
  concept_id: string;
  status: "correct" | "incorrect" | "current" | "later";
};
type DiagnosticResult = {
  accepted_count: number;
  total: number;
  starting_point: string;
  concept_results: { concept_id: string; accepted: boolean }[];
};
type Diagnostic = {
  status: "not_started" | "in_progress" | "completed";
  title: string;
  introduction: string;
  answered_count: number;
  total: number;
  question: string | null;
  scenario_image: ScenarioImage | null;
  workbench?: ComparisonWorkbench | null;
  choices: Choice[];
  concept_results: DiagnosticConceptResult[];
  result: DiagnosticResult | null;
};
type ModuleSummary = {
  module_id: string;
  title: string;
  optional: boolean;
  prerequisite_module_ids: string[];
  nirvana_task: string | null;
  status: "locked" | "available" | "completed";
  practical_mission?: { activity_id: string; title: string } | null;
  intent?: string;
};
type CourseIntroduction = {
  catalog_version: string;
  profile_id: string;
  title: string;
  question: string;
  example: string;
  why: string;
  actions: string[];
  comparison: {
    this_course_question: string;
    other_module_id: string;
    other_title: string;
    other_course_question: string;
    connection: string;
  };
  scenario_image: ScenarioImage;
  image_caption: string;
};
type ModuleConceptSummary = { concept_id: string; objective: string };
type LessonView = {
  profile_id: string; version: string; concept_id: string; title: string; objective: string;
  review_status: string; hook: string; example_label: string;
  worked_steps: {title:string; text:string}[];
  worked_graph: {label:string; nodes:{node_id:string; label:string}[]; edges:{from:string; to:string}[]; note:string} | null;
  definition:string; pitfall:string; takeaway:string; practice_activity_id:string;
  challenge_activity_id:string; challenge_title:string; scenario_image:ScenarioImage | null;
  sources:{source_id:string; citation:string; locator:string}[];
};
type ComparisonWorkbench = {
  title: string;
  introduction: string;
  prompt?: string | null;
  scenario_id: string;
  stage: "investigate" | "capstone";
  tables: {table_id:string; label:string; columns:string[]; rows:string[][]; note?:string|null}[];
};
type ExperimentConfig = {kind:"effect"|"shift"} & Record<string,string|number|boolean>;
type ExperimentMetric = {label:string; value:number; display_value:string};
type ExperimentResult = {
  title:string;
  summary:string;
  metrics:ExperimentMetric[];
  bars:ExperimentMetric[];
  tables:ComparisonWorkbench["tables"];
  cases:{case_id:number; source_text?:string; generated_text?:string; target:string|number|boolean;
    prediction:string|number|boolean; cue:string|number|boolean; measurement:string|number|boolean;
    emitted?:boolean; metadata_known?:boolean; source_consistent?:boolean; unsupported_addition?:boolean}[];
};
type ExperimentSnapshot = {
  experiment_id:string;
  title:string;
  instruction:string;
  revision:number;
  phase:"configure"|"predicted"|"result"|"reflected";
  config:ExperimentConfig;
  parameters:{parameter_id:string; label:string; kind:"range"|"choice"|"toggle";
    value:number|string|boolean; min?:number; max?:number; step?:number; unit?:string;
    options?:{option_id:string; label:string}[]}[];
  prediction:string|null;
  reflection:string|null;
  runs:{run_id:number; config:ExperimentConfig; prediction:string; result:ExperimentResult}[];
  result:ExperimentResult|null;
  legal_actions:string[];
  can_submit_check:boolean;
  min_distinct_runs:number;
  distinct_runs:number;
  guide?: {
    story:string; goal:string; section:"prediction"|"generation"|"intervention";
    parameter_id:string; parameter_label:string; parameter_description:string;
    prediction_prompt:string; comparison_prompt:string;
    metrics:{metric_label:string; label:string}[];
  } | null;
};
type GuidedPracticeDraft = {
  scope:string; revision:number; started:boolean; editing:boolean;
  config:ExperimentConfig; prediction:string; reflection:string;
};
function guidedPracticeDraft(snapshot:ExperimentSnapshot, scope:string, previous:GuidedPracticeDraft|null):GuidedPracticeDraft {
  if (previous?.scope === scope && previous.revision === snapshot.revision) return previous;
  return {scope,revision:snapshot.revision,started:snapshot.phase !== "configure" || snapshot.runs.length > 0,
    editing:false,config:snapshot.config,prediction:snapshot.prediction ?? "",reflection:snapshot.reflection ?? ""};
}
type FinalCheck = {
  status: "not_started" | "in_progress" | "completed";
  is_current: boolean;
  completed_count: number;
  total_count: number;
};
type DemoState = {
  status: "not_started" | "active" | "completed";
  title: string;
  phase?: string;
  attempt_id?: string | null;
  activity_id?: string | null;
  activity_concept_id?: string | null;
  question?: string | null;
  scenario_image?: ScenarioImage | null;
  choices?: Choice[];
  causal_scene?: CausalScene | null;
  conversation?: Message[];
  can_continue?: boolean;
  can_send_message?: boolean;
  completed_activity_ids?: string[];
  completed_concept_ids?: string[];
  topic_practice_completed_concept_ids?: string[];
  final_check?: FinalCheck | null;
  final_check_activity_ids?: string[];
  diagnostic: Diagnostic | null;
  learning_unlocked: boolean;
  tutor_status: "ready" | "thinking" | "unreachable";
  pending_tutor_message?: { request_id: string; text: string } | null;
  active_module_id: string;
  modules: ModuleSummary[];
  concepts: ModuleConceptSummary[];
  practical_mission?: { activity_id: string; title: string } | null;
  preview_mode?: boolean;
  review_mode?: boolean;
  review_available?: boolean;
  preview_activities?: { activity_id: string; concept_id: string; title: string }[];
  lesson_profiles?: string[];
  profile_id?: string | null;
  course_title?: string;
  lesson?: LessonView | null;
  lesson_is_sample?: boolean;
  course_profiles?: string[];
  profile_required?: boolean;
  profile_content_version?: string | null;
  learning_pack_id?: string;
  learning_pack_version?: string;
  activity_is_transfer?: boolean;
  assessment_submitted?: boolean;
  assessment_accepted?: boolean;
  answer_feedback?: AnswerFeedback | null;
  workbench?: ComparisonWorkbench | null;
  experiment?: ExperimentSnapshot | null;
  course_introduction?: CourseIntroduction | null;
};

const M0_CONCEPTS = [
  { id: "variables-and-values", label: "Variables and values" },
  { id: "observed-association", label: "Observed association" },
  { id: "association-is-not-causation", label: "Association is not causation" },
  { id: "treatment-and-outcome", label: "Treatment and outcome" },
  { id: "observation-vs-intervention", label: "Observation and intervention" },
  { id: "world-data-model", label: "World, data, and model" },
  { id: "data-vs-assumptions", label: "Data and assumptions" },
  { id: "basic-dag-language", label: "Causal graphs" },
  { id: "probabilistic-effects", label: "Probabilistic effects" },
] as const;
type ModuleConcept = { id: string; label: string };
const M0_CONCEPT_LIST: ModuleConcept[] = M0_CONCEPTS.map((concept) => ({
  id: concept.id,
  label: concept.label,
}));
function labelFromConceptId(conceptId: string): string {
  const spaced = conceptId.replace(/-/g, " ");
  return spaced.length === 0 ? spaced : spaced.charAt(0).toUpperCase() + spaced.slice(1);
}
function moduleConcepts(state: DemoState): ModuleConcept[] {
  const activeConcepts = state.concepts ?? [];
  const ids = activeConcepts.map((concept) => concept.concept_id);
  const matchesM0 =
    ids.length === M0_CONCEPTS.length && ids.every((id) => M0_CONCEPTS.some((concept) => concept.id === id));
  if (matchesM0) return M0_CONCEPT_LIST;
  return activeConcepts.map((concept) => ({
    id: concept.concept_id,
    label: labelFromConceptId(concept.concept_id),
  }));
}
const WIDE_WORKSPACE_QUERY = "(min-width: 1100px)";
const EDUCAGENT_AVATAR_SRC = "/media/educagent-mascot.png";
const ENTRY_ROUTE_PANEL_STYLE: CSSProperties = {
  background: "var(--color-background-muted)",
  padding: "var(--spacing-10) var(--spacing-9)",
};
// Astryx Table otherwise escapes the nearest Layout's inherited padding.
const CONTAINED_TABLE_STYLE = {
  "--container-padding-inline-start": "0px",
  "--container-padding-inline-end": "0px",
  "--container-padding-block-start": "0px",
  "--container-padding-block-end": "0px",
  minWidth: 0,
} as CSSProperties;
// Containers focused only by script (tabIndex -1) still guide screen readers and
// the next Tab, but must not draw a ring around the whole page on every load.
// Their buttons, options and inputs keep their own focus rings.
const SCRIPT_FOCUS_STYLE: CSSProperties = {outline:"none"};
// Keeps question and explanation copy near 70-80 characters per line.
const READING_WIDTH = "68ch";
// A picture-and-table scenario card may use more width than running text.
const SCENARIO_WIDTH = "120ch";

// The asked question is the heading; any earlier sentences are its context.
function splitQuestion(text: string): {context: string; question: string} {
  const trimmed = text.trim();
  const end = Math.max(trimmed.lastIndexOf(". "), trimmed.lastIndexOf("? "), trimmed.lastIndexOf("! "));
  if (!trimmed.endsWith("?") || end < 0) return {context: "", question: trimmed};
  return {context: trimmed.slice(0, end + 1), question: trimmed.slice(end + 2)};
}

// Content marks units such as a causal-graph chain with backticks; they render as
// highlighted inline code scaled to the surrounding text, kept tinted across a
// line break.
const INLINE_CODE_STYLE: CSSProperties = {
  fontSize:"0.9em", background:"var(--color-background-teal)", borderRadius:"var(--radius-inner)",
  padding:"0 var(--spacing-1)", boxDecorationBreak:"clone", WebkitBoxDecorationBreak:"clone",
};

function InlineMarkup({text}: {text: string}) {
  return <>{text.split("`").map((part, index) => index % 2
    ? <Code key={index} style={INLINE_CODE_STYLE}>{part}</Code> : part)}</>;
}

function questionGraphNodes(text:string): string[] | null {
  // Only draw a chain already disclosed in the question, never a lesson or answer.
  const chain = text.match(/`([^`]*→[^`]*)`/)?.[1];
  if (!chain || /[←↔]/.test(chain)) return null;
  const nodes = chain.split("→").map(label => label.trim());
  return nodes.length > 1 && nodes.every(Boolean) && new Set(nodes).size === nodes.length ? nodes : null;
}

function QuestionCausalGraph({nodes}:{nodes:string[]}) {
  const horizontal = useMediaQuery("(min-width: 48rem)") && nodes.length <= 3;
  const Flow = horizontal ? HStack : VStack;
  const edges = nodes.slice(1).map((label,index) => `Arrow from ${nodes[index]} to ${label}.`);
  return <VStack as="figure" role="img" aria-label={`Proposed causal graph. ${edges.join(" ")}`} width="100%">
    <Flow gap={2} width="100%" hAlign="center" vAlign="center">
      {nodes.flatMap((label,index) => [
        index > 0 && <svg key={`arrow-${index}`} width="2em" height="2em" viewBox="0 0 32 32"
          aria-hidden="true" focusable="false" style={{flexShrink:0}}>
          <path d={horizontal ? "M2 16H28 M21 9L28 16L21 23" : "M16 2V28 M9 21L16 28L23 21"}
            fill="none" stroke="currentColor" strokeWidth="2" />
        </svg>,
        <VStack key={`node-${index}`} padding={3} width={horizontal ? undefined : "100%"}
          style={{minWidth:0,flex:horizontal ? "1 1 0" : undefined,
            border:"var(--border-width) solid var(--color-border)",borderRadius:"var(--radius-inner)",
            background:"var(--color-background-muted)"}}>
          <Text display="block" weight="medium" style={{textAlign:"center",overflowWrap:"anywhere"}}>{label}</Text>
        </VStack>,
      ])}
    </Flow>
  </VStack>;
}

// Material first, question last: the scenario is the page title, then the picture
// and data, then the question in bold directly above the answers, so nobody has
// to read back up. A one-sentence prompt has no scenario, so it is the title.
// With recorded values too, picture and data share one card so the answers stay
// on screen; the card reflows to a stack when it is narrow.
function QuestionPrompt({text, image, workbench, headingLevel = 1}: {
  text: string; image?: ScenarioImage | null; workbench?: ComparisonWorkbench | null;
  headingLevel?:1|2;
}) {
  const {context, question} = splitQuestion(text);
  const graphNodes = questionGraphNodes(text);
  const contextTitle = graphNodes && /^A proposed causal graph contains `[^`]+`\.$/.test(context)
    ? "A proposed causal graph" : context;
  const title = contextTitle && <Heading level={headingLevel} textWrap="pretty"><InlineMarkup text={contextTitle} /></Heading>;
  const graph = graphNodes && <QuestionCausalGraph nodes={graphNodes} />;
  const ask = context
    ? <Text type="large" weight="medium"><InlineMarkup text={question} /></Text>
    : <Heading level={headingLevel} textWrap="pretty"><InlineMarkup text={question} /></Heading>;
  if (image && workbench) {
    return <VStack gap={4}>
      {title && <VStack maxWidth={READING_WIDTH}>{title}</VStack>}
      {graph}
      <VStack padding={3} style={{border:"var(--border-width) solid var(--color-border)", borderRadius:"var(--radius-container)"}}>
        <Grid columns={{minWidth:280, max:2, repeat:"fit"}} gap={5} align="start">
          <QuestionIllustration image={image} />
          <ComparisonWorkbenchCanvas workbench={workbench} />
        </Grid>
      </VStack>
      {ask}
    </VStack>;
  }
  return <VStack gap={4}>
    {title}
    {graph}
    <QuestionIllustration image={image} />
    {workbench && <ComparisonWorkbenchCanvas workbench={workbench} />}
    {ask}
  </VStack>;
}

function Eyebrow({
  children,
  color,
}: {
  children: ReactNode;
  color?: "primary" | "secondary" | "accent";
}) {
  return (
    <Text
      type="supporting"
      weight="semibold"
      color={color === "accent" ? "accent" : undefined}
      style={{
        textTransform: "uppercase",
        letterSpacing: "0.08em",
        fontSize: "var(--font-size-sm)",
      }}
    >
      {children}
    </Text>
  );
}

function requestId(kind: string): string {
  if (typeof crypto.randomUUID === "function") return `web.${kind}.${crypto.randomUUID()}`;
  // Public HTTP lacks randomUUID, but getRandomValues still supplies secure bytes.
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = Array.from(bytes, byte => byte.toString(16).padStart(2, "0")).join("");
  const uuid = [hex.slice(0, 8), hex.slice(8, 12), hex.slice(12, 16), hex.slice(16, 20), hex.slice(20)].join("-");
  return `web.${kind}.${uuid}`;
}
class ApiFailure extends Error {
  constructor(message: string, readonly code: string, readonly retryable: boolean) {
    super(message);
  }
}
async function api(
  path: string,
  body: Record<string, unknown> = {},
): Promise<DemoState> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 20_000);
  try {
    const response = await fetch(path, {
      method: path === "/api/state" ? "GET" : "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: path === "/api/state" ? undefined : JSON.stringify({ request_id: requestId("command"), ...body }),
      signal: controller.signal,
    });
    const value: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      const failure =
        value !== null && typeof value === "object"
          ? (value as Record<string, unknown>)
          : {};
      const label =
        typeof failure.error === "string" ? failure.error : `HTTP ${response.status}`;
      const diagnostic =
        typeof failure.diagnostic === "string" ? ` (${failure.diagnostic})` : "";
      const upstream = typeof failure.upstream_status === "number" && Number.isInteger(failure.upstream_status)
        && failure.upstream_status >= 100 && failure.upstream_status <= 599
        ? ` Upstream HTTP ${failure.upstream_status}.` : "";
      const request =
        typeof failure.request_id === "string" ? ` Request: ${failure.request_id}.` : "";
      const detail = typeof failure.detail === "string" ? ` ${failure.detail}` : "";
      const recovery = typeof failure.recovery === "string" ? ` ${failure.recovery}` : "";
      throw new ApiFailure(`${label}${diagnostic}.${upstream}${detail}${recovery}${request}`,
        typeof failure.code === "string" ? failure.code : "request_failed",
        failure.retryable === true);
    }
    return value as DemoState;
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError")
      throw new ApiFailure("The request timed out after 20 seconds. Reconnect to check your saved progress.", "network_timeout", true);
    if (error instanceof TypeError)
      throw new ApiFailure("The learning service could not be reached. Reconnect to check your saved progress.", "network_unavailable", true);
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
}

export function App() {
  const [state, setState] = useState<DemoState | null>(null);
  const [messageDrafts, setMessageDrafts] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [isWorking, setIsWorking] = useState(false);
  const [isProfileDialogOpen, setIsProfileDialogOpen] = useState(false);
  const [pendingMessage, setPendingMessage] = useState<{
    request_id: string;
    text: string;
  } | null>(null);
  // PageFrame reparents the whole LearningScreen at a breakpoint; drafts must live above it.
  const [guidedDraft,setGuidedDraft] = useState<GuidedPracticeDraft|null>(null);
  const [isIntroductionOpen,setIsIntroductionOpen] = useState(false);
  useEffect(() => setIsIntroductionOpen(false), [state?.profile_id,state?.active_module_id]);
  useEffect(() => {
    if (state) document.title = `EducAgent · ${state.course_title ?? state.title}`;
  }, [state?.course_title, state?.title]);
  const refresh = useCallback(async () => {
    try {
      const next = await api("/api/state");
      setState(next);
      setError(null);
      return next;
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The learning service could not be reached.");
      return null;
    }
  }, []);
  const run = useCallback(
    async (path: string, body: Record<string, unknown> = {}) => {
      setIsWorking(true);
      try {
        const resetBody = path === "/api/reset" && !state?.preview_mode && (state?.course_profiles?.length ?? 0) > 0
          ? {profile_id:state?.profile_id, pack_id:state?.learning_pack_id, version:state?.learning_pack_version, ...body}
          : body;
        const next = await api(path, resetBody);
        if (path === "/api/select-module" || path === "/api/preview") {
          const href = path === "/api/preview"
            ? previewLocation(window.location.href, !!next.preview_mode)
            : window.location.href;
          window.history.replaceState(window.history.state, "", moduleLocation(href, next.active_module_id));
        }
        setState(next);
        if (path === "/api/reset" || path === "/api/start") setIsIntroductionOpen(false);
        setPendingMessage(next.pending_tutor_message ?? null);
        setError(null);
      } catch (reason) {
        setError(reason instanceof Error ? reason.message : "Tutor request failed.");
      } finally {
        setIsWorking(false);
      }
    },
    [state?.profile_id, state?.learning_pack_id, state?.learning_pack_version, state?.preview_mode, state?.course_profiles],
  );
  useEffect(() => {
    const parameters = new URLSearchParams(window.location.search);
    const requestedModuleId = parameters.get("module");
    void (async () => {
      try {
        let current = await refresh();
        if (parameters.get("preview") === "1" && !current?.preview_mode)
          current = await api("/api/preview", { enabled: true });
        const target = current?.modules.find((module) => module.module_id === requestedModuleId);
        if (target && target.status !== "locked" && target.module_id !== current?.active_module_id)
          current = await api("/api/select-module", { module_id: target.module_id });
        const profileId = parameters.get("lesson");
        if (profileId && current?.lesson_profiles?.includes(profileId))
          current = await api("/api/start-lesson", { profile_id: profileId });
        const activityId = parameters.get("activity");
        if (activityId && current?.preview_mode)
          current = await api("/api/preview/navigate", { activity_id: activityId });
        if (current) setState(current);
      } catch (reason) { setError(reason instanceof Error ? reason.message : "The learning request failed."); }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const deliverMessage = useCallback(async (
    request_id: string,
    text: string,
    retrying = false,
  ) => {
    setIsWorking(true);
    setPendingMessage({ request_id, text });
    if (!retrying) setState((current) => {
      if (
        current === null ||
        current.status !== "active" ||
        current.activity_id === undefined ||
        current.activity_id === null ||
        current.attempt_id === undefined ||
        current.attempt_id === null
      )
        return current;
      const optimisticMessage: Message = {
        role: "learner",
        kind: "message",
        activity_id: current.activity_id,
        attempt_id: current.attempt_id,
        text,
      };
      const conceptId = current.activity_concept_id ?? conceptForActivity(
        current.activity_id,
        moduleConcepts(current),
      );
      if (conceptId !== null) optimisticMessage.concept_id = conceptId;
      return {
        ...current,
        tutor_status: "thinking",
        conversation: [
          ...(current.conversation ?? []),
          optimisticMessage,
        ],
      };
    });
    try {
      setState(await api("/api/message", { request_id, text }));
      setError(null);
      setPendingMessage(null);
      return true;
    } catch (reason) {
      const retainedForRetry = !(reason instanceof ApiFailure && !reason.retryable && reason.code !== "tutor_configuration");
      if (!retainedForRetry) {
        setPendingMessage(null);
        try { setState(await api("/api/state")); } catch { /* Keep the diagnostic below if refresh also fails. */ }
      } else {
        setState((current) => current === null ? null : { ...current,
          tutor_status: reason instanceof ApiFailure && reason.code === "tutor_configuration" ? "ready" : "unreachable" });
      }
      setError(
        reason instanceof Error ? reason.message : "Tutor request failed.",
      );
      return retainedForRetry;
    } finally {
      setIsWorking(false);
    }
  }, []);
  const sendMessage = useCallback(
    (text: string) => deliverMessage(requestId("message"), text),
    [deliverMessage],
  );
  const reconnect = useCallback(async () => {
    const next = await refresh();
    const pending = next?.pending_tutor_message ?? pendingMessage;
    if (next !== null && pending !== null)
      await deliverMessage(pending.request_id, pending.text, true);
  }, [deliverMessage, pendingMessage, refresh]);
  const onSelectModule = useCallback(
    (moduleId: string, testOnlyForceUnlock = false) => {
      return run("/api/select-module", {
        module_id: moduleId,
        // TEST ONLY: bypasses the prerequisite check server-side. Never set
        // this from a normal, non-test UI action.
        ...(testOnlyForceUnlock ? { test_only_force_unlock: true } : {}),
      });
    },
    [run],
  );
  const selectProfile = async (profileId: string) => {
    setIsWorking(true);
    try {
      const next = await api("/api/select-profile", {profile_id:profileId});
      setState(next);
      setPendingMessage(next.pending_tutor_message ?? null);
      setError(null);
      setIsProfileDialogOpen(false);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "The profile could not be selected."); }
    finally { setIsWorking(false); }
  };
  if (state === null)
    return (
      <PageFrame>
        <LoadingScreen error={error} onRetry={() => void refresh()} />
      </PageFrame>
    );
  const messageDraftKey = [state.active_module_id, state.profile_id, state.learning_pack_id,
    state.learning_pack_version, state.attempt_id].join("|");
  if (state.diagnostic !== null && state.status === "not_started")
    return (
      <PageFrame>
        <DiagnosticScreen
          state={state}
          diagnostic={state.diagnostic}
          error={error}
          isWorking={isWorking}
          onRun={run}
          onSelectModule={(moduleId, force) => void onSelectModule(moduleId, force)}
          onChangeProfile={() => setIsProfileDialogOpen(true)}
        />
        <ProfileDialog state={state} isOpen={isProfileDialogOpen || !!state.profile_required && !state.preview_mode}
          isWorking={isWorking} error={error} onOpenChange={setIsProfileDialogOpen} onSelect={selectProfile} />
      </PageFrame>
    );
  return (
    <PageFrame>
      <LearningScreen
        state={state}
        guidedDraft={guidedDraft}
        onGuidedDraftChange={setGuidedDraft}
        isIntroductionOpen={isIntroductionOpen}
        onIntroductionOpenChange={setIsIntroductionOpen}
        messageDraft={messageDrafts[messageDraftKey] ?? ""}
        onMessageDraftChange={(value) => setMessageDrafts((drafts) => ({...drafts, [messageDraftKey]:value}))}
        error={error}
        isWorking={isWorking}
        onRun={run}
        onSendMessage={sendMessage}
        onReconnect={() => void reconnect()}
        onSelectModule={(moduleId, force) => void onSelectModule(moduleId, force)}
        onChangeProfile={() => setIsProfileDialogOpen(true)}
      />
      <ProfileDialog state={state} isOpen={isProfileDialogOpen || !!state.profile_required && !state.preview_mode}
        isWorking={isWorking} error={error} onOpenChange={setIsProfileDialogOpen} onSelect={selectProfile} />
    </PageFrame>
  );
}

function ProfileDialog({state, isOpen, isWorking, error, onOpenChange, onSelect}: {
  state:DemoState; isOpen:boolean; isWorking:boolean; error:string|null;
  onOpenChange:(open:boolean)=>void; onSelect:(profileId:string)=>Promise<void>;
}) {
  const [profileId,setProfileId] = useState(state.profile_id ?? "general");
  useEffect(() => { if (isOpen) setProfileId(state.profile_id ?? "general"); }, [isOpen, state.profile_id]);
  const required = !!state.profile_required;
  return <Dialog isOpen={isOpen} onOpenChange={onOpenChange} purpose={required ? "required" : "form"} width={520}>
    <Layout padding={5} defaultHasDividers
      header={<DialogHeader title={required ? "Choose your learning profile" : "Change your learning profile"}
        subtitle="Choose the examples you prefer. Change this at any time."
        onOpenChange={required ? undefined : onOpenChange} />}
      content={<LayoutContent><VStack gap={4}>
        <HStack gap={4} width="100%" role="group" aria-label="Example context">
          {[
            {id:"general", label:"General", emoji:"🧑"},
            {id:"medical", label:"Medical", emoji:"👩‍⚕️"},
          ].map(profile => <Button key={profile.id} label={profile.label} variant="secondary"
            aria-pressed={profileId === profile.id} isDisabled={isWorking}
            onClick={() => setProfileId(profile.id)}
            style={{
              flex:"1 1 0", minWidth:0, height:"auto", aspectRatio:"1 / 1",
              padding:"var(--spacing-4)", borderRadius:"var(--radius-container)",
              border:"var(--border-width) solid var(--color-border)",
              backgroundColor:profileId === profile.id ? "var(--color-accent-muted)" : "var(--color-background-surface)",
              boxShadow:profileId === profile.id ? "inset 0 0 0 var(--border-width) var(--color-accent)" : "none",
            }}>
            <VStack as="span" gap={2} hAlign="center" vAlign="center">
              <Text as="span" aria-hidden="true" style={{fontSize:"calc(var(--font-size-5xl) * 1.5)", lineHeight:1}}>{profile.emoji}</Text>
              <Text as="span" weight={profileId === profile.id ? "semibold" : "medium"}>{profile.label}</Text>
            </VStack>
          </Button>)}
        </HStack>
        <Text type="supporting">Both profiles cover the same topics. Each keeps its own progress.</Text>
        {error && <Text>{error}</Text>}
        <Button label={required ? "Continue with this profile" : "Use this profile"} variant="primary"
          isDisabled={isWorking} onClick={() => void onSelect(profileId)} />
      </VStack></LayoutContent>} />
  </Dialog>;
}

function ProfileButton({state,isWorking,onChange}: {state:DemoState; isWorking:boolean; onChange:()=>void}) {
  if ((state.course_profiles?.length ?? 0) === 0 || state.lesson_is_sample) return null;
  return <Button label={`${state.profile_id === "medical" ? "👩‍⚕️ Medical" : "🧑 General"} · Change profile`}
    variant="ghost" size="sm" isDisabled={isWorking} onClick={onChange} />;
}

function PageFrame({ children }: { children: ReactNode }) {
  const isWide = useMediaQuery(WIDE_WORKSPACE_QUERY);
  if (!isWide) return <>{children}</>;
  return (
    <VStack
      padding={4}
      width="100%"
      height="100dvh"
      style={{
        background: "var(--color-background-muted)",
        alignItems: "center",
        boxSizing: "border-box",
        overflow: "hidden",
      }}
    >
      <VStack
        width="100%"
        maxWidth={1600}
        height="100%"
        style={{
          background: "var(--color-background-surface)",
          border: "var(--border-width) solid var(--color-border)",
          borderRadius: "var(--radius-page)",
          overflow: "hidden",
        }}
      >
        {children}
      </VStack>
    </VStack>
  );
}

function LoadingScreen({
  error,
  onRetry,
}: {
  error: string | null;
  onRetry: () => void;
}) {
  const isWide = useMediaQuery(WIDE_WORKSPACE_QUERY);
  return (
    <AppShell
      contentPadding={0}
      height="fill"
      variant="section"
      style={isWide ? { height: "100%" } : undefined}
    >
      <Layout
        contentWidth="60ch"
        padding={5}
        content={
          <LayoutContent role="main" label="Connecting to EducAgent">
            <VStack gap={4}>
              <WorkspaceHeader label="EducAgent workspace" tutorStatus="thinking" />
              <Section variant="muted" padding={4}>
                <VStack gap={2}>
                  <Heading level={1}>Connecting to EducAgent</Heading>
            <Text>{error ?? "Loading your course and saved progress."}</Text>
                  {error !== null && (
                    <Button
                      label="Reconnect"
                      variant="primary"
                      onClick={onRetry}
                    />
                  )}
                </VStack>
              </Section>
            </VStack>
          </LayoutContent>
        }
      />
    </AppShell>
  );
}

function DiagnosticScreen({
  state,
  diagnostic,
  error,
  isWorking,
  onRun,
  onSelectModule,
  onChangeProfile,
}: {
  state: DemoState;
  diagnostic: Diagnostic;
  error: string | null;
  isWorking: boolean;
  onRun: (path: string, body?: Record<string, unknown>) => Promise<void>;
  onSelectModule: (moduleId: string, testOnlyForceUnlock?: boolean) => void;
  onChangeProfile: () => void;
}) {
  const isWide = useMediaQuery(WIDE_WORKSPACE_QUERY);
  const questionNumber = diagnostic.answered_count + 1;
  const body = (
    <VStack
      gap={5}
      width="100%"
      maxWidth={isWide ? "120ch" : "72ch"}
    >
      {error !== null && (
        <ConnectionNotice title="Learning request failed" description={error} onReconnect={() => void onRun("/api/state")} />
      )}
      {state.preview_mode && (state.lesson_profiles?.length ?? 0) > 0 && <LessonEntry state={state} isWorking={isWorking} onRun={onRun} />}
      {diagnostic.status === "not_started" && (
        <QuizIntro
          isWorking={isWorking}
          onStart={() => void onRun("/api/diagnostic/start")}
          onSkip={() => void onRun("/api/diagnostic/skip")}
          onStartScene={state.practical_mission ? () => void onRun("/api/start-scene") : undefined}
        />
      )}
      {diagnostic.status === "in_progress" && diagnostic.question !== null && (
        <VStack gap={4} width="100%"
          maxWidth={diagnostic.scenario_image && diagnostic.workbench ? SCENARIO_WIDTH : READING_WIDTH}>
          <VStack gap={1}>
            <HStack gap={2} vAlign="center" wrap="wrap">
              <Eyebrow color="accent">
                {M0_CONCEPTS[Math.min(diagnostic.answered_count, M0_CONCEPTS.length - 1)]?.label}
              </Eyebrow>
              <Text type="supporting">
                Question {questionNumber} of {diagnostic.total}
              </Text>
            </HStack>
            <QuestionPrompt text={diagnostic.workbench?.prompt ?? diagnostic.question}
              image={diagnostic.scenario_image} workbench={diagnostic.workbench} />
          </VStack>
          <VStack gap={5} width="100%" maxWidth={READING_WIDTH}>
            <AnswerCommitment
              activityKey={`diagnostic.${state.profile_id}.${state.learning_pack_id}.${state.learning_pack_version}.${diagnostic.answered_count}`}
              choices={diagnostic.choices}
              isWorking={isWorking}
              onCommit={(optionId) =>
                void onRun("/api/diagnostic/respond", {
                  request_id: requestId("diagnostic"),
                  option_id: optionId,
                })
              }
            />
            <Button
              label="Leave the quiz and start from the basics"
              variant="ghost"
              isDisabled={isWorking}
              onClick={() => void onRun("/api/diagnostic/skip")}
            />
          </VStack>
        </VStack>
      )}
      {diagnostic.status === "completed" && (
        <Section variant="muted" padding={4}>
          <VStack gap={3}>
            <Eyebrow>Entry quiz complete</Eyebrow>
            <Heading level={1} type="display-1">
              Choose where to begin
            </Heading>
            <Text>
              {diagnostic.result?.accepted_count === diagnostic.total
                ? "You answered all the starting questions correctly. You can still explore the full course and try its practical activities."
                : "Review selected topics to focus on the ideas you found less familiar, or take the full course for explanations and practice across all nine topics."}
            </Text>
            {diagnostic.result?.accepted_count !== diagnostic.total && <Button
              label="Review selected topics"
              variant="primary"
              isDisabled={isWorking}
              onClick={() => void onRun("/api/start")}
            />}
            <Button
              label="Start the full course"
              variant="secondary"
              isDisabled={isWorking}
              onClick={() => void onRun("/api/diagnostic/skip")}
            />
          </VStack>
        </Section>
      )}
    </VStack>
  );
  return (
    <AppShell
      contentPadding={0}
      height="fill"
      variant="wash"
      style={isWide ? { height: "100%" } : undefined}
    >
      <Layout
        height="fill"
        contentWidth={isWide ? "100%" : "72ch"}
        padding={isWide ? 5 : 4}
        defaultHasDividers
        header={
          <LayoutHeader
            hasDivider
            label="EducAgent entry diagnostic"
            style={{ padding: isWide ? "18px 40px" : undefined }}
          >
            <HStack gap={2} hAlign="between" vAlign="center" wrap="wrap" width="100%" style={{minWidth:0}}>
          <HStack gap={2} vAlign="center" wrap="wrap" style={{minWidth:0,maxWidth:"100%"}}>
            <Text weight="semibold" style={{ fontSize: "17px", letterSpacing: "-0.01em" }}>
              EducAgent
            </Text>
            <Text type="supporting">
              {diagnostic.status === "not_started"
                ? state.course_title ?? "Causality foundations"
                : "Entry quiz"}
            </Text>
          </HStack>
          <HStack gap={3} vAlign="center" wrap="wrap" style={{minWidth:0,maxWidth:"100%",flex:"0 1 auto"}}>
            <ProfileButton state={state} isWorking={isWorking} onChange={onChangeProfile} />
            {state.modules.length > 1 && <ModuleSwitcher modules={state.modules}
              activeModuleId={state.active_module_id} isWorking={isWorking} onSelectModule={onSelectModule} />}
            {diagnostic.status === "in_progress" && (
              <Text type="supporting">
                Question {questionNumber} of {diagnostic.total}
              </Text>
            )}
            <HStack gap={1} vAlign="center">
              <StatusDot variant="success" label="Tutor ready" />
              <Text type="supporting">Tutor ready</Text>
            </HStack>
            <Button
              label="Reset progress"
              variant="ghost"
              size="sm"
              isDisabled={isWorking}
              onClick={() => void onRun("/api/reset")}
            />
          </HStack>
            </HStack>
          </LayoutHeader>
        }
        content={
          <LayoutContent
            padding={isWide ? 6 : 5}
            label="Entry diagnostic"
            style={isWide ? { padding: "var(--spacing-8) var(--spacing-12) var(--spacing-10)" } : undefined}
          >
            {body}
            {!isWide && (
              <Collapsible trigger={<Text weight="semibold">View course topics</Text>}>
                <RouteList showStatus={false} started={conceptsWithPractice(state)} />
              </Collapsible>
            )}
          </LayoutContent>
        }
        end={
          isWide ? (
            <LayoutPanel
              hasDivider
              padding={4}
              width={400}
              label="Course topics"
              style={ENTRY_ROUTE_PANEL_STYLE}
            >
              <EntryRouteRail state={state} isWorking={isWorking} onSelectModule={onSelectModule} />
            </LayoutPanel>
          ) : undefined
        }
      />
    </AppShell>
  );
}

function QuizIntro({
  isWorking,
  onStart,
  onSkip,
  onStartScene,
  diagnostic = true,
  title = "Causality foundations",
}: {
  isWorking: boolean;
  onStart: () => void;
  onSkip?: () => void;
  onStartScene?: () => void;
  diagnostic?: boolean;
  title?: string;
}) {
  return (
    <VStack gap={4}>
      <VStack gap={2}>
        <Eyebrow>{title}</Eyebrow>
        <Heading level={1} type="display-1">
          {diagnostic ? "Start learning causality." : title}
        </Heading>
        <Text>
          {diagnostic
            ? "Learn the basics of causality through examples and exercises. You can start the course or take a nine-question quiz to find topics to review."
            : "Start the first activity. Ask EducAgent for help as you work through it."}
        </Text>
      </VStack>
      <HStack gap={2} wrap="wrap" role="group" aria-label="Learning entry options">
        {onSkip !== undefined && (
          <Button
            label="Start from the basics"
            variant="secondary"
            size="lg"
            isDisabled={isWorking}
            onClick={onSkip}
          />
        )}
        <Button
          label={diagnostic ? "Take the optional quiz" : "Start learning"}
          variant={onSkip === undefined ? "primary" : "secondary"}
          size="lg"
          isDisabled={isWorking}
          onClick={onStart}
        />
        {onStartScene !== undefined && (
          <Button
            label="Try an exercise"
            variant="secondary"
            size="lg"
            isDisabled={isWorking}
            onClick={onStartScene}
          />
        )}
      </HStack>
      <Text type="supporting">
        <a href="/sources.html">Sources &amp; rights</a>
      </Text>
    </VStack>
  );
}

function FinalCheckIntroduction({courseTitle, topicCount, questionCount, topicsComplete, isWorking, onStart, onReview, titleRef}: {
  courseTitle:string;
  topicCount:number;
  questionCount:number;
  topicsComplete:boolean;
  isWorking:boolean;
  onStart:()=>void;
  onReview:()=>void;
  titleRef:RefObject<HTMLHeadingElement|null>;
}) {
  return <VStack gap={5} maxWidth={READING_WIDTH} paddingBlock={6} aria-label="Final check introduction">
    <Eyebrow>{courseTitle} · Final check</Eyebrow>
    <Heading ref={titleRef} tabIndex={-1} level={1} type="display-3" style={SCRIPT_FOCUS_STYLE}>
      {topicsComplete ? "Congratulations!" : "Ready for the final check?"}
    </Heading>
    {topicsComplete && <Text type="large">You’ve completed all {topicCount} topics in {courseTitle}.</Text>}
    <Text>The final check has {questionCount} questions that bring these ideas together. You can start now, or revisit the course topics first.</Text>
    <HStack gap={3} wrap="wrap">
      <Button label="Start the final check" variant="primary" size="lg" isDisabled={isWorking} onClick={onStart} />
      <Button label="Review course topics" variant="secondary" size="lg" isDisabled={isWorking} onClick={onReview} />
    </HStack>
    <Text type="supporting">Your course progress is saved.</Text>
  </VStack>;
}

function CourseIntroductionCanvas({introduction, isWorking, hasStarted, onContinue, titleRef, hideCaption = false}: {
  introduction:CourseIntroduction;
  isWorking:boolean;
  hasStarted:boolean;
  onContinue:()=>void;
  titleRef:RefObject<HTMLHeadingElement|null>;
  hideCaption?:boolean;
}) {
  const comparison = introduction.comparison;
  return <VStack gap={6} width="100%" maxWidth="100%" aria-label="Course introduction">
    <VStack gap={3}>
      <Eyebrow>{introduction.profile_id === "medical" ? "Medical" : "General"} · Course introduction</Eyebrow>
      <Heading ref={titleRef} tabIndex={-1} level={1} type="display-3" textWrap="pretty" style={SCRIPT_FOCUS_STYLE}>{introduction.title}</Heading>
      <Text type="large" weight="semibold">{introduction.question}</Text>
      <HStack gap={3} vAlign="center" wrap="wrap">
        <Button label={hasStarted ? "Back to learning" : "Start this course"} variant="primary"
          isDisabled={isWorking} onClick={onContinue} />
        {hasStarted && <Text type="supporting">Your current activity and progress stay in place.</Text>}
      </HStack>
    </VStack>
    <Grid columns={{minWidth:280,max:2,repeat:"fit"}} gap={5} align="start">
      <VStack gap={2} width="100%">
        <AspectRatio ratio={3/2} fit="contain">
          <img src={`/${introduction.scenario_image.path}`} alt={introduction.scenario_image.alt_text} />
        </AspectRatio>
        {!hideCaption && introduction.image_caption && <Text type="supporting">{introduction.image_caption}</Text>}
      </VStack>
      <VStack gap={5}>
        <VStack gap={2}>
          <Heading level={2}>Start with a situation</Heading>
          <Text>{introduction.example}</Text>
        </VStack>
        <VStack gap={2}>
          <Heading level={2}>Why learn this?</Heading>
          <Text>{introduction.why}</Text>
        </VStack>
      </VStack>
    </Grid>
    <Divider />
    <Grid columns={{minWidth:280,max:2,repeat:"fit"}} gap={6} align="start">
      <VStack gap={3}>
        <Heading level={2}>What you will do</Heading>
        <VStack gap={3} as="ol" style={{margin:0,paddingInlineStart:"var(--spacing-5)"}}>
          {introduction.actions.map((action) => <VStack key={action} as="li" style={{display:"list-item",listStyle:"decimal"}}><Text>{action}</Text></VStack>)}
        </VStack>
      </VStack>
      <VStack gap={3}>
        <Heading level={2}>How the courses fit together</Heading>
        <Text><Text as="span" weight="semibold">{introduction.title}: </Text>{comparison.this_course_question}</Text>
        <Text><Text as="span" weight="semibold">{comparison.other_title}: </Text>{comparison.other_course_question}</Text>
        <Text>{comparison.connection}</Text>
      </VStack>
    </Grid>
    <Text type="supporting"><a href="/sources.html">Sources &amp; rights</a></Text>
  </VStack>;
}

function PreviewControls({state, isWorking, onRun}: {
  state: DemoState;
  isWorking: boolean;
  onRun: (path: string, body?: Record<string, unknown>) => Promise<void>;
}) {
  return <VStack gap={3}>
    <Banner status="info" title="Testing preview"
      description="Browse any activity, including completed topics. Preview attempts do not change your learning progress." />
    <Collapsible defaultIsOpen={false} trigger={<Text weight="semibold">Browse all activities</Text>}>
      <List density="compact" hasDividers>
        {(state.preview_activities ?? []).map((activity) => <ListItem key={activity.activity_id}
          label={activity.title} description={activity.activity_id}
          isSelected={state.activity_id === activity.activity_id} isDisabled={isWorking}
          onClick={() => void onRun("/api/preview/navigate", {activity_id: activity.activity_id})} />)}
      </List>
    </Collapsible>
  </VStack>;
}

function LessonEntry({state, isWorking, onRun}: {
  state:DemoState; isWorking:boolean; onRun:(path:string, body?:Record<string,unknown>)=>Promise<void>;
}) {
  const [profile, setProfile] = useState("general");
  return <Collapsible defaultIsOpen={state.status === "not_started"} trigger={<Text weight="semibold">Try a worked lesson: association is not causation</Text>}>
    <VStack gap={3}>
      <Text>Choose the context for this lesson sample. Both versions teach the same causal distinction.</Text>
      <RadioList label="Example profile" value={profile} onChange={setProfile} isDisabled={isWorking} htmlName="lesson-profile">
        <RadioListItem value="general" label="General" />
        <RadioListItem value="medical" label="Medical" />
      </RadioList>
      <Button label="Explore this worked lesson" variant="primary" isDisabled={isWorking}
        onClick={() => void onRun("/api/start-lesson", {profile_id:profile})} />
    </VStack>
  </Collapsible>;
}

function AnswerFeedbackNotice({feedback, choices}: {
  feedback:AnswerFeedback | null | undefined; choices:Choice[];
}) {
  const feedbackRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (feedback) feedbackRef.current?.scrollIntoView({block:"nearest"});
  }, [feedback?.accepted, feedback?.option_id, feedback?.text]);
  if (!feedback) return null;
  const chosen = choices.find((choice) => choice.option_id === feedback.option_id)?.text;
  return <VStack ref={feedbackRef}><Banner status={feedback.accepted ? "success" : "error"}
    title={feedback.accepted ? "Correct" : "Incorrect. Try again."}
    description={<VStack gap={2}>
      {!feedback.accepted && chosen && <Text>You chose: {chosen}</Text>}
      <Text>{feedback.text}</Text>
    </VStack>} /></VStack>;
}

function LessonCanvas({lesson, state, isWorking, onRun}: {
  lesson:LessonView; state:DemoState; isWorking:boolean;
  onRun:(path:string, body?:Record<string,unknown>)=>Promise<void>;
}) {
  const isChallenge = state.activity_is_transfer ?? state.activity_id === lesson.challenge_activity_id;
  const [reading, setReading] = useState(false);
  const submitted = state.assessment_submitted ?? !!state.can_continue;
  const accepted = state.assessment_accepted ?? !!state.can_continue;
  // A rejected quiz stays on its answers; the explanation is opened on request,
  // so it cannot silently supply the answer for the retry.
  useEffect(() => {
    setReading(!isChallenge && accepted);
  }, [isChallenge, submitted, accepted]);
  const graph = lesson.worked_graph;
  const labelForNode = (id:string) => graph?.nodes.find((node) => node.node_id === id)?.label ?? id;
  const conceptLabel = moduleConcepts(state).find((concept) => concept.id === lesson.concept_id)?.label ?? labelFromConceptId(lesson.concept_id);
  const graphPanel = graph && <VStack padding={4} style={{background:"var(--color-background-muted)", borderRadius:"var(--radius-container)"}}>
    <VStack gap={2}>
      <Text weight="semibold">{graph.label}</Text>
      <svg style={{width:"100%", maxWidth:420}} viewBox="0 0 420 150" role="img" aria-label={graph.edges.map((edge) => `${labelForNode(edge.from)} may influence ${labelForNode(edge.to)}`).join("; ")}>
        <defs><marker id={`lesson-arrow-${lesson.profile_id}`} markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">
          <path d="M0,0 L7,3.5 L0,7 Z" fill="currentColor" />
        </marker></defs>
        <rect x="55" y="5" width="310" height="36" rx="6" fill="none" stroke="currentColor" />
        <text x="210" y="28" textAnchor="middle" fontSize="14" fill="currentColor">{labelForNode(graph.edges[0].from)}</text>
        {graph.edges.map((edge,index) => {
          const x = index === 0 ? 105 : 315;
          return <g key={`${edge.from}.${edge.to}`}>
            <line x1="210" y1="42" x2={x} y2="92" stroke="currentColor" markerEnd={`url(#lesson-arrow-${lesson.profile_id})`} />
            <rect x={x-96} y="100" width="192" height="36" rx="6" fill="none" stroke="currentColor" />
            <text x={x} y="123" textAnchor="middle" fontSize="14" fill="currentColor">{labelForNode(edge.to)}</text>
          </g>;
        })}
      </svg>
      <Text type="supporting">{graph.note}</Text>
    </VStack>
  </VStack>;
  const scenarioCard = !reading && !!state.scenario_image && !!state.workbench;
  return <VStack gap={4} width="100%" maxWidth={reading || scenarioCard ? SCENARIO_WIDTH : READING_WIDTH}>
    <HStack gap={2} hAlign="between" vAlign="center" wrap="wrap">
      <VStack gap={2}>
        <Heading level={2} textWrap="pretty">{conceptLabel}</Heading>
        <Text type="supporting" aria-label="Topic sequence">
          <Text as="span" type="inherit" weight={!reading && !isChallenge ? "semibold" : undefined}>Quiz</Text>
          {" → "}<Text as="span" type="inherit" weight={reading ? "semibold" : undefined}>Explanation</Text>
          {" → "}<Text as="span" type="inherit" weight={isChallenge && !reading ? "semibold" : undefined}>Challenge</Text>
        </Text>
      </VStack>
      {!reading && (submitted || isChallenge) && <Button label={isChallenge || accepted ? "Review the explanation" : "Show the explanation"} variant="ghost" size="sm" onClick={() => setReading(true)} />}
    </HStack>
    {reading ? <Grid columns={{minWidth:400, max:2, repeat:"fit"}} gap={6} align="start" width="100%">
      <VStack as="article" aria-label="Lesson explanation" gap={4} width="100%" maxWidth={READING_WIDTH} style={{minWidth:0}}>
        <Heading level={1} textWrap="pretty">{lesson.title}</Heading>
        {!graph && <QuestionIllustration image={lesson.scenario_image} />}
        <AnswerFeedbackNotice feedback={state.answer_feedback} choices={state.choices ?? []} />
        <VStack as="blockquote" gap={2} padding={4} aria-label="Course definition" style={{margin:0, borderInlineStart:"var(--spacing-1) solid var(--color-border)", background:"var(--color-background-muted)"}}>
          <Text weight="semibold"><InlineMarkup text={lesson.definition} /></Text>
          <Text type="supporting">Course definition, adapted from {lesson.sources.map((source) => `${source.citation} (${source.locator})`).join("; ")}. <a href="/sources.html">Sources &amp; rights</a></Text>
        </VStack>
        <Text><InlineMarkup text={lesson.hook} /></Text>
        {graphPanel}
        <HStack gap={2} wrap="wrap">
          {accepted && !isChallenge ? <Button label="Go to the challenge" variant="primary" isDisabled={isWorking}
            onClick={() => void onRun("/api/continue", {request_id:requestId("continue")})} />
            : <Button label={isChallenge ? "Go to the challenge" : "Try the quiz again"} variant="primary" isDisabled={isWorking} onClick={() => setReading(false)} />}
        </HStack>
      </VStack>
      <VStack as="aside" aria-label="More explanation and sources" width="100%" style={{minWidth:0}}>
        <Collapsible defaultIsOpen={false} trigger={<Text weight="medium">More explanation and sources</Text>}>
          <VStack gap={4}>
            {lesson.worked_steps.map((step,index) => <VStack gap={1} key={step.title}>
              <Heading level={2}>{state.active_module_id === "m1_shift" || state.active_module_id === "m1_effect" ? step.title : `${index+1}. ${step.title}`}</Heading><Text><InlineMarkup text={step.text} /></Text>
            </VStack>)}
            {lesson.pitfall && <VStack gap={1}><Text weight="semibold">A useful distinction</Text><Text><InlineMarkup text={lesson.pitfall} /></Text></VStack>}
            <Text><InlineMarkup text={lesson.takeaway} /></Text>
            <Text type="supporting">Source: <a href="https://web.math.ku.dk/~peters/jonas_files/ElementsOfCausalInference.pdf">Elements of Causal Inference</a>. {lesson.sources.map((source) => source.locator).join("; ")}.</Text>
          </VStack>
        </Collapsible>
      </VStack>
    </Grid> : <>
      <QuestionPrompt text={state.workbench?.prompt ?? state.question ?? ""} image={state.scenario_image} workbench={state.workbench} />
      <VStack gap={4} width="100%" maxWidth={READING_WIDTH}>
        {!state.can_continue && <AnswerFeedbackNotice feedback={state.answer_feedback} choices={state.choices ?? []} />}
        {state.can_continue ? <CommitBar isWorking={isWorking} onContinue={() => void onRun("/api/continue", {request_id:requestId("continue")})} />
          : <AnswerCommitment activityKey={`${state.attempt_id}.${state.activity_id}`} choices={state.choices ?? []} isWorking={isWorking}
            onCommit={(optionId) => void onRun("/api/respond", {request_id:requestId("answer"), option_id:optionId})} />}
      </VStack>
    </>}
  </VStack>;
}

function ComparisonWorkbenchCanvas({workbench, padding = 4}: {workbench:ComparisonWorkbench; padding?:0|4}) {
  const [tableId, setTableId] = useState(workbench.tables[0]?.table_id ?? "");
  useEffect(() => setTableId(workbench.tables[0]?.table_id ?? ""), [workbench.scenario_id, workbench.stage]);
  const table = workbench.tables.find((item) => item.table_id === tableId) ?? workbench.tables[0];
  return <VStack gap={3} width="100%" padding={padding} style={{background:"var(--color-background-muted)", borderRadius:"var(--radius-container)", minWidth:0}}>
    {workbench.tables.length > 1 && <HStack gap={2} wrap="wrap" aria-label="Compare records">
      {workbench.tables.map((item) => <Button key={item.table_id} label={item.label} size="sm"
        variant={table?.table_id === item.table_id ? "primary" : "secondary"}
        aria-pressed={table?.table_id === item.table_id} onClick={() => setTableId(item.table_id)} />)}
    </HStack>}
    {table && <VStack gap={2} width="100%" style={{minWidth:0}}>
      {/* One line for the table name and what a row is. */}
      <Text><Text as="span" type="inherit" weight="semibold">{table.label}</Text> · {workbench.introduction}</Text>
      <VStack width="100%" style={CONTAINED_TABLE_STYLE}>
        <Table key={table.table_id} aria-label={table.label} data={table.rows.map((cells,index) => ({row:index, ...Object.fromEntries(cells.map((cell,column) => [`column${column}`, cell]))}))}
          idKey="row" density="balanced" dividers="rows" isStriped
          columns={table.columns.map((label,index) => ({key:`column${index}`, width:proportional(1),
            // Header cells otherwise truncate; a variable name or unit must stay readable.
            header:<Text as="span" type="inherit" style={{whiteSpace:"normal"}}>{label}</Text>}))} />
      </VStack>
      {table.note && <Text type="supporting">{table.note}</Text>}
    </VStack>}
  </VStack>;
}

function GuidedExperimentWorkbench({snapshot, draftState, onDraftChange, isWorking, isFrozen, onAction}: {
  snapshot:ExperimentSnapshot;
  draftState:GuidedPracticeDraft;
  onDraftChange:(changes:Partial<GuidedPracticeDraft>)=>void;
  isWorking:boolean;
  isFrozen:boolean;
  onAction:(action:Record<string,unknown>)=>void;
}) {
  const guide = snapshot.guide!;
  const {started,editing,config:draft,prediction,reflection} = draftState;
  const stepHeadingRef = useRef<HTMLHeadingElement>(null);
  useLayoutEffect(() => {
    if (started) stepHeadingRef.current?.focus({preventScroll:true});
  }, [started,editing,snapshot.phase]);
  const parameter = snapshot.parameters.find((item) => item.parameter_id === guide.parameter_id);
  const disabled = isWorking || isFrozen;
  const configuring = started && (snapshot.phase === "configure" || editing);
  const saved = started && snapshot.phase === "predicted" && !editing;
  const showingResult = started && !configuring && !saved && !!snapshot.result;
  const latestRun = snapshot.runs.at(-1);
  const previousRun = [...snapshot.runs].reverse().find((run) =>
    run.config[guide.parameter_id] !== latestRun?.config[guide.parameter_id]);
  const comparedRuns = previousRun && latestRun ? [previousRun,latestRun] : [];
  const interventionTableRuns = guide.section === "intervention"
    ? (comparedRuns.length ? comparedRuns : latestRun ? [latestRun] : []).filter((run) => run.result.tables.length > 0) : [];
  const otherSettingsChanged = comparedRuns.length > 0 && Object.keys(comparedRuns[0].config).some((key) =>
    key !== guide.parameter_id && comparedRuns[0].config[key] !== comparedRuns[1].config[key]);
  const settingLabel = (value:string|number|boolean) => parameter?.kind === "choice"
    ? parameter.options?.find((option) => option.option_id === value)?.label ?? String(value)
    : parameter?.kind === "toggle" ? value ? "On" : "Off" : `${value}${parameter?.unit ?? ""}`;
  const metricValue = (result:ExperimentResult, label:string) =>
    result.metrics.find((metric) => metric.label === label)?.display_value ?? "Not recorded";
  const beginEdit = () => {
    onDraftChange({editing:true,prediction:""});
  };
  const stepTitle = !started ? "The situation" : configuring ? snapshot.runs.length ? "Change one setting, then predict" : "Make your first prediction"
    : saved ? "Prediction saved. Run the test." : snapshot.can_submit_check ? "Comparison recorded" : comparedRuns.length ? "Compare the two tests" : "Read your first result";
  const generationCase = guide.section === "generation"
    ? snapshot.result?.cases.find((item) => item.metadata_known === false) ?? snapshot.result?.cases[0] : null;
  const earlierGenerationCase = generationCase && comparedRuns[0]?.result.cases.find((item) => item.case_id === generationCase.case_id);
  const flipCase = guide.parameter_id === "flip_cue" && comparedRuns.length
    ? comparedRuns[1].result.cases.find((item) => comparedRuns[0].result.cases.some((earlier) =>
      earlier.case_id === item.case_id && earlier.target === item.target && earlier.measurement === item.measurement && earlier.cue !== item.cue)) : null;
  const earlierFlipCase = flipCase && comparedRuns[0].result.cases.find((item) => item.case_id === flipCase.case_id);
  const presence = (value:string|number|boolean) => value === 1 || value === true ? "present" : value === 0 || value === false ? "absent" : String(value);
  return <VStack gap={5} width="100%" maxWidth={READING_WIDTH} style={{minWidth:0}} aria-label="Guided practice">
    <VStack gap={2}>
      <Text type="supporting">{guide.section === "intervention" ? "Intervention practice · Predict → Run → Compare"
        : guide.section === "generation" ? "Part 2 · Generation: write from the available record" : "Part 1 · Prediction: test a rule in a changed setting"}</Text>
      <Heading level={1}>{snapshot.title}</Heading>
      <Text>{guide.story}</Text>
      <Text weight="semibold">Your task: {guide.goal}</Text>
    </VStack>
    <VStack gap={4} width="100%" padding={4} style={{background:"var(--color-background-muted)",borderRadius:"var(--radius-container)",minWidth:0}}>
      <Heading ref={stepHeadingRef} level={2} tabIndex={-1} style={SCRIPT_FOCUS_STYLE}>{stepTitle}</Heading>
      {!started ? <>
        <Text>You will make a prediction, run one test, then change just one setting and compare. Your prediction and comparison are not graded.</Text>
        <Button label="Start practice" variant="primary" isDisabled={disabled} onClick={() => onDraftChange({started:true})} />
      </> : configuring && parameter ? <>
        <Text>{guide.parameter_description}</Text>
        {snapshot.runs.length > 0 && <Text type="supporting">Last tested: {guide.parameter_label}: {settingLabel(snapshot.config[guide.parameter_id])}. Keep everything else the same.</Text>}
        {parameter.kind === "range" ? <Slider label={guide.parameter_label} value={Number(draft[parameter.parameter_id])}
          min={parameter.min ?? 0} max={parameter.max ?? 100} step={parameter.step ?? 10}
          valueDisplay="text" formatValue={(value) => `${value}${parameter.unit ?? ""}`} width="100%" isDisabled={disabled}
          onChange={(value:number) => onDraftChange({config:{...draft,[parameter.parameter_id]:value}})} />
          : parameter.kind === "toggle" ? <CheckboxInput label={guide.parameter_label} value={!!draft[parameter.parameter_id]} isDisabled={disabled}
            onChange={(value) => onDraftChange({config:{...draft,[parameter.parameter_id]:value}})} />
          : <Selector label={guide.parameter_label} value={String(draft[parameter.parameter_id])} width="100%" isDisabled={disabled}
            options={(parameter.options ?? []).map((option) => ({value:option.option_id,label:option.label}))}
            onChange={(value) => onDraftChange({config:{...draft,[parameter.parameter_id]:value}})} />}
        <TextArea label={guide.prediction_prompt} description="A short guess is enough. This is not graded."
          value={prediction} onChange={(value) => onDraftChange({prediction:value})} rows={3} maxLength={800} width="100%" isDisabled={disabled} />
        <Button label="Save my prediction" variant="primary"
          isDisabled={disabled || !snapshot.legal_actions.includes("commit_prediction") || !prediction.trim() || Array.from(prediction.trim()).length > 800}
          onClick={() => onAction({kind:"commit_prediction",config:draft,prediction:prediction.trim()})} />
        {snapshot.runs.length > 0 && <Button label={snapshot.phase === "predicted" ? "Back to the saved prediction" : "Back to the recorded result"}
          variant="ghost" isDisabled={isWorking} onClick={() => onDraftChange({editing:false})} />}
      </> : saved ? <>
        <Text>{guide.parameter_label}: {settingLabel(snapshot.config[guide.parameter_id])}</Text>
        <Text>Your prediction: {snapshot.prediction}</Text>
        <HStack gap={2} wrap="wrap">
          <Button label="Run this test" variant="primary" isDisabled={disabled || !snapshot.legal_actions.includes("run")}
            onClick={() => onAction({kind:"run"})} />
          <Button label="Edit my setup or prediction" variant="secondary" isDisabled={disabled} onClick={() => onDraftChange({editing:true})} />
        </HStack>
      </> : showingResult && snapshot.result ? <>
        <Text type="supporting">Test {latestRun?.run_id} · {guide.parameter_label}: {settingLabel(snapshot.config[guide.parameter_id])}</Text>
        <Text>Your prediction: {snapshot.prediction}</Text>
        <VStack gap={2} role="status" aria-live="polite">
          {guide.metrics.map((metric) => <Text key={metric.metric_label}><Text as="span" weight="semibold">{metric.label}: </Text>{metricValue(snapshot.result!,metric.metric_label)}</Text>)}
        </VStack>
        {guide.section === "intervention" && snapshot.result.metrics.some((metric) => /\bpp\b/.test(metric.display_value))
          && <Text type="supporting">pp means percentage points: a difference between two percentages.</Text>}
        {interventionTableRuns.length > 0 && <VStack gap={4}>
          {interventionTableRuns.map((run) => <ComparisonWorkbenchCanvas key={`groups.${run.run_id}`} padding={0}
            workbench={{title:`Test ${run.run_id} · Starting groups`,introduction:"People in each programme's starting groups for this test.",
              scenario_id:`${snapshot.experiment_id}.run-${run.run_id}`,stage:"investigate",
              tables:run.result.tables.map((table) => ({...table,label:`Test ${run.run_id} · ${table.label}`}))}} />)}
        </VStack>}
        {generationCase?.source_text && generationCase.generated_text && <VStack gap={3}>
          <Text type="supporting">Example case {generationCase.case_id}{generationCase.metadata_known === false ? " · Required context is missing from this record." : " · Required context is recorded."}</Text>
          <VStack gap={1}><Text weight="semibold">One source record</Text><Text>{generationCase.source_text}</Text></VStack>
          {earlierGenerationCase?.generated_text && <VStack gap={1}>
            <Text weight="semibold">Test {comparedRuns[0].run_id} · Draft written by this rule</Text><Text>{earlierGenerationCase.generated_text}</Text>
          </VStack>}
          <VStack gap={1}><Text weight="semibold">Test {latestRun?.run_id} · Draft written by this rule</Text><Text>{generationCase.generated_text}</Text></VStack>
        </VStack>}
        {comparedRuns.length > 0 && <VStack gap={3}>
          <Text weight="semibold">{otherSettingsChanged ? "These saved tests also differ in other conditions. Compare them cautiously."
            : `Only this setting changed: ${guide.parameter_label}.`}</Text>
          <VStack width="100%" style={CONTAINED_TABLE_STYLE}>
            <Table aria-label="Compare the two tests" idKey="measure" density="balanced" dividers="rows"
              data={[
                {measure:guide.parameter_label,first:settingLabel(comparedRuns[0].config[guide.parameter_id]),second:settingLabel(comparedRuns[1].config[guide.parameter_id])},
                ...guide.metrics.map((metric) => ({measure:metric.label,first:metricValue(comparedRuns[0].result,metric.metric_label),second:metricValue(comparedRuns[1].result,metric.metric_label)})),
              ]}
              columns={[{key:"measure",header:"What to compare",width:proportional(2)},
                {key:"first",header:`Test ${comparedRuns[0].run_id}`,width:proportional(1)},
                {key:"second",header:`Test ${comparedRuns[1].run_id}`,width:proportional(1)}]} />
          </VStack>
        </VStack>}
        {flipCase && earlierFlipCase && <VStack gap={2}>
          <Text weight="semibold">Follow the same example · Case {flipCase.case_id}</Text>
          <Text>The simulated condition was {presence(flipCase.target)} in both tests. Its recorded measurement also stayed {presence(flipCase.measurement)}.</Text>
          <Text>Marker value: {String(earlierFlipCase.cue)} → {String(flipCase.cue)}. Predicted condition: {presence(earlierFlipCase.prediction)} → {presence(flipCase.prediction)}.</Text>
          <Text type="supporting">The marker has two labels, 0 and 1. Present and absent describe the condition being predicted. Changing a label did not change that condition.</Text>
        </VStack>}
        {!isFrozen && <Button label="Change one setting and test again" variant={comparedRuns.length ? "secondary" : "primary"}
          isDisabled={disabled || !snapshot.legal_actions.includes("commit_prediction")} onClick={beginEdit} />}
        {snapshot.legal_actions.includes("reflect") && !snapshot.can_submit_check && <>
          <TextArea label={guide.comparison_prompt} description="Compare the two results with your prediction. Your explanation is not graded."
            value={reflection} onChange={(value) => onDraftChange({reflection:value})} rows={3} maxLength={800} width="100%" isDisabled={disabled} />
          <Button label="Record my comparison" variant="primary"
            isDisabled={disabled || !reflection.trim() || Array.from(reflection.trim()).length > 800}
            onClick={() => onAction({kind:"reflect",reflection:reflection.trim()})} />
        </>}
        {snapshot.reflection && <Text>Recorded comparison: {snapshot.reflection}</Text>}
        {snapshot.can_submit_check ? <Text weight="semibold">Your comparison is saved. Check your interpretation below.</Text>
          : <Text type="supporting">{snapshot.distinct_runs < snapshot.min_distinct_runs
            ? "Try a different value of this setting, then compare the two results."
            : "Record your comparison to open the interpretation question."}</Text>}
        {isFrozen && <Text type="supporting">This practice has been checked. Its saved tests are read-only.</Text>}
      </> : <Text>The saved practice is ready to resume.</Text>}
    </VStack>
    {started && snapshot.runs.length > 0 && <Collapsible defaultIsOpen={false} trigger={<Text weight="semibold">Review recorded tests</Text>}>
      <VStack gap={4}>
        {snapshot.runs.map((run) => <VStack key={run.run_id} gap={1}>
          <Text weight="semibold">Test {run.run_id} · {guide.parameter_label}: {settingLabel(run.config[guide.parameter_id])}</Text>
          <Text>Prediction: {run.prediction}</Text>
          {guide.metrics.map((metric) => <Text key={metric.metric_label}>{metric.label}: {metricValue(run.result,metric.metric_label)}</Text>)}
        </VStack>)}
      </VStack>
    </Collapsible>}
  </VStack>;
}

function ExperimentWorkbench({snapshot, isWorking, isFrozen, onAction}: {
  snapshot:ExperimentSnapshot;
  isWorking:boolean;
  isFrozen:boolean;
  onAction:(action:Record<string,unknown>)=>void;
}) {
  const [draft,setDraft] = useState(snapshot.config);
  const [prediction,setPrediction] = useState(snapshot.prediction ?? "");
  const [reflection,setReflection] = useState(snapshot.reflection ?? "");
  const [selectedRunId,setSelectedRunId] = useState<number|null>(snapshot.runs.at(-1)?.run_id ?? null);
  useEffect(() => {
    setDraft(snapshot.config);
    setPrediction(snapshot.prediction ?? "");
    setReflection(snapshot.reflection ?? "");
    setSelectedRunId(snapshot.runs.at(-1)?.run_id ?? null);
  }, [snapshot.experiment_id,snapshot.revision]);
  const disabled = isWorking || isFrozen;
  const configChanged = snapshot.parameters.some((parameter) => draft[parameter.parameter_id] !== snapshot.config[parameter.parameter_id]);
  const predictionChanged = prediction.trim() !== (snapshot.prediction ?? "");
  const hasChanges = configChanged || predictionChanged;
  const selectedRun = snapshot.runs.find((run) => run.run_id === selectedRunId) ?? snapshot.runs.at(-1);
  const result = selectedRun?.result ?? snapshot.result;
  const latestRuns = snapshot.runs.slice(-2);
  const comparedMetrics = [...new Set(latestRuns.flatMap((run) => run.result.metrics.map((metric) => metric.label)))];
  const displaySetting = (parameter:ExperimentSnapshot["parameters"][number], value:string|number|boolean) =>
    parameter.kind === "choice" ? parameter.options?.find((option) => option.option_id === value)?.label ?? String(value)
      : parameter.kind === "toggle" ? value ? "On" : "Off" : `${value}${parameter.unit ?? ""}`;
  const comparisonRows = [
    ...snapshot.parameters.map((parameter) => ({metric:`Setting: ${parameter.label}`,
      ...Object.fromEntries(latestRuns.map((run) => [`run${run.run_id}`,displaySetting(parameter,run.config[parameter.parameter_id])]))})),
    ...comparedMetrics.map((label) => ({metric:label,...Object.fromEntries(latestRuns.map((run) => [
      `run${run.run_id}`,run.result.metrics.find((metric) => metric.label === label)?.display_value ?? "Not recorded",
    ]))})),
  ];
  const setParameter = (id:string,value:string|number|boolean) => setDraft((current) => ({...current,[id]:value}));
  return <VStack gap={5} width="100%" style={{minWidth:0}}>
    <VStack gap={2}>
      <Heading level={2}>{snapshot.title}</Heading>
      <Text>{snapshot.instruction}</Text>
      {isFrozen && <Text type="supporting">Your answer has been checked. These experiment settings are now read-only.</Text>}
    </VStack>
    <Grid columns={{minWidth:280,max:2,repeat:"fit"}} gap={5} align="start">
      <VStack gap={4} padding={4} style={{background:"var(--color-background-muted)",borderRadius:"var(--radius-container)",minWidth:0}}>
        <Heading level={3}>Set up your test</Heading>
        {snapshot.parameters.map((parameter) => parameter.kind === "range" ? <Slider key={parameter.parameter_id}
          label={parameter.label} value={Number(draft[parameter.parameter_id])}
          min={parameter.min ?? 0} max={parameter.max ?? 100} step={parameter.step ?? 10}
          valueDisplay="text" formatValue={(value) => `${value}${parameter.unit ?? ""}`}
          isDisabled={disabled} width="100%"
          onChange={(value:number) => setParameter(parameter.parameter_id,value)} />
          : parameter.kind === "toggle" ? <CheckboxInput key={parameter.parameter_id}
            label={parameter.label} value={!!draft[parameter.parameter_id]} isDisabled={disabled}
            onChange={(value) => setParameter(parameter.parameter_id,value)} />
          : <Selector key={parameter.parameter_id} label={parameter.label} value={String(draft[parameter.parameter_id])}
            options={(parameter.options ?? []).map((option) => ({value:option.option_id,label:option.label}))}
            isDisabled={disabled} width="100%" onChange={(value) => setParameter(parameter.parameter_id,value)} />)}
        <TextArea label="What do you predict?" description="A short guess is enough. Your prediction is not graded. Save it before running."
          value={prediction} onChange={setPrediction} rows={3} maxLength={800} width="100%" isDisabled={disabled} />
        <HStack gap={2} wrap="wrap">
          <Button label={snapshot.runs.length === 0 ? "Save my prediction" : "Save my next prediction"}
            variant="secondary" isDisabled={disabled || !snapshot.legal_actions.includes("commit_prediction") || prediction.trim() === ""}
            onClick={() => onAction({kind:"commit_prediction",config:draft,prediction:prediction.trim()})} />
          <Button label="Run experiment" variant="primary"
            isDisabled={disabled || hasChanges || !snapshot.legal_actions.includes("run")}
            onClick={() => onAction({kind:"run"})} />
        </HStack>
        {hasChanges && snapshot.phase !== "configure" && <Text type="supporting">These edits have not been saved. Save the new prediction before running them.</Text>}
        {snapshot.phase === "predicted" && !hasChanges && <Text type="supporting">Prediction saved. Run the experiment to reveal the result.</Text>}
      </VStack>
      <VStack gap={4} style={{minWidth:0}}>
        {snapshot.runs.length > 0 && <Selector label="Inspect a recorded run" value={String(selectedRun?.run_id ?? "")}
          options={snapshot.runs.map((run) => ({value:String(run.run_id),label:`Run ${run.run_id}`}))}
          onChange={(value) => setSelectedRunId(Number(value))} width="100%" />}
        {result ? <VStack gap={4}>
          <Heading level={3}>{result.title}</Heading>
          {selectedRun && <VStack gap={1}>
            <Text weight="semibold">Saved settings · Run {selectedRun.run_id}</Text>
            {snapshot.parameters.map((parameter) => {
              const value = selectedRun.config[parameter.parameter_id];
              return <Text key={parameter.parameter_id} type="supporting">{parameter.label}: {displaySetting(parameter,value)}</Text>;
            })}
          </VStack>}
          {selectedRun && <Text type="supporting">Recorded prediction: {selectedRun.prediction}</Text>}
          {snapshot.result === null && <Text type="supporting">This is a previous recorded result. Run the current settings to reveal their result.</Text>}
          <ExperimentPlot key={`plot.${snapshot.experiment_id}.${selectedRun?.run_id}`} metrics={result.bars} label="Experiment result comparison" />
          <Text>{result.summary}</Text>
          <List density="compact" hasDividers>
            {result.metrics.map((metric,index) => <ListItem key={`${metric.label}.${index}`} label={metric.label}
              endContent={<Text weight="semibold">{metric.display_value}</Text>} />)}
          </List>
          {result.cases.length > 0 && <ExperimentCaseInspector key={`cases.${snapshot.experiment_id}.${selectedRun?.run_id}`} cases={result.cases} />}
          {result.tables.length > 0 && <Collapsible trigger={<Text weight="semibold">Inspect the result records</Text>}>
            <ComparisonWorkbenchCanvas workbench={{title:result.title,introduction:"Records for this run.",
              scenario_id:`${snapshot.experiment_id}.${selectedRun?.run_id}`,stage:"investigate",tables:result.tables}} />
          </Collapsible>}
        </VStack> : <VStack gap={4} padding={4} style={{border:"var(--border-width) solid var(--color-border-emphasized)",borderRadius:"var(--radius-container)"}}>
          <Heading level={3}>No result yet</Heading>
          <Text>Choose your settings, save a prediction, then run the experiment.</Text>
          <Text type="supporting">Repeating the same setup gives the same teaching-model result, not a new random sample.</Text>
        </VStack>}
      </VStack>
    </Grid>
    {latestRuns.length === 2 && <VStack gap={3} width="100%">
      <Heading level={3}>Compare your last two runs</Heading>
      <Text>Check which settings changed before comparing the results. For a clear comparison, change only the setting named in the instructions.</Text>
      <VStack width="100%" style={CONTAINED_TABLE_STYLE}>
        <Table aria-label="Latest two experiment runs" data={comparisonRows} idKey="metric" density="compact" dividers="rows" isStriped
          columns={[{key:"metric",header:"Setting or measure",width:proportional(2)},
            ...latestRuns.map((run) => ({key:`run${run.run_id}`,header:`Run ${run.run_id}`,width:proportional(1)}))]} />
      </VStack>
    </VStack>}
    {snapshot.runs.length > 0 && <VStack gap={3} padding={4} style={{background:"var(--color-background-muted)",borderRadius:"var(--radius-container)"}}>
      <HStack gap={2} hAlign="between" wrap="wrap">
        <Heading level={3}>Compare and explain</Heading>
        <Text type="supporting">Different setups tried: {snapshot.distinct_runs} · At least {snapshot.min_distinct_runs} required</Text>
      </HStack>
      <Text>Compare the saved results with your prediction. Keep or revise your explanation, and give a reason. The explanation itself is not graded.</Text>
      <TextArea label="What did the comparison show?"
        description="Say what changed, whether it matched your prediction, and why you kept or changed your explanation."
        value={reflection} onChange={setReflection} rows={3} maxLength={800} isDisabled={disabled} width="100%" />
      <HStack gap={2} wrap="wrap">
        <Button label="Record my comparison" variant="primary"
          isDisabled={disabled || hasChanges || !snapshot.legal_actions.includes("reflect") || reflection.trim() === ""}
          onClick={() => onAction({kind:"reflect",reflection:reflection.trim()})} />
        {snapshot.distinct_runs < snapshot.min_distinct_runs && <Text type="supporting">Test another setting before recording the comparison.</Text>}
      </HStack>
      {hasChanges && <Text type="supporting">Your edited settings or prediction have not been run. Save and run them before recording this comparison.</Text>}
      {snapshot.reflection && <Text type="supporting">Recorded comparison: {snapshot.reflection}</Text>}
    </VStack>}
    {snapshot.can_submit_check ? <Text weight="semibold">Your experiment comparison is recorded. Check your interpretation below.</Text>
      : <Text type="supporting">Test {snapshot.min_distinct_runs} different settings and record your comparison to open the interpretation check below.</Text>}
  </VStack>;
}

function ExperimentPlot({metrics,label}: {metrics:ExperimentMetric[]; label:string}) {
  const [selected,setSelected] = useState(0);
  const metric = metrics[selected] ?? metrics[0];
  return <VStack gap={2} width="100%" style={{minWidth:0}}>
    <svg viewBox={`0 0 520 ${metrics.length*72+38}`} role="group" aria-label={label}
      style={{width:"100%",color:"var(--color-text-primary)",fontFamily:"var(--font-family-body)"}}>
      {[0,25,50,75,100].map((tick) => <g key={tick}>
        <line x1={10+tick*4.5} x2={10+tick*4.5} y1="20" y2={metrics.length*72+12} stroke="var(--color-border)" />
        <text x={10+tick*4.5} y={metrics.length*72+32} fontSize="12" textAnchor="middle" fill="var(--color-text-secondary)">{tick}</text>
      </g>)}
      {metrics.map((item,index) => <g key={`${item.label}.${index}`} role="button" tabIndex={0}
        aria-label={`${item.label}: ${item.display_value}`} aria-pressed={selected === index}
        onClick={() => setSelected(index)} onKeyDown={(event) => {if (event.key === "Enter" || event.key === " ") {event.preventDefault(); setSelected(index);}}}
        style={{cursor:"pointer"}}>
        <title>{item.label}: {item.display_value}</title>
        <rect x="4" y={index*72+3} width="510" height="68" rx="6" fill="transparent"
          stroke={selected === index ? "var(--color-accent)" : "transparent"} />
        <text x="12" y={index*72+23} fontSize="14" fill="currentColor">{item.label}</text>
        <rect x="12" y={index*72+34} width="450" height="24" rx="4" fill="var(--color-background-muted)" />
        <rect x="12" y={index*72+34} width={Math.max(0,Math.min(100,item.value))*4.5} height="24" rx="4" fill="var(--color-accent)" />
      </g>)}
    </svg>
    {metric && <Text weight="semibold" aria-live="polite">{metric.label}: {metric.display_value}</Text>}
  </VStack>;
}

function ExperimentCaseInspector({cases}: {cases:ExperimentResult["cases"]}) {
  const [caseId,setCaseId] = useState(String(cases[0]?.case_id ?? ""));
  const example = cases.find((item) => String(item.case_id) === caseId) ?? cases[0];
  if (!example) return null;
  return <VStack gap={3} padding={4} style={{background:"var(--color-background-muted)",borderRadius:"var(--radius-container)",minWidth:0}}>
    <Heading level={3}>Inspect a generated case</Heading>
    <Text type="supporting">Selected example cases are shown here; the summary uses all 100 teaching cases.</Text>
    <Selector label="Case" value={String(example.case_id)} width="100%" onChange={setCaseId}
      options={cases.map((item) => ({value:String(item.case_id),label:`Case ${item.case_id}`}))} />
    <VStack gap={1}><Text weight="semibold">Source record</Text><Text>{example.source_text}</Text></VStack>
    <VStack gap={1}><Text weight="semibold">Generated draft</Text><Text>{example.generated_text}</Text></VStack>
    <Text type="supporting">1 means present; 0 means absent. Reference is the teaching model's answer. Measurement is the recorded flag, prediction is the rule's output, and cue is the site label.</Text>
    <Text type="supporting">Prediction: {String(example.prediction)} · Reference: {String(example.target)} · Cue: {String(example.cue)} · Measurement: {String(example.measurement)}</Text>
    {example.emitted === false && <Token label="Withheld" color="gray" size="sm" />}
    {example.metadata_known === false && <Token label="Required context missing" color="gray" size="sm" />}
    {example.unsupported_addition && <Token label="Unsupported addition" color="orange" size="sm" />}
    {example.source_consistent && example.emitted !== false && <Token label="Source flag preserved" color="green" size="sm" />}
  </VStack>;
}

function LearningScreen({
  state,
  guidedDraft,
  onGuidedDraftChange,
  isIntroductionOpen,
  onIntroductionOpenChange:setIsIntroductionOpen,
  messageDraft,
  onMessageDraftChange,
  error,
  isWorking,
  onRun,
  onSendMessage,
  onReconnect,
  onSelectModule,
  onChangeProfile,
}: {
  state: DemoState;
  guidedDraft:GuidedPracticeDraft|null;
  onGuidedDraftChange:(update:(previous:GuidedPracticeDraft|null)=>GuidedPracticeDraft)=>void;
  isIntroductionOpen:boolean;
  onIntroductionOpenChange:(open:boolean)=>void;
  messageDraft: string;
  onMessageDraftChange: (value:string) => void;
  error: string | null;
  isWorking: boolean;
  onRun: (path: string, body?: Record<string, unknown>) => Promise<void>;
  onSendMessage: (text: string) => Promise<boolean>;
  onReconnect: () => void;
  onSelectModule: (moduleId: string, testOnlyForceUnlock?: boolean) => void;
  onChangeProfile: () => void;
}) {
  const isWide = useMediaQuery(WIDE_WORKSPACE_QUERY);
  const [isReviewing, setIsReviewing] = useState(false);
  const [startedFinalAttempt, setStartedFinalAttempt] = useState<string | null>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const introductionTitleRef = useRef<HTMLHeadingElement>(null);
  const finalCheckTitleRef = useRef<HTMLHeadingElement>(null);
  const introductionButtonRef = useRef<HTMLButtonElement>(null);
  const learningScrollRef = useRef<{scope:string; top:number; left:number; windowX:number; windowY:number}|null>(null);
  useEffect(() => setIsReviewing(false), [state.profile_id, state.active_module_id, state.review_mode]);
  const introduction = state.course_introduction;
  const showIntroduction = !!introduction && (state.status === "not_started" || isIntroductionOpen);
  const finalAttemptScope = `${state.active_module_id}.${state.profile_id}.${state.learning_pack_version}.${state.attempt_id}`;
  const showFinalCheckIntroduction = state.status === "active" && !showIntroduction
    && !state.review_mode && !state.preview_mode && !state.lesson_is_sample
    && !!state.final_check?.is_current && state.final_check.completed_count === 0
    && !state.assessment_submitted && !state.assessment_accepted && !state.can_continue
    && startedFinalAttempt !== finalAttemptScope;
  const introductionScope = `${state.active_module_id}.${state.profile_id}`;
  useLayoutEffect(() => {
    const content = contentRef.current;
    if (showIntroduction) {
      if (!(state.profile_required && !state.preview_mode)) {
        content?.scrollTo({top:0,left:0});
        introductionTitleRef.current?.scrollIntoView({block:"start"});
        introductionTitleRef.current?.focus({preventScroll:true});
      }
    } else {
      const previous = learningScrollRef.current;
      if (previous?.scope === introductionScope) {
        content?.scrollTo({top:previous.top,left:previous.left});
        window.scrollTo(previous.windowX,previous.windowY);
        introductionButtonRef.current?.focus({preventScroll:true});
      } else if (previous) content?.scrollTo({top:0,left:0});
      learningScrollRef.current = null;
    }
  }, [showIntroduction,introductionScope,state.profile_required,state.preview_mode]);
  useLayoutEffect(() => {
    if (state.status !== "active" || showIntroduction || (state.profile_required && !state.preview_mode)) return;
    contentRef.current?.scrollTo({top:0,left:0});
    if (showFinalCheckIntroduction) {
      finalCheckTitleRef.current?.focus({preventScroll:true});
      return;
    }
    document.getElementById("learning-activity")?.focus({preventScroll:true});
    // Only a new activity/attempt moves focus; chat and experiment updates keep drafts and scroll position.
  }, [state.active_module_id,state.profile_id,state.attempt_id,state.activity_id,showFinalCheckIntroduction]);
  const openIntroduction = () => {
    learningScrollRef.current = {scope:introductionScope,top:contentRef.current?.scrollTop ?? 0,
      left:contentRef.current?.scrollLeft ?? 0,windowX:window.scrollX,windowY:window.scrollY};
    setIsIntroductionOpen(true);
  };
  const concepts = moduleConcepts(state);
  const currentConcept = state.activity_concept_id ?? conceptForActivity(state.activity_id, concepts);
  const courseTitle = state.course_title ?? state.title;
  const allMessages = state.conversation ?? [];
  const messages = allMessages.filter(
    (message) => message.attempt_id === state.attempt_id,
  );
  const firstLearnerMessage = messages.findIndex(message => message.role === "learner");
  const visibleMessages = showFinalCheckIntroduction
    ? firstLearnerMessage < 0 ? [] : messages.slice(firstLearnerMessage)
    : messages;
  const hasCurrentQuestion = state.question !== undefined && state.question !== null;
  const guidedExperiment = !!state.experiment?.guide;
  const guidedScope = `${state.active_module_id}.${state.profile_id}.${state.learning_pack_version}.${state.attempt_id}.${state.experiment?.experiment_id}`;
  const canTalk = state.status === "active" || !!state.review_available;
  const navigateConcept = (conceptId: string) => {
    if (showIntroduction) {
      learningScrollRef.current = null;
      setIsIntroductionOpen(false);
      contentRef.current?.scrollTo({top:0,left:0});
    }
    if (state.review_available)
      return onRun("/api/review-topic", {concept_id:conceptId});
    const activity = state.preview_activities?.find((item) => item.concept_id === conceptId);
    return state.preview_mode && activity
      ? onRun("/api/preview/navigate", {activity_id:activity.activity_id})
      : onRun("/api/navigate", {request_id:requestId("navigate"), concept_id:conceptId});
  };
  const navigateFinalCheck = () => {
    if (showIntroduction) {
      learningScrollRef.current = null;
      setIsIntroductionOpen(false);
      contentRef.current?.scrollTo({top:0,left:0});
    }
    return onRun("/api/final-check", {request_id:requestId("final-check")});
  };
  const main = (
    <VStack
      gap={5}
      width="100%"
      maxWidth="100%"
    >
      {state.review_mode && <HStack gap={3} hAlign="between" vAlign="center" wrap="wrap">
        <Text type="supporting">{state.final_check?.is_current ? "Final check review" : "Topic review"} · Your course progress is saved.</Text>
        <Button label="Back to my course" variant="ghost" size="sm" isDisabled={isWorking}
          onClick={() => void onRun("/api/end-review")} />
      </HStack>}
      {state.preview_mode && <PreviewControls state={state} isWorking={isWorking} onRun={onRun} />}
      {state.preview_mode && !state.lesson && (state.lesson_profiles?.length ?? 0) > 0 && <LessonEntry state={state} isWorking={isWorking} onRun={onRun} />}
      {(error !== null ||
        state.tutor_status === "unreachable" ||
        state.pending_tutor_message !== null &&
          state.pending_tutor_message !== undefined) && (
        <ConnectionNotice
          title={
            state.pending_tutor_message !== null &&
            state.pending_tutor_message !== undefined
              ? "Tutor response pending"
              : "Tutor request failed"
          }
          description={
            error ??
            "Your message is saved, but the tutor has not replied yet. Retry it when the tutor is available."
          }
          actionLabel={
            state.pending_tutor_message !== null &&
            state.pending_tutor_message !== undefined
              ? "Retry saved message"
              : "Reconnect"
          }
          onReconnect={onReconnect}
        />
      )}
      {showIntroduction && <CourseIntroductionCanvas key="course-introduction" introduction={introduction}
        hideCaption={state.active_module_id === "m1_shift"}
        titleRef={introductionTitleRef}
        isWorking={isWorking} hasStarted={state.status !== "not_started"}
        onContinue={() => state.status === "not_started" ? void onRun("/api/start") : setIsIntroductionOpen(false)} />}
      {showFinalCheckIntroduction && <FinalCheckIntroduction
        courseTitle={courseTitle} topicCount={concepts.length} questionCount={state.final_check!.total_count}
        topicsComplete={concepts.length > 0 && concepts.every(concept => state.topic_practice_completed_concept_ids?.includes(concept.id))}
        titleRef={finalCheckTitleRef} isWorking={isWorking}
        onStart={() => setStartedFinalAttempt(finalAttemptScope)}
        onReview={() => { const lastTopic = concepts.at(-1); if (lastTopic) void navigateConcept(lastTopic.id); }} />}
      {/* Keep drafts mounted while the learner revisits the course introduction. */}
      <VStack key="learning-content" id="learning-activity" role="region" aria-label="Learning activity" tabIndex={-1}
        gap={5} width="100%" style={showIntroduction || showFinalCheckIntroduction ? {display:"none"} : SCRIPT_FOCUS_STYLE}>
      {state.status === "not_started" && !introduction && (
        <QuizIntro
          title={state.modules.find((module) => module.module_id === state.active_module_id)?.title ?? state.title}
          isWorking={isWorking}
          onStart={() => void onRun("/api/start")}
          onStartScene={state.practical_mission ? () => void onRun("/api/start-scene") : undefined}
          diagnostic={false}
        />
      )}
      {state.status === "completed" && state.preview_mode && (
        <Banner status="info" title="Preview attempt complete" description="This was a test attempt. Your learning progress has not changed. Open another activity above or return to learning." />
      )}
      {state.status === "completed" && !state.preview_mode && state.lesson_is_sample && (
        <VStack gap={3}>
          <Heading level={1}>Lesson sample complete</Heading>
          <Text>You practised the distinction and checked a new case. This completes this sample, not the full Foundations course or a claim of mastery.</Text>
          <Button label="Return to Foundations" variant="primary" onClick={() => onSelectModule("causality_m0")} />
        </VStack>
      )}
      {state.status === "completed" && !state.preview_mode && !state.lesson_is_sample && (
        <RouteCompleteSummary
          key={`${state.active_module_id}.${state.profile_id}.${state.learning_pack_id}.${state.learning_pack_version}`}
          state={state}
          isReviewing={isReviewing}
          onReviewChange={setIsReviewing}
          isWorking={isWorking}
          onSelectModule={onSelectModule}
        />
      )}
      {state.status === "active" && (
        <VStack gap={6}>
          {state.profile_id === "medical" && state.causal_scene && <Text type="supporting">This fictional umbrella exercise practises the same causal idea. You do not need medical knowledge.</Text>}
          {state.lesson && !state.causal_scene && state.workbench?.stage !== "capstone" && !state.experiment ? <LessonCanvas key={`${state.profile_id}.${state.attempt_id}`} lesson={state.lesson} state={state} isWorking={isWorking} onRun={onRun} />
          : state.causal_scene !== null && state.causal_scene !== undefined ? (
            <CausalSceneWorkbench
              key={`${state.profile_id}.${state.attempt_id}.${state.activity_id}`}
              scene={state.causal_scene}
              isWorking={isWorking}
              canContinue={state.can_continue ?? false}
              onShareHypothesis={onSendMessage}
              onSceneAction={(action) =>
                void onRun("/api/scene-action", {
                  request_id: requestId("scene"),
                  input_revision: state.causal_scene?.revision ?? 0,
                  action,
                })
              }
              onSubmitEvidence={() =>
                void onRun("/api/scene-evidence", {
                  request_id: requestId("scene-evidence"),
                })
              }
              onContinue={() =>
                void onRun("/api/continue", {
                  request_id: requestId("continue"),
                })
              }
            />
          ) : hasCurrentQuestion && (
            <InvestigationCanvas
              image={state.scenario_image ?? null}
              recordText={state.workbench?.prompt ?? state.question ?? ""}
              workbench={state.workbench}
              deferQuestion={guidedExperiment}
              experiment={state.experiment ? guidedExperiment ? <GuidedExperimentWorkbench key={`${state.profile_id}.${state.attempt_id}.${state.experiment.experiment_id}`}
                snapshot={state.experiment} isWorking={isWorking} isFrozen={!!state.assessment_accepted}
                draftState={guidedPracticeDraft(state.experiment,guidedScope,guidedDraft)}
                onDraftChange={(changes) => onGuidedDraftChange((previous) => ({...guidedPracticeDraft(state.experiment!,guidedScope,previous),...changes}))}
                onAction={(action) => void onRun("/api/experiment-action", {
                  request_id:requestId("experiment"), attempt_id:state.attempt_id,
                  experiment_id:state.experiment?.experiment_id, input_revision:state.experiment?.revision, action,
                })} /> : <ExperimentWorkbench key={`${state.profile_id}.${state.attempt_id}.${state.experiment.experiment_id}`}
                snapshot={state.experiment} isWorking={isWorking} isFrozen={!!state.assessment_accepted}
                onAction={(action) => void onRun("/api/experiment-action", {
                  request_id:requestId("experiment"), attempt_id:state.attempt_id,
                  experiment_id:state.experiment?.experiment_id, input_revision:state.experiment?.revision, action,
                })} /> : undefined}
              conceptId={currentConcept}
              concepts={concepts}
              commitment={
                guidedExperiment && !state.experiment?.can_submit_check ? undefined : <VStack gap={3}>
                {!state.can_continue && <AnswerFeedbackNotice feedback={state.answer_feedback}
                  choices={state.choices ?? []} />}
                {state.can_continue ? (
                  <CommitBar
                    isWorking={isWorking}
                    onContinue={() =>
                      void onRun("/api/continue", {
                        request_id: requestId("continue"),
                      })
                    }
                  />
                ) : (
                  <AnswerCommitment
                    activityKey={`${state.attempt_id}.${state.activity_id ?? "current"}`}
                    choices={state.choices ?? []}
                    isWorking={isWorking || !!state.experiment && !state.experiment.can_submit_check}
                    onCommit={(optionId) =>
                      void onRun("/api/respond", {
                        request_id: requestId("answer"),
                        option_id: optionId,
                      })
                    }
                  />
                )}
                </VStack>
              }
            />
          )}
          {!hasCurrentQuestion && !state.can_continue && (
            <AnswerCommitment
              activityKey={`${state.attempt_id}.${state.activity_id ?? "current"}`}
              choices={state.choices ?? []}
              isWorking={isWorking}
              onCommit={(optionId) =>
                void onRun("/api/respond", {
                  request_id: requestId("answer"),
                  option_id: optionId,
                })
              }
            />
          )}
        </VStack>
      )}
      </VStack>
    </VStack>
  );
  const complete = state.status === "completed";
  return (
    <AppShell
      contentPadding={0}
      height="fill"
      variant="wash"
      style={isWide ? { height: "100%" } : undefined}
    >
      <Layout
        height="fill"
        contentWidth={isWide ? "100%" : "72ch"}
        padding={0}
        defaultHasDividers
        header={
          <LayoutHeader
            hasDivider
            label="EducAgent workspace"
            style={{ padding: isWide ? "var(--spacing-4) var(--spacing-6)" : undefined }}
          >
            <HStack gap={2} hAlign="between" vAlign="center" wrap="wrap" width="100%" style={{minWidth:0}}>
          <HStack gap={2} vAlign="center" wrap="wrap" style={{minWidth:0,maxWidth:"100%",flex:"1 1 22ch"}}>
            <Text weight="semibold" style={{ fontSize: "16px", letterSpacing: "-0.01em" }}>
              EducAgent
            </Text>
            <Text type="supporting">
              {showIntroduction
                ? `${courseTitle} · Introduction`
                : isReviewing
                ? `${courseTitle} · Trace`
                : complete
                  ? `${courseTitle} · Route complete`
                  : state.final_check?.is_current
                  ? `${courseTitle} · Final check`
                  : `${courseTitle} · ${
                      concepts.find(
                        (concept) =>
                          concept.id ===
                          currentConcept,
                      )?.label ?? "Investigation"
                    }`}
            </Text>
          </HStack>
          <HStack gap={2} vAlign="center" wrap="wrap" style={{minWidth:0,maxWidth:"100%",flex:"0 1 auto"}}>
            {!isWide && canTalk && <Button label="Go to Tutor" variant="secondary" size="sm"
              href="#educagent-tutor" aria-controls="educagent-tutor" />}
            {state.preview_mode && <Button label="Return to learning" variant="ghost" size="sm"
              isDisabled={isWorking} onClick={() => void onRun("/api/preview", {enabled:false})} />}
            <ProfileButton state={state} isWorking={isWorking} onChange={onChangeProfile} />
            {introduction && state.status !== "not_started" && <Button ref={introductionButtonRef}
              label={guidedExperiment ? "Leave practice" : "Course introduction"} variant="ghost" size="sm" isDisabled={isWorking}
              style={showIntroduction ? {display:"none"} : undefined} onClick={openIntroduction} />}
            {state.modules.length > 1 && (
              <ModuleSwitcher
                modules={state.modules}
                activeModuleId={state.active_module_id}
                isWorking={isWorking}
                onSelectModule={onSelectModule}
              />
            )}
            {isReviewing && !showIntroduction ? (
              <Button
                label="Back to workspace"
                variant="secondary"
                size="sm"
                onClick={() => setIsReviewing(false)}
              />
            ) : (
              <>
                  <HStack gap={1} vAlign="center">
                    <StatusDot
                      variant={
                        state.tutor_status === "unreachable"
                          ? "warning"
                          : "success"
                      }
                      label={
                        state.tutor_status === "unreachable"
                          ? "Tutor disconnected"
                          : "Tutor ready"
                      }
                    />
                    <Text type="supporting">
                      {state.tutor_status === "unreachable"
                        ? "Tutor disconnected"
                        : "Tutor ready"}
                    </Text>
                  </HStack>
                <Button
                  label="Reset progress"
                  variant="ghost"
                  size="sm"
                  isDisabled={isWorking}
                  onClick={() => void onRun("/api/reset")}
                />
              </>
            )}
          </HStack>
            </HStack>
          </LayoutHeader>
        }
        content={
          <LayoutContent
            ref={contentRef}
            padding={isWide ? 6 : 4}
            label="Causal investigation canvas"
            style={{padding:isWide ? "var(--spacing-6) var(--spacing-8)" : undefined, minWidth:0}}
          >
            <VStack gap={6} width="100%">
              {main}
              {!isWide && canTalk && (
                <TutorPanel
                  showBackToActivity={!showIntroduction && !showFinalCheckIntroduction}
                  messageDraft={messageDraft}
                  onMessageDraftChange={onMessageDraftChange}
                  routeComplete={complete}
                  messages={visibleMessages}
                  isWorking={isWorking}
                  tutorDirection={
                    state.causal_scene?.next_interaction_focus_label ?? null
                  }
                  conceptId={currentConcept}
                  concepts={concepts}
                  completed={conceptsWithRouteCredit(state)}
                  topicCompleted={state.topic_practice_completed_concept_ids ?? []}
                  finalCheck={state.preview_mode || state.lesson_is_sample ? null : state.final_check}
                  started={conceptsWithPractice(state)}
                  current={currentConcept}
                  diagnosticStatuses={state.diagnostic?.concept_results ?? []}
                  canExplain={state.can_send_message !== false}
                  canSend={state.can_send_message !== false && state.pending_tutor_message == null}
                  onExplain={() =>
                    void onRun("/api/explain", {
                      request_id: requestId("explain"),
                    })
                  }
                  onNavigate={(conceptId) => void navigateConcept(conceptId)}
                  onFinalCheck={() => void navigateFinalCheck()}
                  onSend={onSendMessage}
                />
              )}
            </VStack>
          </LayoutContent>
        }
        end={
          isWide && (!isReviewing || showIntroduction) ? (
            <LayoutPanel
              hasDivider
              padding={canTalk ? 0 : 4}
              width={canTalk ? 420 : 400}
              label={canTalk ? "EducAgent tutor" : "Learning route"}
              isScrollable={!canTalk}
              style={canTalk ? { background: "var(--color-background-muted)" } : ENTRY_ROUTE_PANEL_STYLE}
            >
              {canTalk ? (
                <TutorPanel
                  messageDraft={messageDraft}
                  onMessageDraftChange={onMessageDraftChange}
                  routeComplete={complete}
                  messages={visibleMessages}
                  isWorking={isWorking}
                  tutorDirection={
                    state.causal_scene?.next_interaction_focus_label ?? null
                  }
                  conceptId={currentConcept}
                  concepts={concepts}
                  completed={conceptsWithRouteCredit(state)}
                  topicCompleted={state.topic_practice_completed_concept_ids ?? []}
                  finalCheck={state.preview_mode || state.lesson_is_sample ? null : state.final_check}
                  started={conceptsWithPractice(state)}
                  current={currentConcept}
                  diagnosticStatuses={state.diagnostic?.concept_results ?? []}
                  canExplain={state.can_send_message !== false}
                  canSend={state.can_send_message !== false && state.pending_tutor_message == null}
                  onExplain={() =>
                    void onRun("/api/explain", {
                      request_id: requestId("explain"),
                    })
                  }
                  onNavigate={(conceptId) => void navigateConcept(conceptId)}
                  onFinalCheck={() => void navigateFinalCheck()}
                  onSend={onSendMessage}
                />
              ) : state.status === "not_started" ? (
                <EntryRouteRail state={state} isWorking={isWorking} onSelectModule={onSelectModule} />
              ) : (
                <ContextRail
                  state={state}
                  isWorking={isWorking}
                  onNavigate={(conceptId) => void navigateConcept(conceptId)}
                  onFinalCheck={() => void navigateFinalCheck()}
                />
              )}
            </LayoutPanel>
          ) : undefined
        }
      />
    </AppShell>
  );
}

function CausalSceneWorkbench({
  scene,
  isWorking,
  canContinue,
  onShareHypothesis,
  onSceneAction,
  onSubmitEvidence,
  onContinue,
}: {
  scene: CausalScene;
  isWorking: boolean;
  canContinue: boolean;
  onShareHypothesis: (text: string) => Promise<boolean>;
  onSceneAction: (action: Record<string, unknown>) => void;
  onSubmitEvidence: () => void;
  onContinue: () => void;
}) {
  const [edges, setEdges] = useState<string[]>([]);
  const [prediction, setPrediction] = useState("");
  const [reflection, setReflection] = useState("");
  const [hypothesis, setHypothesis] = useState("");
  const keepExplanationStarter = "I am keeping my current arrows because ";
  const savedEdgesKey = scene.graph_edges.map(edgeKey).join("|");
  useEffect(() => {
    setEdges(scene.graph_edges.map(edgeKey));
    setPrediction(scene.prediction_id ?? "");
    setReflection(scene.reflection ?? "");
    // A chat refresh must not clear an unsaved explanation or graph draft.
  }, [scene.revision, savedEdgesKey, scene.prediction_id, scene.reflection]);

  const nodeLabel = (nodeId: string) =>
    scene.nodes.find((node) => node.node_id === nodeId)?.label ?? labelFromConceptId(nodeId);
  const selectedEdges = scene.permitted_edges.filter((edge) =>
    edges.includes(edgeKey(edge)),
  );
  const hasReverse = (edge: SceneEdge) =>
    edges.includes(`${edge.child_id}->${edge.parent_id}`);
  const submit = (action: Record<string, unknown>) => onSceneAction(action);

  if (scene.simulation) return <DynamicUmbrellaWorkbench scene={scene} simulation={scene.simulation}
    isWorking={isWorking} canContinue={canContinue} onShareHypothesis={onShareHypothesis}
    onSceneAction={onSceneAction} onSubmitEvidence={onSubmitEvidence} onContinue={onContinue} />;

  return (
    <VStack gap={6} width="100%">
      <VStack gap={2} width="100%">
        <Heading level={1} type="display-3" textWrap="pretty">
          {scene.title}
        </Heading>
      </VStack>

      {scene.phase === "hook" && (
        <VStack width="100%">
          <VStack padding={4} style={{background:"var(--color-background-muted)", borderRadius:"var(--radius-container)"}}>
            <VStack gap={3}>
              <Text>{scene.resources.hook}</Text>
              <TextArea
                label="Why might umbrellas and wet pavement occur together?"
                description="Share your idea with the tutor, or view the data to investigate."
                value={hypothesis}
                onChange={setHypothesis}
                placeholder="Describe a possible explanation. It is fine to be unsure."
                rows={3}
                maxLength={800}
                isDisabled={isWorking}
                width="100%"
              />
              <HStack gap={2} wrap="wrap">
                <Button
                  label="Discuss my idea with EducAgent"
                  tooltip="Send your idea to the tutor without opening the data."
                  variant="secondary"
                  isDisabled={isWorking || hypothesis.trim() === ""}
                  onClick={async () => {
                    if (await onShareHypothesis(hypothesis.trim())) setHypothesis("");
                  }}
                />
                <Button
                  label="View the data"
                  tooltip="Open the recorded data and continue the exercise."
                  variant="primary"
                  isDisabled={isWorking}
                  onClick={() => submit({ kind: "open_records" })}
                />
              </HStack>
            </VStack>
          </VStack>
        </VStack>
      )}

      {scene.phase !== "hook" && (
        <VStack width="100%">
          <VStack gap={3}>
            <HStack hAlign="between" vAlign="center" wrap="wrap">
              <VStack gap={0.5}>
                <Text type="supporting">Example dataset</Text>
                <Text>{scene.resources.records}</Text>
              </VStack>
              <Token label="Observation" color="gray" size="sm" />
            </HStack>
            <SceneRecordsTable records={scene.observed_records} label="Recorded umbrella and pavement data" />
          </VStack>
        </VStack>
      )}

      {scene.phase === "records" && (
        <VStack padding={4} style={{background:"var(--color-background-muted)", borderRadius:"var(--radius-container)"}}>
          <VStack gap={4}>
            <VStack gap={1}>
              <Text type="supporting">Your proposed causal model</Text>
              <Text>{scene.resources.model}</Text>
            </VStack>
            <SceneModelGraph scene={scene} edges={edges} onChange={setEdges} isDisabled={isWorking} />
            <CheckboxList
              label="Select the arrows you currently propose"
              description="You can revise these arrows after comparing the result. Do not select both directions between two variables."
              value={edges}
              onChange={setEdges}
              isDisabled={isWorking}
              hasDividers
              width="100%"
            >
              {scene.permitted_edges.map((edge) => (
                <CheckboxListItem
                  key={edgeKey(edge)}
                  value={edgeKey(edge)}
                  label={`${nodeLabel(edge.parent_id)} → ${nodeLabel(edge.child_id)}`}
                  isDisabled={!edges.includes(edgeKey(edge)) && hasReverse(edge)}
                />
              ))}
            </CheckboxList>
            <HStack>
              <Button
                label="Commit this model"
                variant="primary"
                isDisabled={isWorking || selectedEdges.length === 0}
                onClick={() => submit({ kind: "submit_graph", edges: selectedEdges })}
              />
            </HStack>
          </VStack>
        </VStack>
      )}

      {scene.phase === "model" && (
        <VStack padding={4} style={{background:"var(--color-background-muted)", borderRadius:"var(--radius-container)"}}>
          <VStack gap={4}>
            <VStack gap={1}>
              <Text type="supporting">Predict before the reveal</Text>
              <Text>{scene.resources.prediction}</Text>
            </VStack>
            <SceneModelGraph scene={scene} edges={edges} />
            <RadioList
              label="If everyone carried an umbrella on purpose, what would you expect?"
              value={prediction}
              onChange={setPrediction}
              isDisabled={isWorking}
              isRequired
              htmlName={`scene.${scene.scene_id}.prediction`}
              width="100%"
            >
              {scene.predictions.map((option) => (
                <RadioListItem
                  key={option.prediction_id}
                  label={option.label}
                  value={option.prediction_id}
                />
              ))}
            </RadioList>
            <HStack>
              <Button
                label="Record my prediction"
                variant="primary"
                isDisabled={isWorking || prediction === ""}
                onClick={() =>
                  submit({ kind: "submit_prediction", prediction_id: prediction })
                }
              />
            </HStack>
          </VStack>
        </VStack>
      )}

      {scene.phase === "prediction" && (
        <VStack padding={4} style={{background:"var(--color-background-muted)", borderRadius:"var(--radius-container)"}}>
          <VStack gap={4}>
            <VStack gap={1}>
              <Heading level={2}>Everyone carries an umbrella</Heading>
              <Text>{scene.resources.intervention}</Text>
            </VStack>
            <Button
              label="Show the result"
              variant="primary"
              isDisabled={isWorking}
              onClick={() =>
                submit({
                  kind: "run_intervention",
                  intervention_action_id: scene.intervention.action_id,
                })
              }
            />
          </VStack>
        </VStack>
      )}

      {(scene.phase === "comparison" || scene.phase === "revision") &&
        scene.intervention_action_id !== null && (
          <VStack width="100%">
            <VStack gap={3}>
              <HStack hAlign="between" vAlign="center" wrap="wrap">
                <VStack gap={0.5}>
                  <Text type="supporting">Result after the change</Text>
                  <Text>{scene.resources.result}</Text>
                </VStack>
                <Token label="Intervention" color="teal" size="sm" />
              </HStack>
              <SceneRecordsTable records={scene.intervention.result_records} label="Teaching-model result after everyone carries an umbrella" />
              <Text type="supporting">
                All arrival records remain: {scene.observed_records.reduce((total, record) => total + record.arrivals, 0)} before → {scene.intervention.result_records.reduce((total, record) => total + record.arrivals, 0)} after. This is not a filter of the original umbrella carriers.
              </Text>
            </VStack>
          </VStack>
        )}

      {scene.phase === "comparison" && (
        <VStack padding={4} style={{background:"var(--color-background-muted)", borderRadius:"var(--radius-container)"}}>
          <VStack gap={4}>
            <VStack gap={1}>
              <Text type="supporting">Revise your account</Text>
              <Text>{scene.resources.reflection}</Text>
              <Text weight="semibold">
                Your recorded prediction: {scene.predictions.find(
                  (option) => option.prediction_id === scene.prediction_id,
                )?.label ?? "Not recorded"}
              </Text>
            </VStack>
            <SceneModelGraph scene={scene} edges={edges} onChange={setEdges} isDisabled={isWorking} />
            <CheckboxList
              label="Revise the arrows in your causal model"
              value={edges}
              onChange={setEdges}
              isDisabled={isWorking}
              hasDividers
              width="100%"
            >
              {scene.permitted_edges.map((edge) => (
                <CheckboxListItem
                  key={edgeKey(edge)}
                  value={edgeKey(edge)}
                  label={`${nodeLabel(edge.parent_id)} → ${nodeLabel(edge.child_id)}`}
                  isDisabled={!edges.includes(edgeKey(edge)) && hasReverse(edge)}
                />
              ))}
            </CheckboxList>
            <TextArea
              label="What did you learn from the comparison?"
              description="You can keep your explanation if it still fits. Say why, or describe what you changed."
              value={reflection}
              onChange={setReflection}
              rows={3}
              maxLength={800}
              isDisabled={isWorking}
              width="100%"
            />
            <HStack gap={2} wrap="wrap">
              <Button label="Keep my explanation" variant="secondary" isDisabled={isWorking}
                tooltip="Fill a starter for your note. Add your reason before recording it. Your arrows are not changed."
                onClick={() => setReflection(keepExplanationStarter)} />
              <Button
                label="Record my explanation"
                variant="primary"
                isDisabled={isWorking || selectedEdges.length === 0 || reflection.trim() === "" || reflection.trim() === keepExplanationStarter.trim()}
                onClick={() =>
                  submit({
                    kind: "submit_revision",
                    edges: selectedEdges,
                    reflection: reflection.trim() || undefined,
                  })
                }
              />
            </HStack>
          </VStack>
        </VStack>
      )}

      {scene.phase === "revision" && (
        <VStack padding={4} style={{background:"var(--color-background-muted)", borderRadius:"var(--radius-container)"}}>
          <VStack gap={3}>
            <Heading level={2}>Check your graph</Heading>
            <Text>{scene.resources.direct_explanation}</Text>
            <SceneModelGraph scene={scene} edges={edges}
              onChange={scene.evidence_status === "rejected" ? setEdges : undefined} isDisabled={isWorking} />
            {canContinue ? (
              <CommitBar isWorking={isWorking} onContinue={onContinue} scene />
            ) : scene.evidence_status === "rejected" ? (
              <VStack gap={4}>
                <Banner status="error" title="The arrows do not match yet"
                  description="Compare your arrows with the supplied assumptions, then update your graph and try again." />
                <CheckboxList
                  label="Revise the arrows in your causal model"
                  value={edges}
                  onChange={setEdges}
                  isDisabled={isWorking}
                  hasDividers
                  width="100%"
                >
                  {scene.permitted_edges.map((edge) => (
                    <CheckboxListItem
                      key={edgeKey(edge)}
                      value={edgeKey(edge)}
                      label={`${nodeLabel(edge.parent_id)} → ${nodeLabel(edge.child_id)}`}
                      isDisabled={!edges.includes(edgeKey(edge)) && hasReverse(edge)}
                    />
                  ))}
                </CheckboxList>
                <Button
                  label="Save revised graph"
                  variant="primary"
                  isDisabled={isWorking || selectedEdges.length === 0}
                  onClick={() =>
                    submit({
                      kind: "submit_revision",
                      edges: selectedEdges,
                      reflection: reflection.trim() || undefined,
                    })
                  }
                />
              </VStack>
            ) : (
              <VStack gap={2}>
                <Button
                  label="Check my graph"
                  variant="primary"
                  isDisabled={isWorking}
                  onClick={onSubmitEvidence}
                />
              </VStack>
            )}
          </VStack>
        </VStack>
      )}

      <Collapsible defaultIsOpen={false} trigger={<Text type="supporting">About this exercise</Text>}>
        <Text>This exercise uses a fixed teaching model. The displayed result is authored in advance, not recalculated from your arrows. The graph check compares your arrows with the supplied assumptions. Your first prediction and explanation are not scored, and one test does not establish a unique real-world graph.</Text>
      </Collapsible>
    </VStack>
  );
}

function DynamicUmbrellaWorkbench({scene, simulation, isWorking, canContinue, onShareHypothesis,
  onSceneAction, onSubmitEvidence, onContinue}: {
  scene:CausalScene; simulation:UmbrellaSimulation; isWorking:boolean; canContinue:boolean;
  onShareHypothesis:(text:string)=>Promise<boolean>;
  onSceneAction:(action:Record<string,unknown>)=>void;
  onSubmitEvidence:()=>void; onContinue:()=>void;
}) {
  const [hypothesisId, setHypothesisId] = useState(simulation.selected_hypothesis_id ?? "");
  const [prediction, setPrediction] = useState(scene.prediction_id ?? "");
  const [edges, setEdges] = useState(scene.graph_edges.map(edgeKey));
  const [reflection, setReflection] = useState(scene.reflection ?? "");
  const [idea, setIdea] = useState("");
  const savedEdgesKey = scene.graph_edges.map(edgeKey).join("|");
  useEffect(() => {
    setHypothesisId(simulation.selected_hypothesis_id ?? "");
    setPrediction(scene.prediction_id ?? "");
    setEdges(scene.graph_edges.map(edgeKey));
    setReflection(scene.reflection ?? "");
  }, [scene.revision, simulation.selected_hypothesis_id, scene.prediction_id, savedEdgesKey, scene.reflection]);

  const legal = (kind:string) => scene.legal_action_kinds.includes(kind);
  const selected = simulation.hypotheses.find(item => item.hypothesis_id === simulation.selected_hypothesis_id);
  const changedHypothesis = hypothesisId !== (simulation.selected_hypothesis_id ?? "");
  const latestRun = simulation.runs.at(-1);
  const predictionLabel = (id:string|null) => scene.predictions.find(item => item.prediction_id === id)?.label ?? "Not recorded";
  const nodeLabel = (id:string) => scene.nodes.find(node => node.node_id === id)?.label ?? labelFromConceptId(id);
  const selectedEdges = scene.permitted_edges.filter(edge => edges.includes(edgeKey(edge)));
  const percent = (value:number) => `${value.toLocaleString("en-GB", {maximumFractionDigits:1})}%`;
  const savedReflection = reflection.trim() || scene.reflection?.trim() || "";
  const observedRecords = <VStack gap={3}>
    <Heading level={2}>Start with the observed records</Heading>
    <Text>{scene.resources.records}</Text>
    <SceneRecordsTable records={scene.observed_records} label="Observed umbrella and pavement data" />
    <Text type="supporting">These records come from the reference world. They do not by themselves select a causal explanation.</Text>
  </VStack>;
  const chooser = legal("select_hypothesis") && <VStack gap={3}>
    <RadioList label="Choose a hypothesis to test" value={hypothesisId} onChange={setHypothesisId}
      description="Each explanation has explicit rules. Selecting it does not make it true."
      isDisabled={isWorking} htmlName={`scene.${scene.scene_id}.hypothesis`} width="100%">
      {simulation.hypotheses.map(item => <RadioListItem key={item.hypothesis_id} value={item.hypothesis_id}
        label={item.label} description={item.mechanism} />)}
    </RadioList>
    <HStack><Button label="Save hypothesis" variant={scene.phase === "records" ? "primary" : "secondary"}
      isDisabled={isWorking || hypothesisId === ""}
      onClick={() => onSceneAction({kind:"select_hypothesis", hypothesis_id:hypothesisId})} /></HStack>
    {changedHypothesis && <Text type="supporting">Save this choice before recording a prediction. Earlier runs stay available.</Text>}
  </VStack>;
  const referenceEditor = <VStack gap={3}>
    <SceneModelGraph scene={scene} edges={edges} title="Your reconstruction of the reference world"
      onChange={setEdges} isDisabled={isWorking} />
    <CheckboxList label="Represent the supplied reference-world assumptions" value={edges} onChange={setEdges}
      isDisabled={isWorking} hasDividers width="100%">
      {scene.permitted_edges.map(edge => <CheckboxListItem key={edgeKey(edge)} value={edgeKey(edge)}
        label={`${nodeLabel(edge.parent_id)} → ${nodeLabel(edge.child_id)}`}
        isDisabled={!edges.includes(edgeKey(edge)) && edges.includes(`${edge.child_id}->${edge.parent_id}`)} />)}
    </CheckboxList>
  </VStack>;
  const latestComparison = latestRun && <VStack gap={4}>
    <VStack gap={1}>
      <Heading level={2}>Compare the two results</Heading>
      <Text>Run {latestRun.run_id} · {latestRun.hypothesis_label}</Text>
      <Text>Your recorded prediction: {predictionLabel(latestRun.prediction_id)}</Text>
    </VStack>
    <Grid columns={{minWidth:280, max:2, repeat:"fit"}} gap={5} align="start">
      <VStack gap={2} style={{minWidth:0}}>
        <Heading level={3}>Your hypothesis model</Heading>
        <Text>{latestRun.hypothesis_label} · Wet pavement: {percent(latestRun.hypothesis_wet_pct)}</Text>
        <SceneRecordsTable records={latestRun.hypothesis_result_records} label="Calculated result from your hypothesis model" />
      </VStack>
      <VStack gap={2} style={{minWidth:0}}>
        <Heading level={3}>Independent reference world</Heading>
        <Text>Unchanged across your tests · Wet pavement: {percent(latestRun.reference_wet_pct)}</Text>
        <SceneRecordsTable records={latestRun.reference_result_records} label="Calculated result from the independent reference world" />
      </VStack>
    </Grid>
    <Text>The same intervention is applied to all arrivals, not just the recorded umbrella carriers. Matching one result does not uniquely establish a real-world causal graph.</Text>
  </VStack>;

  return <VStack gap={6} width="100%" style={{minWidth:0}}>
    <Heading level={1} type="display-3" textWrap="pretty">{scene.title}</Heading>
    {scene.phase === "hook" ? <VStack gap={3}>
      <Text>{scene.resources.hook}</Text>
      <Text>You will test different explanations against one independent reference world. Your choices change the hypothesis, not that world.</Text>
      <TextArea label="Why might umbrellas and wet pavement occur together?" value={idea} onChange={setIdea}
        description="Share an idea with the tutor, or open the data first." rows={3} maxLength={800}
        isDisabled={isWorking} width="100%" />
      <HStack gap={2} wrap="wrap">
        <Button label="Discuss my idea with EducAgent" variant="secondary" isDisabled={isWorking || idea.trim() === ""}
          onClick={async () => {if (await onShareHypothesis(idea.trim())) setIdea("");}} />
        <Button label="View the data" variant="primary" isDisabled={isWorking || !legal("open_records")}
          onClick={() => onSceneAction({kind:"open_records"})} />
      </HStack>
    </VStack> : scene.phase === "records" ? observedRecords : null}

    {scene.phase !== "hook" && <Text weight="semibold" aria-live="polite">
      {simulation.distinct_hypotheses_tried} {simulation.distinct_hypotheses_tried === 1 ? "hypothesis" : "hypotheses"} tested · at least {simulation.minimum_hypotheses} required
    </Text>}
    {scene.phase === "records" && chooser}
    {(scene.phase === "model" || scene.phase === "prediction") && <VStack gap={4}>
      <VStack gap={1}>
        <Heading level={2}>Your hypothesis: {selected?.label ?? "Choose an explanation"}</Heading>
        {selected && <Text>{selected.mechanism}</Text>}
      </VStack>
      <SceneModelGraph scene={scene} edges={scene.graph_edges.map(edgeKey)} title="Hypothesis being tested" />
      {scene.phase === "model" ? <VStack gap={3}>
        <RadioList label="If everyone carried an umbrella on purpose, what do you predict?" value={prediction}
          onChange={setPrediction} isDisabled={isWorking} isRequired width="100%"
          description="Record your own guess before calculating either result. This prediction is not scored."
          htmlName={`scene.${scene.scene_id}.prediction`}>
          {scene.predictions.map(item => <RadioListItem key={item.prediction_id} value={item.prediction_id} label={item.label} />)}
        </RadioList>
        <HStack><Button label="Record my prediction" variant="primary"
          isDisabled={isWorking || prediction === "" || changedHypothesis || !legal("submit_prediction")}
          onClick={() => onSceneAction({kind:"submit_prediction", prediction_id:prediction})} /></HStack>
      </VStack> : <VStack gap={3}>
        <Text weight="semibold">Your recorded prediction: {predictionLabel(scene.prediction_id)}</Text>
        <Text>Give everyone an umbrella in both models. Each model uses its own rules to calculate what happens.</Text>
        <HStack><Button label="Run intervention" variant="primary"
          isDisabled={isWorking || changedHypothesis || !legal("run_intervention")}
          onClick={() => onSceneAction({kind:"run_intervention", intervention_action_id:scene.intervention.action_id})} /></HStack>
      </VStack>}
      <Collapsible defaultIsOpen={false} trigger={<Text>Change hypothesis</Text>}>{chooser}</Collapsible>
    </VStack>}

    {latestRun && (scene.phase === "comparison" || scene.phase === "revision" ? latestComparison
      : <Collapsible defaultIsOpen={false} trigger={<Text>Review earlier run</Text>}>{latestComparison}</Collapsible>)}

    {scene.phase === "comparison" && <VStack gap={4}>
      {!simulation.ready_for_revision && <Text>Test another hypothesis and compare its result before reconstructing the reference model.</Text>}
      {simulation.ready_for_revision
        ? <Collapsible defaultIsOpen={false} trigger={<Text>Try another hypothesis</Text>}>{chooser}</Collapsible>
        : chooser}
    </VStack>}
    {simulation.runs.length > 1 && <Collapsible defaultIsOpen={false} trigger={<Text>Run history ({simulation.runs.length})</Text>}>
      <VStack style={CONTAINED_TABLE_STYLE}>
        <Table aria-label="Saved hypothesis and reference-world comparisons" density="compact" dividers="rows"
          data={simulation.runs.map(run => ({run:run.run_id, hypothesis:run.hypothesis_label,
            predicted:predictionLabel(run.prediction_id), hypothesis_result:percent(run.hypothesis_wet_pct),
            reference_result:percent(run.reference_wet_pct)}))} idKey="run"
          columns={[
            {key:"run", header:"Run"}, {key:"hypothesis", header:"Hypothesis", width:proportional(2)},
            {key:"predicted", header:"Your prediction", width:proportional(2)},
            {key:"hypothesis_result", header:"Hypothesis wet", width:proportional(1)},
            {key:"reference_result", header:"Reference wet", width:proportional(1)},
          ]} />
      </VStack>
    </Collapsible>}

    {simulation.ready_for_revision && simulation.reference_assumptions && <VStack gap={3}>
      <Heading level={2}>The reference-world assumptions</Heading>
      <Text>{simulation.reference_assumptions}</Text>
      <Text type="supporting">These rules were supplied for this teaching world, not discovered from your selected hypothesis or one matching test.</Text>
    </VStack>}
    {scene.phase === "comparison" && simulation.ready_for_revision && legal("submit_revision") && <VStack gap={4}>
      <Heading level={2}>Explain the comparison</Heading>
      {referenceEditor}
      <TextArea label="What changed between the hypotheses, and what stayed fixed?" value={reflection} onChange={setReflection}
        description="Compare your prediction with the calculated results, then represent the supplied reference-world assumptions above. Your note is not scored."
        rows={3} maxLength={800} isDisabled={isWorking} width="100%" />
      <HStack><Button label="Record my explanation" variant="primary"
        isDisabled={isWorking || selectedEdges.length === 0 || reflection.trim() === ""}
        onClick={() => onSceneAction({kind:"submit_revision", edges:selectedEdges, reflection:reflection.trim()})} /></HStack>
    </VStack>}
    {scene.phase === "revision" && <VStack gap={4}>
      <Heading level={2}>Check your reconstruction</Heading>
      <Text>The graph check asks whether you can represent the supplied reference-world assumptions. It does not grade your first hypothesis or prediction.</Text>
      {canContinue ? <>
        <SceneModelGraph scene={scene} edges={scene.graph_edges.map(edgeKey)} title="Your recorded reconstruction" />
        <CommitBar isWorking={isWorking} onContinue={onContinue} scene />
      </> : scene.evidence_status === "rejected" ? <>
        <Banner status="error" title="The arrows do not match yet"
          description="Compare the graph with the supplied reference-world assumptions, then update it and try again." />
        {referenceEditor}
        <HStack><Button label="Save revised graph" variant="primary" isDisabled={isWorking || selectedEdges.length === 0 || savedReflection === "" || !legal("submit_revision")}
          onClick={() => onSceneAction({kind:"submit_revision", edges:selectedEdges, reflection:savedReflection})} /></HStack>
      </> : <>
        <SceneModelGraph scene={scene} edges={scene.graph_edges.map(edgeKey)} title="Your recorded reconstruction" />
        <HStack><Button label="Check my graph" variant="primary" isDisabled={isWorking} onClick={onSubmitEvidence} /></HStack>
      </>}
    </VStack>}
    {scene.phase !== "hook" && scene.phase !== "records" && <Collapsible defaultIsOpen={false}
      trigger={<Text>Review observed records</Text>}>{observedRecords}</Collapsible>}
    <Collapsible defaultIsOpen={false} trigger={<Text type="supporting">About this exercise</Text>}>
      <Text>Both results are calculated by a deterministic teaching simulator. A hypothesis includes explicit causal rules, not arrows alone. Changing it never changes the independent reference world. Runs and predictions are unscored; the existing graph check remains separate. This is a synthetic exercise, not evidence about real patients or campuses.</Text>
    </Collapsible>
  </VStack>;
}

function SceneModelGraph({scene, edges, onChange, isDisabled = false, title = "Your proposed explanation"}: {
  scene:CausalScene;
  edges:string[];
  onChange?:(edges:string[])=>void;
  isDisabled?:boolean;
  title?:string;
}) {
  const positions = [{x:260,y:42}, {x:105,y:224}, {x:415,y:224}];
  const proposedNodeIds = [...new Set(scene.permitted_edges.flatMap((edge) => [edge.parent_id,edge.child_id]))];
  const nodes = [
    ...proposedNodeIds.filter((id) => !scene.nodes.some((node) => node.node_id === id))
      .map((id) => ({node_id:id, label:labelFromConceptId(id), initially_visible:false})),
    ...scene.nodes,
  ];
  const nodeLabel = (id:string) => nodes.find((node) => node.node_id === id)?.label ?? id;
  const selected = scene.permitted_edges.filter((edge) => edges.includes(edgeKey(edge)));
  const markerId = `model-arrow-${scene.scene_id}-${title.replace(/[^a-z0-9]/gi, "-")}`;
  return <VStack gap={2} width="100%">
    <Text weight="semibold">{title}</Text>
    {onChange && <Text type="supporting">Click an arrow to add or remove a possible influence. Solid arrows are selected. You can also use the choices below.</Text>}
    <svg viewBox="0 0 520 275" style={{width:"100%", maxHeight:300, color:"var(--color-text-primary)"}}
      role={onChange ? "group" : "img"} aria-label={`Proposed influences between ${nodes.map((node) => node.label).join(", ")}`}>
      <defs>
        <marker id={markerId} markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
          <path d="M0,0 L8,4 L0,8 Z" fill="var(--color-accent)" />
        </marker>
        <marker id={`${markerId}-option`} markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
          <path d="M0,0 L8,4 L0,8 Z" fill="var(--color-text-secondary)" />
        </marker>
      </defs>
      {scene.permitted_edges.map((edge) => {
        const parent = positions[nodes.findIndex((node) => node.node_id === edge.parent_id)];
        const child = positions[nodes.findIndex((node) => node.node_id === edge.child_id)];
        if (!parent || !child) return null;
        const key = edgeKey(edge);
        const active = edges.includes(key);
        if (!onChange && !active) return null;
        const blocked = isDisabled || !active && edges.includes(`${edge.child_id}->${edge.parent_id}`);
        const dx = child.x-parent.x, dy = child.y-parent.y;
        const length = Math.hypot(dx,dy);
        const inset = Math.min(86/Math.abs(dx), 25/Math.abs(dy));
        const offsetX = -dy/length*7, offsetY = dx/length*7;
        const x1 = parent.x+dx*inset+offsetX, y1 = parent.y+dy*inset+offsetY;
        const x2 = child.x-dx*inset+offsetX, y2 = child.y-dy*inset+offsetY;
        const label = `${nodeLabel(edge.parent_id)} may influence ${nodeLabel(edge.child_id)}`;
        const toggle = () => {
          if (!onChange || blocked) return;
          onChange(active ? edges.filter((value) => value !== key) : [...edges,key]);
        };
        return <g key={key} role={onChange ? "button" : undefined} tabIndex={onChange && !blocked ? 0 : undefined}
          aria-label={onChange ? `${active ? "Remove" : "Add"}: ${label}` : undefined}
          aria-pressed={onChange ? active : undefined} aria-disabled={onChange ? blocked : undefined}
          onClick={toggle} onKeyDown={(event) => {if (event.key === "Enter" || event.key === " ") {event.preventDefault(); toggle();}}}
          style={{cursor:onChange && !blocked ? "pointer" : "default", opacity:blocked && !active ? 0.35 : 1}}>
          <title>{label}</title>
          <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="transparent" strokeWidth="24" />
          <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={active ? "var(--color-accent)" : "var(--color-text-secondary)"}
            strokeWidth={active ? 3 : 1.5} strokeDasharray={active ? undefined : "6 5"}
            markerEnd={`url(#${markerId}${active ? "" : "-option"})`} />
        </g>;
      })}
      {nodes.map((node,index) => {
        const position = positions[index];
        if (!position) return null;
        const words = node.label.split(" ");
        const splitAt = words.length > 2 ? Math.ceil(words.length/2) : words.length;
        return <g key={node.node_id}>
          <rect x={position.x-86} y={position.y-25} width="172" height="50" rx="10"
            fill="var(--color-background-surface)" stroke="var(--color-border-emphasized)" />
          <text x={position.x} y={position.y+(splitAt < words.length ? -3 : 5)} textAnchor="middle"
            fontSize="15" fill="currentColor" fontFamily="var(--font-family-body)">
            <tspan x={position.x}>{words.slice(0,splitAt).join(" ")}</tspan>
            {splitAt < words.length && <tspan x={position.x} dy="19">{words.slice(splitAt).join(" ")}</tspan>}
          </text>
        </g>;
      })}
    </svg>
    <Text type="supporting" aria-live="polite">{selected.length === 0 ? "No influences selected yet." : selected.map((edge) => `${nodeLabel(edge.parent_id)} → ${nodeLabel(edge.child_id)}`).join("; ")}</Text>
  </VStack>;
}

function SceneRecordsTable({ records, label }: { records: SceneRecord[]; label: string }) {
  return (
    <VStack gap={2} width="100%" style={CONTAINED_TABLE_STYLE}>
    <Table
      aria-label={label}
      data={records}
      idKey={(record) => `${record.umbrella_carried}.${record.pavement_wet}`}
      density="compact"
      dividers="rows"
      isStriped
      columns={[
        { key: "umbrella_carried", header: "Umbrella carried", width: proportional(1) },
        { key: "pavement_wet", header: "Pavement wet", width: proportional(1) },
        { key: "arrivals", header: "Arrival records", width: proportional(1) },
      ]}
    />
    <Text type="supporting">Total: {records.reduce((total, record) => total + record.arrivals, 0)} arrival records.</Text>
    </VStack>
  );
}

function edgeKey(edge: SceneEdge): string {
  return `${edge.parent_id}->${edge.child_id}`;
}

function InvestigationCanvas({
  image,
  recordText,
  workbench,
  experiment,
  deferQuestion = false,
  conceptId,
  concepts,
  commitment,
}: {
  image: ScenarioImage | null;
  recordText: string;
  workbench?: ComparisonWorkbench | null;
  experiment?: ReactNode;
  deferQuestion?: boolean;
  conceptId: string | null;
  concepts: ModuleConcept[];
  commitment?: ReactNode;
}) {
  const conceptLabel =
    concepts.find((concept) => concept.id === conceptId)?.label ??
    "Causal investigation";
  // Experiments keep the full canvas; question pages keep a reading measure.
  const scenarioCard = !experiment && !!image && !!workbench;
  return (
    <VStack gap={4} width="100%" maxWidth={experiment ? undefined : scenarioCard ? SCENARIO_WIDTH : READING_WIDTH}>
      <VStack gap={2} width="100%">
        <Text type="supporting">{workbench?.title ?? conceptLabel}</Text>
        {!deferQuestion && <QuestionPrompt text={recordText} image={image} workbench={experiment ? null : workbench} />}
      </VStack>

      {experiment}

      {deferQuestion && commitment !== undefined && <QuestionPrompt text={recordText} image={image} workbench={null} headingLevel={2} />}

      {commitment !== undefined && (
        <Card variant="transparent" padding={0} width="100%">
          <VStack gap={3} maxWidth={experiment ? undefined : READING_WIDTH}>{commitment}</VStack>
        </Card>
      )}
    </VStack>
  );
}

function MessageTurn({
  message,
  concepts,
}: {
  message: Message;
  concepts: ModuleConcept[];
}) {
  const tutor = message.role === "tutor";
  const roles = readExampleRoles(message.example_roles);
  if (!tutor) {
    return (
      <div
        style={{
          alignSelf: "flex-end",
          maxWidth: "380px",
          padding: "12px 16px",
          borderRadius: "18px 18px 6px 18px",
          background: "#F2F2F1",
        }}
      >
        <Text style={{ lineHeight: 1.55 }}>{message.text}</Text>
      </div>
    );
  }
  return (
    <div style={{ display: "flex", gap: "12px", alignItems: "flex-start" }}>
      <img
        src={EDUCAGENT_AVATAR_SRC}
        alt=""
        style={{
          flex: "none",
          width: "28px",
          height: "28px",
          borderRadius: "9999px",
          objectFit: "cover",
          border: "1px solid #E5E5E5",
        }}
      />
      <div style={{ display: "flex", flexDirection: "column", gap: "10px", minWidth: 0 }}>
        <div style={{ fontSize: "var(--text-body-size)", lineHeight: 1.65 }}>
          <RichText text={message.text} />
        </div>
        {roles && <ExampleRolesLegend roles={roles} />}
        {message.kind === "direct_instruction" &&
          message.references !== undefined &&
          message.references.length > 0 && (
          <TutorReferences
            conceptId={message.concept_id}
            concepts={concepts}
            references={message.references}
          />
        )}
      </div>
    </div>
  );
}
function readExampleRoles(value:unknown):ExampleRoles|null {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  const record = value as Record<string,unknown>;
  return ["treatment", "outcome", "common_cause", "target_population"].every(
    (key) => typeof record[key] === "string" && record[key].trim() !== "",
  ) ? value as ExampleRoles : null;
}
function ExampleRolesLegend({roles}:{roles:ExampleRoles}) {
  return <Collapsible defaultIsOpen trigger={<Text type="supporting" weight="medium">In this hypothetical example</Text>}>
    <VStack gap={1} role="note" aria-label="Variables in this example" style={{minWidth:0, overflowWrap:"anywhere"}}>
      <Text type="supporting">Action: {roles.treatment}</Text>
      <Text type="supporting">Outcome: {roles.outcome}</Text>
      <Text type="supporting">Shared cause before the action: {roles.common_cause}</Text>
      <Text type="supporting">Target group: {roles.target_population}</Text>
    </VStack>
  </Collapsible>;
}
function tutorMarkdown(text: string): string {
  // Present old verified replies as Markdown without changing saved events.
  if (!text.startsWith("Textbook quotation (mathematical notation transcribed):\n\n")
      && !text.startsWith("Textbook excerpt: ")) return text;
  return text.replace(/^(Textbook quotation \(mathematical notation transcribed\):\n\n)("[^\n]+")/,
    "$1> $2").replace(/^Textbook excerpt: ("[^\n]+"\.)/, "Textbook excerpt:\n\n> $1")
    .replace(/(?<!\()https:\/\/mitpress\.mit\.edu\/9780262037310\/elements-of-causal-inference\//g,
      "[Publisher source](https://mitpress.mit.edu/9780262037310/elements-of-causal-inference/)");
}
function RichText({ text }: { text: string }) {
  return (
    <VStack gap={1} style={{minWidth:0, maxWidth:"100%", overflowWrap:"anywhere"}}>
      <ReactMarkdown skipHtml remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}
        components={{
          blockquote: ({children}) => <VStack as="blockquote" gap={2} padding={3}
            style={{margin:0, minWidth:0, borderInlineStart:"var(--spacing-1) solid var(--color-border)",
              background:"var(--color-background-muted)"}}>{children}</VStack>,
          img: () => null,
        }}>
        {tutorMarkdown(text)}
      </ReactMarkdown>
    </VStack>
  );
}
function TutorReferences({
  conceptId,
  concepts,
  references,
}: {
  conceptId?: string;
  concepts: ModuleConcept[];
  references: TutorReference[];
}) {
  const conceptLabel =
    concepts.find((concept) => concept.id === conceptId)?.label ??
    "Current concept";
  return (
    <div
      style={{
        borderLeft: "2px solid #005348",
        background: "#FCFCFB",
        padding: "10px 14px",
        display: "flex",
        flexDirection: "column",
        gap: "4px",
      }}
    >
      <Eyebrow>{conceptLabel}</Eyebrow>
      {references.map((reference) => (
        <div key={`${reference.claim_id}:${reference.locator}`} style={{ display: "flex", flexDirection: "column" }}>
          <Text style={{ fontSize: "14px", lineHeight: 1.5 }}>{reference.proposition}</Text>
          <Text type="supporting">
            {reference.citation} · {reference.locator}
          </Text>
        </div>
      ))}
    </div>
  );
}
function CommitBar({
  isWorking,
  onContinue,
  scene = false,
}: {
  isWorking: boolean;
  onContinue: () => void;
  scene?: boolean;
}) {
  // Plain, left-aligned with the question: no tinted box around the result.
  return (
    <VStack gap={3}>
      <HStack gap={2} vAlign="center">
        <StatusDot variant="success" label="Activity check passed" />
        <Text weight="semibold">{scene ? "Model matches the supplied assumptions" : "Correct"}</Text>
      </HStack>
      <Text>
        {scene && "The graph check passed. Your prediction and reflection are recorded but unscored. "}
        Continue when you’re ready.
      </Text>
      <HStack>
        <Button
          label="Continue"
          variant="primary"
          size="lg"
          isDisabled={isWorking}
          onClick={onContinue}
          />
      </HStack>
    </VStack>
  );
}
function TutorPanel({
  showBackToActivity = false,
  messageDraft,
  onMessageDraftChange,
  routeComplete = false,
  messages,
  isWorking,
  concepts,
  completed,
  topicCompleted = [],
  finalCheck,
  started,
  current,
  diagnosticStatuses,
  canExplain,
  canSend,
  onExplain,
  onNavigate,
  onFinalCheck,
  onSend,
}: {
  showBackToActivity?: boolean;
  messageDraft: string;
  onMessageDraftChange: (value:string) => void;
  routeComplete?: boolean;
  messages: Message[];
  isWorking: boolean;
  tutorDirection: string | null;
  conceptId: string | null;
  concepts: ModuleConcept[];
  completed: string[];
  topicCompleted?: string[];
  finalCheck?: FinalCheck | null;
  started: string[];
  current: string | null;
  diagnosticStatuses: DiagnosticConceptResult[];
  canExplain: boolean;
  canSend: boolean;
  onExplain: () => void;
  onNavigate: (conceptId: string) => void;
  onFinalCheck?: () => void;
  onSend: (value: string) => Promise<boolean>;
}) {
  const isWide = useMediaQuery(WIDE_WORKSPACE_QUERY);
  const transcriptRef = useRef<HTMLDivElement>(null);
  const topicsRef = useRef<HTMLDivElement>(null);
  useLayoutEffect(() => {
    if (!isWide || !finalCheck?.is_current) return;
    const tools = topicsRef.current;
    const finalRow = tools?.querySelector("li:last-child");
    if (tools && finalRow && finalRow.getClientRects().length > 0) {
      tools.scrollTo({top:tools.scrollTop + Math.max(0,
        finalRow.getBoundingClientRect().bottom - tools.getBoundingClientRect().bottom)});
    }
  }, [isWide, finalCheck?.is_current, finalCheck?.completed_count]);
  useEffect(() => {
    const transcript = transcriptRef.current;
    transcript?.scrollTo({
      top: transcript.scrollHeight,
      behavior: "smooth",
    });
  }, [isWorking, messages.length]);
  return (
    <VStack id="educagent-tutor" role="region" aria-label="EducAgent tutor" tabIndex={-1}
      height={isWide ? "100%" : "min(44rem, 75dvh)"}
      style={{...SCRIPT_FOCUS_STYLE, minHeight:0, minWidth:0, overflow:"hidden", flexShrink:0}}>
      <HStack gap={3} padding={4} vAlign="center"
        style={{
          borderBottom: "var(--border-width) solid var(--color-border)", flexShrink:0,
        }}
      >
        <TutorAvatar />
        <VStack gap={0.5} style={{minWidth:0}}>
          <Text weight="semibold">
            EducAgent
          </Text>
          <Text type="supporting">
            {routeComplete ? "Choose a topic below to review with me."
              : "Ask me to explain a term or talk through an example."}
          </Text>
        </VStack>
      </HStack>
      <VStack gap={5} padding={4} isScrollable role="log" tabIndex={0}
        aria-relevant="additions" aria-atomic={false}
        ref={transcriptRef}
        style={{
          flex: 1,
          minHeight: 0,
          scrollbarGutter:"stable",
        }}
        aria-label="Tutor conversation"
      >
        {routeComplete && <VStack gap={3}>
          <Text>You’ve finished this route. We can revisit an explanation, try an example, or talk through a question together.</Text>
          <Text weight="semibold">Choose a topic to review</Text>
          <RouteList concepts={concepts} completed={completed} topicCompleted={topicCompleted}
            finalCheck={finalCheck} onFinalCheck={onFinalCheck}
            started={started} isDisabled={isWorking} onNavigate={onNavigate} />
        </VStack>}
        {isWorking && (
          <HStack gap={2} vAlign="center">
            <StatusDot variant="accent" label="Request in progress" isPulsing />
            <Text type="supporting">Updating your session…</Text>
          </HStack>
        )}
        {messages.map((message, index) => (
          <MessageTurn
            key={`dialogue.${message.activity_id}.${index}`}
            message={message}
            concepts={concepts}
          />
        ))}
      </VStack>
      <VStack gap={3} padding={4}
        style={{
          borderTop: "var(--border-width) solid var(--color-border)", flexShrink:0, maxHeight:"65%",
        }}
      >
        {/* The composer stays in place; only the concept tools and topic list scroll. */}
        {showBackToActivity && <Button label="Back to activity" variant="ghost" size="sm" href="#learning-activity" />}
        {!routeComplete && <PlainComposer value={messageDraft} onChange={onMessageDraftChange}
          onSubmit={onSend} isDisabled={isWorking || !canSend} />}
        <VStack ref={topicsRef} gap={3} isScrollable aria-label="Concept tools and topics"
          style={{flex:"1 1 auto", minHeight:0, scrollbarGutter:"stable"}}>
          {canExplain && (
            <HStack gap={2} vAlign="center" wrap="wrap">
              <Button
                label="Explain this concept"
                variant="ghost"
                size="sm"
                isDisabled={isWorking}
                onClick={onExplain}
              />
            </HStack>
          )}
          {!routeComplete && <Collapsible defaultIsOpen={isWide}
            trigger={<Text type="supporting">Topics completed · {topicCompleted.length} of {concepts.length}</Text>}>
            <Text type="supporting">This records topic practice. The final assessment and full course are separate.</Text>
            <RouteList
              concepts={concepts}
              completed={completed}
              topicCompleted={topicCompleted}
              finalCheck={finalCheck}
              started={started}
              current={current}
              diagnosticStatuses={diagnosticStatuses}
              isDisabled={isWorking}
              onNavigate={onNavigate}
              onFinalCheck={onFinalCheck}
            />
          </Collapsible>}
          <Text type="supporting"><a href="/sources.html">Sources &amp; rights</a></Text>
        </VStack>
      </VStack>
    </VStack>
  );
}
function PlainComposer({
  value,
  onChange,
  onSubmit,
  isDisabled,
}: {
  value: string;
  onChange: (value:string) => void;
  onSubmit: (value: string) => Promise<boolean>;
  isDisabled: boolean;
}) {
  // Match LearnerMessageText's existing code-point bound, not a turn quota.
  const length = Array.from(value.trim()).length;
  const tooLong = length > 1000;
  const submit = async () => {
    const trimmed = value.trim();
    if (trimmed === "" || isDisabled || tooLong) return;
    // A rejected/stale request was not recorded; keep its editable draft.
    if (await onSubmit(trimmed)) onChange("");
  };
  return (
    <VStack gap={2} width="100%" style={{minWidth:0}}>
      <TextArea label="Message EducAgent" isLabelHidden
        value={value}
        onChange={onChange}
        onKeyDown={(event) => {
          if (event.nativeEvent.isComposing || event.keyCode === 229) return;
          if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            return submit();
          }
        }}
        placeholder="Ask EducAgent…"
        isDisabled={isDisabled}
        rows={2}
        width="100%"
        status={tooLong ? {type:"error",message:"Please shorten this message to 1,000 characters. Your text is kept."} : undefined}
        statusVariant="detached"
      />
      <HStack gap={2} hAlign="between" vAlign="center" wrap="wrap">
        <Text type="supporting">Enter to send · Shift+Enter for a new line. {length}/1,000</Text>
        <Button label="Send" size="sm" variant="secondary" onClick={submit}
          isDisabled={isDisabled || value.trim() === "" || tooLong} />
      </HStack>
    </VStack>
  );
}
function AnswerCommitment({
  activityKey,
  choices,
  isWorking,
  onCommit,
}: {
  activityKey: string;
  choices: Choice[];
  isWorking: boolean;
  onCommit: (optionId: string) => void;
}) {
  const [selected, setSelected] = useState("");
  useEffect(() => setSelected(""), [activityKey]);
  return (
    <VStack gap={3}>
      <RadioList
        label="Choose one, then submit."
        value={selected}
        onChange={setSelected}
        isDisabled={isWorking}
        isRequired
        htmlName={`answer.${activityKey}`}
        width="100%"
      >
        {choices.map((choice) => (
          <RadioListItem
            key={choice.option_id}
            label={choice.text}
            value={choice.option_id}
          />
        ))}
      </RadioList>
      <HStack
        hAlign="between"
        vAlign="center"
        wrap="wrap"
        gap={2}
      >
        <Text type="supporting">
          You can revise your choice before submitting.
        </Text>
        <Button
          label="Submit"
          variant="primary"
          isDisabled={isWorking || selected === ""}
          onClick={() => onCommit(selected)}
        />
      </HStack>
    </VStack>
  );
}
function EntryRouteRail({
  state,
  isWorking,
  onSelectModule,
}: {
  state: DemoState;
  isWorking: boolean;
  onSelectModule: (moduleId: string) => void;
}) {
  const diagnostic = state.diagnostic;
  const quizInProgress = diagnostic?.status === "in_progress";
  const concepts = moduleConcepts(state);
  return (
    <VStack gap={6}>
      {/* The quiz picture is shown under its question, not repeated here. */}
      <HStack gap={3} vAlign="center">
        <TutorAvatar />
        <VStack gap={0}>
          <Text weight="semibold">EducAgent</Text>
          <Text type="supporting">Causal tutor</Text>
        </VStack>
      </HStack>
      <Divider />
      <VStack gap={2}>
        <Eyebrow>{quizInProgress ? "Quiz topics" : diagnostic ? "Foundations topics" : `${state.course_title ?? state.title} topics`}</Eyebrow>
        <RouteList
          concepts={concepts}
          completed={conceptsWithRouteCredit(state)}
          topicCompleted={state.topic_practice_completed_concept_ids ?? []}
          finalCheck={quizInProgress || state.preview_mode || state.lesson_is_sample ? null : state.final_check}
          started={conceptsWithPractice(state)}
          diagnosticStatuses={diagnostic?.concept_results ?? []}
          quizMode={!!quizInProgress}
          current={quizInProgress ? concepts[Math.min(diagnostic.answered_count, concepts.length - 1)]?.id : null}
        />
      </VStack>
      {state.modules.length > 1 && (
        <>
          <Divider />
          <VStack gap={2}>
            <Eyebrow>Also available</Eyebrow>
            <Text type="supporting">You can start either course at any time.</Text>
            <VStack gap={2}>
              {state.modules.filter((module) => module.module_id !== state.active_module_id).map((module) => {
                const isLocked = module.status === "locked";
                const actionLabel = module.status === "completed" ? "Review" : isLocked ? "Locked" : "Start";
                return (
                  <Grid key={module.module_id} gap={3} align="center" width="100%"
                    style={{gridTemplateColumns:"minmax(0, 1fr) auto"}}>
                    <VStack gap={0} style={{minWidth:0}}>
                      <Text weight="semibold">{module.title}</Text>
                      {isLocked && <Text type="supporting">Complete the foundation first</Text>}
                    </VStack>
                    <Button label={actionLabel} aria-label={`${actionLabel} ${module.title}`}
                      variant="secondary" size="sm" isDisabled={isWorking || isLocked}
                      onClick={() => onSelectModule(module.module_id)} />
                  </Grid>
                );
              })}
            </VStack>
          </VStack>
        </>
      )}
    </VStack>
  );
}
function ContextRail({
  state,
  isWorking,
  onNavigate,
  onFinalCheck,
}: {
  state: DemoState;
  isWorking: boolean;
  onNavigate: (conceptId: string) => void;
  onFinalCheck?: () => void;
}) {
  const complete = state.status === "completed";
  const concepts = moduleConcepts(state);
  return (
    <VStack gap={5}>
      {!complete &&
        state.scenario_image !== null &&
        state.scenario_image !== undefined && (
          <VStack gap={2}>
            <Text type="supporting">
              Scenario context
            </Text>
            <ScenarioPlate image={state.scenario_image} />
          </VStack>
        )}
      {!complete && <Divider />}
      <VStack gap={2}>
        <Text type="supporting">
          {complete ? "Route record" : `${state.title} route`}
        </Text>
        <RouteList
          concepts={concepts}
          completed={conceptsWithRouteCredit(state)}
          topicCompleted={state.topic_practice_completed_concept_ids ?? []}
          finalCheck={state.preview_mode || state.lesson_is_sample ? null : state.final_check}
          started={conceptsWithPractice(state)}
          current={state.activity_concept_id ?? conceptForActivity(state.activity_id, concepts)}
          completeMarker={complete}
          diagnosticStatuses={state.diagnostic?.concept_results ?? []}
          isDisabled={isWorking || complete}
          onNavigate={onNavigate}
          onFinalCheck={onFinalCheck}
        />
      </VStack>
    </VStack>
  );
}
function RouteList({
  concepts = M0_CONCEPT_LIST,
  completed = [],
  topicCompleted = [],
  finalCheck,
  started = [],
  current,
  showStatus = true,
  completeMarker = false,
  quizMode = false,
  diagnosticStatuses = [],
  isDisabled = false,
  onNavigate,
  onFinalCheck,
}: {
  concepts?: ModuleConcept[];
  completed?: string[];
  topicCompleted?: string[];
  finalCheck?: FinalCheck | null;
  started?: string[];
  current?: string | null;
  showStatus?: boolean;
  completeMarker?: boolean;
  quizMode?: boolean;
  diagnosticStatuses?: DiagnosticConceptResult[];
  isDisabled?: boolean;
  onNavigate?: (conceptId: string) => void;
  onFinalCheck?: () => void;
}) {
  const done = new Set(completed);
  const topicDone = new Set(topicCompleted);
  const inProgress = new Set(started);
  const diagnostic = new Map(
    diagnosticStatuses.map((result) => [result.concept_id, result.status]),
  );
  const selectedConcept = finalCheck?.is_current ? null : current;
  const status = (conceptId: string) => {
    const diagnosticStatus = diagnostic.get(conceptId);
    if (quizMode) {
      if (selectedConcept === conceptId)
        return { symbol: null, label: "Current" };
      if (done.has(conceptId) || diagnosticStatus === "correct" || diagnosticStatus === "incorrect")
        return { symbol: null, label: "Answered" };
      return { symbol: null, label: "Later" };
    }
    if (done.has(conceptId) || topicDone.has(conceptId))
      return { symbol: "✓", label: "Completed" };
    if (selectedConcept === conceptId)
      return { symbol: "?", label: "Learning" };
    if (inProgress.has(conceptId))
      return { symbol: null, label: "In progress" };
    if (diagnosticStatus === "correct")
      return { symbol: null, label: "Entry check correct" };
    if (diagnosticStatus === "incorrect")
      return { symbol: "×", label: "Needs review" };
    if (diagnosticStatus === "current")
      return { symbol: null, label: "Entry check incomplete" };
    return { symbol: null, label: "Later" };
  };
  return (
    <List density="compact" hasDividers>
      {concepts.map((concept) => {
        const itemStatus = status(concept.id);
        return (
          <ListItem
            key={concept.id}
            label={concept.label}
            isSelected={selectedConcept === concept.id}
            isDisabled={isDisabled}
            onClick={onNavigate ? () => onNavigate(concept.id) : undefined}
            endContent={
              showStatus || completeMarker ? (
                <HStack gap={1} vAlign="center">
                  {itemStatus.symbol !== null && (
                    <Text weight="semibold">{itemStatus.symbol}</Text>
                  )}
                  <Text type="supporting">{itemStatus.label}</Text>
                </HStack>
              ) : undefined
            }
          />
        );
      })}
      {!quizMode && finalCheck && <ListItem
        label="Final check"
        isSelected={finalCheck.is_current}
        isDisabled={isDisabled}
        onClick={onFinalCheck}
        endContent={<HStack gap={1} vAlign="center">
          {finalCheck.status === "completed" && <Text weight="semibold">✓</Text>}
          <Text type="supporting">{finalCheck.status === "completed" ? "Completed"
            : finalCheck.is_current || finalCheck.status === "in_progress" ? "In progress" : "Later"}</Text>
        </HStack>}
      />}
    </List>
  );
}
function QuestionIllustration({image}:{image:ScenarioImage | null | undefined}) {
  if (!image) return null;
  // A wide 2:1 crop fills its column; capping the width at 70vh keeps the
  // height within 35% of the window so the answers stay in view.
  return <VStack width="100%" maxWidth="70vh">
    <AspectRatio ratio={2} fit="cover">
      <img src={`/${image.path}`} alt={image.alt_text} />
    </AspectRatio>
  </VStack>;
}
function ScenarioPlate({ image }: { image: ScenarioImage | null }) {
  if (image === null) return null;
  return (
    <VStack gap={2}>
      <AspectRatio ratio={4 / 3} fit="cover">
        <img src={`/${image.path}`} alt={image.alt_text} />
      </AspectRatio>
      <Text type="supporting">
        Study the situation before making your judgment.
      </Text>
    </VStack>
  );
}
function RouteCompleteSummary({
  state,
  isReviewing,
  onReviewChange,
  isWorking,
  onSelectModule,
}: {
  state: DemoState;
  isReviewing: boolean;
  onReviewChange: (value: boolean) => void;
  isWorking: boolean;
  onSelectModule: (moduleId: string, testOnlyForceUnlock?: boolean) => void;
}) {
  const isWideReview = useMediaQuery("(min-width: 900px)");
  const concepts = moduleConcepts(state);
  const finalActivityIds = new Set(state.final_check_activity_ids ?? []);
  const finalSectionId = "$final-check";
  const sections = finalActivityIds.size > 0
    ? [...concepts, {id:finalSectionId, label:"Final check"}] : concepts;
  const sectionForMessage = (message:Message | undefined) => message === undefined ? null
    : finalActivityIds.has(message.activity_id) ? finalSectionId
    : message.concept_id ?? conceptForActivity(message.activity_id, concepts);
  const [selectedSectionId, setSelectedSectionId] = useState<string | null>(
    sectionForMessage(state.conversation?.at(-1)),
  );
  const sectionId = sections.some((section) => section.id === selectedSectionId)
    ? selectedSectionId : sections[0]?.id ?? null;
  const sectionLabel =
    sections.find((section) => section.id === sectionId)?.label ??
    "Latest accepted activity";
  const transcript = (state.conversation ?? []).filter(
    (message) => sectionForMessage(message) === sectionId,
  );
  const activeModule = state.modules.find(
    (module) => module.module_id === state.active_module_id,
  );
  const otherModules = state.modules.filter(
    (module) => module.module_id !== state.active_module_id,
  );
  return (
    <VStack gap={4} width="100%">
        {isReviewing ? (
          <HStack gap={6} vAlign="start" wrap={isWideReview ? "nowrap" : "wrap"} width="100%">
            <VStack width={isWideReview ? 240 : "100%"} padding={3}
              style={{flexShrink:0, background:"var(--color-background-muted)", borderRadius:"var(--radius-container)"}}>
              <VStack gap={1}>
                <Text type="supporting">
                  Course sections
                </Text>
                {sections.map((section) => (
                  <Button
                    key={section.id}
                    label={section.label}
                    variant={section.id === sectionId ? "secondary" : "ghost"}
                    size="sm"
                    onClick={() => setSelectedSectionId(section.id)}
                  />
                ))}
              </VStack>
            </VStack>
            <VStack gap={4} width="100%" maxWidth={980} style={{minWidth:0, flex:"1 1 auto"}}>
                <Text type="supporting">
                  {sectionId === finalSectionId ? "Course final check" : `Concept ${
                    concepts.findIndex((concept) => concept.id === sectionId) + 1
                  } of ${concepts.length}`}
                </Text>
                <Heading level={1} type="display-3">
                  {sectionLabel}
                </Heading>
                <HStack gap={2} vAlign="center">
                  <Token
                    label={transcript.length === 0 ? "No dialogue recorded" : "Dialogue recorded"}
                    color="green"
                    size="sm"
                  />
                  <Text type="supporting">
                    {transcript.length === 0
                      ? "Activity completion is recorded separately."
                      : "Saved in your course record."}
                  </Text>
                </HStack>
                <VStack gap={0} width="100%" height="min(540px, 58dvh)" minHeight={320}
                  style={{border:"var(--border-width) solid var(--color-border-emphasized)", borderRadius:"var(--radius-container)", background:"var(--color-background-muted)", overflow:"hidden"}}>
                  <HStack gap={2} padding={4} vAlign="center" style={{borderBottom:"var(--border-width) solid var(--color-border)", flexShrink:0}}>
                    <TutorAvatar />
                    <Text weight="semibold">Conversation with EducAgent</Text>
                  </HStack>
                  <VStack gap={5} padding={4} isScrollable role="log" aria-label={`${sectionLabel} dialogue transcript`}
                    style={{flex:1, minHeight:0, scrollbarGutter:"stable"}}>
                    {transcript.length === 0 ? (
                      <Text type="supporting">
                        You have no saved conversation for this section on this
                        route. Quiz results and activity completion are
                        recorded separately.
                      </Text>
                    ) : (
                      transcript.map((message, index) => (
                        <MessageTurn
                          key={`trace.${sectionId}.${index}`}
                          message={message}
                          concepts={concepts}
                        />
                      ))
                    )}
                  </VStack>
                </VStack>
                <Button
                  label="Back to completion"
                  variant="ghost"
                  onClick={() => onReviewChange(false)}
                />
            </VStack>
          </HStack>
        ) : (
          <>
            <Text type="supporting">
              Selected route complete
            </Text>
            <Heading level={1} type="display-1">
              Your selected activity route is complete.
            </Heading>
            <Text>
              {state.completed_activity_ids?.length ?? 0} {(state.completed_activity_ids?.length ?? 0) === 1 ? "activity" : "activities"} completed in
              this session. An exercise, a topic review, and the full
              course cover different amounts of material. This record does not establish
              mastery or readiness for advanced causal methods.
            </Text>
            <HStack gap={2} wrap="wrap">
              <Button
                label="Review my trace"
                variant="primary"
                size="lg"
                onClick={() => onReviewChange(true)}
              />
              {activeModule?.nirvana_task != null && (
                <a href={`/nirvana/?task=${activeModule.nirvana_task}`}>
                  <Button
                    label="Try research framing in Nirvana"
                    variant="secondary"
                    size="lg"
                  />
                </a>
              )}
            </HStack>
            {otherModules.length > 0 && (
              <VStack padding={4} style={{background:"var(--color-background-muted)", borderRadius:"var(--radius-container)"}}>
                <VStack gap={3}>
                  <Text weight="semibold">Modules</Text>
                  <Text type="supporting">
                    Explore either course in any order. You can return to this route at any time.
                  </Text>
                  <VStack gap={2}>
                    {otherModules.map((module) => {
                      const isActive = module.module_id === state.active_module_id;
                      const isLocked = module.status === "locked";
                      const actionLabel = isActive
                        ? "Current"
                        : module.status === "completed"
                          ? "Review"
                          : module.status === "available"
                            ? "Start"
                            : "Locked";
                      return (
                        <HStack
                          key={module.module_id}
                          gap={2}
                          vAlign="center"
                          hAlign="between"
                          wrap="wrap"
                        >
                          <VStack gap={0}>
                            <Text weight={isActive ? "semibold" : undefined}>
                              {module.title}
                            </Text>
                            <Text type="supporting">
                              {isLocked
                                ? "Complete the foundation first"
                                : module.status === "completed"
                                  ? "Completed"
                                  : "Available"}
                            </Text>
                          </VStack>
                          <Button
                            label={actionLabel}
                            variant={isActive ? "secondary" : "primary"}
                            size="sm"
                            isDisabled={isWorking || isActive || isLocked}
                            onClick={() => onSelectModule(module.module_id)}
                          />
                        </HStack>
                      );
                    })}
                  </VStack>
                </VStack>
              </VStack>
            )}
          </>
        )}
    </VStack>
  );
}
function ConnectionNotice({
  title = "Tutor disconnected",
  description = "We could not reach the tutor. Reconnect to continue this learning session.",
  actionLabel = "Reconnect",
  onReconnect,
}: {
  title?: string;
  description?: string;
  actionLabel?: string;
  onReconnect: () => void;
}) {
  return (
    <VStack gap={2}>
      <Banner
        status="warning"
        title={title}
        description={description}
      />
      <Button label={actionLabel} variant="secondary" onClick={onReconnect} />
    </VStack>
  );
}
function ModuleSwitcher({
  modules,
  activeModuleId,
  isWorking,
  onSelectModule,
}: {
  modules: ModuleSummary[];
  activeModuleId: string;
  isWorking: boolean;
  onSelectModule: (moduleId: string, testOnlyForceUnlock?: boolean) => void;
}) {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <Popover isOpen={isOpen} onOpenChange={setIsOpen} alignment="end" label="Switch module"
      width="min(420px, calc(100vw - var(--spacing-8)))"
      content={<VStack gap={3} padding={4}>
        <Text weight="semibold">Choose a course</Text>
        {modules.map((module) => {
          const isActive = module.module_id === activeModuleId;
          const isLocked = module.status === "locked";
          const actionLabel = isActive
            ? "Current"
            : module.status === "completed"
              ? "Review"
              : module.status === "available"
                ? "Continue"
                : "Locked";
          return (
            <HStack
              key={module.module_id}
              gap={2}
              vAlign="center"
              hAlign="between"
              wrap="wrap"
            >
              <VStack gap={1} style={{minWidth:0,flex:"1 1 24ch"}}>
                <Text weight={isActive ? "semibold" : undefined}>
                  {module.title}
                </Text>
                {module.intent && <Text type="supporting">{module.intent}</Text>}
                {isLocked && (
                  <Text type="supporting">
                    Complete the foundation first
                  </Text>
                )}
              </VStack>
              <HStack gap={2} vAlign="center" style={{flexShrink:0}}>
                <Button
                  label={actionLabel}
                  variant={isActive ? "secondary" : "ghost"}
                  size="sm"
                  isDisabled={isWorking || isActive || isLocked}
                  onClick={() => {setIsOpen(false); onSelectModule(module.module_id);}}
                />
              </HStack>
            </HStack>
          );
        })}
      </VStack>}>
      <Button label="Switch module ▾" variant="ghost" size="sm" isDisabled={isWorking} />
    </Popover>
  );
}
function WorkspaceHeader({
  label,
  tutorStatus,
  onReset,
}: {
  label: string;
  tutorStatus: DemoState["tutor_status"];
  onReset?: () => void;
}) {
  const status =
    tutorStatus === "unreachable"
      ? "warning"
      : tutorStatus === "thinking"
        ? "accent"
        : "success";
  const labelText =
    tutorStatus === "unreachable"
      ? "Tutor disconnected"
      : tutorStatus === "thinking"
        ? "Tutor thinking"
        : "Tutor ready";
  return (
    <LayoutHeader hasDivider label="EducAgent workspace">
      <HStack gap={3} padding={4} hAlign="between" vAlign="center" wrap="wrap" width="100%" style={{minWidth:0}}>
        <HStack gap={2} vAlign="center" wrap="wrap" style={{minWidth:0,maxWidth:"100%"}}>
          <Text weight="semibold">EducAgent</Text>
          <Text type="supporting">{label}</Text>
        </HStack>
        <HStack gap={2} vAlign="center" wrap="wrap" style={{minWidth:0,maxWidth:"100%",flex:"0 1 auto"}}>
          <HStack gap={1} vAlign="center">
            <StatusDot
              variant={status}
              label={labelText}
              isPulsing={tutorStatus === "thinking"}
            />
            <Text type="supporting">{labelText}</Text>
          </HStack>
          {onReset !== undefined && (
            <Button
              label="Reset progress"
              variant="ghost"
              size="sm"
              onClick={onReset}
            />
          )}
        </HStack>
      </HStack>
    </LayoutHeader>
  );
}
function TutorAvatar({ featured = false }: { featured?: boolean }) {
  return (
    <Avatar
      name="EducAgent"
      src={EDUCAGENT_AVATAR_SRC}
      tooltip={false}
      size={featured ? 64 : "lg"}
    />
  );
}
function conceptForActivity(
  activityId: string | null | undefined,
  concepts: ModuleConcept[],
): string | null {
  if (activityId === "m0-integrated-transfer.01")
    return "association-is-not-causation";
  return (
    concepts.find((concept) => activityId?.startsWith(`${concept.id}.`))?.id ??
    null
  );
}
function conceptsWithRouteCredit(state: DemoState): string[] {
  // Only the replay-derived completion predicate can complete a concept route.
  return state.completed_concept_ids ?? [];
}
function conceptsWithPractice(state: DemoState): string[] {
  const concepts = moduleConcepts(state);
  const completed = new Set(state.completed_activity_ids ?? []);
  return [...new Set([
    ...[...completed].map((activityId) => conceptForActivity(activityId, concepts)),
    ...(state.conversation ?? []).filter((message) => completed.has(message.activity_id))
      .map((message) => message.concept_id ?? conceptForActivity(message.activity_id, concepts)),
  ].filter((conceptId):conceptId is string => conceptId != null))];
}
