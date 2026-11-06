"""The lesson renderer must not silently redraw an unsupported causal topology."""

import json
import unittest

from pydantic import ValidationError

from educagent_sdk.contracts import LessonWorkedGraph


class LessonGraphLayoutTest(unittest.TestCase):
    def graph_data(self):
        return {
            "label": "Possible explanation",
            "nodes": [
                {"node_id": "cause", "label": "Common cause"},
                {"node_id": "first", "label": "First outcome"},
                {"node_id": "second", "label": "Second outcome"},
            ],
            "edges": [
                {"parent_id": "cause", "child_id": "first"},
                {"parent_id": "cause", "child_id": "second"},
            ],
            "note_resource_id": "example.graph-note",
        }

    def test_three_node_common_cause_fork_is_supported(self):
        graph = LessonWorkedGraph.model_validate_json(json.dumps(self.graph_data()))
        self.assertEqual({edge.parent_id for edge in graph.edges}, {"cause"})
        self.assertEqual({edge.child_id for edge in graph.edges}, {"first", "second"})

    def test_chain_is_rejected_instead_of_being_drawn_as_a_fork(self):
        data = self.graph_data()
        data["edges"][1]["parent_id"] = "first"
        with self.assertRaisesRegex(ValidationError, "three-node common-cause fork"):
            LessonWorkedGraph.model_validate_json(json.dumps(data))


if __name__ == "__main__":
    unittest.main()
