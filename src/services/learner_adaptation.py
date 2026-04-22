from __future__ import annotations

from datetime import datetime, timezone
import json
import re
from typing import Literal, TypeAlias

from pydantic import BaseModel, Field, ValidationError

from src.logging import get_logger
from src.services.auth.db import LearnerProfile
from src.services.auth.schemas import LearnerAdaptationContext
from src.services.llm import complete

ProfileSig: TypeAlias = Literal["default", "bio", "cs", "econ"]
PROFILE_SIG_VALUES: tuple[ProfileSig, ...] = ("default", "bio", "cs", "econ")
DEFAULT_PROFILE_SIG: ProfileSig = "default"
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
ORG_RE = re.compile(
    r"\b(?:university|college|institute|hospital|school|inc|llc|ltd|corp|company)\b",
    re.IGNORECASE,
)

logger = get_logger("LearnerAdaptation")


class LearnerAdaptationDerivation(BaseModel):
    profile_sig: ProfileSig = DEFAULT_PROFILE_SIG
    adaptation_ctx: LearnerAdaptationContext = Field(default_factory=LearnerAdaptationContext)


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = " ".join(value.split()).strip()
    return normalized or None


def _contains_disallowed_pii(value: str | None) -> bool:
    if not value:
        return False
    return bool(EMAIL_RE.search(value) or URL_RE.search(value) or ORG_RE.search(value))


def _sanitize_context(context: LearnerAdaptationContext) -> LearnerAdaptationContext:
    return LearnerAdaptationContext(
        background_summary=None
        if _contains_disallowed_pii(context.background_summary)
        else _normalize_text(context.background_summary),
        role_summary=None
        if _contains_disallowed_pii(context.role_summary)
        else _normalize_text(context.role_summary),
        prior_knowledge=list(context.prior_knowledge),
        expertise_level=_normalize_text(context.expertise_level),
        learning_goal_summary=None
        if _contains_disallowed_pii(context.learning_goal_summary)
        else _normalize_text(context.learning_goal_summary),
        domain_framing=None
        if _contains_disallowed_pii(context.domain_framing)
        else _normalize_text(context.domain_framing),
    )


def _default_context(learner_profile: LearnerProfile) -> LearnerAdaptationContext:
    return LearnerAdaptationContext(
        prior_knowledge=list(learner_profile.prior_knowledge or []),
        expertise_level=learner_profile.expertise_level,
    )


def build_default_adaptation(
    learner_profile: LearnerProfile | None,
) -> LearnerAdaptationDerivation:
    if learner_profile is None:
        return LearnerAdaptationDerivation()

    return LearnerAdaptationDerivation(
        profile_sig=DEFAULT_PROFILE_SIG,
        adaptation_ctx=_default_context(learner_profile),
    )


def _extract_json_payload(raw_response: str) -> dict:
    candidate = raw_response.strip()
    fenced_match = re.search(r"```(?:json)?\s*(\{[\s\S]*\})\s*```", candidate)
    if fenced_match:
        candidate = fenced_match.group(1)
    else:
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start != -1 and end != -1 and end >= start:
            candidate = candidate[start : end + 1]

    return json.loads(candidate)


def _build_prompt(learner_profile: LearnerProfile) -> str:
    learner_payload = {
        "background": learner_profile.background,
        "role": learner_profile.role,
        "prior_knowledge": learner_profile.prior_knowledge,
        "expertise_level": learner_profile.expertise_level,
        "learning_goal": learner_profile.learning_goal,
    }
    schema_hint = {
        "profile_sig": "default | bio | cs | econ",
        "adaptation_ctx": {
            "background_summary": "string or null",
            "role_summary": "string or null",
            "prior_knowledge": ["string"],
            "expertise_level": "string or null",
            "learning_goal_summary": "string or null",
            "domain_framing": "string or null",
        },
    }

    return (
        "Given this learner profile, classify it into a single routing key and produce "
        "a PII-free adaptation context for future content generation.\n\n"
        "Rules:\n"
        "- Output valid JSON only.\n"
        "- profile_sig must be exactly one of: default, bio, cs, econ.\n"
        "- adaptation_ctx must exclude names, emails, institutions, employer names, "
        "lab names, and any direct identifiers.\n"
        "- Use broad summaries, not verbatim copies.\n"
        "- If the domain is unclear, use profile_sig='default'.\n\n"
        f"Input profile:\n{json.dumps(learner_payload, ensure_ascii=True, indent=2)}\n\n"
        f"Output schema:\n{json.dumps(schema_hint, ensure_ascii=True, indent=2)}"
    )


async def derive_learner_adaptation(
    learner_profile: LearnerProfile | None,
) -> LearnerAdaptationDerivation:
    if learner_profile is None or learner_profile.is_skipped:
        return build_default_adaptation(learner_profile)

    if not any(
        [
            learner_profile.background,
            learner_profile.role,
            learner_profile.prior_knowledge,
            learner_profile.expertise_level,
            learner_profile.learning_goal,
        ]
    ):
        return build_default_adaptation(learner_profile)

    try:
        prompt = _build_prompt(learner_profile)
        raw_response = await complete(
            prompt=prompt,
            system_prompt=(
                "You classify learner profiles into a small routing key and return "
                "schema-valid JSON for application use."
            ),
            temperature=0,
        )
        payload = _extract_json_payload(raw_response)
        derivation = LearnerAdaptationDerivation.model_validate(payload)
        return LearnerAdaptationDerivation(
            profile_sig=derivation.profile_sig,
            adaptation_ctx=_sanitize_context(derivation.adaptation_ctx),
        )
    except (ValidationError, ValueError, TypeError, json.JSONDecodeError) as exc:
        logger.warning(f"Falling back to default learner adaptation after invalid output: {exc}")
    except Exception as exc:
        logger.warning(f"Falling back to default learner adaptation after derivation error: {exc}")

    return build_default_adaptation(learner_profile)


def build_adaptation_record_payload(
    derivation: LearnerAdaptationDerivation,
    *,
    source_profile_updated_at: datetime | None,
) -> dict:
    return {
        "profile_sig": derivation.profile_sig,
        "adaptation_ctx": derivation.adaptation_ctx.model_dump(),
        "generated_at": datetime.now(timezone.utc),
        "source_profile_updated_at": source_profile_updated_at,
    }
