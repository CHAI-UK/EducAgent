// Curated navigation, not adapters or scientific endorsements. Checked 2026-09-11.
const NirvanaDestinations = {
  "effect": [
    {
      "name": "DAGitty",
      "url": "https://www.dagitty.net/",
      "about": "Browser-based drawing and analysis of causal diagrams.",
      "inputs": "Define nodes, exposure, outcome and defensible arrows, including possible hidden common causes.",
      "next": "Use the Brief to sketch a provisional graph with a methodologist, then inspect adjustment implications.",
      "limit": "Graph analysis is conditional on your assumptions; it does not discover the true graph or estimate effects.",
      "fields": [
        "exposure",
        "outcome",
        "assumptions"
      ]
    },
    {
      "name": "DoWhy",
      "url": "https://www.pywhy.org/dowhy/v0.13/user_guide/causal_tasks/index.html",
      "about": "Python workflow for modelling, identifying, estimating and challenging causal effects.",
      "inputs": "An analysis dataset, treatment/outcome column names and a supported identification model.",
      "next": "Translate the reviewed contrast and assumptions into an analysis specification before fitting anything.",
      "limit": "A written Brief is preparation, not executable input; identification and estimator choice need review.",
      "fields": [
        "exposure",
        "comparator",
        "outcome",
        "population",
        "assumptions"
      ]
    }
  ],
  "shift": [
    {
      "name": "Domain Generalization Copilot",
      "url": "https://chai-uk.github.io/domain-generalization-copilot/",
      "about": "Interactive causal-framing workflow for prediction under data shifts: variables, augmented graph, feasibility and candidate deployment strategies.",
      "inputs": "Prediction target, variables, source/deployment environments, graph assumptions, suspected shifts and data availability.",
      "next": "Keep the copied notes beside the tool; enter these details into its forms and review the graph and feasibility questions there.",
      "limit": "No prompt-paste import. Suitability for CTPA image synthesis must be checked; Nirvana does not reproduce DG reasoning.",
      "fields": [
        "prediction-target",
        "candidate-predictors",
        "training-environment",
        "deployment-environment",
        "shift-sources",
        "deployment-constraints"
      ]
    },
    {
      "name": "DomainBed",
      "url": "https://github.com/facebookresearch/DomainBed",
      "about": "Python research benchmark for comparing domain-generalisation algorithms.",
      "inputs": "Prepared datasets split into environments, labels, model configuration and evaluation protocol.",
      "next": "Ask an ML researcher to turn your environments into held-out-domain evaluations and appropriate baselines.",
      "limit": "Not a causal identification tool or a ready-made medical image-synthesis pipeline.",
      "fields": [
        "training-environment",
        "deployment-environment",
        "shift-sources",
        "prediction-target"
      ]
    }
  ],
  "mediation": [
    {
      "name": "mediation (R)",
      "url": "https://cran.r-project.org/web/packages/mediation/index.html",
      "about": "Causal mediation estimation, with sensitivity analysis for supported model combinations.",
      "inputs": "Treatment and mediator names, analysis data, fitted mediator and outcome models, and a justified causal estimand.",
      "next": "Review timing and mediator-outcome confounding with a specialist before specifying the two models.",
      "limit": "Randomising treatment does not randomise the mediator; not every longitudinal pathway is supported.",
      "fields": [
        "mediation-exposure",
        "mediator",
        "mediation-outcome",
        "mediation-effect",
        "mediation-time",
        "mediation-uncertainty"
      ]
    }
  ],
  "descriptive": [
    {
      "name": "survey (R)",
      "url": "https://r-survey.r-forge.r-project.org/survey/",
      "about": "Analysis of complex surveys, including weighted means, totals and subgroup summaries.",
      "inputs": "Data, outcome definitions and survey design information such as weights, strata and cluster IDs.",
      "next": "Map the population, denominator and reporting periods to a survey-design specification, then check missingness.",
      "limit": "Use when the sampling design warrants it. A descriptive report does not establish a causal effect.",
      "fields": [
        "descriptive-population",
        "descriptive-measure",
        "descriptive-denominator",
        "descriptive-strata",
        "descriptive-limitations"
      ]
    }
  ],
  "discovery": [
    {
      "name": "causal-learn",
      "url": "https://causal-learn.readthedocs.io/en/latest/",
      "about": "Python implementations of causal structure discovery methods.",
      "inputs": "A prepared variable matrix, variable types, supported discovery/test choices and relevant prior constraints.",
      "next": "Translate measured variables and temporal knowledge into a data dictionary; compare algorithms whose assumptions fit the study.",
      "limit": "Compatible graphs are candidates, not proof. Hidden causes, selection and measurement error affect interpretation.",
      "fields": [
        "discovery-variables",
        "discovery-data",
        "discovery-knowledge",
        "discovery-uncertainty"
      ]
    }
  ],
  "policy": [
    {
      "name": "policytree (R)",
      "url": "https://grf-labs.github.io/policytree/",
      "about": "Learns interpretable action-selection trees from estimated rewards.",
      "inputs": "Decision-time features and per-action reward scores, supported action-effect evidence, and an evaluation split.",
      "next": "For a single decision, agree actions and utility, then work with a specialist to estimate rewards and evaluate the rule.",
      "limit": "Not a plug-in solution for the sequential STAR*D example. Sequential decisions require a dynamic-treatment-regime specialist; no clinical deployment claim.",
      "fields": [
        "policy-actions",
        "policy-objective",
        "policy-information",
        "policy-evidence",
        "policy-constraints"
      ]
    }
  ],
  "counterfactual": [
    {
      "name": "DoWhy GCM",
      "url": "https://www.pywhy.org/dowhy/v0.13/user_guide/causal_tasks/what_if/counterfactuals.html",
      "about": "Computes model-dependent counterfactuals using a structural causal model.",
      "inputs": "A suitable fitted structural model, observed case or background-noise values, and a specified intervention.",
      "next": "First specify which mechanisms change and which background factors are retained, then assess whether the model supports case-level inference.",
      "limit": "Counterfactual identification is stronger than plausible generation; the Brief alone cannot fit or validate the model.",
      "fields": [
        "cf-observed",
        "cf-intervention",
        "cf-target",
        "cf-model"
      ]
    },
    {
      "name": "DeepSCM research code",
      "url": "https://github.com/biomedia-mira/deepscm",
      "about": "Research implementation of deep structural causal models, including brain-image experiments.",
      "inputs": "Compatible prepared data, a structural model, trained parameters and compute; see repository experiment requirements.",
      "next": "Use as a research reference for the MRI example, with a specialist reviewing the structural assumptions and data match.",
      "limit": "Not a general medical imaging product or a drop-in CTPA converter. Generated alternatives remain model-dependent.",
      "fields": [
        "cf-target",
        "cf-intervention",
        "cf-model",
        "cf-uncertainty"
      ]
    }
  ],
  "prediction": [
    {
      "name": "scikit-learn",
      "url": "https://scikit-learn.org/stable/model_selection.html",
      "about": "Python predictive modelling, model selection and evaluation tools.",
      "inputs": "Features available at prediction time, labels, patient/group identifiers, split rules and metrics.",
      "next": "Turn the target and timing into labels, prevent patient/future-data leakage, then implement a held-out validation plan.",
      "limit": "Predictive accuracy is not a treatment effect or proof of clinical usefulness. Imaging may need a separate model framework.",
      "fields": [
        "prediction-outcome",
        "prediction-inputs",
        "prediction-data",
        "prediction-evaluation"
      ]
    }
  ]
};
