"""The new learner revision remains an authored, deterministic Foundations pack."""

import copy
import json
import unittest
from pathlib import Path

from authoring.foundation_learner_revision import apply_learner_revision
from educagent_sdk import (
    ClassificationEvidence, ContentPack, evaluate_classification, load_content_pack,
    validate_release,
)
from educagent_sdk.evaluation import ChoiceEvidence, evaluate_evidence


ROOT = Path(__file__).resolve().parents[1]


class FoundationLearnerRevisionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.historical = {
            profile: load_content_pack(ROOT / f"content/foundation_{profile}_course_1_3_0.json")
            for profile in ("general", "medical")
        }

    def revised(self, profile):
        data = self.historical[profile].model_dump(mode="json")
        apply_learner_revision(data, profile)
        return ContentPack.model_validate_json(json.dumps(data))

    def test_revision_preserves_curriculum_activity_ids_and_old_pack_objects(self):
        for profile, historical in self.historical.items():
            with self.subTest(profile=profile):
                frozen = historical.model_dump_json()
                pack = self.revised(profile)
                self.assertEqual(len(pack.activities), 28)
                self.assertEqual(len(pack.lessons), 9)
                self.assertEqual(pack.concepts, historical.concepts)
                self.assertEqual(pack.sources, historical.sources)
                self.assertEqual(pack.causal_scenes, historical.causal_scenes)
                self.assertEqual(tuple(a.activity_id for a in pack.activities),
                                 tuple(a.activity_id for a in historical.activities))
                self.assertEqual(tuple(r.resource_id for r in pack.resources),
                                 tuple(r.resource_id for r in historical.resources))
                self.assertEqual(tuple(c.claim_id for c in pack.claims),
                                 tuple(c.claim_id for c in historical.claims))
                for original, revised in zip(historical.activities, pack.activities, strict=True):
                    self.assertEqual({c.option_id for c in original.choices if c.correct},
                                     {c.option_id for c in revised.choices if c.correct})
                    self.assertTrue({c.option_id for c in original.choices}.issubset(
                        {c.option_id for c in revised.choices}))
                    self.assertEqual(original.activity_type, revised.activity_type)
                    self.assertEqual(original.requires_revision, revised.requires_revision)
                    self.assertEqual(original.is_transfer, revised.is_transfer)
                self.assertEqual(validate_release(pack).unused_resource_ids, ())
                self.assertEqual(historical.model_dump_json(), frozen)

    def test_variable_questions_distinguish_lists_of_features_values_and_settings(self):
        for profile in self.historical:
            pack = self.revised(profile)
            resources = {r.resource_id: r.text for r in pack.resources}
            for stage in ("practice", "transfer"):
                with self.subTest(profile=profile, stage=stage):
                    activity = next(a for a in pack.activities
                                    if a.activity_id == f"variables-and-values.{stage}")
                    self.assertEqual(len(activity.choices), 4)
                    self.assertIn("two variables recorded in this table", resources[activity.question_resource_id])
                    if stage == "practice":
                        self.assertTrue(resources[activity.question_resource_id].startswith("A variable is a feature"))
                    self.assertEqual(sum(choice.correct for choice in activity.choices), 1)
                    for index, choice in enumerate(activity.choices):
                        evidence = ClassificationEvidence(
                            activity_id=activity.activity_id,
                            classification_id=choice.option_id,
                            artifact_id=f"learner-revision.{profile}.{stage}.{index}",
                        )
                        self.assertEqual(evaluate_classification(pack, evidence).accepted, choice.correct)
                    self.assertTrue(all("Fixed story detail" not in c.text for c in activity.choices))
                    correct = next(c.text for c in activity.choices if c.correct)
                    self.assertNotIn("The clinic", correct)
                    self.assertNotIn("The IT service", correct)
            variable_lesson = next(l for l in pack.lessons if l.concept_id == "variables-and-values")
            self.assertIn("depends on what this table records", resources[variable_lesson.definition_resource_id])
            self.assertIn("another study", resources[variable_lesson.pitfall_resource_id])
            if profile == "general":
                self.assertIn("IT service", resources[variable_lesson.pitfall_resource_id])
                self.assertNotIn("clinic", resources[variable_lesson.pitfall_resource_id].lower())
            else:
                self.assertIn("clinic", resources[variable_lesson.pitfall_resource_id])
            if profile == "general":
                self.assertIn("failed-login alert count", resources["variables.question.practice"])
                self.assertIn("support ticket", resources["variables.question.transfer"])
                self.assertIsNone(variable_lesson.scenario_image)
            else:
                self.assertIn("resting heart rate", resources["variables.question.practice"])
                self.assertIn("systolic blood pressure", resources["variables.question.transfer"])

    def test_association_options_read_patterns_without_untaught_causal_labels(self):
        for profile in self.historical:
            with self.subTest(profile=profile):
                pack = self.revised(profile)
                for stage in ("practice", "transfer"):
                    activity = next(a for a in pack.activities
                                    if a.activity_id == f"observed-association.{stage}")
                    for choice in activity.choices:
                        self.assertIn("in these records", choice.text)
                        self.assertNotIn("Established causal effect", choice.text)
                        self.assertNotIn("Observed association", choice.text)
                        if not choice.correct:
                            self.assertEqual(choice.misconception_id, "association-direction-misread")

    def test_all_lessons_have_compact_first_read_and_separate_worked_detail(self):
        for profile in self.historical:
            with self.subTest(profile=profile):
                pack = self.revised(profile)
                resources = {r.resource_id: r.text for r in pack.resources}
                for lesson in pack.lessons:
                    self.assertLessEqual(len(resources[lesson.hook_resource_id].split()), 50)
                    self.assertLessEqual(len(resources[lesson.definition_resource_id].split()), 65)
                    self.assertEqual(len(lesson.worked_steps), 3)
                    self.assertTrue(all(len(resources[step.resource_id].split()) <= 45
                                        for step in lesson.worked_steps))
                    self.assertEqual(lesson.review_status, "author_draft")
                self.assertIn("actively sets a variable", resources[
                    next(l for l in pack.lessons if l.concept_id == "association-is-not-causation").definition_resource_id])
                self.assertIn("recorded values of one or more variables", resources[
                    next(l for l in pack.lessons if l.concept_id == "world-data-model").definition_resource_id])

    def test_example_labels_stay_with_their_revised_stories(self):
        for profile in self.historical:
            pack = self.revised(profile)
            resources = {r.resource_id: r.text for r in pack.resources}
            labels = {lesson.concept_id: resources[lesson.example_label_resource_id]
                      for lesson in pack.lessons}
            self.assertTrue(all("review pending" not in text.lower() for text in labels.values()))
            self.assertTrue(all(lesson.review_status == "author_draft" for lesson in pack.lessons))
            self.assertIn("umbrella model", labels["basic-dag-language"])
            if profile == "general":
                self.assertIn("study-session offer", labels["treatment-and-outcome"])
                self.assertIn("reminder setting", labels["observation-vs-intervention"])
                self.assertIn("electricity readings", labels["world-data-model"])
                self.assertFalse(any("drug" in text or "sleep intervention" in text or "disease"
                                     in text for text in labels.values()))
            else:
                self.assertIn("no benefit or dose recommendation", labels["treatment-and-outcome"])

    def test_causal_graph_defines_direction_acyclicity_and_two_path_concepts(self):
        for profile in self.historical:
            with self.subTest(profile=profile):
                pack = self.revised(profile)
                resources = {r.resource_id: r.text for r in pack.resources}
                lesson = next(l for l in pack.lessons if l.concept_id == "basic-dag-language")
                self.assertEqual(lesson.title, "Read a causal graph")
                definition = resources[lesson.definition_resource_id]
                self.assertIn("directed acyclic graph", definition)
                self.assertIn("cannot lead back", definition)
                self.assertIn("regardless of arrow direction", definition)
                self.assertIn("follows every arrow forward", definition)
                self.assertIn("assumptions", definition)
                self.assertIn("can be right or wrong", resources[lesson.pitfall_resource_id])
                self.assertIn("causal graph", resources["integrated.question"])
                self.assertNotIn("DAG", resources["integrated.question"])

    def test_probability_questions_do_not_confuse_heterogeneity_with_random_mechanisms(self):
        for profile in self.historical:
            with self.subTest(profile=profile):
                pack = self.revised(profile)
                resources = {r.resource_id: r.text for r in pack.resources}
                self.assertIn("does not tell us whether", resources["probability.explanation"])
                self.assertIn("deterministic or random", resources["probability.explanation"])
                for stage in ("practice", "transfer"):
                    activity = next(a for a in pack.activities
                                    if a.activity_id == f"probabilistic-effects.{stage}")
                    self.assertIn("What follows?", resources[activity.question_resource_id])
                    self.assertNotIn("or deterministic", resources[activity.question_resource_id])
                    correct = next(c for c in activity.choices if c.correct)
                    self.assertTrue("not guaranteed" in correct.text or "not certain" in correct.text or "remains possible" in correct.text)
                    self.assertNotIn("deterministic", correct.text.lower())
                probability_claims = [c for c in pack.claims if c.claim_id in {
                    "causes-can-change-probability", f"foundation.{profile}.probabilistic-effects.reference",
                }]
                self.assertEqual(len(probability_claims), 2)
                self.assertTrue(all("does not require" in c.proposition for c in probability_claims))

    def test_new_exercise_image_is_versioned_and_medical_context_stays_separate(self):
        general = self.revised("general")
        medical = self.revised("medical")
        for items in (general.lessons, general.activities):
            item = next(item for item in items if getattr(item, "concept_id") == "observed-association"
                        and (not hasattr(item, "activity_id") or item.activity_id.endswith(".practice")))
            self.assertEqual(item.scenario_image.path, "media/causality-m0/observed-association-park-v2.png")
            self.assertEqual(item.scenario_image.alt_text, "Adults after exercise in a park. Illustration only.")
            self.assertTrue((ROOT / "web/public" / item.scenario_image.path).is_file())
        medical_lesson = next(l for l in medical.lessons if l.concept_id == "observed-association")
        self.assertNotEqual(medical_lesson.scenario_image.path, "media/causality-m0/observed-association-park-v2.png")

    def test_feedback_matches_revised_questions_and_final_summary_rows(self):
        for profile in self.historical:
            with self.subTest(profile=profile):
                pack = self.revised(profile)
                resources = {r.resource_id: r.text for r in pack.resources}
                self.assertNotIn("drawing", resources["world-data-model.consequence.accepted"])
                self.assertNotIn("mastery", resources["not-causation.consequence.accepted"])
                self.assertNotIn("nine", resources["integrated.consequence.accepted"])
                self.assertIn("team recorded", resources["intervention.consequence.accepted"])
                final_seven = next(a for a in pack.activities if a.activity_id == "m0-final-quiz.07")
                self.assertIn("summary table", resources[final_seven.question_resource_id])
                self.assertTrue(all("Each row contains an attendance count" not in c.text
                                    for c in final_seven.choices))
                self.assertEqual(final_seven.workbench.prompt,
                                 resources[final_seven.question_resource_id].split("\n\nEarlier observed groups:")[0])
                final_nine = next(a for a in pack.activities if a.activity_id == "m0-final-quiz.09")
                self.assertTrue(resources[final_nine.question_resource_id].startswith("Suppose"))
                self.assertNotIn("simulator", resources[final_nine.question_resource_id])
                self.assertIn("hypothetical model", resources[final_nine.explanation_resource_id])
                hints = [resources[f"m0-final-quiz.{index:02d}.final.hint"] for index in range(1, 10)]
                self.assertEqual(len(set(hints)), 9)
                for activity in pack.activities[-9:]:
                    for choice in activity.choices:
                        # The final uses the choice evaluator, never the tutor.
                        self.assertEqual(evaluate_evidence(pack, ChoiceEvidence(
                            activity_id=activity.activity_id, option_id=choice.option_id,
                        )).accepted, choice.correct)

    def test_unknown_profile_does_not_mutate_the_pack(self):
        data = self.historical["general"].model_dump(mode="json")
        before = copy.deepcopy(data)
        with self.assertRaisesRegex(ValueError, "general or medical"):
            apply_learner_revision(data, "unknown")
        self.assertEqual(data, before)


if __name__ == "__main__":
    unittest.main()
