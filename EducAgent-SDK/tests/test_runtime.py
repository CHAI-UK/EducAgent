import copy
import json
import unittest
from pathlib import Path

from pydantic import ValidationError

from educagent_sdk import (
    ChoiceEvidence,
    ContentPack,
    Evaluation,
    ReleaseValidationError,
    TeachingCandidate,
    TeachingMove,
    allowed_teaching_moves,
    evaluate_choice,
    load_content_pack,
    runtime_hold_candidate,
    teaching_candidates,
    validate_runtime_hold,
    validate_teaching_candidate,
    validate_teaching_move,
)


ROOT = Path(__file__).resolve().parents[1]
PACK_PATH = ROOT / "content" / "causality_m0.json"


def pack_data() -> dict:
    return json.loads(PACK_PATH.read_text(encoding="utf-8"))


def validate_pack(data: dict) -> ContentPack:
    return ContentPack.model_validate_json(json.dumps(data))


def evidence(option_id: str) -> ChoiceEvidence:
    return ChoiceEvidence(
        activity_id="observation-vs-intervention.01",
        option_id=option_id,
    )


class ChoiceEvaluationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.pack = load_content_pack(PACK_PATH)

    def test_evidence_accepts_only_stable_activity_and_option_ids(self) -> None:
        self.assertEqual(evidence("association-only").option_id, "association-only")

        invalid = (
            {"activity_id": "observation-vs-intervention.01"},
            {
                "activity_id": "observation-vs-intervention.01",
                "option_id": 0,
            },
            {
                "activity_id": "observation-vs-intervention.01",
                "option_id": "association-only",
                "accepted": True,
            },
            {
                "activity_id": "observation-vs-intervention.01",
                "option_id": "association-only",
                "advance": True,
            },
            {
                "activity_id": "observation-vs-intervention.01",
                "option_id": "association-only",
                "consequence_resource_id": "injected",
            },
        )
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValidationError):
                ChoiceEvidence.model_validate(value)

    def test_correct_and_incorrect_choices_return_exact_semantic_ids(self) -> None:
        accepted = evaluate_choice(self.pack, evidence("association-only"))
        rejected = evaluate_choice(
            self.pack,
            evidence("association-proves-intervention"),
        )

        self.assertEqual(
            accepted,
            Evaluation(
                accepted=True,
                misconception_id=None,
                consequence_resource_id=(
                    "observation-vs-intervention.consequence.accepted"
                ),
            ),
        )
        self.assertEqual(
            rejected,
            Evaluation(
                accepted=False,
                misconception_id="association-implies-intervention",
                consequence_resource_id=(
                    "observation-vs-intervention.consequence.rejected"
                ),
            ),
        )

        resources = {resource.resource_id: resource for resource in self.pack.resources}
        self.assertEqual(
            resources[accepted.consequence_resource_id].claim_ids,
            (
                "association-is-observational",
                "observation-does-not-identify-intervention",
            ),
        )

    def test_evaluation_contract_rejects_inconsistent_or_injected_verdicts(self) -> None:
        invalid = (
            {
                "accepted": True,
                "misconception_id": "injected",
                "consequence_resource_id": "resource",
            },
            {
                "accepted": False,
                "misconception_id": None,
                "consequence_resource_id": "resource",
            },
            {
                "accepted": True,
                "misconception_id": None,
                "consequence_resource_id": "resource",
                "licensed_claim_ids": ["injected"],
            },
        )
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValidationError):
                Evaluation.model_validate(value)

    def test_unknown_activity_and_option_ids_fail_closed(self) -> None:
        invalid = (
            ChoiceEvidence(activity_id="missing.activity", option_id="association-only"),
            evidence("missing-option"),
        )
        for value in invalid:
            with self.subTest(value=value), self.assertRaisesRegex(
                ValueError, "unknown (activity_id|option_id)"
            ):
                evaluate_choice(self.pack, value)

    def test_option_identity_is_independent_of_authored_order(self) -> None:
        data = pack_data()
        data["activities"][0]["choices"].reverse()
        reordered = validate_pack(data)

        self.assertEqual(
            evaluate_choice(reordered, evidence("association-only")),
            evaluate_choice(self.pack, evidence("association-only")),
        )
        self.assertEqual(
            evaluate_choice(
                reordered,
                evidence("association-proves-intervention"),
            ),
            evaluate_choice(
                self.pack,
                evidence("association-proves-intervention"),
            ),
        )

    def test_evaluation_requires_a_releasable_pack(self) -> None:
        data = pack_data()
        consequence_id = data["activities"][0]["choices"][0][
            "consequence_resource_id"
        ]
        next(
            resource
            for resource in data["resources"]
            if resource["resource_id"] == consequence_id
        )["release_status"] = "draft"

        with self.assertRaises(ReleaseValidationError):
            evaluate_choice(validate_pack(data), evidence("association-only"))


class TeachingMoveGateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.pack = load_content_pack(PACK_PATH)
        self.accepted = evidence("association-only")
        self.rejected = evidence("association-proves-intervention")

    def test_allowed_moves_follow_the_current_truth_table(self) -> None:
        cases = (
            (
                self.rejected,
                False,
                (
                    TeachingMove(
                        strategy="socratic_hint",
                        resource_id="observation-vs-intervention.hint.01",
                    ),
                ),
            ),
            (
                self.rejected,
                True,
                (
                    TeachingMove(
                        strategy="socratic_hint",
                        resource_id="observation-vs-intervention.hint.01",
                    ),
                ),
            ),
            (
                self.accepted,
                False,
                (
                    TeachingMove(
                        strategy="elicit",
                        resource_id="observation-vs-intervention.question.01",
                    ),
                ),
            ),
            (
                self.accepted,
                True,
                (TeachingMove(strategy="advance"),),
            ),
        )
        for learner_evidence, requirements_met, expected in cases:
            with self.subTest(
                evidence=learner_evidence,
                requirements_met=requirements_met,
            ):
                self.assertEqual(
                    allowed_teaching_moves(
                        self.pack,
                        learner_evidence,
                        curriculum_requirements_met=requirements_met,
                    ),
                    expected,
                )

    def test_curriculum_gate_requires_a_real_boolean(self) -> None:
        with self.assertRaisesRegex(TypeError, "must be a boolean"):
            allowed_teaching_moves(
                self.pack,
                self.accepted,
                curriculum_requirements_met=1,
            )

    def test_rejected_evidence_cannot_validate_advance(self) -> None:
        with self.assertRaisesRegex(ValueError, "not allowed"):
            validate_teaching_move(
                self.pack,
                self.rejected,
                TeachingMove(strategy="advance"),
                curriculum_requirements_met=True,
            )

    def test_accepted_evidence_still_requires_the_curriculum_gate(self) -> None:
        advance = TeachingMove(strategy="advance")
        with self.assertRaisesRegex(ValueError, "not allowed"):
            validate_teaching_move(
                self.pack,
                self.accepted,
                advance,
                curriculum_requirements_met=False,
            )

        self.assertEqual(
            validate_teaching_move(
                self.pack,
                self.accepted,
                advance,
                curriculum_requirements_met=True,
            ),
            advance,
        )

    def test_validation_returns_the_runtime_canonical_move(self) -> None:
        candidate = TeachingMove(
            strategy="elicit",
            resource_id="observation-vs-intervention.question.01",
        )

        validated = validate_teaching_move(
            self.pack,
            self.accepted,
            candidate,
            curriculum_requirements_met=False,
        )

        self.assertEqual(validated, candidate)
        self.assertIsNot(validated, candidate)

    def test_unrelated_or_wrong_role_resources_fail_closed(self) -> None:
        invalid = (
            (
                self.rejected,
                TeachingMove(
                    strategy="socratic_hint",
                    resource_id="observation-vs-intervention.explanation.01",
                ),
                False,
            ),
            (
                self.accepted,
                TeachingMove(
                    strategy="elicit",
                    resource_id="observation-vs-intervention.hint.01",
                ),
                False,
            ),
        )
        for learner_evidence, move, requirements_met in invalid:
            with self.subTest(move=move), self.assertRaisesRegex(
                ValueError, "not allowed"
            ):
                validate_teaching_move(
                    self.pack,
                    learner_evidence,
                    move,
                    curriculum_requirements_met=requirements_met,
                )

    def test_valid_resources_cannot_cross_evaluation_branches(self) -> None:
        invalid = (
            (
                self.rejected,
                TeachingMove(
                    strategy="elicit",
                    resource_id="observation-vs-intervention.question.01",
                ),
                False,
            ),
            (
                self.accepted,
                TeachingMove(
                    strategy="socratic_hint",
                    resource_id="observation-vs-intervention.hint.01",
                ),
                False,
            ),
            (
                self.accepted,
                TeachingMove(
                    strategy="elicit",
                    resource_id="observation-vs-intervention.question.01",
                ),
                True,
            ),
        )
        for learner_evidence, move, requirements_met in invalid:
            with self.subTest(move=move), self.assertRaisesRegex(
                ValueError, "not allowed"
            ):
                validate_teaching_move(
                    self.pack,
                    learner_evidence,
                    move,
                    curriculum_requirements_met=requirements_met,
                )

    def test_same_kind_resource_from_another_option_is_not_allowed(self) -> None:
        data = pack_data()
        hint = next(
            resource
            for resource in data["resources"]
            if resource["resource_id"] == "observation-vs-intervention.hint.01"
        )
        other_hint = copy.deepcopy(hint)
        other_hint["resource_id"] = "observation-vs-intervention.hint.02"
        data["resources"].append(other_hint)
        data["activities"][0]["choices"].append(
            {
                "option_id": "another-incorrect-option",
                "text": "The observed pattern identifies the reverse causal effect.",
                "correct": False,
                "misconception_id": "association-implies-reverse-intervention",
                "hint_resource_ids": ["observation-vs-intervention.hint.02"],
                "consequence_resource_id": (
                    "observation-vs-intervention.consequence.rejected"
                ),
            }
        )
        pack = validate_pack(data)

        with self.assertRaisesRegex(ValueError, "not allowed"):
            validate_teaching_move(
                pack,
                self.rejected,
                TeachingMove(
                    strategy="socratic_hint",
                    resource_id="observation-vs-intervention.hint.02",
                ),
                curriculum_requirements_met=False,
            )

    def test_move_contract_rejects_unknown_authority_fields(self) -> None:
        invalid = (
            {"strategy": "explain_then_advance"},
            {"strategy": "socratic_hint"},
            {
                "strategy": "advance",
                "resource_id": "observation-vs-intervention.hint.01",
            },
            {"strategy": "advance", "next_activity_id": "injected"},
            {"strategy": "advance", "free_text": "Move on."},
            {"strategy": "advance", "claim_ids": ["injected"]},
        )
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValidationError):
                TeachingMove.model_validate(value)

    def test_only_the_first_ordered_hint_is_revealed(self) -> None:
        data = pack_data()
        first_hint = next(
            resource
            for resource in data["resources"]
            if resource["resource_id"] == "observation-vs-intervention.hint.01"
        )
        second_hint = copy.deepcopy(first_hint)
        second_hint["resource_id"] = "observation-vs-intervention.hint.02"
        second_hint["text"] = "Compare the observed and assigned values again."
        data["resources"].append(second_hint)
        data["activities"][0]["choices"][1]["hint_resource_ids"] = [
            "observation-vs-intervention.hint.02",
            "observation-vs-intervention.hint.01",
        ]

        self.assertEqual(
            allowed_teaching_moves(
                validate_pack(data),
                self.rejected,
                curriculum_requirements_met=False,
            ),
            (
                TeachingMove(
                    strategy="socratic_hint",
                    resource_id="observation-vs-intervention.hint.02",
                ),
            ),
        )

    def test_option_from_another_activity_is_not_valid_evidence(self) -> None:
        data = pack_data()
        other_activity = copy.deepcopy(data["activities"][0])
        other_activity["activity_id"] = "observation-vs-intervention.02"
        other_activity["choices"][0]["option_id"] = "association-only.02"
        other_activity["choices"][1]["option_id"] = (
            "association-proves-intervention.02"
        )
        data["activities"].append(other_activity)
        data["concepts"][0]["completion_activity_ids"].append(
            "observation-vs-intervention.02"
        )
        pack = validate_pack(data)

        with self.assertRaisesRegex(ValueError, "unknown option_id"):
            evaluate_choice(
                pack,
                ChoiceEvidence(
                    activity_id="observation-vs-intervention.01",
                    option_id="association-only.02",
                ),
            )

    def test_gate_is_pure_and_repeatable(self) -> None:
        before = self.pack.model_dump(mode="json")

        first = allowed_teaching_moves(
            self.pack,
            self.rejected,
            curriculum_requirements_met=False,
        )
        second = allowed_teaching_moves(
            self.pack,
            self.rejected,
            curriculum_requirements_met=False,
        )

        self.assertEqual(first, second)
        self.assertEqual(self.pack.model_dump(mode="json"), before)

    def test_full_candidates_separate_tutor_and_runtime_authority(self) -> None:
        candidates = teaching_candidates(
            self.pack,
            self.rejected,
            curriculum_requirements_met=False,
        )

        self.assertEqual(len(candidates), 2)
        self.assertEqual(candidates[0].selection_scope, "tutor_selectable")
        self.assertEqual(candidates[0].move.strategy, "socratic_hint")
        self.assertEqual(candidates[1], runtime_hold_candidate())

    def test_selector_kind_enforces_candidate_scope(self) -> None:
        tutor_candidate, hold = teaching_candidates(
            self.pack,
            self.accepted,
            curriculum_requirements_met=True,
        )

        with self.assertRaisesRegex(ValueError, "cannot select"):
            validate_teaching_candidate(
                self.pack,
                self.accepted,
                hold,
                curriculum_requirements_met=True,
                selector_kind="baseline",
            )
        with self.assertRaisesRegex(ValueError, "cannot select"):
            validate_teaching_candidate(
                self.pack,
                self.accepted,
                tutor_candidate,
                curriculum_requirements_met=True,
                selector_kind="recovery",
            )

        self.assertEqual(
            validate_runtime_hold(hold, selector_kind="recovery"),
            hold,
        )

    def test_hold_contract_is_resource_free_and_runtime_only(self) -> None:
        invalid = (
            {"strategy": "hold", "resource_id": "injected"},
            {
                "candidate_id": "injected.hold",
                "move": {"strategy": "hold"},
                "selection_scope": "tutor_selectable",
            },
            {
                "candidate_id": "injected.hint",
                "move": {
                    "strategy": "socratic_hint",
                    "resource_id": "observation-vs-intervention.hint.01",
                },
                "selection_scope": "runtime_only",
            },
        )
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValidationError):
                if "candidate_id" in value:
                    TeachingCandidate.model_validate(value)
                else:
                    TeachingMove.model_validate(value)


if __name__ == "__main__":
    unittest.main()
