# Rain, umbrella use, and wet pavement: Causal-scene design record

- **Status:** implemented S21 design record; the declared synthetic scene is released in the M0 content pack
- **Step:** S20 — Causal-workbench and Socratic-investigation design
- **Implementation gate:** this record authorizes S21 implementation with the
  stated defaults. It does not itself release learner-visible content.

## 1. Decision and pedagogical purpose

The first workbench object is one small, **synthetic** causal scene. A campus
entry log shows umbrella carrying and wet pavement occurring together. The
learner investigates whether that observational pattern establishes an arrow
from umbrella carrying to wet pavement.

The scene is not a claim about a measured campus population, a weather model,
or an empirical causal result. Its records and intervention result are a
declared deterministic micro-world, authored solely to make the M0 distinction
visible. Its released scenario claim and learner-visible text passed the
ordinary content review and release process.

The object supports these M0 ideas together:

- records can show an observed association;
- an association alone does not establish a causal direction;
- a DAG makes a proposed causal explanation visible;
- `do(umbrella_carried)` means deliberately setting umbrella carrying rather
  than observing the existing record; and
- world, data, and model are different: rain is part of the scene world, the
  initial log omits it, and a DAG is a proposed model.

It is a teaching investigation, not an automatic quiz. The learner's initial
explanation, graph, and prediction are visible and append-only but unscored.
After the deterministic comparison, the learner submits a revised causal model
as the formal evidence. The pre-reveal prediction remains in that immutable
evidence snapshot for review, but is not retrospectively scored after its
result has been shown. This preserves prediction as a useful calibration
moment rather than turning a post-reveal revision into an impossible retry.

## 2. Authored micro-world

### Variables and hidden state

| ID | Learner label | Initial visibility | Role in the declared synthetic world |
| --- | --- | --- | --- |
| `rain` | Rain | hidden from the initial records; available as an explicitly suggested possible common cause in the model view | common cause |
| `umbrella_carried` | Umbrella carried | observed | candidate treatment/model variable |
| `pavement_wet` | Pavement wet | observed | candidate outcome/model variable |

The declared world DAG is `rain -> umbrella_carried` and
`rain -> pavement_wet`. It contains no arrow from `umbrella_carried` to
`pavement_wet`. This is a property of the synthetic scene, not a general claim
that umbrellas can never affect whether a surface is wet.

### Records and deterministic intervention result

The observation view is a fixed log of 240 arrivals. It deliberately hides
`rain`.

| Umbrella carried | Pavement wet | Arrivals |
| --- | --- | ---: |
| Yes | Yes | 96 |
| Yes | No | 0 |
| No | Yes | 0 |
| No | No | 144 |

The records therefore show an association: in this synthetic log, umbrella
carrying and wet pavement occur together. They do not disclose why.

The only intervention in S21 is `do(umbrella_carried = yes)`. The scene holds
the underlying rain pattern fixed and gives every one of the same 240 arrivals
an umbrella. Its deterministic result is:

| Umbrella carried after assignment | Pavement wet | Arrivals |
| --- | --- | ---: |
| Yes | Yes | 96 |
| Yes | No | 144 |

The result is fixed regardless of the learner's graph or prediction. A later
scene may add `do(umbrella_carried = no)` or probability variation only after a
second real use case requires it; S21 must not add a generic simulation
control.

### Release and provenance requirements

Before this scene appears in a released pack, content authors must add:

1. one reviewed deterministic scene record that declares the variables,
   world DAG, record table, intervention, and result;
2. released resources for the hook, labels, hint ladder, direct explanation,
   and result interpretation; and
3. links from general causal teaching to the existing reviewed M0 claims for
   association, causal assumptions, DAG language, and intervention.

The fixed tables qualify as a deterministic scene result, not a cited empirical
statistic. The general causal statements still require reviewed claims. Until
these records are released, this document is a design draft and neither a
tutor nor a renderer may show the scene to learners.

## 3. Learner sequence

The shell presents one active scene canvas and one persistent tutor panel. The
tutor directs attention to the current action; it does not become a separate
lesson transcript.

| Phase | Learner-visible action | Recorded result | Scoring and reveal rule |
| --- | --- | --- | --- |
| Hook | Read the unfamiliar campus-log situation; write a short first explanation or select **I am not sure yet**. | A visible, unscored starting hypothesis. | No causal answer or hidden variable is revealed. `I am not sure yet` is a valid attempt and routes to the records. |
| Records | Open the two-variable arrival table and identify what the log records. | `open_records` action. | The table is visible; it establishes only the displayed association. |
| Model | Submit a small DAG using declared variables and permitted arrows. The learner may add the labelled possible unobserved cause `rain`. | A versioned graph artifact. | A graph is a model proposal, not a correctness event. The tutor may stage a suggestion but the learner must explicitly apply or decline it. |
| Prediction | Before any result, predict what will happen if every arrival is given an umbrella. | One unscored prediction. | The result stays hidden until a prediction is committed. A bounded hint or direct explanation ends by requesting a fresh prediction. |
| Intervention | Run the single declared `do(umbrella_carried = yes)` action. | A deterministic result table linked to the prediction. | A button cannot award evidence or completion. |
| Comparison and revision | Compare prediction with result; revise the DAG and/or short explanation. | A second versioned graph/explanation artifact. | The tutor asks about the observed change (or lack of it), never merely repeats the hook. |
| Formal causal evidence | Submit the revised model after comparing it with the declared result. | Immutable `CausalSceneEvidence`, including the recorded pre-reveal prediction and intervention identity. | The evaluator checks the revised declared DAG and observed intervention; the prediction remains trace evidence, not a post-reveal score. |

The scene is the `association-is-not-causation.transfer` activity, with
supporting links to the other listed concepts. It does not silently make those
supporting concepts complete.

## 4. Declared action surface and replay boundary

S21 should add one causality-owned `CausalScene` extension rather than a
generic interaction SDK. Its minimum learner actions are:

| Action | Parameters | Runtime validation | Deterministic output |
| --- | --- | --- | --- |
| `open_records` | none | legal only from the hook | initial observational table is visible |
| `submit_graph` | a complete graph made from declared nodes and permitted edges | graph is acyclic; no unknown node, arrow, or hidden parameter; scene revision must match | new graph revision |
| `submit_prediction` | one declared outcome label | legal only after records and before the result | prediction is locked for comparison |
| `run_intervention` | exactly `umbrella_carried = yes` | legal only after a prediction, once per scene revision | declared intervention table |
| `submit_revision` | a complete permitted graph plus optional bounded reflection | legal only after the result | revised artifact |

The renderer may keep unfinished graph edits locally, but only a submitted
action is appended. Each recorded scene action contains the scene ID, attempt
ID, action ID, bounded parameters, input scene revision, output revision, and
the deterministic result reference where applicable. Replay reconstructs the
same visible scene from the events. It rejects stale revisions, repeated
interventions, invalid DAGs, unknown variables, and any parameter the author
did not declare.

The initial hypothesis remains the existing bounded, unscored learner-message
path. It may influence selection among legal pedagogical focuses; it cannot be
converted into a causal verdict or progression permission. A scene action is
also not a correctness event. Only the separately declared causal-scene
evaluator can emit `Evaluation.accepted` from the final immutable snapshot.

## 5. Model interaction

The graph editor is a small model builder, not a free drawing canvas. S21
permits only these nodes and candidate edges:

| Edge | Learner may submit? | Why it is useful |
| --- | --- | --- |
| `umbrella_carried -> pavement_wet` | yes | surfaces the tempting causal reading of the records |
| `pavement_wet -> umbrella_carried` | yes | surfaces an alternative direction without endorsing it |
| `rain -> umbrella_carried` | yes after `rain` is introduced as a possible unobserved cause | makes a common-cause model explicit |
| `rain -> pavement_wet` | yes after `rain` is introduced | completes the common-cause model |

Every arrow is labelled as a **proposed causal direction**. The UI must not
colour a graph correct or incorrect before a declared evaluator exists. After
the intervention result, the tutor may point out that a graph with an umbrella
arrow predicted a change that the synthetic result did not show. The tutor
still does not score the graph; the learner decides whether to revise it.

## 6. Tutor protocol

The S22 agent will use one compact master instruction plus a typed,
content-declared `interaction_focus_id`. It receives only a frozen scene
snapshot, bounded recent turns, legal focus IDs, and released resources.

| Dialogue job | Required grounding | Permitted next direction |
| --- | --- | --- |
| `orient` | current phase and hook resource | invite a first explanation or route an explicit unsure response to the records |
| `elicit_prediction` | current graph, visible records, and prediction focus | ask one question about the declared intervention before reveal |
| `interpret_observation` | learner prediction, declared intervention result, and graph revision | ask the learner to compare prediction with result and revise |
| `consolidate` | completed scene actions and the next released activity | state the bounded distinction through released content and route to formal transfer |

The agent must name the learner's latest relevant action, prediction, or result
when one exists. It may not rephrase the initial umbrella question as a new
Socratic turn, invent another intervention, create an edge, or write the
learner's graph. Existing exact and semantic question-repetition validation
still applies.

The content pack supplies a finite escalation ladder:

1. an attention cue to distinguish the visible records from a causal
   explanation;
2. a second cue to inspect what was deliberately set in the intervention;
3. a released direct explanation of association, model, and intervention; then
4. a fresh learner graph revision (or, before the reveal, a prediction).

An explicit accessibility or explanation request may enter the ladder without a
new attempted answer. A direct explanation never advances the scene or the
curriculum by itself.

## 7. Accessibility and responsive equivalence

The graphical presentation is optional. The same actions and results must be
available without a pointer, canvas, colour distinction, or wide display.

| Need | Required equivalent |
| --- | --- |
| Keyboard graph editing | A labelled arrow list with add/remove controls, an announced graph summary, predictable focus after a submitted edit, and no drag-only action. |
| Screen-reader graph access | A text model such as “Rain points to umbrella carried; rain points to pavement wet,” plus the available candidate arrows and current graph revision. |
| Record comparison | Semantic HTML tables with captions, column headers, row headers, and a textual summary of the association. |
| Intervention result | A labelled result table and sentence that identifies the deliberate assignment and the unchanged wet-pavement count. The result is not conveyed only by a chart. |
| Prediction and revision | Native, labelled controls with visible validation and a reviewable locked prediction. An unsure first explanation is available without typing. |
| Narrow screen | The scene becomes a linear sequence: current action and result first, persistent tutor context and composer directly after it, then route metadata. No default-hidden tutor or horizontally inaccessible graph. |
| Motion and colour | No essential inference depends on animation or colour. Respect reduced-motion settings and use text/status labels. |

The S23 browser qualification must test mouse, keyboard-only, narrow-screen,
and text-equivalent paths through exactly the same authored sequence.

## 8. Authority, tool, and safety boundary

| Owner | Owns here | Explicitly does not own |
| --- | --- | --- |
| Content pack | scene data, resources, legal nodes/edges/actions, hint ladder, release/provenance declarations | mutable learner state or grading |
| Causal-scene domain extension | pure action validation and fixed scene transition/result | teaching prose, cursor changes, or curriculum acceptance |
| Runtime | append/replay, phase, budget, legal candidate construction, frozen snapshots, progression gate | invented scene facts or graph verdicts |
| Evaluator | final causal-model `Evaluation.accepted` and its consequence | tutor tone, scene rendering, or unscored hypothesis interpretation |
| Tutor | one typed dialogue job and legal focus; a tentative, traceable hypothesis | scene writes, edge creation, intervention execution, factual invention, correctness, or progression |
| Renderer | accessible controls and display of declared state | causal simulation, hidden reveals, or accepted evidence |

The tutor's later read-only tool surface contains at most:

1. `inspect_scene`: current frozen phase, graph, prediction, and legal action;
2. `inspect_last_result`: the released observation or deterministic result
   already legal to reveal; and
3. `list_legal_focuses`: author-declared focus IDs and associated next action.

There is no live Python/Jupyter kernel, arbitrary code, remote causal package,
free-form graph DSL, dynamically loaded tool, learner-supplied query, or
network tool. Learner text and retrieved source material are low-trust data;
they cannot alter tool instructions, scene parameters, resources, or system
rules. The agent returns a typed proposal and cannot call the action command.

## 9. Workbench UI contract

The Claude handoff at
[`../claude-design-handoff/EducAgent Learner Workbench.dc.html`](../claude-design-handoff/EducAgent%20Learner%20Workbench.dc.html)
is a useful visual reference, not a canonical implementation or content
source. Its useful decisions are retained:

- main action canvas plus a persistent tutor panel on wide screens;
- one visible phase and one next action, rather than a long quiz form;
- records, model, intervention, and reflection as views of one scene;
- staged tutor suggestions that require learner confirmation; and
- explicit recovery, text alternatives, and narrow-screen treatment.

S21 may adapt the visual language to Astryx, but it must not copy inline HTML
or replace the existing safety boundary with front-end state.

## 10. S23 qualification target

Before a broader visual-tool roadmap is considered, S23 will judge the scene
against this short rubric:

1. the learner can identify the current action and make a first prediction;
2. the tutor refers to the actual prediction, graph, or result rather than
   repeating the opening question;
3. the object makes the observation/intervention difference visible and allows
   revision of the same artifact;
4. no tutor response, UI click, or graph state grants accepted evidence or
   progression; and
5. learners can finish the formal causal-model evidence through keyboard, narrow,
   and text-equivalent flows.

The outcome question remains whether this sequence improves immediate and
delayed unseen transfer under the frozen S11 protocol. A polished graph,
conversation count, or a favourable LLM judgement is not success evidence.

## 11. Open review questions

1. Does the causal-content reviewer approve the synthetic world and the
   intentionally perfect observational association, or should the scene use a
   less deterministic-looking record while retaining the same causal logic?
2. Which exact M0 curriculum position should launch the scene, and should one
   supporting concept receive an additional formal evaluator after the existing
   association transfer?
3. Is the “possible unobserved cause” affordance sufficiently discoverable
   without prematurely revealing the intended model?
4. Does the proposed narrow layout keep both the active object and tutor usable
   at the target device widths?
5. Are the proposed S23 behaviours an adequate human-review rubric before S21
   implementation begins?
