from __future__ import annotations

from datetime import datetime, timezone
import uuid

import pytest

from src.services.auth.db import LearnerProfile
from src.services.learner_adaptation import (
    DEFAULT_PROFILE_SIG,
    derive_learner_adaptation,
)


@pytest.fixture
def learner_profile() -> LearnerProfile:
    return LearnerProfile(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        background="Biology student with wet-lab experience",
        role="Student learning causal inference for experiments",
        prior_knowledge=["probability_statistics"],
        expertise_level="knows_correlation_confounding",
        learning_goal="Understand experimental design better",
        is_skipped=False,
        created_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
    )


@pytest.mark.asyncio
async def test_derive_learner_adaptation_sanitizes_pii(monkeypatch, learner_profile):
    async def fake_complete(**_kwargs):
        return """
        {
          "profile_sig": "biologist",
          "adaptation_ctx": {
            "background_summary": "Biology learner at Example University",
            "role_summary": "Student learning experiment design",
            "prior_knowledge": ["probability_statistics"],
            "expertise_level": "knows_correlation_confounding",
            "learning_goal_summary": "Reach me at learner@example.com",
            "domain_framing": "biology"
          }
        }
        """

    monkeypatch.setattr("src.services.learner_adaptation.complete", fake_complete)

    derivation = await derive_learner_adaptation(learner_profile)

    assert derivation.profile_sig == "biologist"
    assert derivation.adaptation_ctx.background_summary is None
    assert derivation.adaptation_ctx.learning_goal_summary is None
    assert derivation.adaptation_ctx.role_summary == "Student learning experiment design"


@pytest.mark.asyncio
async def test_derive_learner_adaptation_falls_back_on_invalid_output(
    monkeypatch,
    learner_profile,
):
    async def fake_complete(**_kwargs):
        return '{"profile_sig":"history"}'

    monkeypatch.setattr("src.services.learner_adaptation.complete", fake_complete)

    derivation = await derive_learner_adaptation(learner_profile)

    assert derivation.profile_sig == DEFAULT_PROFILE_SIG
    assert derivation.adaptation_ctx.prior_knowledge == ["probability_statistics"]
