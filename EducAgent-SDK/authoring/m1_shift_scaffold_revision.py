"""Novice-first copy and one-control guides for the unchanged Shift curriculum.

Apply after the historical 1.2.0 clarity revision. The new release is a copy;
this module changes no option identity, accepted answer, model or initial setup.
"""

from copy import deepcopy

if __package__:
    from .m1_shift_revision import CONCEPT_IDS
else:
    from m1_shift_revision import CONCEPT_IDS


def apply_shift_scaffold_revision(data: dict, profile_id: str) -> dict:
    """Retell one concrete story, teaching prediction before report generation."""
    if profile_id not in {"general", "medical"}:
        raise ValueError("shift scaffold revision requires general or medical")
    if data.get("pack_id") != f"causality.m1.shift.{profile_id}":
        raise ValueError("shift scaffold revision requires the matching shift profile pack")
    if tuple(item["concept_id"] for item in data["concepts"]) != CONCEPT_IDS:
        raise ValueError("shift scaffold revision requires the existing four-concept curriculum")
    if len(data["activities"]) != 16:
        raise ValueError("shift scaffold revision requires the existing sixteen activities")

    revised = deepcopy(data)
    resources = {item["resource_id"]: item for item in revised["resources"]}
    activities = {item["activity_id"]: item for item in revised["activities"]}
    medical = profile_id == "medical"
    site = "hospital" if medical else "warehouse"
    cases = "chest images" if medical else "parcels"
    condition = "an opacity is present" if medical else "a parcel is damaged"
    marker = "hospital marker" if medical else "warehouse label"
    measurement = "recorded opacity flag" if medical else "recorded parcel-damage flag"
    finding = "image finding" if medical else "damage finding from the photograph"
    physical = "the patient's condition" if medical else "the parcel's condition"
    target_description = (
        "whether an opacity is present: a cloudy area on a chest image"
        if medical else "whether a parcel is damaged"
    )
    reference_description = (
        "a preset checking answer for whether the opacity is present"
        if medical else "a preset checking answer for whether the parcel is damaged"
    )
    story = (
        "A hospital wants an assistant to predict whether an opacity is present on a chest image. "
        "An opacity is a cloudy area, not a diagnosis by itself. The assistant can read a hospital "
        "marker or a recorded opacity flag: a yes/no image finding. At the first hospital, the marker often matches the "
        "checking answer. Another hospital may mark images differently or record findings less reliably."
        if medical else
        "A warehouse wants an assistant to predict whether a parcel is damaged. The assistant can "
        "read a warehouse label or a recorded parcel-damage flag: a yes/no finding from a photograph. At the first warehouse, "
        "the label often matches the checking answer. Another warehouse may label parcels differently "
        "or take photographs that make damage harder to record."
    )

    lessons = (
        (
            "Will the prediction work at another " + site + "?",
            "Distribution shift means that the cases, measurements or process producing an outcome change between settings. An old test score describes the old setting; it does not guarantee performance after a change.",
            story,
            (
                ("The job and its checking answer", f"The assistant predicts {target_description}. A reference is a separate answer used to check the prediction. Here it is {reference_description}, set by the teaching model before any measurement error. It is not a real clinical or inspection review."),
                ("What can be different?", f"The new {site} may see different cases, use different {marker}s or record the {finding} less reliably. These are different changes. A fall in accuracy tells us that predictions are worse on the tested cases, not which change caused every error."),
                ("A check that matches the proposed use", f"Test records from the intended {site}, with suitable checking answers. Keep them separate from records used for training or tuning. In the practice, you will change how often the {marker} matches the reference and test one fixed prediction rule."),
            ),
            "Splitting the first site's records again does not test new measurements at another site.",
            "Name the setting that changed, then test predictions on cases representing that setting.",
        ),
        (
            "Does the assistant rely on the " + marker + "?",
            "A shortcut is an input that predicts well in one setting because it is associated with the answer there. That does not mean changing the input changes the underlying outcome. A plausible causal feature also needs reliable measurement and new-setting checks.",
            f"The {marker} often matches whether {condition}. Suppose we edit only that recorded marker. Could the assistant's prediction change while {physical} stays the same?",
            (
                ("A clue is not an outcome-changing action", f"The {marker} is a clue, sometimes called a cue. It can be useful because different kinds of cases arrive at different {site}s. Relabelling a recorded input is not an action that changes {physical}. Prediction and changing an outcome are different tasks."),
                ("Follow the same case", f"In the practice, compare the same case number before and after the marker edit. Its checking answer and {measurement} stay fixed. If the prediction changes, you have shown dependence on the marker. You have not shown that the marker caused or treated the underlying condition."),
                ("What a causal explanation adds", "A causal explanation asks which processes produce the outcome and the recorded inputs. It can explain why a site shortcut may fail when those processes change. Other inputs still need checking: a feature proposed as a cause can be measured poorly or used for kinds of cases that have not been tested."),
            ),
            "Changing a prediction is not the same as changing the condition being predicted.",
            "Ask what changed: the recorded input, the assistant's answer, or the underlying condition.",
        ),
        (
            "What if the measurement becomes less reliable?",
            "An invariant relationship stays the same across the settings compared. Using it elsewhere assumes the relevant outcome process, measurements and range of cases remain suitable. Stable results are limited evidence, not proof of a cause or a guarantee for every new setting.",
            f"The assistant now reads the {measurement} instead of the {marker}. Ignoring the marker avoids that shortcut. But what happens if the {measurement} is recorded incorrectly more often?",
            (
                ("The rule still reads a measurement", f"The image-reading rule copies the {measurement}. The teaching model first sets the checking answer and then sometimes records the opposite finding. This measurement is not a feature established to cause the target. Reading it is not direct access to truth."),
                ("Stable under which change?", "A rule that ignores the site marker can stay unchanged when only the marker changes. It may still fail when its own measured input becomes less reliable. A causal account helps identify the processes assumed to stay fixed and distinguish changes that test different assumptions."),
                ("Compare relevant cases, not just one average", "The same overall accuracy can hide different errors in different groups. A conditional comparison checks outcomes for cases with the same relevant measured features, over values represented in both settings. The range represented is called support. Reference-group error rates shown in this exercise are useful error checks, not a direct test of that outcome-given-features relationship or a unique causal graph."),
            ),
            "Stable scores under a marker change do not validate a new measurement process or an unseen kind of case.",
            "Say what was held fixed, what changed and which changes still need testing.",
        ),
        (
            "Write a report from the record",
            "Generation produces an output such as a report. Source fidelity means keeping the facts actually recorded without inventing details. It is not proof that the source is true. Coverage is the share of cases receiving a full report.",
            f"So far the assistant has predicted {target_description}. Now it must write a short report from the recorded finding and its context. Some records do not contain the required context. Should it fill the gap or leave the report for review?",
            (
                ("Check what the source actually says", f"The source is the {measurement} plus the context, if available. A draft that reverses a recorded finding fails source fidelity. A faithful copy can still preserve a wrong measurement, so comparing with the source is different from checking with the independent reference."),
                ("Two report rules", "Complete every report writes a full draft and fills missing context with an unsupported detail. Preserve source facts copies available facts and withholds a full report when required context is absent. These are fixed teaching templates, not an LLM. Changing the report rule does not repair the input measurement."),
                ("Show both the errors and the missing reports", "Compare unsupported additions and full-report coverage over all cases. Also count source-supported reports among those issued. Withholding can reduce unsupported additions while leaving fewer cases with reports. If none are issued, fidelity among issued reports is undefined, not perfect. Withholding an unsupported claim, or abstaining, needs a clear review path and does not verify the missing fact."),
            ),
            "Fluent wording does not prevent invented facts, and copying the source can preserve a mistake. A withheld report has not supplied a correct answer.",
            "Check prediction accuracy, source fidelity and coverage separately; make unsupported cases visible for review.",
        ),
    )
    for lesson, copy in zip(revised["lessons"], lessons, strict=True):
        title, definition, hook, details, pitfall, takeaway = copy
        lesson["title"] = title
        lesson["challenge_title"] = "Try the idea in another situation"
        for field, text in (("definition", definition), ("hook", hook), ("pitfall", pitfall), ("takeaway", takeaway)):
            resources[lesson[field + "_resource_id"]]["text"] = text
        for step, (heading, text) in zip(lesson["worked_steps"], details, strict=True):
            step["title"] = heading
            resources[step["resource_id"]]["text"] = text

    def question(activity_id, prompt, correct, alternatives, hint, accepted, rejected):
        activity = activities[activity_id]
        copy = {activity_id + ".supported": correct}
        copy.update({activity_id + f".alternative-{index}": text for index, text in enumerate(alternatives, 1)})
        if set(copy) != {choice["option_id"] for choice in activity["choices"]}:
            raise ValueError("scaffold wording must preserve every existing answer option")
        for choice in activity["choices"]:
            choice["text"] = copy[choice["option_id"]]
            resources[choice["consequence_resource_id"]]["text"] = accepted if choice["correct"] else rejected
            for hint_id in choice.get("hint_resource_ids", ()):
                resources[hint_id]["text"] = hint
        resources[activity["explanation_resource_id"]]["text"] = accepted
        grounded = prompt
        if activity.get("workbench"):
            activity["workbench"]["prompt"] = prompt
            tables = ["\n".join((table["label"], " | ".join(table["columns"]),
                      *(" | ".join(row) for row in table["rows"]), table.get("note", "")))
                      for table in activity["workbench"]["tables"]]
            grounded += "\n\nRecords available in this step:\n" + "\n\n".join(tables)
        resources[activity["question_resource_id"]]["text"] = grounded

    question(CONCEPT_IDS[0] + ".quiz",
        f"An assistant predicts whether {condition}. It was tested at one {site}, but a second {site} records images differently. How should the team test it at the second site?",
        "Test separate cases from the new site with suitable checking answers.",
        ("Split the first site's records again and use that score.",
         "Match the new case mix but do not check the changed measurements."),
        "Which records contain the conditions the assistant will now face?",
        "Records from the new site let the team check performance with the changed measurements. Use suitable checking answers and keep these records separate from training and tuning. Splitting the old records again can miss those measurement errors.",
        "Where did the test records come from? Check whether they include the new measurements.")
    question(CONCEPT_IDS[0] + ".challenge",
        ("An opacity predictor scored 90% at its original hospital. A second hospital changes both scanner settings and patient mix. Its new test score is 70%. What can we conclude from these tests?" if medical else
         "A parcel-damage predictor scored 90% at its original warehouse. A second warehouse changes both camera settings and parcel mix. Its new test score is 70%. What can we conclude from these tests?"),
        "Accuracy was lower on the new test, but the tests do not isolate the cause.",
        ("The changed recording settings caused the entire drop in accuracy.",
         "The old score still establishes 90% accuracy for the new site."),
        "Could these tests separate the effects of the recording settings from those of the case mix?",
        "Recording settings and case mix both changed, so these tests do not show how much each contributed to the lower accuracy.",
        "Read the new result and list both changes. The comparison does not hold one fixed while testing the other.")
    question(CONCEPT_IDS[1] + ".quiz",
        f"The assistant reads the {marker}. We edit only that recorded marker; {physical} stays fixed. Its prediction changes. What have we learned?",
        "The prediction depends on the marker; the underlying condition stayed the same.",
        ("The marker edit changed the underlying condition because the prediction changed.",
         "Removing the marker validates all other inputs without further testing."),
        "Separate the input, the prediction and the condition being described.",
        "Changing only the recorded marker changed the prediction while the underlying condition stayed fixed. The other inputs still need testing.",
        "Which part of the case did the edit change, and which part stayed fixed?")
    question(CONCEPT_IDS[1] + ".challenge",
        ("The teaching model assumes blood oxygen level affects an exercise-test score. A new device measures blood oxygen poorly. Does that causal role guarantee reliable score predictions?" if medical else
         "The teaching model assumes thicker cardboard reduces crushing damage. A new camera records thickness poorly. Does the causal role of thickness guarantee reliable damage predictions?"),
        "No. Check the measurements and the predictions in the new setting.",
        ("Yes. A causal role makes the old rule reliable despite measurement errors.",
         "No. A feature cannot help predict an outcome until it has been experimentally changed."),
        "The assistant receives a measured value, not direct access to the proposed cause.",
        ("The assumed causal link does not fix an inaccurate blood-oxygen measurement. Check the predictions for the new cases and the process producing the exercise-test score." if medical else
         "The assumed causal link does not fix an inaccurate thickness measurement. Check the predictions for the new parcels and the process producing damage."),
        "Which value reaches the assistant: the feature itself or the device's recorded measurement?")
    question(CONCEPT_IDS[2] + ".quiz",
        ("In a teaching example, three hospitals compare adult chest images with the same recorded finding. They see similar opacity rates. Children's images were not tested. What does this support?" if medical else
         "Three warehouses compare cardboard parcels with the same recorded damage finding. They see similar damage rates. Padded bags were not tested. What does this support?"),
        "A stable relationship over those tested settings and ranges.",
        ("Proof of a cause, so no more new-site testing is needed.",
         "Reliable prediction for feature values absent from every tested site."),
        "Which kinds of cases did the teams actually compare?",
        ("The similar opacity rates support stability for adult images with the same recorded finding at the tested hospitals. They do not check children's images or establish a cause. A new hospital may also change the process producing the outcome." if medical else
         "The similar damage rates support stability for cardboard parcels with the same recorded finding at the tested warehouses. They do not check padded bags or establish a cause. A new warehouse may also change the process producing damage."),
        "Does the conclusion include cases that none of the three sites tested?")
    question(CONCEPT_IDS[2] + ".challenge",
        ("Two hospitals both report 85% accuracy. At the second, errors are higher for high-risk patients, and the patient mix differs. Does the shared overall score show that performance stayed stable for similar patients?" if medical else
         "Two warehouses both report 85% accuracy. At the second, errors are higher for fragile parcels, and the parcel mix differs. Does the shared overall score show that performance stayed stable for similar parcels?"),
        "No. The same average can hide different errors within relevant groups.",
        ("Yes. Equal averages establish stability despite the different group errors.",
         "Yes. Equal averages mean changing group sizes cannot affect the comparison."),
        "Could different group errors combine into the same overall score?",
        "An overall score mixes groups. Compare similar cases within those groups and check that there is enough data to judge uncertainty. A matching average alone does not do this.",
        "How do the reported errors differ within the groups? Consider that alongside the overall score.")
    source_negative = "no opacity identified" if medical else "no damage recorded"
    source_positive = "opacity present" if medical else "damage recorded"
    question(CONCEPT_IDS[3] + ".quiz",
        f"Now the assistant writes a report. The source says '{source_negative}', but the fluent draft says '{source_positive}'. Which check does the draft fail?",
        "Source fidelity: the draft reverses a recorded fact.",
        ("Only a style check; fluent wording is enough to verify the facts.",
         "Nothing; polished wording can replace the source's factual statement."),
        "Compare the findings stated in the source and the draft.",
        "The draft contradicts its source. Source fidelity checks recorded meaning; it does not establish whether that source itself is correct.",
        "Does the draft make the same factual claim as the source?")
    question(CONCEPT_IDS[3] + ".challenge",
        f"A new {site}'s record lacks a fact required for a full report. Its recording method has not been evaluated. What should the assistant do?",
        "Flag the gap, withhold the unsupported claim and request review.",
        ("Add a plausible missing fact and treat the completed draft as evidence.",
         "Issue the full report based on the old score without flagging the untested setup."),
        "Is the needed fact actually recorded, and was this setup tested?",
        "Flag the missing fact and untested setup for review. Withholding a claim does not verify the missing fact. Evidence is still needed before extending use to these cases.",
        "An old score and a confident draft cannot supply the missing source fact.")

    practices = (
        (
            "Prediction: a label that stops being useful",
            "prediction", "cue_accuracy_pct", f"{marker.capitalize()} matches the checking answer",
            f"Change only the percentage of cases in which the {marker} matches the preset checking answer. The assistant keeps reading that marker; all other settings stay fixed.",
            f"Test the {marker} prediction rule after the marking pattern changes.",
            f"How often will the marker-reading rule correctly predict whether {condition}, at 90% and then 50% marker agreement?",
            "Compare prediction accuracy in the two runs. Which marking patterns did you test? What would still need checking after a different measurement change?",
            "Predict accuracy at 90% agreement, then run the test. Set agreement to 50%, predict again and rerun. Compare the two accuracies and select Record my comparison before answering below. Keep all other settings fixed.",
            "What can you conclude from the two marker-agreement settings you tested?",
            "These runs measure this rule only under the settings tested; future changes still need checking.",
            ("The first score remains valid under a different, untested measurement process.",
             "The new score applies to every other site without further testing."),
            "Name the settings you actually ran. Which possible changes remain untested?",
            "You tested one fixed marker-reading rule under the marking patterns you ran. These runs do not check a different measurement process or other untested conditions.",
            "The experiment did not test every process that might change at another site.",
        ),
        (
            "Prediction: edit the marker, not the condition",
            "prediction", "flip_cue", f"Reverse the recorded {marker}",
            f"Switch this on to reverse the marker for the same cases. The preset checking answer and {measurement} stay fixed. The assistant still reads the marker.",
            "Distinguish changing an assistant's input from changing the underlying outcome.",
            f"If you reverse only the {marker}, what will happen to predictions? Will the checking answers change too?",
            f"Compare a matching case before and after the edit: marker, prediction and checking answer. Did this edit change {physical}, or just the assistant's input?",
            "Predict and run with the marker edit off. Then switch it on, predict again and rerun. Compare the same case numbers, select Record my comparison, and answer below. Keep all other settings fixed.",
            "The marker edit changes a prediction while its checking answer stays fixed. What did the edit test?",
            "Whether the prediction depends on the marker; the underlying condition stayed fixed.",
            ("Whether changing the marker improves the underlying condition.",
             "Whether the image-reading rule works under an untested recording process."),
            "What did the edit change, and what did the experiment hold fixed?",
            "The input marker changed while the checking answer and image measurement stayed fixed. The changed prediction therefore shows that the rule uses the marker, without showing a change in the underlying condition.",
            "Follow the unchanged checking answer. The experiment did not change the condition it represents.",
        ),
        (
            "Prediction: test the image-reading rule's limit",
            "prediction", "measurement_error_pct", f"{measurement.removeprefix('recorded ').capitalize()} recorded incorrectly",
            f"The assistant now reads the {measurement}, not the marker. Change only how often this measurement is the opposite of the preset checking answer. It is a noisy measurement, not a cause of the target.",
            "Test how measurement errors affect a rule that ignores the marker.",
            f"At 10% and then 40% measurement error, how often do you expect the image-reading rule to agree with the checking answer?",
            "Compare accuracy before and after the measurement change. Why does ignoring the marker not protect a rule from errors in the measurement it reads?",
            "Predict the result at 10% measurement error and run the test. Change the single control to 40%, predict again and rerun. Compare accuracy, select Record my comparison, and answer below. Keep all other settings fixed.",
            "An image-reading rule has the same accuracy after a marker change, but lower accuracy when its measurement worsens. What can we conclude?",
            "Stability under one change does not guarantee stability under a different change.",
            ("Stable results after one marker change validate every future measurement process.",
             "Two stable scores identify the feature's causal direction without other evidence."),
            f"The marker and the {measurement} are different inputs.",
            "The rule ignores the marker but reads a noisy measurement. Results from the tested changes do not establish a cause or cover every untested process. Grouping errors by the checking answer also does not directly test whether outcomes stay similar for the same measured features.",
            "Which input does the rule read? Check whether the conclusion assumes that input remains reliable after it changes.",
        ),
        (
            "Generation: choose what to do with a missing fact",
            "generation", "generator", "Report rule",
            "Change only the report rule. The prediction rule, measured findings and missing-context cases stay the same. The templates either complete every report or preserve source facts and withhold incomplete reports.",
            "Compare unsupported additions with the number of cases receiving a full report.",
            "What will happen to unsupported additions and full-report coverage if the assistant stops filling in missing context?",
            "Compare the same source and draft in each run. How did unsupported additions and coverage change? Did the report rule repair an incorrect source measurement?",
            "Predict and run with Complete every report. Change only to Preserve source facts, predict again and rerun. Compare drafts, unsupported additions and coverage, select Record my comparison, and answer below. Keep all input settings fixed.",
            "Some drafts copy a source measurement that disagrees with the checking answer. Other records lack required context. What can a source-preserving report rule establish?",
            "A faithful draft can retain a measurement error; it cannot supply missing context.",
            ("Preserving the source proves the recorded measurement agrees with the checking answer.",
             "Adding a plausible detail establishes the fact missing from the source record."),
            "Compare the prediction with its checking answer, and the draft with its recorded source.",
            "Reference accuracy checks predictions against the checking answer; source fidelity checks drafts against the recorded source. A faithful draft can preserve a measurement error. Withholding incomplete reports can avoid unsupported additions, but fewer cases receive reports and the missing facts remain unknown.",
            "A report rule cannot make an absent fact known or repair an incorrectly recorded measurement.",
        ),
    )
    for index, item in enumerate(practices, 1):
        (title, section, parameter_id, parameter_label, parameter_description, goal,
         prediction_prompt, comparison_prompt, instructions, *question_copy) = item
        activity = activities[f"m1-shift-investigation.{index:02d}"]
        experiment = activity["experiment"]
        experiment["title"] = title
        guide_story = story
        if section == "generation":
            guide_story = (
                f"The {site} assistant now writes a report from each {measurement} and its recording context. "
                "Only 60 of 100 records contain the required context; the other 40 lack it. "
                "A complete-looking draft can fill that gap without evidence. Checking what a report says is a separate task from checking a prediction."
            )
        elif index == 3:
            guide_story += f" For this stage the assistant reads the {measurement}, not the marker."
        metrics = [{"metric_label": "Reference prediction accuracy", "label": "Predictions matching the checking answer"}]
        if section == "generation":
            metrics = [
                {"metric_label": "Full-report coverage", "label": "Cases receiving a full report"},
                {"metric_label": "Reports with unsupported additions / all cases", "label": "Cases with an invented detail"},
            ]
        experiment["guide"] = {
            "story": guide_story, "goal": goal, "section": section,
            "parameter_id": parameter_id, "parameter_label": parameter_label,
            "parameter_description": parameter_description,
            "prediction_prompt": prediction_prompt, "comparison_prompt": comparison_prompt,
            "metrics": metrics,
        }
        resources[experiment["instructions_resource_id"]]["text"] = instructions
        activity["workbench"]["title"] = f"Practical exercise {index} of 4"
        activity["workbench"]["introduction"] = guide_story
        old_table = activity["workbench"]["tables"][0]
        old_table["label"] = f"Earlier {site} test, not the current run"
        old_table["rows"][0][0] = "Marker-reading rule"
        old_table["rows"][1][0] = "Image-reading rule"
        old_table["note"] = "Separate earlier test cases. These fixed scores are background, not the results of your current settings."
        question(activity["activity_id"], *question_copy)

    # Prediction comes first even in the final: report checks appear in item 4.
    final_story = (
        "A new hospital will use a readmission predictor. The team has checking answers for whether patients were readmitted and recorded measurements available before discharge."
        if medical else
        "A new town will use a flood-alert predictor. The team has checking answers for whether flooding occurred and recorded rainfall measurements."
    )
    for index in range(1, 5):
        workbench = activities[f"m1-shift-final.{index:02d}"]["workbench"]
        workbench["title"] = f"Final check {index} of 4"
        # The generator reuses one authored table object across final items.
        # Give each question its own view before narrowing the displayed rows.
        workbench["tables"] = deepcopy(workbench["tables"])
        workbench["introduction"] = final_story if index < 4 else (
            "The same team now checks an assistant that drafts a report from recorded facts. This report task needs its own checks, separate from predicting an event."
        )
        if index < 4:
            table = workbench["tables"][0]
            table["rows"] = table["rows"][:1]
            table["label"] = "Prediction test at the new site"
            table["note"] = "Both measurements and case mix changed. This table does not isolate the cause of the accuracy gap."
        else:
            table = workbench["tables"][0]
            table["label"] = "Report additions at the new site"
            table["columns"] = ["Report check", "Original site", "New site"]
            table["rows"] = [row for row in table["rows"]
                             if row[0] == "Drafts with unsupported factual additions"]
            if len(table["rows"]) != 1:
                raise ValueError("the generation final requires its authored unsupported-addition counts")
            table["note"] = "These counts describe unsupported additions, not writing quality or prediction accuracy. Missing source facts still need review."
    question("m1-shift-final.01",
        "The predictor is correct in 91/100 original-site cases and 72/100 new-site cases. Both measurements and case mix changed. What can we conclude from this comparison?",
        "Accuracy fell on this new test; the comparison does not isolate why.",
        ("The recording change alone caused the entire drop in prediction accuracy.",
         "The original test validates new-site use despite the observed performance gap."),
        "Which result did the team measure, and which changes did the tests separate?",
        "Accuracy was lower in the new test. Measurements and case mix both changed, so the comparison does not show how much each contributed to the drop.",
        "The test did not vary one condition while holding the others fixed. Do not assign the whole gap to one change.")
    question("m1-shift-final.02",
        ("The team can predict readmission using a hospital ID or a pre-discharge feature proposed to affect recovery. What can it conclude about these inputs?" if medical else
         "The team can predict flooding using a town ID or a rainfall feature proposed to affect flooding. What can it conclude about these inputs?"),
        "An ID can predict without causing the outcome; a causal feature still needs measurement checks.",
        ("The more predictive ID is the better action for improving the underlying outcome.",
         "A causal feature's old rule remains reliable despite a changed measurement process."),
        "Predicting an outcome, changing it and predicting reliably elsewhere are separate questions.",
        "An ID can predict because it records where cases came from; changing it need not change the outcome. A causal feature may help prediction, but its measurements, case ranges and outcome process still need checking.",
        "What would changing the ID do to the outcome? What still needs checking when the assistant receives a measured causal feature?")
    question("m1-shift-final.03",
        "Similar cases had similar outcomes in two old settings. The new setting changes the process producing the outcome. Can the team rely on the old relationship without checking it again?",
        "No. A changed outcome process falls outside the earlier stability argument.",
        ("Yes. Overlapping feature ranges validate reuse even after the outcome process changes.",
         "Yes. Two stable old settings already cover the new outcome-producing process."),
        "Which process did the earlier argument assume would stay the same?",
        "The relationship was stable in the old settings. Changing the process that produces the outcome changes an assumption behind reuse, even if measured feature ranges overlap.",
        "Which assumption changes when the process producing the outcome changes? The earlier tests did not cover that process.")
    question("m1-shift-final.04",
        "Now check report generation. New-site drafts add unsupported facts in 12/100 cases. A new record also lacks a needed fact and uses untested measurements. How should the team evaluate the outputs and handle this record?",
        "Check predictions and source fidelity separately; withhold the unsupported claim for review.",
        ("Check writing quality, fill the missing detail and use the draft as evidence.",
         "Use old-site accuracy to issue the complete report without flagging its missing fact."),
        "What evidence is needed to check each output, and what should happen when a required fact is missing?",
        "Reference accuracy checks predictions; source fidelity checks drafts. Flag the untested range and missing source fact for review instead of filling in the report. Keep monitoring the defined errors; these checks do not guarantee zero future failures.",
        "Would this plan leave an unsupported claim in the report? Include a review step for cases with missing evidence.")
    # Group the existing activities into two teaching sections. Their identities,
    # concept requirements and deterministic acceptance rules are unchanged.
    order = [concept + suffix for concept in CONCEPT_IDS[:3] for suffix in (".quiz", ".challenge")]
    order += [f"m1-shift-investigation.{index:02d}" for index in range(1, 4)]
    order += [CONCEPT_IDS[3] + suffix for suffix in (".quiz", ".challenge")]
    order += ["m1-shift-investigation.04"]
    order += [f"m1-shift-final.{index:02d}" for index in range(1, 5)]
    if set(order) != set(activities):
        raise ValueError("shift sections must retain every existing activity")
    revised["activities"] = [activities[activity_id] for activity_id in order]
    return revised
