"""Story-first Shift wording preserves the curriculum and deterministic truth."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import unittest

from authoring.build_m1_courses import build_all, course_filename
from authoring.m1_shift_revision import CONCEPT_IDS
from authoring.m1_shift_scaffold_revision import apply_shift_scaffold_revision
from educagent_sdk import ClassificationEvidence, evaluate_classification, load_content_pack, validate_release
from educagent_sdk.contracts import ContentPack
from tests.test_m1_shift_revision import metric, run_model


ROOT = Path(__file__).resolve().parents[1]
FROZEN_HASHES = {
    "m1_effect_course_general_1_2_0.json": "62f5154b1af036a2a4e7e02823025239fad0ee74c62c86b3da92e81e0f93cfe1",
    "m1_effect_course_medical_1_2_0.json": "0d8f4f73fab5763ad72d99a8d8714274db10c1db8dc6a4e69b4e838656c7b313",
    "m1_shift_course_general_1_2_0.json": "dc112f6c81b43225dd310b2ad0e186cb0bf897796962b1042446ac8458a980d3",
    "m1_shift_course_medical_1_2_0.json": "3be89e2d0ffa9f83c8674a997e4050f74f1e3c735dd3fdc4133f066f5025bd7c",
}


class ShiftScaffoldRevisionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.originals = {
            profile: json.loads((ROOT / f"content/m1_shift_course_{profile}_1_2_0.json").read_text(encoding="utf-8"))
            for profile in ("general", "medical")
        }
        cls.revisions = {
            profile: apply_shift_scaffold_revision(data, profile)
            for profile, data in cls.originals.items()
        }

    def test_historical_files_remain_byte_identical_and_registry_only_selects_new_shift(self):
        for filename, digest in FROZEN_HASHES.items():
            with self.subTest(filename=filename):
                self.assertEqual(hashlib.sha256((ROOT / "content" / filename).read_bytes()).hexdigest(), digest)
        entries = json.loads((ROOT / "content/modules.json").read_text(encoding="utf-8"))["modules"]
        versions = {"causality_m0": "1.8.0", "m1_effect": "1.4.0", "m1_shift": "1.4.0"}
        for entry in entries:
            for path in entry["profile_pack_paths"].values():
                self.assertEqual(load_content_pack(ROOT / path).version, versions[entry["module_id"]])

    def test_copy_is_idempotent_and_invalid_curricula_are_rejected(self):
        for profile, original in self.originals.items():
            revision = self.revisions[profile]
            self.assertEqual(apply_shift_scaffold_revision(revision, profile), revision)
            self.assertIsNot(revision, original)
            revision_copy = deepcopy(revision)
            revision_copy["resources"][0]["text"] = "Another caller's copy."
            self.assertNotEqual(revision_copy, original)
        with self.assertRaisesRegex(ValueError, "general or medical"):
            apply_shift_scaffold_revision(self.originals["general"], "other")
        with self.assertRaisesRegex(ValueError, "matching shift profile"):
            apply_shift_scaffold_revision(self.originals["general"], "medical")
        invalid = deepcopy(self.originals["general"])
        invalid["concepts"].reverse()
        with self.assertRaisesRegex(ValueError, "four-concept"):
            apply_shift_scaffold_revision(invalid, "general")
        invalid = deepcopy(self.originals["general"])
        invalid["activities"].pop()
        with self.assertRaisesRegex(ValueError, "sixteen activities"):
            apply_shift_scaffold_revision(invalid, "general")

    def test_curriculum_answer_identity_and_every_option_truth_are_unchanged(self):
        for profile, original in self.originals.items():
            revised = self.revisions[profile]
            before = ContentPack.model_validate_json(json.dumps(original))
            after = ContentPack.model_validate_json(json.dumps(revised))
            self.assertEqual(before.concepts, after.concepts)
            self.assertEqual(before.claims, after.claims)
            self.assertEqual(before.sources, after.sources)
            self.assertEqual(tuple(c.concept_id for c in after.concepts), CONCEPT_IDS)
            original_activities = {a.activity_id: a for a in before.activities}
            self.assertEqual(set(original_activities), {a.activity_id for a in after.activities})
            for new in after.activities:
                old = original_activities[new.activity_id]
                with self.subTest(profile=profile, activity=new.activity_id):
                    for field in ("concept_id", "activity_type", "requires_revision", "is_transfer", "covered_concept_ids", "causal_scene_id"):
                        self.assertEqual(getattr(old, field), getattr(new, field))
                    self.assertEqual(tuple((c.option_id, c.correct) for c in old.choices),
                                     tuple((c.option_id, c.correct) for c in new.choices))
                    self.assertEqual(old.workbench is None, new.workbench is None)
                    if old.workbench:
                        self.assertEqual((old.workbench.stage, old.workbench.scenario_id),
                                         (new.workbench.stage, new.workbench.scenario_id))
                    for choice in new.choices:
                        evidence = ClassificationEvidence(activity_id=new.activity_id,
                            classification_id=choice.option_id, artifact_id="s42.option.truth")
                        self.assertEqual(evaluate_classification(before, evidence).accepted,
                                         evaluate_classification(after, evidence).accepted)

    def test_built_files_release_cleanly_and_preserve_models_initial_configs_and_results(self):
        authored = build_all()
        for profile, original in self.originals.items():
            filename = course_filename("shift", profile)
            self.assertEqual(authored[filename], json.loads((ROOT / "content" / filename).read_text(encoding="utf-8")))
            pack = load_content_pack(ROOT / "content" / filename)
            historical = load_content_pack(ROOT / f"content/m1_shift_course_{profile}_1_3_0.json")
            self.assertEqual(historical.version, "1.3.0")
            self.assertEqual(validate_release(pack).unused_resource_ids, ())
            old_pack = ContentPack.model_validate_json(json.dumps(original))
            original_activities = {a.activity_id: a for a in old_pack.activities}
            for new in pack.activities:
                old = original_activities[new.activity_id]
                if old.experiment is None:
                    continue
                for field in ("experiment_id", "model", "model_version", "initial_config", "min_distinct_runs"):
                    self.assertEqual(getattr(old.experiment, field), getattr(new.experiment, field))
                stage = int(new.activity_id.rsplit(".", 1)[1])
                change = ({"cue_accuracy_pct": 50}, {"flip_cue": True},
                          {"measurement_error_pct": 40}, {"generator": "grounded"})[stage - 1]
                for config in (old.experiment.initial_config, old.experiment.initial_config.model_copy(update=change)):
                    self.assertEqual(run_model(old.experiment, config), run_model(new.experiment, config))

    def test_normal_route_finishes_prediction_practice_before_introducing_generation(self):
        expected = (
            "distribution-shift.quiz", "distribution-shift.challenge",
            "causal-vs-spurious-features.quiz", "causal-vs-spurious-features.challenge",
            "invariance-across-environments.quiz", "invariance-across-environments.challenge",
            "m1-shift-investigation.01", "m1-shift-investigation.02", "m1-shift-investigation.03",
            "when-predictions-can-still-fail.quiz", "when-predictions-can-still-fail.challenge",
            "m1-shift-investigation.04",
            "m1-shift-final.01", "m1-shift-final.02", "m1-shift-final.03", "m1-shift-final.04",
        )
        for profile, revised in self.revisions.items():
            with self.subTest(profile=profile):
                self.assertEqual(tuple(a["activity_id"] for a in revised["activities"]), expected)

    def test_final_table_views_keep_generation_evidence_separate_without_shared_mutation(self):
        authored = build_all()
        for profile, revised in self.revisions.items():
            for source, data in (("parsed historical input", revised),
                                 ("generator shared-table input", authored[course_filename("shift", profile)])):
                with self.subTest(profile=profile, source=source):
                    activities = {a["activity_id"]: a for a in data["activities"]}
                    for index in range(1, 4):
                        table = activities[f"m1-shift-final.{index:02d}"]["workbench"]["tables"][0]
                        self.assertEqual(table["rows"], [["Event prediction accuracy", "91 / 100", "72 / 100"]])
                    final = activities["m1-shift-final.04"]["workbench"]
                    table = final["tables"][0]
                    self.assertEqual(table["rows"], [["Drafts with unsupported factual additions", "1 / 100", "12 / 100"]])
                    self.assertNotIn("prediction", table["label"].lower())
                    self.assertEqual(table["columns"], ["Report check", "Original site", "New site"])

    def test_guides_focus_one_relevant_control_and_keep_generation_last(self):
        for profile, revised in self.revisions.items():
            pack = ContentPack.model_validate_json(json.dumps(revised))
            practices = [a for a in pack.activities if a.experiment]
            self.assertEqual([a.experiment.guide.parameter_id for a in practices],
                             ["cue_accuracy_pct", "flip_cue", "measurement_error_pct", "generator"])
            self.assertEqual([a.experiment.guide.section for a in practices],
                             ["prediction", "prediction", "prediction", "generation"])
            for index, activity in enumerate(practices):
                guide = activity.experiment.guide
                self.assertIn("hospital" if profile == "medical" else "warehouse", guide.story)
                for text in (guide.story, guide.goal, guide.parameter_description,
                             guide.prediction_prompt, guide.comparison_prompt):
                    self.assertTrue(text.strip())
                result = run_model(activity.experiment, activity.experiment.initial_config)
                self.assertTrue(all(any(m.label == item.metric_label for m in result.metrics) for item in guide.metrics))
                if index < 3:
                    self.assertEqual([item.metric_label for item in guide.metrics], ["Reference prediction accuracy"])
                    self.assertNotIn("generation", guide.story.lower())
                else:
                    self.assertEqual({item.metric_label for item in guide.metrics},
                        {"Full-report coverage", "Reports with unsupported additions / all cases"})
            initial = practices[2].experiment.initial_config
            self.assertEqual(initial.predictor, "content")
            self.assertEqual(metric(run_model(practices[2].experiment, initial), "Reference prediction accuracy"), 90)
            self.assertEqual(metric(run_model(practices[2].experiment, initial.model_copy(update={"measurement_error_pct": 40})), "Reference prediction accuracy"), 60)

    def test_prediction_topics_and_first_three_final_questions_do_not_mix_in_generation(self):
        for profile, revised in self.revisions.items():
            resources = {r["resource_id"]: r["text"] for r in revised["resources"]}
            for lesson in revised["lessons"][:3]:
                text = " ".join(resources[lesson[key]] for key in (
                    "hook_resource_id", "definition_resource_id", "pitfall_resource_id", "takeaway_resource_id"))
                text += " ".join(resources[s["resource_id"]] for s in lesson["worked_steps"])
                self.assertNotIn("generation", text.lower())
                self.assertTrue(all(not step["title"][0].isdigit() for step in lesson["worked_steps"]))
            for activity in revised["activities"]:
                if activity["concept_id"] not in CONCEPT_IDS[:3]:
                    continue
                visible = resources[activity["question_resource_id"]] + " ".join(c["text"] for c in activity["choices"])
                self.assertNotIn("generation", visible.lower())
                self.assertNotIn("draft", visible.lower())
                self.assertNotIn("source-fidel", visible.lower())
            final = next(a for a in revised["activities"] if a["activity_id"] == "m1-shift-final.04")
            self.assertIn("report generation", resources[final["question_resource_id"]])

    def test_short_options_and_wrong_feedback_do_not_give_the_correct_wording(self):
        for profile, revised in self.revisions.items():
            self.assertNotRegex(json.dumps(revised), re.compile(r"\b([A-Za-z]+)\s+\1\b", re.I))
            resources = {r["resource_id"]: r["text"] for r in revised["resources"]}
            for activity in revised["activities"]:
                correct = next(c for c in activity["choices"] if c["correct"])
                accepted = resources[correct["consequence_resource_id"]]
                for choice in activity["choices"]:
                    with self.subTest(profile=profile, activity=activity["activity_id"], option=choice["option_id"]):
                        self.assertLessEqual(len(choice["text"].split()), 19)
                        if not choice["correct"]:
                            rejected = resources[choice["consequence_resource_id"]]
                            self.assertNotEqual(rejected, accepted)
                            self.assertNotIn(accepted, rejected)
                            self.assertNotIn(correct["text"], rejected)


if __name__ == "__main__":
    unittest.main()
