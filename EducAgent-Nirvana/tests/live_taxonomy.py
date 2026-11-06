"""Opt-in local ELM smoke test. Run explicitly with --live; not a benchmark."""
import argparse
import json
import urllib.request

CASES = [
  {
    "name": "Alzheimer's biomarker relationships",
    "task": "discovery",
    "message": "We have ADNI observational data on Alzheimer's disease biomarkers, including amyloid beta, phosphorylated tau, FDG-PET, APOE genotype and clinical or cognitive measurements. We want to investigate candidate causal directions among these variables, rather than only predict a diagnosis. How should we frame a causal structure discovery study, combining the data with biological knowledge while accounting for unmeasured factors and uncertainty in the graph?"
  },
  {
    "name": "Sequential depression treatment",
    "task": "policy",
    "message": "Using data from the STAR*D study, we want to investigate a sequence of treatment-selection rules for people with depression. At each treatment stage, the rule would use information already available about the patient's response to earlier treatment to choose among eligible next options, aiming to improve subsequent depression outcomes. How should we specify the decision stages, available actions, patient history and objective? This is a research question about treatment policies, not a request for advice for an individual patient."
  },
  {
    "name": "The same brain, different ventricle volume",
    "task": "counterfactual",
    "message": "For one observed brain MRI, we want to ask what the image would look like under a hypothetical intervention that changes ventricle volume in a structural causal model while preserving the same subject's inferred background factors. How should we specify the factual scan, the intervention, the counterfactual image target and the model assumptions? The generated image would be a model-dependent hypothetical, not an observed alternative outcome or a validated clinical prediction."
  },
  {
    "name": "Predicting readmission from EHRs",
    "task": "prediction",
    "message": "We want to use electronic health records available at hospital discharge to predict whether a patient will have an unplanned readmission within 30 days. Our immediate goal is to evaluate predictive accuracy in our hospital data, not to estimate a treatment effect or claim robustness at a new hospital. How should we define the target, allowable inputs and validation plan?"
  },
  {
    "name": "Population effect",
    "task": "effect",
    "message": "Does offering job training increase annual earnings compared with not offering it among eligible unemployed adults?"
  },
  {
    "name": "Effect transport",
    "task": "effect",
    "tag": "transport",
    "message": "We estimated a drug's average treatment effect in a trial population. Can we transport that treatment effect to a different country's population? We are not building a prediction model."
  },
  {
    "name": "Mediation",
    "task": "mediation",
    "message": "Does an educational intervention improve exam results partly through increased study time? I want the indirect effect through study time."
  },
  {
    "name": "Descriptive disparity",
    "task": "descriptive",
    "message": "What proportion of applicants received a loan in 2025, broken down by sex? I want to report the observed group rates only."
  },
  {
    "name": "Generation under shift",
    "task": "shift",
    "tag": "generation",
    "message": "We synthesise non-contrast CT from contrast CT. Can causal modelling make this generator robust to new scanner vendors and different age and sex distributions?"
  },
  {
    "name": "Unclear request",
    "task": "other",
    "message": "Can you help with my research? I have not decided the scientific question yet."
  }
]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Send these fictional questions to the configured ELM")
    args = parser.parse_args()
    if not args.live:
        parser.error("Explicit --live is required; this script sends questions to ELM")
    failures = 0
    for case in CASES:
        request = urllib.request.Request("http://127.0.0.1:8011/api/frame", data=json.dumps({"message": case["message"], "context": "New question; draft from this message only."}).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=100) as response:
            result = json.load(response)
        ok = result["task"] == case["task"] and ("tag" not in case or case["tag"] in result.get("tags", []))
        failures += not ok
        print(json.dumps({"case": case["name"], "expected": case["task"], "actual": result["task"], "tags": result.get("tags", []), "nonempty_specs": sum(bool(v) for v in result["fields"].values()), "passed": ok}), flush=True)
    raise SystemExit(bool(failures))
