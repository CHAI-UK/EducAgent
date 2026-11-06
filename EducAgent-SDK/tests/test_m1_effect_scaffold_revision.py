"""Guided Effect practice preserves the historical experiment and scoring."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import unittest

from authoring.build_m1_courses import build_all, course_filename
from authoring.m1_effect_scaffold_revision import CONCEPT_IDS, apply_effect_scaffold_revision
from educagent_sdk import ClassificationEvidence, ContentPack, evaluate_classification, load_content_pack, validate_release
from tests.test_m1_shift_revision import metric, run_model


ROOT = Path(__file__).resolve().parents[1]
HISTORICAL = {
    "general": "62f5154b1af036a2a4e7e02823025239fad0ee74c62c86b3da92e81e0f93cfe1",
    "medical": "0d8f4f73fab5763ad72d99a8d8714274db10c1db8dc6a4e69b4e838656c7b313",
}
EDITORIAL_CHOICE_TEXT = {
    "defining-an-intervention.quiz.supported": (
        "Randomly assign the specified reminder or no reminder, then measure the same next-month outcome.",
        "Randomly assign this reminder or no reminder, then measure the same next-month outcome.",
    ),
    "defining-an-intervention.challenge.supported": (
        "It targets being offered support versus no offer, on attendance in this study population.",
        "It targets the effect of offering support versus no offer on attendance in this study population.",
    ),
    "m1-effect-investigation.03.supported": (
        "It compares average outcomes under A and B for this target, not each person's benefit.",
        "It compares average outcomes under A and B for this target population; it does not give each person's benefit.",
    ),
    "average-treatment-effect.challenge.alternative-2": (
        "The comparison identifies which 14 people were caused to succeed by programme A.",
        "The comparison shows which 14 people succeeded because they received programme A.",
    ),
    "confounding-and-adjustment.quiz.supported": (
        "Compare within-baseline-group outcomes using the same target-population weights for both treatments.",
        "Compare outcomes within each baseline group, using the same target-population weights for both treatments.",
    ),
    "identifiability-of-effects.quiz.supported": (
        "It can sharpen the association estimate without resolving the intervention effect.",
        "It can estimate the association more precisely while leaving the intervention effect unresolved.",
    ),
    "identifiability-of-effects.challenge.alternative-2": (
        "Only more rows are needed; the changed population and treatment cannot affect the causal argument.",
        "Only more records are needed; the changed population and treatment cannot affect the causal argument.",
    ),
    "m1-effect-investigation.01.supported": (
        "Pooled averages retain different baseline mixtures; standardization uses common weights for the target population.",
        "Pooled averages use each group's own baseline mix; standardization uses the same target-population weights for both programmes.",
    ),
    "m1-effect-investigation.02.supported": (
        "It changes programme allocation while leaving the model's baseline and outcome mechanisms fixed.",
        "It changes how programmes are allocated while keeping the model's baseline and outcome mechanisms fixed.",
    ),
    "m1-effect-investigation.04.supported": (
        "It depends on the declared adjustment, overlap, consistency and stable within-group rates, not agreement alone.",
        "The interpretation relies on the declared adjustment assumptions, overlap, consistency and stable within-group rates; matching results alone are not enough.",
    ),
    "m1-effect-final.03.supported": (
        "Use the eligible population's same travel-difficulty weights for each reminder value under those assumptions.",
        "Use the eligible population's travel-difficulty weights for both reminder groups under those assumptions.",
    ),
}


class EffectScaffoldRevisionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.originals = {profile: load_content_pack(ROOT / f"content/m1_effect_course_{profile}_1_2_0.json")
                         for profile in HISTORICAL}

    def test_historical_bytes_and_every_curriculum_and_score_contract_are_preserved(self):
        for profile, original in self.originals.items():
            path = ROOT / f"content/m1_effect_course_{profile}_1_2_0.json"
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), HISTORICAL[profile])
            # This historical assertion freezes the 1.3 editorial release;
            # later assessment versions have separate answer meanings and tests.
            current = load_content_pack(ROOT / f"content/m1_effect_course_{profile}_1_3_0.json")
            self.assertEqual(current.version, "1.3.0")
            for field in ("schema_version", "pack_id", "title", "concepts", "sources", "claims", "lessons"):
                self.assertEqual(getattr(original, field), getattr(current, field))
            self.assertEqual(tuple(a.activity_id for a in original.activities), tuple(a.activity_id for a in current.activities))
            for old, new in zip(original.activities, current.activities, strict=True):
                with self.subTest(profile=profile, activity=new.activity_id):
                    for field in ("concept_id", "activity_type", "requires_revision", "is_transfer", "covered_concept_ids"):
                        self.assertEqual(getattr(old, field), getattr(new, field))
                    for before, after in zip(old.choices, new.choices, strict=True):
                        if after.option_id in EDITORIAL_CHOICE_TEXT:
                            old_text, new_text = EDITORIAL_CHOICE_TEXT[after.option_id]
                            self.assertEqual(before.text, old_text)
                            self.assertEqual(after.text, new_text)
                            self.assertEqual(before.correct, after.correct)
                            self.assertEqual(before.model_dump(exclude={"text"}),
                                             after.model_dump(exclude={"text"}))
                        else:
                            self.assertEqual(before, after)
                    for choice in new.choices:
                        evidence = ClassificationEvidence(activity_id=new.activity_id,
                            classification_id=choice.option_id, artifact_id="s43.option.truth")
                        self.assertEqual(evaluate_classification(original, evidence).accepted,
                                         evaluate_classification(current, evidence).accepted)
                    if new.experiment:
                        for field in ("experiment_id", "model", "model_version", "initial_config", "min_distinct_runs"):
                            self.assertEqual(getattr(old.experiment, field), getattr(new.experiment, field))

    def test_authored_guides_are_fresh_releasable_and_focus_only_the_declared_operation(self):
        generated = build_all()
        for profile in HISTORICAL:
            filename = course_filename("effect", profile)
            shipped = json.loads((ROOT / "content" / filename).read_text(encoding="utf-8"))
            self.assertEqual(generated[filename], shipped)
            self.assertNotRegex(json.dumps(shipped), re.compile(r"\b([A-Za-z]+)\s+\1\b", re.I))
            pack = load_content_pack(ROOT / "content" / filename)
            self.assertEqual(validate_release(pack).unused_resource_ids, ())
            specs = [a.experiment for a in pack.activities if a.experiment]
            self.assertEqual([s.guide.section for s in specs], ["intervention"] * 4)
            self.assertEqual([s.guide.parameter_id for s in specs], ["analysis", "assignment", "target_high_pct", "assignment"])
            for spec in specs:
                guide = spec.guide
                self.assertIn("six-week", guide.story)
                self.assertIn("rehabilitation" if profile == "medical" else "college", guide.story)
                result = run_model(spec, spec.initial_config)
                self.assertTrue(all(any(m.label == item.metric_label for m in result.metrics) for item in guide.metrics))
                self.assertTrue(all(value.strip() for value in (guide.story, guide.goal,
                    guide.parameter_description, guide.prediction_prompt, guide.comparison_prompt)))

    def test_each_authored_one_control_change_keeps_exact_historical_results(self):
        changes = ({"analysis": "standardized"}, {"assignment": "self_selected"},
                   {"target_high_pct": 80}, {"assignment": "randomized"})
        for profile, old_pack in self.originals.items():
            current = load_content_pack(ROOT / "content" / course_filename("effect", profile))
            originals = [a.experiment for a in old_pack.activities if a.experiment]
            specs = [a.experiment for a in current.activities if a.experiment]
            for index, (old, new, change) in enumerate(zip(originals, specs, changes, strict=True)):
                with self.subTest(profile=profile, stage=index + 1):
                    self.assertEqual(set(change), {new.guide.parameter_id})
                    base = new.initial_config
                    for config in (base, base.model_copy(update=change)):
                        self.assertEqual(run_model(old, config), run_model(new, config))
            self.assertEqual(metric(run_model(specs[0], specs[0].initial_config), "Selected analysis contrast"), -6)
            self.assertEqual(metric(run_model(specs[0], specs[0].initial_config.model_copy(update=changes[0])), "Selected analysis contrast"), 15)
            self.assertEqual(metric(run_model(specs[2], specs[2].initial_config), "Target-standardized A minus B"), 12)
            self.assertEqual(metric(run_model(specs[2], specs[2].initial_config.model_copy(update=changes[2])), "Target-standardized A minus B"), 18)
            self.assertEqual(metric(run_model(specs[3], specs[3].initial_config), "Target-standardized A minus B"), 18)
            self.assertEqual(metric(run_model(specs[3], specs[3].initial_config.model_copy(update=changes[3])), "Target-standardized A minus B"), 18)

    def test_copy_is_idempotent_and_rejects_other_curricula_or_profiles(self):
        for profile, original in self.originals.items():
            data = original.model_dump(mode="json")
            frozen = deepcopy(data)
            revised = apply_effect_scaffold_revision(data, profile)
            self.assertEqual(data, frozen)
            self.assertEqual(apply_effect_scaffold_revision(revised, profile), revised)
            self.assertEqual(tuple(c["concept_id"] for c in revised["concepts"]), CONCEPT_IDS)
        data = self.originals["general"].model_dump(mode="json")
        with self.assertRaisesRegex(ValueError, "general or medical"):
            apply_effect_scaffold_revision(data, "other")
        with self.assertRaisesRegex(ValueError, "matching Effect profile"):
            apply_effect_scaffold_revision(data, "medical")
        invalid = deepcopy(data)
        invalid["concepts"].reverse()
        with self.assertRaisesRegex(ValueError, "four-concept"):
            apply_effect_scaffold_revision(invalid, "general")
        invalid = deepcopy(data)
        invalid["activities"].pop()
        with self.assertRaisesRegex(ValueError, "sixteen activities"):
            apply_effect_scaffold_revision(invalid, "general")


if __name__ == "__main__":
    unittest.main()
