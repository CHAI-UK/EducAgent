"""Full-course context adaptation preserves assessment and historical General scope."""

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from pydantic import ValidationError
from pydantic_ai.models import override_allow_model_requests
from pydantic_ai.models.test import TestModel

from educagent_sdk import (
    ClassificationEvidence, ContentPack, ReleaseValidationError, build_tutor_deps,
    close_attempt, complete_session, evaluate_classification, load_content_pack,
    record_classification_response, replay, run_tutor_turn, start_attempt,
    start_session, validate_release,
)
from educagent_sdk.causal_scene import (
    OpenRecords, RunIntervention, SubmitGraph, SubmitPrediction, SubmitRevision,
    dialogue_job_for_scene_focus,
)
from educagent_sdk.contracts import CausalSceneEdge
from educagent_sdk.demo import DemoController
from educagent_sdk.events import record_causal_scene_action, record_causal_scene_evidence
from educagent_sdk.foundation_profiles import CONCEPT_CLAIM_IDS, load_foundation_profiles
from educagent_sdk.lesson_samples import lesson_lecture_context, lesson_projection, lesson_view


ROOT = Path(__file__).resolve().parents[1]


class FoundationProfilesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = load_content_pack(ROOT / "content/causality_m0_full.json")
        resources = {item.resource_id: item for item in cls.base.resources}
        activities = {item.activity_id: item for item in cls.base.activities}
        cls.source = {"version": "1.0.0", "profiles": {}}
        for profile_id in ("general", "medical"):
            lectures = []
            for concept in cls.base.concepts:
                explanation = resources[activities[concept.completion_activity_ids[0]].explanation_resource_id].text
                lectures.append({
                    "concept_id": concept.concept_id,
                    "title": f"{profile_id} {concept.concept_id}",
                    "hook": f"Synthetic {profile_id} worked example for {concept.concept_id}.",
                    "worked_steps": [{"title": "Inspect the example", "text": explanation}],
                    "definition": explanation,
                    "pitfall": "Separate an observed record from an assumed causal explanation.",
                    "takeaway": concept.objective,
                })
            cls.source["profiles"][profile_id] = {"lectures": lectures}
        cls.source["profiles"]["medical"]["resources"] = {
            item.question_resource_id: "Synthetic medical teaching case: " + resources[item.question_resource_id].text
            for item in cls.base.activities if item.activity_type != "causal_scene"
        }
        cls.samples = cls.compile_source(cls.source)

    @classmethod
    def compile_source(cls, data):
        with patch.object(Path, "read_text", return_value=json.dumps(data)):
            return load_foundation_profiles(cls.base, "profiles.json")

    def changed(self, mutate):
        data = json.loads(json.dumps(self.source))
        mutate(data)
        return self.compile_source(data)

    def test_profiles_keep_all_objectives_activity_ids_order_and_scoring_fields(self):
        original = self.base.model_dump_json()
        samples = self.compile_source(self.source)
        self.assertEqual(self.base.model_dump_json(), original)
        self.assertEqual(samples["general"].pack_id, "causality.m0.general.teaching")
        self.assertEqual(samples["medical"].pack_id, "causality.m0.medical")
        self.assertEqual(self.base.version, "1.1.0")
        for profile_id, pack in samples.items():
            with self.subTest(profile=profile_id):
                self.assertEqual(pack.version, "1.0.0")
                self.assertEqual(pack.concepts, self.base.concepts)
                self.assertEqual(len(pack.activities), 19)
                self.assertEqual(len(pack.lessons), 9)
                self.assertIsNone(pack.lesson)
                self.assertEqual(pack.causal_scenes, self.base.causal_scenes)
                self.assertEqual(tuple(item.concept_id for item in pack.lessons), tuple(CONCEPT_CLAIM_IDS))
                self.assertTrue(all(item.profile_id == profile_id for item in pack.lessons))
                for original_activity, activity in zip(self.base.activities, pack.activities):
                    self.assertEqual(activity.model_dump(exclude={"choices", "scenario_image"}),
                                     original_activity.model_dump(exclude={"choices", "scenario_image"}))
                    self.assertEqual(tuple(choice.model_dump(exclude={"text"}) for choice in activity.choices),
                                     tuple(choice.model_dump(exclude={"text"}) for choice in original_activity.choices))
                self.assertEqual(validate_release(pack).unused_resource_ids, ())
        self.assertEqual(samples["general"].activities, self.base.activities)
        original_resources = {item.resource_id: item for item in samples["general"].resources}
        for item in self.base.resources:
            self.assertEqual(original_resources[item.resource_id], item)

    def test_general_teaching_companion_keeps_original_runtime_pack_and_events(self):
        controller = DemoController(self.base, profile_id="general", teaching_pack=self.samples["general"])
        state = controller.start(session_id="foundation.general")
        self.assertEqual(state["activity_id"], self.base.activities[0].activity_id)
        self.assertIs(controller.pack, self.base)
        self.assertEqual(controller.events[0].pack_id, self.base.pack_id)
        self.assertEqual(controller.events[0].pack_version, self.base.version)

    def test_current_concept_projection_has_no_other_lessons_or_assessment_keys(self):
        for profile_id, pack in self.samples.items():
            for concept in self.base.concepts:
                with self.subTest(profile=profile_id, concept=concept.concept_id):
                    view = lesson_projection(pack, concept.concept_id)
                    self.assertEqual(view.concept_id, concept.concept_id)
                    self.assertEqual(view.objective, concept.objective)
                    self.assertEqual(view.profile_id, profile_id)
                    self.assertEqual(view.review_status, "author_draft")
                    self.assertIsNone(view.worked_graph)
                    self.assertIsNone(view.scenario_image)
                    lecture = json.dumps(lesson_view(pack, concept.concept_id))
                    self.assertNotIn('"choices"', lecture)
                    self.assertNotIn('"correct"', lecture)
                    self.assertNotIn('"feedback"', lecture)
                    for other in pack.lessons:
                        if other.concept_id != concept.concept_id:
                            self.assertNotIn(other.title, lecture)
                    context = "\n".join(lesson_lecture_context(pack, concept.concept_id))
                    self.assertIn(view.hook, context)
                    for activity in pack.activities:
                        for choice in activity.choices:
                            self.assertNotIn(choice.option_id, lecture)
                            self.assertNotIn(choice.consequence_resource_id, context)
            self.assertIsNone(lesson_projection(pack, "unknown-concept"))

    def test_only_declared_association_scene_can_be_a_lesson_challenge(self):
        pack = self.samples["medical"]
        lesson = next(item for item in pack.lessons if item.concept_id == "association-is-not-causation")
        activity = next(item for item in pack.activities if item.activity_id == lesson.challenge_activity_id)
        self.assertEqual(activity.activity_type, "causal_scene")
        self.assertEqual(activity.causal_scene_id, self.base.causal_scenes[0].scene_id)
        original_scene_resources = {item.resource_id: item for item in self.base.resources
                                    if item.resource_id.startswith("scene.rain-umbrella.")
                                    or item.resource_id == activity.question_resource_id}
        compiled_resources = {item.resource_id: item for item in pack.resources}
        self.assertTrue(all(compiled_resources[key] == value for key, value in original_scene_resources.items()))
        data = pack.model_dump(mode="json")
        data["lessons"][0]["challenge_activity_id"] = lesson.challenge_activity_id
        with self.assertRaises(ValidationError):
            ContentPack.model_validate_json(json.dumps(data))

    def test_source_rejects_unknown_fields_missing_topics_and_assessment_scope_changes(self):
        cases = (
            lambda data: data.__setitem__("correct", True),
            lambda data: data["profiles"].pop("medical"),
            lambda data: data["profiles"]["general"]["lectures"].pop(),
            lambda data: data["profiles"]["medical"]["lectures"].reverse(),
            lambda data: data["profiles"]["general"].__setitem__("resources", {"variables.question.practice": "Changed"}),
            lambda data: data["profiles"]["medical"]["resources"].__setitem__("scene.rain-umbrella.hook", "Changed"),
            lambda data: data["profiles"]["medical"]["resources"].__setitem__("not-causation.question.transfer", "Changed"),
            lambda data: data["profiles"]["medical"]["resources"].pop("integrated.question"),
            lambda data: data["profiles"]["medical"].__setitem__("choice_text", {"new-choice": "Changed"}),
            lambda data: data["profiles"]["medical"].__setitem__("activity_images", {"association-is-not-causation.transfer": None}),
        )
        for mutate in cases:
            with self.subTest(mutation=mutate):
                with self.assertRaises(ValueError):
                    self.changed(mutate)

    def test_per_concept_source_refs_and_optional_fork_are_actually_projected(self):
        def add_graph(data):
            lecture = data["profiles"]["medical"]["lectures"][2]
            lecture["source_refs"] = [{
                "source_id": "peters-janzing-scholkopf-2017",
                "locator": "Section 1.3, Figure 1.2 and Principle 1.1",
            }]
            lecture["worked_graph"] = {
                "label": "Possible explanation only",
                "nodes": [
                    {"node_id": "severity", "label": "Severity"},
                    {"node_id": "receipt", "label": "Treatment receipt"},
                    {"node_id": "recovery", "label": "Recovery"},
                ],
                "edges": [{"from": "severity", "to": "receipt"}, {"from": "severity", "to": "recovery"}],
                "note": "This is a partial hypothesis; the treatment effect remains unresolved.",
            }
        pack = self.changed(add_graph)["medical"]
        view = lesson_projection(pack, "association-is-not-causation")
        self.assertEqual(len(view.worked_graph.edges), 2)
        self.assertIn("Section 1.3, Figure 1.2 and Principle 1.1", {item.locator for item in view.sources})
        self.assertIn(view.worked_graph.note, lesson_lecture_context(pack, view.concept_id))
        with self.assertRaisesRegex(ValueError, "unknown base source"):
            self.changed(lambda data: data["profiles"]["medical"]["lectures"][0].__setitem__(
                "source_refs", [{"source_id": "unknown", "locator": "Chapter 1"}]))

    def test_lesson_release_checks_cover_every_normal_route_lecture(self):
        data = self.samples["medical"].model_dump(mode="json")
        data["lessons"][7]["definition_resource_id"] = "missing-definition"
        pack = ContentPack.model_validate_json(json.dumps(data))
        with self.assertRaises(ReleaseValidationError) as caught:
            lesson_projection(pack, "variables-and-values")
        self.assertTrue(any(issue.path == "/lessons/7/definition_resource_id"
                            and issue.code == "missing-resource" for issue in caught.exception.report.issues))

    def test_shipped_authoring_source_compiles_all_eighteen_lectures_and_medical_questions(self):
        path = ROOT / "content/foundation_profiles.json"
        source = json.loads(path.read_text(encoding="utf-8"))
        packs = load_foundation_profiles(self.base, path)
        question_ids = {item.question_resource_id for item in self.base.activities
                        if item.activity_type != "causal_scene"}
        self.assertEqual(len(question_ids), 18)
        self.assertEqual(set(source["profiles"]["medical"]["resources"]), question_ids)
        for profile_id, pack in packs.items():
            with self.subTest(profile=profile_id):
                self.assertEqual(len(pack.lessons), 9)
                self.assertEqual(pack.concepts, self.base.concepts)
                self.assertEqual(pack.causal_scenes, self.base.causal_scenes)
                self.assertEqual(validate_release(pack).unused_resource_ids, ())
                for concept in self.base.concepts:
                    view = lesson_projection(pack, concept.concept_id)
                    self.assertEqual(view.objective, concept.objective)
                    self.assertEqual(len(view.worked_steps), 3)
                    self.assertTrue(view.sources)
                    self.assertEqual(view.review_status, "author_draft")
                    visible = view.model_dump_json()
                    self.assertNotIn('"correct"', visible)
                    self.assertNotIn('"choices"', visible)
        medical_resources = {item.resource_id: item for item in packs["medical"].resources}
        for resource_id, text in source["profiles"]["medical"]["resources"].items():
            self.assertEqual(medical_resources[resource_id].text, text)
            self.assertIn("fictional", text.lower())
        self.assertEqual(packs["general"].activities, self.base.activities)

    def test_shipped_medical_images_are_explicit_context_and_resolve_to_public_assets(self):
        path = ROOT / "content/foundation_profiles.json"
        packs = load_foundation_profiles(self.base, path)
        medical = packs["medical"]
        images = [item.scenario_image for item in medical.lessons if item.scenario_image is not None]
        images.extend(item.scenario_image for item in medical.activities if item.scenario_image is not None)
        for image in images:
            with self.subTest(image=image.path):
                self.assertTrue((ROOT / "web/public" / image.path).is_file())
                self.assertTrue(image.alt_text)
        activities = {item.activity_id: item for item in medical.activities}
        self.assertIsNone(activities["basic-dag-language.practice"].scenario_image)
        self.assertIsNone(activities["probabilistic-effects.practice"].scenario_image)
        self.assertEqual(activities["association-is-not-causation.transfer"].scenario_image,
                         self.base.activities[5].scenario_image)


class MedicalFoundationTrajectoryTest(unittest.IsolatedAsyncioTestCase):
    async def test_shipped_medical_nineteen_activity_route_completes_with_original_evaluator_and_replay(self):
        base = load_content_pack(ROOT / "content/causality_m0_full.json")
        pack = load_foundation_profiles(base, ROOT / "content/foundation_profiles.json")["medical"]
        events = []
        start_session(events, pack, session_id="medical.full-route")

        async def choose_first(request_id):
            deps = build_tutor_deps(events, pack, request_id=request_id)
            output = {"candidate_id": deps.candidates[0].candidate_id}
            if deps.legal_interaction_focus_ids:
                focus = deps.legal_interaction_focus_ids[0]
                output.update(interaction_focus_id=focus, dialogue_job=dialogue_job_for_scene_focus(focus))
            with override_allow_model_requests(False):
                return await run_tutor_turn(events, pack, request_id=request_id,
                                            model=TestModel(custom_output_args=output))

        for ordinal, activity in enumerate(pack.activities, start=1):
            attempt_id = f"medical.attempt.{ordinal}"
            start_attempt(events, pack, attempt_id=attempt_id)
            if activity.activity_type == "causal_scene":
                scene = pack.causal_scenes[0]
                actions = (
                    ("records", 0, OpenRecords()),
                    ("model", 1, SubmitGraph(edges=(CausalSceneEdge(
                        parent_id="umbrella-carried", child_id="pavement-wet",
                    ),))),
                    ("prediction", 2, SubmitPrediction(prediction_id="wet-pavement-less-often")),
                    ("intervention", 3, RunIntervention(intervention_action_id=scene.intervention.action_id)),
                    ("revision", 4, SubmitRevision(edges=scene.assessment.accepted_edges)),
                )
                for suffix, revision, action in actions:
                    request_id = f"medical.scene.{ordinal}.{suffix}"
                    record_causal_scene_action(events, pack, attempt_id=attempt_id,
                                               request_id=request_id, input_revision=revision, action=action)
                    await choose_first(request_id)
                request_id = f"medical.scene.{ordinal}.evidence"
                response = record_causal_scene_evidence(events, pack, attempt_id=attempt_id,
                                                       request_id=request_id)
                self.assertTrue(response.payload.evaluation.accepted)
                advanced = await choose_first(request_id)
            else:
                correct = next(choice for choice in activity.choices if choice.correct)
                evidence_args = {"activity_id": activity.activity_id, "artifact_id": f"medical.artifact.{ordinal}"}
                if activity.requires_revision:
                    incorrect = next(choice for choice in activity.choices if not choice.correct)
                    wrong = ClassificationEvidence(**evidence_args, classification_id=incorrect.option_id)
                    self.assertEqual(evaluate_classification(pack, wrong), evaluate_classification(base, wrong))
                    request_id = f"medical.answer.{ordinal}.original"
                    original = record_classification_response(
                        events, pack, attempt_id=attempt_id, request_id=request_id,
                        evidence=wrong, curriculum_requirements_met=True,
                    )
                    self.assertFalse(original.payload.evaluation.accepted)
                    reflected = await choose_first(request_id)
                    self.assertEqual(reflected.event.payload.move.strategy, "reflect")
                    evidence_args["revises_evidence_event_id"] = original.event_id
                evidence = ClassificationEvidence(**evidence_args, classification_id=correct.option_id)
                self.assertEqual(evaluate_classification(pack, evidence), evaluate_classification(base, evidence))
                request_id = f"medical.answer.{ordinal}.accepted"
                response = record_classification_response(
                    events, pack, attempt_id=attempt_id, request_id=request_id,
                    evidence=evidence, curriculum_requirements_met=True,
                )
                self.assertTrue(response.payload.evaluation.accepted)
                advanced = await choose_first(request_id)
            self.assertEqual(advanced.event.payload.move.strategy, "advance")
            close_attempt(events, pack, attempt_id=attempt_id, status="completed")

        completion = complete_session(events, pack)
        state = replay(events)
        self.assertEqual(state.pack_id, "causality.m0.medical")
        self.assertEqual(state.pack_version, "1.0.0")
        self.assertEqual(state.completed_activity_ids, tuple(item.activity_id for item in pack.activities))
        self.assertEqual(state.completed_concept_ids, tuple(item.concept_id for item in base.concepts))
        self.assertEqual(state.m1_ready_concept_ids, ())
        self.assertEqual(completion.payload.completed_concept_ids, state.completed_concept_ids)
        self.assertEqual(replay(tuple(events)), state)


if __name__ == "__main__":
    unittest.main()
