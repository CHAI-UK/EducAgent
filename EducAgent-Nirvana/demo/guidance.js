// Original explanations with textbook section locators in lessons below.
// Shared by field help, framing and the bounded clarification checklist.
const NirvanaGuidance = {
  help: {
  "problem": "Describe the research decision, who or what is studied, and what you want to learn. Do not include patient identifiers.",
  "decision": "What decision would the result inform? For example, whether a hospital should offer a programme. This is the purpose, not the effect estimate.",
  "exposure": "Define the intervention or exposure, including dose, timing and eligibility where known. Lottery invitation and actual enrolment are different variables.",
  "comparator": "What is the explicit alternative: usual care, no exposure, or another dose? State it rather than assuming an untreated group exists.",
  "outcome": "Name the measured endpoint, its definition and units. For example, a positive depression screen, not simply better health.",
  "population": "Define eligibility, setting and the people the conclusion should concern. A study sample may differ from that target population.",
  "time": "State time zero and follow-up duration. For example, six months after assignment; avoid mixing baseline and post-treatment measurements.",
  "assumptions": "Record plausible causal assumptions and what might violate them: common causes, selection, measurement or missingness. These are not established by clicking Accept.",
  "prediction-target": "What should the model output, from which input, and for what use? For CTPA, clarify the desired non-contrast image/reference and how it will be used; do not assume image synthesis is diagnosis.",
  "candidate-predictors": "List the information actually available to the model and when it is measured: images, age, sex, scanner vendor. Separate recorded metadata from intended model inputs; training availability does not imply deployment availability.",
  "training-environment": "Describe where and how the training data were generated: hospitals, scanner vendors/protocols, recruitment, dates and patient mix. This is not your GPU, Python environment, operating system or training framework. Name only sites/vendors actually in the data.",
  "deployment-environment": "Describe where the model is intended to be used: new hospitals, scanners, protocols, patient groups or time periods. Distinguish desired coverage from observed training coverage. This is not the server hosting the model.",
  "shift-sources": "What may change between source and deployment data? For example, acquisition protocol, referral patterns or age distribution. Name suspected changes without declaring which causal mechanism is proven.",
  "predictor-roles": "Describe plausible directions: disease may affect image appearance; scanner settings may also affect appearance. Separate causes, consequences and proxies only when defensible; correlated metadata is not automatically a confounder.",
  "deployment-constraints": "Will target-site images, labels or metadata be available before deployment? Can the model be adapted, and with what privacy/compute restrictions? GPU limits belong here only if they constrain adaptation.",
  "shift-uncertainty": "What remains unverified: vendor coverage, paired reference images, stable mechanisms, evaluation criteria or safety of synthesis? Record unknowns rather than claiming causal modelling guarantees robustness.",
  "mediation-decision": "What mechanism would understanding the pathway clarify? State the scientific purpose separately from whether the treatment works overall.",
  "mediation-exposure": "Specify treatment and comparison, such as pain education plus exercise versus standard physiotherapy. Note assignment and receipt if different.",
  "mediator": "Name the proposed intermediate process and measurement time, such as fear of movement after treatment. It is a hypothesis, not an established pathway.",
  "mediation-outcome": "Define the later outcome, its scale and follow-up. It must be distinguishable from the proposed mediator.",
  "mediation-population": "Who is studied and to whom should the mechanism apply? Specify eligibility and clinical setting where known.",
  "mediation-effect": "Are you interested in total, direct or indirect effects? If unfamiliar, say that you want the part operating through the named mediator; the precise estimand can remain unresolved.",
  "mediation-time": "Put exposure, mediator and outcome in temporal order. Flag simultaneous measurement or feedback rather than assuming the order.",
  "mediation-uncertainty": "Record possible mediator-outcome common causes, including those affected by treatment, measurement error and temporal uncertainty. Randomising treatment does not randomise the mediator.",
  "descriptive-purpose": "What needs monitoring or summarising? A prevalence report describes observations; it does not explain what caused a change.",
  "descriptive-population": "Specify the cohort, eligibility and exclusions. For a population survey, distinguish participants from the population represented by weights.",
  "descriptive-measure": "Define the statistic and operational measurement: prevalence using a stated threshold, count, mean or rate. Include units where relevant.",
  "descriptive-denominator": "What is counted in the denominator: people, discharges, eligible scans or person-time? Explain repeated observations and exclusions.",
  "descriptive-strata": "Which breakdowns are needed, such as age, sex or hospital? Group differences alone do not establish discrimination or causality.",
  "descriptive-time": "State the calendar period and follow-up window. Repeated survey waves are not necessarily repeated measurements of the same individuals.",
  "descriptive-limitations": "Name the data source, survey weights if relevant, missingness, nonresponse and incomplete capture. Do not invent representativeness.",
  "discovery-purpose": "Which scientific relationships do you want to investigate? Distinguish learning directions from predicting diagnosis or estimating a specified effect.",
  "discovery-variables": "List measured variables, units, time points and candidate latent factors. Define what each node would represent before drawing arrows.",
  "discovery-data": "Describe observational versus experimental data, intervention targets if known, sample selection and repeated measures. Mention sample size only if known.",
  "discovery-knowledge": "Record supported temporal ordering, required/forbidden relationships and biological knowledge, with uncertainty. A preferred pathway is not a verified graph.",
  "discovery-uncertainty": "Could hidden common causes, selection, feedback or measurement error explain dependencies? Multiple graphs may fit the same data.",
  "policy-purpose": "Who makes the decision, for whom, and at which stage? Frame research on a decision rule, not an individual treatment prescription.",
  "policy-actions": "List eligible alternatives at each decision stage and the current policy. Include contraindications or unavailable actions if known.",
  "policy-objective": "What outcome or utility should the rule improve, over what horizon? Specify trade-offs and harms if agreed, not invented.",
  "policy-information": "What patient history is known before each choice? Exclude later outcomes to avoid information leakage into the decision rule.",
  "policy-constraints": "State capacity, budget, timing, eligibility or equity constraints. Unknown limits can remain unknown; do not assume a specific budget.",
  "policy-evidence": "What randomised or observational data inform how outcomes change under each action? High predicted risk is not the same as high treatment benefit.",
  "policy-uncertainty": "Record confounding, action overlap, missing history and whether a sequential rule can be evaluated. A learned policy still needs clinical validation.",
  "cf-purpose": "Identify the observed case and why its alternative is useful. Use de-identified descriptions; do not provide patient identifiers.",
  "cf-observed": "What was actually observed for this case: exposures, measurements and outcome? Separate observations from inferred background factors.",
  "cf-intervention": "Precisely which variable is hypothetically set to which alternative value? Distinguish changing a causal mechanism from editing a correlated image feature.",
  "cf-target": "What alternative outcome or image is requested for the same case? This is not simply predicting an unobserved person.",
  "cf-model": "What structural relationships and background factors would be retained? State which are assumed or learned; these determine the hypothetical answer.",
  "cf-uncertainty": "Record ambiguity in the structural model and case-level inference. A plausible generated MRI is not a verified alternative clinical outcome.",
  "prediction-purpose": "Who will use the prediction, for which patients, and at what decision point? Prediction alone need not estimate a causal effect.",
  "prediction-outcome": "Define the label and horizon: e.g. unplanned readmission within 30 days after discharge. Specify how it is measured.",
  "prediction-inputs": "Which variables are available at the prediction moment? Exclude future notes, outcomes and other leakage.",
  "prediction-data": "Describe training and held-out evaluation cohorts, sites and dates. Keep patients separated across splits when observations repeat.",
  "prediction-evaluation": "What metrics and validation plan match intended use: discrimination, calibration, error or subgroup reporting? Do not equate one accuracy score with clinical usefulness.",
  "prediction-uncertainty": "List missing data, outcome capture, leakage and generalisation concerns. Unknown deployment robustness is not evidence of robustness."
},
  lessons: {
  "effect": {
    "concept": "Intervention versus observation",
    "text": "Comparing observed groups is not automatically the same as changing treatment. A common cause can influence both exposure and outcome. Make the intervention, alternative and population explicit before asking how the outcome would change.",
    "sections": "3.2; 6.6; 9.2",
    "keys": [
      "exposure",
      "comparator",
      "outcome"
    ],
    "check": "In your study, what would be changed, what is the alternative, and what could influence both exposure and outcome?"
  },
  "shift": {
    "concept": "Environment, mechanism and invariance",
    "text": "An environment describes how data are produced, not the computer used for training. Patient mix and acquisition can change separately. A causal approach asks which relationships might survive those changes; it does not guarantee they will. Synthesis needs its own target and evaluation, not automatic reuse of a classification solution.",
    "sections": "2.1; 5.2; 8.3",
    "keys": [
      "prediction-target",
      "training-environment",
      "deployment-environment",
      "shift-sources"
    ],
    "check": "For your data, name one change you expect at deployment and one relationship you think might remain stable. What evidence would challenge that belief?"
  },
  "mediation": {
    "concept": "An intermediate pathway",
    "text": "A mediator is proposed to lie between an exposure and an outcome. The total effect and the part operating through that pathway are different questions. Random treatment assignment alone does not resolve mediator-outcome confounding.",
    "sections": "3.2; 6.2; 6.6 (foundations; mediation explanation is our synthesis)",
    "keys": [
      "mediation-exposure",
      "mediator",
      "mediation-outcome"
    ],
    "check": "Why do you place the proposed mediator after treatment and before the outcome? What else could affect both mediator and outcome?"
  },
  "descriptive": {
    "concept": "Description is a valid destination",
    "text": "A frequency or trend summarises what was observed in a defined population and period. It needs clear measurement, denominators and sampling information, but no intervention contrast unless the research goal changes.",
    "sections": "1.1; 1.3",
    "keys": [
      "descriptive-population",
      "descriptive-measure",
      "descriptive-time"
    ],
    "check": "What exactly is counted, and who or what belongs in the denominator?"
  },
  "discovery": {
    "concept": "Graphs express assumptions",
    "text": "An arrow represents a proposed direct causal relation, not just a correlation. Observational data may support several compatible graphs. Timing, interventions and domain knowledge help constrain the possibilities but do not remove all uncertainty.",
    "sections": "6.1; 6.8; 7.1; 9.4",
    "keys": [
      "discovery-variables",
      "discovery-data",
      "discovery-knowledge"
    ],
    "check": "Which ordering comes from prior knowledge, and which direction do you actually want the data to investigate?"
  },
  "policy": {
    "concept": "Predicting risk versus choosing an action",
    "text": "A policy maps information available at a decision to an action. Someone with high predicted risk is not necessarily the person who benefits most from treatment. Sequential policies must respect what is known at each stage.",
    "sections": "3.2; 8.2",
    "keys": [
      "policy-actions",
      "policy-objective",
      "policy-information"
    ],
    "check": "At one decision point, what is already known, what actions are possible, and what later outcome matters?"
  },
  "counterfactual": {
    "concept": "The same case under a different intervention",
    "text": "A counterfactual combines an observed case with assumptions about how its outcome is generated. The model uses that evidence, changes a specified mechanism, and reasons about the alternative while retaining relevant background factors. Image realism alone does not validate this reasoning.",
    "sections": "3.1–3.3; 6.4",
    "keys": [
      "cf-observed",
      "cf-intervention",
      "cf-target"
    ],
    "check": "What would change for this same case, and what do you assume stays the same?"
  },
  "prediction": {
    "concept": "Prediction is not an intervention effect",
    "text": "A model can forecast outcomes from information available now without establishing what would happen if you changed a variable. Validation must resemble the intended use and avoid future information leaking into inputs.",
    "sections": "1.2; 1.3; 5.2",
    "keys": [
      "prediction-outcome",
      "prediction-inputs",
      "prediction-data"
    ],
    "check": "At the prediction moment, which inputs are genuinely available and which are only learned later?"
  }
}
};
if (typeof module !== "undefined") module.exports = NirvanaGuidance;
