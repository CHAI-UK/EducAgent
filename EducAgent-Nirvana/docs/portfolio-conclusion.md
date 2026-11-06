# EducAgent Portfolio Conclusion

**Status:** current ecosystem strategy; awaiting supervisor/CHAI and specialist-tool-owner review

**Last consolidated:** 2026-10-23

## The decision in one paragraph

EducAgent should be presented as one layered learning ecosystem. **Portal** is the selected EducAgent-SDK Causality M0 learning route. **Nirvana** is a lower-threshold research front door: it helps researchers express a real problem, create a reviewable Causal Research Brief, and choose an appropriate next route. **Specialist CHAI tools**, beginning with the Domain Generalization Copilot as a concrete example, continue from that handoff for specific problem classes. The products may overlap in user-facing explanation because they are complementary work by colleagues; the important boundary is that Nirvana does not duplicate specialist causal policy or claim ownership of the downstream solution.

This is the stable answer to “what are we building?” Portal uses the current SDK; Nirvana remains a separate lightweight prototype while its product policy is tested.

The roles below are product targets, not a description of fully implemented capabilities. The current Portal combines mostly classification activities with one authored causal scene and phase-aware guided local chat. As of 2026-09-09, Nirvana offers provisional AI task recognition and structured Brief drafting/refinement alongside manual editing. A diagnostic teaching loop and verified user understanding remain unimplemented. Both paths remain exploratory and unqualified as study arms.

## Proposed learning entry

The review Learning page now places EducAgent first, followed by the compact
external resource list. Its light palette matches the observed CHAI white,
grey-purple (`#524c63`) and teal (`#487a7b`) colours; the existing manual/system
light-dark preference remains available. This is a subdomain resource page,
not a claim of integration into the main CHAI navigation.

```text
Learning Resources
├─ Learning with EducAgent
│  ├─ EducAgent Portal -> /portal/
│  └─ Causal Research Framing -> /nirvana/
├─ Books
├─ Online courses
└─ Practical resources
```

The public label `Learn with EducAgent` can remain umbrella language. `Nirvana` is an internal codename until an external name is approved.

## Why two entry routes and a specialist layer

| Route | User arrives with | Product job | Leaves with |
|---|---|---|---|
| Portal | Little or no causal vocabulary or research background | Complete authored everyday tasks using the selected SDK M0 concept backbone | Inspectable task outputs; concept exposure and completion kept separate from independent transfer and mastery |
| Nirvana | A meaningful research problem but little formal causal training | Identify the causal task, structure the supported parts, teach only what is needed, and prepare the next route | A Causal Research Brief the researcher understands, plus a bounded handoff when specialist work is needed |
| Specialist tools | A sufficiently formulated problem of a supported specialist type | Apply domain- and task-specific causal frameworks | Feasibility, design, or method guidance within the specialist tool’s stated boundary |

Combining these into one adaptive chatbot would blur the audience, stopping rule, and success measure. Keeping layered products with explicit handoffs makes it possible to reuse specialist expertise without forcing causal novices to begin inside a technical interface.

## Relationship to existing CHAI specialist work

Kurt Butler, Damian Machlanski and colleagues’ [causal framework for mitigating healthcare data shifts](https://arxiv.org/html/2603.13595v1) already owns a four-stage specialist reasoning process: problem conceptualisation, causal description, feasibility analysis, and deployment strategies. The accompanying [Domain Generalization Copilot](https://chai-uk.github.io/domain-generalization-copilot/) operationalises that process through variables, an augmented causal graph, shift assumptions, feasibility questions, and candidate mitigation strategies.

This work should be treated as a collaborator and downstream capability, not as a weak competitor to reproduce. The proposed ownership boundary is:

| Layer | Owns | Does not own |
|---|---|---|
| Nirvana | plain-language intake, task recognition, minimum just-in-time teaching, editable assumptions and uncertainty, user understanding, confirmed Brief, and handoff choice | domain-generalisation feasibility rules or deployment-method recommendations |
| DG Copilot | prediction-under-shift conceptualisation, augmented causal description, feasibility questions, and candidate deployment strategies | the general novice entry across all causal research tasks |
| Methodologist / capable LLM | challenge, explanation, or later work under a bounded request | silent replacement of the researcher’s confirmed problem or assumptions |

The exact interface remains a hypothesis. A manual preparatory note and link can make the local route explicit, but they are not an integration. Observe whether causal novices can use DG Copilot directly and identify repeated blockage before expanding the prelude or automating transfer. DG Copilot's form-and-graph workflow should not be described as a chatbot that accepts a pasted prompt.

## What this positioning gains and gives up

### Gains

- a clear audience and outcome for each route;
- a board-visible result that can be delivered in stages;
- differentiation through a learning trajectory and persistent artifact rather than through “having a chatbot”;
- a concrete route for collaboration with existing CHAI frameworks and tools;
- honest comparison with textbooks, worksheets, general LLMs, document-grounded assistants, and human methodologists;
- a credible basis for later funding if one route demonstrates value.

### Deliberate losses

- no claim that the guided local text paths are the final tutor policy or interchangeable with earlier vanilla-baseline evidence;
- no claim to replace ChatGPT, Claude, NotebookLM, courses, or causal experts;
- no automated identification, estimator choice, coding, or effect estimation;
- no reimplementation of specialist DG feasibility or deployment logic;
- no assumption that both routes need one runtime or must advance at the same speed;
- no cross-disciplinary effectiveness claim before it is observed.

These are boundaries, not deficiencies. They should change only in response to repeated evidence.

## Shared and separate responsibilities

Share only what is genuinely common at first:

- causal vocabulary and reviewed explanatory content;
- visual treatment of source, user review, evidence support, and uncertainty;
- accessibility and responsible-AI principles;
- a public learning identity and optional navigation between routes;
- a common handoff convention in which task-specific views are derived from a researcher-confirmed Brief.

Keep separate:

- the product contract and completion outcome;
- review and release decisions;
- user-study evidence;
- runtime and state, while the local demos reuse the same ELM configuration;
- specialist scientific rules, which remain with the tool and expert group that owns them.

Evidence from Portal cannot pass a Nirvana gate, and a good Nirvana brief cannot establish that Portal teaches novices effectively.

## Evidence boundary

Completed work establishes that the layered concept can be described coherently and that testable first slices can be specified. It does **not** yet establish usability, learning, comparative value, downstream impact, CHAI acceptance, institutional adoption, or funding eligibility.

Board-safe language is therefore:

- “designed to help,” not “proven to improve”;
- “provisional causal relations,” not “discovers the true graph”;
- “prepares a handoff to people, LLMs, and relevant specialist tools,” not “automates the research workflow”;
- “value will be compared with the best task-matched existing route,” not “better than ChatGPT, Claude, or another CHAI tool.”

## Decision still required

Before either route is treated as a public product, ask the supervisor/CHAI-facing reviewer to accept, revise, or reject six propositions:

1. Portal and Nirvana are useful, distinct entry routes under one learning offer.
2. Portal should retain the selected SDK M0 concept backbone while testing one fixed, authored task-driven mission before expanding or personalising the curriculum.
3. Nirvana should first serve researchers new to causal methods and stop at a reviewable brief and task-matched handoff.
4. Each route may simplify or stop independently if its simplest credible alternative is sufficient.
5. The available people and time justify advancing both routes now; otherwise one route is explicitly parked with a reopen condition.
6. For prediction-under-data-shift questions, DG Copilot owns specialist reasoning while Nirvana tests only whether a novice-facing prelude and handoff resolve an observed access or understanding problem.

The immediate output of that discussion should be one corrected narrative, one named owner per active route, and one next review—not a commitment to build every later phase.

These external decisions do not block the requested local reliability, source-rights, or documentation repairs. They remain necessary before public-product claims, participant work, or institutional deployment.

## Funding and expansion boundary

New disciplines, additional causal problem classes, deeper tool integrations, and a broader tutoring platform are later investments. A separate funding proposal becomes sensible only after there is a completed first slice and evidence of a concrete user or impact route. Funding criteria and CHAI public language must be rechecked at the time of application; thematic fit is not an award or product endorsement.
