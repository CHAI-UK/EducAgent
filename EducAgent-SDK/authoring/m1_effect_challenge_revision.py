"""Complementary Effect assessment over the unchanged 1.3 teaching world."""


def apply_effect_challenge_revision(data: dict, profile: str) -> None:
    """Teach Challenge facets in visible core copy and replace one repeated sum."""
    if profile not in {"general", "medical"}:
        raise ValueError("Effect Challenge revision requires general or medical")
    if data.get("pack_id") != f"causality.m1.effect.{profile}":
        raise ValueError("Effect Challenge revision requires the matching Effect profile pack")
    if len(data["activities"]) != 16 or len(data["lessons"]) != 4:
        raise ValueError("Effect Challenge revision requires sixteen activities and four lessons")

    medical = profile == "medical"
    resources = {item["resource_id"]: item for item in data["resources"]}
    lessons = {item["concept_id"]: item for item in data["lessons"]}
    lessons["average-treatment-effect"]["title"] = "Average effects and individual outcomes"
    core_definitions = {
        "defining-an-intervention": (
            "An intervention actively sets a treatment. Selecting records of people who already received it leaves their original assignment process in place. "
            "Specify the treatment, alternative, target population, outcome and follow-up. Assignment and actual use can differ: some people may not take up their assigned option. "
            "Randomization applies to assignment; comparing actual users may bring their own choices back into the comparison."
        ),
        "average-treatment-effect": (
            "An average treatment effect compares mean outcomes under two interventions for the same target population. "
            "Subtract the comparison from the treatment and state the units. For a binary (yes/no) outcome, a probability difference uses percentage points, not a relative percentage. "
            "An individual's effect compares that person's outcome under A with their outcome under B. Group averages do not reveal that pair for each person. "
            "Even with a positive average, some people may see no benefit or be harmed. Sampling uncertainty means another sample could give a different estimate."
        ),
        "identifiability-of-effects": (
            "Identification asks whether the data and stated causal assumptions determine an effect. Estimation calculates it from a finite sample, with uncertainty. "
            "Transport asks whether the result applies to another population, treatment version or follow-up time, using evidence and assumptions for that new target. "
            "A precise estimate alone does not settle the other questions."
        ),
    }
    for concept_id, text in core_definitions.items():
        resources[lessons[concept_id]["definition_resource_id"]]["text"] = text
    resources[lessons["average-treatment-effect"]["hook_resource_id"]]["text"] = (
        "Consider two hypothetical people on a score where higher is better. Compared with B, A would raise one person's score by 10 points and lower the other's by 2 points. "
        "Their average effect is +4 points, even though one person is harmed. These individual effects are given for the example; group averages alone would not reveal them."
    )
    baseline = "mobility limitation" if medical else "learning difficulty"
    resources[lessons["confounding-and-adjustment"]["hook_resource_id"]]["text"] = (
        f"Baseline {baseline} can influence both programme choice and later success. The overall A and B groups may therefore contain different starting conditions. "
        "Suppose a programme changes practice time, which then affects success. Practice time is a mediator in this model. "
        "The programme's total effect includes this pathway. Adjusting for practice time would block it."
    )

    activity = next(item for item in data["activities"]
                    if item["activity_id"] == "average-treatment-effect.challenge")
    question = (
        "A randomized study records recovery by day 30 in 54/100 people assigned A and 40/100 assigned B. "
        "A has the higher group recovery rate. What can these results tell us about any one patient's benefit from A rather than B?"
        if medical else
        "A randomized study records course completion by day 30 in 54/100 students assigned A and 40/100 assigned B. "
        "A has the higher group completion rate. What can these results tell us about any one student's benefit from A rather than B?"
    )
    prefix = activity["question_resource_id"].removesuffix(".question")
    explanation = (
        "Each participant was assigned one programme. These results do not show how that same person would have done under the other programme. "
        "The group rates estimate an average difference with uncertainty; they do not identify who benefited, saw no benefit or was harmed."
    )
    for suffix, text in (
        ("question", question),
        ("hint", "Do the two group rates show how the same person would have done under both assignments?"),
        ("explanation", explanation),
        ("accepted", explanation),
        ("rejected", "A difference between groups does not reveal each person's two possible outcomes. Check whether the answer claims to know everyone's response or the identities of those who benefited."),
    ):
        resources[f"{prefix}.{suffix}"]["text"] = text
    answer_prefix = "average-treatment-effect.challenge.individual-effects"
    alternatives = iter((
        ("all-benefit", "Every participant would have a better outcome under A than under B.", "average-is-individual-guarantee"),
        ("names-beneficiaries", "The two group rates identify exactly which participants benefited from A.", "average-identifies-individuals"),
    ))
    for choice in activity["choices"]:
        if choice["correct"]:
            choice.update(
                option_id=f"{answer_prefix}.group-average",
                text="They estimate a group-average difference, but do not identify which participants benefited from A.",
            )
        else:
            suffix, text, misconception = next(alternatives)
            choice.update(option_id=f"{answer_prefix}.{suffix}", text=text,
                          misconception_id=f"m1.effect.{misconception}")
