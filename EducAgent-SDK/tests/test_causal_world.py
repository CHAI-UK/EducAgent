"""Deterministic M1 causal-world and two-axis diagnosis contracts."""

import unittest

from educagent_sdk import (
    BinaryCausalWorld,
    BinaryRecord,
    CausalEdge,
    LearnerDagSubmission,
    StructuralEquation,
    diagnose_intervention_answer,
    estimate_adjusted_risk,
    evaluate_counterfactual,
    evaluate_world,
    is_valid_backdoor_adjustment_set,
)


def confounded_world() -> BinaryCausalWorld:
    return BinaryCausalWorld(
        world_id="m1.confounding-world.01",
        node_ids=("confounder", "treatment", "outcome"),
        exogenous_node_ids=("confounder",),
        edges=(
            CausalEdge(parent_id="confounder", child_id="treatment"),
            CausalEdge(parent_id="confounder", child_id="outcome"),
            CausalEdge(parent_id="treatment", child_id="outcome"),
        ),
        equations=(
            StructuralEquation(
                node_id="treatment", parent_ids=("confounder",), operator="copy"
            ),
            StructuralEquation(
                node_id="outcome",
                parent_ids=("confounder", "treatment"),
                operator="or",
            ),
        ),
    )


class CausalWorldTest(unittest.TestCase):
    def test_intervention_overrides_a_structural_equation(self) -> None:
        world = confounded_world()
        observed = evaluate_world(world, exogenous_values={"confounder": True})
        intervened = evaluate_world(
            world,
            exogenous_values={"confounder": True},
            interventions={"treatment": False},
        )
        self.assertEqual(observed, {"confounder": True, "treatment": True, "outcome": True})
        self.assertEqual(intervened, {"confounder": True, "treatment": False, "outcome": True})
        self.assertEqual(
            evaluate_counterfactual(
                world,
                abducted_exogenous_values={"confounder": False},
                interventions={"treatment": True},
            )["outcome"],
            True,
        )

    def test_dag_provenance_separates_model_and_reasoning_errors(self) -> None:
        world = confounded_world()
        submission = LearnerDagSubmission(
            artifact_id="m1.artifact.01",
            activity_id="m1.dag.01",
            world_id=world.world_id,
            node_ids=world.node_ids,
            edges=(
                CausalEdge(parent_id="confounder", child_id="treatment"),
                CausalEdge(parent_id="outcome", child_id="treatment"),
            ),
        )
        diagnosis = diagnose_intervention_answer(
            world,
            submission,
            exogenous_values={"confounder": True},
            interventions={"treatment": False},
            outcome_id="outcome",
            learner_outcome=False,
        )
        self.assertEqual(diagnosis.model_match, "mixed")
        self.assertEqual(diagnosis.reasoning_match, "incorrect_intervention_result")
        self.assertTrue(diagnosis.missing_edges)
        self.assertEqual(diagnosis.reversed_edges[0], CausalEdge(parent_id="treatment", child_id="outcome"))

    def test_backdoor_oracle_and_adjusted_estimation_are_deterministic(self) -> None:
        world = confounded_world()
        self.assertFalse(
            is_valid_backdoor_adjustment_set(
                world,
                treatment_id="treatment",
                outcome_id="outcome",
                adjustment_node_ids=(),
            )
        )
        self.assertTrue(
            is_valid_backdoor_adjustment_set(
                world,
                treatment_id="treatment",
                outcome_id="outcome",
                adjustment_node_ids=("confounder",),
            )
        )
        records = (
            BinaryRecord(values={"confounder": False, "treatment": False, "outcome": False}),
            BinaryRecord(values={"confounder": False, "treatment": True, "outcome": True}),
            BinaryRecord(values={"confounder": True, "treatment": False, "outcome": True}),
            BinaryRecord(values={"confounder": True, "treatment": True, "outcome": True}),
        )
        self.assertEqual(
            estimate_adjusted_risk(
                records,
                treatment_id="treatment",
                outcome_id="outcome",
                treatment_value=False,
                adjustment_node_ids=("confounder",),
            ),
            0.5,
        )


if __name__ == "__main__":
    unittest.main()
