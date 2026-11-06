"""Author the compact Foundations revision following Kurt and Damian's reviews."""


# Current editorial changes preserve pack identity and scoring. The builder
# refreshes only the selected course outputs; historical JSON remains frozen.
LESSON_CORE = {
    "variables-and-values": (
        "Variables and recorded values",
        "A variable is a feature that can take different values, such as age or a count. A value is one entry for that feature. Which features we call variables here depends on what this table records.",
        "A recorded number is a value, not the variable's name. A setting such as the clinic can be a variable in another study if that study records different clinics.",
        "Name the recorded feature, then read its value for one case.",
    ),
    "observed-association": (
        "Describe the pattern in the records",
        "An association is a pattern between recorded variables: knowing one gives information about the other. They can rise together, or one can tend to fall as the other rises.",
        "Check the direction of the pattern. An association need not mean that both values increase.",
        "Describe which recorded values tend to occur together.",
    ),
    "association-is-not-causation": (
        "A pattern does not establish its cause",
        "An intervention actively sets a variable instead of only observing it. A causal effect is a difference in an outcome, or its probability, when we set that variable differently. Observing an association alone does not establish that effect.",
        "Do not conclude causation from co-occurrence. A possible shared cause is an explanation to investigate, not proof that no other effect exists.",
        "Separate what the records show from what changing a variable would do.",
    ),
    "treatment-and-outcome": (
        "Specify the change and its outcome",
        "A causal question asks what would change if we intervened. The treatment is the change we are considering; the outcome is the result we care about. Comparing existing treatment groups asks a different question.",
        "Calling something a treatment does not show that it helps. The question must specify the change and the outcome.",
        "Ask: what would happen to this outcome if we made this change?",
    ),
    "observation-vs-intervention": (
        "Recording a value or actively setting it",
        "Observation records a variable's existing values. An intervention actively sets or changes that variable instead of leaving its usual causes to determine it. Selecting records with a value is not the same as setting the value.",
        "Assigning a plan is not necessarily the same as controlling what someone actually does. Name the variable that the action directly changes.",
        "Identify what was actively changed, not just what was measured.",
    ),
    "world-data-model": (
        "The system, the data and the model",
        "The world is the system being studied. Data are recorded values of one or more variables. A model describes how those values could be generated; it is an explanation, not another measurement.",
        "A plausible explanation can still be wrong. Compare the model with evidence rather than treating it as a recorded fact.",
        "Distinguish the system, its recorded values and an explanation of them.",
    ),
    "data-vs-assumptions": (
        "An observation or an additional assumption",
        "Data describe recorded values and patterns. A causal assumption adds a claim about what produces those patterns. Keep the observed pattern separate from the explanation proposed for it.",
        "A familiar explanation is not automatically measured by the available columns.",
        "State what the records contain and what the explanation also assumes.",
    ),
    "basic-dag-language": (
        "Read a causal graph",
        "In a directed acyclic graph (DAG), arrows have a direction, and following them forward cannot lead back to the starting variable. A path connects variables regardless of arrow direction; a directed path follows every arrow forward. The graph represents a model's causal assumptions.",
        "A causal graph is a model. Its assumptions can be right or wrong; an arrow is not a measured effect size.",
        "Read the variables and arrows, then check whether a route follows every arrow forward.",
    ),
    "probabilistic-effects": (
        "A changed chance is not a guarantee",
        "A causal effect can change an outcome's probability without guaranteeing the same outcome for everyone. This concerns chances across cases; it does not tell us whether the underlying causal mechanisms are deterministic or random.",
        "One unsuccessful case does not by itself contradict a higher success probability. These hypothetical examples are not real treatment findings.",
        "Keep a change in probability separate from a guarantee for every person.",
    ),
}

EXAMPLES = {
    "general": {
        "variables-and-values": (
            "An IT service records failed-login alerts and password-reset requests for each hour. Counts such as 3 and 8 are values; the two count features are variables.",
            "Each row concerns one hour at the same IT service.",
            "The recorded features are the failed-login alert count and password-reset request count.",
            "Three alerts is one value. The service's name describes the setting; this table does not record different service names.",
        ),
        "observed-association": (
            "People reporting more exercise also tend to report lower resting heart rates. The pattern has one value increasing while the other decreases.",
            "The two variables are reported exercise and resting heart rate.",
            "Higher exercise values tend to occur with lower heart-rate values in these records.",
            "This association describes the pattern without explaining why it occurs.",
        ),
        "association-is-not-causation": (
            "Ice-cream sales and sunglasses sales rise together. That does not tell us whether changing ice-cream sales would change sunglasses sales.",
            "The records show sales rising together.",
            "Sunny weather could increase both kinds of sale. This is a proposed explanation, not a conclusion established by the records.",
            "Changing ice-cream sales is an intervention question. Its effect cannot be read from the association alone.",
        ),
        "treatment-and-outcome": (
            "A college asks whether offering extra study sessions would improve later test scores. The session offer is the treatment; the later score is the outcome.",
            "Specify the offers being compared, such as an extra session or the usual offer.",
            "Name the outcome and when it is measured: the later test score.",
            "Comparing people who already attended different numbers of sessions does not by itself answer what changing the offer would do.",
        ),
        "observation-vs-intervention": (
            "An IT team can read an existing reminder setting or actively switch it on for a test. Only the second action intervenes on that setting.",
            "Reading the existing setting leaves the process that chose it unchanged.",
            "Switching the reminder setting on actively sets that variable.",
            "Whether users then respond is a separate outcome; setting the reminder does not guarantee their response.",
        ),
        "world-data-model": (
            "Temperature and electricity-use readings are data. An explanation of how temperature changes demand is a model of how those readings arise.",
            "The world includes the weather, buildings and people using electricity.",
            "The data contain recorded temperature and electricity-use values.",
            "The proposed model explains how those processes could produce the readings. Check it against evidence before accepting it.",
        ),
        "data-vs-assumptions": (
            "Museum donations and cafe sales rise together. More visitors could cause both, but that explanation is not directly recorded by the two totals.",
            "The recorded variables are donation totals and cafe sales.",
            "Visitor numbers are a proposed shared cause of both totals.",
            "The records show an association. The proposed explanation also assumes visitor numbers influence both.",
        ),
        "basic-dag-language": (
            "The umbrella model says rain affects both umbrella carrying and pavement wetness. A causal graph draws those assumptions as arrows between variables.",
            "Rain, umbrella carrying and pavement wetness are variables, represented by nodes. The two arrows show the model's assumed causes.",
            "Umbrella carrying <- Rain -> Pavement wetness is a path. It is not a directed path from umbrellas to wet pavement: the first arrow points the other way.",
            "Rain -> Umbrella carrying is a directed path. No sequence of forward arrows returns to Rain, so this graph has no directed cycle.",
        ),
        "probabilistic-effects": (
            "Suppose an extra tutorial increases the chance of passing an exam. Some learners may still not pass; a better chance is not a guarantee.",
            "The hypothetical comparison is an extra tutorial versus the usual teaching.",
            "The stated effect increases the chance of passing. It does not promise a pass for every learner.",
            "Different individual results do not tell us whether the underlying model uses random or deterministic mechanisms.",
        ),
    },
    "medical": {
        "variables-and-values": (
            "A clinic records age and resting heart rate for each patient. Age and heart rate are variables; 45 years and 72 beats per minute are values in one row.",
            "Each row concerns one patient at the same clinic.",
            "The recorded variables are age and resting heart rate.",
            "The clinic is the setting for this table. Clinic identity could be another variable if a different study recorded several clinics.",
        ),
        "observed-association": (
            "Patients reporting more weekly walking tend to have lower resting heart rates. This describes a pattern in their records.",
            "The recorded variables are weekly walking and resting heart rate.",
            "Higher walking values tend to occur with lower heart-rate values.",
            "This association describes the pattern without establishing its cause.",
        ),
        "association-is-not-causation": (
            "Patients receiving Treatment A recover less often in the records. This alone does not show whether giving Treatment A causes poorer recovery.",
            "The treated and untreated groups have different recorded recovery rates.",
            "Patients with more severe illness might be more likely to receive Treatment A. This is one possible explanation to investigate.",
            "The records alone establish neither harm nor benefit from changing treatment.",
        ),
        "treatment-and-outcome": (
            "A clinician asks whether changing a drug dose would change recovery. The dose is the treatment being considered; recovery is the outcome.",
            "Specify which dose would be changed and the alternative dose being compared.",
            "Specify the recovery outcome and when it would be assessed.",
            "A difference between existing dose groups is not by itself the effect of assigning different doses.",
        ),
        "observation-vs-intervention": (
            "Recording how long someone already slept is observation. In a hypothetical study, actively setting a wake-up time is an intervention on wake-up time.",
            "Reading an existing sleep duration only measures what happened.",
            "A hypothetical study might wake participants after a specified time asleep. That action changes sleep duration instead of only recording it.",
            "Assigning a suggested bedtime does not guarantee actual sleep duration. Distinguish the assigned plan from the sleep that occurs.",
        ),
        "world-data-model": (
            "Laboratory readings are data. A proposed explanation of how an illness produces those readings is a model.",
            "The world includes the patient's underlying biological processes.",
            "The data are the recorded values of measured clinical variables.",
            "The model proposes how the processes could generate the readings. It still needs to be checked against evidence.",
        ),
        "data-vs-assumptions": (
            "A review flag and more symptoms appear together in clinic records. Saying that illness severity causes both adds a proposed explanation.",
            "The available columns contain review flags and symptom counts.",
            "Illness severity is proposed as a shared cause of the flag and the symptoms.",
            "That causal explanation goes beyond the pattern in the two recorded columns.",
        ),
        "basic-dag-language": (
            "The umbrella example is a causal graph: its arrows represent the model's proposed causes. The same graphical language can express a clinical hypothesis.",
            "Each node is a variable. In the umbrella model, arrows from Rain to Umbrella carrying and Pavement wetness express the supplied assumptions.",
            "Umbrella carrying <- Rain -> Pavement wetness is a path, but not a directed path from umbrellas to wet pavement: the first arrow points the other way.",
            "A directed path follows every arrow forward. A directed cycle would return to its starting variable; the supplied umbrella graph has none.",
        ),
        "probabilistic-effects": (
            "Suppose a treatment increases the chance of recovery. Some treated patients may still not recover; a better chance is not a guarantee.",
            "The hypothetical comparison is receiving the treatment versus the specified alternative.",
            "A higher recovery probability still permits some patients not to recover.",
            "This probability statement does not determine whether the underlying causal model is random or deterministic.",
        ),
    },
}

STEP_TITLES = {
    "variables-and-values": ("Identify a case", "Name the variables", "Separate names from values"),
    "observed-association": ("Identify the variables", "Read the direction", "Describe, do not explain"),
    "association-is-not-causation": ("Describe the records", "Consider another explanation", "Ask what changing something would do"),
    "treatment-and-outcome": ("Name the change", "Name the outcome", "Distinguish the question from a group comparison"),
    "observation-vs-intervention": ("Observe an existing value", "Actively change a value", "Check what the action controls"),
    "world-data-model": ("The system", "The recorded values", "The proposed explanation"),
    "data-vs-assumptions": ("Read the columns", "Identify the explanation", "Separate the two claims"),
    "basic-dag-language": ("Read the nodes and arrows", "A path need not follow arrow direction", "A directed path follows arrows forward"),
    "probabilistic-effects": ("Specify the comparison", "Allow different outcomes", "Keep the statement's scope clear"),
}


EXAMPLE_LABELS = {
    "general": {
        "variables-and-values": "Example IT-service records; not operational data.",
        "observed-association": "Hypothetical exercise records; not study findings.",
        "association-is-not-causation": "Hypothetical city records and a proposed explanation.",
        "treatment-and-outcome": "Hypothetical study-session offer; no benefit is established.",
        "observation-vs-intervention": "Hypothetical reminder setting; no effect on responses is established.",
        "world-data-model": "Hypothetical electricity readings and a proposed explanation.",
        "data-vs-assumptions": "Hypothetical museum records and a proposed explanation.",
        "basic-dag-language": "Hypothetical umbrella model; arrows show assumptions, not measured effects.",
        "probabilistic-effects": "Hypothetical example; no real-world effect is claimed.",
    },
    "medical": {
        "variables-and-values": "Example clinic records; not patient data.",
        "observed-association": "Hypothetical walking records; not a finding about heart health.",
        "association-is-not-causation": "Treatment A and these records are hypothetical; explanations need testing.",
        "treatment-and-outcome": "Hypothetical treatment question; no benefit or dose recommendation.",
        "observation-vs-intervention": "Hypothetical sleep example; no real intervention or health effect.",
        "world-data-model": "Hypothetical laboratory readings and an unverified illness model.",
        "data-vs-assumptions": "Hypothetical clinic records and a proposed explanation.",
        "basic-dag-language": "Hypothetical umbrella model; arrows show assumptions, not measured effects.",
        "probabilistic-effects": "Hypothetical example; no real-world effect is claimed.",
    },
}


def apply_learner_revision(data: dict, profile_id: str) -> None:
    """Revise a new pack's authored teaching copy without touching runtime state."""

    if profile_id not in EXAMPLES:
        raise ValueError("Foundations learner revision requires general or medical")
    medical = profile_id == "medical"
    resources = {item["resource_id"]: item for item in data["resources"]}
    activities = {item["activity_id"]: item for item in data["activities"]}
    updates = {}
    for lesson in data["lessons"]:
        concept_id = lesson["concept_id"]
        title, definition, pitfall, takeaway = LESSON_CORE[concept_id]
        hook, *steps = EXAMPLES[profile_id][concept_id]
        lesson["title"] = title
        updates[lesson["example_label_resource_id"]] = EXAMPLE_LABELS[profile_id][concept_id]
        for field, text in (("hook", hook), ("definition", definition), ("pitfall", pitfall), ("takeaway", takeaway)):
            updates[lesson[field + "_resource_id"]] = text
        for step, step_title, text in zip(lesson["worked_steps"], STEP_TITLES[concept_id], steps, strict=True):
            step["title"] = step_title
            updates[step["resource_id"]] = text
        if not medical and concept_id in {"variables-and-values", "treatment-and-outcome", "observation-vs-intervention"}:
            lesson["scenario_image"] = None
        if not medical and concept_id == "observed-association":
            lesson["scenario_image"] = {
                "path": "media/causality-m0/observed-association-park-v2.png",
                "alt_text": "Adults after exercise in a park. Illustration only.",
            }
        if concept_id == "variables-and-values":
            lesson["challenge_title"] = "Identify variables in a different table"
            if not medical:
                updates[lesson["pitfall_resource_id"]] = (
                    "A recorded number is a value, not the variable's name. The IT service is the setting for this table; "
                    "service identity could be another variable in another study that records different services."
                )
            updates[lesson["example_label_resource_id"]] = (
                "Example clinic records; not patient data." if medical
                else "Example IT-service records; not operational data."
            )
            if medical and lesson.get("scenario_image"):
                lesson["scenario_image"]["alt_text"] = (
                    "A clinician and patients in a clinic. Illustration only; not the exercise data."
                )
        elif concept_id == "basic-dag-language":
            lesson["challenge_title"] = "Follow a route through a proposed causal graph"
            if lesson.get("worked_graph"):
                lesson["worked_graph"]["label"] = "The supplied umbrella model"
                updates[lesson["worked_graph"]["note_resource_id"]] = (
                    "This graph represents the supplied umbrella model; the observations alone did not establish it."
                )
        elif concept_id == "probabilistic-effects":
            updates[lesson["example_label_resource_id"]] = "Hypothetical example; no real-world effect is claimed."
        if concept_id == "association-is-not-causation" and lesson.get("worked_graph"):
            updates[lesson["worked_graph"]["note_resource_id"]] = (
                "This is one proposed explanation, not a graph established by the records."
            )

    variable_cases = (
        (
            "A clinic table records each patient's age and resting heart rate. One row contains 45 years and 72 beats per minute. Which list names the two variables recorded in this table?",
            ("Age and resting heart rate", "45 years and 72 beats per minute", "The clinic and age", "Age and 72 beats per minute"),
        ),
        (
            "A hospital table records systolic blood pressure and body temperature for each patient. One row contains 118 mmHg and 37.1 degrees C. Which list names the two variables recorded in this table?",
            ("Systolic blood pressure and body temperature", "118 mmHg and 37.1 degrees C", "The hospital and systolic blood pressure", "Systolic blood pressure and 37.1 degrees C"),
        ),
    ) if medical else (
        (
            "An IT-service table records failed-login alert count and password-reset request count for each hour. One row contains 3 alerts and 8 requests. Which list names the two variables recorded in this table?",
            ("Failed-login alert count and password-reset request count", "3 alerts and 8 requests", "The IT service and failed-login alert count", "Failed-login alert count and 8 requests"),
        ),
        (
            "An IT-service table records waiting time in minutes and message count for each support ticket. One row contains 12 minutes and 4 messages. Which list names the two variables recorded in this table?",
            ("Waiting time and message count", "12 minutes and 4 messages", "The IT service and waiting time", "Waiting time and 4 messages"),
        ),
    )
    for stage, (question, labels) in zip(("practice", "transfer"), variable_cases, strict=True):
        activity = activities[f"variables-and-values.{stage}"]
        updates[activity["question_resource_id"]] = (
            "A variable is a feature that can take different values. " + question
            if stage == "practice" else question
        )
        right = next(choice for choice in activity["choices"] if choice["correct"])
        wrong = next(choice for choice in activity["choices"] if not choice["correct"])
        right["text"] = labels[0]
        wrong.update(text=labels[1], misconception_id="value-is-variable")
        activity["choices"] = [right, wrong, *(
            {**wrong, "option_id": f"variables.{stage}.{suffix}", "text": label,
             "misconception_id": misconception}
            for suffix, label, misconception in (
                ("setting", labels[2], "setting-is-variable"),
                ("mixed", labels[3], "value-is-variable"),
            )
        )]
        if not medical:
            activity["scenario_image"] = None
        elif activity.get("scenario_image"):
            activity["scenario_image"]["alt_text"] = (
                "A clinician and patients in a clinic. Illustration only; not the exercise data."
            )

    updates.update({
        "association.question.practice": (
            "Clinic records show that patients reporting more weekly walking tend to have lower resting heart rates. Which statement describes this recorded pattern?"
            if medical else "Records show that people reporting more exercise tend to have lower resting heart rates. Which statement describes this recorded pattern?"
        ),
        "association.question.transfer": (
            "Clinic records show that patients using the patient portal more often also attend more scheduled appointments. Which statement describes this recorded pattern?"
            if medical else "A document-editing service records that people who save drafts more often also finish more documents. Which statement describes this recorded pattern?"
        ),
        "not-causation.question.practice": (
            "Clinic records show lower recovery rates among patients receiving Treatment A. Can these records alone tell us whether giving Treatment A causes poorer recovery?"
            if medical else "In city records, ice-cream sales and sunglasses sales rise together. Can these records alone tell us whether changing ice-cream sales would change sunglasses sales?"
        ),
        "not-causation.question.transfer": "A synthetic campus log records umbrella carrying and wet pavement. Would giving everyone an umbrella change how often the pavement is wet? Test your explanation.",
        "treatment.question.practice": (
            "A clinician is reviewing a patient's drug dose. Which question asks about the effect of a dose change on recovery?"
            if medical else "A college is reviewing its study-support programme. Which question asks about the effect of offering extra study sessions on later test scores?"
        ),
        "treatment.question.transfer": (
            "A physiotherapy team asks whether assigning a different weekly session schedule would change mobility. What does the team want to find out?"
            if medical else "A service team asks whether providing a setup tutorial would make more people keep using its service. What does the team want to find out?"
        ),
        "intervention.question.practice": (
            "A clinic records how long patients already slept. It does not change their sleep. What did the clinic do?"
            if medical else "An IT team records how long support tickets already took to resolve. It does not change the ticket process. What did the team do?"
        ),
        "intervention.question.transfer": (
            "A clinical team compares patients who already chose a symptom-tracking app with patients who did not. It assigns no app use. What did the team do?"
            if medical else "A service team compares people who already chose dark mode with people who did not. It assigns no settings. What did the team do?"
        ),
        "world-data-model.question.practice": (
            "A researcher proposes an explanation of how an illness produces laboratory readings. Is that explanation data or a model?"
            if medical else "A researcher proposes an explanation of how temperature changes produce different electricity-use readings. Is that explanation data or a model?"
        ),
        "world-data-model.question.transfer": (
            "A hospital engineer proposes how a device's internal calibration produces drifting laboratory readings. Is that explanation data or a model?"
            if medical else "An engineer proposes how a machine's internal calibration produces drifting sensor readings. Is that explanation data or a model?"
        ),
        "assumptions.question.practice": (
            "Clinic records contain only review flags and symptom counts. The two occur together. The team says illness severity causes both. What is the status of that causal explanation?"
            if medical else "A dataset contains only umbrella carrying and pavement wetness. They occur together. A researcher says rain causes both. What is the status of that causal explanation?"
        ),
        "assumptions.question.transfer": (
            "Clinic records contain only symptom-tracker use and nurse-contact counts. They rise together. The team says symptom severity causes both. What is the status of that causal explanation?"
            if medical else "A software-service log contains only help-page visits and bug-report counts. They rise together. The team says confusion causes both. What is the status of that causal explanation?"
        ),
        "dag.question.practice": (
            "A proposed causal graph contains Drug dose -> Symptom score. What does this arrow mean in the model?"
            if medical else "A proposed causal graph contains Sleep -> Concentration. What does this arrow mean in the model?"
        ),
        "dag.question.transfer": (
            "A proposed causal graph contains Physiotherapy -> Mobility -> Discharge readiness. How would you describe the route from Physiotherapy to Discharge readiness?"
            if medical else "A proposed causal graph contains Tutorial -> Continued use -> Renewed subscription. How would you describe the route from Tutorial to Renewed subscription?"
        ),
        "probability.question.practice": (
            "Suppose a treatment raises the chance of recovery, but some treated patients still do not recover. What follows?"
            if medical else "Suppose an extra tutorial raises the chance of passing an exam, but some learners still do not pass. What follows?"
        ),
        "probability.question.transfer": (
            "Suppose an exercise programme lowers the chance of readmission, but some patients in the programme are still readmitted. What follows?"
            if medical else "Suppose a setup tutorial increases the chance that people keep using a digital service, but some people still leave. What follows?"
        ),
        "integrated.question": (
            "A clinic records how long patients choose to sleep, their concentration and their recovery. A team draws a causal graph to explain their association. Which conclusion do the records alone support?"
            if medical else "A team records how long people choose to sleep, their concentration and their recovery. It draws a causal graph to explain their association. Which conclusion do the records alone support?"
        ),
        "variables.hint": "Look for feature names used across rows, not one row's values or the study's setting.",
        "variables.explanation": "Variables name the features recorded across rows. A particular number is a value of a variable, and the setting is not another recorded column in these tables.",
        "variables.consequence.accepted": "Correct. This list names both recorded features rather than particular values or the setting.",
        "variables.consequence.rejected": "This list includes a value or setting instead of two recorded features. Compare each item with the columns described in the question.",
        "association.hint": "Compare whether the values tend to rise together or whether one falls as the other rises.",
        "association.explanation": "An association describes how recorded variables vary together. State the direction of that pattern before proposing its cause.",
        "association.consequence.accepted": "Correct. This statement describes the pattern in the recorded variables.",
        "association.consequence.rejected": "This reverses the stated pattern. Compare the direction of change in the two recorded variables.",
        "not-causation.explanation": LESSON_CORE["association-is-not-causation"][1],
        "not-causation.hint": "Separate the pattern in the records from what would happen if one variable were deliberately changed.",
        "not-causation.consequence.accepted": "Correct. These records alone do not establish the effect of changing one variable.",
        "not-causation.consequence.rejected": "The pattern does not tell us what an intervention would do. Another explanation could produce the same observed pattern.",
        "treatment.explanation": LESSON_CORE["treatment-and-outcome"][1],
        "treatment.hint": "Identify the deliberate change and the result the question asks about.",
        "treatment.consequence.accepted": "Correct. It asks what would happen if the treatment or offer were changed.",
        "treatment.consequence.rejected": "The question asks about an active change, not only a difference between existing groups.",
        "intervention.explanation": LESSON_CORE["observation-vs-intervention"][1],
        "intervention.hint": "Was the team actively changing the variable, or only recording what had already happened?",
        "intervention.consequence.accepted": "Correct. The team recorded existing values instead of actively changing them.",
        "intervention.consequence.rejected": "Recording or comparing existing values is different from actively setting the variable.",
        "world-data-model.explanation": LESSON_CORE["world-data-model"][1],
        "world-data-model.hint": "Is this a set of recorded variable values, or an explanation of how those values arise?",
        "world-data-model.consequence.accepted": "Correct. The proposed explanation is a model of how the recorded values could arise.",
        "world-data-model.consequence.rejected": "Data are the recorded variable values. The explanation of how those values arise is a model.",
        "assumptions.explanation": LESSON_CORE["data-vs-assumptions"][1],
        "dag.explanation": LESSON_CORE["basic-dag-language"][1],
        "dag.hint": "Distinguish a variable from an arrow or a route. A directed path follows every arrow forward.",
        "dag.consequence.accepted": "Correct. Nodes represent variables; arrows and paths describe the model's proposed causal structure.",
        "dag.consequence.rejected": "Check whether the question asks about one variable, one causal arrow, or a route connecting several variables.",
        "probability.explanation": LESSON_CORE["probabilistic-effects"][1],
        "probability.hint": "Does the example state a change in chance, or promise the outcome for every person?",
        "probability.consequence.accepted": "Correct. The chance changes, but the outcome is not guaranteed for every individual.",
        "probability.consequence.rejected": "The example explicitly allows different individual outcomes. A changed chance is not a guarantee for everyone.",
        "integrated.consequence.accepted": "Correct. An association and a proposed graph do not by themselves establish the effect of an intervention.",
        "integrated.consequence.rejected": "The graph is an explanation to check, not extra evidence that changing sleep would improve recovery.",
    })
    # The displayed final table summarizes groups, not individual patient rows.
    final_seven = activities.get("m0-final-quiz.07")
    if final_seven is not None:
        question = (
            "The summary table lists attendance groups, group sizes and mean follow-up scores. Which statement adds a causal assumption to these summaries?"
        )
        old_question = resources[final_seven["question_resource_id"]]["text"]
        suffix = old_question.partition("\n\nEarlier observed groups:")[2]
        updates[final_seven["question_resource_id"]] = question + (
            "\n\nEarlier observed groups:" + suffix if suffix else ""
        )
        final_seven["workbench"]["prompt"] = question
        for choice in final_seven["choices"]:
            if choice["option_id"] == "m0-final-quiz.07.final.option.4":
                choice["text"] = "The table lists an attendance group and its recorded mean score"
    final_nine = activities.get("m0-final-quiz.09")
    if final_nine is not None:
        target = "mobility" if medical else "reading"
        people = "patients" if medical else "people"
        question = (
            f"Suppose the chance of reaching a {target} target is 0.40 under a one-session offer and 0.60 under a three-session offer. Some {people} offered three sessions still miss the target. Which interpretation is correct?"
        )
        old_question = resources[final_nine["question_resource_id"]]["text"]
        suffix = old_question.partition("\n\nEarlier observed groups:")[2]
        updates[final_nine["question_resource_id"]] = question + (
            "\n\nEarlier observed groups:" + suffix if suffix else ""
        )
        final_nine["workbench"]["prompt"] = question
        explanation = (
            "In this hypothetical model, the chance increases by 0.20, or 20 percentage points. A probability of 0.60 still permits failures. These assumed probabilities are not a real-world effect estimate."
        )
        updates[final_nine["explanation_resource_id"]] = explanation
        updates["m0-final-quiz.09.final.accepted"] = explanation
        updates["m0-final-quiz.09.final.rejected"] = "Not quite. " + explanation
    for index, hint in enumerate((
        "Separate the recorded feature's name from one participant's value.",
        "Read the observed group means without assuming how assignment would change the outcome.",
        "Consider whether people who chose different attendance could also differ in other ways.",
        "Find the question about deliberately changing an offer, rather than describing existing records.",
        "Identify what the coordinator actively assigns; separate that assignment from its possible outcomes.",
        "Distinguish a proposed explanation from recorded variable values and from the system itself.",
        "Look for a statement about what causes the pattern, beyond what the summary columns record.",
        "Follow the arrows in order and check whether any forward route returns to its starting variable.",
        "Separate a changed chance from an individual guarantee and from a real-world finding.",
    ), start=1):
        resource_id = f"m0-final-quiz.{index:02d}.final.hint"
        if resource_id in resources:
            updates[resource_id] = hint
    choice_text = {
        "association.practice.yes": "More walking tends to go with lower heart rates in these records." if medical else "More exercise tends to go with lower heart rates in these records.",
        "association.practice.no": "More walking tends to go with higher heart rates in these records." if medical else "More exercise tends to go with higher heart rates in these records.",
        "association.transfer.yes": "More portal use tends to go with more attended appointments in these records." if medical else "More draft saving tends to go with more finished documents in these records.",
        "association.transfer.no": "More portal use tends to go with fewer attended appointments in these records." if medical else "More draft saving tends to go with fewer finished documents in these records.",
        "not-causation.practice.no": "No. The records alone do not establish what changing treatment would do to recovery." if medical else "No. The records alone do not establish what changing ice-cream sales would do to sunglasses sales.",
        "not-causation.practice.yes": "Yes. The recorded difference establishes what changing treatment would do to recovery." if medical else "Yes. The recorded rise together establishes what changing ice-cream sales would do to sunglasses sales.",
        "treatment.practice.yes": "How changing the drug dose would change recovery." if medical else "How changing the session offer would change later test scores.",
        "treatment.practice.no": "How existing dose groups differed in their recorded recovery rates." if medical else "How existing attendance groups differed in their recorded test scores.",
        "treatment.transfer.yes": "How changing the assigned session schedule would change mobility." if medical else "How providing the tutorial would change continued use.",
        "treatment.transfer.no": "How existing session attendance and mobility varied together." if medical else "How existing tutorial use and continued use varied together.",
        "intervention.practice.observation": "Observed patients' existing sleep durations." if medical else "Observed the existing ticket-resolution times.",
        "intervention.practice.intervention": "Intervened to set patients' sleep durations." if medical else "Intervened to set each ticket's resolution time.",
        "intervention.transfer.observation": "Observed patients' existing app choices." if medical else "Observed people's existing display choices.",
        "intervention.transfer.intervention": "Intervened to assign app use to patients." if medical else "Intervened to assign dark mode to people.",
        "assumptions.practice.assumption": "It is an additional causal assumption, not directly measured by those columns.",
        "assumptions.practice.data": "It is a direct observation of the cause measured by those columns.",
        "assumptions.transfer.assumption": "It is an additional causal assumption, not directly measured by those columns.",
        "assumptions.transfer.data": "It is a direct observation of the cause measured by those columns.",
        "dag.practice.arrow": "The model says changing drug dose could change symptom score." if medical else "The model says changing sleep could change concentration.",
        "dag.practice.value": "The arrow gives one patient's measured symptom score." if medical else "The arrow gives one person's measured concentration value.",
        "dag.transfer.path": "A directed path through Mobility." if medical else "A directed path through Continued use.",
        "dag.transfer.node": "One node: a single variable called Mobility." if medical else "One node: a single variable called Continued use.",
        "probability.practice.probabilistic": "Recovery becomes more likely, but is not guaranteed for every patient." if medical else "Passing becomes more likely, but is not guaranteed for every learner.",
        "probability.practice.deterministic": "Every patient given the treatment must recover." if medical else "Every learner given the tutorial must pass.",
        "probability.transfer.probabilistic": "Readmission becomes less likely, but remains possible for individual patients." if medical else "Continued use becomes more likely, but is not certain for every person.",
        "probability.transfer.deterministic": "No patient receiving the programme can be readmitted." if medical else "Every person given the tutorial must keep using the service.",
        "integrated.association-only": "The records describe an association; the graph adds an explanation that needs separate support.",
        "integrated.proves-intervention": "The recorded association proves that assigning more sleep would improve recovery.",
    }
    for stage in ("practice", "transfer"):
        choice_text[f"world-data-model.{stage}.model"] = "A model: an explanation of how the readings could be generated."
        choice_text[f"world-data-model.{stage}.data"] = "Data: values already measured and entered in the records."
    for resource_id, text in updates.items():
        resources[resource_id]["text"] = text
    for activity in data["activities"]:
        for choice in activity["choices"]:
            if choice["option_id"] in choice_text:
                choice["text"] = choice_text[choice["option_id"]]
                if choice["option_id"].startswith("association.") and not choice["correct"]:
                    choice["misconception_id"] = "association-direction-misread"
        if not medical and activity["activity_id"] in {"treatment-and-outcome.practice", "observation-vs-intervention.practice"}:
            activity["scenario_image"] = None
        if not medical and activity["activity_id"] == "observed-association.practice":
            activity["scenario_image"] = {
                "path": "media/causality-m0/observed-association-park-v2.png",
                "alt_text": "Adults after exercise in a park. Illustration only.",
            }
    for claim in data["claims"]:
        if claim["claim_id"] in {"causes-can-change-probability", f"foundation.{profile_id}.probabilistic-effects.reference"}:
            claim["proposition"] = (
                "A causal effect can change an outcome's distribution or probability without guaranteeing an identical outcome for all individuals. This probability statement does not require the underlying causal mechanisms to be stochastic."
            )
