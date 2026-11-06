"""Apply the October 2026 wording review to newly versioned Foundations packs."""

import re


COMMON_QUESTIONS = {
    "variables.question.practice": "A clinic records each patient's resting heart rate. Could resting heart rate be a variable?",
    "treatment.question.practice": "A clinician asks whether a patient's recovery would change if they were given a different drug dose. Is this a causal question?",
    "intervention.question.practice": "A clinic records its patients' existing sleep durations without assigning a sleep schedule. Is the clinic observing sleep or intervening on it?",
    "probability.question.practice": "Suppose a treatment raises the chance of recovery, but some treated patients still do not recover. Is the effect probabilistic or deterministic?",
}

PROFILE_QUESTIONS = {
    "general": {
        "association.question.practice": "Records show that people who exercise more often also report lower resting heart rates. What can we say about this relationship based on these observations?",
        "not-causation.question.practice": "We observe that ice-cream sales and sunglasses sales rise together. Does this observation alone establish that increased ice-cream sales cause an increase in sunglasses sales?",
        "world-data-model.question.practice": "A researcher draws a diagram explaining how a hidden disease process might generate observed data records. Is the diagram data or a model?",
        "assumptions.question.practice": "A dataset shows that people carrying umbrellas are often near wet streets. Is the claim that rain causes both an observation directly supported by these records, or an additional causal assumption?",
        "dag.question.practice": "In a proposed causal diagram, what does an arrow from sleep to concentration represent?",
        "probability.question.transfer": "Suppose providing a tutorial increases the chance that people keep using a digital service, but some people still stop using it. Is the effect probabilistic or deterministic?",
    },
    "medical": {
        "association.question.practice": "Clinic records show that patients reporting more weekly walking also tend to have lower resting heart rates. What can we say about this relationship based on these observations?",
        "not-causation.question.practice": "A clinic records that patients receiving Treatment A recover less often than patients who do not receive it. Do these records alone establish that Treatment A causes poorer recovery?",
        "world-data-model.question.practice": "An investigator draws a diagram explaining how a hidden illness process might generate observed clinical records. Is the diagram data or a model?",
        "assumptions.question.practice": "Clinic records show that patients flagged for review also have more symptoms. Is the claim that illness severity causes both the review flag and the symptoms an observation directly supported by these records, or an additional causal assumption?",
        "dag.question.practice": "In a clinician's proposed causal diagram, what does an arrow from drug dose to symptom score represent?",
        "probability.question.transfer": "Suppose an exercise programme lowers the chance of readmission, but some patients who receive it are still readmitted. Is the effect probabilistic or deterministic?",
    },
}

PRACTICE_CHOICES = {
    "variables.practice.variable": "Variable",
    "variables.practice.fixed": "Fixed story detail",
    "not-causation.practice.no": "No, these observations alone are not enough to establish a causal relationship",
    "not-causation.practice.yes": "Yes, these observations alone establish a causal relationship",
    "treatment.practice.yes": "Yes, it asks what changing the drug dose would do to recovery",
    "treatment.practice.no": "No, it only asks about an observed association",
    "intervention.practice.observation": "Observation",
    "intervention.practice.intervention": "Intervention",
    "world-data-model.practice.model": "Model",
    "world-data-model.practice.data": "Data",
    "assumptions.practice.assumption": "Additional causal assumption",
    "assumptions.practice.data": "Direct observation from these records",
    "dag.practice.arrow": "A proposed causal relationship",
    "dag.practice.value": "A measured value",
    "probability.practice.probabilistic": "Probabilistic",
    "probability.practice.deterministic": "Deterministic",
}


def _without_fictional(text: str) -> str:
    cleaned = text.replace("A fictional investigator", "An investigator").replace(
        "a fictional investigator", "an investigator",
    ).replace("are fictional;", "are hypothetical;")
    cleaned = re.sub(r"\bfictional\s+", "", cleaned, flags=re.IGNORECASE)
    return cleaned[:1].upper() + cleaned[1:] if text.lower().startswith("fictional ") else cleaned


def apply_review(data: dict, profile_id: str) -> None:
    """Revise display copy in place without changing evidence or provenance."""

    if profile_id not in PROFILE_QUESTIONS:
        raise ValueError("Foundations review requires general or medical")
    resources = {item["resource_id"]: item for item in data["resources"]}
    updates = {**COMMON_QUESTIONS, **PROFILE_QUESTIONS[profile_id]}
    choices = {
        **PRACTICE_CHOICES,
        "association.practice.yes": (
            "More exercise is associated with lower resting heart rate"
            if profile_id == "general"
            else "More weekly walking is associated with lower resting heart rate"
        ),
        "association.practice.no": (
            "More exercise causes lower resting heart rate"
            if profile_id == "general"
            else "More weekly walking causes lower resting heart rate"
        ),
    }
    lessons = {item["concept_id"]: item for item in data["lessons"]}
    probability = lessons["probabilistic-effects"]
    updates[probability["hook_resource_id"]] = (
        "Suppose giving Treatment T increases the chance of recovery, but some treated patients still do not recover. Can both statements be true?"
    )
    updates[probability["example_label_resource_id"]] = (
        "Hypothetical treatment example; not a clinical finding or recommendation."
    )
    for step, text in zip(probability["worked_steps"], (
        "The example says that recovery is more likely with Treatment T than without it.",
        "More likely does not mean certain. Some treated patients may still not recover.",
        "A treatment can change the chance of recovery without guaranteeing recovery for every patient.",
    ), strict=True):
        updates[step["resource_id"]] = text
    probability["worked_steps"][0]["title"] = "Start with a hypothetical effect"
    updates[probability["pitfall_resource_id"]] = (
        "One patient not recovering does not contradict a higher chance of recovery. This hypothetical example does not establish a real treatment benefit."
    )
    updates[probability["takeaway_resource_id"]] = "Separate a better chance from a guaranteed result."
    if profile_id == "general":
        probability["challenge_title"] = "Fresh case: a tutorial and continued use"
        assumptions = lessons["data-vs-assumptions"]
        updates[assumptions["hook_resource_id"]] = (
            "A museum records that days with more donations also tend to have higher cafe sales. Does this pattern alone establish that visitor numbers cause both?"
        )
        updates[assumptions["example_label_resource_id"]] = (
            "Hypothetical museum records and proposed explanation; not an empirical finding."
        )
        for step, text in zip(assumptions["worked_steps"], (
            "The records contain donations and cafe sales. Higher donations tend to occur on days with higher cafe sales: this is the observed pattern.",
            "More visitors could lead to both more donations and more cafe sales. That is a proposed causal explanation, not a direct observation of what causes the pattern.",
            "Write the two statements separately: donations and cafe sales are associated in the records; our proposed explanation assumes that visitor numbers influence both. The pattern alone does not establish that explanation.",
        ), strict=True):
            updates[step["resource_id"]] = text
    for resource_id, text in updates.items():
        resources[resource_id]["text"] = text
    for resource in data["resources"]:
        resource["text"] = _without_fictional(resource["text"])
    for activity in data["activities"]:
        for choice in activity["choices"]:
            choice["text"] = _without_fictional(choices.get(choice["option_id"], choice["text"]))
    for item in [*data["activities"], *data["lessons"]]:
        if item.get("scenario_image") is not None:
            item["scenario_image"]["alt_text"] = _without_fictional(item["scenario_image"]["alt_text"])
