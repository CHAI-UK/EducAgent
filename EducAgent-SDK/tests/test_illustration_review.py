"""HTTP review and preview retain image-only teaching overlays and saved evidence."""

import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.request import Request, urlopen

from pydantic_ai.models.test import TestModel

from educagent_sdk.course_illustrations import load_course_illustrations
from educagent_sdk.web_demo import create_module_hub_server
from examples.playable_demo import _build_module, _load_registry


ROOT = Path(__file__).resolve().parents[1]


class IllustrationReviewTest(unittest.TestCase):
    def test_review_and_preview_keep_overlay_without_rewriting_formal_progress(self):
        catalog = load_course_illustrations(ROOT / "content/course_illustrations.json")
        entries = _load_registry(ROOT / "content/modules.json")
        for module_id, profile, current_concept in (
            ("causality_m0", "general", "observation-vs-intervention"),
            ("m1_effect", "medical", "average-treatment-effect"),
        ):
            with self.subTest(module=module_id, profile=profile), tempfile.TemporaryDirectory() as directory:
                modules = [_build_module(entry, events_root=Path(directory), reset=False,
                                         illustration_catalog=catalog) for entry in entries]
                module = next(item for item in modules if item.module_id == module_id)
                controller = module.profiles[profile].controller
                original_pack = controller.pack.model_dump_json()
                controller.start(session_id=f"illustration.{module_id}.{profile}")
                reviewed_concept = controller.pack.concepts[0].concept_id
                review_activity_ids = controller.topic_activity_ids(reviewed_concept)
                for index, activity_id in enumerate(review_activity_ids):
                    activity = next(item for item in controller.pack.activities if item.activity_id == activity_id)
                    controller.respond(request_id=f"illustration.answer.{index}",
                                       option_id=next(item.option_id for item in activity.choices if item.correct))
                    controller.continue_activity(request_id=f"illustration.next.{index}")
                controller.navigate_to_concept(request_id="illustration.current", concept_id=current_concept)
                normal = controller.view()
                saved = controller.store.path.read_bytes()
                scored_activity = next(item for item in controller.pack.activities
                                       if item.activity_id == normal["activity_id"])
                teaching_activity = next(item for item in controller.teaching_pack.activities
                                         if item.activity_id == normal["activity_id"])
                self.assertNotEqual(scored_activity.scenario_image, teaching_activity.scenario_image)
                self.assertEqual(normal["scenario_image"], teaching_activity.scenario_image.model_dump())
                review_image = next(item.scenario_image.model_dump() for item in controller.teaching_pack.activities
                                    if item.activity_id == review_activity_ids[0])
                server = create_module_hub_server(modules, port=0, model=TestModel())
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                base = f"http://127.0.0.1:{server.server_port}"

                def command(path, **body):
                    request = Request(base + path, data=json.dumps(body).encode(),
                                      headers={"Content-Type": "application/json"})
                    with urlopen(request, timeout=5) as response:
                        return json.load(response)

                def assert_formal_progress_unchanged():
                    self.assertEqual(controller.store.path.read_bytes(), saved)
                    self.assertEqual(controller.pack.model_dump_json(), original_pack)
                    self.assertEqual(controller.view(), normal)

                try:
                    command("/api/select-module", module_id=module_id)
                    selected = command("/api/select-profile", profile_id=profile)
                    self.assertEqual(selected["scenario_image"], normal["scenario_image"])
                    review = command("/api/navigate", request_id="illustration.review", concept_id=reviewed_concept)
                    self.assertTrue(review["review_mode"])
                    self.assertEqual(review["scenario_image"], review_image)
                    self.assertEqual(review["completed_activity_ids"], list(normal["completed_activity_ids"]))
                    assert_formal_progress_unchanged()
                    resumed = command("/api/end-review")
                    self.assertFalse(resumed["review_mode"])
                    self.assertEqual(resumed["attempt_id"], normal["attempt_id"])
                    self.assertEqual(resumed["scenario_image"], normal["scenario_image"])
                    assert_formal_progress_unchanged()
                    command("/api/preview", enabled=True)
                    preview = command("/api/preview/navigate", activity_id=review_activity_ids[0])
                    self.assertTrue(preview["preview_mode"])
                    self.assertEqual(preview["scenario_image"], review_image)
                    self.assertEqual(preview["completed_activity_ids"], [])
                    assert_formal_progress_unchanged()
                    resumed = command("/api/preview", enabled=False)
                    self.assertFalse(resumed["preview_mode"])
                    self.assertEqual(resumed["attempt_id"], normal["attempt_id"])
                    self.assertEqual(resumed["scenario_image"], normal["scenario_image"])
                    assert_formal_progress_unchanged()
                finally:
                    server.shutdown()
                    thread.join(timeout=5)
                    server.server_close()


if __name__ == "__main__":
    unittest.main()
