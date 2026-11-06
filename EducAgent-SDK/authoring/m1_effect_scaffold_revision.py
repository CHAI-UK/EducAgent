"""One-control Effect practice guides over the unchanged 1.2.0 teaching world."""

from copy import deepcopy


CONCEPT_IDS = (
    "defining-an-intervention", "average-treatment-effect",
    "confounding-and-adjustment", "identifiability-of-effects",
)


def apply_effect_scaffold_revision(data: dict, profile_id: str) -> dict:
    """Add authored guidance without changing curriculum, scoring or arithmetic."""
    if profile_id not in {"general", "medical"}:
        raise ValueError("Effect scaffold revision requires general or medical")
    if data.get("pack_id") != f"causality.m1.effect.{profile_id}":
        raise ValueError("Effect scaffold revision requires the matching Effect profile pack")
    if tuple(item["concept_id"] for item in data["concepts"]) != CONCEPT_IDS:
        raise ValueError("Effect scaffold revision requires the existing four-concept curriculum")
    if len(data["activities"]) != 16:
        raise ValueError("Effect scaffold revision requires the existing sixteen activities")
    revised = deepcopy(data)
    resources = {r["resource_id"]: r for r in revised["resources"]}
    activities = {a["activity_id"]: a for a in revised["activities"]}
    medical = profile_id == "medical"
    people = "eligible rehabilitation patients" if medical else "students eligible for study support"
    baseline = "mobility limitation" if medical else "learning difficulty"
    success = "reaching the declared mobility target" if medical else "passing the declared skills check"
    service = "A rehabilitation service" if medical else "A college"
    story = (
        f"{service} is comparing six-week programmes A and B for {people}. Success means {success} "
        f"at six weeks. Before the programme, people have lower or higher {baseline}. "
        "People who choose A can differ from people who choose B before either programme starts. "
        "In this teaching model, success rates within those starting groups stay fixed while you change one part of the comparison at a time."
    )
    overall = {"metric_label": "Source pooled A minus B", "label": "Overall difference (A minus B)"}
    target = {"metric_label": "Target-standardized A minus B", "label": "Target-population difference (A minus B)"}
    stages = (
        {
            "title": "Which people are we averaging?",
            "parameter_id": "analysis", "parameter_label": "How to average the programme results",
            "parameter_description": (
                f"People still choose their programmes. Start with each programme's own mixture of lower and higher {baseline}: the pooled comparison. "
                "Then use the same half-and-half target mixture for A and B: standardization. "
                "Only the averaging rule changes; programme choices, starting groups and success rates stay fixed."
            ),
            "goal": "See how comparing different starting-group mixtures can change an overall programme comparison.",
            "story": story,
            "prediction_prompt": "When both programmes use the same target mixture, do you expect the A-minus-B difference to stay the same? Why?",
            "comparison_prompt": "Compare the two A-minus-B differences. Did within-group outcome rates change, or did the baseline mixture represented by the averages change?",
            "metrics": [{"metric_label": "Selected analysis contrast", "label": "Displayed difference (A minus B)"}],
            "instructions": "Predict and run using the pooled comparison. Change only the averaging rule to the same target weights for A and B, predict again and rerun. Compare the displayed differences, then select Record my comparison.",
        },
        {
            "title": "Who decides the programme?",
            "parameter_id": "assignment", "parameter_label": "How people enter programmes A and B",
            "parameter_description": (
                "Start with balanced random assignment, which gives A and B the same starting-group mix in this model. "
                f"Then let people choose, with more people who have higher {baseline} choosing A. "
                f"Only assignment changes; success rates within each starting group stay fixed. The target remains half lower and half higher {baseline}. "
                "The overall comparison still uses each programme's own mixture."
            ),
            "goal": "Distinguish actively assigning a programme from comparing people who already chose one.",
            "story": story + " This time keep the overall averaging rule and change how people enter the programmes.",
            "prediction_prompt": "If people choose their programme instead of receiving balanced random assignments, what do you expect to happen to the overall A-minus-B difference?",
            "comparison_prompt": "Compare the overall differences and starting-group counts. Who received A or B under each rule? Which outcome rules stayed the same?",
            "metrics": [overall],
            "instructions": "Predict and run with balanced random assignment. Change only to people choosing their programme, predict again and rerun. Keep the target and overall averaging rule fixed. Compare group mixtures and the overall difference, then select Record my comparison.",
        },
        {
            "title": "Which population is the decision for?",
            "parameter_id": "target_high_pct", "parameter_label": f"Target population with higher {baseline}",
            "parameter_description": (
                "The target population is the group we want the programme comparison to represent. "
                f"Change its share with higher {baseline} from 20% to 80%. "
                "Both programmes use that same target mixture. Balanced random assignment, source records and within-group success rates stay fixed."
            ),
            "goal": "See why an average programme difference can depend on which population it describes.",
            "story": story + f" Now consider a target population with a different share of people who have higher {baseline}.",
            "prediction_prompt": f"The share with higher {baseline} rises from 20% to 80%. How might that change the target-population A-minus-B difference?",
            "comparison_prompt": "Compare the target-population differences. Did you change the source records or the target weights? Why can't you read this average as each individual's effect?",
            "metrics": [target],
            "instructions": f"Predict and run with 20% of the target population having higher {baseline}. Change only that percentage to 80%, predict again and rerun. Keep assignment and the common-target averaging rule fixed. Compare the target differences, then select Record my comparison.",
        },
        {
            "title": "Can matching calculations prove the assumptions?",
            "parameter_id": "assignment", "parameter_label": "How people enter programmes A and B",
            "parameter_description": (
                "Start with people choosing, then change only to balanced random assignment. "
                f"Keep a target where 80% of people have higher {baseline}, and use common target weights for A and B. "
                "The model keeps its within-group success rules fixed. Matching adjusted results do not establish that a real study has measured every relevant common cause."
            ),
            "goal": "Separate a calculation under supplied assumptions from evidence that those assumptions hold.",
            "story": story + " For the last comparison, keep one target population and inspect both the overall and common-target differences.",
            "prediction_prompt": "When you change assignment and keep the target weights fixed, which difference do you expect to change: the overall comparison, the target comparison, or both?",
            "comparison_prompt": "Compare both differences under the two assignment rules. Why doesn't agreement in this teaching model show that a real study has no remaining confounding?",
            "metrics": [overall, target],
            "instructions": "Predict and run with people choosing their programme. Change only to balanced random assignment, predict again and rerun. Keep target weights and analysis fixed. Compare overall and target-population differences, then select Record my comparison. State what a real study would still need to justify.",
        },
    )
    for index, stage in enumerate(stages, 1):
        activity = activities[f"m1-effect-investigation.{index:02d}"]
        experiment = activity["experiment"]
        experiment["title"] = stage["title"]
        experiment["guide"] = {"section": "intervention", **{
            key: value for key, value in stage.items() if key not in {"title", "instructions"}
        }}
        resources[experiment["instructions_resource_id"]]["text"] = stage["instructions"]
        activity["workbench"]["introduction"] = stage["story"]
    return revised
