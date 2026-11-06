"""Illustrative records support assumptions tasks without becoming causal evidence."""

import unittest

from authoring.build_foundation_course import ROOT
from educagent_sdk import ClassificationEvidence, evaluate_classification, load_content_pack, validate_release


CASES = {
    ("general", "practice"): (
        ("Umbrella carried", "Pavement wet"),
        (("Yes", "Yes"), ("Yes", "Yes"), ("Yes", "No"), ("No", "Yes"), ("No", "No"), ("No", "No")),
        "one arrival per row", "rain"),
    ("general", "transfer"): (
        ("Help-page visits", "Bug reports"),
        (("1", "0"), ("2", "1"), ("3", "2"), ("4", "1"), ("5", "3"), ("6", "2")),
        "one user per row, same week", "confusion"),
    ("medical", "practice"): (
        ("Flagged for clinical review", "Symptom count at visit"),
        (("Yes", "5"), ("Yes", "3"), ("No", "4"), ("Yes", "2"), ("No", "1"), ("No", "0")),
        "one patient visit per row", "severity"),
    ("medical", "transfer"): (
        ("Used symptom tracker", "Nurse contacts"),
        (("Yes", "3"), ("Yes", "1"), ("No", "2"), ("Yes", "2"), ("No", "0"), ("No", "1")),
        "one patient per row, same week", "severity"),
}


class FoundationAssumptionsTablesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packs = {profile: load_content_pack(ROOT / f"content/foundation_{profile}_course_1_7_0.json")
                     for profile in ("general", "medical")}

    def test_each_short_question_exposes_six_rows_and_its_units_to_both_learner_and_tutor(self):
        for (profile, stage), (columns, rows, unit, proposed_cause) in CASES.items():
            with self.subTest(profile=profile, stage=stage):
                pack = self.packs[profile]
                activity = next(item for item in pack.activities if item.activity_id == f"data-vs-assumptions.{stage}")
                workbench = activity.workbench
                self.assertEqual(workbench.stage, "investigate")
                self.assertEqual(len(workbench.tables), 1)
                table = workbench.tables[0]
                self.assertEqual(table.columns, columns)
                self.assertEqual(table.rows, rows)
                self.assertEqual(len(table.rows), 6)
                self.assertTrue(all(len(row) == 2 for row in table.rows))
                self.assertTrue(table.label.startswith("Example records"))
                self.assertIn(unit, table.label)
                self.assertNotIn(proposed_cause, " ".join(table.columns).casefold())
                self.assertIn("Only", workbench.introduction)
                self.assertLessEqual(len(workbench.prompt.split()), 35)
                self.assertNotIn("\n", workbench.prompt)
                resources = {item.resource_id: item.text for item in pack.resources}
                question = resources[activity.question_resource_id]
                self.assertTrue(question.startswith(workbench.prompt + "\n\n" + table.label + ":\n"))
                self.assertIn(unit, question)
                self.assertIn(" | ".join(columns), question)
                self.assertIn("\n".join(" | ".join(row) for row in rows), question)
                self.assertEqual(validate_release(pack).unused_resource_ids, ())

    def test_all_original_options_keep_their_meaning_order_and_verdict_with_the_visible_data(self):
        for profile, pack in self.packs.items():
            previous = load_content_pack(ROOT / f"content/foundation_{profile}_course_1_6_0.json")
            for stage in ("practice", "transfer"):
                with self.subTest(profile=profile, stage=stage):
                    activity_id = f"data-vs-assumptions.{stage}"
                    activity = next(item for item in pack.activities if item.activity_id == activity_id)
                    old = next(item for item in previous.activities if item.activity_id == activity_id)
                    self.assertEqual(activity.choices, old.choices)
                    for choice in activity.choices:
                        verdict = evaluate_classification(pack, ClassificationEvidence(
                            activity_id=activity_id, classification_id=choice.option_id,
                            artifact_id=f"assumptions-table.{profile}.{choice.option_id}"))
                        self.assertEqual(verdict.accepted, choice.option_id == f"assumptions.{stage}.assumption")
                        self.assertEqual(verdict.consequence_resource_id, choice.consequence_resource_id)
                        self.assertEqual(verdict.misconception_id, choice.misconception_id)

    def test_examples_do_not_change_the_campus_world_or_imply_measuring_a_cause_proves_it(self):
        for profile, pack in self.packs.items():
            resources = {item.resource_id: item.text for item in pack.resources}
            explanation = resources["assumptions.explanation"]
            self.assertIn("Data describe recorded values and patterns.", explanation)
            self.assertIn("A causal assumption adds a claim", explanation)
            self.assertIn("Recording the proposed cause would not, by itself, establish that it causes both variables.", explanation)
            self.assertTrue(resources["assumptions.consequence.rejected"].startswith("Not yet."))
            previous = load_content_pack(ROOT / f"content/foundation_{profile}_course_1_6_0.json")
            self.assertEqual(pack.causal_scenes, previous.causal_scenes)
        general = self.packs["general"]
        activity = next(item for item in general.activities if item.activity_id == "data-vs-assumptions.practice")
        self.assertIn("another campus", activity.workbench.prompt)
        self.assertEqual(set(activity.workbench.tables[0].rows),
                         {("Yes", "Yes"), ("Yes", "No"), ("No", "Yes"), ("No", "No")})
