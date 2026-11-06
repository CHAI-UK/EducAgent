"""Plain-language revision of the existing prediction/generation course.

This edits a copy of authored text only. The caller owns the new pack version,
output filename and registry selection; historical packs are never rewritten.
"""

from copy import deepcopy


CONCEPT_IDS = (
    "distribution-shift",
    "causal-vs-spurious-features",
    "invariance-across-environments",
    "when-predictions-can-still-fail",
)


def apply_shift_revision(data: dict, profile_id: str) -> dict:
    """Return revised copy, preserving curriculum, answer IDs and model rules."""
    if profile_id not in {"general", "medical"}:
        raise ValueError("shift revision requires general or medical")
    if data.get("pack_id") != f"causality.m1.shift.{profile_id}":
        raise ValueError("shift revision requires the matching shift profile pack")
    if tuple(item["concept_id"] for item in data["concepts"]) != CONCEPT_IDS:
        raise ValueError("shift revision requires the existing four-concept curriculum")
    if len(data["activities"]) != 16:
        raise ValueError("shift revision requires the existing sixteen activities")

    revised = deepcopy(data)
    resources = {item["resource_id"]: item for item in revised["resources"]}
    activities = {item["activity_id"]: item for item in revised["activities"]}
    medical = profile_id == "medical"
    site = "hospital" if medical else "warehouse"
    marker = "hospital marker" if medical else "warehouse label"
    flag = "opacity flag" if medical else "parcel-damage flag"
    source_example = "no opacity identified" if medical else "no crack found"
    reversed_example = "opacity present" if medical else "crack present"

    lessons = {
        CONCEPT_IDS[0]: (
            "Check what changes in a new setting",
            "Prediction estimates an outcome or label from available data; generation produces text from a source. Distribution shift is a change in the kinds of cases, their measurements, or the relationship being predicted.",
            ("A hospital teaching case has an assistant predict an opacity label and draft a report. Another hospital has different measurements and patients. The old test score need not apply there."
             if medical else
             "A warehouse assistant predicts parcel damage from recorded image features and drafts an inspection report. Another warehouse has different packaging and lighting. The old test score does not cover those conditions."),
            (
                ("Describe the change", f"List the cases, how measurements are taken and what the checking label means. A new {site} can change several of these at once. A different mix of cases is not the same change as a less reliable measurement or a different process producing the outcome."),
                ("Check the two outputs separately", "For a prediction, compare with a suitable reference label: a separate label used for checking. The teaching model sets its reference label before adding measurement error; it is not a real clinical or inspection review. Real use requires suitable checking information. Matching a report to its recorded source does not establish independent truth."),
                ("Use evidence from the intended setting", f"Evaluate on records from the intended {site} that were not used to fit or tune the system. Keep the checking-label definition appropriate. A fresh random split from the old site answers an old-site question; it does not recreate changed measurements or a new mix of cases."),
            ),
            "A lower score shows a performance gap, not which change caused it. An old-site score is not a guarantee for a new site.",
            "Name the new conditions, then check both predictions and reports under those conditions.",
        ),
        CONCEPT_IDS[1]: (
            "A useful clue is not automatically a cause",
            "A cue is a clue used for prediction. A spurious cue can predict well here without causing the outcome. A causal feature is proposed to affect the outcome; it is not a reliability guarantee. Poor measurement or a changed outcome process can still break prediction.",
            ("A hospital marker appears more often on images with an opacity. Editing only that marker can change a prediction without changing the patient's underlying condition."
             if medical else
             "A warehouse label appears more often on damaged parcels. Editing only that label in a recorded input can change a prediction without changing the parcel's condition."),
            (
                ("Separate a prediction from an intervention", f"Predicting the reference label asks what information the {marker} provides. An intervention actively changes a variable. Editing the recorded marker changes an input to the assistant, but the exercise keeps the underlying condition and its reference label fixed. A prediction change is not a change in that condition."),
                ("Explain why a shortcut can break", f"The {marker} can be associated with the kinds of cases sent to each {site}. That pattern may help in one dataset and fail when the case mix or marking convention changes. An association with a checking label is not evidence that changing the marker would improve the underlying outcome."),
                ("Check a causally motivated feature too", "A plausible causal explanation can help choose a feature, but the predictor receives its measured value. The experiment's content rule reads a noisy target measurement, not a feature established to cause the target. Poor measurement, a new range of cases or a changed outcome-producing process can invalidate prediction. Removing one shortcut does not validate all remaining inputs."),
            ),
            "Do not confuse changing a model's prediction with changing the outcome. A causal label also does not repair a bad measurement.",
            "Ask separately what helps predict, what would change the outcome and what has actually been tested.",
        ),
        CONCEPT_IDS[2]: (
            "Check what stays stable, and where",
            "An invariant relationship stays the same across the settings compared. Using it elsewhere needs assumptions about the outcome-producing process, measurements and the kinds of cases covered. Stability alone does not prove a cause or guarantee future performance.",
            ("Two hospitals report 85% overall accuracy, but the second makes more errors in one patient group. The same overall score can hide a change within that group."
             if medical else
             "Two warehouses report 85% overall accuracy, but the second makes more errors on fragile parcels. The same overall score can hide a change within that group."),
            (
                ("Compare similar cases", "A conditional comparison compares outcomes or errors for cases with the same relevant measured features. An overall average mixes those cases together. Differences in group sizes can hide different group errors. Check the relevant groups, enough observations and a consistent checking-label definition rather than relying on equal overall scores."),
                ("State the assumptions", "A mechanism is the process producing an outcome from its causes. A stability argument may assume this process stays the same while site labels or the case mix change. It also needs suitable measurements. If the new setting changes the outcome-producing process itself, the old argument does not automatically apply."),
                ("Check the range covered", "Support means the feature values and kinds of cases represented in the data. Comparing overlapping ranges avoids pretending that unseen cases were tested. Stable patterns can also occur without a direct causal link, so observations from a few sites do not uniquely identify a causal graph or cover an untested range."),
            ),
            "Equal averages can hide different errors. Even a stable within-group relationship is evidence under assumptions, not proof of a unique causal graph.",
            "Say which relationship stayed stable, which changes were tested and which new conditions remain untested.",
        ),
        CONCEPT_IDS[3]: (
            "Check predictions and reports separately",
            "Report fidelity means keeping recorded source facts without inventing details. It is not proof that the source is true. Prediction accuracy compares with separate reference labels. Coverage is the share receiving a full report; withholding a report leaves that case for review.",
            ("A fluent draft changes 'no opacity identified' to 'opacity present'. A second draft copies a mistaken source correctly. The first fails source fidelity; the second still needs an independent factual check."
             if medical else
             "A fluent draft changes 'no crack found' to 'crack present'. A second draft copies a mistaken source correctly. The first fails source fidelity; the second still needs an independent factual check."),
            (
                ("Define separate checks", "For prediction, define the label being predicted and compare predictions with appropriate independent reference labels. For generation, specify the source facts that must be retained, the additions that lack source support and important omissions. Clear wording is useful, but a style score does not check these factual requirements."),
                ("Count missing and issued reports", "Report the number of source-supported reports among all cases as well as among issued reports. Withholding difficult cases can improve the latter fraction while fewer people receive a full report. If no reports are issued, fidelity among issued reports is not defined, rather than automatically perfect."),
                ("Specify review and re-evaluation", "Abstention means withholding a prediction or report under a stated rule and referring it for review. Define the trigger and who reviews it. Check the intended setting, relevant groups and unfamiliar measurement ranges, then monitor errors and re-evaluate when conditions change. A withheld claim is not a verified answer, and none of these checks promises zero errors."),
            ),
            "A faithful copy can preserve a measurement error. A withheld report lowers coverage; it does not make an unsupported case correct.",
            "Check reference accuracy, source fidelity and the fraction receiving reports, with a clear review rule for gaps.",
        ),
    }
    for lesson in revised["lessons"]:
        title, definition, hook, steps, pitfall, takeaway = lessons[lesson["concept_id"]]
        lesson["title"] = title
        lesson["challenge_title"] = "Try another case"
        for field, text in (("definition", definition), ("hook", hook), ("pitfall", pitfall), ("takeaway", takeaway)):
            resources[lesson[field + "_resource_id"]]["text"] = text
        for step, (step_title, text) in zip(lesson["worked_steps"], steps, strict=True):
            step["title"] = step_title
            resources[step["resource_id"]]["text"] = text

    def question(activity_id, prompt, correct, alternatives, hint, accepted, rejected):
        activity = activities[activity_id]
        texts = {activity_id + ".supported": correct}
        texts.update({activity_id + f".alternative-{index}": text for index, text in enumerate(alternatives, 1)})
        if set(texts) != {choice["option_id"] for choice in activity["choices"]}:
            raise ValueError("shift wording must preserve every existing answer option")
        for choice in activity["choices"]:
            choice["text"] = texts[choice["option_id"]]
            resources[choice["consequence_resource_id"]]["text"] = accepted if choice["correct"] else rejected
            for hint_id in choice.get("hint_resource_ids", ()):
                resources[hint_id]["text"] = hint
        resources[activity["explanation_resource_id"]]["text"] = accepted
        grounded_question = prompt
        if activity.get("workbench"):
            activity["workbench"]["prompt"] = prompt
            table_texts = ["\n".join((table["label"], " | ".join(table["columns"]),
                *(" | ".join(row) for row in table["rows"]), table.get("note", "")))
                for table in activity["workbench"]["tables"]]
            grounded_question += "\n\nRecords available in this step:\n" + "\n\n".join(table_texts)
        resources[activity["question_resource_id"]]["text"] = grounded_question

    question(CONCEPT_IDS[0] + ".quiz",
        f"An assistant was tested only on records from one {site}. Another {site} uses different measurements and has a different mix of cases. How should the team test the assistant there?",
        "Test separate records from the intended new site, using appropriate checking labels.",
        ("Reuse a new random split from the old site as the deployment check.",
         "Match old records to the new case mix without checking the new measurements."),
        "Ask which records contain the conditions the assistant will actually face.",
        "Use records from the intended setting with checking labels suited to the task. Keep them separate from training and tuning so the test provides evidence about the proposed use.",
        "Which measurements and cases did that test include? Check whether it covers the new conditions.")
    question(CONCEPT_IDS[0] + ".challenge",
        ("After a scanner change, a report generator keeps the same writing-quality score. Nobody checks whether its findings still match the source images and notes. What is still needed?" if medical else
         "After a camera change, a description generator keeps the same writing-quality score. Nobody checks whether its descriptions still match the photographed items and records. What is still needed?"),
        "Check that the drafts retain source facts and agree with suitable reference facts in the new setting.",
        ("Use the stable writing score as evidence that the new drafts retain the source facts.",
         "Inspect generated facts only on old-site inputs, since the generator's software is unchanged."),
        "Writing quality and factual preservation are different properties of a report.",
        "A writing-quality score does not check whether drafts retain source facts or are independently correct. Check their content with the changed inputs in the intended setting.",
        "A fluent report can still omit or change a fact. Check what the proposed test actually measures.")
    question(CONCEPT_IDS[1] + ".quiz",
        f"An assistant uses a {marker} to predict a recorded outcome. In this exercise, editing only that marker leaves the underlying condition unchanged. What does a changed prediction show?",
        "The prediction depends on the marker; the underlying condition stayed fixed.",
        ("It shows the marker changed the condition because the predicted label changed.",
         "It shows removing the marker is enough to validate the other inputs."),
        "Separate the input, the predicted label and the underlying condition.",
        "Changing the recorded input changed the prediction while the underlying condition stayed fixed. This tests dependence on that input. It does not test a treatment for the condition or validate other predictions.",
        "Which part of the case did the edit change? Compare that with the condition being predicted.")
    question(CONCEPT_IDS[1] + ".challenge",
        ("Suppose a biological feature affects an outcome in a proposed causal model. A new laboratory measures that feature poorly. Does including it guarantee reliable predictions there?" if medical else
         "Suppose a material property affects parcel damage in a proposed causal model. A new camera measures that property poorly. Does including it guarantee reliable predictions there?"),
        "No. Both measurement quality and prediction performance in the new setting still need checking.",
        ("Yes. Its causal role lets the old rule handle the new measurement process.",
         "No. The feature must be experimentally changed before it can predict an outcome."),
        "The predictor receives a measured value, not direct access to the proposed cause.",
        "The causal explanation may give a reason to use the feature. Check its measurement, the range of cases and the process producing the outcome before relying on the predictions.",
        "Which value reaches the predictor: the feature itself or its recorded measurement?")
    question(CONCEPT_IDS[2] + ".quiz",
        f"Across three {site}s, cases with the same relevant measured features have similar outcome patterns over overlapping feature ranges. Which conclusion is justified?",
        "The relationship was stable over the tested ranges; causation and transfer remain unverified.",
        ("It establishes causation, so checking the relationship at another site is no longer necessary.",
         "It validates prediction for unfamiliar feature values outside the ranges present at all three sites."),
        "Which settings and feature ranges did the teams actually compare?",
        "The comparison supports stability over the tested ranges. It does not prove a cause, validate unfamiliar feature ranges or establish that a new outcome process is unchanged.",
        "Does the conclusion include settings or feature values that the teams did not test?")
    question(CONCEPT_IDS[2] + ".challenge",
        ("Two hospitals both report 85% overall accuracy. One makes more errors on high-risk patients at the second hospital, where group sizes differ. Does the equal average establish stability for similar patients?" if medical else
         "Two warehouses both report 85% overall accuracy. One makes more errors on fragile parcels at the second warehouse, where group sizes differ. Does the equal average establish stability for similar parcels?"),
        "No. A shared average can hide different errors within relevant groups.",
        ("Yes. Matching overall scores establish stability despite different errors within the relevant groups.",
         "Yes. Equal averages rule out an effect of different group sizes on the comparison."),
        "Ask whether the same average could hide different errors in the groups that matter.",
        "Overall accuracy mixes groups. Compare relevant within-group behaviour over comparable ranges, with enough data to judge uncertainty; a matching average alone does not do this.",
        "How do the reported errors differ within the groups? Consider that alongside the overall score.")
    question(CONCEPT_IDS[3] + ".quiz",
        f"The source says '{source_example}', but a draft says '{reversed_example}'. Its writing-quality score improves. Which check does the draft fail?",
        "It fails source fidelity: the draft contradicts the recorded source.",
        ("It passes source fidelity because the writing score checks the meaning.",
         "It is factually validated because polished wording replaces the source record."),
        "Compare the findings stated in the source and the draft.",
        "The draft reverses what the source says. Source fidelity checks whether the draft retains the source's meaning. Fluency and the correctness of the source itself need separate checks.",
        "Does the draft make the same factual claim as the source?")
    question(CONCEPT_IDS[3] + ".challenge",
        ("A scan uses an untested recording protocol, and its source does not contain a fact needed for the requested report. What should the assistant do?" if medical else
         "A photo uses an untested camera setup, and its source does not contain a fact needed for the requested report. What should the assistant do?"),
        "Flag the missing fact, withhold the claim and request review before extending use to these cases.",
        ("Add a plausible missing fact and treat the completed draft as evidence.",
         "Issue a full report using the old score without flagging this setup."),
        "Ask whether the required fact is actually available and whether this setup was evaluated.",
        "Flag the missing information and untested setting for review. Withholding a claim does not establish the missing fact. New evidence is needed before extending use to these cases.",
        "An old score and a confident draft cannot supply the missing source fact.")

    practice = (
        ("Change the reliability of a site clue",
         f"The site cue is a {marker}; the content measurement is a recorded {flag}. The model sets a reference label before adding measurement errors; no real images or reviews are used. Keep the cue prediction rule and other controls fixed. Predict at 90% cue agreement, choose Save my prediction, then Run experiment. Change only cue agreement to 50%; predict, choose Save my next prediction and run again. Compare reference accuracy and matching case IDs. After these two different configurations, reflect using Record my comparison, then answer below.",
         "What can you conclude from the two cue-agreement settings you tested?",
         "It measures the chosen rule only under the settings actually tested.",
         ("It validates reusing the first score after another, untested measurement change.",
          "It establishes accuracy at another site, including recording methods not tested here."),
         "Which settings did you run, and which possible changes remain untested?",
         "You tested the chosen predictor under the cue settings you ran. These runs do not check other changes to the measurements or the process producing the outcome.",
         "Does the statement include a setting that you did not run?"),
        ("Edit a clue without changing the reference",
         f"Use the initial cue prediction rule and source-preserving report rule. The {marker} is only a recorded input. Keep cue agreement and measurement error fixed. With the cue edit off, predict, choose Save my prediction and Run experiment. Turn on only Edit the cue; predict, choose Save my next prediction and run again. Compare matching case IDs: the model's reference label and source measurement stay fixed. After two different configurations, reflect with Record my comparison and answer below. This edit does not change the underlying target in the model.",
         "In matching cases, a cue edit changes a prediction but not the reference label. What has the edit tested?",
         "The prediction depends on the cue; the underlying outcome stayed fixed.",
         ("It tests whether changing the input marker improves the underlying target condition.",
          "It validates the content rule under a different, untested measurement process."),
         "Compare what the control changed with what the reference label describes.",
         "The cue edit changes an input while keeping the model's reference and measured content fixed. It tests which input the predictor uses, without changing the underlying outcome.",
         "Follow the reference label across the two runs. Did the edit change the condition it represents?"),
        ("Test a stable rule under another change",
         "The content rule reads a noisy target measurement, not a feature established to cause the target. Keep the initial prediction and report rules. Predict, choose Save my prediction and Run experiment. Change only cue agreement from 90% to 20%; predict, choose Save my next prediction and run again. Compare matching cases and reference-group errors. Grouping errors by reference label does not directly test the outcome relationship for fixed feature values. You may run a third setting with measurement error at 40%. Reflect with Record my comparison, then answer below; these tests do not prove a causal graph.",
         "A content-based rule stays stable under the tested cue changes. What can you conclude from these runs?",
         "They test the cue changes you ran; they do not establish causation or cover untested changes.",
         ("It validates transferring the old accuracy to every new measurement process.",
          "It identifies the feature's causal direction because the two scores agree."),
         "Name both the setting that changed and the process the comparison left fixed.",
         "A rule that ignores the cue can remain unchanged under cue-only edits. Its measured input can still be damaged by measurement changes. The displayed reference-group error rates are not a direct test of an outcome-given-features relationship or proof of causation.",
         "Which process stayed fixed in these runs? Check whether the conclusion also assumes it stays fixed elsewhere."),
        ("Compare complete and source-preserving reports",
         "Keep the content prediction rule, 30% measurement error and 60% required context availability fixed. With Complete every report, filling missing context, predict, choose Save my prediction and Run experiment. Change only the report rule to Preserve source facts; withhold if context is missing. Predict, choose Save my next prediction and run again. Compare source text, draft text, reference accuracy and full-report coverage: the fraction receiving reports. After two different configurations, reflect using Record my comparison, then answer below. The fixed report templates do not repair wrong measurements or missing context.",
         "Some drafts copy a source measurement that disagrees with the reference. Other cases lack required context. What can a source-preserving report rule establish?",
         "A faithful draft can retain a measurement error; it cannot supply missing context.",
         ("Source-preserving wording establishes that the noisy flag agrees with the reference.",
          "Completing the report with a plausible detail supplies the missing source fact."),
         "Compare predictions with reference labels and draft assertions with the source actually recorded.",
         "Reference accuracy checks predictions against the reference label; source fidelity checks drafts against the recorded source. Withholding incomplete reports can avoid unsupported additions while fewer cases receive reports. It does not establish the missing facts for withheld cases.",
         "The source and reference can disagree. A report rule cannot establish an absent fact or turn a mistaken source measurement into truth."),
    )
    for index, (title, instruction, *item) in enumerate(practice, 1):
        activity = activities[f"m1-shift-investigation.{index:02d}"]
        activity["experiment"]["title"] = title
        resources[activity["experiment"]["instructions_resource_id"]]["text"] = instruction
        activity["workbench"]["title"] = f"Practical exercise {index} of 4"
        activity["workbench"]["introduction"] = f"Use the controls to test a prediction rule and report rule for this {site} teaching case."
        question(activity["activity_id"], *item)

    final_context = (
        "A hospital team tests a readmission predictor and a discharge-summary drafter at a new hospital. Reference labels check the predicted event; source records check the draft's retained facts."
        if medical else
        "A town team tests a flood-alert predictor and an incident-bulletin drafter in a new town. Reference labels check the predicted event; source records check the bulletin's retained facts."
    )
    for index in range(1, 5):
        workbench = activities[f"m1-shift-final.{index:02d}"]["workbench"]
        workbench["title"] = f"Final check {index} of 4"
        workbench["introduction"] = final_context
    question("m1-shift-final.01",
        "At the new site, prediction accuracy falls from 91/100 to 72/100 and drafts preserving required source facts fall from 96/100 to 78/100. Measurements and the case mix both changed. What can we conclude from the table?",
        "Performance fell on both tasks in this external set; the table does not isolate why.",
        ("It identifies the recording method as the cause of the full performance drop.",
         "It validates continued new-site use because the original test was separate from training."),
        "Which results did the team measure, and which changes did the tests separate?",
        "Prediction accuracy and source fidelity were lower in the new test. Measurements and case mix both changed, so the table does not show how much each contributed to the drop.",
        "The tests changed more than one condition. Did they separate those changes enough to attribute the whole drop to one cause?")
    question("m1-shift-final.02",
        ("The team can use a hospital ID or a pre-discharge health feature proposed as a cause in its model. What can it conclude about prediction, changing the outcome and reliability at the new hospital?" if medical else
         "The team can use a town ID or a rainfall feature proposed as a cause in its model. What can it conclude about prediction, changing flood risk and reliability in the new town?"),
        "An ID can predict without causing the outcome; a proposed causal feature still needs measurement and transfer checks.",
        ("Use the more predictive ID as the better way to improve the underlying outcome.",
         "Use the causally motivated feature's old rule despite the changed measurement process."),
        "A useful predictor, an outcome-changing action and a reliable new-site rule are different claims.",
        "An ID can reflect where cases came from. A causal account may motivate a feature, but measurements, case ranges and the outcome process still limit transfer.",
        "What would changing the ID do to the outcome? What still needs checking when the predictor receives a measured causal feature?")
    question("m1-shift-final.03",
        "In two old settings, cases with similar measured features had similar outcome patterns over overlapping ranges. The new setting changes the process producing the outcome. Can the team rely on the old relationship without checking it again?",
        "No. A changed outcome process falls outside the earlier stability argument.",
        ("Yes. Overlapping feature ranges validate reuse even when the outcome-producing process changes.",
         "Yes. Stable groups at two old sites already cover this new outcome process."),
        "Which process did the earlier argument assume would stay the same?",
        "The relationship was stable under the old conditions. Changing the process that produces the outcome changes an assumption behind reuse, even if the feature ranges overlap.",
        "Which assumption changes when the process producing the outcome changes? Overlapping ranges do not test that new process.")
    question("m1-shift-final.04",
        "External drafts contain unsupported additions in 12/100 cases. A new record uses an untested measurement range and lacks a required source fact. How should the team evaluate the outputs and handle this record?",
        "Check reference accuracy and source fidelity separately; flag this case and withhold the claim pending review.",
        ("Measure writing quality and fill the missing detail, then use the draft as its reference.",
         "Test old-site cases and use the old average score to issue this unsupported report."),
        "What evidence is needed to check each output, and what should happen when a required fact is missing?",
        "Check prediction and generation separately, state when review is required and keep monitoring errors. The new range and missing source fact need evidence before the report is completed. These checks do not guarantee zero errors.",
        "Would this plan leave an unsupported claim in the report? Include a review step for cases and measurements that the previous tests did not cover.")
    return revised
