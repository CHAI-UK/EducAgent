"""Public file isolation and optional, non-credit-bearing learning entry."""

import asyncio
import json
import tempfile
import threading
import unittest
from http import HTTPStatus
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from pydantic_ai.messages import ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models import override_allow_model_requests
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.models.test import TestModel
from pydantic_ai.exceptions import ModelHTTPError

from educagent_sdk import load_content_pack
from educagent_sdk.demo import DemoController, JsonlEventStore
from educagent_sdk.diagnostic import DiagnosticSession, load_diagnostic_plan
from educagent_sdk.foundation_profiles import load_foundation_profiles
from educagent_sdk.web_demo import (
    ModuleRuntime, ProfileRuntime, _handle_command, _request_failure, _state, create_demo_server,
    create_module_hub_server,
)


ROOT = Path(__file__).resolve().parents[1]


class WebBoundaryTest(unittest.TestCase):
    def test_provider_failure_exposes_only_a_valid_integer_upstream_status(self) -> None:
        secret = "synthetic-provider-key-do-not-log"
        for upstream_status in (100, 401, 403, 404, 429, 500, 599):
            with self.subTest(status=upstream_status):
                error = ModelHTTPError(upstream_status, "synthetic-model-name",
                    body={"error": "private provider response", "api_key": secret},
                    headers={"Authorization": secret})
                status, failure = _request_failure(error, "safe.request")
                self.assertEqual(status, HTTPStatus.SERVICE_UNAVAILABLE)
                self.assertIs(type(failure["upstream_status"]), int)
                self.assertEqual(failure["upstream_status"], upstream_status)
                self.assertEqual(failure["retryable"], upstream_status not in {401, 403, 404})
                self.assertEqual(failure["diagnostic"], "ModelHTTPError")
                self.assertEqual(set(failure), {"error", "code", "diagnostic", "request_id",
                                                "retryable", "recovery", "upstream_status"})
                for private in (secret, "private provider response", "synthetic-model-name", "Authorization"):
                    self.assertNotIn(private, json.dumps(failure))

    def test_malformed_upstream_status_is_omitted_without_string_coercion(self) -> None:
        for supplied in (True, False, 0, 99, 600, -1, "429\nprivate", [429], {"key": "private"}):
            with self.subTest(status=supplied):
                error = RuntimeError("private error body and synthetic API key")
                error.status_code = supplied
                status, failure = _request_failure(error, "malformed.status")
                self.assertEqual(status, HTTPStatus.SERVICE_UNAVAILABLE)
                self.assertNotIn("upstream_status", failure)
                self.assertNotIn("private", json.dumps(failure))
                self.assertTrue(failure["retryable"])

    def test_lan_binding_requires_explicit_opt_in(self) -> None:
        server = create_demo_server(
            DemoController(load_content_pack(ROOT / "content/causality_m0_full.json")),
            host="0.0.0.0", allow_lan=True, port=0, model=TestModel(),
        )
        try:
            self.assertEqual(server.server_address[0], "0.0.0.0")
        finally:
            server.server_close()

    def setUp(self) -> None:
        self.pack = load_content_pack(ROOT / "content/causality_m0_full.json")
        self.plan = load_diagnostic_plan(ROOT / "content/causality_m0_diagnostic.json")

    def test_skip_starts_full_route_and_reloads_without_diagnostic_credit(self) -> None:
        diagnostic = DiagnosticSession(self.pack, self.plan)
        diagnostic.start()
        diagnostic.respond(
            request_id="diagnostic.before-skip",
            option_id=next(c.option_id for c in diagnostic.activities[0].choices if c.correct),
        )
        with tempfile.TemporaryDirectory() as directory:
            store = JsonlEventStore(Path(directory) / "review.jsonl")
            controller = DemoController(self.pack, store=store)
            state = asyncio.run(_handle_command(
                controller, "/api/diagnostic/skip", {},
                model=TestModel(), diagnostic=diagnostic,
            ))
            self.assertEqual(state["status"], "active")
            self.assertEqual(state["route_scope"], "all")
            self.assertEqual(state["completed_concept_ids"], ())
            self.assertEqual(state["diagnostic"]["status"], "in_progress")
            self.assertEqual(len(diagnostic.responses), 1)
            self.assertTrue(state["learning_unlocked"])
            event_count = len(controller.events)
            asyncio.run(_handle_command(
                controller, "/api/diagnostic/skip", {},
                model=TestModel(), diagnostic=diagnostic,
            ))
            self.assertEqual(len(controller.events), event_count)
            resumed = _state(
                DemoController(self.pack, store=store),
                DiagnosticSession(self.pack, self.plan), TestModel(),
            )
            self.assertTrue(resumed["learning_unlocked"])
            self.assertEqual(resumed["route_scope"], "all")
            self.assertEqual(resumed["completed_concept_ids"], ())

    def test_practical_mission_can_start_without_answering_a_diagnostic(self) -> None:
        diagnostic = DiagnosticSession(self.pack, self.plan)
        state = asyncio.run(_handle_command(
            DemoController(self.pack), "/api/start-scene", {},
            model=TestModel(), diagnostic=diagnostic,
        ))
        self.assertEqual(state["activity_id"], "association-is-not-causation.transfer")
        self.assertEqual(state["diagnostic"]["status"], "not_started")
        self.assertEqual(state["completed_concept_ids"], ())
        self.assertTrue(state["learning_unlocked"])

    def test_only_public_files_are_served_even_with_a_workspace_static_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            public = (
                "index.html", "styles.css", "sources.html", "assets/app.js",
                "portal/index.html", "portal/assets/app.css", "nirvana/index.html",
                "nirvana/app.js", "media/causality/scene.png",
            )
            private = (
                ".env", "README.md", "start-demo.ps1", "index.zip",
                "EducAgent-SDK/assets/book.mmd", "EducAgent-SDK/assets/figure.jpg",
                "EducAgent-SDK/.env", "portal/.env", "assets/.private/image.png",
                "media/book.pdf", "assets/app.js.map", "nirvana/test.jsonl",
                "EducAgent-SDK/public/index.html",
            )
            for relative in (*public, *private):
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("synthetic boundary fixture", encoding="utf-8")
            server = create_demo_server(
                DemoController(self.pack), port=0, model=TestModel(), static_root=root,
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_port}"
            try:
                for relative in (*public, "portal/", "nirvana", ""):
                    with self.subTest(public=relative), urlopen(f"{base}/{relative}", timeout=5) as response:
                        self.assertEqual(response.status, 200)
                        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
                        if relative == "nirvana":
                            self.assertTrue(response.url.endswith("/nirvana/"))
                denied = (*private,
                    "%2eenv", "portal/%2e%2e/EducAgent-SDK/assets/figure.jpg",
                    "portal%5c..%5cEducAgent-SDK%5c.env", "assets/app.js%3Asecret",
                )
                for relative in denied:
                    with self.subTest(private=relative), self.assertRaises(HTTPError) as error:
                        urlopen(f"{base}/{relative}", timeout=5)
                    self.assertEqual(error.exception.code, 404)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)


class CompletedCourseReviewTest(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        directory = Path(temporary.name)
        pack = load_content_pack(ROOT / "content/causality_m0_full.json")
        profiles = load_foundation_profiles(pack, ROOT / "content/foundation_profiles.json")
        self.general = DemoController(
            pack, store=JsonlEventStore(directory / "general.jsonl"),
            profile_id="general", teaching_pack=profiles["general"],
        )
        self.medical = DemoController(
            profiles["medical"], store=JsonlEventStore(directory / "medical.jsonl"),
            profile_id="medical",
        )
        self.general.start(session_id="review.general")
        activities = tuple(
            item for item in self.medical.pack.activities
            if item.activity_id.startswith("variables-and-values.")
        )
        self.medical.start(
            session_id="review.medical", route_scope="preferred",
            preferred_activity_ids=tuple(item.activity_id for item in activities),
        )
        for index, activity in enumerate(activities):
            self.medical.respond(
                request_id=f"review.complete.answer.{index}",
                option_id=next(item.option_id for item in activity.choices if item.correct),
            )
            self.medical.continue_activity(request_id=f"review.complete.continue.{index}")
        self.assertEqual(self.medical.view()["status"], "completed")
        self.original = self.medical.view()
        self.medical_bytes = self.medical.store.path.read_bytes()
        self.general_bytes = self.general.store.path.read_bytes()
        self.contexts = []

        def reply(messages, _info):
            for message in messages:
                for part in message.parts:
                    if isinstance(part, UserPromptPart) and isinstance(part.content, str):
                        context = json.loads(part.content)
                        if "learner_message" in context:
                            self.contexts.append(context)
            return ModelResponse(parts=[TextPart("A variable can have different recorded values.")])

        self.module = ModuleRuntime(
            "causality_m0", "Causality foundations", False, (), None, self.general,
            profiles={"general": ProfileRuntime(self.general), "medical": ProfileRuntime(self.medical)},
        )
        effect = ModuleRuntime(
            "m1_effect", "Effect of an intervention", True, ("causality_m0",), "effect",
            DemoController(load_content_pack(ROOT / "content/m1_effect_of_an_intervention.json")),
        )
        self.server = create_module_hub_server(
            [self.module, effect], port=0, model=FunctionModel(reply), unguarded_tutor=True,
        )
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()

        def stop_server() -> None:
            self.server.shutdown()
            thread.join(timeout=5)
            self.server.server_close()

        self.addCleanup(stop_server)
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def command(self, path: str, **body: object) -> dict:
        request = Request(
            self.base + path, data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
        )
        with override_allow_model_requests(False), urlopen(request, timeout=5) as response:
            return json.load(response)

    def assert_progress_unchanged(self) -> None:
        self.assertEqual(self.medical.store.path.read_bytes(), self.medical_bytes)
        self.assertEqual(self.general.store.path.read_bytes(), self.general_bytes)
        self.assertEqual(self.medical.view(), self.original)

    def test_completed_course_can_discuss_a_topic_without_changing_saved_credit(self) -> None:
        self.command("/api/select-profile", profile_id="medical")
        review = self.command("/api/review-topic", concept_id="variables-and-values")
        self.assertTrue(review["review_mode"])
        self.assertEqual(review["status"], "active")
        self.assertEqual(review["activity_id"], "variables-and-values.practice")
        self.assertEqual(review["lesson"]["profile_id"], "medical")
        self.assertTrue(review["can_send_message"])
        self.assertFalse(review["can_continue"])
        self.assertEqual(review["completed_activity_ids"], list(self.original["completed_activity_ids"]))
        self.assertEqual(review["completed_concept_ids"], list(self.original["completed_concept_ids"]))
        first = self.command(
            "/api/message", request_id="review.question.1", text="Can two patients have the same value?",
        )
        retried = self.command(
            "/api/message", request_id="review.question.1", text="Can two patients have the same value?",
        )
        self.assertEqual(retried, first)
        second = self.command(
            "/api/message", request_id="review.question.2", text="What varies if their values match?",
        )
        self.assertEqual(second["learner_message_count"], 2)
        self.assertEqual(len(self.contexts), 2)
        self.assertEqual(self.contexts[-1]["profile_id"], "medical")
        self.assertIn("Can two patients", json.dumps(self.contexts[-1]["recent_conversation"]))
        self.assert_progress_unchanged()
        restored = self.command("/api/end-review")
        self.assertFalse(restored["review_mode"])
        self.assertEqual(restored["status"], "completed")
        self.assertEqual(restored["completed_activity_ids"], list(self.original["completed_activity_ids"]))
        self.assertNotIn("Can two patients", json.dumps(restored["conversation"]))
        self.assert_progress_unchanged()

    def test_topic_review_reaches_its_challenge_before_returning_to_saved_route(self) -> None:
        self.command("/api/select-profile", profile_id="medical")
        self.command("/api/review-topic", concept_id="variables-and-values")
        for index, activity_id in enumerate((
            "variables-and-values.practice", "variables-and-values.transfer",
        )):
            activity = next(item for item in self.medical.pack.activities if item.activity_id == activity_id)
            correct = self.command(
                "/api/respond", request_id=f"review.sequence.answer.{index}",
                option_id=next(item.option_id for item in activity.choices if item.correct),
            )
            self.assertTrue(correct["assessment_accepted"])
            continued = self.command("/api/continue", request_id=f"review.sequence.continue.{index}")
            if index == 0:
                self.assertTrue(continued["review_mode"])
                self.assertEqual(continued["status"], "active")
                self.assertEqual(continued["activity_id"], "variables-and-values.transfer")
                self.assertFalse(continued["assessment_accepted"])
                self.assertFalse(continued["can_continue"])
            else:
                self.assertFalse(continued["review_mode"])
                self.assertEqual(continued["status"], "completed")
            self.assert_progress_unchanged()

    def test_all_correct_diagnostic_can_review_quiz_explanation_and_challenge(self) -> None:
        self.general.reset()
        diagnostic = DiagnosticSession(
            self.general.pack, load_diagnostic_plan(ROOT / "content/causality_m0_diagnostic.json"),
        )
        self.module.profiles["general"] = ProfileRuntime(self.general, diagnostic)
        self.command("/api/select-profile", profile_id="general")
        self.command("/api/diagnostic/start")
        for index, activity in enumerate(diagnostic.activities):
            self.command(
                "/api/diagnostic/respond", request_id=f"review.diagnostic.{index}",
                option_id=next(item.option_id for item in activity.choices if item.correct),
            )
        route = self.command("/api/start", session_id="review.diagnostic-complete")
        self.assertEqual(route["status"], "completed")
        self.assertEqual(route["completed_activity_ids"], [])
        self.assertEqual(route["diagnostic"]["result"]["accepted_count"], 9)
        saved_bytes = self.general.store.path.read_bytes()
        review = self.command("/api/review-topic", concept_id="variables-and-values")
        self.assertEqual(review["activity_id"], "variables-and-values.practice")
        activity = next(item for item in self.general.pack.activities if item.activity_id == review["activity_id"])
        explanation = self.command(
            "/api/respond", request_id="review.diagnostic.quiz",
            option_id=next(item.option_id for item in activity.choices if item.correct),
        )
        self.assertTrue(explanation["assessment_accepted"])
        self.assertEqual(explanation["lesson"]["challenge_activity_id"], "variables-and-values.transfer")
        challenge = self.command("/api/continue", request_id="review.diagnostic.challenge")
        self.assertTrue(challenge["review_mode"])
        self.assertEqual(challenge["status"], "active")
        self.assertEqual(challenge["activity_id"], "variables-and-values.transfer")
        self.assertFalse(challenge["can_continue"])
        self.assertEqual(challenge["completed_activity_ids"], [])
        self.assertEqual(self.general.store.path.read_bytes(), saved_bytes)

    def test_review_requires_a_completed_normal_course_and_a_declared_concept(self) -> None:
        self.command("/api/select-profile", profile_id="general")
        with self.assertRaises(HTTPError):
            self.command("/api/review-topic", concept_id="variables-and-values")
        self.command("/api/select-profile", profile_id="medical")
        with self.assertRaises(HTTPError) as invalid:
            self.command("/api/review-topic", concept_id="invented-concept")
        self.assertEqual(invalid.exception.code, 400)
        self.command("/api/preview", enabled=True)
        with self.assertRaises(HTTPError):
            self.command("/api/review-topic", concept_id="variables-and-values")
        self.command("/api/preview", enabled=False)
        self.module.lesson_samples["medical"] = DemoController(self.medical.pack, profile_id="medical")
        self.command("/api/start-lesson", profile_id="medical")
        with self.assertRaises(HTTPError):
            self.command("/api/review-topic", concept_id="variables-and-values")
        self.assert_progress_unchanged()

    def test_review_selection_restores_after_preview_and_exits_on_profile_module_or_reset(self) -> None:
        self.command("/api/select-profile", profile_id="medical")
        review = self.command("/api/review-topic", concept_id="variables-and-values")
        self.command("/api/preview", enabled=True)
        self.command("/api/preview/navigate", activity_id="data-vs-assumptions.practice")
        restored = self.command("/api/preview", enabled=False)
        self.assertTrue(restored["review_mode"])
        self.assertEqual(restored["attempt_id"], review["attempt_id"])
        self.assert_progress_unchanged()
        general = self.command("/api/select-profile", profile_id="general")
        self.assertFalse(general["review_mode"])
        self.assertEqual(general["attempt_id"], self.general.view()["attempt_id"])
        medical = self.command("/api/select-profile", profile_id="medical")
        self.assertFalse(medical["review_mode"])
        self.assertEqual(medical["status"], "completed")
        self.command("/api/review-topic", concept_id="variables-and-values")
        effect = self.command("/api/select-module", module_id="m1_effect", test_only_force_unlock=True)
        self.assertFalse(effect["review_mode"])
        returned = self.command("/api/select-module", module_id="causality_m0")
        self.assertEqual(returned["status"], "completed")
        self.assertFalse(returned["review_mode"])
        self.assert_progress_unchanged()
        self.command("/api/review-topic", concept_id="variables-and-values")
        reset = self.command(
            "/api/reset", profile_id="medical", pack_id=self.medical.pack.pack_id,
            version=self.medical.pack.version,
        )
        self.assertFalse(reset["review_mode"])
        self.assertTrue(reset["profile_required"])
        self.assertFalse(self.medical.events)
        self.assertEqual(self.medical.store.path.read_bytes(), b"")
        self.assertEqual(self.general.store.path.read_bytes(), self.general_bytes)
        reselected = self.command("/api/select-profile", profile_id="medical")
        self.assertFalse(reselected["review_mode"])
        self.assertEqual(reselected["status"], "not_started")


if __name__ == "__main__":
    unittest.main()
