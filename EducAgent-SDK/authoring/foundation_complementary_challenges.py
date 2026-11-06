"""Author complementary transfer facets for the Foundations 1.8.0 course."""

if __package__:
    from .foundation_assessment_revision import _set_table_question
else:
    from foundation_assessment_revision import _set_table_question


def apply_complementary_challenges(data: dict, profile_id: str) -> None:
    """Change six transfer tasks and their visible teaching, leaving quizzes intact."""

    if profile_id not in {"general", "medical"}:
        raise ValueError(f"Unknown Foundations profile: {profile_id}")
    medical = profile_id == "medical"
    feature = "systolic blood pressure" if medical else "waiting time"
    value = "118 mmHg" if medical else "12 minutes"
    other_feature = "body temperature" if medical else "message count"
    cases = (
        {
            "activity_id": "variables-and-values.transfer", "prefix": "variables.transfer.value",
            "title": "Identify a recorded value",
            "question": f"The first {'patient' if medical else 'ticket'} record shows {value}. What is {value} in this table?",
            "options": (
                ("recorded-value", f"One recorded value of {feature}.", None),
                ("variable-name", f"The name of the {feature} variable.", "value-is-variable"),
                ("other-variable", f"One recorded value of {other_feature}.", "value-matched-to-wrong-variable"),
                ("setting", "The hospital where the record was collected." if medical else "The IT service where the record was collected.", "value-is-setting"),
            ),
            "hint": "Match the number and unit to a column. Is it the column's name or one entry in that column?",
            "explanation": f"{feature.capitalize()} is a variable. {value} is one recorded value of it, for one {'patient' if medical else 'ticket'}. The unit tells us how that value was measured.",
            "accepted": "Correct. This is one entry for the named variable, with its unit.",
            "rejected": "Not yet. Separate the column name, an entry in that column and the setting. Which role does the question's number have?",
        },
        {
            "activity_id": "observed-association.transfer", "prefix": "association.transfer.linked-records",
            "title": "Choose records for an association",
            "question": (
                "A clinic wants to compare portal use and attended appointments during the same month. Which information should stay linked for this comparison between patients?"
                if medical else
                "A document service wants to compare draft saving and document completion during the same week. Which information should stay linked for this comparison between users?"
            ),
            "introduction": "Each row pairs one patient's two counts for the same month." if medical else "Each row pairs one user's two counts for the same week.",
            "options": (
                ("same-case", "Each patient's portal use and attended appointments for that month." if medical else "Each user's draft count and finished-document count for that week.", None),
                ("unlinked-groups", "Portal-use counts from one group and appointment counts from an unrelated group." if medical else "Draft counts from one group and document counts from an unrelated group.", "association-from-unlinked-groups"),
                ("unlinked-totals", "Two clinic-wide totals, without information about which values occurred together for patients." if medical else "Two service-wide totals, without information about which values occurred together for users.", "association-from-unlinked-marginals"),
            ),
            "hint": "Check whether both values belong to the same person and the period specified in the question.",
            "explanation": "The two values must refer to the same units for this comparison. Linked records preserve that pairing; counts of value combinations can preserve it too. Unlinked totals lose the information about how the values occur together.",
            "accepted": "Correct. This keeps both values linked for the same person and period.",
            "rejected": "Not yet. With unrelated groups or unlinked totals, can you tell which values occurred together for the people being compared?",
        },
        {
            "activity_id": "treatment-and-outcome.transfer", "prefix": "treatment.transfer.roles",
            "title": "Name the treatment and outcome",
            "question": (
                "A physiotherapy team asks whether changing the assigned weekly session schedule would change mobility. Which pair identifies the treatment and the outcome?"
                if medical else
                "A service team asks whether offering a setup tutorial would change continued use. Which pair identifies the treatment and the outcome?"
            ),
            "options": (
                ("action-and-result", "Treatment: the assigned session schedule. Outcome: mobility." if medical else "Treatment: whether the tutorial is offered. Outcome: continued use of the service.", None),
                ("reversed", "Treatment: mobility. Outcome: the assigned session schedule." if medical else "Treatment: continued use. Outcome: whether the tutorial is offered.", "treatment-outcome-reversed"),
                ("uptake-as-target", "Treatment: the assigned session schedule. Outcome: how many patients attend." if medical else "Treatment: whether the tutorial is offered. Outcome: how many people open it.", "outcome-misidentified"),
            ),
            "hint": "Identify what the team would change, then the result it wants to study.",
            "explanation": "The treatment is what the team would set differently; the outcome is the result named in its question. Participation can be another result, but it is not the outcome specified here.",
            "accepted": "Correct. The pair separates the proposed change from the result named in the question.",
            "rejected": "Not yet. Check both labels against the team's question. Which item is the proposed change, and which is the result being studied?",
        },
        {
            "activity_id": "observation-vs-intervention.transfer", "prefix": "intervention.transfer.set-value",
            "title": "Choose an intervention",
            "question": (
                "A clinical team is planning a study of symptom-tracker use. Which action would intervene on use?"
                if medical else
                "A service team plans to study dark mode and reported eye strain. Which action would intervene on the display setting?"
            ),
            "options": (
                ("actively-set", "In a supervised study session, have participants use the tracker or leave it unused." if medical else "Set participants' displays to dark mode or the default setting before recording eye strain.", None),
                ("filter-existing", "Select patient records in which tracker use is already marked yes." if medical else "Select records from people who had already chosen dark mode.", "selection-is-intervention"),
                ("compare-existing", "Compare patients who had chosen tracker use with patients who had not." if medical else "Compare existing dark-mode and default-mode users.", "comparison-is-intervention"),
            ),
            "hint": "Which action changes the variable's value, rather than selecting people by a value they already have?",
            "explanation": "An intervention actively sets the variable. Filtering or comparing existing records leaves their values unchanged.",
            "accepted": "Correct. This action actively sets the variable being studied.",
            "rejected": "Not yet. Selecting or comparing existing records does not change the values they already contain. Look for the action that sets the variable.",
        },
        {
            "activity_id": "data-vs-assumptions.transfer", "prefix": "assumptions.transfer.observation",
            "title": "Read an observation from the records",
            "question": (
                "A clinic is checking its weekly tracker-use and nurse-contact records. Which statement can be read directly from these records?"
                if medical else
                "A software team is checking its weekly help-page and bug-report log. Which statement can be read directly from these records?"
            ),
            "options": (
                ("recorded-statement", "One patient used the tracker and had one nurse contact in the recorded week." if medical else "One user had four help-page visits and one bug report in the recorded week.", None),
                ("common-cause", "Symptom severity caused both tracker use and nurse contacts." if medical else "User confusion caused both help-page visits and bug reports.", "causal-assumption-read-as-data"),
                ("intervention-claim", "Making patients use the tracker would increase nurse contacts." if medical else "Reducing help-page visits would reduce bug reports.", "intervention-effect-read-from-records"),
            ),
            "hint": "Which option only reports entries that you can check in the table?",
            "explanation": "A row can support a statement about its recorded values. A claim about what causes them, or what an intervention would change, needs support beyond these records.",
            "accepted": "Correct. This statement describes a record without adding a causal explanation.",
            "rejected": "Not yet. Check whether the statement reports a visible record or adds a cause or an intervention result.",
        },
        {
            "activity_id": "probabilistic-effects.transfer", "prefix": "probability.transfer.mechanism",
            "title": "Distinguish outcomes from mechanisms",
            "question": (
                "Suppose an exercise programme lowers the chance of readmission, and patients still have different outcomes. What can you conclude about the mechanism behind them?"
                if medical else
                "Suppose a setup tutorial increases the chance of continued use, and users still have different outcomes. What can you conclude about the mechanism behind them?"
            ),
            "options": (
                ("not-determined", "These outcomes do not by themselves tell us whether the mechanism follows fixed rules or includes randomness.", None),
                ("random-required", "Different outcomes prove that the mechanism includes randomness.", "outcome-variation-proves-random-mechanism"),
                ("fixed-means-identical", "A fixed rule would give every patient the same outcome." if medical else "A fixed rule would give every user the same outcome.", "fixed-rule-means-identical-outcomes"),
            ),
            "hint": "Could people have different starting conditions even if the same fixed rule applies?",
            "explanation": "A fixed rule can give different outcomes when its inputs differ. Different outcomes across people therefore do not establish whether the mechanism itself includes randomness. The stated effect concerns a change in chance.",
            "accepted": "Correct. Variation across people does not identify whether a mechanism's rules include randomness.",
            "rejected": "Not yet. Think about a fixed rule applied to people with different starting conditions. Would it have to give them identical outcomes?",
        },
    )
    resources = {item["resource_id"]: item for item in data["resources"]}
    activities = {item["activity_id"]: item for item in data["activities"]}
    lessons = {item["concept_id"]: item for item in data["lessons"]}
    for case in cases:
        activity = activities[case["activity_id"]]
        old_choices = activity["choices"]
        right_index = next(i for i, choice in enumerate(old_choices) if choice["correct"])
        right = old_choices[right_index]
        wrong = [choice for choice in old_choices if not choice["correct"]]
        prefix = case["prefix"]
        templates = {
            "explanation": activity["explanation_resource_id"],
            "hint": wrong[0]["hint_resource_ids"][0],
            "accepted": right["consequence_resource_id"],
            "rejected": wrong[0]["consequence_resource_id"],
        }
        for suffix, template_id in templates.items():
            data["resources"].append({**resources[template_id],
                "resource_id": f"{prefix}.{suffix}", "text": case[suffix]})
        choices = []
        for index, (suffix, text, misconception) in enumerate(case["options"]):
            template = right if index == 0 else wrong[index - 1]
            choices.append({**template, "option_id": f"{prefix}.{suffix}", "text": text,
                "correct": index == 0, "misconception_id": misconception,
                "hint_resource_ids": [] if index == 0 else [f"{prefix}.hint"],
                "consequence_resource_id": f"{prefix}.{'accepted' if index == 0 else 'rejected'}"})
        accepted, *rejected = choices
        activity["choices"] = [*rejected[:right_index], accepted, *rejected[right_index:]]
        activity["explanation_resource_id"] = f"{prefix}.explanation"
        if activity.get("workbench"):
            if "introduction" in case:
                activity["workbench"]["introduction"] = case["introduction"]
            _set_table_question(resources, activity, case["question"])
        else:
            resources[activity["question_resource_id"]]["text"] = case["question"]
        lessons[activity["concept_id"]]["challenge_title"] = case["title"]

    # These are the default-visible definition and worked-example resources.
    association = lessons["observed-association"]
    resources[association["definition_resource_id"]]["text"] = (
        "An association is a pattern between recorded variables: knowing one gives information about the other. "
        "Values may rise together or move in opposite directions. For this comparison, keep each person's two values linked, "
        "or count combinations of values. Separate unlinked totals do not show that relationship."
    )
    resources[association["hook_resource_id"]]["text"] = (
        "Each patient's record pairs weekly walking with resting heart rate. More walking tends to go with a lower heart rate in these records."
        if medical else
        "Each person's record pairs weekly exercise with resting heart rate. More exercise tends to go with a lower heart rate in these records."
    )
    probability = lessons["probabilistic-effects"]
    resources[probability["definition_resource_id"]]["text"] = (
        "A causal effect can change an outcome's probability without guaranteeing the same outcome for everyone. "
        "A fixed rule can give different outcomes when people's starting conditions differ. "
        "A probability change does not tell us whether the underlying causal mechanisms are deterministic or random."
    )
    resources[probability["hook_resource_id"]]["text"] = (
        "Suppose a treatment raises the chance of recovery. A teaching model may use a fixed rule that depends on patients' starting conditions, "
        "so patients can still have different outcomes. A changed recovery rate alone does not show whether that rule includes randomness."
        if medical else
        "Suppose an extra tutorial raises the chance of passing. A teaching model may use a fixed rule that depends on each learner's prior knowledge, "
        "so learners can still have different outcomes. A changed pass rate alone does not show whether that rule includes randomness."
    )
