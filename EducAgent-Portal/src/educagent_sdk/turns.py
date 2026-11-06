"""Pure resolution and rendering of validated headless tutor turns."""

from collections.abc import Iterable
from difflib import SequenceMatcher
from typing import Annotated

from pydantic import StringConstraints

from .contracts import (
    Activity,
    ContentPack,
    ContractModel,
    NonEmptyText,
    SemanticVersion,
    StableId,
)
from .release import validate_release
from .runtime import TeachingCandidate, TeachingMove, TeachingStrategy


FRAMING_CATALOG_VERSION: SemanticVersion = "2.1.0"
MAX_TUTOR_REPLY_CHARS = 1200
SocraticQuestion = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=4000),
]
TutorReply = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_TUTOR_REPLY_CHARS),
]
QUESTION_CAPABLE_STRATEGIES = frozenset(
    {"elicit", "socratic_hint", "clarify", "reflect"}
)

_FRAMING_IDS = {
    "elicit": "framing.elicit.question",
    "socratic_hint": "framing.socratic-hint.retry",
    "clarify": "framing.clarify.focus",
    "direct_instruction": "framing.direct-instruction.retry",
    "reflect": "framing.reflect.revise",
    "advance": "framing.advance.continue",
    "hold": "framing.hold.saved",
}


class ResolvedTutorTurn(ContractModel):
    """Replay-stable references derived from one validated candidate."""

    activity_id: StableId
    candidate_id: StableId
    move: TeachingMove
    framing_catalog_version: SemanticVersion
    framing_id: StableId
    grounding_resource_ids: tuple[StableId, ...]
    grounding_claim_ids: tuple[StableId, ...]
    expected_evidence_predicate_ids: tuple[StableId, ...]


class RenderedTutorTurn(ContractModel):
    """Fixed learner-visible text composed without a model call."""

    resolved: ResolvedTutorTurn
    text: NonEmptyText


def resolve_tutor_turn(
    pack: ContentPack,
    activity_id: StableId,
    candidate: TeachingCandidate,
) -> ResolvedTutorTurn:
    """Resolve framing, grounding closure, and expected evidence from a candidate."""

    validate_release(pack)
    activity = next(
        (item for item in pack.activities if item.activity_id == activity_id),
        None,
    )
    if activity is None:
        raise ValueError(f"unknown activity_id: {activity_id}")

    move = candidate.move
    resource_ids = grounding_resource_ids_for_move(activity, move)

    resources = {resource.resource_id: resource for resource in pack.resources}
    unknown = [resource_id for resource_id in resource_ids if resource_id not in resources]
    if unknown:
        raise ValueError(f"candidate references unknown resources: {', '.join(unknown)}")

    claim_ids = tuple(
        dict.fromkeys(
            claim_id
            for resource_id in resource_ids
            for claim_id in resources[resource_id].claim_ids
        )
    )
    return ResolvedTutorTurn(
        activity_id=activity_id,
        candidate_id=candidate.candidate_id,
        move=move,
        framing_catalog_version=FRAMING_CATALOG_VERSION,
        framing_id=framing_id_for_move(move),
        grounding_resource_ids=resource_ids,
        grounding_claim_ids=claim_ids,
        expected_evidence_predicate_ids=expected_evidence_for_move(move),
    )


def compose_tutor_turn(
    pack: ContentPack,
    resolved: ResolvedTutorTurn,
    *,
    socratic_question: SocraticQuestion | None = None,
    tutor_reply: TutorReply | None = None,
    allow_legacy_clarify: bool = False,
) -> RenderedTutorTurn:
    """Compose a grounded move with optional bounded tutor wording."""

    scope = "runtime_only" if resolved.move.strategy == "hold" else "tutor_selectable"
    canonical = resolve_tutor_turn(
        pack,
        resolved.activity_id,
        TeachingCandidate(
            candidate_id=resolved.candidate_id,
            move=resolved.move,
            selection_scope=scope,
        ),
    )
    if resolved != canonical:
        raise ValueError("resolved turn does not match the framing and grounding catalog")

    activity = _activity_for_id(pack, resolved.activity_id)
    question = validate_socratic_question(
        socratic_question,
        resolved.move.strategy,
        answer_labels=(choice.text for choice in activity.choices),
        allow_legacy_clarify=allow_legacy_clarify,
    )

    if tutor_reply is not None:
        return RenderedTutorTurn(resolved=resolved, text=tutor_reply)

    resources = {resource.resource_id: resource for resource in pack.resources}
    texts = [
        activity.workbench.prompt
        if (activity.experiment is not None and activity.workbench is not None
            and activity.workbench.prompt is not None
            and resource_id == activity.question_resource_id)
        else resources[resource_id].text
        for resource_id in resolved.grounding_resource_ids
    ]
    strategy = resolved.move.strategy
    if strategy == "elicit":
        text = question or texts[0]
    elif strategy == "socratic_hint":
        text = question or texts[0]
    elif strategy == "clarify":
        text = question or texts[0]
    elif strategy == "direct_instruction":
        text = texts[0]
    elif strategy == "reflect":
        text = _join_prompt(texts[0], question)
    elif strategy == "advance":
        text = "Your response meets the current requirement. Let's continue."
    else:
        text = (
            "I couldn't produce a grounded reply for this turn. Your response "
            "was saved; use the released explanation or record your judgment."
        )
    return RenderedTutorTurn(resolved=resolved, text=text)


def validate_socratic_question(
    question: SocraticQuestion | None,
    strategy: TeachingStrategy,
    *,
    answer_labels: Iterable[str] = (),
    allow_legacy_clarify: bool = False,
) -> SocraticQuestion | None:
    """Accept only one short, non-answer-revealing question from the tutor."""

    if question is None:
        return None
    if strategy == "clarify" and allow_legacy_clarify:
        return question
    if strategy not in QUESTION_CAPABLE_STRATEGIES:
        raise ValueError("a Socratic question is not legal for this teaching strategy")
    question_marks = question.count("?") + question.count("？")
    if "\n" in question or question_marks != 1 or not question.endswith(("?", "？")):
        raise ValueError("a Socratic question must be one line ending in one question mark")
    core = question.rstrip("?？")
    words = core.split()
    has_cjk = any("一" <= character <= "鿿" for character in core)
    if has_cjk:
        if not 3 <= len(core) <= 60:
            raise ValueError("a Socratic question must contain three to sixty characters")
    elif not 3 <= len(words) <= 32:
        raise ValueError("a Socratic question must contain three to thirty-two words")
    prohibited = {"answer", "correct", "option", "select", "solution"}
    if prohibited & {word.strip(".,:;!?'\"").lower() for word in words}:
        raise ValueError("a Socratic question must not reveal or name an answer")
    normalized_question = _normalized_words(question)
    for label in answer_labels:
        normalized_label = _normalized_words(label)
        if normalized_label and normalized_label in normalized_question:
            raise ValueError("a Socratic question must not repeat an answer label")
    return question


def validate_socratic_question_focus(
    question: SocraticQuestion | None,
    strategy: TeachingStrategy,
    *,
    answer_labels: Iterable[str] = (),
    activity_question: str,
    previous_questions: Iterable[str] = (),
    allow_legacy_clarify: bool = False,
) -> SocraticQuestion | None:
    """Validate a question's shape and ensure it changes the teaching focus."""

    validated = validate_socratic_question(
        question,
        strategy,
        answer_labels=answer_labels,
        allow_legacy_clarify=allow_legacy_clarify,
    )
    if strategy == "clarify" and allow_legacy_clarify:
        return validated
    if validated is None:
        return None
    if _questions_are_similar(validated, activity_question):
        raise ValueError("a Socratic question must not repeat the current activity question")
    if any(
        _questions_are_similar(validated, previous)
        for previous in previous_questions
    ):
        raise ValueError("a Socratic question must not repeat a prior teaching focus")
    return validated


def _join_prompt(text: str, question: SocraticQuestion | None) -> str:
    return text if question is None else f"{text}\n\n{question}"


def _activity_for_id(pack: ContentPack, activity_id: StableId) -> Activity:
    return next(
        activity
        for activity in pack.activities
        if activity.activity_id == activity_id
    )


def _normalized_words(text: str) -> str:
    return " ".join(
        "".join(character if character.isalnum() else " " for character in text.casefold()).split()
    )


def _questions_are_similar(left: str, right: str) -> bool:
    """Reject exact and near-duplicate teaching focuses without a provider call."""

    normalized_left = _normalized_words(left)
    normalized_right = _normalized_words(right)
    if normalized_left == normalized_right:
        return True
    left_tokens = set(normalized_left.split())
    right_tokens = set(normalized_right.split())
    union = left_tokens | right_tokens
    token_overlap = len(left_tokens & right_tokens) / len(union) if union else 1.0
    sequence_overlap = SequenceMatcher(
        None,
        normalized_left,
        normalized_right,
    ).ratio()
    return token_overlap >= 0.62 or sequence_overlap >= 0.78


def framing_id_for_move(move: TeachingMove) -> StableId:
    return _FRAMING_IDS[move.strategy]


def grounding_resource_ids_for_move(
    activity: Activity,
    move: TeachingMove,
) -> tuple[StableId, ...]:
    if move.strategy == "direct_instruction":
        assert move.resource_id is not None
        return (move.resource_id, activity.question_resource_id)
    if move.resource_id is not None:
        return (move.resource_id,)
    return ()


def expected_evidence_for_move(move: TeachingMove) -> tuple[StableId, ...]:
    if move.strategy == "advance":
        return ("attempt.completed",)
    if move.strategy == "reflect":
        return ("learner.revision",)
    return ("learner.new-action",)
