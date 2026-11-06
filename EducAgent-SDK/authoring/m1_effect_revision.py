"""Revise Effect course copy without changing its curriculum or experiment world."""


def apply_effect_revision(data: dict, profile_id: str) -> None:
    """Apply the shared editorial standards to a newly versioned Effect pack."""

    if profile_id not in {"general", "medical"}:
        raise ValueError("Effect revision requires general or medical")
    medical = profile_id == "medical"
    resources = {item["resource_id"]: item for item in data["resources"]}
    activities = {item["activity_id"]: item for item in data["activities"]}
    population = "eligible rehabilitation patients" if medical else "students eligible for study support"
    baseline = "mobility limitation" if medical else "learning difficulty"
    units = "mobility-score points" if medical else "skills-score points"
    outcome = "reach the mobility target" if medical else "pass the skills check"
    end_point = "attend the next appointment" if medical else "return an item on time"
    final_population = "eligible clinic patients" if medical else "eligible library users"

    lessons = {
        "defining-an-intervention": (
            "Specify the change and the comparison",
            f"For {population}, compare assignment to programme A with assignment to programme B. Success means {outcome} at six weeks; choosing a programme is not the same as being assigned one.",
            "An intervention actively sets a treatment. Selecting records of people who already received it leaves their original assignment process in place. Specify the treatment, alternative, target population, outcome and follow-up. Assignment and actual use can be different variables.",
            (
                ("Define the decision", f"For {population}, let A=1 mean assignment to the specified six-week programme and A=0 mean assignment to its stated comparison. Define success and the follow-up time. The notation do(A=1) means actively setting assignment to 1, not selecting existing records with A=1."),
                ("Distinguish choosing from assignment", f"People choosing a programme may differ in motivation, access or baseline {baseline}. Those factors can also affect success. Filtering existing programme users leaves that selection process in place."),
                ("Keep the effect specific", "Randomizing the offer can help estimate its effect under the study conditions. If some people do not take up the offer, the effect of actual use is a different question. A new programme version or population also needs separate evidence and assumptions."),
            ),
            "A historical or before-and-after comparison does not automatically reproduce random assignment; time and the people included may also differ.",
            "Name the assigned change, its alternative, the people and the outcome time.",
        ),
        "average-treatment-effect": (
            "Report the average difference and its units",
            f"Suppose the same target population would average 68 {units} under A and 62 under B. A minus B is a population-average contrast, not a promise about every person.",
            "An average treatment effect compares mean outcomes under two interventions for the same target population. Subtract the comparison from the treatment and state the units. For a binary (yes/no) outcome, a probability difference uses percentage points, not a relative percentage. Sampling uncertainty means another sample could give a different estimate.",
            (
                ("Use one population for both alternatives", "Define the mean outcome if the same target population were assigned A and if it were assigned B. This is different from comparing whichever people happened to choose each programme."),
                ("Keep the outcome's scale", f"For the score example, 68 - 62 = +6 {units}. For a binary outcome, 75% - 60% = +15 percentage points. The relative increase is 15/60 = 25%; these are different summaries."),
                ("Distinguish an average from an individual", "A positive average can include people who benefit by different amounts, people who do not benefit and people who are harmed. A study based on a finite sample estimates that population contrast with uncertainty. Subtracting the sample means does not remove the uncertainty."),
            ),
            "A percentage-point difference is not a relative percentage, and an average does not identify each person's response.",
            "Report A minus B, its units, the target population and the follow-up.",
        ),
        "confounding-and-adjustment": (
            "Use a common population for both treatments",
            f"Baseline {baseline} can influence both programme choice and later success. The overall A and B groups may therefore contain different starting conditions.",
            "Baseline means measured before treatment. Confounding occurs when a common cause affects treatment and outcome. Standardization compares rates within pre-treatment groups using the same target weights for both treatments; pooling keeps each selected group's own mixture. Causal interpretation requires no remaining confounding, overlap (both treatments possible) and consistency (well-defined treatment versions).",
            (
                ("Find the pre-treatment common cause", f"If baseline {baseline} affects choice and success, pooling all A records and all B records can mix programme differences with differences in who chose each programme. A stratum is a group with the same specified baseline category."),
                ("Apply the same weights", "In a separate worked example, A/B success rates are 80%/70% in the lower-baseline group and 50%/40% in the higher-baseline group. With a half-and-half target, A is 0.5 x 80% + 0.5 x 50% = 65%; B is 55%. The contrast is +10 percentage points."),
                ("Check the causal assumptions", "The pre-treatment variables must remove confounding; both treatments must occur in each relevant group; treatment versions must be consistent. Do not add every predictor. A mediator carries part of the treatment's effect; adjusting for it can remove that part. A collider is a common effect; conditioning on it can introduce bias."),
            ),
            "Weighting does not repair an omitted common cause or a group with no comparison treatment. A good outcome predictor is not automatically safe to adjust for.",
            "Justify the baseline groups and use one target mixture for both alternatives.",
        ),
        "identifiability-of-effects": (
            "Separate identification, estimation and a new use",
            "A large registry can describe a group difference precisely while leaving its cause unresolved. A trial result can also be specific to the people, programme and follow-up studied.",
            "Identification asks whether the data and stated causal assumptions determine an effect. Estimation calculates it from a finite sample, with uncertainty. Transport asks whether it applies to another population or treatment version. A precise estimate alone does not settle the other questions.",
            (
                ("Check what determines the effect", "An effect is identified relative to a set of data and assumptions if every causal model compatible with them gives the same effect. Different models fitting the observations can otherwise imply different intervention effects."),
                ("Separate assumptions from sample size", f"Adjustment by baseline {baseline} assumes no remaining confounding, both programmes possible in the relevant groups, and consistent versions. Random assignment can support an assignment-effect argument under its design and follow-up conditions. More records can reduce sampling error without repairing missing causal assumptions."),
                ("Check the proposed new use", "A different population, programme version or outcome time is a different target. Assess the evidence and assumptions for that target separately. Agreement between an adjusted estimate and a trial estimate does not prove every assumption, and missing follow-up can create another problem."),
            ),
            "A narrow uncertainty interval is not proof that confounding is absent or that the effect transfers to a different setting.",
            "State why the effect is identifiable, how uncertain its estimate is, and where it applies.",
        ),
    }
    for lesson in data["lessons"]:
        title, hook, definition, steps, pitfall, takeaway = lessons[lesson["concept_id"]]
        lesson["title"] = title
        lesson["challenge_title"] = "Apply the idea to another case"
        for field, text in (("hook", hook), ("definition", definition), ("pitfall", pitfall), ("takeaway", takeaway)):
            resources[lesson[field + "_resource_id"]]["text"] = text
        for target, (step_title, text) in zip(lesson["worked_steps"], steps, strict=True):
            target["title"] = step_title
            resources[target["resource_id"]]["text"] = text
        if lesson.get("scenario_image"):
            lesson["scenario_image"]["alt_text"] = (
                "A rehabilitation team reviewing programme records. Illustration only."
                if medical else "A student-support team reviewing programme records. Illustration only."
            )

    # For every activity: question, supported statement, two alternatives, hint,
    # explanation/accepted feedback, and a distinct rejection teaching cue.
    copy = {
        "defining-an-intervention.quiz": (
            "A clinic has records of patients who chose to turn on appointment reminders. Which plan would actively assign reminders?" if medical else "A library has records of readers who chose to turn on return-date reminders. Which plan would actively assign reminders?",
            "Randomly assign this reminder or no reminder, then measure the same next-month outcome.",
            "Compare people who already enabled reminders with people who did not, leaving their choices unchanged.",
            "Compare this month's reminder users with last year's users, leaving each year's assignment unchanged.",
            "Which plan decides how reminders are assigned, rather than sorting people by an earlier choice?",
            "Random assignment changes how the specified reminder is assigned. The other plans compare existing choices or different time periods; neither sets a new assignment rule.",
            "Sorting existing users or comparing years does not change their original assignment process. Which plan does?",
        ),
        "defining-an-intervention.challenge": (
            "A hospital offers transport support at random. Some patients who receive the offer do not use it. The study measures attendance over 30 days. Which effect is the randomized comparison designed to estimate?" if medical else "A college offers a travel voucher at random. Some students who receive the offer do not use it. The study measures attendance over 30 days. Which effect is the randomized comparison designed to estimate?",
            "It targets the effect of offering support versus no offer on attendance in this study population.",
            "It targets the effect of actual support use versus non-use, without additional assumptions.",
            "It targets a future transport service using the same offer, without checking population differences.",
            "Was the offer randomized, or was later use randomized?",
            "The study randomizes who receives the offer, not who takes it up. People decide whether to use the support, so comparing actual users can answer a different question. A future policy or population would also define a different target.",
            "The assigned offer, later use and a future policy are different targets. Which one did this study randomize?",
        ),
        "average-treatment-effect.quiz": (
            f"Eligible participants are randomly assigned A or B. Their mean scores at six weeks are 68 and 62 {units}, respectively. For this calculation, ignore sampling uncertainty. What is A minus B?",
            f"It is +6 {units} on average in the eligible study population.",
            f"It is exactly +6 {units} for each individual participant.",
            "It is a relative increase of 6%, regardless of the score's units.",
            "Calculate the difference between the two means. Does that number describe the group average or every participant?",
            f"68 - 62 = +6 {units}. This is the average six-week score difference for the eligible study population. It is neither a relative percentage nor an individual effect.",
            "Check the subtraction and keep the units as score points. A group average does not tell you each participant's response.",
        ),
        "average-treatment-effect.challenge": (
            "A randomized dataset records recovery by day 30: 54/100 people assigned A recover, compared with 40/100 assigned B. What is the risk difference (A minus B) for this study population?" if medical else "A randomized dataset records course completion by day 30: 54/100 people assigned A complete the course, compared with 40/100 assigned B. What is the risk difference (A minus B) for this study population?",
            "The estimated difference is +14 percentage points for this study's day-30 outcome.",
            "The estimated relative increase is 14%, because subtracting the two percentages gives 14.",
            "The comparison shows which 14 people succeeded because they received programme A.",
            "For a risk difference, subtract the probabilities. For a relative increase, divide that difference by the comparison probability.",
            "0.54 - 0.40 = 0.14, or 14 percentage points. Relative to B, the increase is 0.14/0.40 = 35%. These group outcomes do not identify individual responses. A finite study also has uncertainty.",
            "Check the quantity and what it describes. Keep the denominators fixed: a difference between group probabilities does not identify any one person's response.",
        ),
        "confounding-and-adjustment.quiz": (
            "Baseline severity affects both treatment choice and recovery. Assume that adjusting for severity removes all confounding, that both treatments occur at each severity, and that treatment versions are consistent. How should we calculate the target-population comparison?" if medical else "Baseline workload affects both programme choice and completion. Assume that adjusting for workload removes all confounding, that both programmes occur at each workload, and that programme versions are consistent. How should we calculate the target-population comparison?",
            "Compare outcomes within each baseline group, using the same target-population weights for both treatments.",
            "Average each treatment using its own selected-group weights, even when those mixtures differ.",
            "Add all recorded predictors, including post-treatment variables, without checking their causal role.",
            "Both treatment alternatives must describe the same target population, under the stated adjustment assumptions.",
            "Use each treatment's outcome rates within the pre-treatment groups and apply the same target weights to both. The causal interpretation requires adequate adjustment, overlap and consistency; calculating weights does not establish those assumptions.",
            "Each selected group's own weights represent its own mixture, not one common target. Adding predictors also requires a causal reason; having more variables does not establish the assumptions.",
        ),
        "confounding-and-adjustment.challenge": (
            "We want the total effect of operation type on recovery. Assume baseline risk already controls confounding. In the proposed model, operation type affects infection, which affects recovery. Should we also adjust for infection just because it predicts recovery?" if medical else "We want the total effect of coaching on passing. Assume baseline preparation already controls confounding. In the proposed model, coaching changes later study time, which affects passing. Should we also adjust for study time just because it predicts passing?",
            "No. Adjusting for it can remove the effect carried along that treatment-to-outcome pathway.",
            "Yes. Its predictive value is enough to justify including it in total-effect adjustment.",
            "No. All baseline adjustment should also be removed because observational data cannot support a causal comparison.",
            "A mediator carries an effect from treatment to outcome. Check whether the proposed variable lies on that route.",
            "In this model, the later variable is a mediator through which part of the treatment's effect passes. Adjusting for it can block that part. This does not invalidate the stated adequate baseline set or make observational inference impossible.",
            "A useful prediction does not by itself tell us what to adjust for. Check the effect being estimated and whether this variable carries part of it.",
        ),
        "identifiability-of-effects.quiz": (
            "A registry has a million records of treatment and recovery. A missing factor may cause both. No other design for identifying the causal effect is given. What can the large sample tell us?" if medical else "A platform has a million records of coaching and passing. A missing factor may cause both. No other design for identifying the causal effect is given. What can the large sample tell us?",
            "It can estimate the association more precisely while leaving the intervention effect unresolved.",
            "It removes the missing factor's confounding simply by increasing the number of records.",
            "It identifies the causal effect if the association has a very precise estimate.",
            "More records can improve precision without resolving which causal explanation is right.",
            "A large sample can reduce sampling error for the observed association. Without a design or assumptions that address the missing common cause, different intervention effects can still fit those records.",
            "Precision and identification are different. Ask what assumption or design addresses the missing common cause, rather than how many rows are available.",
        ),
        "identifiability-of-effects.challenge": (
            "A well-run randomized trial identifies the effect of assignment for eligible adults with complete follow-up. A team applies the result to children receiving a different dose and assessed later. What needs more evidence or assumptions?" if medical else "A well-run randomized trial identifies the effect of assignment for eligible adults with complete follow-up. A team applies the result to schoolchildren using a different programme length and assessed later. What needs more evidence or assumptions?",
            "The new population, treatment version and outcome time need their own evidence and assumptions.",
            "The original randomization already establishes the same effect for the changed people, treatment and time.",
            "Only more records are needed; the changed population and treatment cannot affect the causal argument.",
            "Compare the proposed use with the population, treatment and follow-up actually studied.",
            "The trial supports its specified assignment comparison under the study's design conditions. Applying it to different people, treatment versions or follow-up times needs a separate argument and often more evidence.",
            "A randomized result does not automatically cover a different target. Compare the new population, treatment and follow-up with those in the study.",
        ),
        "m1-effect-investigation.01": (
            "You compared the pooled result with the common-target result. Why can the A-minus-B contrast change?",
            "Pooled averages use each group's own baseline mix; standardization uses the same target-population weights for both programmes.",
            "The pooled difference identifies the intervention effect without considering how people selected programmes.",
            "Common-target weighting removes an unmeasured common cause even when the adjustment assumptions fail.",
            "Compare how much each baseline group contributes to each programme's average in both calculations.",
            "Each pooled average uses its programme group's own baseline mixture. Standardization applies the same target weights to both programmes. A causal interpretation still requires adequate pre-treatment adjustment, overlap and consistency. Read the numerical results from your saved runs.",
            "Pooled rates can combine programme outcome differences with differences in who chose each programme. Weighting still relies on the causal assumptions; the calculation does not check whether they hold.",
        ),
        "m1-effect-investigation.02": (
            "After changing only how programmes are assigned, how is this different from sorting the existing records into A and B?",
            "It changes how programmes are allocated while keeping the model's baseline and outcome mechanisms fixed.",
            "It compares only existing A records with existing B records, without changing programme assignment.",
            "It moves people between the lower and higher baseline categories when their programme changes.",
            "Did you change how people enter each programme, or only select records with a particular programme value?",
            "The control changes the assignment rule in this teaching model. A filter only selects rows that already exist. A model run does not establish an individual benefit or show how a real programme would be implemented.",
            "Check which process the control changes. Labels, baseline conditions and individual outcomes are not automatically changed by replacing assignment.",
        ),
        "m1-effect-investigation.03": (
            "You changed the target mixture while keeping the outcome rates fixed. What does the average A-minus-B difference describe?",
            "It compares average outcomes under A and B for this target population; it does not give each person's benefit.",
            "It gives the same fixed benefit for every individual, regardless of the target mixture.",
            "It is a relative percentage that does not depend on outcome units or a target population.",
            "Report the probability difference in percentage points, using the same target weights for A and B.",
            "The target average applies the same population mixture to both programme alternatives. Changing that mixture can change the average even though within-group rates and source records stay fixed. The probability difference is measured in percentage points; it does not give each person's effect.",
            "An average describes a particular population on a particular outcome scale. It is not a relative percentage or the effect for every person.",
        ),
        "m1-effect-investigation.04": (
            "You compared two assignment rules using the same target mixture. What would justify interpreting the adjusted contrast causally?",
            "The interpretation relies on the declared adjustment assumptions, overlap, consistency and stable within-group rates; matching results alone are not enough.",
            "Agreement between adjusted runs verifies that the model's causal assumptions also hold in a real registry.",
            "The precision of a model result verifies the real-world assumptions needed for the adjusted target contrast.",
            "Which assumptions are built into the teaching model, and what evidence would support them in an external study?",
            "The teaching model specifies its causal and design assumptions. Matching adjusted results do not verify those assumptions in another study. Check uncertainty from finite data and whether the result applies to a new population or programme version.",
            "Two calculations can agree even when the assumptions have not been checked in a real study. Separate what the model assumes from what these runs tested.",
        ),
        "m1-effect-final.01": (
            f"A study assigns the specified reminder or no reminder to {final_population}. It measures whether people {end_point} within 30 days. Which effect matches that design?",
            "It targets reminder assignment versus no reminder in the eligible population at 30 days.",
            "It is the effect of choosing to read the reminder, even though reading was not randomized.",
            "It is the effect of any reminder technology in other populations and time periods.",
            "Which variable was assigned, and which outcome did the study follow?",
            "The study randomizes assignment to the specified reminder in the eligible population. Reading a reminder happens later. Different reminder versions, populations or follow-up times define other effects.",
            "Match the assigned variable, eligible population and 30-day outcome. Later use or a broader service would answer a different question.",
        ),
        "m1-effect-final.02": (
            "Among people assigned a reminder, 82/100 reach the outcome; among those assigned no reminder, 74/100 do. Ignore sampling uncertainty for this arithmetic. How should we report A minus B?",
            "The estimate is +8 percentage points for reminder assignment in this study population.",
            "The estimate is an 8% relative increase for reminder assignment in the same study population.",
            "The estimate is an eight-percentage-point improvement for each participant who was assigned the reminder.",
            "Subtract the proportions. Then distinguish percentage points from a relative percentage and from an individual effect.",
            "82% - 74% = +8 percentage points. The relative increase is 8/74, about 10.8%. Both are summaries for this study population and have sampling uncertainty. Neither identifies every individual's response.",
            "Check which quantity the answer reports. Keep the denominators and units clear, and do not treat a study-population average as the benefit for each participant.",
        ),
        "m1-effect-final.03": (
            "A separate observational registry records reminder choice and attendance. Baseline travel difficulty causes both. Assume adequate adjustment, overlap and consistent versions. Which comparison represents one eligible population?" if medical else "A separate observational registry records reminder choice and on-time returns. Baseline travel difficulty causes both. Assume adequate adjustment, overlap and consistent versions. Which comparison represents one eligible population?",
            "Use the eligible population's travel-difficulty weights for both reminder groups under those assumptions.",
            "Use each selected reminder group's own travel-difficulty weights, even if their mixtures differ.",
            "Adjust for later reminder reading as if compliance were a pre-treatment common cause.",
            "The two alternatives should represent the same people before reminder assignment.",
            "This separate registry assumes adequate baseline adjustment, overlap and consistency. Applying the eligible population's same weights to both reminder groups removes differences in their measured baseline composition. The separate randomized study does not supply the registry's adjustment weights.",
            "The two reminder groups need the same target weights, rather than their different selected-group mixtures. Adjusting for a variable measured after treatment also needs a causal justification.",
        ),
        "m1-effect-final.04": (
            "A manager applies the estimated eight-percentage-point reminder effect to a new population. The reminder has changed and follow-up is incomplete. What should be checked?",
            "Assess uncertainty, missing outcomes and transfer to the changed population and reminder separately.",
            "The original eight-percentage-point estimate identifies the true effect for the changed service population.",
            "The original randomization resolves missing outcomes and changed reminder versions in the new service.",
            "Separate identification in the original study, estimation uncertainty and the evidence needed for the proposed new use.",
            "Identification depends on the original study's causal and design assumptions. The estimate also has finite-sample uncertainty. A new population, reminder version or follow-up process needs its own assessment; it cannot simply inherit the original result.",
            "Check the new population, reminder version and missing-outcome process on their own. The original study's design does not automatically apply to a changed service.",
        ),
    }
    for activity_id, (question, supported, alternative_one, alternative_two, hint, explanation, rejected) in copy.items():
        activity = activities[activity_id]
        prefix = activity["question_resource_id"].removesuffix(".question")
        old_question = resources[activity["question_resource_id"]]["text"]
        table_suffix = old_question.partition("\n\nRecords available in this step:")[2]
        resources[activity["question_resource_id"]]["text"] = question + (
            "\n\nRecords available in this step:" + table_suffix if table_suffix else ""
        )
        for suffix, text in (("hint", hint), ("explanation", explanation), ("accepted", explanation), ("rejected", rejected)):
            resources[prefix + "." + suffix]["text"] = text
        labels = {"supported": supported, "alternative-1": alternative_one, "alternative-2": alternative_two}
        for choice in activity["choices"]:
            choice["text"] = labels[choice["option_id"].removeprefix(activity_id + ".")]
        if activity.get("workbench"):
            activity["workbench"]["prompt"] = question

    instructions = (
        ("Compare two ways to average", "Keep people choosing their programme and a target with 50% higher-baseline cases. Run Source pooled comparison, then change only the chart's analysis to Same target weights for A and B and run again. Compare saved contrasts and baseline mixtures; explain what changed and whether it matched your prediction."),
        ("Change programme assignment", "Keep the target at 50% higher-baseline cases and use Source pooled comparison. Run Balanced random assignment, then change only assignment to People choose their programme and run again. Compare the A/B baseline mixtures and outcome contrasts; explain what assignment changed and what stayed fixed."),
        ("Change who the target represents", "Keep randomized assignment and Same target weights for A and B. Run with 20% higher-baseline cases in the target, then change only that percentage to 80% and run again. Compare target rates and their difference in percentage points; check that source counts did not change."),
        ("Compare computations and assumptions", "Keep Same target weights for A and B and a target with 80% higher-baseline cases. Run People choose their programme, then change only assignment to Balanced random assignment and run again. Compare adjusted contrasts; distinguish the model's assumptions from what a real study would need to justify."),
    )
    for index, (title, instruction) in enumerate(instructions, start=1):
        activity = activities[f"m1-effect-investigation.{index:02d}"]
        activity["experiment"]["title"] = title
        resources[activity["experiment"]["instructions_resource_id"]]["text"] = (
            instruction + " Before each run, use Save my prediction (or Save my next prediction), then Run experiment. Explain your comparison and use Record my comparison."
        )
        activity["workbench"]["title"] = f"Programme practice {index} of 4"
        activity["workbench"]["introduction"] = (
            f"Compare programmes A and B for {population}; success means {outcome} at six weeks. Change settings, predict, run two different setups and record a comparison. Reference records below are an earlier example, not the current run."
        )
        for record_table in activity["workbench"]["tables"]:
            record_table["note"] = (
                "Earlier self-selected records; baseline is measured before programme choice. These are not current experiment runs. Each run uses the target percentage shown in its controls."
            )
    # Keep the table facts in released question resources aligned with their view.
    for activity in data["activities"]:
        if activity.get("workbench"):
            workbench = activity["workbench"]
            records = []
            for record_table in workbench["tables"]:
                records.append("\n".join((record_table["label"], " | ".join(record_table["columns"]),
                    *(" | ".join(row) for row in record_table["rows"]), record_table.get("note", ""))))
            resources[activity["question_resource_id"]]["text"] = (
                workbench["prompt"] + "\n\nRecords available in this step:\n" + "\n\n".join(records)
            )
            if workbench["stage"] == "capstone":
                workbench["title"] = "Course final check"
                workbench["introduction"] = (
                    f"For {final_population}, assignment is this reminder versus none. The outcome is whether people {end_point} within 30 days. The table summarizes the completed randomized study; question 3 describes a separate observational registry."
                )
                if activity["activity_id"] == "m1-effect-final.03":
                    workbench["introduction"] = (
                        f"This question concerns a separate observational reminder registry for {final_population}, not the randomized trial. Its supplied assumptions are listed below; no registry outcome counts are supplied."
                    )
                    workbench["tables"] = [{
                        "table_id": "registry-assumptions", "label": "Registry assumptions for this question",
                        "columns": ["Item", "Given information"],
                        "rows": [
                            ["Dataset", "Separate observational reminder registry"],
                            ["Baseline variable", "Travel difficulty before reminder choice"],
                            ["Adjustment", "Assume travel difficulty removes confounding"],
                            ["Overlap", "Both reminder choices occur in each relevant baseline group"],
                            ["Consistency", "Assume consistent reminder versions and outcome definitions"],
                        ],
                        "note": "These are assumptions given for this question, not conclusions proved by the earlier randomized trial.",
                    }]
                    registry_table = workbench["tables"][0]
                    resources[activity["question_resource_id"]]["text"] = (
                        workbench["prompt"] + "\n\nRecords available in this step:\n" + "\n".join((
                            registry_table["label"], " | ".join(registry_table["columns"]),
                            *(" | ".join(row) for row in registry_table["rows"]), registry_table["note"],
                        ))
                    )
