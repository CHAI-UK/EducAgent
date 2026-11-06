"""Build the Portal Foundations course without rewriting its historical pack."""

import argparse
import json
from pathlib import Path

from educagent_sdk import ContentPack, load_content_pack, validate_release
from educagent_sdk.foundation_profiles import CONCEPT_CLAIM_IDS, load_foundation_profiles
if __package__:
    from .foundation_assessment_revision import apply_assessment_revision, apply_data_world_challenge
    from .foundation_complementary_challenges import apply_complementary_challenges
    from .foundation_dynamic_umbrella import apply_dynamic_umbrella
    from .foundation_expert_review import apply_review
    from .foundation_learner_revision import apply_learner_revision
else:
    from foundation_assessment_revision import apply_assessment_revision, apply_data_world_challenge
    from foundation_complementary_challenges import apply_complementary_challenges
    from foundation_dynamic_umbrella import apply_dynamic_umbrella
    from foundation_expert_review import apply_review
    from foundation_learner_revision import apply_learner_revision


ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.8.0"

# Keep earlier course outputs available for their existing learning traces.
def course_path(profile_id: str) -> Path:
    return ROOT / f"content/foundation_{profile_id}_course_{VERSION.replace('.', '_')}.json"


SCENE_COPY = {
    "hook": "Umbrellas and wet pavement often appear together. Start with a possible explanation, then compare it with the example records.",
    "records": "Each record is one person's arrival at campus. The table groups 240 arrivals by umbrella carrying and pavement wetness. These are arrival records, not 240 different days.",
    "prediction": "Predict whether wet pavement would be more common, less common or unchanged if everyone carried an umbrella.",
    "intervention": "An intervention actively sets a variable instead of only recording it. Here, make all 240 people carry an umbrella, including the 144 who originally did not. Keep the background conditions the same. This example uses a prewritten teaching-model result, not calculated from your proposed arrows.",
    "result": "Wet pavement remains in 96 of 240 records (40%). All 240 records stay in the example. Filtering the original umbrella carriers would keep only 96 records, all with wet pavement (100%). Changing carrying and selecting existing carriers are different comparisons.",
    "reflection": "Keep or revise your explanation. For the graph check, use the supplied assumptions: rain affects both umbrella carrying and pavement wetness, with no other direct arrows. This result alone does not establish that graph.",
    "explanation": "The graph check asks you to represent the supplied rain assumptions, not discover a unique graph from these records. The intervention kept wetness at 40%; filtering original carriers would give 100%. Your written reflection is not scored.",
}

# The final case tests each objective directly, rather than granting nine-topic
# credit from one question labelled as covering the whole curriculum.
FINAL_CASES = (
    {
        "general": "A community reading programme records 0, 2 or 4 sessions attended for each participant. Which option names the variable being recorded?",
        "medical": "A rehabilitation programme records 0, 2 or 4 sessions attended for each patient. Which option names the variable being recorded?",
        "options": ("Number of sessions attended", "4 sessions", "2 sessions", "0 sessions"),
        "explanation": "The variable is the feature recorded for every person. Zero, two and four are possible values of that feature.",
    },
    {
        "general": "In programme records, 20 people attending at least three reading sessions have a mean comprehension score of 74; 20 attending fewer sessions have a mean of 62. What do these records show directly?",
        "medical": "In programme records, 20 patients attending at least three rehabilitation sessions have a mean mobility score of 60; 20 attending fewer sessions have a mean of 48. What do these records show directly?",
        "options": ("These records suggest that attendance and score may be associated", "Assigning more sessions necessarily raises the score", "A higher score causes attendance", "The groups were randomly assigned"),
        "explanation": "The recorded groups have different mean scores, suggesting an association. This small table does not establish a population-wide relationship or either causal direction; no intervention is recorded.",
    },
    {
        "general": "Participants chose whether to attend the reading sessions. The programme team says the higher scores among frequent attendees prove that offering more sessions will help everyone. What can you conclude?",
        "medical": "Patients chose whether to attend the rehabilitation sessions. The programme team says the higher mobility scores among frequent attendees prove that offering more sessions will help everyone. What can you conclude?",
        "options": ("The group difference alone does not establish the effect of assigning sessions", "Every person will improve by the observed group difference", "Attendance cannot possibly affect the score", "A larger observational table would automatically remove all alternative explanations"),
        "explanation": "People chose whether to attend, so the groups could differ for other reasons. The observed pattern alone proves neither a benefit nor an absence of effect.",
    },
    {
        "general": "Which question directly asks about the effect of an intervention in this reading programme?",
        "medical": "Which question directly asks about the effect of an intervention in this rehabilitation programme?",
        "options": ("How would mean follow-up scores differ if comparable people were assigned different session offers?", "Who attended most sessions last month?", "What was the largest recorded score?", "Which two recorded columns are associated?"),
        "explanation": "An intervention-effect question specifies a change to the offer and asks about the resulting outcome, rather than merely describing existing records.",
    },
    {
        "general": "The coordinator uses random numbers to assign participants to a three-session offer or a one-session offer, then records scores. How does this differ from grouping people by their existing attendance?",
        "medical": "The coordinator uses random numbers to assign patients to a three-session offer or a one-session offer, then records mobility scores. How does this differ from grouping patients by their existing attendance?",
        "options": ("The offer is deliberately assigned rather than only observed", "Recording an outcome guarantees that everyone receives the same value", "Random assignment proves the intervention helps every individual", "Both approaches merely observe an existing offer"),
        "explanation": "The deliberate assignment is the intervention. Random assignment does not guarantee a beneficial effect or an identical outcome for everyone.",
    },
    {
        "general": "Family encouragement was not measured. A researcher proposes that it influences both attendance and reading progress. Is this explanation part of the world, data or a model?",
        "medical": "Baseline illness severity was not measured. A researcher proposes that it influences both attendance and mobility recovery. Is this explanation part of the world, data or a model?",
        "options": ("A model of how the system may work", "A measured value in the attendance column", "The complete underlying world itself", "A directly observed effect of random assignment"),
        "explanation": "A proposed explanation is part of the model. It may describe an unmeasured part of the world, but proposing it does not make it observed data or show that it is true.",
    },
    {
        "general": "The attendance table contains only session counts and follow-up scores. Which statement adds a causal assumption beyond those recorded columns?",
        "medical": "The rehabilitation table contains only session counts and follow-up mobility scores. Which statement adds a causal assumption beyond those recorded columns?",
        "general_options": ("Initial motivation affects both attendance and later scores", "The high-attendance group contains 20 records", "The high-attendance group has the larger recorded mean", "Each row contains an attendance count and a score"),
        "medical_options": ("Baseline severity affects both attendance and later mobility scores", "The high-attendance group contains 20 records", "The high-attendance group has the larger recorded mean", "Each row contains an attendance count and a mobility score"),
        "explanation": "A claim about what causes attendance and scores is an additional causal assumption. Row counts, recorded means and recorded columns describe the data.",
    },
    {
        "general": "A proposed diagram shows Offer → Sessions attended → Comprehension score. How would you describe the route from Offer to Comprehension score?",
        "medical": "A proposed diagram shows Offer → Sessions attended → Mobility score. How would you describe the route from Offer to Mobility score?",
        "options": ("A directed path through an intermediate variable", "One measured value", "A directed cycle returning to Offer", "A numerical estimate of the intervention effect"),
        "explanation": "Following both arrows gives a directed path through sessions attended. There is no arrow returning to Offer, and drawing the path does not estimate an effect size.",
    },
    {
        "general": "A teaching simulator sets the chance of reaching a reading target to 0.40 under a one-session offer and 0.60 under a three-session offer. Some simulated people assigned three sessions still miss the target. Which interpretation is correct?",
        "medical": "A teaching simulator sets the chance of reaching a mobility target to 0.40 under a one-session offer and 0.60 under a three-session offer. Some simulated patients assigned three sessions still miss the target. Which interpretation is correct?",
        "options": ("The model changes the target's probability without guaranteeing each person's outcome", "The model guarantees success for every person offered three sessions", "One failure disproves the stipulated probability difference", "The numbers prove a real-world treatment benefit"),
        "explanation": "The stipulated chance increases by 0.20, or 20 percentage points. A probability of 0.60 still permits failures; these simulator rules are not a real-world effect estimate.",
    },
)


def build(profile_id: str) -> ContentPack:
    base = load_content_pack(ROOT / "content/causality_m0_full.json")
    profiles = load_foundation_profiles(base, ROOT / "content/foundation_profiles.json")
    data = profiles[profile_id].model_dump(mode="json")
    data.update(pack_id=f"causality.m0.{profile_id}.course", version=VERSION,
                title="Causality foundations")
    apply_review(data, profile_id)
    for item in data["resources"]:
        suffix = item["resource_id"].removeprefix("scene.rain-umbrella.")
        if item["resource_id"].startswith("scene.rain-umbrella.") and suffix in SCENE_COPY:
            item["text"] = SCENE_COPY[suffix]
    data["causal_scenes"][0]["title"] = "Umbrellas and wet pavement"
    fixture_id = "foundation.final-case"
    data["claims"].append({
        "claim_id": fixture_id,
        "proposition": "The programme records and probability rules in the final case are authored teaching fixtures, not empirical findings.",
        "deterministic_derivation": {"method_id": fixture_id, "method_version": VERSION},
        "release_status": "released",
    })
    for index, (concept, case) in enumerate(zip(data["concepts"], FINAL_CASES)):
        # Keep the final at the end of the route, outside topic-local prefixes.
        activity_id = f"m0-final-quiz.{index + 1:02d}"
        prefix = activity_id + ".final"
        claims = [*CONCEPT_CLAIM_IDS[concept["concept_id"]], fixture_id]

        def resource(suffix: str, kind: str, text: str) -> str:
            resource_id = prefix + "." + suffix
            data["resources"].append({"resource_id": resource_id, "kind": kind,
                "text": text, "claim_ids": claims, "release_status": "released"})
            return resource_id

        question = case[profile_id]
        score_label = "Mean comprehension score" if profile_id == "general" else "Mean mobility score"
        high_score, low_score = ("74", "62") if profile_id == "general" else ("60", "48")
        columns = ["Existing attendance", "People", score_label]
        rows = [["At least three sessions", "20", high_score],
                ["Fewer than three sessions", "20", low_score]]
        question_id = resource("question", "question", question + "\n\nEarlier observed groups:\n"
                               + "\n".join(" | ".join(row) for row in [columns, *rows]))
        explanation = case["explanation"]
        explanation_id = resource("explanation", "explanation", explanation)
        hint_id = resource("hint", "hint", "Separate the recorded information, the proposed explanation and the deliberately assigned action.")
        accepted_id = resource("accepted", "consequence", explanation)
        rejected_id = resource("rejected", "consequence", "Reconsider the distinction in this question. " + explanation)
        options = case.get(profile_id + "_options", case.get("options"))
        # Rotate positions while keeping answer IDs stable and semantic.
        order = list(range(4))
        offset = index % 4
        order = order[offset:] + order[:offset]
        choices = [{"option_id": f"{prefix}.option.{option + 1}", "text": options[option],
                    "correct": option == 0,
                    "consequence_resource_id": accepted_id if option == 0 else rejected_id,
                    **({} if option == 0 else {"misconception_id": concept["concept_id"] + ".final-gap", "hint_resource_ids": [hint_id]})}
                   for option in order]
        data["activities"].append({
            "activity_id": activity_id, "concept_id": concept["concept_id"],
            "activity_type": "choice", "question_resource_id": question_id,
            "choices": choices, "explanation_resource_id": explanation_id,
            "is_transfer": True,
            "workbench": {
                "title": f"Foundations final check · Question {index + 1} of 9",
                "introduction": "Use the programme case to bring together the ideas from this course.",
                "prompt": question,
                "scenario_id": "foundation.programme.final", "stage": "capstone",
                "tables": [{"table_id": "earlier-records", "label": "Earlier observed groups",
                    "columns": columns, "rows": rows,
                    "note": "People chose their attendance; these rows do not describe a randomized assignment."}],
            },
        })
        concept["completion_activity_ids"].append(activity_id)
    apply_learner_revision(data, profile_id)
    apply_assessment_revision(data, profile_id)
    apply_data_world_challenge(data, profile_id)
    apply_dynamic_umbrella(data)
    apply_complementary_challenges(data, profile_id)
    pack = ContentPack.model_validate_json(json.dumps(data))
    validate_release(pack)
    return pack


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for profile_id in ("general", "medical"):
        pack = build(profile_id)
        destination = course_path(profile_id)
        output = pack.model_dump_json(indent=2) + "\n"
        if args.check:
            if not destination.exists() or destination.read_text(encoding="utf-8") != output:
                raise SystemExit(f"Regenerate {destination.name}")
        else:
            destination.write_text(output, encoding="utf-8")
        print(f"{profile_id}: {len(pack.concepts)} concepts, {len(pack.activities)} activities, {len(pack.lessons)} explanations")


if __name__ == "__main__":
    main()
