"""Pure runtime gate for canonical teaching candidates."""

from typing import Literal, Self

from pydantic import model_validator

from .contracts import Activity, ContentPack, ContractModel, StableId
from .evaluation import (
    CausalSceneEvidence,
    ChoiceEvidence,
    ClassificationEvidence,
    Evaluation,
    LearnerEvidence,
    evaluate_choice,
)


TeachingStrategy = Literal[
    "elicit",
    "socratic_hint",
    "clarify",
    "direct_instruction",
    "reflect",
    "advance",
    "hold",
]
SelectionScope = Literal["tutor_selectable", "runtime_only"]
SelectorKind = Literal[
    "baseline",
    "tutor",
    "unsupported_request",
    "recovery",
    "timeout",
    "provider_failure",
    "invalid_output",
]
SupportRequestKind = Literal[
    "orientation",
    "clarification",
    "explanation",
    "accessibility",
    "do_not_know",
]
SELECTOR_VERSION = "4.1.0"
FIXED_POLICY_VERSION = SELECTOR_VERSION


class TeachingMove(ContractModel):
    """One bounded move containing no generated prose or progression target."""

    strategy: TeachingStrategy
    resource_id: StableId | None = None

    @model_validator(mode="after")
    def validate_resource(self) -> Self:
        if self.strategy in {"advance", "hold"} and self.resource_id is not None:
            raise ValueError(f"{self.strategy} cannot carry a resource_id")
        if self.strategy not in {"advance", "hold"} and self.resource_id is None:
            raise ValueError("a learner-visible move requires a resource_id")
        return self


class TeachingCandidate(ContractModel):
    """One canonical move with an explicit selection authority."""

    candidate_id: StableId
    move: TeachingMove
    selection_scope: SelectionScope

    @model_validator(mode="after")
    def validate_scope(self) -> Self:
        if self.move.strategy == "hold" and self.selection_scope != "runtime_only":
            raise ValueError("hold must be runtime_only")
        if self.move.strategy != "hold" and self.selection_scope != "tutor_selectable":
            raise ValueError("learner-facing candidates must be tutor_selectable")
        return self


def teaching_candidates(
    pack: ContentPack,
    evidence: ChoiceEvidence,
    *,
    curriculum_requirements_met: bool,
) -> tuple[TeachingCandidate, ...]:
    """Build tutor-selectable candidates plus the runtime-only hold fallback."""

    if type(curriculum_requirements_met) is not bool:
        raise TypeError("curriculum_requirements_met must be a boolean")

    evaluation = evaluate_choice(pack, evidence)
    activity = next(
        item for item in pack.activities if item.activity_id == evidence.activity_id
    )

    return scored_teaching_candidates(
        activity,
        evidence,
        evaluation,
        curriculum_requirements_met=curriculum_requirements_met,
        support_level=0,
        support_budget=_support_budget(activity),
    )


def scored_teaching_candidates(
    activity: Activity,
    evidence: LearnerEvidence,
    evaluation: Evaluation,
    *,
    curriculum_requirements_met: bool,
    support_level: int,
    support_budget: int,
    requires_reflection: bool = False,
) -> tuple[TeachingCandidate, ...]:
    """Build the legal candidates for one scored response."""

    _validate_support_state(support_level, support_budget)
    if requires_reflection:
        move = TeachingMove(
            strategy="reflect",
            resource_id=evaluation.consequence_resource_id,
        )
    elif not evaluation.accepted:
        if isinstance(evidence, CausalSceneEvidence):
            move = TeachingMove(
                strategy="direct_instruction",
                resource_id=activity.explanation_resource_id,
            )
            return (_tutor_candidate(move), runtime_hold_candidate())
        choice = next(
            (
                item
                for item in activity.choices
                if item.option_id == _selected_option_id(evidence)
            ),
            None,
        )
        if choice is None:
            raise ValueError(f"unknown response ID: {_selected_option_id(evidence)}")
        if support_level < len(choice.hint_resource_ids):
            move = TeachingMove(
                strategy="socratic_hint",
                resource_id=choice.hint_resource_ids[support_level],
            )
        else:
            move = TeachingMove(
                strategy="direct_instruction",
                resource_id=activity.explanation_resource_id,
            )
    elif not curriculum_requirements_met:
        move = TeachingMove(
            strategy="elicit",
            resource_id=activity.question_resource_id,
        )
    else:
        move = TeachingMove(strategy="advance")
    return (_tutor_candidate(move), runtime_hold_candidate())


def support_teaching_candidates(
    activity: Activity,
    request_kind: SupportRequestKind,
) -> tuple[TeachingCandidate, ...]:
    """Build legal candidates for an explicit unscored support request."""

    if request_kind == "orientation":
        move = TeachingMove(
            strategy="elicit",
            resource_id=activity.question_resource_id,
        )
    elif request_kind == "clarification":
        move = TeachingMove(
            strategy="clarify",
            resource_id=activity.question_resource_id,
        )
    else:
        move = TeachingMove(
            strategy="direct_instruction",
            resource_id=activity.explanation_resource_id,
        )
    return (_tutor_candidate(move), runtime_hold_candidate())


def message_teaching_candidates(
    activity: Activity,
    *,
    support_level: int,
    support_budget: int,
) -> tuple[TeachingCandidate, ...]:
    """Build bounded choices for an unscored natural-language learner message."""

    _validate_support_state(support_level, support_budget)
    candidates = [
        _tutor_candidate(
            TeachingMove(
                strategy="clarify",
                resource_id=activity.question_resource_id,
            )
        ),
        _tutor_candidate(
            TeachingMove(
                strategy="direct_instruction",
                resource_id=activity.explanation_resource_id,
            )
        ),
    ]
    return (*candidates, runtime_hold_candidate())


def gate_reused_direct_instruction(
    candidates: tuple[TeachingCandidate, ...],
    *,
    used_resource_ids: frozenset[StableId],
    clarify_resource_id: StableId,
) -> tuple[TeachingCandidate, ...]:
    """Remove explanations already used in the current activity attempt.

    The gate always leaves a legal learner-visible move. When a repeated direct
    instruction was the only tutor choice, a grounded clarify move replaces it.
    """

    gated = tuple(
        candidate
        for candidate in candidates
        if not (
            candidate.move.strategy == "direct_instruction"
            and candidate.move.resource_id in used_resource_ids
        )
    )
    if gated == candidates or any(
        candidate.selection_scope == "tutor_selectable" for candidate in gated
    ):
        return gated
    clarify = _tutor_candidate(
        TeachingMove(strategy="clarify", resource_id=clarify_resource_id)
    )
    return (clarify, *gated)


def allowed_teaching_moves(
    pack: ContentPack,
    evidence: ChoiceEvidence,
    *,
    curriculum_requirements_met: bool,
) -> tuple[TeachingMove, ...]:
    """Return only candidates that a normal tutor may select."""

    return tuple(
        candidate.move
        for candidate in teaching_candidates(
            pack,
            evidence,
            curriculum_requirements_met=curriculum_requirements_met,
        )
        if candidate.selection_scope == "tutor_selectable"
    )


def runtime_hold_candidate() -> TeachingCandidate:
    """Return the single canonical fallback that is never tutor-selectable."""

    return TeachingCandidate(
        candidate_id="runtime.hold",
        move=TeachingMove(strategy="hold"),
        selection_scope="runtime_only",
    )


def validate_teaching_candidate(
    pack: ContentPack,
    evidence: ChoiceEvidence,
    candidate: TeachingCandidate,
    *,
    curriculum_requirements_met: bool,
    selector_kind: SelectorKind,
) -> TeachingCandidate:
    """Return an exact canonical candidate allowed for the selector authority."""

    for allowed in teaching_candidates(
        pack,
        evidence,
        curriculum_requirements_met=curriculum_requirements_met,
    ):
        if candidate == allowed:
            return _validate_selection_scope(allowed, selector_kind)
    raise ValueError("teaching candidate is not canonical for the current evidence")


def validate_candidate_membership(
    candidates: tuple[TeachingCandidate, ...],
    candidate: TeachingCandidate,
    *,
    selector_kind: SelectorKind,
) -> TeachingCandidate:
    """Validate exact membership and selector authority for any current turn."""

    for allowed in candidates:
        if candidate == allowed:
            return _validate_selection_scope(allowed, selector_kind)
    raise ValueError("teaching candidate is not canonical for the current turn")


def validate_runtime_hold(
    candidate: TeachingCandidate,
    *,
    selector_kind: Literal[
        "unsupported_request",
        "recovery",
        "timeout",
        "provider_failure",
        "invalid_output",
    ],
) -> TeachingCandidate:
    """Validate the canonical hold for a declared runtime-only path."""

    if candidate != runtime_hold_candidate():
        raise ValueError("runtime fallback is not the canonical hold candidate")
    return _validate_selection_scope(candidate, selector_kind)


def _validate_selection_scope(
    candidate: TeachingCandidate,
    selector_kind: SelectorKind,
) -> TeachingCandidate:
    if selector_kind in {"baseline", "tutor"}:
        required_scope = "tutor_selectable"
    elif selector_kind in {
        "unsupported_request",
        "recovery",
        "timeout",
        "provider_failure",
        "invalid_output",
    }:
        required_scope = "runtime_only"
    else:
        raise ValueError(f"unknown selector_kind: {selector_kind}")

    if candidate.selection_scope != required_scope:
        raise ValueError(
            f"{selector_kind} cannot select {candidate.selection_scope} candidates"
        )
    return candidate


def _candidate_id(move: TeachingMove) -> StableId:
    if move.resource_id is None:
        return f"tutor.{move.strategy}"
    return f"tutor.{move.strategy}.{move.resource_id}"


def _selected_option_id(evidence: LearnerEvidence) -> StableId:
    if isinstance(evidence, ChoiceEvidence):
        return evidence.option_id
    if isinstance(evidence, ClassificationEvidence):
        return evidence.classification_id
    raise ValueError("causal-scene evidence has no selected option")


def _tutor_candidate(move: TeachingMove) -> TeachingCandidate:
    return TeachingCandidate(
        candidate_id=_candidate_id(move),
        move=move,
        selection_scope="tutor_selectable",
    )


def _support_budget(activity: Activity) -> int:
    return max(
        (len(choice.hint_resource_ids) for choice in activity.choices),
        default=0,
    )


def _validate_support_state(support_level: int, support_budget: int) -> None:
    if type(support_level) is not int or type(support_budget) is not int:
        raise TypeError("support level and budget must be integers")
    if support_level < 0 or support_budget < 0 or support_level > support_budget:
        raise ValueError("support level must be within the support budget")


def _teaching_move_for_evaluation(
    activity: Activity,
    evidence: LearnerEvidence,
    evaluation: Evaluation,
    *,
    curriculum_requirements_met: bool,
) -> TeachingMove:
    """Derive the sole normal move from already-validated scored evidence."""

    if not evaluation.accepted:
        if isinstance(evidence, CausalSceneEvidence):
            return TeachingMove(
                strategy="direct_instruction",
                resource_id=activity.explanation_resource_id,
            )
        choice = next(
            item
            for item in activity.choices
            if item.option_id == _selected_option_id(evidence)
        )
        return TeachingMove(
            strategy="socratic_hint",
            resource_id=choice.hint_resource_ids[0],
        )
    if not curriculum_requirements_met:
        return TeachingMove(
            strategy="elicit",
            resource_id=activity.question_resource_id,
        )
    return TeachingMove(strategy="advance")


def validate_teaching_move(
    pack: ContentPack,
    evidence: ChoiceEvidence,
    candidate: TeachingMove,
    *,
    curriculum_requirements_met: bool,
) -> TeachingMove:
    """Return the canonical move only when the candidate exactly matches it."""

    for allowed in allowed_teaching_moves(
        pack,
        evidence,
        curriculum_requirements_met=curriculum_requirements_met,
    ):
        if candidate == allowed:
            return allowed
    raise ValueError("teaching move is not allowed for the current evidence and gate")
