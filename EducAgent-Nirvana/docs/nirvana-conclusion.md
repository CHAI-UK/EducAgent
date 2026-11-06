# EducAgent Nirvana: Product Conclusion

**Status:** worksheet and concise framing guidance verified through tests, live probes, Chrome, and local restart; specialist interface and external evaluation pending

**Internal codename:** Nirvana

**Last consolidated:** 2026-09-09

## Product identity

Latest interaction update (2026-09-09): initial generation creates an editable draft; chat follow-ups propose per-field Before/Proposed diffs that require Accept/Reject. They do not auto-edit the Brief. Rejected proposals leave fields unchanged. Pending proposals are excluded from handoffs. Copy is allowed for both drafts and reviewed Briefs, with review status carried in the text; earlier confirmation-gated copy descriptions below are superseded. Route includes a short, task-specific causal-applicability summary, not a validated causal analysis.

Nirvana is a bounded, novice-facing causal problem-framing and routing bridge for researchers who know their domain but have little or no formal causal training.

It transforms:

> “I observed or care about X and Y; how could causality help my research?”

into:

> “Here is the kind of causal problem I have, the parts I can state defensibly, what I have assumed or still do not understand, and the right person, LLM, or specialist workflow to continue with.”

The durable product is the **Causal Research Brief**, not the chat transcript. A worksheet, deterministic guided flow, or bounded LLM-assisted flow is only an interface for constructing that brief. A specialist handoff is a derived view of the confirmed Brief, not a second scientific source of truth.

As of 2026-09-09, the local implementation uses `/api/frame` to classify new natural-language questions and extract task-specific Brief fields through the shared ELM model. Follow-up answers return a complete revised draft. Missing facts remain blank; inferred framing remains provisional. Manual editing and task selection are still available. It does not formally diagnose a conceptual blockage, assess teach-back, maintain item-level provenance, or persist the Brief across sessions. User confirmation records review of a draft, not verification of its causal claims or the user's understanding.

Generate starts from the current question only, excluding earlier worksheet values. Follow-up sends the current Brief and recent conversation. AI updates preserve the conversation and invalidate confirmation; manual edits clear conversation and discard in-flight replies. Request failure retains the draft and exposes a retryable error rather than substituting a fixed example. The handoff prompt is assembled from the current task-specific fields, so edits cannot leave a stale AI-generated prompt. DG preparation notes remain a manual companion to DG Copilot, not an import format.

The local worksheet starts with an empty problem and no selected task. Selecting another task clears its predecessor's fields; editing a synthetic example's problem clears the example-derived answers. A whole-Brief synthetic/manual source label is visible, not item-level provenance. Every Brief edit invalidates confirmation, refreshes the route preview, and clears the old chat context while discarding late replies. Copy is enabled only after explicit confirmation and uses the same current snapshot as the preview. Opening DG Copilot sends no Brief content; copying notes remains a manual action. Refreshing the page loses the worksheet and conversation.

Earlier on 2026-09-05, four Python tests, one Node UI-state regression, and Chrome checks passed for worksheet repairs. Two original vanilla API requests returned 200 but produced long seven-/nine-section checklists. That prompted a separate guidance repair: answer the immediate question, help with one genuinely missing field by default, preserve unknowns, and give requested detail without a rigid one-question cap. Explicit user answers in recent conversation remain usable even when the worksheet still says unknown; conflicts require clarification, and the agent must not pretend to edit the worksheet.

The revised server passed eight provider-independent tests; the Node UI-state regression also passed. Authorised live tests use the same `gpt-5.6-luna` configuration. The final direct initial reply was 44 words; its 53-word follow-up recognised outcome/population/time and asked for the missing comparator. An explicit detail request received 156 words. Two intermediate tuning probes re-asked population, so the prompt was corrected before the final follow-up probe. Final Chrome replies were about 69 and 55 words, carrying weekly journeys, adult city residents, and six months forward and asking for the missing comparison. The `Framing guide via ELM` label is deployed in the restarted local demo; port 8011 health returned 200. These are targeted regression observations, not general reliability, a diagnostic teaching system, or evidence of learning/comparative value.

## Primary user and promise

The first user is a healthcare or life-science researcher who can explain a scientifically meaningful context but is new to causal methods. Education and social-science cases may later test transfer; they should not be pooled into the initial healthcare claim.

The first-session hypothesis is:

> Within a 15-minute active task, the researcher can produce a provisional Causal Research Brief they understand and either continue through the supported effect-question branch or choose a defensible next route.

This is a target to test, not a current result. The 15-minute session, at most one reviewed concept intervention, and one bounded next step are constraints for the first test; they are not permanent limits on every future user or task.

## The first intended job

The first intended causal-method branch frames the effect of one exposure or intervention, compared with an alternative, on an outcome in a defined population and time horizon. The local AI front door suggests effect, shift, mediation, descriptive, or other; users can override it manually. This is provisional automated task recognition, not a fully validated teaching branch.

The target route to test is:

1. hear the problem in the researcher’s own language under the permitted information tier;
2. clarify the intended decision or scientific purpose and recognise the likely task class;
3. explain why the problem fits the supported branch, a specialist workflow, or another route;
4. for the supported effect branch, state the exposure or intervention, comparator, outcome, population, and time;
5. make provisional causal relations, assumptions, provenance, and uncertainty visible;
6. teach at most one reviewed concept if a fixed diagnostic shows it blocks progress;
7. let the researcher edit, reject, or mark uncertainty;
8. confirm the brief and choose one bounded next step or handoff.

A prediction-under-data-or-domain-shift request is recognised as a candidate specialist route rather than being silently converted into an effect question. Version 0 may prepare a plain-language handoff to the Domain Generalization Copilot, but it does not perform that tool’s augmented-graph feasibility or deployment-strategy reasoning. Other descriptive, predictive, discovery, literature, coding, mechanism/mediation, sensitive, or individual-advice requests are redirected or stopped as appropriate.

The local prototype includes four explicitly synthetic examples: intervention effect, prediction across changing environments, mediation, and descriptive measurement. These populate task-specific provisional worksheets, not inferred answers to a new user problem. The mediation and descriptive worksheets illustrate a next route; they do not expand the intended causal-method scope beyond intervention effects.

## Causal Research Brief

The target Brief should contain the following. Item-level provenance, support verification, and durable version history remain unimplemented; a visible draft/confirmation state must not imply they exist.

- the research question and intended decision;
- the recognised task class and why the current route was selected;
- population and setting;
- exposure or intervention;
- comparator;
- outcome and time horizon;
- available evidence as reported by the user, clearly marked as unassessed;
- provisional causal relations and assumptions;
- the origin, user-review status, support status, and uncertainty of each proposed item;
- limitations and unresolved questions;
- one bounded next action;
- the selected next consumer and any route-specific fields derived for that handoff;
- version and confirmation state.

A complete brief may contain visible uncertainty. It must never turn “the user kept this suggestion” into “this claim is true or evidence-supported.”

## The bridge function

Nirvana should do one part exceptionally well: help a causal novice cross from an informal research concern into a problem representation they understand and an appropriate next workflow.

The handoff contains one confirmed brief revision and one fixed review request. It asks the recipient to recover the intended contrast, identify material missing information, preserve uncertainty and provenance, and suggest one bounded next step. It does not ask a downstream LLM to invent facts, establish identification, choose an estimator, or run an analysis. External transfer is always initiated by the user; no hidden conversation or research content is sent automatically.

This makes Nirvana complementary to stronger general LLMs, methodologists, and specialist CHAI tools rather than a weak replacement for them.

### Domain Generalization Copilot handoff

The [Causal Framework for Mitigating Data Shifts in Healthcare](https://arxiv.org/html/2603.13595v1) and its [Domain Generalization Copilot](https://chai-uk.github.io/domain-generalization-copilot/) already own the specialist path from a prediction problem through causal description and feasibility to candidate deployment strategies.

When the researcher’s problem is prediction under changing hospitals, populations, time periods, devices, policies, or measurement processes, Nirvana may derive a pre-handoff view containing:

- the intended prediction target and real-world use;
- the training and expected deployment environments;
- candidate observed and unobserved variables named by the researcher, including when they are measured;
- suspected shifted variables or mechanisms;
- the researcher’s provisional view of how candidate predictors relate to the target, including `unknown`;
- available deployment data and adaptation constraints;
- researcher-stated assumptions and uncertainty;
- concepts the researcher could not yet explain;
- a bounded request to continue inside the specialist workflow.

Nirvana should not invent the augmented causal graph, classify variables as stable, or recommend a mitigation method on behalf of the specialist tool. Initially the handoff is a user-reviewed preparation note and link with manual field mapping. DG Copilot is a form-and-graph workflow, not a prompt-paste chatbot; a copied note is reference material for the user or a human/LLM reviewer, not an executed tool request. Automatic transfer is unnecessary until evidence shows that re-entry is a material burden and the owners agree an interface.

The public wording should describe this route as **“prediction across changing environments,” “prepare for Domain Generalization Copilot,”** and **“continue with Domain Generalization Copilot.”** Use `data/domain shift` in the Brief and specialist handoff when technical precision is useful. Do not say that Nirvana designs a robust model or recommends a mitigation strategy. Preparation may help the researcher review how the specialist workflow connects candidate strategies to graph or structural assumptions, feasibility conditions, missing evidence, and possible stress tests.

## Alternatives and the product test

Nirvana must earn its extra complexity against credible alternatives:

| Alternative | What it already does well | What Nirvana must add to justify itself |
|---|---|---|
| Static brief worksheet | Makes the required fields explicit with minimal risk | Resolves repeated blockage or improves understanding/handoff enough to justify guidance |
| Strong framing prompt in a capable LLM | Flexible clarification and fast draft generation | Stable state, editable provenance, recovery, bounded teaching, and governed handoff |
| Document-grounded assistant | Works with a supplied paper or protocol bundle | A clearer decision/comparison/assumption trajectory when source retrieval is not the core problem |
| Domain Generalization Copilot | Guides prediction-under-shift problems through causal description, feasibility, and deployment-strategy candidates | Only a demonstrated novice-facing prelude: task recognition, minimum teaching, understandable assumptions, and clean handoff |
| Human methodologist | Supplies expert judgement and scientific challenge | A better-prepared researcher and a clearer starting artifact, never replacement expertise |

If the worksheet or strong prompt is equally useful with lower burden and risk, it should become the product or fallback. “Uses an agent” is not a value proposition.

## Delivery modes

The first test should select one of three modes:

- **static worksheet** if structure alone is sufficient;
- **deterministic guided flow** if sequencing, clarification, or one reviewed teaching intervention adds value;
- **bounded LLM-assisted flow** only if repeated case-specific adaptation is necessary and structured-output, provider, privacy, and failure-recovery checks pass.

The 2026-09-09 user request selects LLM-assisted drafting for the local demo. This does not select a validated study arm. All guided modes must retain a complete manual editing path and provider-independent brief representation.

## Explicit stopping boundary

Nirvana does not:

- infer the true causal graph;
- establish identifiability;
- select or run the final statistical analysis;
- provide individual clinical advice;
- verify literature or source support in version 0;
- replace causal, domain, governance, or ethical expertise;
- support every causal task or discipline.
- reproduce specialist domain-generalisation policy or present its candidate strategies as recommendations from Nirvana.

It should stop and recommend review when missing context, high stakes, ambiguity, or unsupported assumptions make further automation misleading.

## Minimal evidence sequence

1. **Specialist gap check:** agree the intended ownership/interface with Damian and Kurt, then observe 4–5 causal novices using the existing DG Copilot directly on synthetic prediction-under-shift cases. Record repeated conceptual blockage, facilitator help, incorrect assumptions, false confidence, time, and what the tool already handles adequately.
2. **Before expanding the local prototype:** expert-review the front-door task classification, intended effect branch, Brief, stopping boundary, specialist handoff, synthetic cases, and fair static alternative.
3. **Usability:** observe 5–8 eligible researchers using the selected Nirvana mode; measure completion, routing, friction, understanding, time, and critical authority failures.
4. **Task-matched comparative value:** for effect questions compare with the selected worksheet or capable-LLM route; for data-shift questions compare direct DG Copilot use with Nirvana-prelude-plus-DG-Copilot. Do not pool the two task classes.
5. **Handoff utility:** only after researcher-side value survives, test whether the intended consumer recovers the researcher’s goal and uncertainty better from the confirmed Brief than from the raw starting problem.
6. **Verified reuse:** only if handoff value survives and governance permits real questions, observe whether researchers later edit, share, or act on the brief.

Artifact quality and user understanding are separate outcomes. Positive comments, polished prose, opening an export, or a protocol existing on paper do not establish value.

## Data and safety conclusion

Use synthetic cases until the institutional host, data controller, lawful basis, privacy notice, storage, access, retention, deletion, withdrawal, incident process, and external-provider boundary are explicitly approved. Ordinary product analytics should be content-free. Real unpublished questions, free-text study records, and external model calls require a separately authorised route.

## Current next decision

### Task taxonomy: focused literature review (2026-09-09)

This is a focused, source-checked review requested by the user, not an exhaustive systematic review or a validated taxonomy. The existing `effect / shift / mediation / descriptive / other` menu is adequate for the current demo, but not a comprehensive ontology. It mixes an inferential goal (effect), a narrower explanatory task (mediation), an environment condition (shift), and a legitimate non-causal objective (description).

#### Literature anchors

| Source | Actual organising principle | Implication and limit for Nirvana |
| --- | --- | --- |
| Hernán, Hsu & Healy (2019), *A Second Chance to Get Causal Inference Right: A Classification of Data Science Tasks*. [Open manuscript](https://arxiv.org/abs/1804.10846) | Description, prediction, and counterfactual prediction, including causal inference. | Start with what the researcher wants to know. Their broad use of counterfactual prediction is not identical to Pearl's third rung. |
| Pearl (2019), *The Seven Tools of Causal Inference, with Reflections on Machine Learning*. [Author manuscript](https://ftp.cs.ucla.edu/pub/stat_ser/r481.pdf) | Association, intervention, and counterfactual queries demand different information. | Use the causal hierarchy to check knowledge requirements, not as a complete product menu or an estimator-selection rule. |
| Guo, Cheng, Li, Hahn & Liu (2020), *A Survey of Learning Causality with Data: Problems and Methods*. [Open manuscript](https://arxiv.org/abs/1809.09337) | Learning causal effects and causal relations/structure. | Recognise causal discovery separately from estimating a specified intervention effect. Recognising it does not mean running discovery. |
| Kaddour, Lynch, Liu, Kusner & Silva, *Causal Machine Learning: A Survey and Open Problems* (2022 preprint; arXiv v3, 2026). [Open text](https://arxiv.org/html/2206.15475v3) | Causal supervised learning, generative modelling, explanations, fairness, and reinforcement learning. | Particularly relevant to researchers asking how causality can help an ML system. It does not provide the whole effect-inference taxonomy; its categories need not be mutually exclusive research intents. |
| Athey & Wager (2021), *Policy Learning with Observational Data*. [Open manuscript](https://arxiv.org/abs/1702.02896) | Learning a decision policy rather than merely estimating an effect. | Capture actions, outcomes, utility and constraints in a specialist policy brief. This is a task-specific contribution, not a global taxonomy. |
| Bareinboim & Pearl (2016), *Causal inference and the data-fusion problem*. [Open article](https://pmc.ncbi.nlm.nih.gov/articles/PMC4941504/) | Combining heterogeneous information and transporting causal effects across environments. | Effect transportability is not the same objective as predictive robustness/domain generalisation. A mention of a new population must not automatically route to DG Copilot. |
| Rojas-Carulla, Schölkopf, Turner & Peters (2018), *Invariant Models for Causal Transfer Learning*. [JMLR](https://www.jmlr.org/papers/v19/16-432.html) | Transfer using invariant conditional relationships under specified assumptions. | Supports asking about environments and potentially stable mechanisms; does not establish robustness for arbitrary scanner shifts. |
| Pawlowski, Coelho de Castro & Glocker (2020), *Deep Structural Causal Models for Tractable Counterfactual Inference*. [NeurIPS](https://proceedings.neurips.cc/paper_files/paper/2020/hash/0987b8b338d6c90bbedd8631bc499221-Abstract.html) | Counterfactual inference with deep structural causal models, including image examples. | High-dimensional generation deserves recognition. This is not evidence of efficacy for the CTPA project, and conditional image translation is not automatically causal counterfactual generation. |

These sources offer complementary organising frameworks, not a single consensus menu. Likewise, model → identify → estimate → refute is a workflow, not a task taxonomy; see [DoWhy's effect-inference documentation](https://www.pywhy.org/dowhy/v0.9.1/user_guide/effect_inference/index.html).

#### Proposed adaptation — not implemented or externally validated

Use three separate layers: **research goal → context tags → supported destination**. The following is our synthesis for the product, not a taxonomy copied from one paper:

| Plain-language goal | Possible subtask |
| --- | --- |
| Estimate the effect of a change | Average/heterogeneous effect; effect transport to another population |
| Understand how or why | Mediation/pathways; event attribution or individual counterfactuals, kept distinct |
| Discover causal relationships | Structure, direction, and missing domain knowledge |
| Choose an action or policy | Action comparison, allocation, sequential decisions |
| Build a model that generalises | Prediction, image generation or representation under environment changes |
| Describe or predict without a causal claim | Description, association, ordinary prediction; a valid non-causal exit |
| Not sure yet | Clarification rather than forced classification |

Context tags can include distribution shift, image synthesis, multiple populations, longitudinal data, or fairness. Allow multiple tags, but do not infer a fairness objective merely from the presence of age or sex. Keep one recommended goal and a short explanation visible; expose alternatives progressively rather than making users understand an ontology first.

Keep `recognised task` separate from `implemented route`. Discovery, policies and counterfactual explanation could initially produce a general specialist-preparation brief without claiming an implemented solver. No menu/schema expansion has been made in this change; review these distinctions with the team first.

#### Example 5: CTPA synthesis

The user asks to synthesise their stated non-contrast CTPA target from contrast CTPA and investigate robustness across scanner manufacturers and demographic composition. A useful framing is:

- **Goal:** build a synthesis model that generalises.
- **Task/output:** conditional image synthesis; clarify the exact intended target image.
- **Context:** scanner and demographic distribution shifts.
- **Potential causal contribution:** hypothesise patient-related versus acquisition-related factors and which mechanisms may remain stable; make assumptions explicit for representation and robustness evaluation.
- **Unknowns:** training vendor coverage, deployment conditions, paired references, available metadata at deployment, and success criteria. Do not substitute the desired vendor list for observed training coverage.
- **Destination:** a specialist robustness workflow, potentially DG Copilot after checking suitability for the synthesis objective. Not an automatic import, graph, or recommendation to deploy a method.

If the researcher explicitly asks for the same individual's image under a different acquisition intervention, clarify whether they intend an individual counterfactual question. Do not infer this solely from the word synthesis. Likewise, do not promise that causal methods will improve this model; that remains a hypothesis requiring task-matched evaluation.

Suggested positioning: **Nirvana helps researchers turn open-ended questions into explicit research goals, reviewable causal assumptions, and actionable briefs for specialist workflows.**

Worksheet reliability and concise framing guidance passed provider-independent, live-probe, and Chrome checks, and the local demo has restarted. Retain the short-default/requested-depth distinction and carry-forward of explicit user answers while testing additional cases. The formal teaching/teach-back loop remains unimplemented. Prompt guidance is not a semantic guarantee, and these repairs do not widen the scientific boundary or substitute for a participant study.

In parallel, confirm the collaboration boundary with the DG Copilot owners and arrange the direct-use specialist gap check under an approved route. Review the intended effect-question branch. The subsequent product decision is whether evidence supports a static, deterministic-guided, or provisionally LLM-assisted front door—and exactly which observed blockage it owns. Build only that slice; do not rebuild the specialist framework.
# Implementation update — 9 September 2026

The taxonomy proposal below is now implemented as eight substantive framing
tasks plus other/unclear, with dedicated specifications, classification reasons,
orthogonal context tags and literature-inspired examples 6–9.
See [Task specs](task-specs.md) for the current contract. This expands research
framing and specialist preparation only; no downstream causal analysis engine or
automatic DG Copilot integration has been added.
