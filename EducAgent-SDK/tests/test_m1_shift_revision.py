"""The plain-language Shift revision preserves scoring and its teaching model."""

from copy import deepcopy
import json
from pathlib import Path
import unittest

from authoring.m1_shift_revision import CONCEPT_IDS, apply_shift_revision
from educagent_sdk import validate_release
from educagent_sdk.contracts import ContentPack
from educagent_sdk.experiments import (
    CommitExperimentPrediction, RunExperiment, apply_experiment_action,
    initial_experiment_snapshot,
)


ROOT = Path(__file__).resolve().parents[1]


def frozen_pack(profile):
    """Use the unchanged 1.1 input, independent of the current builder version."""
    return json.loads((ROOT / "content" / f"m1_shift_course_{profile}.json").read_text(encoding="utf-8"))


def as_pack(data):
    return ContentPack.model_validate_json(json.dumps(data))


def run_model(spec, config):
    snapshot = initial_experiment_snapshot(spec)
    snapshot = apply_experiment_action(spec, snapshot,
        CommitExperimentPrediction(config=config, prediction="I will compare this prediction with the computed result."),
        input_revision=snapshot.revision)
    return apply_experiment_action(spec, snapshot, RunExperiment(), input_revision=snapshot.revision).result


def metric(result, label):
    return next(item.value for item in result.metrics if item.label == label)


class ShiftRevisionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.originals = {profile: frozen_pack(profile) for profile in ("general", "medical")}
        cls.revisions = {profile: apply_shift_revision(data, profile) for profile, data in cls.originals.items()}

    def test_input_is_unchanged_and_repeat_application_is_idempotent(self):
        for profile, source in self.originals.items():
            with self.subTest(profile=profile):
                self.assertEqual(source, frozen_pack(profile))
                self.assertIsNot(source, self.revisions[profile])
                self.assertEqual(apply_shift_revision(self.revisions[profile], profile), self.revisions[profile])
                separate = apply_shift_revision(source, profile)
                separate["resources"][0]["text"] = "A caller can edit the returned copy."
                self.assertEqual(source, frozen_pack(profile))

    def test_invalid_profile_or_curriculum_cannot_silently_rewrite_another_pack(self):
        source = self.originals["general"]
        with self.assertRaisesRegex(ValueError, "general or medical"):
            apply_shift_revision(source, "other")
        with self.assertRaisesRegex(ValueError, "matching shift profile"):
            apply_shift_revision(source, "medical")
        invalid = deepcopy(source)
        invalid["concepts"].reverse()
        with self.assertRaisesRegex(ValueError, "four-concept"):
            apply_shift_revision(invalid, "general")
        invalid = deepcopy(source)
        invalid["activities"].pop()
        with self.assertRaisesRegex(ValueError, "sixteen activities"):
            apply_shift_revision(invalid, "general")

    def test_only_authored_copy_changes_not_curriculum_provenance_or_scoring_contracts(self):
        for profile, original in self.originals.items():
            revised = self.revisions[profile]
            with self.subTest(profile=profile):
                self.assertEqual(tuple(c["concept_id"] for c in revised["concepts"]), CONCEPT_IDS)
                for key in ("schema_version", "pack_id", "version", "title", "concepts", "sources", "claims"):
                    self.assertEqual(original[key], revised[key])
                self.assertEqual(len(revised["activities"]), 16)
                self.assertEqual(sum(a.get("workbench") is None for a in revised["activities"]), 8)
                self.assertEqual(sum(a.get("experiment") is not None for a in revised["activities"]), 4)
                self.assertEqual(sum(a.get("workbench", {}).get("stage") == "capstone" for a in revised["activities"]), 4)
                before = deepcopy(original)
                after = deepcopy(revised)
                for data in (before, after):
                    for resource in data["resources"]:
                        resource["text"] = "COPY"
                    for lesson in data["lessons"]:
                        lesson["title"] = lesson["challenge_title"] = "COPY"
                        for step in lesson["worked_steps"]:
                            step["title"] = "COPY"
                    for activity in data["activities"]:
                        for choice in activity["choices"]:
                            choice["text"] = "COPY"
                        if activity.get("workbench"):
                            for field in ("title", "introduction", "prompt"):
                                activity["workbench"][field] = "COPY"
                        if activity.get("experiment"):
                            activity["experiment"]["title"] = "COPY"
                self.assertEqual(before, after)

    def test_revised_packs_release_with_all_resources_grounded(self):
        for profile, data in self.revisions.items():
            with self.subTest(profile=profile):
                pack = as_pack(data)
                self.assertEqual(validate_release(pack).unused_resource_ids, ())
                resources = {r.resource_id: r.text for r in pack.resources}
                for activity in pack.activities:
                    if activity.workbench:
                        question = resources[activity.question_resource_id]
                        for table in activity.workbench.tables:
                            self.assertIn(table.label, question)
                            self.assertTrue(all(" | ".join(row) in question for row in table.rows))

    def test_first_terms_and_compact_lessons_keep_scientific_boundaries(self):
        for profile, data in self.revisions.items():
            resources = {r["resource_id"]: r["text"] for r in data["resources"]}
            definitions = [resources[lesson["definition_resource_id"]] for lesson in data["lessons"]]
            with self.subTest(profile=profile):
                self.assertTrue(all(len(text.split()) <= 55 for text in definitions))
                self.assertIn("Prediction estimates", definitions[0])
                self.assertIn("generation produces text", definitions[0])
                self.assertIn("Distribution shift is", definitions[0])
                self.assertIn("A cue is", definitions[1])
                self.assertIn("A spurious cue", definitions[1])
                self.assertIn("A causal feature is proposed to affect the outcome", definitions[1])
                self.assertIn("not a reliability guarantee", definitions[1])
                self.assertIn("An invariant relationship", definitions[2])
                self.assertIn("does not prove a cause", definitions[2])
                self.assertIn("process, measurements", definitions[2])
                self.assertIn("not proof that the source is true", definitions[3])
                self.assertIn("Coverage is the share", definitions[3])
                all_text = " ".join(resources.values())
                self.assertIn("Support means the feature values", all_text)
                self.assertIn("Abstention means withholding", all_text)
                self.assertIn("not a real clinical or inspection review", all_text)
                self.assertIn("not a feature established to cause the target", all_text)
                self.assertIn("does not directly test the outcome relationship for fixed feature values", all_text)
                self.assertIn("not defined, rather than automatically perfect", all_text)

    def test_rejections_guide_retry_without_copying_accepted_answers(self):
        for profile, data in self.revisions.items():
            resources = {r["resource_id"]: r["text"] for r in data["resources"]}
            for activity in data["activities"]:
                correct = next(c for c in activity["choices"] if c["correct"])
                accepted = resources[correct["consequence_resource_id"]]
                for wrong in (c for c in activity["choices"] if not c["correct"]):
                    with self.subTest(profile=profile, activity=activity["activity_id"], option=wrong["option_id"]):
                        rejected = resources[wrong["consequence_resource_id"]]
                        self.assertNotEqual(rejected, accepted)
                        self.assertNotIn(correct["text"], rejected)
                        self.assertNotIn(accepted, rejected)
                        self.assertTrue(wrong["hint_resource_ids"])
                        self.assertTrue(all(resources[rid].strip() for rid in wrong["hint_resource_ids"]))

    def test_correct_choice_length_does_not_give_a_universal_answer_key(self):
        for profile, data in self.revisions.items():
            strict_longest = strict_shortest = 0
            for activity in data["activities"]:
                length = len(next(c["text"] for c in activity["choices"] if c["correct"]).split())
                alternatives = [len(c["text"].split()) for c in activity["choices"] if not c["correct"]]
                strict_longest += length > max(alternatives)
                strict_shortest += length < min(alternatives)
            with self.subTest(profile=profile, strict_longest=strict_longest, strict_shortest=strict_shortest):
                self.assertLessEqual(strict_longest, 10)
                self.assertLessEqual(strict_shortest, 10)
                self.assertGreater(strict_longest, 0)
                self.assertGreater(strict_shortest, 0)

    def test_practice_instructions_describe_replayable_controls_not_passive_tables(self):
        for profile, data in self.revisions.items():
            resources = {r["resource_id"]: r["text"] for r in data["resources"]}
            for activity in (a for a in data["activities"] if a.get("experiment")):
                with self.subTest(profile=profile, activity=activity["activity_id"]):
                    instruction = resources[activity["experiment"]["instructions_resource_id"]]
                    for label in ("Save my prediction", "Save my next prediction", "Run experiment", "Record my comparison"):
                        self.assertIn(label, instruction)
                    self.assertIn("Compare", instruction)
                    self.assertIn("Keep", instruction)
                    self.assertNotIn("Commit my prediction", instruction)

    def test_original_and_revised_models_produce_identical_results_at_each_authored_change(self):
        for profile, source in self.originals.items():
            original = as_pack(source)
            revised = as_pack(self.revisions[profile])
            for left, right in zip(original.activities, revised.activities, strict=True):
                if left.experiment is None:
                    continue
                stage = int(left.activity_id.rsplit(".", 1)[1])
                changes = ({"cue_accuracy_pct": 50}, {"flip_cue": True},
                           {"cue_accuracy_pct": 20}, {"generator": "grounded"})[stage - 1]
                configs = [left.experiment.initial_config,
                           left.experiment.initial_config.model_copy(update=changes),
                           left.experiment.initial_config.model_copy(update={"predictor": "content", "measurement_error_pct": 40})]
                for config in configs:
                    with self.subTest(profile=profile, activity=left.activity_id, config=config):
                        self.assertEqual(run_model(left.experiment, config), run_model(right.experiment, config))

    def test_numeric_consequences_keep_cue_content_and_report_fidelity_separate(self):
        for profile, data in self.revisions.items():
            pack = as_pack(data)
            activities = {a.activity_id: a for a in pack.activities}
            specs = [activities[f"m1-shift-investigation.{i:02d}"].experiment for i in range(1, 5)]
            with self.subTest(profile=profile):
                cue = run_model(specs[0], specs[0].initial_config)
                moved = run_model(specs[0], specs[0].initial_config.model_copy(update={"cue_accuracy_pct": 50}))
                self.assertEqual(metric(cue, "Reference prediction accuracy"), 90)
                self.assertEqual(metric(moved, "Reference prediction accuracy"), 50)
                baseline = run_model(specs[1], specs[1].initial_config)
                edited = run_model(specs[1], specs[1].initial_config.model_copy(update={"flip_cue": True}))
                self.assertEqual(metric(edited, "Reference prediction accuracy"), 10)
                for left, right in zip(baseline.cases, edited.cases, strict=True):
                    self.assertEqual((left.target, left.measurement, left.source_text),
                                     (right.target, right.measurement, right.source_text))
                    self.assertEqual(left.prediction, 1 - right.prediction)
                stable = run_model(specs[2], specs[2].initial_config.model_copy(update={"cue_accuracy_pct": 20}))
                noisy = run_model(specs[2], specs[2].initial_config.model_copy(update={"measurement_error_pct": 40}))
                self.assertEqual(metric(stable, "Reference prediction accuracy"), 90)
                self.assertEqual(metric(noisy, "Reference prediction accuracy"), 60)
                complete = run_model(specs[3], specs[3].initial_config)
                grounded = run_model(specs[3], specs[3].initial_config.model_copy(update={"generator": "grounded"}))
                self.assertEqual(metric(complete, "Reference prediction accuracy"), 70)
                self.assertEqual(metric(grounded, "Reference prediction accuracy"), 70)
                self.assertEqual(metric(complete, "Full-report coverage"), 100)
                self.assertEqual(metric(complete, "Complete source-supported reports / all cases"), 60)
                self.assertEqual(metric(complete, "Reports with unsupported additions / all cases"), 40)
                self.assertEqual(metric(grounded, "Full-report coverage"), 60)
                self.assertEqual(metric(grounded, "Source-supported / emitted reports"), 100)
                self.assertEqual(metric(grounded, "Reports with unsupported additions / all cases"), 0)
                empty = run_model(specs[3], specs[3].initial_config.model_copy(update={"generator": "grounded", "metadata_available_pct": 0}))
                self.assertEqual(metric(empty, "Full-report coverage"), 0)
                fidelity = next(m for m in empty.metrics if m.label == "Source-supported / emitted reports")
                self.assertIn("Not defined", fidelity.display_value)
                final = activities["m1-shift-final.01"].workbench.tables[0]
                flattened = "".join("".join(row) for row in final.rows).replace(" ", "")
                for value in ("91/100", "72/100", "96/100", "78/100", "1/100", "12/100"):
                    self.assertIn(value, flattened)


if __name__ == "__main__":
    unittest.main()
