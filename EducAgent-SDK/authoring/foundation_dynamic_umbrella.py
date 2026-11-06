"""Author a bounded hypothesis/reference comparison without changing M0 scoring."""


SCENE_COPY = {
    "hook": "Umbrellas and wet pavement often appear together. Propose an explanation, then test what it predicts when everyone carries an umbrella.",
    "records": "Each record is one person's arrival at campus. The table groups 240 arrivals by umbrella carrying and pavement wetness. These are arrival records, not 240 different days. Different explanations can produce this same table.",
    "model": "Choose one of the three hypotheses. Each includes arrows and a rule for generating the variable values. Arrows alone do not specify numerical predictions. All three hypotheses reproduce the displayed observations, but they can predict different intervention results.",
    "prediction": "Use your selected hypothesis and its rule to predict whether wet pavement would be more common, less common or unchanged if everyone carried an umbrella. This prediction is unscored.",
    "intervention": "An intervention actively sets a variable instead of only recording it. Make all 240 people carry an umbrella, using the same background cases. The server calculates the outcome for your selected hypothesis and for a fixed reference world separately. Changing your hypothesis does not change that reference world.",
    "result": "Compare the wet-pavement counts calculated for your hypothesis and the reference world. Both use all 240 arrivals. Then choose a different hypothesis and test again. Filtering the original umbrella carriers instead keeps only 96 arrivals, all with wet pavement (100%); selecting those records is not the same as actively setting umbrella carrying.",
    "reflection": "After testing at least two different hypotheses, compare their predictions with the reference result. Agreement with one intervention does not establish a unique graph. For the final graph check, use the reference world's assumptions shown here: rain causes umbrella carrying and pavement wetness, with no other direct arrows. Your comparison and prediction are unscored.",
    "explanation": "Each hypothesis includes arrows and a rule for generating the variable values. Changing the hypothesis changes its calculated prediction while the reference world stays fixed. In the reference world, rain causes both umbrella carrying and wet pavement. Giving everyone an umbrella therefore leaves wetness at 96 of 240 arrivals (40%). The reverse-causation hypothesis also predicts unchanged wetness, so agreement with this intervention does not identify a unique graph. The final graph check asks you to represent the reference world's stated assumptions. Predictions and reflections are unscored.",
    "hint": "For the final graph check, use the reference world's stated assumptions: rain causes umbrella carrying and pavement wetness, with no other direct arrows. The experiments did not identify a unique graph.",
    "consequence.accepted": "Your graph represents the reference world's stated assumptions. Matching that supplied model does not prove that these data identify a unique graph. Your hypothesis comparisons, predictions and reflections remain unscored.",
    "consequence.rejected": "This graph does not yet represent the reference world's stated assumptions. Include rain causing umbrella carrying and wet pavement, with no other direct arrows. Other graphs can fit the observations or this intervention result. This check asks you to represent the supplied model; it does not test whether you discovered a unique graph.",
}


def apply_dynamic_umbrella(data: dict) -> None:
    """Replace only the scene's teaching copy and add its versioned model catalog.

    The finite simulation kernel owns equations and graphs. Content supplies
    readable assumptions; existing scored activities and reference rows remain
    unchanged, so the new interaction does not silently redefine correctness.
    """

    scene = next(item for item in data["causal_scenes"]
                 if item["scene_id"] == "causality.rain-umbrella")
    scene["simulation"] = {
        "kind": "umbrella_scm",
        "model_version": "1.0.0",
        "population_size": 240,
        "root_yes_count": 96,
        "minimum_hypotheses": 2,
        "reference_hypothesis_id": "rain-common-cause",
        "hypotheses": [
            {
                "hypothesis_id": "rain-common-cause",
                "label": "Rain causes both",
                "mechanism": "It rains for 96 of 240 arrivals. For each arrival, umbrella carrying and pavement wetness match the rain value. Giving everyone an umbrella replaces only the usual rule for umbrella carrying.",
            },
            {
                "hypothesis_id": "umbrella-causes-wet",
                "label": "Umbrellas cause wet pavement",
                "mechanism": "People carry an umbrella in 96 of 240 arrivals. Pavement wetness matches umbrella carrying. Giving everyone an umbrella replaces the usual rule for carrying; wetness still follows the carrying value.",
            },
            {
                "hypothesis_id": "wet-causes-umbrella",
                "label": "Wet pavement causes umbrella carrying",
                "mechanism": "The pavement is wet for 96 of 240 arrivals. Umbrella carrying matches pavement wetness. Giving everyone an umbrella replaces the usual rule for carrying and leaves the rule for wetness unchanged.",
            },
        ],
    }
    for resource in data["resources"]:
        if resource["resource_id"].startswith("scene.rain-umbrella."):
            suffix = resource["resource_id"].removeprefix("scene.rain-umbrella.")
            if suffix in SCENE_COPY:
                resource["text"] = SCENE_COPY[suffix]
