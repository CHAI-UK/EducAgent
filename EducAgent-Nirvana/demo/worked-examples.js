// Paper-anchored teaching specifications; provenance distinguishes authored choices.
const NirvanaWorkedExamples = {
  "effect": {
    "problem": "## Research question\nDoes Medicaid coverage change the probability of a positive depression screen among low-income adults?\n\n## Published study setting\nBaicker et al. (2013) studied Oregon's 2008 lottery offering an opportunity to apply for Medicaid. Depression was assessed using PHQ-8 approximately two years later. Lottery selection and actual insurance enrollment are different variables.\n\n## Educational analysis plan\nFor this worked example, focus on depression rather than the paper's entire outcome set. Define the coverage contrast, separate it from the effect of the lottery offer, and explain which population an instrumental-variable estimate concerns. Before estimating anything, assess the instrument assumptions and discuss nonresponse and generalisability. This is a paper-based teaching specification, not a new analysis or a statement that the assumptions have been verified for another dataset.",
    "fields": {
      "decision": "Teaching focus: estimate a coverage effect on depression screening, separately reporting the lottery-offer contrast. This is effect estimation, not an individual treatment rule.",
      "exposure": "Medicaid enrollment; lottery selection is an instrument, not equivalent to receiving coverage.",
      "comparator": "No Medicaid enrollment for the coverage contrast; nonselection for the separate lottery-offer contrast.",
      "outcome": "Positive depression screen: PHQ-8 score at least 10, not a clinical diagnosis.",
      "population": "Low-income uninsured adults eligible for Oregon Health Plan Standard; the in-person study sampled the Portland metropolitan area. Teaching estimand: coverage compliers under the stated IV assumptions, not all US adults.",
      "time": "Interviews averaged 25 months after the lottery began, during September 2009–December 2010.",
      "assumptions": "Paper analysis uses lottery selection as an instrument, adjusts for household list size, clusters by household and uses design weights. Teaching checklist: assess relevance, conditional random assignment, exclusion and monotonicity; distinguish assumptions from observed facts. Examine missing outcomes and whether conclusions transfer outside this population. Do not compare enrollees and non-enrollees as if enrollment itself were random. Data access and an executable analysis are not supplied by this example."
    },
    "provenance": [
      {
        "fields": [
          "exposure",
          "comparator",
          "outcome",
          "population",
          "time",
          "assumptions"
        ],
        "status": "paper-reported",
        "source": "Baicker et al. (2013), The Oregon Experiment—Effects of Medicaid on Clinical Outcomes, Methods and Table 2",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC3701298/",
        "note": "Supports study setting, measurement and reported analysis design; does not establish assumptions for a new dataset."
      },
      {
        "fields": [
          "decision",
          "population",
          "assumptions"
        ],
        "status": "teaching-assumption",
        "source": "Nirvana educational framing based on the cited study",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC3701298/",
        "note": "Depression-only focus, explicit complier target and diagnostic checklist are educational choices; not new empirical findings."
      }
    ]
  },
  "shift": {
    "problem": "## Research question\nCan a prostate MRI segmentation model remain reliable at centres absent from its training data?\n\n## Published study setting\nOuyang et al. studied single-source generalisation, including a six-centre prostate MRI benchmark. Their method perturbs appearance and weakens misleading image correlations using causality-inspired augmentation.\n\n## Educational analysis plan\nWe want a research segmentation tool, not autonomous clinical deployment. Separate anatomical information from acquisition-related appearance, state which relationships we hypothesise will remain stable, and compare causality-inspired augmentation with an ordinary training baseline. Use centre-separated evaluation, examine individual-centre failures and keep tuning independent of target outcomes. We have not selected a new hospital or a clinical acceptance threshold. Please frame this as a robustness study, not a guarantee that a causal method will transfer, and help distinguish data-collection environments from computing hardware.",
    "fields": {
      "prediction-target": "Prostate segmentation mask from MRI. Teaching intended use: research delineation with human inspection, not autonomous diagnosis.",
      "candidate-predictors": "MRI pixels at inference; reference segmentation masks supervise training. Teaching choice: centre IDs are evaluation strata rather than predictive inputs; do not supply target masks to the model.",
      "training-environment": "One acquisition centre per experiment; source split 70% training, 10% validation and 20% testing. Environment means the image-generating setting, not GPU or Python version.",
      "deployment-environment": "The other five centres are held-out targets; rotate the source across all six centres. A new clinical hospital is not specified in this teaching scenario.",
      "shift-sources": "Acquisition-related intensity/texture differences and image correlations that may not transfer. Teaching audit: additionally check annotation conventions and case mix rather than assuming appearance is the only change.",
      "predictor-roles": "Teaching causal hypothesis: anatomy contributes to image content and the desired mask; acquisition affects appearance. Contextual appearance can be a shortcut. Ask domain experts to challenge this provisional model; centre membership alone does not identify a causal mechanism.",
      "deployment-constraints": "Single-source setting: no target data during training or target fine-tuning; target labels are for evaluation. Teaching constraint: keep hyperparameter selection source-only and record any departure as a different protocol.",
      "shift-uncertainty": "The paper evaluates Dice overlap against an ERM baseline. Teaching additions: report each centre and uncertainty, inspect clinically relevant boundary failures, and assess whether augmentations preserve labels. A clinical acceptance threshold is unresolved; benchmark performance does not certify safety or unseen-hospital robustness."
    },
    "provenance": [
      {
        "fields": [
          "prediction-target",
          "candidate-predictors",
          "training-environment",
          "deployment-environment",
          "shift-sources",
          "deployment-constraints",
          "shift-uncertainty"
        ],
        "status": "paper-reported",
        "source": "Ouyang et al., Causality-inspired Single-source Domain Generalization for Medical Image Segmentation, Sections III, IV-A and V; TMI 2023 / author preprint",
        "url": "https://arxiv.org/html/2111.12525",
        "note": "Supports segmentation, acquisition-shift motivation, source/target protocol and reported metric/baseline."
      },
      {
        "fields": [
          "prediction-target",
          "candidate-predictors",
          "shift-sources",
          "predictor-roles",
          "deployment-constraints",
          "shift-uncertainty"
        ],
        "status": "teaching-assumption",
        "source": "Nirvana educational study-design choices",
        "url": "https://pubmed.ncbi.nlm.nih.gov/36417741/",
        "note": "Human-inspected research use, centre-ID role, explicit causal hypothesis, extra audits and evaluation safeguards are proposed teaching choices, not reported paper requirements or validated graph edges."
      },
      {
        "fields": [
          "deployment-environment",
          "shift-uncertainty"
        ],
        "status": "not-reported",
        "source": "Unresolved scope of this educational adaptation",
        "url": "https://pubmed.ncbi.nlm.nih.gov/36417741/",
        "note": "No new destination hospital or clinical acceptance threshold is supplied. These remain user decisions, not blanks to fabricate from a benchmark paper."
      }
    ]
  },
  "mediation": {
    "problem": "## Worked learning example: pain-treatment mechanisms\n\nMurillo et al. (2023) analysed a randomised primary-care trial comparing pain neuroscience education plus exercise with standard physiotherapy for chronic spinal pain. Candidate mediators were measured after treatment; disability was measured at six months. Their analysis considered kinesiophobia, catastrophizing, central sensitization-related distress, pain intensity and earlier disability, including possible mediator interactions.\n\nFor this teaching exercise, we prioritise whether changing fear of movement could explain part of the treatment effect on later disability. Our provisional estimand is the mean disability difference under the education-plus-exercise assignment when fear-of-movement values are drawn from its distribution under each treatment arm. This is an illustrative interventional indirect-effect question, not a claim to reproduce the paper's estimator. A specialist must specify how the other mediators are handled before estimation.\n\nThe intended population is the trial's chronic-spinal-pain primary-care participants, not all patients. Treatment precedes the mediator assessment, which precedes the final outcome. Randomisation does not itself remove mediator-outcome confounding. As teaching assumptions to investigate, we propose consistency, overlap, adequate pretreatment confounder measurement, an explicit dependence model for the mediators, and a plan for missing follow-up. The exact adjustment set and implementation remain decisions for a protocol review, not established facts. How should we frame this mechanism question?",
    "fields": {
      "mediation-decision": "Teaching focus: investigate a treatment mechanism, rather than only whether the treatment works; use fear of movement as the focal pathway.",
      "mediation-exposure": "Randomised assignment: pain neuroscience education plus exercise versus standard physiotherapy.",
      "mediator": "Post-treatment kinesiophobia (fear of movement). Other measured candidates include catastrophizing, sensitization-related distress, pain intensity and earlier disability; dependence matters.",
      "mediation-outcome": "Disability at six-month follow-up.",
      "mediation-population": "Chronic spinal pain participants in the primary-care trial.",
      "mediation-effect": "Teaching estimand: under education-plus-exercise assignment, compare mean disability when fear-of-movement values are drawn from their distribution under each arm. This illustrative interventional indirect contrast is not the paper's verified estimand; specify the joint handling of other mediators first.",
      "mediation-time": "Treatment assignment, then post-treatment mediators, then six-month outcome.",
      "mediation-uncertainty": "Teaching review assumptions, not verified study facts: consistency, overlap and sufficient pretreatment mediator-outcome confounder measurement. Randomising treatment does not randomise the mediator. Review mediator dependence, treatment-induced confounding, measurement error and missing follow-up. Exact adjustment set, scale coding and estimator implementation need the full methods and a reviewed protocol."
    },
    "provenance": [
      {
        "fields": [
          "mediation-exposure",
          "mediator",
          "mediation-outcome",
          "mediation-population",
          "mediation-time"
        ],
        "status": "paper-reported",
        "source": "Murillo et al. (2023), Pain; abstract",
        "url": "https://pubmed.ncbi.nlm.nih.gov/37289577/",
        "note": "Design anchors paraphrased; no numerical findings copied."
      },
      {
        "fields": [
          "mediation-decision",
          "mediation-effect",
          "mediation-uncertainty"
        ],
        "status": "teaching-assumption",
        "source": "Nirvana authored teaching adaptation; not a paper result",
        "url": "https://pubmed.ncbi.nlm.nih.gov/37289577/",
        "note": "The focal estimand and methodological checklist are illustrative decisions for review, not a reconstruction of the study's analysis. The question intentionally retains mediator-dependence uncertainty."
      },
      {
        "fields": [
          "mediation-effect",
          "mediation-uncertainty"
        ],
        "status": "not-reported",
        "source": "Limits of the inspected abstract",
        "url": "https://pubmed.ncbi.nlm.nih.gov/37289577/",
        "note": "Exact estimator, adjustment set and scale coding were not established from the abstract inspected here; this does not imply that the full paper omits them."
      }
    ]
  },
  "descriptive": {
    "problem": "## Worked learning example: adult obesity surveillance\n\nAdapt the adult analysis in Hales et al. (2018): describe NHANES obesity trends across five two-year cycles, 2007-2008 through 2015-2016. The target is US civilian, noninstitutionalized adults aged at least 20, excluding pregnancy. Define obesity as BMI >=30 and severe obesity as BMI >=40 kg/m2 using measured height and weight. Report prevalence and confidence intervals by sex and ages 20-39, 40-59 and 60+, accounting for examination weights and complex sampling.\n\nFor our educational reporting plan, use each cycle's eligible measured sample as the analytic denominator, not the number of people already classified as obese; weights connect that sample to the population. We will distinguish sample counts from population percentages, publish an explicit exclusion and missing-measurement audit, and label crude versus age-standardized outputs. These reporting choices are our teaching specification, not a new analysis result.\n\nRepeated cross-sectional surveys describe different samples over time: they do not trace an individual's weight trajectory or identify a treatment effect. Potential nonresponse bias remains despite weighting. Our next step is a survey-aware descriptive table, with uncertainty and subgroup denominators, not a causal model. How should this be represented in a Brief?",
    "fields": {
      "descriptive-purpose": "Monitor obesity prevalence over time; description, not an intervention-effect estimate.",
      "descriptive-population": "US civilian, noninstitutionalized adults aged 20+; pregnancy excluded.",
      "descriptive-measure": "Measured BMI: obesity >=30, severe obesity >=40 kg/m2; prevalence with confidence intervals.",
      "descriptive-denominator": "Teaching specification: eligible adults with usable BMI in each cycle/subgroup. Report unweighted analytic counts separately from examination-weighted population percentages; audit exclusions and missing measurements.",
      "descriptive-strata": "Sex and age groups 20-39, 40-59 and 60+.",
      "descriptive-time": "Five two-year NHANES cycles: 2007-2008 through 2015-2016.",
      "descriptive-limitations": "Complex-survey examination weights are required; residual nonresponse bias is possible. Teaching checks: preserve design variables, label crude versus standardized summaries, report denominator changes and avoid interpreting repeated cross-sectional trends as individual trajectories or causal effects."
    },
    "provenance": [
      {
        "fields": [
          "descriptive-population",
          "descriptive-measure",
          "descriptive-strata",
          "descriptive-time",
          "descriptive-limitations"
        ],
        "status": "paper-reported",
        "source": "Hales et al. (2018), JAMA; Methods, Table 2 and Discussion",
        "url": "https://jamanetwork.com/journals/jama/fullarticle/2676543",
        "note": "Eligibility, measures, grouping, sampling and nonresponse anchors."
      },
      {
        "fields": [
          "descriptive-purpose",
          "descriptive-denominator",
          "descriptive-limitations"
        ],
        "status": "teaching-assumption",
        "source": "Nirvana authored teaching adaptation; not a new empirical finding",
        "url": "https://jamanetwork.com/journals/jama/fullarticle/2676543",
        "note": "The adult-only learning task and explicit audit/reporting checklist are a worked specification; no analysis is executed or prevalence result invented."
      }
    ]
  },
  "adni_discovery": {
    "problem": "## Research question\nWe want to investigate candidate causal directions among Alzheimer's biomarkers and diagnosis, rather than predict diagnosis. This teaching study is based on Shen et al. (2020): ADNI observations at baseline and 24 months, with FCI and FGES compared against a literature-derived reference graph.\n\n## Worked-study choices\nFor this educational extension, we would create a variable dictionary, separate each measurement occasion, and document every prohibited edge before fitting. We would compare results with and without these restrictions, report unresolved directions, and ask an Alzheimer's specialist to review contradictions. These are proposed workflow choices, not a new analysis or a claim that the reference graph is true.\n\n## What we need to learn\nHow should we combine observational measurements with temporal and biological knowledge to obtain reviewable candidate graphs? How should we distinguish stable associations, algorithm-dependent directions and evidence still needed for causal interpretation? We have not selected a new data release or a prospective intervention; those are explicit decisions for a real follow-on study.",
    "fields": {
      "discovery-purpose": "Teaching goal: produce candidate causal structures and a transparent assumption log, not a diagnostic predictor or a proven biological mechanism.",
      "discovery-variables": "Paper: FDG-PET, CSF amyloid beta and phosphorylated tau, APOE epsilon4, age, sex, education and diagnosis; repeated biomarkers/diagnosis are time-indexed.",
      "discovery-data": "Paper: ADNI 1 and 2/GO; 1,008 participants with a complete record, 266 with two-year follow-up; missing records excluded; 100 participant-level bootstrap samples. No experimental intervention is introduced by this discovery analysis.",
      "discovery-knowledge": "Paper: compare no restrictions, demographic restrictions, and additional prohibition of later-to-earlier edges. Teaching choice: audit each constraint independently rather than copying a reference graph as unquestionable ground truth.",
      "discovery-uncertainty": "Paper: selection artifacts, small longitudinal samples, latent confounding and reference-graph uncertainty matter. Teaching extension: preserve equivalence/ambiguous edges; assess preprocessing and missing-data sensitivity before proposing experiments. A new data-release choice and independently justified measurement-error model remain unresolved."
    },
    "provenance": [
      {
        "fields": [
          "discovery-variables",
          "discovery-data",
          "discovery-knowledge",
          "discovery-uncertainty"
        ],
        "status": "paper-reported",
        "source": "Shen et al. (2020), Scientific Reports: Methods and Discussion",
        "url": "https://www.nature.com/articles/s41598-020-59669-x",
        "note": "Only text prefixed Paper reports the source; explanatory research-design additions are labelled separately. The reported reference graph is an evaluation assumption, not certified truth."
      },
      {
        "fields": [
          "discovery-purpose",
          "discovery-knowledge",
          "discovery-uncertainty"
        ],
        "status": "teaching-assumption",
        "source": "Nirvana authored teaching extension",
        "url": "https://www.nature.com/articles/s41598-020-59669-x",
        "note": "The audit log, independent specialist review and sensitivity workflow are illustrative next-study choices, not claimed paper findings."
      },
      {
        "fields": [
          "discovery-uncertainty"
        ],
        "status": "not-reported",
        "source": "New-study decisions outside this worked example",
        "url": "https://www.nature.com/articles/s41598-020-59669-x",
        "note": "A new release identifier and a justified measurement-error model are not supplied for the proposed extension; they must not be silently inferred."
      }
    ]
  },
  "depression_policy": {
    "problem": "## Research question\nWe want to learn a sequence of treatment-selection rules for major depression using the STAR*D setting of Pineau et al. (2007). The paper optimises decisions at stages 2–4 after initial citalopram, using treatment history, symptom measurements and patient preferences. This is policy research, not advice for an individual.\n\n## Worked-study choices\nFor this teaching extension, our output is a research-only dynamic regime: at each stage it maps information already observed to an eligible action. We would keep patient preference and eligibility as restrictions, compare the learned sequence with a prespecified comparator regime, and estimate the whole sequence's value rather than choose whichever action correlates with the best outcome.\n\n## Remaining study design\nWe propose an independent evaluation split and uncertainty reporting as teaching choices. A clinician and trial statistician must review the reward, missingness, support for each history/action combination and whether the randomisation actually identifies the comparisons we want. We have not chosen cost or adverse-effect utility weights, and we will not claim the learned rule is ready for clinical deployment.",
    "fields": {
      "policy-purpose": "Teaching goal: learn a research-only dynamic treatment regime for trial-like adults with persistent depression; distinguish treatment assignment from risk prediction.",
      "policy-actions": "Paper: stage 2 offers bupropion-SR, sertraline, venlafaxine-XR or cognitive therapy as switches, or citalopram augmented with bupropion-SR, buspirone or cognitive therapy. Stage 3: mirtazapine/nortriptyline switches or lithium/thyroid augmentation. Stage 4: tranylcypromine versus mirtazapine plus venlafaxine-XR.",
      "policy-objective": "Paper: terminal remission reward is 1 for exit QIDS-SR16 <= 5, otherwise 0, through stage 4; earlier remission receives no extra credit.",
      "policy-information": "Paper: baseline QIDS-SR16, earlier symptom-score slopes, previous treatments and switch/augmentation preference. Teaching rule: never use measurements collected after the decision being evaluated.",
      "policy-constraints": "Teaching choice: preserve stage eligibility, acceptability and clinical oversight; no autonomous recommendations. Cost, capacity and adverse-effect utility weights need stakeholder decisions rather than invented numbers.",
      "policy-evidence": "Paper: sequential trial data with randomisation inside acceptable treatment options; initial citalopram is common to everyone. Teaching extension: validate a prespecified policy comparison with a dynamic-regime specialist, accounting for selection into preference groups.",
      "policy-uncertainty": "Teaching checklist: sparse histories/actions, dropout, unavailable outcomes, model dependence, support and transport to other clinics. Use held-out policy evaluation and uncertainty estimates; these are proposed evaluation steps, not evidence that an optimal clinical rule has been established."
    },
    "provenance": [
      {
        "fields": [
          "policy-actions",
          "policy-objective",
          "policy-information",
          "policy-evidence"
        ],
        "status": "paper-reported",
        "source": "Pineau et al. (2007), sections 4.1–4.2",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC1934348/",
        "note": "Paper-prefixed text describes the historical study and reward. These action names are research specifications, not contemporary prescribing recommendations."
      },
      {
        "fields": [
          "policy-purpose",
          "policy-information",
          "policy-constraints",
          "policy-evidence",
          "policy-uncertainty"
        ],
        "status": "teaching-assumption",
        "source": "Nirvana authored teaching extension",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC1934348/",
        "note": "The comparator, independent evaluation, decision-time audit and review requirements are proposed teaching choices, not a reproduced analysis or a claimed trial result."
      },
      {
        "fields": [
          "policy-constraints"
        ],
        "status": "not-reported",
        "source": "New-study utility and feasibility decisions",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC1934348/",
        "note": "The proposed extension has no numerical budget, capacity or adverse-effect weights; these remain open rather than being filled with fictional facts."
      }
    ]
  },
  "brain_cf": {
    "problem": "## Research question\nFor the same observed person, what would their brain MRI have looked like if ventricle volume had been different?\n\n## Published study setting\nPawlowski et al. (2020) demonstrate a deep structural causal model using UK Biobank brain MRI, age, sex, brain volume and ventricle volume. Their counterfactual procedure conditions on the observed case before changing a structural assignment.\n\n## Explicit fictional teaching case\nConsider a 60-year-old participant recorded as female, with total brain volume 1100 mL and ventricle volume 30 mL. Suppose a corresponding preprocessed MRI is available in an approved research dataset; no actual scan is attached to this demo. Ask for the model-implied image under do(ventricle volume = 40 mL), compared with this participant's factual image. Keep the same inferred exogenous state and propagate the intervention through the assumed model. The numbers are invented for learning, not extracted from a paper participant. We want a research illustration and difference map, not a disease forecast or treatment recommendation. Is this counterfactual well specified, and what assumptions would make it defensible?",
    "fields": {
      "cf-purpose": "Teaching goal: visualise a same-person counterfactual MRI for one fictional participant, rather than predict a different patient or estimate a population treatment effect.",
      "cf-observed": "Fictional case: age 60 years, sex recorded as female, brain volume 1100 mL, ventricle volume 30 mL. Assume an associated preprocessed MRI in an approved research dataset. No real participant record or scan is supplied here.",
      "cf-intervention": "Teaching contrast: replace the ventricle-volume assignment with do(v = 40 mL); compare against the factual 30 mL case. This is a mathematical intervention, not a claim that a clinical procedure can set volume while leaving everything else unchanged.",
      "cf-target": "The model-implied MRI and its difference from the factual image for this same case; describe which anatomical features change and which remain preserved. Teaching evaluation: inspect image consistency, not only realism.",
      "cf-model": "Paper setup: a specified SCM with age, sex, brain and ventricle volumes and an image mechanism; infer case-specific noise, intervene, then generate. Brain volume depends on age and sex; ventricle volume depends on age and brain volume. Teaching requirement: retain the abducted state and unchanged mechanisms, not an independently resampled patient; inspect the complete graph and trained mechanism before implementation.",
      "cf-uncertainty": "The paper conditions causal interpretation on the assumed SCM and absence of unobserved confounding. Teaching checklist: assess graph and measurement validity, posterior uncertainty and support for the hypothetical volume. Image plausibility cannot establish the unobserved alternative as true. No trained model, individual scan, or observed counterfactual is provided by this demo; the stated case is only a complete input specification."
    },
    "provenance": [
      {
        "fields": [
          "cf-model",
          "cf-uncertainty"
        ],
        "status": "paper-reported",
        "source": "Pawlowski, Castro and Glocker (2020), Deep Structural Causal Models for Tractable Counterfactual Inference, Sections 2 and 5, Appendix B",
        "url": "https://arxiv.org/html/2006.06485",
        "note": "Supports brain-imaging variables, structural assignments and abduction/intervention/generation procedure; these are assumed model semantics, not a clinically validated intervention."
      },
      {
        "fields": [
          "cf-purpose",
          "cf-observed",
          "cf-intervention",
          "cf-target",
          "cf-model",
          "cf-uncertainty"
        ],
        "status": "teaching-assumption",
        "source": "Nirvana fictional worked case",
        "url": "https://arxiv.org/abs/2006.06485",
        "note": "All participant numbers, the 30-to-40 mL contrast and the proposed review checklist are invented teaching choices. No paper participant or image is reproduced."
      },
      {
        "fields": [
          "cf-observed",
          "cf-uncertainty"
        ],
        "status": "not-reported",
        "source": "Inputs not supplied by this demo",
        "url": "https://github.com/biomedia-mira/deepscm",
        "note": "A runnable analysis still requires authorised data, the complete model and fitted parameters; the Brief is not itself an image-generating model."
      }
    ]
  },
  "ehr_predict": {
    "problem": "## Research question\nCan EHR information available at discharge predict an adult patient's unplanned readmission within 30 days?\n\n## Published study setting\nRajkomar et al. (2018) studied hospital records at two US academic medical centres, evaluated each hospital separately, and included a discharge-time readmission prediction task. This provides a prediction example, not evidence that acting on a risk score prevents readmission.\n\n## Explicit educational design\nFor this worked example, plan a retrospective, silent evaluation in one hospital among adults with index stays lasting at least 24 hours. Use only information actually available before the discharge prediction timestamp. Predict readmissions captured by that hospital's records and disclose that outside-hospital events may be missed. Split by patient for development and use a later-period holdout, retaining only holdout patients absent from development. Compare a simple logistic baseline with a flexible model; assess discrimination, calibration and subgroup performance. We have not chosen a clinical alert threshold or any intervention. Help refine the prediction specification without turning it into a treatment-effect or cross-hospital generalisation claim.",
    "fields": {
      "prediction-purpose": "Teaching use: retrospective, silent readmission-risk evaluation for adult inpatients with stays of at least 24 hours at one hospital. No care assignment or autonomous discharge decision is requested.",
      "prediction-outcome": "Unplanned admission within 30 days after index discharge, predicted at discharge. Teaching operational definition: count events captured in the same hospital's records, exclude planned admissions by a prespecified coding rule, and explicitly report incomplete capture outside that system.",
      "prediction-inputs": "Teaching candidate inputs: age, prior encounters, diagnoses already recorded, medications, laboratory results and vital signs available by the prediction timestamp. Exclude future encounters, late-entered discharge coding and any post-discharge information. A timestamp audit must check actual availability rather than clinical event time alone.",
      "prediction-data": "Paper basis: two hospital datasets analysed separately. Teaching plan: use one hospital's authorised historical records; patient-disjoint development sets and a later-period holdout restricted to patients absent from development. Fit preprocessing only on training data. Specific hospital, calendar cutoffs and dataset access remain to be chosen.",
      "prediction-evaluation": "Teaching plan: compare logistic regression and a flexible predictor; report AUROC, precision-recall performance, calibration and uncertainty on untouched holdout data. Review age/sex subgroups and missing-data strata. Report event prevalence and exclusions. No clinical operating threshold or acceptable error trade-off has yet been agreed.",
      "prediction-uncertainty": "Teaching checks: missing outside-system readmissions, coding errors, missingness, repeated-admission leakage and delayed documentation. Patient-disjoint temporal evaluation may change the evaluated population and should be reported. Predictive accuracy neither identifies causes nor shows that intervening on a high-risk patient improves outcomes. Do not infer causal importance from feature attribution."
    },
    "provenance": [
      {
        "fields": [
          "prediction-purpose",
          "prediction-outcome",
          "prediction-data"
        ],
        "status": "paper-reported",
        "source": "Rajkomar et al. (2018), Scalable and accurate deep learning with electronic health records, Methods: prediction timing, study cohort and algorithm development",
        "url": "https://www.nature.com/articles/s41746-018-0029-1",
        "note": "Supports the adult cohort, minimum stay, discharge-time 30-day task and separate hospital analyses; does not supply the hypothetical local study's design decisions."
      },
      {
        "fields": [
          "prediction-purpose",
          "prediction-outcome",
          "prediction-inputs",
          "prediction-data",
          "prediction-evaluation",
          "prediction-uncertainty"
        ],
        "status": "teaching-assumption",
        "source": "Nirvana proposed local prediction protocol",
        "url": "https://www.nature.com/articles/s41746-018-0029-1",
        "note": "One-hospital silent use, input subset, local event capture, disjoint temporal validation, baseline and expanded evaluation checks are explicit teaching choices, not a replication of the paper's exact protocol."
      },
      {
        "fields": [
          "prediction-data",
          "prediction-evaluation"
        ],
        "status": "not-reported",
        "source": "Decisions not supplied for the educational local study",
        "url": "https://www.nature.com/articles/s41746-018-0029-1",
        "note": "Local institution, dates, dataset permission and clinical threshold cannot be inferred from the cited publication."
      }
    ]
  }
};
