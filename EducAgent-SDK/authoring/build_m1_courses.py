"""Build the four authored M1 context packs; no model or network is involved.

Run from EducAgent-SDK with ``python authoring/build_m1_courses.py``; add
``--check`` to verify freshness without writing files. The old
0.1.0 seeds and 1.1.0 course outputs remain intact for historical traces. These
Effect and Shift 1.4.0 revisions give each topic a complementary Challenge and
teach its required distinctions in the visible explanation. Historical course
files stay unchanged.
Reference tables are authored teaching data; experiment outcomes are recomputed
from the released model and learner settings. ECI supplies the conceptual
references, not these original scenarios or empirical study results.
"""

import argparse
import json
from pathlib import Path

if __package__:
    from .m1_effect_revision import apply_effect_revision
    from .m1_effect_scaffold_revision import apply_effect_scaffold_revision
    from .m1_effect_challenge_revision import apply_effect_challenge_revision
    from .m1_shift_revision import apply_shift_revision
    from .m1_shift_scaffold_revision import apply_shift_scaffold_revision
    from .m1_shift_challenge_revision import apply_shift_challenge_revision
else:
    from m1_effect_revision import apply_effect_revision
    from m1_effect_scaffold_revision import apply_effect_scaffold_revision
    from m1_effect_challenge_revision import apply_effect_challenge_revision
    from m1_shift_revision import apply_shift_revision
    from m1_shift_scaffold_revision import apply_shift_scaffold_revision
    from m1_shift_challenge_revision import apply_shift_challenge_revision


ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.2.0"
VERSIONS = {"effect": "1.4.0", "shift": "1.4.0"}
SOURCE_ID = "peters-janzing-scholkopf-2017"
SOURCE = {
    "source_id": SOURCE_ID,
    "citation": "Peters, Jonas; Janzing, Dominik; Schölkopf, Bernhard. Elements of Causal Inference: Foundations and Learning Algorithms. MIT Press, 2017.",
    "rights": "Reference source: CC BY-NC-ND 4.0 (https://creativecommons.org/licenses/by-nc-nd/4.0/). This pack contains independently authored explanations and invented teaching data, not textbook excerpts or figures. Source metadata checked locally; subject-matter expert approval is separate.",
    "review_status": "reviewed",
}

EFFECT_CONCEPTS = (
    ("defining-an-intervention", "Specify a treatment, comparison, population and outcome, and distinguish setting a treatment from observing its value."),
    ("average-treatment-effect", "Calculate a population-average contrast between two intervention values, stating direction, units and target population without assigning it to each individual."),
    ("confounding-and-adjustment", "Explain confounding and standardize stratum-specific outcomes to a common population only under an adequate pre-treatment adjustment set, overlap and consistency."),
    ("identifiability-of-effects", "Distinguish effect identification under explicit causal and design assumptions from estimation with finite data and from generalization to another population."),
)
SHIFT_CONCEPTS = (
    ("distribution-shift", "Identify changes in the population, measurement or target-generating process and distinguish within-environment performance from evidence about deployment."),
    ("causal-vs-spurious-features", "Distinguish prediction from intervention targets and explain why neither predictive strength nor a causal label alone guarantees robustness."),
    ("invariance-across-environments", "Compare conditional relationships across environments and state the mechanism and support assumptions needed for a scoped invariance argument, without treating stability as causal proof."),
    ("when-predictions-can-still-fail", "Design external-environment checks for prediction and generation, including content preservation, failure monitoring and abstention when evidence does not cover the intended use."),
)

EFFECT_CLAIMS = (
    ("intervention", "An intervention replaces the assignment mechanism of the selected variable; observing a value generally leaves its causes and selection process in place.", "Sections 3.2 and 6.3, intervention definitions and Example 6.10"),
    ("average", "An average causal effect contrasts expected outcomes under two specified interventions in a specified population; for a binary outcome a risk difference is expressed in probability or percentage points.", "Section 6.6, Example 6.37, equations (6.11)-(6.12)"),
    ("adjustment", "A valid adjustment formula combines conditional outcome distributions with the same pre-intervention covariate distribution for each treatment. Validity depends on the causal structure, not merely on including many variables.", "Section 6.6, Definition 6.38, equations (6.13)-(6.15), and the warning following Definition 6.39"),
    ("identification", "An intervention distribution may be determined by observational data together with a causal model and valid adjustment assumptions; an observational association alone need not determine it.", "Section 6.6, truncated factorization (6.8)-(6.9), Example 6.37 and Definition 6.38; Sections 9.1-9.2, interventional sufficiency and Simpson's paradox"),
)
SHIFT_CLAIMS = (
    ("shift", "A relationship useful for prediction in observed environments need not apply in a new environment whose generating processes or support differ.", "Section 8.3, Domain Adaptation, environments and equation (8.7)"),
    ("prediction", "The most informative observational predictor need not be an effective intervention target, because prediction and changing the target are different tasks.", "Section 6.3, Example 6.10, Predictors and intervention targets"),
    ("invariance", "Under a causal model, changes to other mechanisms can leave the target mechanism invariant. Domain generalization additionally assumes that the relevant conditional relationship persists in the test environment and has adequate support; stability can also occur for non-parent predictor sets.", "Section 6.6, equation (6.7); Section 8.3, equation (8.7), discussion of non-parent sets and overlapping supports"),
    ("limits", "Evidence from multiple environments is interpreted under assumptions about which mechanisms change. Hidden variables and previously unexamined mechanism changes can invalidate an invariance argument.", "Section 8.3, equation (8.7) assumptions; Section 9.5.6, restrictions on hidden variables and environment interventions"),
)


class Course:
    """Small JSON authoring helper over the existing ContentPack contract."""

    def __init__(self, task, profile, title, concepts, claims, image_alt):
        self.task = task
        self.profile = profile
        self.concepts = concepts
        self.image = {"path": f"media/m1-courses/{task}-{profile}.png", "alt_text": image_alt}
        self.data = {
            "schema_version": "3.0", "pack_id": f"causality.m1.{task}.{profile}",
            "version": VERSION, "title": title, "concepts": [], "sources": [SOURCE],
            "claims": [{"claim_id": f"m1.{task}.{key}", "proposition": proposition,
                        "source_refs": [{"source_id": SOURCE_ID, "locator": locator}],
                        "release_status": "released"} for key, proposition, locator in claims],
            "resources": [], "activities": [], "lessons": [],
        }
        self.data["claims"].append({
            "claim_id": f"m1.{task}.authored-case",
            "proposition": "Reference counts and assessment cases in this pack are authored teaching data. Interactive experiment outcomes are deterministically recomputed from the released model and learner settings. Ratios, differences and weighted sums use declared denominators and target weights. Generation fidelity and withholding criteria are declared teaching-model rules, not empirical guarantees or textbook claims about a particular generator.",
            "deterministic_derivation": {"method_id": "m1.authored-case", "method_version": "1.1.0"},
            "release_status": "released",
        })

    def resource(self, resource_id, kind, text, claim):
        self.data["resources"].append({
            "resource_id": resource_id, "kind": kind, "text": text,
            "claim_ids": [f"m1.{self.task}.{claim}", f"m1.{self.task}.authored-case"],
            "release_status": "released",
        })
        return resource_id

    def question(self, concept, suffix, text, correct, wrong, hint, explanation, claim, *, tables=(), introduction=None, scenario=None, stage=None, experiment=None):
        if stage:
            ordinal = sum(1 for activity in self.data["activities"]
                          if activity.get("workbench", {}).get("stage") == stage) + 1
            activity_id = f"m1-{self.task}-{suffix}.{ordinal:02}"
        else:
            activity_id = concept + "." + suffix
        prefix = f"m1.{self.task}.{activity_id}"
        prompt = text
        if stage:
            # The prompt is the compact view. Its released resource also owns
            # every currently visible table fact for deterministic grounding.
            rendered_tables = ["\n".join((item["label"], " | ".join(item["columns"]),
                               *(" | ".join(row) for row in item["rows"]), item.get("note", "")))
                               for item in tables]
            text += "\n\nRecords available in this step:\n" + "\n\n".join(rendered_tables)
        res = lambda key, kind, value: self.resource(prefix + "." + key, kind, value, claim)
        good_id = res("accepted", "consequence", explanation)
        bad_id = res("rejected", "consequence", "Reconsider the distinction in this case. " + explanation)
        hint_id = res("hint", "hint", hint)
        choices = [{"option_id": activity_id + ".supported", "text": correct, "correct": True,
                    "consequence_resource_id": good_id}]
        choices.extend({"option_id": activity_id + f".alternative-{index}", "text": value,
                        "correct": False, "misconception_id": f"m1.{self.task}.{claim}.confusion",
                        "hint_resource_ids": [hint_id], "consequence_resource_id": bad_id}
                       for index, value in enumerate(wrong, 1))
        # Fixed authored positions keep the exercise independent of a first-option habit.
        position = len(self.data["activities"]) % len(choices)
        choices = choices[1:position + 1] + choices[:1] + choices[position + 1:]
        activity = {
            "activity_id": activity_id, "concept_id": concept,
            "activity_type": "classification", "question_resource_id": res("question", "question", text),
            "choices": choices, "explanation_resource_id": res("explanation", "explanation", explanation),
            "is_transfer": suffix in ("challenge", "final"),
        }
        if stage:
            activity["workbench"] = {
                "title": ("Practical investigation" if stage == "investigate" else "Final module quiz"),
                "introduction": introduction, "scenario_id": scenario, "stage": stage,
                "tables": list(tables), "prompt": prompt,
            }
        if experiment:
            activity["experiment"] = {
                "experiment_id": activity_id + ".experiment",
                "title": experiment["title"],
                "instructions_resource_id": res("experiment-instructions", "explanation", experiment["instructions"]),
                "model_version": "1.0.0", "model": experiment["model"],
                "initial_config": experiment["initial_config"], "min_distinct_runs": 2,
            }
        self.data["activities"].append(activity)
        return activity_id

    def lesson(self, concept, title, hook, steps, definition, pitfall, takeaway, claim):
        prefix = f"m1.{self.task}.{concept}.lecture"
        res = lambda key, kind, text: self.resource(prefix + "." + key, kind, text, claim)
        self.data["lessons"].append({
            "profile_id": self.profile, "concept_id": concept, "title": title,
            "hook_resource_id": res("hook", "question", hook),
            "example_label_resource_id": res("example-label", "explanation", "Worked example"),
            "worked_steps": [{"title": title.removeprefix(f"{index}. "), "resource_id": res(f"step-{index}", "explanation", text)}
                             for index, (title, text) in enumerate(steps, 1)],
            "definition_resource_id": res("definition", "explanation", definition),
            "pitfall_resource_id": res("pitfall", "explanation", pitfall),
            "takeaway_resource_id": res("takeaway", "explanation", takeaway),
            "practice_activity_id": concept + ".quiz", "challenge_activity_id": concept + ".challenge",
            "challenge_title": "Apply the idea in a new case", "scenario_image": self.image,
        })

    def finish(self):
        for concept_id, objective in self.concepts:
            self.data["concepts"].append({
                "concept_id": concept_id, "objective": objective,
                "completion_activity_ids": [a["activity_id"] for a in self.data["activities"] if a["concept_id"] == concept_id],
            })
        return self.data


def table(table_id, label, columns, rows, note=None):
    result = {"table_id": table_id, "label": label, "columns": columns, "rows": rows}
    if note:
        result["note"] = note
    return result


def effect_course(profile):
    medical = profile == "medical"
    course = Course("effect", profile, "Effect of an intervention", EFFECT_CONCEPTS, EFFECT_CLAIMS,
                    "A rehabilitation team compares programme assignments and follow-up records; no numbers or causal conclusions are shown." if medical else
                    "A student-support team compares programme assignments and follow-up records; no numbers or causal conclusions are shown.")
    intervention, average, confounding, identification = [c[0] for c in EFFECT_CONCEPTS]
    population = "adults eligible for a six-week rehabilitation programme" if medical else "students eligible for a six-week study-support programme"
    treatment = "the supervised rehabilitation programme" if medical else "the scheduled study-support programme"
    outcome = "reaching the declared mobility target at six weeks" if medical else "passing the declared skills check at six weeks"
    baseline = "baseline mobility limitation" if medical else "baseline learning difficulty"
    low, high = ("Lower limitation", "Higher limitation") if medical else ("Lower difficulty", "Higher difficulty")
    course.lesson(intervention, "Define the change before comparing outcomes",
        "People who choose a programme may differ before it begins. What exactly would change if the same eligible population were assigned the programme instead?",
        [("1. Name the decision", f"Consider {population}. Define A=1 as assignment to {treatment} and A=0 as assignment to the stated comparison programme. Define the outcome as {outcome}. Fix the eligibility rule, follow-up time and programme version, so 'the effect' refers to one clear decision."),
         ("2. Separate selection from assignment", f"Looking only at people who selected A=1 keeps their original selection process. Motivation, access and {baseline} may explain both selection and the later outcome. An intervention instead specifies a rule for setting A; it does not merely filter existing rows."),
         ("3. Keep the contrast specific", "A trial could randomize programme assignment while measuring the same endpoint in both arms. This directly addresses assignment to the specified programmes under the trial conditions. It does not automatically identify the effect of attendance when people do not follow assignment, nor effects of an unspecified future programme.")],
        "An intervention changes how a treatment variable is set. do(A=1) denotes setting A to 1 in the model; observing A=1 denotes selecting cases whose existing value is 1. The two distributions can differ.",
        "A before/after comparison or a group of enthusiastic volunteers is not automatically equivalent to random assignment. The source of treatment differences matters.",
        "Write the treatment, comparison, eligible population, endpoint and timing before asking which records can answer the question.", "intervention")
    course.question(intervention, "quiz",
        ("A clinic wants the effect of assigning an appointment reminder on attendance next month. It currently has records of patients who switched reminders on themselves. Which additional plan directly changes assignment?" if medical else
         "A library wants the effect of assigning a return-date reminder on on-time returns next month. It currently has records of readers who switched reminders on themselves. Which additional plan directly changes assignment?"),
        "Randomly assign the specified reminder or no reminder among eligible users, then measure the same follow-up outcome.",
        ["Select only users who already enabled the reminder and rename this do(reminder=1).", "Compare this month's users with last year's users and assume the year cannot matter."],
        "Ask whether the plan changes the assignment rule or only selects existing records.",
        "Random assignment sets the reminder under a declared rule. Filtering existing reminder users retains self-selection; a historical comparison also changes time and potentially the population.", "intervention")
    course.question(intervention, "challenge",
        ("A hospital randomly offers transport support, but some offered patients do not use it. The endpoint is attendance within 30 days. Which intervention contrast does comparing the randomized groups directly target?" if medical else
         "A college randomly offers a travel voucher, but some offered students do not use it. The endpoint is attendance within 30 days. Which intervention contrast does comparing the randomized groups directly target?"),
        "The effect of being offered the specified support versus not being offered it in the eligible study population.",
        ["The effect of actually using support, with no further assumptions about non-use.", "The effect of every transport policy in every future population."],
        "The randomized variable is the offer, not later uptake.",
        "The assignment intervention is the offer. An effect of actual use is a different target because uptake can be selective; transporting any result to a new policy or population needs further support.", "intervention")

    units = "mobility-score points" if medical else "skills-score points"
    course.lesson(average, "Make the average contrast explicit",
        f"Suppose the target population's mean outcome would be 68 {units} under programme A and 62 under programme B. What does the difference describe?",
        [("1. Use the same population twice", "The contrast describes two alternative assignments for the same target population, not the difference between whichever people happened to choose A and whichever chose B. The two expected outcomes are defined before choosing an estimator."),
         ("2. Keep the outcome scale", f"For the continuous score, A minus B is 68 - 62 = +6 {units}. If the outcome were whether a target was reached, a change from 60% to 75% would be +15 percentage points. That differs from a relative increase of 25%. State which quantity you report."),
         ("3. Read the average carefully", "A positive average contrast need not mean that every person benefits. Some may benefit more, some less and some may be harmed. A finite study estimates the population contrast with uncertainty; the arithmetic alone is not an uncertainty analysis.")],
        "The average treatment effect is E[Y under do(A=1)] - E[Y under do(A=0)] for a stated population and outcome. Direction, units, timing and assignment versions are part of its meaning.",
        "Do not turn a percentage-point difference into a relative percentage or an individual guarantee. Changing the population mixture can also change an average effect.",
        "Report the two expected outcomes, their difference and its units, then name the target population.", "average")
    course.question(average, "quiz",
        ("In a randomized teaching dataset of eligible rehabilitation patients, the mean six-week mobility score is 68 under A and 62 under B. Ignoring sampling uncertainty for this arithmetic question, what is the A-minus-B contrast?" if medical else
         "In a randomized teaching dataset of eligible learners, the mean six-week skills score is 68 under A and 62 under B. Ignoring sampling uncertainty for this arithmetic question, what is the A-minus-B contrast?"),
        f"+6 {units} on average for the eligible study population.",
        [f"Every participant gains exactly 6 {units}.", "A relative increase of 6%, regardless of the outcome units."],
        "Subtract B from A and keep the outcome's original units.",
        f"68 - 62 = +6 {units}. This is a group-average estimate in the declared study, not each person's effect or a 6% relative change.", "average")
    course.question(average, "challenge",
        ("A randomized follow-up dataset reports recovery in 54 of 100 assigned A and 40 of 100 assigned B by day 30. Which statement reports the risk difference correctly?" if medical else
         "A randomized follow-up dataset reports course completion in 54 of 100 assigned A and 40 of 100 assigned B by day 30. Which statement reports the risk difference correctly?"),
        "A minus B is +14 percentage points for this study population and endpoint; individual effects are not determined.",
        ["A raises the outcome by 14% relative to B, because 54 minus 40 is 14.", "Exactly 14 specified individuals were caused to succeed, and we know which ones."],
        "Compute the difference between probabilities; a relative change divides that difference by the comparison risk.",
        "0.54 - 0.40 = 0.14, or 14 percentage points. The relative increase is 0.14/0.40 = 35%; the data do not identify the response of each individual.", "average")

    course.lesson(confounding, "Compare like strata, then restore the population",
        f"What if people with higher {baseline} more often choose the intensive programme and also have lower success regardless of programme?",
        [("1. Locate the shared cause", f"If {baseline} affects programme choice and the outcome, the raw A and B groups mix different starting conditions. Comparing their overall success rates can combine the programme contrast with this compositional difference."),
         ("2. Use one set of weights", f"Imagine success rates of 80% versus 70% in the {low.lower()} stratum and 50% versus 40% in the {high.lower()} stratum. In a target population that is half in each stratum, standardize A to 0.5×80% + 0.5×50% = 65%, and B to 0.5×70% + 0.5×40% = 55%. Both use the target mixture, giving +10 percentage points."),
         ("3. Check whether adjustment is justified", "The calculation has a causal interpretation only if the selected pre-treatment strata suffice to control confounding, both treatments are possible in each relevant stratum, and the treatment/outcome definitions are consistent. Adding every measured variable is unsafe: a mediator changes the target and conditioning on a collider can introduce bias.")],
        "Covariate adjustment estimates each treatment's outcome within valid pre-treatment strata and averages using the same target-population distribution. A valid adjustment set is a causal assumption, not a property guaranteed by a spreadsheet.",
        "Different weights for A and B reproduce selection rather than remove it. A weighted calculation cannot fix a missing common cause or a stratum with no comparison cases.",
        "Name why the adjustment set is valid, check overlap, then apply one declared target mixture to both treatment-specific rates.", "adjustment")
    course.question(confounding, "quiz",
        ("Baseline symptom severity affects both treatment choice and recovery. Under the stated model it is the only common cause, both treatments occur at each severity and versions are consistent. How should a target-population effect be calculated?" if medical else
         "Baseline workload affects both support-programme choice and task completion. Under the stated model it is the only common cause, both programmes occur at each workload and versions are consistent. How should a target-population effect be calculated?"),
        "Compare treatment-specific outcomes within baseline strata and average each treatment using the same target-stratum weights.",
        ["Average each treatment with its own observed group mixture and call the difference adjusted.", "Adjust for every recorded variable, including outcomes measured after treatment, regardless of the causal model."],
        "The two hypothetical assignments must refer to the same target population.",
        "With an adequate pre-treatment adjustment set and overlap, one common target mixture separates treatment-specific rates from differences in who selected each treatment. These assumptions, not the number of columns, license the calculation.", "adjustment")
    course.question(confounding, "challenge",
        ("A surgical registry records baseline risk and post-operative infection. The goal is the total effect of the operation type on recovery. Assume baseline risk is an adequate adjustment set. A colleague adds post-operative infection because it predicts recovery. What is the sound response?" if medical else
         "A learning-platform registry records baseline preparation and later study time. The goal is the total effect of coaching on passing. Assume baseline preparation is an adequate adjustment set. A colleague adds later study time because it predicts passing. What is the sound response?"),
        "Check the causal role before adjustment; a post-treatment mediator can block part of the total effect, so prediction alone does not justify adding it.",
        ["Always add the variable: every accurate predictor improves causal adjustment.", "Remove all baseline variables because observational studies can never support an effect under assumptions."],
        "A variable measured after treatment may lie on a pathway through which treatment works.",
        "The declared baseline set is adequate here. Adjusting for a mediator would generally target a different contrast, and other structures such as colliders can create bias. Neither maximal adjustment nor a blanket rejection of observational inference follows.", "adjustment")

    course.lesson(identification, "Ask what makes the effect identifiable",
        "If two causal explanations fit the same recorded association but disagree about a deliberate change, can the records choose between their effects?",
        [("1. Separate the question from its estimate", "The intervention effect is the target quantity. Identification asks whether the observed distribution and accepted assumptions determine that quantity. Estimation asks how accurately a finite sample approximates the identified expression. More data reduce sampling uncertainty but do not resolve an unacknowledged causal ambiguity."),
         ("2. State the assumptions that link worlds", f"For {population}, adjustment by {baseline} requires that no additional common cause remains after conditioning on it, that both programmes are available in relevant strata, and that the specified treatment corresponds to observed versions. Random assignment can support a different identification argument for assignment effects when follow-up and implementation are adequate."),
         ("3. Scope the conclusion", "Even a sound within-study identification argument does not establish transport to a new population, a new programme version or a different outcome time. State the target and design, report uncertainty, and mark which parts depend on causal knowledge rather than on the observed table.")],
        "An effect is identifiable relative to data and a model class when every model consistent with those inputs gives the same value for it. Identification is conditional on assumptions; a precise association is not a substitute.",
        "Agreement between one adjusted estimate and one trial estimate does not prove every causal assumption. A larger observational sample cannot by itself reveal a missing common cause.",
        "Before computing, state why the available data and assumptions determine this particular intervention contrast.", "identification")
    course.question(identification, "quiz",
        ("A registry has a million treatment/recovery records but omits an unmeasured factor that may cause both. No alternative identification design is supplied. What does the large sample establish about the treatment effect?" if medical else
         "A platform has a million coaching/passing records but omits an unmeasured factor that may cause both. No alternative identification design is supplied. What does the large sample establish about the coaching effect?"),
        "It may estimate the observed association precisely, but does not alone identify the intervention effect in the presence of unresolved confounding.",
        ["One million rows eliminate confounding even without measuring the common cause.", "A narrow confidence interval proves the intervention effect has been identified."],
        "Sampling error and causal ambiguity are different problems.",
        "Sample size addresses statistical precision for a chosen estimand. If an omitted common cause leaves multiple compatible intervention effects, observational precision does not choose one of them.", "identification")
    course.question(identification, "challenge",
        ("An otherwise well-run randomized trial identifies the assignment effect for eligible adults with complete follow-up. A team claims the same effect for children using a different dose and outcome time. Which part of that claim needs additional justification?" if medical else
         "An otherwise well-run randomized trial identifies the assignment effect for eligible adults with complete follow-up. A team claims the same effect for schoolchildren using a different programme length and outcome time. Which part of that claim needs additional justification?"),
        "Transport to the new population and versions; the original randomization does not establish that the same contrast holds there.",
        ["Nothing: randomization makes an effect universal across people, versions and times.", "Only the number of rows, because causal assumptions can never matter after a trial."],
        "Compare the original target population, treatment version and endpoint with the proposed use.",
        "Randomization supports the specified trial assignment contrast under its design conditions. Generalizing to different people, versions or timings requires a separate argument and usually additional evidence.", "identification")

    observed = table("programme-observed", "Self-selected programme records", ["Baseline", "A successes / total", "B successes / total"],
                     [[low, "18 / 20 (90%)", "64 / 80 (80%)"], [high, "48 / 80 (60%)", "8 / 20 (40%)"],
                      ["All records", "66 / 100 (66%)", "72 / 100 (72%)"]],
                     "The baseline is measured before programme selection. The target population is 50% in each baseline stratum.")
    experiment_model = {
        "kind": "effect", "a_low": 0.9, "a_high": 0.6, "b_low": 0.8, "b_high": 0.4,
        "selected_high_a_pct": 80, "selected_high_b_pct": 20,
        "low_label": low, "high_label": high, "outcome_label": outcome,
        "treatment_a_label": "Programme A", "treatment_b_label": "Programme B",
    }

    def experiment(title, instructions, assignment, target_high_pct, analysis):
        return {
            "title": title, "instructions": instructions, "model": experiment_model,
            "initial_config": {"kind": "effect", "assignment": assignment,
                               "target_high_pct": target_high_pct, "analysis": analysis},
        }

    story = f"Programme investigation: {population}. Compare A, {treatment}, with the specified B programme; success means {outcome}. The reference table is an earlier self-selected record. Use the controls and Run to compute new results, then compare and revise."
    course.question(confounding, "investigation",
        "Stage 1 of 4. Run and compare the same selected groups using pooled and standardized analysis. After recording your comparison and revision, which statement explains why the two analyses need not agree?",
        "Pooled groups can contain different baseline mixtures; standardization applies one declared target mixture to both groups, with a causal reading dependent on adequate adjustment assumptions.",
        ["The larger pooled rate always identifies the better intervention, regardless of selection.", "Standardization automatically removes every unmeasured common cause, whatever the causal structure."],
        "Compare the proportions in each baseline row with the mixture of rows inside each treatment.",
        "A pooled contrast retains each selected group's composition. A standardized contrast uses common target weights; it has a causal interpretation only under the declared valid-adjustment, overlap and consistency assumptions. Refer to your saved runs for their computed values.", "adjustment",
        tables=[observed], introduction=story, scenario="effect.programme-investigation", stage="investigate",
        experiment=experiment("Compare pooled and standardized analysis",
            "Keep self-selected assignment and the target at 50% higher-baseline cases. Before each run, submit your prediction. Run pooled analysis, then change only analysis to standardized and run again. Compare the saved outcomes and the baseline composition. Write what changed, whether it matched your prediction, and how you would revise your explanation. You may explore more settings before the scored check.",
            "self_selected", 50, "pooled"))
    course.question(intervention, "investigation",
        "Stage 2 of 4. Change only the programme assignment rule and compare your runs. What distinguishes this operation from merely filtering existing records by programme?",
        "It replaces the programme-selection mechanism while holding the declared outcome mechanisms fixed, rather than selecting people who already had a recorded treatment value.",
        ["Renaming an existing selected group randomized changes its assignment mechanism.", "Random assignment changes every person's baseline and guarantees that every person benefits."],
        "The selected plan must set assignment, not just select cases with a recorded treatment value.",
        "The assignment control changes how programmes are allocated in the declared model. Comparing existing treatment rows is conditioning instead. A real assignment-effect interpretation also depends on clear programme versions, follow-up and implementation; a simulated contrast is not a guarantee about each individual.", "intervention",
        tables=[observed], introduction=story, scenario="effect.programme-investigation", stage="investigate",
        experiment=experiment("Replace the assignment mechanism",
            "Keep the target at 50% higher-baseline cases and use pooled analysis. Predict and run the balanced randomized assignment. Then change only assignment to self-selected, submit a new prediction and run again. Compare treatment-group baseline composition and the outcome contrast. Reflect on what replacing assignment changed, what stayed fixed, and how the observation revises your initial account.",
            "randomized", 50, "pooled"))
    course.question(average, "investigation",
        "Stage 3 of 4. Hold the assignment rule and group-specific outcome mechanisms fixed, and compare two target-population mixtures using standardization. What does the target average contrast describe?",
        "The difference between population-average outcomes under the two programme assignments for the specified target mixture; it can change with that mixture without assigning the same benefit to every person.",
        ["A fixed individual benefit shared by every person, regardless of the target population.", "A relative percentage change that never needs outcome units or a target population."],
        "Use the same target weights for both assignments and state the units of their difference.",
        "The target-average contrast uses the same declared population mixture for both programme alternatives. Different target weights can change the average while leaving stratum-specific mechanisms and source records unchanged. A probability difference is reported in percentage points and does not reveal each person's effect.", "average",
        tables=[observed], introduction=story, scenario="effect.programme-investigation", stage="investigate",
        experiment=experiment("Change the target population",
            "Use randomized assignment and standardized analysis. Start with 20% higher-baseline cases in the target. Submit a prediction and run. Change only the target mixture to 80%, predict and run again. Compare target means and their difference; also check which source-population quantities did not change. Reflect on the population, units and whether an average can be assigned to every person.",
            "randomized", 20, "standardized"))
    course.question(identification, "investigation",
        "Stage 4 of 4. Compare assignment rules while keeping one target mixture and standardized analysis fixed. What licenses a causal interpretation of the adjusted target contrast in this teaching model?",
        "The declared adequate pre-treatment adjustment, overlap, consistent programme definitions and stable stratum mechanisms; agreement between runs does not prove those assumptions in an external population.",
        ["Two matching computed values prove there can be no hidden common cause in any real dataset.", "A precise simulated number establishes an identical effect for every new programme, population and outcome time."],
        "Separate the model's declared assumptions from what equality of two computed results can establish.",
        "Identification is conditional on the declared causal and design assumptions. This simulator keeps those mechanisms explicit; agreement of its runs cannot verify them for a real study or establish universal transport. Real finite-data estimates also require an uncertainty assessment.", "identification",
        tables=[observed], introduction=story, scenario="effect.programme-investigation", stage="investigate",
        experiment=experiment("Compare results and their assumptions",
            "Keep the target at 80% higher-baseline cases and use standardized analysis. Predict and run self-selected assignment, then change only assignment to randomized, predict and run again. Compare the results and write a reflection distinguishing model assumptions, computed evidence and what would require support in an external study. Revise your conclusion rather than treating agreement as proof of every assumption.",
            "self_selected", 80, "standardized"))

    final_population = "eligible clinic patients" if medical else "eligible community-library users"
    final_outcome = "attend the next appointment" if medical else "return a borrowed item on time"
    final_story = f"Final module quiz: a new reminder service for {final_population}. A is assignment to a precisely specified reminder, B is no reminder, and the endpoint is whether users {final_outcome} within 30 days. Apply each of the module's four ideas."
    final_table = table("reminder-final", "Completed randomized assignment", ["Assignment", "Endpoint reached / assigned", "Rate"],
                        [["Specified reminder", "82 / 100", "82%"], ["No reminder", "74 / 100", "74%"]],
                        "Assume random assignment, complete follow-up, consistent reminder versions and no interference. These are the study conditions, not a statement about other populations.")
    course.question(intervention, "final",
        f"Final 1 of 4. For {final_population}, which target matches the randomized reminder decision and the declared 30-day endpoint?",
        f"The average effect of assigning this reminder versus no reminder on whether users {final_outcome} in this eligible population.",
        ["The effect of choosing to read a reminder, even though reading was not randomized.", "The effect of every reminder technology in every population and time period."],
        "Use the variable the study assigned and the endpoint it actually followed.",
        "Assignment to the specified reminder is the intervention. Reading is later behaviour, and broader technologies or populations define different targets.", "intervention",
        tables=[final_table], introduction=final_story, scenario="effect.reminder-final", stage="capstone")
    course.question(average, "final",
        "Final 2 of 4. The randomized reminder arm has 82/100 endpoint successes versus 74/100 without a reminder. Ignoring sampling uncertainty only for the arithmetic, which estimate and interpretation are correct?",
        "+8 percentage points for reminder assignment in the study population, not a guarantee of benefit to each user.",
        ["+8% relative improvement, with no need to name a population.", "Exactly the same +8-point benefit for every user."],
        "Subtract the two proportions and retain probability-difference units.",
        "82%-74%=8 percentage points. The relative increase is 8/74, approximately 10.8%; neither quantity determines each user's individual response.", "average",
        tables=[final_table], introduction=final_story, scenario="effect.reminder-final", stage="capstone")
    course.question(confounding, "final",
        ("Final 3 of 4. In a separate non-randomized registry, baseline travel difficulty affects both opting into reminders and appointment attendance. Assume it suffices to block confounding and both reminder values occur in each stratum. What makes an adjusted comparison appropriate?" if medical else
         "Final 3 of 4. In a separate non-randomized registry, baseline travel difficulty affects both opting into reminders and on-time returns. Assume it suffices to block confounding and both reminder values occur in each stratum. What makes an adjusted comparison appropriate?"),
        "Use the same eligible-population travel-difficulty weights for each reminder value, under the stated adequate-adjustment, overlap and consistency assumptions.",
        ["Use each reminder group's own weights, since selected groups always represent the same population.", "Condition on later reminder reading and every outcome predictor without checking the causal structure."],
        "The adjusted alternatives should represent the same population before treatment.",
        "The causal assumptions license adjustment by the stated baseline variable. Common population weights remove differences in measured baseline composition; using selected-group weights or indiscriminately adjusting later variables does not do that.", "adjustment",
        tables=[final_table], introduction=final_story, scenario="effect.reminder-final", stage="capstone")
    course.question(identification, "final",
        "Final 4 of 4. A manager wants to apply the estimated +8-point reminder effect to a new population with a different reminder version and incomplete follow-up. Which assessment distinguishes identification, estimation and transport?",
        "The original design supports its specified assignment contrast under its assumptions; uncertainty, missingness and transport to the new population/version need separate assessment.",
        ["The +8-point sample estimate proves the true effect is exactly +8 everywhere.", "Randomization in one study automatically repairs missing outcomes and version changes in a later service."],
        "Track which conclusion belongs to the completed study and which belongs to a new use.",
        "Identification uses the study's causal/design assumptions; estimation has finite-sample uncertainty. A new version, population and follow-up process require a new argument rather than inheriting the original result automatically.", "identification",
        tables=[final_table], introduction=final_story, scenario="effect.reminder-final", stage="capstone")
    data = course.finish()
    apply_effect_revision(data, profile)
    revised = apply_effect_scaffold_revision(data, profile)
    apply_effect_challenge_revision(revised, profile)
    revised["version"] = VERSIONS["effect"]
    return revised


def shift_course(profile):
    medical = profile == "medical"
    course = Course("shift", profile, "Robust prediction or generation", SHIFT_CONCEPTS, SHIFT_CLAIMS,
                    "Researchers compare imaging workflows at two hospitals with a report draft; the illustration contains no diagnostic evidence or results." if medical else
                    "An inspection team compares parcel-camera workflows at two warehouses with a report draft; the illustration contains no evidence or results.")
    shift, prediction, invariance, limits = [c[0] for c in SHIFT_CONCEPTS]
    object_name = "chest images" if medical else "parcel photographs"
    target = "whether a reference-reviewed opacity is present" if medical else "whether reference inspection confirms parcel damage"
    env = "hospital" if medical else "warehouse"
    cue = "hospital-specific image marker" if medical else "warehouse-specific background label"
    content = "the image content relevant to the stated finding" if medical else "the visible parcel condition"
    noise = "a new acquisition protocol" if medical else "a new low-light camera setup"

    course.lesson(shift, "Locate what changes between environments",
        f"An assistant predicts {target} from {object_name} and drafts a short report. Its old test score is high. What must be checked before moving it to another {env}?",
        [("1. Describe training and deployment", f"Name the people or objects sampled, the input acquisition process, the endpoint definition and the intended use. In this case the new {env} may have different case proportions, cameras or scanners, labels and reporting conventions. A familiar file format does not mean the generating process is unchanged."),
         ("2. Separate types of change", f"The frequency of inputs can change while a useful target-given-input relation remains the same. Alternatively, measurement or the target-generating mechanism can change. A shift in {cue} could break a shortcut; a change in reference labels could also change what success means. A lower score alone does not identify the cause."),
         ("3. Evaluate the actual output", "A predictive score and a generated report are different outputs. Test prediction against independent reference outcomes; test generated content against source facts and required details. Use data from the intended external setting with a clean separation from training and tuning. A random split of the old setting does not recreate an unseen environment.")],
        "Distribution shift means that the joint data distribution differs between environments. Possible changes include case mixture, measurements, selection and the relation between inputs and the target; each has different implications.",
        "Do not infer 'the model is robust' from a high score on another random subset of its original environment, or infer one causal explanation from a performance drop alone.",
        "Specify which process could change, then collect evaluation evidence from the intended environment and output type.", "shift")
    course.question(shift, "quiz",
        ("A risk predictor is trained and randomly split within Hospital A. Hospital B uses a different measurement protocol and has a different patient mix. Which result directly addresses the proposed deployment?" if medical else
         "A delivery predictor is trained and randomly split within City A. City B uses a different sensor protocol and has a different mix of routes. Which result directly addresses the proposed deployment?"),
        "Evaluation on appropriately labelled, held-out data from the intended new environment, with its measurement and population differences documented.",
        ["Another random split of the original environment, treated as a guarantee about the new setting.", "Checking only that the input files have the same extension."],
        "Which evidence includes the environment the model is actually expected to face?",
        "External evaluation samples the intended changed setting. An old-environment split can measure a different question even when the input shape is identical; reference definitions and evaluation separation still need to be appropriate.", "shift")
    course.question(shift, "challenge",
        ("A hospital report generator retains its old average language-quality score after a scanner change, but no one has checked whether generated findings still match the images and source notes. What is missing?" if medical else
         "A product-description generator retains its old average language-quality score after a camera change, but no one has checked whether descriptions still match the photographed items and source records. What is missing?"),
        "External-setting content-fidelity evaluation against the source and relevant reference facts; fluent wording alone does not establish correct generation.",
        ["Nothing: a stable language score proves every generated factual statement remains correct.", "Only a prettier output font; output truth is unrelated to the changed inputs."],
        "A generator can produce convincing language while adding or omitting a crucial fact.",
        "A shift can affect content grounding even if fluency is stable. This course's generation criterion separately checks preserved facts, critical omissions and unsupported additions in the target environment.", "shift")

    course.lesson(prediction, "A predictor is not automatically a causal lever",
        f"Suppose the {cue} predicts the target well in the original data. Would editing the marker change the underlying outcome? Would removing it guarantee a reliable model?",
        [("1. Name the task", f"Predicting {target} concerns an outcome from available inputs. Changing the true outcome is a different causal question. In the supplied case, editing an image marker changes the recorded input but does not change the underlying condition of the person or parcel."),
         ("2. Explain the shortcut", f"The {cue} might track which cases arrived at which {env}. A model can exploit that association without learning {content}. If the case mixture or marker convention changes, the shortcut can fail. Strong predictive association therefore does not establish a useful intervention on the underlying target."),
         ("3. Avoid the opposite shortcut", f"A content-based or causally motivated feature still depends on measurement quality, available support and the target mechanism. {noise.capitalize()} might obscure the feature. Test paired input perturbations and external outcomes; do not declare universal reliability merely because a feature has a plausible causal story.")],
        "Predictive usefulness concerns information about a target under a data distribution. Causal usefulness concerns what would change the target under an intervention. Robustness concerns performance over specified environment changes; none of these implies the others by itself.",
        "Removing an obvious shortcut can help address one failure mode, but it does not prove the remaining model is causal or safe under every shift.",
        "Ask separately: what predicts, what changes the outcome, and which environment changes the evidence covers.", "prediction")
    course.question(prediction, "quiz",
        ("A diagnosis predictor relies on a hospital marker because the hospital sees more severe cases. In the declared case, digitally changing only that marker leaves the patient's condition unchanged. Which conclusion follows?" if medical else
         "A returns predictor relies on a warehouse label because that warehouse handles more fragile goods. In the declared case, digitally changing only that label leaves the parcel's condition unchanged. Which conclusion follows?"),
        "The marker can predict the outcome without being a lever that changes the underlying outcome.",
        ["Because the marker predicts well, editing it must improve the underlying outcome.", "Once the marker is removed, all future performance is guaranteed."],
        "Distinguish a change to a recorded cue from a change to the process producing the target.",
        "The stipulated input edit does not change the underlying condition. It can reveal sensitivity to a cue but cannot establish a causal treatment effect; removing the cue also leaves other robustness questions open.", "prediction")
    course.question(prediction, "challenge",
        ("A biomarker is genuinely upstream of a target in the proposed biological model. The deployment lab uses a new assay that measures it poorly. Should 'causal feature' be treated as a guarantee of predictive robustness?" if medical else
         "Traffic volume is genuinely upstream of journey time in the proposed transport model. The deployment city uses a new sensor that measures it poorly. Should 'causal feature' be treated as a guarantee of predictive robustness?"),
        "No. A causal role does not repair measurement error, changed support or a changed target mechanism; evaluate the intended measurement process and environment.",
        ["Yes. Any genuinely causal feature is perfectly measured and invariant under every possible change.", "No. A causal feature can never provide useful predictive information."],
        "The mechanism and the way a feature is measured are separate parts of the system.",
        "Causal knowledge can motivate features and assumptions, but the model consumes measured values. Changed measurement, limited support and changes to the outcome mechanism can still cause failure.", "prediction")

    course.lesson(invariance, "Use stability as a conditional argument",
        f"A content-based model performs similarly across three {env}s while a marker-based model varies sharply. What does that support, and what does it leave open?",
        [("1. Compare like relationships", "A shared aggregate accuracy is not the same as an invariant conditional relationship. Different subgroup errors can cancel in the average. Compare the outcome distribution given the candidate features across environments, using adequate sample sizes, common definitions and overlapping feature ranges."),
         ("2. Name the stable mechanism", f"A causal argument may suppose the rule linking {content} to the reference target is unchanged, while the environment changes marker conventions or case mixture. Under such assumptions a target mechanism can remain stable. The argument fails if the new environment directly changes that target mechanism or destroys measurement of the relevant inputs."),
         ("3. Keep evidence distinct from proof", "Stable conditional patterns across observed environments support a candidate relation under stated assumptions, but do not uniquely prove its causal direction. Other predictor sets can be invariant too. A new environment outside the tested range needs new justification and evaluation, even if the old comparisons looked reassuring.")],
        "Invariance is the persistence of a specified relationship across specified environments. Domain generalization uses an assumption about persistence into an unseen setting, with adequate support; observing stability is evidence about that assumption, not a universal guarantee.",
        "Equal overall scores can hide different conditional errors. Invariance across three sites does not prove the true graph or cover arbitrary interventions on the target.",
        "State the conditional relationship, the changes already tested and which mechanism is assumed to remain fixed next.", "invariance")
    course.question(invariance, "quiz",
        ("Across three hospitals, the conditional relation between a candidate measured feature and the reference outcome looks stable over overlapping ranges. What is a justified interpretation?" if medical else
         "Across three factories, the conditional relation between a candidate measured feature and the reference outcome looks stable over overlapping ranges. What is a justified interpretation?"),
        "It supports a scoped candidate invariance argument; causal interpretation and transfer still depend on assumptions about mechanisms, measurement and the new environment.",
        ["It proves this feature is a cause and guarantees accuracy after every future mechanism change.", "It has no relevance because only the best-fitting single site can matter."],
        "Evidence across environments is useful without proving every causal or future claim.",
        "The observed stability can support further investigation and a bounded prediction strategy. It neither uniquely establishes causality nor proves that an unseen target mechanism or measurement process will remain unchanged.", "invariance")
    course.question(invariance, "challenge",
        ("Two hospitals both report 85% overall accuracy. One model misses many high-risk patients at Hospital B but few at A; the proportions of patient subgroups differ. Does equal overall accuracy establish invariance of the relevant conditional relation?" if medical else
         "Two towns both report 85% overall accuracy. One model misses many remote-route delays in Town B but few in A; the proportions of route types differ. Does equal overall accuracy establish invariance of the relevant conditional relation?"),
        "No. Aggregate equality can hide compensating subgroup errors; compare the relevant conditional behaviour with overlapping support and uncertainty.",
        ["Yes. Identical aggregate accuracy proves all mechanisms and subgroup errors are unchanged.", "Yes. Subgroup composition never affects an aggregate performance score."],
        "The same average can result from different mixtures of different error rates.",
        "Marginal performance pools cases with different feature values. Conditional stability requires more targeted comparisons; equal overall scores alone do not supply that evidence.", "invariance")

    course.lesson(limits, "Test both accuracy and faithful generation",
        f"The assistant now moves to a {env} using {noise}. It also generates reports. What evidence would make its limits visible before routine use?",
        [("1. Predefine the failure criteria", "For prediction, choose the target label, useful error measures, important subgroups and uncertainty summaries. For generation, declare which input facts must be preserved, which unsupported additions are unacceptable and when a draft should be withheld for review. A fluent report can be wrong; an accurate average can conceal harmful subgroup errors."),
         ("2. Evaluate the external setting", "Use an external-environment set separated from training and tuning. Review generated outputs against source records and an appropriate independent reference; compare omission and addition rates as well as language quality. Evaluate unsupported input ranges explicitly rather than letting the easy cases dominate the score."),
         ("3. Define a response to uncertainty", "If an input is outside evaluated support or the source cannot establish a required fact, abstain from a confident prediction or generated claim and route for review. Monitor drift and errors after any bounded use, and re-evaluate when conditions change. These checks reduce exposure to known gaps; they do not promise zero errors or universal robustness.")],
        "A robustness claim should name the output task, evaluated environments, metrics and remaining assumptions. For this course's generated reports, fidelity means preserving required source facts while avoiding unsupported additions, even when style changes.",
        "A realistic-looking image, fluent paragraph or stable mean score does not establish factual preservation. Abstention is useful only with an explicit trigger and a practical review path.",
        "Validate the intended setting, preserve the required content and define when the system must withhold an unsupported output.", "limits")
    course.question(limits, "quiz",
        ("A report generator changes 'no opacity identified' to 'opacity present' while adapting to a new hospital's style. The paragraph is fluent and its style score improves. What has the output failed?" if medical else
         "An inspection-summary generator changes 'no crack found' to 'crack present' while adapting to a new factory's style. The paragraph is fluent and its style score improves. What has the output failed?"),
        "Content preservation: the generated factual assertion contradicts the source, regardless of its fluent style.",
        ["Nothing: a better style score authorizes changing facts.", "Only spelling; factual preservation is irrelevant to generation."],
        "Compare the meaning of the source assertion with the generated assertion.",
        "The declared generation task permits changes of wording, not an inversion of the source fact. Fidelity must be evaluated separately from fluency or realism in the intended environment.", "limits")
    course.question(limits, "challenge",
        ("An assistant receives a scan from a new protocol outside its evaluated range, and the source is insufficient to determine the requested finding. Which operating rule best matches the evidence?" if medical else
         "An assistant receives a photograph from a new sensor outside its evaluated range, and the source is insufficient to determine the requested damage detail. Which operating rule best matches the evidence?"),
        "Flag the unsupported case, withhold the confident claim and request review or suitable reference information before extending the claimed scope.",
        ["Generate the most plausible detail so the report is complete, then treat it as source evidence.", "Use the old mean score as a guarantee for the unsupported case."],
        "A missing source fact cannot be established by making the output sound confident.",
        "The case exceeds evaluated support and lacks a required source fact. A declared abstention/review rule keeps an unsupported assertion from being presented as established; additional evaluation is needed before widening scope.", "limits")

    old = table("site-original", f"Original {env} held-out set", ["Model", "Correct / evaluated", "Accuracy"],
                [["Cue-based A", "94 / 100", "94%"], ["Content-based B", "88 / 100", "88%"]],
                f"Both models predict {target}. This is a held-out split of the original environment, not a deployment guarantee.")
    experiment_model = {
        "kind": "shift",
        "source_positive": "Recorded opacity flag: present." if medical else "Recorded parcel-damage flag: present.",
        "source_negative": "Recorded opacity flag: absent." if medical else "Recorded parcel-damage flag: absent.",
        "qualifier": "Acquisition context: standard protocol." if medical else "Inspection context: controlled indoor light.",
        "unsupported_detail": "Acquisition context: enhanced protocol." if medical else "Inspection context: direct sunlight.",
    }

    def experiment(title, instructions, **changes):
        config = {"kind": "shift", "predictor": "cue", "cue_accuracy_pct": 90,
                  "measurement_error_pct": 10, "flip_cue": False, "generator": "fluent",
                  "metadata_available_pct": 100}
        config.update(changes)
        return {"title": title, "instructions": instructions, "model": experiment_model, "initial_config": config}

    report_type = "clinical" if medical else "inspection"
    story = f"Assistant investigation: predict {target} from {object_name}, then draft a source-grounded {report_type} report. The reference table describes an earlier setup, not your current run. Change the controls, predict, run and compare the generated cases before revising your explanation."
    course.question(shift, "investigation",
        "Stage 1 of 4. Change the cue relationship while holding the predictor and measurement process fixed. After comparing two actual runs, what can this comparison establish?",
        "How the chosen predictor performs under these declared environment settings; an old score alone does not establish performance after a new change.",
        ["A high score in the first run guarantees the same accuracy for every other environment.", "The model with the most promising name is guaranteed robust without running the changed setting."],
        "Compare evidence from the settings actually run, rather than extending a score to untested changes.",
        "A controlled environment comparison measures the selected model under the declared change. Its scope is the settings and outputs evaluated; neither an old score nor a model label guarantees performance under other measurement or target changes.", "shift",
        tables=[old], introduction=story, scenario="shift.assistant-investigation", stage="investigate",
        experiment=experiment("Change the cue relationship",
            "Keep the cue predictor, measurement error and generation strategy fixed. Submit a prediction and run with cue reliability at 90%. Change only cue reliability to 50%, predict again and run. Inspect the generated cases and compare prediction against reference truth. Reflect on which input relationship changed, what the scores show and how you revise your expectation for a new environment."))
    course.question(prediction, "investigation",
        f"Stage 2 of 4. Compare matched runs that edit only the {cue}. If a prediction changes while the reference truth stays fixed, what has the edit tested?",
        "The model's dependence on a recorded cue, rather than an intervention that changes the underlying outcome.",
        ["The input edit changed the underlying condition because the model's output changed.", "The edit proves that every content-based model must work under all future measurement protocols."],
        "A change in a model's output is not necessarily a change in the real target.",
        "The cue-edit control changes recorded inputs while keeping reference truth and measured content fixed. It probes model dependence. A prediction change is not an outcome-changing intervention or a universal robustness result.", "prediction",
        tables=[old], introduction=story, scenario="shift.assistant-investigation", stage="investigate",
        experiment=experiment("Edit the cue without changing the target",
            "Use the cue predictor and grounded generation. Hold cue reliability and measurement error fixed. Predict and run with cue editing off, then turn only cue editing on, make a new prediction and run again. Compare matching case IDs: source content and reference truth versus cue and prediction. Reflect on whether an input edit and an intervention on the underlying outcome are the same action.",
            generator="grounded"))
    course.question(invariance, "investigation",
        "Stage 3 of 4. Inspect a content predictor across cue changes, then explore a measurement change. Which statement correctly scopes any observed stability?",
        "Stability under the tested cue changes concerns that declared relationship; it neither proves a causal graph nor guarantees stability after the measurement or target mechanism changes.",
        ["Stable scores in two cue settings guarantee perfect predictions under every measurement change.", "The best score in one original setting uniquely establishes every causal arrow."],
        "State what changed, what remained fixed and which mechanism a new setting could alter.",
        "The content predictor can be unaffected by cue-only edits in the declared model because it reads another input. Measurement changes still affect that input. Observed stability has a stated scope; aggregate equality alone is not a proof of conditional invariance or a uniquely identified graph.", "invariance",
        tables=[old], introduction=story, scenario="shift.assistant-investigation", stage="investigate",
        experiment=experiment("Test the boundary of stability",
            "Choose the content predictor and grounded generation. Predict and run the initial setting. Change only cue reliability, predict and run again; compare the reference groups and matching case IDs. You can then add a third run changing only measurement error to test a different boundary. Reflect on the relationship that stayed stable, which changes were actually tested and why this does not prove universal robustness.",
            predictor="content", generator="grounded"))
    course.question(limits, "investigation",
        "Stage 4 of 4. Compare complete and source-preserving drafts for the same measured cases, including records with missing required context. Which interpretation keeps prediction truth and generation fidelity separate?",
        "A draft can preserve the recorded source without proving the underlying target is correct; missing required context should be exposed rather than replaced by an unsupported factual detail.",
        ["Faithful copying proves that a noisy measurement is the true underlying outcome.", "A fluent complete draft may invent missing context and treat the invention as source evidence."],
        "Evaluate predictions against independent reference truth and generated assertions against what the source actually contains.",
        "Content fidelity concerns preservation of the measured source and its available context, while prediction accuracy concerns reference truth. Source-preserving generation may withhold an incomplete report; filling a gap does not establish its truth. Compare coverage, source fidelity and unsupported details from your runs before deciding how to review unsupported cases.", "limits",
        tables=[old], introduction=story, scenario="shift.assistant-investigation", stage="investigate",
        experiment=experiment("Compare complete and source-preserving drafts",
            "Start with the content predictor, the declared measurement error and required context available in 60% of source records. Keep those inputs fixed. Submit a prediction and run fluent generation, then change only the generator to grounded, predict and run again. Compare actual source text, report text, output coverage, source-fidelity metrics and prediction against reference truth. Reflect on omissions or unsupported details, whether withholding changed coverage and why faithful copying does not repair measurement error.",
            predictor="content", cue_accuracy_pct=50, measurement_error_pct=30, flip_cue=True,
            metadata_available_pct=60))

    final_name = "a readmission predictor and discharge-summary drafter moving between hospitals" if medical else "a flood-alert predictor and incident-bulletin drafter moving between towns"
    final_cue = "the hospital identifier" if medical else "the town identifier"
    final_feature = "pre-discharge measurements" if medical else "upstream rainfall measurements"
    final_story = f"Final module quiz: review {final_name}. The target is a reference-defined future event; the draft must preserve source facts. Each item tests a different module concept in this new setting."
    final_eval = table("new-service-final", "External evaluation summary", ["Check", "Original setting", "External setting"],
                       [["Event prediction accuracy", "91 / 100", "72 / 100"],
                        ["Drafts preserving all required source facts", "96 / 100", "78 / 100"],
                        ["Drafts with unsupported factual additions", "1 / 100", "12 / 100"]],
                       "The external set uses a new recording protocol and a changed case mix. The table does not identify which change caused each error.")
    course.question(shift, "final",
        "Final 1 of 4. External prediction accuracy is 72/100 instead of 91/100 and source-faithful drafts fall from 96/100 to 78/100. What does this evaluation establish?",
        "The evaluated external setting has worse performance on both declared tasks; investigate measurement, case mix and target differences rather than attributing the drop to one cause from this table alone.",
        ["The original random split was a universal guarantee, so external errors must be impossible.", "The table proves the new recording protocol is the sole causal reason for every error."],
        "A performance comparison describes what happened under the tested conditions, not a uniquely identified cause.",
        "The table gives external task-performance evidence and reveals a gap. Because several processes differ, it does not isolate the causal contribution of each change; prediction and generation need their own checks.", "shift",
        tables=[final_eval], introduction=final_story, scenario="shift.new-service-final", stage="capstone")
    course.question(prediction, "final",
        f"Final 2 of 4. The team proposes either using {final_cue} as a predictor or using {final_feature} with a plausible causal role. Which statement correctly separates prediction, intervention and robustness?",
        "The identifier may predict without being an outcome lever; the measured features may be useful, but a causal story alone does not guarantee correct measurement or transfer.",
        ["The most predictive identifier must be the best intervention target.", "Any feature with a plausible causal role must work perfectly under every recording change."],
        "A predictive association, an outcome-changing action and a transfer guarantee are three different claims.",
        "A setting identifier can encode selection or measurement conventions. Mechanistically motivated features can still fail through measurement changes, lack of support or altered target mechanisms, so the intended use needs evaluation.", "prediction",
        tables=[final_eval], introduction=final_story, scenario="shift.new-service-final", stage="capstone")
    course.question(invariance, "final",
        "Final 3 of 4. A selected feature set has a stable outcome-given-features relation across two original settings with overlapping support. The new setting changes the target mechanism directly. Which inference is justified?",
        "The original invariance argument does not cover a direct change to the target mechanism; new-environment evidence and revised assumptions are required.",
        ["Two stable settings prove that no target-mechanism change can affect the relation.", "Observed stability uniquely identifies every causal arrow, so external evaluation is unnecessary."],
        "The invariance argument assumed a particular mechanism persisted; check whether that assumption still applies.",
        "A relationship can persist when other mechanisms change yet fail when its own target mechanism is altered. Evidence from the original settings cannot establish the excluded case automatically.", "invariance",
        tables=[final_eval], introduction=final_story, scenario="shift.new-service-final", stage="capstone")
    course.question(limits, "final",
        "Final 4 of 4. External drafts have unsupported additions in 12/100 cases. A new input lies outside the evaluated recording range and lacks a required source fact. Which final evaluation/operating plan is appropriate?",
        "Evaluate required-fact preservation and unsupported additions by environment and relevant subgroup, with independent references; withhold the unsupported claim and route this case for review while monitoring defined errors.",
        ["Prefer fluent completeness, invent the missing fact and count the invented claim as a correct reference.", "Report only pooled language quality and silently extend the old performance claim to the unsupported range."],
        "A faithful draft must be supported by its input; missing evidence needs a visible review rule.",
        "The course's generation criterion treats preservation, omissions and unsupported additions as distinct from style. External evaluation, uncertainty, scoped use and an explicit abstention/review path address the stated gaps without claiming zero future errors.", "limits",
        tables=[final_eval], introduction=final_story, scenario="shift.new-service-final", stage="capstone")
    data = course.finish()
    revised = apply_shift_scaffold_revision(apply_shift_revision(data, profile), profile)
    apply_shift_challenge_revision(revised, profile)
    revised["version"] = VERSIONS["shift"]
    return revised


def course_filename(task, profile):
    return f"m1_{task}_course_{profile}_{VERSIONS[task].replace('.', '_')}.json"


def build_all():
    return {course_filename(task, profile): builder(profile)
            for task, builder in (("effect", effect_course), ("shift", shift_course))
            for profile in ("general", "medical")}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    for filename, data in build_all().items():
        path = ROOT / "content" / filename
        output = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != output:
                raise SystemExit(f"Regenerate {path.name}")
        else:
            path.write_text(output, encoding="utf-8")
        verb = "Checked" if args.check else "Built"
        print(f"{verb} {path.relative_to(ROOT)}: {len(data['lessons'])} lessons, {len(data['activities'])} activities")


if __name__ == "__main__":
    main()
