"""Remove answer cues from the Foundations assessments after Chrome review."""

import re


# Target positions as learners see them. The runtime reverses choices on odd
# course activity indices (and odd entry-quiz question numbers), so authored
# order is derived from these targets instead of always listing the answer first.
DISPLAY_POSITIONS = {
    "variables-and-values.practice": 2, "variables-and-values.transfer": 1,
    "observed-association.practice": 2, "observed-association.transfer": 0,
    "association-is-not-causation.practice": 1,
    "treatment-and-outcome.practice": 0, "treatment-and-outcome.transfer": 2,
    "observation-vs-intervention.practice": 0, "observation-vs-intervention.transfer": 1,
    "world-data-model.practice": 1, "world-data-model.transfer": 0,
    "data-vs-assumptions.practice": 0, "data-vs-assumptions.transfer": 2,
    "basic-dag-language.practice": 1, "basic-dag-language.transfer": 0,
    "probabilistic-effects.practice": 2, "probabilistic-effects.transfer": 1,
    "m0-integrated-transfer.01": 1,
    "m0-final-quiz.01": 2, "m0-final-quiz.02": 0, "m0-final-quiz.03": 3,
    "m0-final-quiz.04": 1, "m0-final-quiz.05": 2, "m0-final-quiz.06": 0,
    "m0-final-quiz.07": 1, "m0-final-quiz.08": 3, "m0-final-quiz.09": 2,
}

# Nudges for a rejected final answer; they are also the final hints.
FINAL_NUDGES = (
    "Look for the recorded feature's name. Compare it with one person's value and the programme setting.",
    "Compare the recorded group means. Do they tell you how the groups were formed or what assigning sessions would change?",
    "People chose how many sessions to attend. Could the groups also differ in other ways?",
    "Recall what makes a question causal. Which option asks that kind of question?",
    "Ask who decided each person's offer, and how.",
    "Is the researcher describing the real system, recorded values, or an explanation of how the system works?",
    "Check which statements only repeat what the table records.",
    "Start at Offer and follow the arrows. What kind of route do they form?",
    "Ask what a change in chance says about a group, and what it says about each individual.",
)

FINAL_OPTIONS = {
    "m0-final-quiz.01.final.option.1": "Number of sessions attended by each person",
    "m0-final-quiz.01.final.option.2": "Four sessions, recorded for one person",
    "m0-final-quiz.01.final.option.3": "The programme that runs the sessions",
    "m0-final-quiz.01.final.option.4": "The largest attendance count recorded",
    "m0-final-quiz.02.final.option.1": "The records suggest an association between attendance and score",
    "m0-final-quiz.02.final.option.2": "Assigning more sessions would raise every person's score",
    "m0-final-quiz.02.final.option.3": "Higher scores cause people to attend more sessions",
    "m0-final-quiz.02.final.option.4": "The two attendance groups were formed by random assignment",
    "m0-final-quiz.04.final.option.1": "How would scores differ if similar people were given different session offers?",
    "m0-final-quiz.04.final.option.2": "Which people attended the most sessions during the last month of records?",
    "m0-final-quiz.04.final.option.3": "What was the largest follow-up score recorded anywhere in the programme?",
    "m0-final-quiz.04.final.option.4": "Which two recorded columns tend to rise and fall together?",
    "m0-final-quiz.08.final.option.2": "One measured value of the attendance variable",
    "m0-final-quiz.09.final.option.1": "Success becomes more likely, but some people can still miss the target",
    "m0-final-quiz.09.final.option.2": "The missed targets show that three sessions have no real effect",
    "m0-final-quiz.09.final.option.3": "Three sessions helped only the people who reached the target",
    "m0-final-quiz.09.final.option.4": "These assumed chances prove a benefit in real-world programmes",
}

# Rewritten question stems by resource ID.
GENERAL = {
    "intervention.question.practice": "An IT team takes last month's ticket-resolution times from its records, then compares the fastest and slowest tickets. What did the team do with resolution time?",
    "intervention.question.transfer": "A service team compares people who had already switched on dark mode with people who had not. The groups report different eye strain. What did the team do with the display setting?",
    "world-data-model.question.practice": "A researcher sketches how outdoor temperature could affect heating use and lead to the recorded electricity readings. Is the sketch data, a model or the world?",
    "world-data-model.question.transfer": "An engineer sketches how a machine's internal calibration could make its sensor readings drift over time. Is the sketch data, a model or the world?",
    "assumptions.question.practice": "Only umbrella carrying and pavement wetness are recorded for each arrival. The two occur together. A researcher says rain causes both. Do the records show this cause, or is it an extra assumption?",
    "assumptions.question.transfer": "A software log records only help-page visits and bug reports. The two rise together. The team says user confusion causes both. Does the log show this cause, or is it an extra assumption?",
}
MEDICAL = {
    "intervention.question.practice": "A sleep clinic uses sleep diaries to group patients by shorter or longer sleep, then compares daytime alertness. What did the clinic do with sleep duration?",
    "intervention.question.transfer": "A clinical team compares patients who had chosen to use a symptom-tracking app with patients who had not. What did the team do with app use?",
    "world-data-model.question.practice": "A researcher sketches how an illness could affect the body and lead to a patient's recorded laboratory readings. Is the sketch data, a model or the world?",
    "world-data-model.question.transfer": "A hospital engineer sketches how a device's internal calibration could make laboratory readings drift over time. Is the sketch data, a model or the world?",
    "assumptions.question.practice": "Clinic records contain only review flags and symptom counts. The two occur together. The team says illness severity causes both. Do the records show this cause, or is it an extra assumption?",
    "assumptions.question.transfer": "Clinic records contain only symptom-tracker use and nurse-contact counts. The two rise together. The team says symptom severity causes both. Do the records show this cause, or is it an extra assumption?",
}

# Values belong in a visible table rather than a long question heading:
# activity ID -> (question, what one row is, table label, columns, rows).
DATA_TABLES = {
    "general": {
        "variables-and-values.practice": (
            "A variable is a feature that can take different values. This IT-service table has one row per hour. Which option names the two recorded variables?",
            "Each row is one hour at the same IT service.", "Hourly IT-service records",
            ("Failed-login alert count", "Password-reset request count"), (("3", "8"), ("5", "6"), ("2", "11"))),
        "variables-and-values.transfer": (
            "This IT-service table has one row per support ticket. Which option names the two recorded variables?",
            "Each row is one support ticket.", "Support-ticket records",
            ("Waiting time (minutes)", "Message count"), (("12", "4"), ("30", "7"), ("5", "2"))),
        "observed-association.practice": (
            "These four records show weekly exercise and resting heart rate. Which statement describes the pattern?",
            "Each row is one person's record.", "Exercise records",
            ("Weekly exercise (hours)", "Resting heart rate (beats per minute)"),
            (("1", "78"), ("3", "72"), ("5", "66"), ("7", "61"))),
        "observed-association.transfer": (
            "A document service records drafts saved and documents finished for four users. Which statement describes the pattern?",
            "Each row is one user's record.", "Document-service records",
            ("Drafts saved", "Documents finished"), (("2", "1"), ("5", "3"), ("9", "4"), ("14", "7"))),
        "data-vs-assumptions.practice": (
            "At another campus, a researcher says rain causes umbrella carrying and wet pavement. Do these records show that cause, or is it an extra assumption?",
            "Only umbrella carrying and pavement wetness are recorded.",
            "Example records (one arrival per row)",
            ("Umbrella carried", "Pavement wet"),
            (("Yes", "Yes"), ("Yes", "Yes"), ("Yes", "No"), ("No", "Yes"), ("No", "No"), ("No", "No"))),
        "data-vs-assumptions.transfer": (
            "A software team says user confusion causes both help-page visits and bug reports. Do these records show that cause, or is it an extra assumption?",
            "Only help-page visits and bug-report counts are recorded.",
            "Example records (one user per row, same week)",
            ("Help-page visits", "Bug reports"),
            (("1", "0"), ("2", "1"), ("3", "2"), ("4", "1"), ("5", "3"), ("6", "2"))),
    },
    "medical": {
        "variables-and-values.practice": (
            "A variable is a feature that can take different values. This clinic table has one row per patient. Which option names the two recorded variables?",
            "Each row is one patient at the same clinic.", "Clinic records",
            ("Age (years)", "Resting heart rate (beats per minute)"), (("45", "72"), ("63", "80"), ("29", "66"))),
        "variables-and-values.transfer": (
            "This hospital table has one row per patient. Which option names the two recorded variables?",
            "Each row is one patient at the same hospital.", "Hospital records",
            ("Systolic blood pressure (mmHg)", "Body temperature (degrees C)"),
            (("118", "37.1"), ("132", "36.8"), ("125", "38.0"))),
        "observed-association.practice": (
            "These four patient records show weekly walking and resting heart rate. Which statement describes the pattern?",
            "Each row is one patient's record.", "Walking records",
            ("Weekly walking (minutes)", "Resting heart rate (beats per minute)"),
            (("30", "80"), ("90", "74"), ("150", "69"), ("210", "63"))),
        "observed-association.transfer": (
            "These four patient records show patient-portal use and attended appointments. Which statement describes the pattern?",
            "Each row is one patient's record.", "Patient-portal records",
            ("Portal logins per month", "Attended appointments"), (("1", "2"), ("4", "3"), ("8", "5"), ("12", "6"))),
        "data-vs-assumptions.practice": (
            "A clinic team says illness severity causes both review flags and symptom counts. Do these records show that cause, or is it an extra assumption?",
            "Only the clinical-review flag and symptom count are recorded.",
            "Example records (one patient visit per row)",
            ("Flagged for clinical review", "Symptom count at visit"),
            (("Yes", "5"), ("Yes", "3"), ("No", "4"), ("Yes", "2"), ("No", "1"), ("No", "0"))),
        "data-vs-assumptions.transfer": (
            "A clinic team says symptom severity causes both tracker use and nurse contacts. Do these records show that cause, or is it an extra assumption?",
            "Only tracker use and nurse-contact counts are recorded.",
            "Example records (one patient per row, same week)",
            ("Used symptom tracker", "Nurse contacts"),
            (("Yes", "3"), ("Yes", "1"), ("No", "2"), ("Yes", "2"), ("No", "0"), ("No", "1"))),
    },
}

FEEDBACK = {
    "variables.consequence.rejected": "Not yet. This list includes a value or setting instead of two recorded features. Compare each item with the table's column names.",
    "association.consequence.rejected": "Not yet. Read the numbers again: as one value goes up, does the other tend to go up or down?",
    "not-causation.consequence.rejected": "Not yet. Ask what the records describe, and what you would need to know about deliberately changing one variable.",
    "treatment.consequence.rejected": "Not yet. Name the proposed change and the result the question asks about. Compare each option with both.",
    "intervention.consequence.rejected": "Not yet. Ask how each value arose: did the team set it, or did it already exist before the team recorded it?",
    "world-data-model.consequence.rejected": "Not yet. The world is the real system, data are recorded values, and a model proposes how those values arise. Which describes the sketch itself?",
    "world-data-model.consequence.accepted": "Correct. The sketch is a model: it proposes how the recorded values could arise.",
    "world-data-model.hint": "Is this a set of recorded values, the real system itself, or an explanation of how the values arise?",
    "assumptions.explanation": "Data describe recorded values and patterns. A causal assumption adds a claim about what produces those patterns. Keep the observed pattern separate from the explanation proposed for it. Recording the proposed cause would not, by itself, establish that it causes both variables.",
    "assumptions.consequence.rejected": "Not yet. Compare what the records show with the team's claim about what causes the pattern. What additional support would that claim need?",
    "dag.consequence.rejected": "Not yet. A node is a variable, an arrow is a proposed causal link in the model, and a path is a route along arrows. Which of these does the question ask about, and what does it claim?",
    "probability.consequence.rejected": "Not yet. A change in chance describes what becomes more likely across many people. Does that tell you what must happen to each individual?",
    "probability.hint": "Does a change in chance promise each person's result, or describe what becomes more likely across people?",
    "integrated.consequence.rejected": "Not yet. Ask what the records show on their own and what the drawn graph adds to them.",
}


def _choices(medical: bool) -> dict[str, tuple[str, ...]]:
    """Correct text first, then each rejected option ID suffix and text."""

    if medical:
        return {
            "association.practice": ("More walking tends to go with a lower resting heart rate in these records.",
                "More walking tends to go with a higher resting heart rate in these records.",
                "These records show that walking more lowers resting heart rate."),
            "association.transfer": ("More portal use tends to go with more attended appointments in these records.",
                "More portal use tends to go with fewer attended appointments in these records.",
                "These records show that using the portal makes patients attend more appointments."),
            "not-causation.practice": ("Yes, if the difference in recovery rates between the groups is large enough.",),
            "treatment.practice": ("How many patients would accept the changed dose if it were offered.",),
            "treatment.transfer": ("How many patients would attend the sessions under the new schedule.",),
            "intervention.practice": ("Ran an experiment on sleep by comparing short and long sleepers.",),
            "intervention.transfer": ("Ran an experiment on app use by comparing users with non-users.",),
            "world-data-model.practice": ("A model: it proposes how the readings could be produced.",
                "Data: it is based on the recorded laboratory readings.",
                "The world: it is the patient's real biological processes."),
            "world-data-model.transfer": ("A model: it describes a possible process behind the readings.",
                "Data: it concerns the measured laboratory readings.",
                "The world: it is the device and its real calibration."),
            "assumptions.practice": ("An extra assumption: illness severity is not recorded, so these columns cannot show that it causes both.",
                "The records show that severity causes both, because flags and symptoms occur together.",
                "Shown by the records, because severity explains the pattern so well."),
            "assumptions.transfer": ("An extra assumption: the records contain tracker use and nurse contacts, not symptom severity.",
                "The records show that severity causes both, because tracker use and nurse contacts rise together.",
                "Shown by the records, because severity is the most obvious explanation."),
            "dag.practice": ("The records have proved that drug dose changes symptom score.",),
            "dag.transfer": ("A directed cycle: the arrows lead back to Physiotherapy.",),
            "probability.practice": ("Recovery becomes more likely, but is not guaranteed for every patient.",
                "The treatment has no effect, because some treated patients still do not recover.",
                "The treatment helped only the patients who recovered and did nothing for the rest."),
            "probability.transfer": ("Readmission becomes less likely, but remains possible for individual patients.",
                "The programme does not work, because some patients are still readmitted.",
                "The programme helped only the patients who were not readmitted and did nothing for the rest."),
        }
    return {
        "association.practice": ("More exercise tends to go with a lower resting heart rate in these records.",
            "More exercise tends to go with a higher resting heart rate in these records.",
            "These records show that exercising more lowers resting heart rate."),
        "association.transfer": ("More draft saving tends to go with more finished documents in these records.",
            "More draft saving tends to go with fewer finished documents in these records.",
            "These records show that saving drafts makes people finish more documents."),
        "not-causation.practice": ("Yes, if the two kinds of sales rise together closely enough in the records.",),
        "treatment.practice": ("How many students would sign up if extra sessions were offered.",),
        "treatment.transfer": ("How many people would open the tutorial if it were provided.",),
        "intervention.practice": ("Ran an experiment on resolution time by comparing fast and slow tickets.",),
        "intervention.transfer": ("Ran an experiment on dark mode by comparing the two groups.",),
        "world-data-model.practice": ("A model: it proposes how the readings could be produced.",
            "Data: it is based on the recorded electricity readings.",
            "The world: it is the real heating and electricity system."),
        "world-data-model.transfer": ("A model: it describes a possible process behind the readings.",
            "Data: it concerns the measured sensor readings.",
            "The world: it is the machine and its real calibration."),
        "assumptions.practice": ("An extra assumption: rain is not recorded, so these columns cannot show that it causes both.",
            "The records show that rain causes both, because umbrellas and wet pavement occur together.",
            "Shown by the records, because rain explains the pattern so well."),
        "assumptions.transfer": ("An extra assumption: the log records visits and reports, not confusion.",
            "The log shows that confusion causes both, because visits and reports rise together.",
            "Shown by the log, because confusion is the most obvious explanation."),
        "dag.practice": ("The records have proved that sleep changes concentration.",),
        "dag.transfer": ("A directed cycle: the arrows lead back to Tutorial.",),
        "probability.practice": ("Passing becomes more likely, but is not guaranteed for every learner.",
            "The tutorial has no effect, because some learners still do not pass.",
            "The tutorial helped only the learners who passed and did nothing for the rest."),
        "probability.transfer": ("Continued use becomes more likely, but is not certain for every person.",
            "The tutorial does not work, because some people still leave.",
            "The tutorial helped only the people who stayed and did nothing for those who left."),
    }


# Existing option IDs keep their meaning; a third plausible confusion gets a new
# ID so a single rejection no longer reveals a two-option answer by elimination.
NEW_OPTIONS = {
    "association": ("causal", "association-read-as-causation"),
    "not-causation": ("strength", "strong-association-is-causation"),
    "treatment": ("uptake", "outcome-misidentified"),
    "intervention": ("comparison", "comparison-is-intervention"),
    "world-data-model": ("world", "model-is-world"),
    "assumptions": ("fit", "good-fit-is-observed"),
    "dag": ("proven", "arrow-is-established"),
    "probability": ("individual", "individual-effect-from-outcome"),
}
REWORDED = {"association", "world-data-model", "assumptions", "probability"}


def apply_assessment_revision(data: dict, profile_id: str) -> None:
    """Rewrite cue-bearing items for a new pack version; IDs keep their truth."""

    medical = profile_id == "medical"
    resources = {item["resource_id"]: item for item in data["resources"]}
    updates = {**(MEDICAL if medical else GENERAL), **FEEDBACK}
    updates["association.consequence.causal-rejected"] = (
        "Not yet. These records show how two values vary together. Ask whether they "
        "show, on their own, what changing one value would do."
    )
    data["resources"].append({**resources["association.consequence.rejected"],
                              "resource_id": "association.consequence.causal-rejected"})
    resources = {item["resource_id"]: item for item in data["resources"]}
    for index, nudge in enumerate(FINAL_NUDGES, start=1):
        prefix = f"m0-final-quiz.{index:02d}.final"
        updates[prefix + ".hint"] = nudge
        updates[prefix + ".rejected"] = "Not yet. " + nudge
    for resource_id, text in updates.items():
        resources[resource_id]["text"] = text

    texts = _choices(medical)
    for activity in data["activities"]:
        stage = activity["activity_id"].partition(".")[2]
        prefix = next((choice["option_id"].rsplit(".", 2)[0] for choice in activity["choices"]), "")
        key = f"{prefix}.{stage}"
        if key in texts and prefix in NEW_OPTIONS:
            right = next(choice for choice in activity["choices"] if choice["correct"])
            wrong = [choice for choice in activity["choices"] if not choice["correct"]]
            alternatives = texts[key]
            if prefix in REWORDED:
                right["text"], wrong[0]["text"], extra = alternatives
            else:
                (extra,) = alternatives
            suffix, misconception = NEW_OPTIONS[prefix]
            added = {**wrong[0], "option_id": f"{prefix}.{stage}.{suffix}", "text": extra,
                     "misconception_id": misconception}
            if prefix == "association":
                added["consequence_resource_id"] = "association.consequence.causal-rejected"
            activity["choices"].append(added)
        for choice in activity["choices"]:
            if choice["option_id"] in FINAL_OPTIONS:
                choice["text"] = FINAL_OPTIONS[choice["option_id"]]

    activities = {item["activity_id"]: item for item in data["activities"]}
    for activity_id, (question, row_unit, label, columns, rows) in DATA_TABLES[profile_id].items():
        activity = activities[activity_id]
        activity["workbench"] = {
            "title": "Example records", "introduction": row_unit,
            "scenario_id": "foundation." + activity_id, "stage": "investigate",
        }
        _set_table_question(resources, activity, question, {
            "table_id": "records", "label": label, "columns": list(columns),
            "rows": [list(row) for row in rows]})
    # A causal-graph chain reads as one unit, so it is marked as inline code.
    for resource in resources.values():
        resource["text"] = _mark_graph_chains(resource["text"])
    for activity in data["activities"]:
        if activity.get("workbench") and activity["workbench"].get("prompt"):
            activity["workbench"]["prompt"] = _mark_graph_chains(activity["workbench"]["prompt"])
    # The group table is already visible, so the stem no longer repeats it.
    _set_table_question(resources, activities["m0-final-quiz.02"],
        "The table summarises two attendance groups. What do the programme records show directly?")
    goal = "mobility" if medical else "reading"
    people = "patients" if medical else "people"
    chances = {"table_id": "assumed-chances", "label": "Assumed chances in this teaching model",
               "columns": ["Offer", f"Chance of reaching the {goal} target"],
               "rows": [["One-session offer", "0.40"], ["Three-session offer", "0.60"]],
               "note": "These probabilities are assumed for the exercise, not results from a real programme."}
    _set_table_question(resources, activities["m0-final-quiz.09"],
        f"Suppose the table gives the chances of reaching a {goal} target. Some {people} offered three sessions still miss it. What can you conclude?",
        chances)

    for index, activity in enumerate(data["activities"]):
        target = DISPLAY_POSITIONS.get(activity["activity_id"])
        if target is None:
            continue
        correct = next(choice for choice in activity["choices"] if choice["correct"])
        others = [choice for choice in activity["choices"] if not choice["correct"]]
        authored = target if index % 2 == 0 else len(activity["choices"]) - 1 - target
        activity["choices"] = [*others[:authored], correct, *others[authored:]]


GRAPH_CHAINS = (
    "Tutorial → Continued use → Renewed subscription",
    "Physiotherapy → Mobility → Discharge readiness",
    "Offer → Sessions attended → Comprehension score",
    "Offer → Sessions attended → Mobility score",
    "Umbrella carrying ← Rain → Pavement wetness",
    "Drug dose → Symptom score",
    "Rain → Umbrella carrying",
    "Sleep → Concentration",
)


def _mark_graph_chains(text: str) -> str:
    """Use arrow glyphs and wrap each authored graph chain in backticks once."""

    text = text.replace(" -> ", " → ").replace(" <- ", " ← ")
    for chain in GRAPH_CHAINS:
        text = re.sub(r"(?<!`)" + re.escape(chain) + r"(?!`)", f"`{chain}`", text)
    return text


def _set_table_question(resources: dict, activity: dict, question: str, table: dict | None = None) -> None:
    """Show a short heading while the released question text also grounds the table."""

    workbench = activity["workbench"]
    if table is not None:
        workbench["tables"] = [table]
    shown = workbench["tables"][0]
    lines = (" | ".join(row) for row in [shown["columns"], *shown["rows"]])
    resources[activity["question_resource_id"]]["text"] = (
        question + "\n\n" + shown["label"] + ":\n" + "\n".join(lines)
    )
    workbench["prompt"] = question


def apply_data_world_challenge(data: dict, profile_id: str) -> None:
    """Give the new course a data/world transfer task, preserving the model quiz."""

    if profile_id not in {"general", "medical"}:
        raise ValueError(f"Unknown Foundations profile: {profile_id}")
    medical = profile_id == "medical"
    system = "laboratory device"
    readings = "laboratory readings" if medical else "sensor readings"
    question = (
        "A hospital engineer checks a laboratory device, logs its readings and sketches how it works. "
        if medical else
        "An engineer in a university laboratory checks a device, logs its sensor readings and sketches how it works. "
    ) + "Which option correctly identifies the data and the world?"
    resources = {item["resource_id"]: item for item in data["resources"]}
    activity = next(item for item in data["activities"]
                    if item["activity_id"] == "world-data-model.transfer")
    resources[activity["question_resource_id"]]["text"] = question
    prefix = "world-data-model.transfer.data-world"
    support = {
        "explanation": (
            "world-data-model.explanation",
            f"Data are the measurement values saved in the log. The world is the physical {system} "
            "and the processes that produce its readings. The engineer's sketch is a model: "
            "it proposes an explanation of those readings."),
        "hint": (
            "world-data-model.hint",
            "Which items were recorded, which exist in the physical system, and which are a proposed explanation?"),
        "accepted": (
            "world-data-model.consequence.accepted",
            "Correct. The pair identifies recorded measurements as data and the physical system as the world."),
        "rejected": (
            "world-data-model.consequence.rejected",
            "Not yet. Check both parts of the pair. Are they recorded measurements, the physical system, or a proposed explanation?"),
    }
    for suffix, (template_id, text) in support.items():
        data["resources"].append({**resources[template_id],
                                  "resource_id": f"{prefix}.{suffix}", "text": text})
    activity["explanation_resource_id"] = f"{prefix}.explanation"
    right = f"Data: the {readings} saved in the log. World: the physical {system} and the processes that produce its readings."
    alternatives = iter((
        ("swapped", f"Data: the physical {system} and its processes. World: the {readings} saved in the log.", "data-world-swapped"),
        ("model-as-data", f"Data: the engineer's proposed explanation. World: the physical {system} and the processes that produce its readings.", "model-is-data"),
    ))
    for choice in activity["choices"]:
        if choice["correct"]:
            choice.update(option_id=f"{prefix}.recorded-and-physical", text=right,
                          consequence_resource_id=f"{prefix}.accepted")
        else:
            suffix, text, misconception = next(alternatives)
            choice.update(option_id=f"{prefix}.{suffix}", text=text,
                          misconception_id=misconception,
                          hint_resource_ids=[f"{prefix}.hint"],
                          consequence_resource_id=f"{prefix}.rejected")
    lesson = next(item for item in data["lessons"] if item["concept_id"] == "world-data-model")
    lesson["challenge_title"] = "Identify data and the world"
