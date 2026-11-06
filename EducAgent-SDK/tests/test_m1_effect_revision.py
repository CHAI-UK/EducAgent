"""Editorial revisions preserve Effect assessment and deterministic experiments."""

import copy
import itertools
import json
import unittest
from pathlib import Path

from authoring.m1_effect_revision import apply_effect_revision
from educagent_sdk import ClassificationEvidence, ContentPack, evaluate_classification, load_content_pack, validate_release
from educagent_sdk.contracts import EffectExperimentConfig
from educagent_sdk.experiments import (
    CommitExperimentPrediction, RunExperiment, apply_experiment_action,
    initial_experiment_snapshot,
)


ROOT = Path(__file__).resolve().parents[1]


class EffectRevisionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.originals = {profile: load_content_pack(ROOT / f"content/m1_effect_course_{profile}.json")
                         for profile in ("general", "medical")}

    def revised(self, profile):
        data = self.originals[profile].model_dump(mode="json")
        apply_effect_revision(data, profile)
        return ContentPack.model_validate_json(json.dumps(data))

    def test_valid_pack_keeps_curriculum_scoring_ids_and_original_objects(self):
        for profile, original in self.originals.items():
            with self.subTest(profile=profile):
                frozen = original.model_dump_json()
                pack = self.revised(profile)
                self.assertEqual(pack.concepts, original.concepts)
                self.assertEqual(pack.claims, original.claims)
                self.assertEqual(pack.sources, original.sources)
                self.assertEqual(len(pack.activities), 16)
                self.assertEqual(len(pack.lessons), 4)
                self.assertEqual([a.activity_id for a in pack.activities], [a.activity_id for a in original.activities])
                self.assertEqual([r.resource_id for r in pack.resources], [r.resource_id for r in original.resources])
                for old, revised in zip(original.activities, pack.activities, strict=True):
                    self.assertEqual(old.activity_type, revised.activity_type)
                    self.assertEqual(old.is_transfer, revised.is_transfer)
                    self.assertEqual([c.model_dump(exclude={"text"}) for c in old.choices],
                                     [c.model_dump(exclude={"text"}) for c in revised.choices])
                    for index, choice in enumerate(revised.choices):
                        evidence = ClassificationEvidence(activity_id=revised.activity_id,
                            classification_id=choice.option_id, artifact_id=f"effect.revised.{profile}.{revised.activity_id}.{index}")
                        self.assertEqual(evaluate_classification(pack, evidence).accepted, choice.correct)
                self.assertEqual(validate_release(pack).unused_resource_ids, ())
                self.assertEqual(original.model_dump_json(), frozen)

    def test_first_read_is_compact_and_defines_terms_without_deleting_depth(self):
        for profile in self.originals:
            pack = self.revised(profile)
            resources = {r.resource_id: r.text for r in pack.resources}
            for original, lesson in zip(self.originals[profile].lessons, pack.lessons, strict=True):
                with self.subTest(profile=profile, concept=lesson.concept_id):
                    self.assertEqual(len(lesson.worked_steps), len(original.worked_steps))
                    self.assertEqual(lesson.review_status, "author_draft")
                    self.assertLessEqual(len(resources[lesson.definition_resource_id].split()), 60)
                    self.assertLessEqual(len(resources[lesson.hook_resource_id].split()), 50)
            adjustment = resources[next(l for l in pack.lessons if l.concept_id == "confounding-and-adjustment").definition_resource_id]
            self.assertIn("overlap (both treatments possible)", adjustment)
            self.assertIn("consistency (well-defined treatment versions)", adjustment)
            identification = resources[next(l for l in pack.lessons if l.concept_id == "identifiability-of-effects").definition_resource_id]
            self.assertTrue(all(term in identification for term in ("Identification", "Estimation", "Transport", "uncertainty")))
            detail = " ".join(resources[step.resource_id] for l in pack.lessons for step in l.worked_steps)
            self.assertIn("mediator", detail)
            self.assertIn("collider", detail)
            self.assertIn("15/60 = 25%", detail)

    def test_rejected_feedback_teaches_the_gap_without_copying_supported_option(self):
        for profile in self.originals:
            pack = self.revised(profile)
            resources = {r.resource_id: r.text for r in pack.resources}
            for activity in pack.activities:
                with self.subTest(profile=profile, activity=activity.activity_id):
                    supported = next(c for c in activity.choices if c.correct)
                    for choice in activity.choices:
                        if not choice.correct:
                            rejected = resources[choice.consequence_resource_id]
                            self.assertNotEqual(rejected, resources[activity.explanation_resource_id])
                            self.assertNotIn(supported.text, rejected)
                            self.assertFalse(rejected.startswith("Reconsider the distinction in this case."))
                            self.assertTrue(choice.hint_resource_ids)
                    self.assertTrue(all(c.text.endswith(".") for c in activity.choices))

    def test_tables_and_released_question_facts_remain_consistent(self):
        for profile in self.originals:
            original = self.originals[profile]
            pack = self.revised(profile)
            resources = {r.resource_id: r.text for r in pack.resources}
            for old, revised in zip(original.activities, pack.activities, strict=True):
                if revised.workbench is None:
                    continue
                self.assertEqual(revised.workbench.scenario_id, old.workbench.scenario_id)
                self.assertEqual(revised.workbench.stage, old.workbench.stage)
                self.assertTrue(resources[revised.question_resource_id].startswith(revised.workbench.prompt))
                for original_table, table in zip(old.workbench.tables, revised.workbench.tables, strict=True):
                    if revised.activity_id == "m1-effect-final.03":
                        self.assertEqual(table.table_id, "registry-assumptions")
                        self.assertEqual(table.columns, ("Item", "Given information"))
                        self.assertIn("separate observational", revised.workbench.introduction)
                        self.assertNotIn("82 / 100", resources[revised.question_resource_id])
                        self.assertNotIn("74 / 100", resources[revised.question_resource_id])
                        self.assertNotIn("Completed randomized assignment", resources[revised.question_resource_id])
                        self.assertTrue(all(not any(char.isdigit() for char in " ".join(row)) for row in table.rows))
                        self.assertIn(table.note, resources[revised.question_resource_id])
                        continue
                    self.assertEqual(table.columns, original_table.columns)
                    self.assertEqual(table.rows, original_table.rows)
                    self.assertEqual(table.table_id, original_table.table_id)
                    self.assertIn(table.note, resources[revised.question_resource_id])
                    if revised.experiment:
                        self.assertIn("not current experiment runs", table.note)
                        self.assertNotIn("target population is 50%", table.note)
                    for row in table.rows:
                        self.assertIn(" | ".join(row), resources[revised.question_resource_id])

    def test_numerical_units_and_inference_scope_are_preserved(self):
        for profile in self.originals:
            pack = self.revised(profile)
            resources = {r.resource_id: r.text for r in pack.resources}
            activities = {a.activity_id: a for a in pack.activities}
            self.assertIn("+6", resources[activities["average-treatment-effect.quiz"].explanation_resource_id])
            self.assertIn("14 percentage points", resources[activities["average-treatment-effect.challenge"].explanation_resource_id])
            self.assertIn("35%", resources[activities["average-treatment-effect.challenge"].explanation_resource_id])
            self.assertIn("about 10.8%", resources[activities["m1-effect-final.02"].explanation_resource_id])
            self.assertIn("sampling uncertainty", resources[activities["m1-effect-final.02"].explanation_resource_id])
            registry = resources[activities["m1-effect-final.03"].question_resource_id]
            self.assertIn("separate observational registry", registry)
            self.assertIn("consistent versions", registry)
            self.assertIn("new population", resources[activities["m1-effect-final.04"].question_resource_id])

    def test_supported_options_do_not_follow_a_dominant_length_rule(self):
        for profile in self.originals:
            with self.subTest(profile=profile):
                longest = shortest = 0
                for activity in self.revised(profile).activities:
                    supported = len(next(c.text for c in activity.choices if c.correct).split())
                    alternatives = [len(c.text.split()) for c in activity.choices if not c.correct]
                    longest += supported > max(alternatives)
                    shortest += supported < min(alternatives)
                self.assertLessEqual(longest, 8)
                self.assertLessEqual(shortest, 8)

    def test_all_experiment_configs_produce_identical_results_after_copy_revision(self):
        for profile in self.originals:
            original = self.originals[profile]
            pack = self.revised(profile)
            resources = {r.resource_id: r.text for r in pack.resources}
            for old, revised in zip(original.activities, pack.activities, strict=True):
                if revised.experiment is None:
                    continue
                before, after = old.experiment, revised.experiment
                self.assertEqual(before.model, after.model)
                self.assertEqual(before.initial_config, after.initial_config)
                self.assertEqual(before.experiment_id, after.experiment_id)
                self.assertEqual(before.model_version, after.model_version)
                self.assertEqual(before.min_distinct_runs, after.min_distinct_runs)
                instruction = resources[after.instructions_resource_id]
                self.assertTrue(all(word in instruction.lower() for word in ("prediction", "run", "compare")))
                self.assertTrue(all(label in instruction for label in (
                    "Save my prediction", "Save my next prediction", "Run experiment", "Record my comparison",
                )))
                for assignment, analysis, percentage in itertools.product(
                        ("self_selected", "randomized"), ("pooled", "standardized"), (0, 20, 50, 80, 100)):
                    config = EffectExperimentConfig(assignment=assignment, analysis=analysis, target_high_pct=percentage)
                    results = []
                    for spec in (before, after):
                        snapshot = initial_experiment_snapshot(spec)
                        snapshot = apply_experiment_action(spec, snapshot,
                            CommitExperimentPrediction(config=config, prediction="Compare this declared setup."), input_revision=0)
                        snapshot = apply_experiment_action(spec, snapshot, RunExperiment(), input_revision=snapshot.revision)
                        results.append(snapshot.result)
                    self.assertEqual(*results)

    def test_unknown_profile_is_rejected_without_mutation(self):
        data = self.originals["general"].model_dump(mode="json")
        frozen = copy.deepcopy(data)
        with self.assertRaisesRegex(ValueError, "general or medical"):
            apply_effect_revision(data, "unknown")
        self.assertEqual(data, frozen)


if __name__ == "__main__":
    unittest.main()
