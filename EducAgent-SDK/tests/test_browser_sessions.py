"""Provider-independent HTTP checks for anonymous browser-isolated progress."""

import asyncio
import json
import tempfile
import threading
import unittest
from http.cookiejar import CookieJar
from pathlib import Path
from time import perf_counter
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, Request, build_opener

from pydantic_ai.messages import ModelResponse, TextPart
from pydantic_ai.models.function import FunctionModel

from educagent_sdk import load_content_pack
from educagent_sdk.demo import DemoController, JsonlEventStore
from educagent_sdk.diagnostic import DiagnosticSession, load_diagnostic_plan
from educagent_sdk.events import LearnerMessageRecorded, ResponseRecorded, replay
from educagent_sdk.tutor import run_open_demo_reply
from educagent_sdk.web_demo import ModuleRuntime, ProfileRuntime, create_browser_session_server


ROOT = Path(__file__).resolve().parents[1]


class BrowserSessionsTest(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.sessions = self.root / "browser-sessions"
        self.pack = load_content_pack(ROOT / "content/causality_m0_full.json")
        self.plan = load_diagnostic_plan(ROOT / "content/causality_m0_diagnostic.json")
        self.created = []
        self.models = []
        self.model_clients = []
        self.slow_started = threading.Event()
        self.release_slow = threading.Event()
        self.server = None
        self.start_server()
        self.addCleanup(self.stop_server)

    def factory(self, directory: Path) -> list[ModuleRuntime]:
        self.assertEqual(directory.parent, self.sessions.resolve())
        self.assertRegex(directory.name, r"^[0-9a-f]{64}$")
        self.created.append(directory)
        modules = []
        for module_id in ("foundation", "followup"):
            profiles = {
                profile: ProfileRuntime(
                    DemoController(
                        self.pack, profile_id=profile,
                        store=JsonlEventStore(directory / f"{module_id}-{profile}.jsonl"),
                    ),
                    DiagnosticSession(self.pack, self.plan),
                )
                for profile in ("general", "medical")
            }
            modules.append(ModuleRuntime(
                module_id, module_id.title(), False, (), None,
                profiles["general"].controller, profiles["general"].diagnostic,
                profiles=profiles,
            ))
        return modules

    def model_factory(self):
        test = self

        class LoopBoundClient:
            loop = None
            closed = False

            async def close(self):
                if self.loop is not None:
                    test.assertIs(self.loop, asyncio.get_running_loop())
                self.closed = True

        client = LoopBoundClient()
        self.model_clients.append(client)

        async def reply(messages, _info):
            loop = asyncio.get_running_loop()
            if client.loop is not None:
                self.assertIs(client.loop, loop)
            client.loop = loop
            self.assertFalse(client.closed)
            if "SLOW_BROWSER_ONLY" in str(messages):
                self.slow_started.set()
                while not self.release_slow.is_set():
                    await asyncio.sleep(0.01)
            return ModelResponse(parts=[TextPart("A variable can have different recorded values. What could vary?")])

        model = FunctionModel(reply)
        model.client = client
        self.models.append(model)
        return model

    def start_server(self, **options) -> None:
        self.server = create_browser_session_server(
            options.pop("module_factory", self.factory),
            sessions_root=self.sessions, model_factory=self.model_factory,
            port=0, unguarded_tutor=True, **options,
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def stop_server(self) -> None:
        if self.server is not None:
            self.server.shutdown()
            self.thread.join(timeout=5)
            self.server.server_close()
            self.server = None

    def browser(self):
        jar = CookieJar()
        return build_opener(HTTPCookieProcessor(jar)), jar

    def request(self, browser, path="/api/state", *, headers=None, **body):
        request = Request(
            self.base + path, data=None if not body else json.dumps(body).encode(),
            headers={"Content-Type": "application/json", **(headers or {})},
            method="POST" if body or path != "/api/state" and path not in {"/api/trace", "/api/health"} else "GET",
        )
        with browser.open(request, timeout=10) as response:
            return json.load(response), response.headers

    def command(self, browser, path, **body):
        return self.request(browser, path, **body)[0]

    def state(self, browser):
        return self.request(browser)[0]

    def answer(self, browser, state, *, correct=True):
        activity = next(item for item in self.pack.activities if item.activity_id == state["activity_id"])
        option = next(item.option_id for item in activity.choices if item.correct is correct)
        return self.command(browser, "/api/respond", request_id="same.answer", option_id=option)

    def test_cookie_is_opaque_session_only_and_not_returned_in_learning_data(self) -> None:
        browser, jar = self.browser()
        state, headers = self.request(browser)
        cookie = list(jar)[0]
        self.assertEqual(cookie.name, "educagent_portal_session")
        self.assertRegex(cookie.value, r"^[0-9a-f]{64}$")
        self.assertTrue(cookie.discard)
        self.assertIsNone(cookie.expires)
        self.assertIn("HttpOnly", headers["Set-Cookie"])
        self.assertIn("SameSite=Lax", headers["Set-Cookie"])
        self.assertNotIn("Max-Age", headers["Set-Cookie"])
        self.assertTrue(state["profile_required"])
        self.assertNotIn(cookie.value, json.dumps(state))
        self.assertNotIn(cookie.value, json.dumps(self.command(browser, "/api/trace")))
        self.assertIsNone(self.request(browser)[1].get("Set-Cookie"))
        self.assertEqual(len(self.created), 1)

    def test_two_browsers_isolate_answers_chat_selection_preview_and_reset(self) -> None:
        first, _ = self.browser()
        second, _ = self.browser()
        self.command(first, "/api/select-profile", profile_id="general")
        first_started = self.command(first, "/api/diagnostic/skip")
        first_checked = self.answer(first, first_started)
        self.command(first, "/api/message", request_id="same.chat", text="FIRST_BROWSER_ONLY")
        self.assertTrue(self.state(second)["profile_required"])
        self.command(second, "/api/select-profile", profile_id="medical")
        second_started = self.command(second, "/api/diagnostic/skip")
        self.answer(second, second_started)
        second_chat = self.command(second, "/api/message", request_id="same.chat", text="SECOND_BROWSER_ONLY")
        self.assertNotIn("FIRST_BROWSER_ONLY", json.dumps(second_chat))
        self.assertNotIn("SECOND_BROWSER_ONLY", json.dumps(self.state(first)))
        self.assertEqual(self.state(first)["profile_id"], "general")
        self.assertEqual(self.state(second)["profile_id"], "medical")
        second_bytes = (self.created[1] / "foundation-medical.jsonl").read_bytes()
        self.command(first, "/api/preview", enabled=True)
        self.command(first, "/api/select-module", module_id="followup")
        self.assertFalse(self.state(second)["preview_mode"])
        self.assertEqual(self.state(second)["active_module_id"], "foundation")
        self.command(first, "/api/preview", enabled=False)
        reset = self.command(first, "/api/reset", profile_id="general",
                             pack_id=first_checked["learning_pack_id"], version=first_checked["learning_pack_version"])
        self.assertTrue(reset["profile_required"])
        self.assertEqual((self.created[0] / "foundation-general.jsonl").read_bytes(), b"")
        self.assertEqual((self.created[1] / "foundation-medical.jsonl").read_bytes(), second_bytes)
        self.assertEqual(self.state(second)["status"], "active")
        self.assertEqual(len(self.models), 2)

    def test_same_cookie_resumes_progress_preferences_and_diagnostic_after_restart(self) -> None:
        browser, jar = self.browser()
        self.command(browser, "/api/select-profile", profile_id="medical")
        diagnostic = self.command(browser, "/api/diagnostic/start")
        self.command(browser, "/api/diagnostic/respond", request_id="diagnostic.answer",
                     option_id=diagnostic["diagnostic"]["choices"][0]["option_id"])
        self.command(browser, "/api/select-module", module_id="followup")
        started = self.command(browser, "/api/diagnostic/skip")
        checked = self.answer(browser, started)
        original_cookie = list(jar)[0].value
        self.stop_server()
        self.start_server()
        resumed = self.state(browser)
        self.assertEqual(list(jar)[0].value, original_cookie)
        self.assertEqual(resumed["active_module_id"], "followup")
        self.assertEqual(resumed["profile_id"], "medical")
        self.assertEqual(resumed["attempt_id"], checked["attempt_id"])
        self.assertTrue(resumed["can_continue"])
        diagnostic = self.command(browser, "/api/select-module", module_id="foundation")
        self.assertEqual(diagnostic["diagnostic"]["answered_count"], 1)
        self.assertEqual(diagnostic["diagnostic"]["status"], "in_progress")
        other, _ = self.browser()
        self.assertTrue(self.state(other)["profile_required"])

    def test_cache_eviction_reloads_saved_state_without_additional_listening_sockets(self) -> None:
        self.stop_server()
        self.start_server(max_cached_sessions=1)
        first, first_jar = self.browser()
        second, _ = self.browser()
        self.command(first, "/api/select-profile", profile_id="medical")
        started = self.command(first, "/api/diagnostic/skip")
        checked = self.answer(first, started)
        token = list(first_jar)[0].value
        self.assertTrue(self.state(second)["profile_required"])
        self.assertTrue(self.model_clients[0].closed)
        resumed = self.state(first)
        self.assertEqual(list(first_jar)[0].value, token)
        self.assertEqual(resumed["profile_id"], "medical")
        self.assertEqual(resumed["attempt_id"], checked["attempt_id"])
        self.assertTrue(resumed["can_continue"])
        self.assertEqual(len(set(self.created)), 2)
        self.assertEqual(len(self.created), 3)

    def test_slow_tutor_request_does_not_block_another_browser(self) -> None:
        first, _ = self.browser()
        second, _ = self.browser()
        for browser in (first, second):
            self.command(browser, "/api/select-profile", profile_id="general")
            self.command(browser, "/api/diagnostic/skip")
        result = []
        failure = []

        def slow_request():
            try:
                result.append(self.command(first, "/api/message", request_id="slow.message", text="SLOW_BROWSER_ONLY"))
            except Exception as exc:
                failure.append(exc)

        worker = threading.Thread(target=slow_request, daemon=True)
        worker.start()
        try:
            self.assertTrue(self.slow_started.wait(timeout=5))
            independent = self.command(second, "/api/message", request_id="fast.message", text="What can vary?")
            self.assertEqual(independent["learner_message_count"], 1)
            self.assertTrue(worker.is_alive())
            self.assertIsNot(self.model_clients[0].loop, self.model_clients[1].loop)
        finally:
            self.release_slow.set()
            worker.join(timeout=5)
        self.assertFalse(failure)
        self.assertEqual(result[0]["learner_message_count"], 1)
        self.stop_server()
        self.assertTrue(all(client.closed for client in self.model_clients))

    def test_tutor_deadline_releases_same_cookie_state_and_saved_request_can_retry(self) -> None:
        browser, jar = self.browser()
        self.command(browser, "/api/select-profile", profile_id="general")
        started = self.command(browser, "/api/diagnostic/skip")
        cookie = list(jar)[0]
        cookie_header = {"Cookie": f"{cookie.name}={cookie.value}"}
        # A separate HTTP connection carries the same anonymous browser session.
        state_connection = build_opener()
        body = {"request_id": "deadline.message", "text": "SLOW_BROWSER_ONLY: What can vary?"}
        responses = []
        failures = []

        async def short_deadline(*args, **kwargs):
            return await run_open_demo_reply(*args, **kwargs, timeout_seconds=1)

        def slow_request():
            try:
                responses.append((200, self.command(browser, "/api/message", **body)))
            except HTTPError as exc:
                with exc:
                    responses.append((exc.code, json.load(exc)))
            except Exception as exc:
                failures.append(exc)

        worker = threading.Thread(target=slow_request, daemon=True)
        with patch("educagent_sdk.demo.run_open_demo_reply", side_effect=short_deadline):
            worker.start()
            try:
                self.assertTrue(self.slow_started.wait(timeout=5))
                before_state = perf_counter()
                pending, headers = self.request(state_connection, headers=cookie_header)
                self.assertLess(perf_counter() - before_state, 3)
                worker.join(timeout=3)
                self.assertFalse(worker.is_alive())
                self.assertFalse(failures)
                self.assertFalse(self.release_slow.is_set())
                status, failure = responses[0]
                self.assertEqual(status, 503)
                self.assertEqual(failure["code"], "tutor_unavailable")
                self.assertEqual(failure["diagnostic"], "TimeoutError")
                self.assertTrue(failure["retryable"])
                self.assertEqual(failure["request_id"], body["request_id"])
                self.assertIsNone(headers.get("Set-Cookie"))
                self.assertEqual(pending["pending_tutor_message"], body)
                self.assertEqual(pending["learner_message_count"], 1)

                self.release_slow.set()
                recovered = self.command(browser, "/api/message", **body)
                self.assertIsNone(recovered["pending_tutor_message"])
                self.assertEqual(recovered["learner_message_count"], 1)
                store = JsonlEventStore(self.created[0] / "foundation-general.jsonl")
                saved = store.path.read_bytes()
                repeated = self.command(browser, "/api/message", **body)
                self.assertEqual(store.path.read_bytes(), saved)
                self.assertEqual(repeated["learner_message_count"], 1)
                events = store.load()
                messages = [event for event in events if isinstance(event, LearnerMessageRecorded)]
                self.assertEqual(len(messages), 1)
                self.assertEqual(messages[0].request_id, body["request_id"])
                self.assertFalse(any(isinstance(event, ResponseRecorded) for event in events))
                self.assertIsNone(replay(events).last_evaluation)
                for state in (pending, recovered, repeated):
                    self.assertEqual(state["attempt_id"], started["attempt_id"])
                    self.assertEqual(state["completed_activity_ids"], started["completed_activity_ids"])
                    self.assertFalse(state["assessment_submitted"])
                    self.assertFalse(state["can_continue"])
                self.assertEqual(list(jar)[0].value, cookie.value)
                self.assertEqual(len(self.created), 1)
                self.assertEqual(len(self.models), 1)
            finally:
                self.release_slow.set()
                worker.join(timeout=5)

    def test_full_busy_cache_retries_do_not_create_orphan_session_directories(self) -> None:
        self.stop_server()
        self.start_server(max_cached_sessions=1)
        first, _ = self.browser()
        self.command(first, "/api/select-profile", profile_id="general")
        self.command(first, "/api/diagnostic/skip")
        failures = []

        def slow_request():
            try:
                self.command(first, "/api/message", request_id="capacity.slow", text="SLOW_BROWSER_ONLY")
            except Exception as exc:
                failures.append(exc)

        worker = threading.Thread(target=slow_request, daemon=True)
        worker.start()
        try:
            self.assertTrue(self.slow_started.wait(timeout=5))
            for _ in range(3):
                other, jar = self.browser()
                with self.assertRaises(HTTPError) as busy:
                    self.state(other)
                self.assertEqual(busy.exception.code, 503)
                self.assertIsNone(busy.exception.headers.get("Set-Cookie"))
                self.assertEqual(len(list(jar)), 0)
                self.assertEqual(len(list(self.sessions.iterdir())), 1)
                self.assertEqual(len(self.models), 1)
        finally:
            self.release_slow.set()
            worker.join(timeout=5)
        self.assertFalse(failures)

    def test_failed_initialization_closes_owned_client_without_allocating_hub_runner(self) -> None:
        runner_type = asyncio.Runner
        for failure in ("module_factory", "application_validation", "saved_selection"):
            with self.subTest(failure=failure):
                self.stop_server()

                def failing_factory(directory):
                    if failure == "module_factory":
                        raise ValueError("synthetic module initialization failure")
                    if failure == "application_validation":
                        return []
                    modules = self.factory(directory)
                    (directory / "selection.json").write_text("{", encoding="utf-8")
                    return modules

                self.start_server(module_factory=failing_factory)
                browser, _ = self.browser()
                with patch("educagent_sdk.web_demo.asyncio.Runner", wraps=runner_type) as runners:
                    with self.assertRaises(HTTPError) as unavailable:
                        self.state(browser)
                    self.assertEqual(unavailable.exception.code, 503)
                    self.assertTrue(self.model_clients[-1].closed)
                    # Only the temporary model-close runner is allocated;
                    # invalid modules/preferences never acquire a hub runner.
                    self.assertEqual(runners.call_count, 1)

    def test_forged_and_path_cookies_are_replaced_and_do_not_load_shared_history(self) -> None:
        (self.root / "legacy.jsonl").write_text("PRIVATE_LEGACY_MARKER", encoding="utf-8")
        unknown = "a" * 64
        (self.sessions / unknown).mkdir()
        for token in ("../../outside", "%2e%2e%2fsecret", unknown, "B" * 64):
            with self.subTest(token=token):
                browser, jar = self.browser()
                state, _ = self.request(browser, headers={"Cookie": f"educagent_portal_session={token}"})
                self.assertNotEqual(list(jar)[0].value, token)
                self.assertTrue(state["profile_required"])
                self.assertEqual(state["status"], "not_started")
                self.assertNotIn("PRIVATE_LEGACY_MARKER", json.dumps(state))
        self.assertFalse((self.root / "outside").exists())
        self.assertFalse((self.sessions / unknown / "selection.json").exists())

    def test_health_creates_no_session_and_cross_origin_post_is_denied(self) -> None:
        browser, jar = self.browser()
        state = self.command(browser, "/api/health")
        self.assertEqual(state["progress_scope"], "browser_session")
        self.assertEqual(len(list(jar)), 0)
        self.assertFalse(self.created)
        with self.assertRaises(HTTPError) as denied:
            self.request(browser, "/api/select-profile", headers={"Origin": "https://evil.invalid"}, profile_id="general")
        self.assertEqual(denied.exception.code, 403)
        self.assertFalse(self.created)

    def test_loopback_authoring_page_remains_available_without_a_learner_session(self) -> None:
        browser, jar = self.browser()
        with browser.open(self.base + "/authoring/content-pack-editor.html", timeout=10) as response:
            self.assertEqual(response.status, 200)
            self.assertIn(b"<title>", response.read())
        self.assertEqual(len(list(jar)), 0)
        self.assertFalse(self.created)

    def test_secure_cookie_option_adds_secure_attribute(self) -> None:
        self.stop_server()
        self.start_server(secure_cookie=True)
        browser, _ = self.browser()
        self.assertIn("; Secure", self.request(browser)[1]["Set-Cookie"])


if __name__ == "__main__":
    unittest.main()
