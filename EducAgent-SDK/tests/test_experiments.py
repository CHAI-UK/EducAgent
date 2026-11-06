"""Real parameter changes, visible consequences and replayable M1 artifacts."""

import json
import unittest

from pydantic import ValidationError

from educagent_sdk.contracts import (
    EffectExperimentConfig, EffectExperimentModel, ExperimentWorkbench,
    ShiftExperimentConfig, ShiftExperimentModel,
)
from educagent_sdk.experiments import (
    CommitExperimentPrediction, ReflectOnExperiment, RunExperiment,
    apply_experiment_action, experiment_ready_for_assessment, experiment_view,
    initial_experiment_snapshot,
)


def effect_spec():
    return ExperimentWorkbench(
        experiment_id="test.effect", title="Compare programme designs",
        instructions_resource_id="test.effect.instructions",
        model=EffectExperimentModel(low_label="Lower baseline limitation", high_label="Higher baseline limitation",
            outcome_label="Declared six-week target", treatment_a_label="Programme A", treatment_b_label="Programme B"),
        initial_config=EffectExperimentConfig(), min_distinct_runs=2,
    )


def shift_spec():
    return ExperimentWorkbench(
        experiment_id="test.shift", title="Test the assistant under change",
        instructions_resource_id="test.shift.instructions",
        model=ShiftExperimentModel(source_positive="Observed flag present.", source_negative="Observed flag absent.",
                                  qualifier="The source records the acquisition view.",
                                  unsupported_detail="A view is filled in without source evidence."),
        initial_config=ShiftExperimentConfig(), min_distinct_runs=2,
    )


def run_setup(spec, snapshot, config):
    snapshot = apply_experiment_action(spec, snapshot,
        CommitExperimentPrediction(config=config, prediction="My prediction can be wrong; please run the declared model."),
        input_revision=snapshot.revision)
    return apply_experiment_action(spec, snapshot, RunExperiment(), input_revision=snapshot.revision)


def metric(result, name):
    return next(value.value for value in result.metrics if value.label == name)


class ExperimentWorldTest(unittest.TestCase):
    def test_effect_assignment_changes_source_but_target_weights_do_not_rewrite_records(self):
        spec = effect_spec()
        original = run_setup(spec, initial_experiment_snapshot(spec), EffectExperimentConfig())
        self.assertEqual(metric(original.result, "Source pooled A minus B"), -6)
        self.assertEqual(metric(original.result, "Target-standardized A minus B"), 15)
        randomized = run_setup(spec, original, EffectExperimentConfig(assignment="randomized"))
        self.assertEqual(metric(randomized.result, "Source pooled A minus B"), 15)
        self.assertEqual(metric(randomized.result, "Target-standardized A minus B"), 15)
        for high, expected in ((20, 12), (50, 15), (80, 18)):
            target = run_setup(spec, randomized, EffectExperimentConfig(target_high_pct=high))
            self.assertEqual(metric(target.result, "Source pooled A minus B"), -6)
            self.assertEqual(metric(target.result, "Target-standardized A minus B"), expected)
            self.assertEqual(target.result.tables[0], original.result.tables[0])

    def test_effect_analysis_changes_selected_contrast_not_the_model(self):
        spec = effect_spec()
        pooled = run_setup(spec, initial_experiment_snapshot(spec), EffectExperimentConfig())
        adjusted = run_setup(spec, pooled, EffectExperimentConfig(analysis="standardized"))
        self.assertEqual(metric(pooled.result, "Selected analysis contrast"), -6)
        self.assertEqual(metric(adjusted.result, "Selected analysis contrast"), 15)
        self.assertEqual(pooled.result.tables, adjusted.result.tables)
        self.assertNotEqual(pooled.result.bars, adjusted.result.bars)

    def test_shift_can_break_cue_stability_and_then_content_stability(self):
        spec = shift_spec()
        cue = run_setup(spec, initial_experiment_snapshot(spec), ShiftExperimentConfig())
        self.assertEqual(metric(cue.result, "Reference prediction accuracy"), 90)
        moved = run_setup(spec, cue, ShiftExperimentConfig(cue_accuracy_pct=10))
        self.assertEqual(metric(moved.result, "Reference prediction accuracy"), 10)
        content = run_setup(spec, moved, ShiftExperimentConfig(predictor="content", cue_accuracy_pct=10))
        self.assertEqual(metric(content.result, "Reference prediction accuracy"), 90)
        noisy = run_setup(spec, content, ShiftExperimentConfig(predictor="content", measurement_error_pct=40))
        self.assertEqual(metric(noisy.result, "Reference prediction accuracy"), 60)

    def test_cue_edit_changes_prediction_without_changing_reference_or_measurement(self):
        spec = shift_spec()
        before = run_setup(spec, initial_experiment_snapshot(spec), ShiftExperimentConfig())
        after = run_setup(spec, before, ShiftExperimentConfig(flip_cue=True))
        for left, right in zip(before.result.cases, after.result.cases):
            self.assertEqual(left.target, right.target)
            self.assertEqual(left.measurement, right.measurement)
            self.assertEqual(left.source_text, right.source_text)
            self.assertEqual(left.prediction, 1 - right.prediction)
        self.assertEqual(metric(after.result, "Reference prediction accuracy"), 10)

    def test_generation_changes_real_output_and_reports_coverage_separately(self):
        spec = shift_spec()
        complete = run_setup(spec, initial_experiment_snapshot(spec),
                            ShiftExperimentConfig(predictor="content", measurement_error_pct=40, metadata_available_pct=60))
        grounded = run_setup(spec, complete,
                            ShiftExperimentConfig(predictor="content", measurement_error_pct=40, metadata_available_pct=60, generator="grounded"))
        self.assertEqual(metric(complete.result, "Full-report coverage"), 100)
        self.assertEqual(metric(complete.result, "Reports with unsupported additions / all cases"), 40)
        self.assertEqual(metric(complete.result, "Complete source-supported reports / all cases"), 60)
        self.assertEqual(metric(grounded.result, "Full-report coverage"), 60)
        self.assertEqual(metric(grounded.result, "Source-supported / emitted reports"), 100)
        self.assertEqual(metric(grounded.result, "Reports with unsupported additions / all cases"), 0)
        self.assertEqual(metric(grounded.result, "Reference prediction accuracy"), 60)
        self.assertTrue(any(not case.emitted for case in grounded.result.cases))
        self.assertNotEqual(complete.result.cases, grounded.result.cases)

    def test_empty_generation_denominator_is_not_presented_as_perfect_fidelity(self):
        spec = shift_spec()
        empty = run_setup(spec, initial_experiment_snapshot(spec),
                          ShiftExperimentConfig(generator="grounded", metadata_available_pct=0))
        self.assertEqual(metric(empty.result, "Full-report coverage"), 0)
        fidelity = next(x for x in empty.result.metrics if x.label == "Source-supported / emitted reports")
        self.assertIn("Not defined", fidelity.display_value)


class ExperimentTransitionTest(unittest.TestCase):
    def test_prediction_distinct_runs_and_reflection_are_actual_artifacts_not_correctness(self):
        spec = effect_spec()
        snapshot = initial_experiment_snapshot(spec)
        with self.assertRaisesRegex(ValueError, "prediction"):
            apply_experiment_action(spec, snapshot, RunExperiment(), input_revision=0)
        snapshot = run_setup(spec, snapshot, EffectExperimentConfig())
        repeated = run_setup(spec, snapshot, EffectExperimentConfig())
        self.assertEqual(snapshot.result, repeated.result)
        with self.assertRaisesRegex(ValueError, "different settings"):
            apply_experiment_action(spec, repeated, ReflectOnExperiment(reflection="I looked at the result."), input_revision=repeated.revision)
        second = run_setup(spec, repeated, EffectExperimentConfig(assignment="randomized"))
        self.assertFalse(experiment_ready_for_assessment(spec, second))
        reflected = apply_experiment_action(spec, second,
            ReflectOnExperiment(reflection="My original prediction was wrong. Changing assignment changed the source contrast."),
            input_revision=second.revision)
        self.assertTrue(experiment_ready_for_assessment(spec, reflected))
        # Editing invalidates the old prediction's result and reflected readiness.
        edited = apply_experiment_action(spec, reflected,
            CommitExperimentPrediction(config=EffectExperimentConfig(target_high_pct=80), prediction="I predict a larger target average."),
            input_revision=reflected.revision)
        self.assertIsNone(edited.result)
        self.assertIsNone(edited.reflection)
        self.assertFalse(experiment_ready_for_assessment(spec, edited))
        self.assertEqual(edited.runs, reflected.runs)

    def test_tutor_and_renderer_projection_do_not_contain_unrun_results_or_model_coefficients(self):
        spec = effect_spec()
        initial = initial_experiment_snapshot(spec)
        view = experiment_view(spec, initial, "Predict, run and compare.")
        self.assertIsNone(view["result"])
        self.assertEqual(view["runs"], [])
        self.assertNotIn("a_low", json.dumps(view))
        run = run_setup(spec, initial, EffectExperimentConfig())
        changed = apply_experiment_action(spec, run,
            CommitExperimentPrediction(config=EffectExperimentConfig(target_high_pct=80), prediction="A new prediction."),
            input_revision=run.revision)
        visible = experiment_view(spec, changed, "Predict, run and compare.")
        self.assertIsNone(visible["result"])
        self.assertEqual(visible["runs"][0]["config"]["target_high_pct"], 50)
        self.assertNotIn("+18.0", json.dumps(visible))

    def test_stale_cross_model_and_invalid_typed_inputs_cannot_run(self):
        spec = effect_spec()
        snapshot = initial_experiment_snapshot(spec)
        with self.assertRaisesRegex(ValueError, "stale"):
            apply_experiment_action(spec, snapshot, RunExperiment(), input_revision=1)
        with self.assertRaisesRegex(ValueError, "another model"):
            apply_experiment_action(spec, snapshot,
                CommitExperimentPrediction(config=ShiftExperimentConfig(), prediction="A guess."), input_revision=0)
        for payload in ({"target_high_pct": 51}, {"target_high_pct": "50"}, {"assignment": "invented"}):
            with self.assertRaises(ValidationError):
                EffectExperimentConfig(**payload)
        with self.assertRaises(ValidationError):
            CommitExperimentPrediction(config=EffectExperimentConfig(), prediction=" ")


if __name__ == "__main__":
    unittest.main()
