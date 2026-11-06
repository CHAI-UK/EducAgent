# Nirvana: Positioning, Related Work, and Scope Boundaries

**Status:** research positioning draft for supervisor and collaborator review; not a systematic review

**Last source check:** 2026-09-17

**Audience:** Sotos, Damian, Kurt, EducAgent team

**Purpose:** state what Nirvana should own, what it must not build, and who already occupies the neighbouring space

## 1. Positioning in one paragraph

Every existing causal agent starts after the hard part is done: a dataset exists and the question is already well posed. They automate identification, estimation, and interpretation. Nirvana starts one step earlier, with a researcher who has a vague question, no data yet, and little causal training, and it stops one step earlier too: at a reviewable specification (the Causal Research Brief) and a route to the right tool or person. We do not compete with the analysis agents; we produce the input they all assume.

## 2. Landscape

### 2.1 End-to-end causal analysis agents (downstream of Nirvana)

| System | Input assumed | What it does | Where it stops | Relation to Nirvana |
|---|---|---|---|---|
| [LLM4Causal](https://arxiv.org/abs/2312.17122) (2023/24) | Natural-language query + dataset | Fine-tuned LLM identifies the task (structure, effect, policy), calls the matching function, interprets output | Needs data and an explicit query; no routing outside its own functions | Closest in spirit to task recognition; a possible consumer of a Brief |
| [Causal Agent](https://arxiv.org/abs/2408.06849) (Han et al., 2024) | Tabular data + question | Tools, memory, reasoning over causal-learn; CausalTQA benchmark (four levels, about 1.4K questions) | Data question answering only | Downstream consumer |
| [Causal-Copilot](https://arxiv.org/abs/2504.13263) (UCSD, 2025) | Dataset + natural-language query | 20+ algorithms: discovery, inference, hyperparameter tuning, interpretation; tabular and time series | Assumes the causal question is already stated | The analysis harness to hand off to, not to rebuild |
| [Causal AI Scientist](https://openreview.net/forum?id=EDWTHMVOCj) (NeurIPS 2025; [code](https://github.com/causalNLP/causal-agent)) | Query + dataset + dataset description | Rule-based decision tree selects a method from data properties (randomisation, temporal structure, instruments), executes, self-corrects | Selects over data properties, not over question ambiguity | Downstream consumer; its explicit decision tree is a model for our task rules |
| [pywhy-llm](https://github.com/py-why/pywhyllm) (PyWhy) | A partially built causal model | Suggests confounders, instruments, and critiques of a proposed model | Modelling-stage assistant | We may call it; we do not rebuild it |

Related 2025 to 2026 work in the same layer: [LLM-based agents for automated confounder discovery](https://arxiv.org/abs/2508.07221), [Causal Ensemble Agent](https://arxiv.org/abs/2606.10607), and the [Causal MAS survey](https://arxiv.org/pdf/2509.00987).

### 2.2 Benchmarks on specification and design (closest research neighbours)

| Benchmark | Questions come from | What is scored | Gap it leaves |
|---|---|---|---|
| [CausalReasoningBenchmark](https://arxiv.org/abs/2602.20571) (Sawarni, Tan, Syrgkanis; Feb 2026) | 79 published papers, 3 textbooks, 132 real datasets; 173 queries | Identification specification (strategy, treatment, outcome, controls, design fields) scored separately from estimation. Models pick the right strategy in 79% of cases but produce a fully correct specification in only 34% | Expert-written questions with data; effect estimation only |
| CauSciBench ([OpenReview](https://openreview.net/pdf?id=EO8mTLqDuT)) | Scientific research problems | Framing treatment, outcome, and estimand; identifiability | Expert-posed; effect only |
| [InterveneBench](https://arxiv.org/abs/2603.15542) (Mar 2026) | 744 peer-reviewed social-science studies | Intervention and study-design reasoning without a given graph | Expert-posed policy studies |
| [CausalVerify](https://arxiv.org/abs/2609.07944) (Sept 2026) | 259 economics papers + 100 synthetic scenarios | Executable estimation workflows for four quasi-experimental designs | States that problem formulation and design selection from ambiguous constraints are out of scope |
| [CausalQuest](https://neurips.cc/virtual/2024/100297) (NeurIPS 2024) | 13,500 natural questions from the web | Whether a question is causal; a taxonomy of causal questions (42% of human questions are causal) | Everyday questions, not research questions; no specification |

### 2.3 Health study-design automation (adjacent to the effect branch)

- [THESEUS](https://academic.oup.com/jamiaopen/article/9/4/ooag131/8729191) (JAMIA Open, 2026): free-text study description to a structured target-trial specification to executable OHDSI code; eight LLMs, standardisation accuracy 0.82 to 0.97. Starts from an already designed study.
- [Large Language Models as Co-Pilots for Causal Inference in Medical Studies](https://arxiv.org/abs/2407.19118) (Alaa, Phillips, Kıcıman, Balzer, van der Laan, Petersen; 2024): LLMs help catch study-design flaws before analysis. Conceptual framework with illustrative examples; no user study.

### 2.4 Realistic alternatives a researcher already has (our baselines)

- A plain ChatGPT or Claude prompt.
- A document-grounded assistant such as NotebookLM.
- A static worksheet or target-trial protocol template.
- A human methodologist.

Nirvana must beat or complement the relevant alternative. If the simpler option is as useful with less burden, the simpler option becomes the product.

### 2.5 Specialist destinations (partners, not competitors)

- Domain Generalization Copilot (CHAI) for prediction under shift.
- DoWhy, EconML, causal-learn, DAGitty for analysis and graphs.
- Causal-Copilot or Causal AI Scientist when a dataset exists.

## 3. The gap

1. All agents in 2.1 assume a dataset plus a well-posed question. None decides whether a question is causal, which task class it belongs to, or that it is not a causal question at all.
2. The benchmarks in 2.2 draw questions from published papers, so the question is already expert-written. Nobody benchmarks the raw, under-specified version a novice actually asks.
3. CausalReasoningBenchmark shows that specification is where models fail (34% fully correct). CausalVerify explicitly excludes formulation. The bottleneck is named but not addressed.
4. Every system covers effect estimation or discovery. None covers prediction or generation under distribution shift, and none routes to a specialist tool such as DG Copilot.
5. No system teaches the missing concept to the person asking. Evaluation everywhere is model against gold labels; no real novice researchers are involved.
6. There is no shared, typed handoff object between a formulation step and the analysis agents.

## 4. Research focus: what Nirvana owns

| ID | Contribution | Why nobody else has it |
|---|---|---|
| F1 | **Task recognition and specification from under-specified questions.** A benchmark of novice-style research questions labelled with task class (effect, shift, discovery, mediation, policy, counterfactual, prediction, descriptive, unclear or not causal) and minimum specification fields, including ambiguous and multi-goal cases. Sources: CHAI researchers, degraded versions of published questions, CausalQuest-style collection. | Existing benchmarks use expert-written questions and one task class |
| F2 | **The Causal Research Brief as a handoff contract.** Feed the raw question and the Brief to Causal AI Scientist or Causal-Copilot; score the resulting specification with CausalReasoningBenchmark-style rubrics; validate a subset with human methodologists. Claim shape: a Brief raises an autonomous agent's specification correctness from X to Y. | No typed formulation-to-analysis contract exists |
| F3 | **Evaluation with real novices.** CHAI researchers compare Nirvana against a plain ChatGPT prompt and a static worksheet. Outcomes: blind-rated specification quality, teach-back understanding, routing correctness, time and burden. | No system in this space has been tested with target users |
| F4 | **Routing to specialist workflows, starting with shift to DG Copilot.** Recognise prediction-under-shift questions and prepare a reviewed handoff, with the tool owners as co-authors. | No formulation layer covers generalisation or routes to a specialist tool |
| F5 (optional) | **Just-in-time concept teaching linked to Portal**, measured as user understanding, separately from artifact quality. | Existing tools automate; none teaches |

Suggested order: F1 first as a short paper or workshop submission, because the benchmark angle can be taken by others within months. F2 and F3 together as the main user-study paper after the MVP release. F4 runs alongside with Damian and Kurt.

## 5. Out of scope: what we do not build

| Do not build | Who already does it | What we do instead |
|---|---|---|
| Automated causal discovery, effect estimation, or method selection over data | Causal-Copilot, Causal AI Scientist, LLM4Causal, DoWhy, EconML | Hand off a Brief; consume their output if needed |
| Analysis code generation | THESEUS, CausalVerify-style workflows | Route to them for the effect branch |
| Confounder, instrument, or DAG suggestion engines | pywhy-llm | Call it if a step needs it |
| Feasibility, stability, or deployment-strategy reasoning for shift problems | DG Copilot | Prepare the handoff; never duplicate the framework |
| General causal-reasoning question answering or a causal chatbot | CLadder and CausalBench territory; collapses into "ChatGPT plus a system prompt" | Keep the flow task-bound and artifact-bound |
| Identification proofs, estimand derivation, estimator choice | Methodologists and the tools above | Stop at the specification and one bounded next step |
| A general tutor, LMS, retrieval over the user's papers, multi-agent orchestration, long-term memory | Many | Add only when an observed failure requires it |
| Individual clinical advice, verification of literature claims, claims of learning effect before it is measured | Not ours to claim | Say "designed to help"; show evidence when it exists |

## 6. One-line positioning and main risk

**Positioning:** We are not building another causal analysis agent; Causal-Copilot and Causal AI Scientist already exist. We build the layer they all assume, turning a novice's question into a specification and a route, and we are the only ones testing it with real researchers.

**Main risk:** this field updates monthly (CausalVerify appeared on 2026-09-07). The F1 benchmark angle could be taken within six months. Publish the benchmark short paper first, then the user study.

## 7. Sources

- Causal-Copilot: An Autonomous Causal Analysis Agent. https://arxiv.org/abs/2504.13263
- LLM4Causal: Democratized Causal Tools for Everyone via Large Language Model. https://arxiv.org/abs/2312.17122
- Causal Agent based on Large Language Model. https://arxiv.org/abs/2408.06849
- Causal AI Scientist: Facilitating Causal Data Science with Large Language Models. https://openreview.net/forum?id=EDWTHMVOCj and https://github.com/causalNLP/causal-agent
- pywhy-llm. https://github.com/py-why/pywhyllm
- CausalReasoningBenchmark. https://arxiv.org/abs/2602.20571
- CauSciBench. https://openreview.net/pdf?id=EO8mTLqDuT
- InterveneBench. https://arxiv.org/abs/2603.15542
- CausalVerify. https://arxiv.org/abs/2609.07944
- CausalQuest: Collecting Natural Causal Questions for AI Agents. https://neurips.cc/virtual/2024/100297
- THESEUS: From study design to executable code, automating target trial emulation with LLMs. https://academic.oup.com/jamiaopen/article/9/4/ooag131/8729191
- Large Language Models as Co-Pilots for Causal Inference in Medical Studies. https://arxiv.org/abs/2407.19118
- Causal MAS: A Survey of LLM Architectures for Discovery and Effect Estimation. https://arxiv.org/pdf/2509.00987
- LLM-based Agents for Automated Confounder Discovery and Subgroup Analysis. https://arxiv.org/abs/2508.07221
- Causal Ensemble Agent. https://arxiv.org/abs/2606.10607
- Domain Generalization Copilot (CHAI). https://chai-uk.github.io/domain-generalization-copilot/
