"""Authored M1 content, arithmetic, evidence scope and complete offline routes."""

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from authoring import build_m1_courses as AUTHOR

from educagent_sdk import (
    ClassificationEvidence, close_attempt, complete_session,
    load_content_pack, record_classification_response, replay,
    start_attempt, start_session, validate_release,
    select_fixed_policy_move,
)
from educagent_sdk.lesson_samples import lesson_projection
from educagent_sdk.demo import DemoController
from educagent_sdk.events import record_experiment_action
from educagent_sdk.experiments import (
    CommitExperimentPrediction, ReflectOnExperiment, RunExperiment,
    apply_experiment_action, experiment_view, initial_experiment_snapshot,
)


ROOT = Path(__file__).resolve().parents[1]


def comparison_config(activity):
    """A controlled second setup matching the authored stage's specific task."""
    initial = activity.experiment.initial_config
    stage = int(activity.activity_id.rsplit(".", 1)[1])
    if initial.kind == "effect":
        changes = ({"analysis": "standardized"}, {"assignment": "self_selected"},
                   {"target_high_pct": 80}, {"assignment": "randomized"})[stage - 1]
    else:
        changes = ({"cue_accuracy_pct": 50}, {"flip_cue": True},
                   {"measurement_error_pct": 40} if activity.experiment.guide else {"cue_accuracy_pct": 20},
                   {"generator": "grounded"})[stage - 1]
    return initial.model_copy(update=changes)


def experiment_actions(activity):
    for config in (activity.experiment.initial_config, comparison_config(activity)):
        yield CommitExperimentPrediction(config=config, prediction="I predict a change; I will compare this with the computed result.")
        yield RunExperiment()
    yield ReflectOnExperiment(reflection="I compared both saved setups. The changed setting explains the computed difference or stability under this model; I revise my prediction and keep the conclusion scoped to those settings.")


def complete_experiment_events(events, pack, activity, attempt_id):
    if activity.experiment is None:
        return
    for index, action in enumerate(experiment_actions(activity)):
        snapshot = replay(events).experiment_snapshot
        record_experiment_action(events, pack, attempt_id=attempt_id,
                                 request_id=f"{activity.activity_id}.operation.{index}",
                                 experiment_id=activity.experiment.experiment_id,
                                 input_revision=snapshot.revision, action=action)


def run_model(spec, config):
    snapshot = initial_experiment_snapshot(spec)
    snapshot = apply_experiment_action(spec, snapshot,
        CommitExperimentPrediction(config=config, prediction="An unscored prediction before the result."), input_revision=0)
    return apply_experiment_action(spec, snapshot, RunExperiment(), input_revision=snapshot.revision).result


def metric(result, label):
    return next(item.value for item in result.metrics if item.label == label)


class M1CoursesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packs = {(task, profile): load_content_pack(ROOT / "content" / AUTHOR.course_filename(task, profile))
                     for task in ("effect", "shift") for profile in ("general", "medical")}

    def test_shipped_packs_match_the_authored_source_and_release_cleanly(self):
        for filename, authored in AUTHOR.build_all().items():
            with self.subTest(filename=filename):
                shipped = json.loads((ROOT / "content" / filename).read_text(encoding="utf-8"))
                self.assertEqual(shipped, authored)
        for (task, profile), pack in self.packs.items():
            with self.subTest(task=task, profile=profile):
                self.assertEqual(pack.pack_id, f"causality.m1.{task}.{profile}")
                self.assertEqual(pack.version, AUTHOR.VERSIONS[task])
                self.assertEqual(len(pack.activities), 16)
                self.assertEqual(len(pack.lessons), 4)
                self.assertEqual(validate_release(pack).unused_resource_ids, ())
                for concept in pack.concepts:
                    linked = {a.activity_id for a in pack.activities if a.concept_id == concept.concept_id}
                    self.assertEqual(set(concept.completion_activity_ids), linked)
                    self.assertEqual(len(linked), 4)
                    self.assertIn(concept.concept_id + ".quiz", linked)
                    self.assertIn(concept.concept_id + ".challenge", linked)
                    self.assertEqual(sum(a.workbench is not None and a.workbench.stage == "investigate"
                                         for a in pack.activities if a.activity_id in linked), 1)
                    self.assertEqual(sum(a.workbench is not None and a.workbench.stage == "capstone"
                                         for a in pack.activities if a.activity_id in linked), 1)
                    self.assertFalse(concept.m1_ready_activity_ids)
                self.assertTrue(all(not a.covered_concept_ids for a in pack.activities))

    def test_authoring_check_is_read_only_for_current_files(self):
        with patch.object(Path, "write_text") as write, redirect_stdout(io.StringIO()) as output:
            AUTHOR.main(["--check"])
        write.assert_not_called()
        self.assertEqual(output.getvalue().count("Checked content"), 4)

    def test_authoring_check_rejects_stale_files_without_repairing_them(self):
        with patch.object(Path, "read_text", return_value="stale"), patch.object(Path, "write_text") as write:
            with self.assertRaisesRegex(SystemExit, "Regenerate m1_effect_course_general_1_4_0.json"):
                AUTHOR.main(["--check"])
        write.assert_not_called()

    def test_both_profiles_keep_assessment_semantics_and_have_distinct_contexts(self):
        for task in ("effect", "shift"):
            general = self.packs[task, "general"]
            medical = self.packs[task, "medical"]
            self.assertEqual(general.concepts, medical.concepts)
            gr = {r.resource_id: r.text for r in general.resources}
            mr = {r.resource_id: r.text for r in medical.resources}
            self.assertNotEqual(general.lessons[0].scenario_image.path, medical.lessons[0].scenario_image.path)
            changed_questions = 0
            for a, b in zip(general.activities, medical.activities):
                self.assertEqual(a.activity_id, b.activity_id)
                self.assertEqual(a.is_transfer, b.is_transfer)
                self.assertEqual(tuple((c.option_id, c.correct) for c in a.choices),
                                 tuple((c.option_id, c.correct) for c in b.choices))
                if gr[a.question_resource_id] != mr[b.question_resource_id]:
                    changed_questions += 1
            # Shared arithmetic/design questions deliberately retain equal difficulty.
            self.assertGreaterEqual(changed_questions, 8)

    def test_each_topic_has_a_real_explanation_and_fresh_challenge(self):
        for (task, profile), pack in self.packs.items():
            resources = {r.resource_id: r for r in pack.resources}
            activities = {a.activity_id: a for a in pack.activities}
            for concept in pack.concepts:
                with self.subTest(task=task, profile=profile, concept=concept.concept_id):
                    lecture = lesson_projection(pack, concept.concept_id)
                    self.assertEqual(lecture.profile_id, profile)
                    self.assertEqual(len(lecture.worked_steps), 3)
                    self.assertTrue(all(step.text.strip() for step in lecture.worked_steps))
                    self.assertEqual(len({step.text for step in lecture.worked_steps}), 3)
                    self.assertTrue(lecture.sources)
                    self.assertTrue(lecture.definition and lecture.pitfall and lecture.takeaway)
                    quiz, challenge = (activities[concept.concept_id + suffix] for suffix in (".quiz", ".challenge"))
                    self.assertFalse(quiz.is_transfer)
                    self.assertTrue(challenge.is_transfer)
                    self.assertNotEqual(resources[quiz.question_resource_id].text,
                                        resources[challenge.question_resource_id].text)
                    visible = lecture.model_dump_json()
                    self.assertNotIn('"correct"', visible)
                    self.assertNotIn('"choices"', visible)
                    self.assertNotIn("review pending", visible.lower())

    def test_historical_1_3_editorial_copy_preserves_curriculum_scoring_and_models(self):
        for task, profile in self.packs:
            current = load_content_pack(ROOT / f"content/m1_{task}_course_{profile}_1_3_0.json")
            historical = load_content_pack(ROOT / f"content/m1_{task}_course_{profile}_1_2_0.json")
            with self.subTest(task=task, profile=profile):
                self.assertEqual(current.concepts, historical.concepts)
                before = {activity.activity_id: activity for activity in historical.activities}
                self.assertEqual(set(before), {activity.activity_id for activity in current.activities})
                for activity in current.activities:
                    original = before[activity.activity_id]
                    # The newer guide may reorder presentation, never scoring authority.
                    current_scoring = activity.model_dump(mode="json", exclude={"workbench", "experiment"})
                    original_scoring = original.model_dump(mode="json", exclude={"workbench", "experiment"})
                    for scoring in (current_scoring, original_scoring):
                        for choice in scoring["choices"]:
                            choice.pop("text")
                    self.assertEqual(current_scoring, original_scoring)
                    if activity.experiment is not None:
                        self.assertEqual(activity.experiment.model, original.experiment.model)
                        self.assertEqual(activity.experiment.initial_config, original.experiment.initial_config)
                        self.assertEqual(activity.experiment.min_distinct_runs, original.experiment.min_distinct_runs)
                        self.assertEqual(activity.experiment.model_version, original.experiment.model_version)

    def test_practical_reveals_are_stage_scoped_and_final_quiz_covers_each_concept(self):
        for (task, profile), pack in self.packs.items():
            practical = [a for a in pack.activities if a.workbench and a.workbench.stage == "investigate"]
            final = [a for a in pack.activities if a.workbench and a.workbench.stage == "capstone"]
            self.assertEqual(len(practical), 4)
            self.assertEqual(len(final), 4)
            self.assertEqual({a.concept_id for a in final}, {c.concept_id for c in pack.concepts})
            self.assertEqual(len({a.workbench.scenario_id for a in practical}), 1)
            self.assertEqual(len({a.workbench.scenario_id for a in final}), 1)
            self.assertNotEqual(practical[0].workbench.scenario_id, final[0].workbench.scenario_id)
            self.assertTrue(all(a.is_transfer for a in final))
            resources = {item.resource_id: item for item in pack.resources}
            initial_table = "programme-observed" if task == "effect" else "site-original"
            self.assertEqual(len({a.experiment.initial_config.model_dump_json() for a in practical}), 4)
            for activity in practical:
                self.assertEqual({t.table_id for t in activity.workbench.tables}, {initial_table})
                self.assertIsNotNone(activity.experiment)
                self.assertEqual(activity.experiment.min_distinct_runs, 2)
                instruction = resources[activity.experiment.instructions_resource_id]
                self.assertEqual(instruction.kind, "explanation")
                self.assertIn("predict", instruction.text.lower())
                self.assertIn("run", instruction.text.lower())
                self.assertIn("Record my comparison", instruction.text)
                initial = experiment_view(activity.experiment, initial_experiment_snapshot(activity.experiment), instruction.text)
                self.assertIsNone(initial["result"])
                self.assertEqual(initial["runs"], [])
                self.assertFalse(initial["can_submit_check"])
                for choice in activity.choices:
                    self.assertNotIn("+15", choice.text)
                    self.assertNotIn("64/100", choice.text)
                self.assertNotIn("a_low", json.dumps(initial))

    def test_effect_investigation_arithmetic_uses_one_population(self):
        for profile in ("general", "medical"):
            pack = self.packs["effect", profile]
            activity = next(a for a in pack.activities if a.activity_id == "m1-effect-investigation.03")
            self.assertAlmostEqual((18 + 48) / (20 + 80) - (64 + 8) / (80 + 20), -0.06)
            target_a = 0.5 * 18 / 20 + 0.5 * 48 / 80
            target_b = 0.5 * 64 / 80 + 0.5 * 8 / 20
            self.assertAlmostEqual(target_a, 0.75)
            self.assertAlmostEqual(target_b, 0.60)
            self.assertAlmostEqual(target_a - target_b, 0.15)
            spec = activity.experiment
            config = spec.initial_config.model_copy(update={"assignment": "self_selected", "target_high_pct": 50})
            original = run_model(spec, config)
            randomized = run_model(spec, config.model_copy(update={"assignment": "randomized"}))
            self.assertEqual(metric(original, "Source pooled A minus B"), -6)
            self.assertEqual(metric(original, "Target-standardized A minus B"), 15)
            self.assertEqual(metric(randomized, "Source pooled A minus B"), 15)
            for weight, expected in ((20, 12), (80, 18)):
                target = run_model(spec, config.model_copy(update={"target_high_pct": weight}))
                self.assertEqual(metric(target, "Target-standardized A minus B"), expected)
                self.assertEqual(target.tables[0], original.tables[0])
            final = next(a for a in pack.activities if a.activity_id == "m1-effect-final.02")
            self.assertAlmostEqual(82 / 100 - 74 / 100, 0.08)
            self.assertIn("+8 percentage points", next(c.text for c in final.choices if c.correct))

    def test_shift_teaches_generation_and_does_not_score_universal_causal_robustness_as_correct(self):
        for profile in ("general", "medical"):
            pack = self.packs["shift", profile]
            resources = {r.resource_id: r.text for r in pack.resources}
            generation = next(a for a in pack.activities if a.activity_id == "m1-shift-investigation.04")
            correct = next(c.text for c in generation.choices if c.correct)
            self.assertIn("faithful draft", correct)
            self.assertIn("measurement error", correct)
            self.assertIn("cannot supply missing context", correct)
            explanation = resources[generation.explanation_resource_id]
            self.assertIn("Reference accuracy checks predictions against the checking answer", explanation)
            self.assertIn("source fidelity checks drafts against the recorded source", explanation)
            self.assertIn("missing facts remain unknown", explanation)
            spec = generation.experiment
            config = spec.initial_config
            self.assertEqual(config.metadata_available_pct, 60)
            complete = run_model(spec, config)
            grounded = run_model(spec, config.model_copy(update={"generator": "grounded"}))
            self.assertEqual(metric(complete, "Full-report coverage"), 100)
            self.assertEqual(metric(complete, "Reports with unsupported additions / all cases"), 40)
            self.assertEqual(metric(grounded, "Full-report coverage"), 60)
            self.assertEqual(metric(grounded, "Source-supported / emitted reports"), 100)
            self.assertEqual(metric(grounded, "Reports with unsupported additions / all cases"), 0)
            self.assertEqual(metric(complete, "Reference prediction accuracy"), metric(grounded, "Reference prediction accuracy"))
            self.assertLess(metric(grounded, "Reference prediction accuracy"), 100)
            self.assertNotEqual(complete.cases, grounded.cases)
            final = next(a for a in pack.activities if a.activity_id == "m1-shift-final.03")
            self.assertIn("changed outcome process falls outside", next(c.text for c in final.choices if c.correct))
            self.assertIn("changes the process producing the outcome", resources[final.question_resource_id])

    def test_registry_uses_new_profile_packs_and_keeps_legacy_seed_files(self):
        registry = json.loads((ROOT / "content/modules.json").read_text(encoding="utf-8"))
        for module in registry["modules"]:
            if module["module_id"].startswith("m1_"):
                task = module["module_id"][3:]
                self.assertEqual(module["profile_pack_paths"], {
                    profile: f"content/{AUTHOR.course_filename(task, profile)}" for profile in ("general", "medical")})
        for path, pack_id in (("m1_effect_of_an_intervention.json", "causality.m1.effect.seed"),
                              ("m1_robust_prediction_or_generation.json", "causality.m1.shift.seed")):
            seed = load_content_pack(ROOT / "content" / path)
            self.assertEqual(seed.pack_id, pack_id)
            self.assertEqual(seed.version, "0.1.0")


class M1CourseTrajectoryTest(unittest.TestCase):
    def test_portal_controller_keeps_practical_and_final_quiz_after_all_topics(self):
        for task in ("effect", "shift"):
            for profile in ("general", "medical"):
                pack = load_content_pack(ROOT / "content" / AUTHOR.course_filename(task, profile))
                controller = DemoController(pack, profile_id=profile)
                state = controller.start(session_id=f"m1.{task}.{profile}.portal")
                for index, activity in enumerate(pack.activities):
                    self.assertEqual(state["activity_id"], activity.activity_id)
                    if activity.experiment is not None:
                        self.assertFalse(state["can_submit_response"])
                        for action_index, action in enumerate(experiment_actions(activity)):
                            state = controller.submit_experiment_action(
                                request_id=f"{activity.activity_id}.operation.{action_index}",
                                attempt_id=state["attempt_id"], experiment_id=activity.experiment.experiment_id,
                                input_revision=state["experiment"]["revision"], action=action)
                        self.assertTrue(state["can_submit_response"])
                    correct = next(c for c in activity.choices if c.correct)
                    controller.respond(request_id=f"portal.answer.{index}", option_id=correct.option_id)
                    state = controller.continue_activity(request_id=f"portal.continue.{index}")
                self.assertEqual(len(state["completed_activity_ids"]), 16)
                self.assertEqual(len(state["completed_concept_ids"]), 4)

    def test_all_four_routes_require_per_concept_practical_and_final_evidence(self):
        for task in ("effect", "shift"):
            for profile in ("general", "medical"):
                with self.subTest(task=task, profile=profile):
                    pack = load_content_pack(ROOT / "content" / AUTHOR.course_filename(task, profile))
                    events = []
                    start_session(events, pack, session_id=f"m1.{task}.{profile}.route")
                    for index, activity in enumerate(pack.activities):
                        attempt_id = f"attempt.{index}"
                        start_attempt(events, pack, attempt_id=attempt_id)
                        complete_experiment_events(events, pack, activity, attempt_id)
                        correct = next(c for c in activity.choices if c.correct)
                        request_id = f"answer.{index}"
                        recorded = record_classification_response(
                            events, pack, attempt_id=attempt_id, request_id=request_id,
                            evidence=ClassificationEvidence(activity_id=activity.activity_id,
                                                            classification_id=correct.option_id,
                                                            artifact_id=f"artifact.{index}"),
                            curriculum_requirements_met=True,
                        )
                        self.assertTrue(recorded.payload.evaluation.accepted)
                        advanced = select_fixed_policy_move(events, pack, request_id=request_id)
                        self.assertEqual(advanced.payload.move.strategy, "advance")
                        close_attempt(events, pack, attempt_id=attempt_id, status="completed")
                        completed = set(replay(events).completed_concept_ids)
                        if index < 12:
                            self.assertFalse(completed, "Topic practice or practical alone cannot skip the final quiz")
                        elif index < 15:
                            self.assertEqual(len(completed), index - 11)
                    complete_session(events, pack)
                    state = replay(events)
                    self.assertEqual(len(state.completed_activity_ids), 16)
                    self.assertEqual(state.completed_concept_ids, tuple(c.concept_id for c in pack.concepts))
                    self.assertEqual(replay(tuple(events)), state)


class M1TutorBoundaryTest(unittest.TestCase):
    def test_shipped_practical_rejects_scored_shortcuts_until_runs_and_reflection_exist(self):
        for task in ("effect", "shift"):
            for profile in ("general", "medical"):
                pack = load_content_pack(ROOT / "content" / AUTHOR.course_filename(task, profile))
                activity = next(a for a in pack.activities if a.experiment is not None)
                events = []
                start_session(events, pack, session_id=f"{task}.{profile}.experiment-gate",
                              preferred_activity_ids=(activity.activity_id,), route_scope="preferred")
                start_attempt(events, pack, attempt_id="experiment.attempt", activity_id=activity.activity_id)
                correct = next(c for c in activity.choices if c.correct)
                evidence = ClassificationEvidence(activity_id=activity.activity_id,
                                                   classification_id=correct.option_id,
                                                   artifact_id="experiment.check")

                def check():
                    return record_classification_response(
                        events, pack, attempt_id="experiment.attempt", request_id="experiment.answer",
                        evidence=evidence, curriculum_requirements_met=True)

                with self.assertRaisesRegex(ValueError, "experiment"):
                    check()
                for index, action in enumerate(experiment_actions(activity)):
                    record_experiment_action(
                        events, pack, attempt_id="experiment.attempt", request_id=f"experiment.operation.{index}",
                        experiment_id=activity.experiment.experiment_id,
                        input_revision=replay(events).experiment_snapshot.revision, action=action)
                    if index in (1, 3):
                        # One run is insufficient; two runs without reflection
                        # are also insufficient, regardless of the chosen answer.
                        with self.assertRaisesRegex(ValueError, "experiment"):
                            check()
                self.assertTrue(check().payload.evaluation.accepted)

    def test_wrong_final_answer_cannot_complete_or_advance(self):
        pack = load_content_pack(ROOT / "content" / AUTHOR.course_filename("shift", "medical"))
        activity = next(a for a in pack.activities if a.activity_id == "m1-shift-final.04")
        events = []
        start_session(events, pack, session_id="m1.final.rejection",
                      preferred_activity_ids=(activity.activity_id,), route_scope="preferred")
        start_attempt(events, pack, attempt_id="final.attempt", activity_id=activity.activity_id)
        incorrect = next(c for c in activity.choices if not c.correct)
        recorded = record_classification_response(
            events, pack, attempt_id="final.attempt", request_id="final.wrong",
            evidence=ClassificationEvidence(activity_id=activity.activity_id,
                                            classification_id=incorrect.option_id,
                                            artifact_id="final.artifact"),
            curriculum_requirements_met=True,
        )
        self.assertFalse(recorded.payload.evaluation.accepted)
        selected = select_fixed_policy_move(events, pack, request_id="final.wrong")
        self.assertNotEqual(selected.payload.move.strategy, "advance")
        self.assertFalse(replay(events).completed_concept_ids)
        self.assertFalse(replay(events).completed_activity_ids)


if __name__ == "__main__":
    unittest.main()
