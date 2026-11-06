"""Second-domain proof: fractions reuse the generic runtime unchanged."""

import unittest
from pathlib import Path

from educagent_sdk import load_content_pack, replay, validate_release
from educagent_sdk.demo import DemoController


ROOT = Path(__file__).resolve().parents[1]
PACK_PATH = ROOT / "content" / "fractions_m0.json"


class PortabilityProofTest(unittest.TestCase):
    def test_fraction_pack_reuses_content_evaluation_runtime_and_renderer_boundaries(self) -> None:
        pack = load_content_pack(PACK_PATH)
        self.assertEqual(validate_release(pack).unused_resource_ids, ())

        demo = DemoController(pack)
        first = demo.start(session_id="fractions.session.01")
        self.assertEqual(first["question"], "Which fraction is larger: 1/3 or 1/5?")
        demo.respond(
            request_id="fractions.response.01",
            option_id="fraction.practice.one-third",
        )
        transfer = demo.continue_activity(request_id="fractions.continue.01")
        self.assertEqual(transfer["activity_id"], "unit-fraction.transfer.01")
        demo.respond(
            request_id="fractions.response.02",
            option_id="fraction.transfer.one-eighth",
        )
        complete = demo.continue_activity(request_id="fractions.continue.02")

        state = replay(demo.events)
        self.assertEqual(complete["status"], "completed")
        self.assertEqual(state.m1_ready_concept_ids, ("unit-fraction-order",))


if __name__ == "__main__":
    unittest.main()
