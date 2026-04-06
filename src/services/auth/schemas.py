from __future__ import annotations

from datetime import datetime
import uuid

from fastapi_users import schemas
from pydantic import Field, field_validator, model_validator

PRIOR_KNOWLEDGE_CHOICES = {
    "probability_statistics",
    "machine_learning",
    "correlation_vs_causation",
    "confounding_controls",
    "dags_causal_graphs",
    "experiments_ab_tests",
    "potential_outcomes",
    "interventions_do_calculus",
    "counterfactuals",
    "none",
}
EXPERTISE_LEVEL_CHOICES = {
    "new_to_causality",
    "knows_correlation_confounding",
    "reads_dags",
    "used_causal_methods",
    "comfortable_formal_scm",
}


class UserRead(schemas.BaseUser[uuid.UUID]):
    username: str
    first_name: str | None = None
    last_name: str | None = None
    institution: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class UserCreate(schemas.BaseUserCreate):
    username: str

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("username")
    @classmethod
    def username_required(cls, value: str) -> str:
        if not value:
            raise ValueError("Username is required")
        return value

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserUpdate(schemas.BaseUserUpdate):
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    institution: str | None = None

    @field_validator("username", "first_name", "last_name", "institution", mode="before")
    @classmethod
    def normalize_optional_strings(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class ProfileRead(UserRead):
    avatar_url: str | None = None
    learner_profile: "LearnerProfileRead | None" = None


class LearnerProfileBase(schemas.CreateUpdateDictModel):
    background: str | None = None
    role: str | None = None
    prior_knowledge: list[str] = Field(default_factory=list)
    expertise_level: str | None = None
    learning_goal: str | None = None

    @field_validator("background", "role", "learning_goal", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @field_validator("prior_knowledge", mode="before")
    @classmethod
    def normalize_prior_knowledge(cls, value: list[str] | None) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("Prior knowledge must be a list")

        normalized: list[str] = []
        for item in value:
            if not isinstance(item, str):
                raise ValueError("Prior knowledge items must be strings")
            token = item.strip()
            if not token:
                continue
            if token not in PRIOR_KNOWLEDGE_CHOICES:
                raise ValueError(f"Invalid prior knowledge option: {token}")
            if token not in normalized:
                normalized.append(token)
        return normalized

    @field_validator("expertise_level", mode="before")
    @classmethod
    def normalize_expertise_level(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            value = value.strip().lower()
            return value or None
        return value

    @field_validator("expertise_level")
    @classmethod
    def validate_expertise_level(cls, value: str | None) -> str | None:
        if value is not None and value not in EXPERTISE_LEVEL_CHOICES:
            raise ValueError("Expertise level must be a supported causal learning level")
        return value

    @model_validator(mode="after")
    def enforce_none_exclusivity(self) -> "LearnerProfileBase":
        if "none" in self.prior_knowledge:
            self.prior_knowledge = ["none"]
        return self


class LearnerProfileRead(LearnerProfileBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    is_skipped: bool


class LearnerProfileCreate(LearnerProfileBase):
    pass


class LearnerProfileUpdate(schemas.CreateUpdateDictModel):
    background: str | None = None
    role: str | None = None
    prior_knowledge: list[str] | None = None
    expertise_level: str | None = None
    learning_goal: str | None = None

    @field_validator("background", "role", "learning_goal", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        return LearnerProfileBase.normalize_optional_text.__func__(cls, value)

    @field_validator("prior_knowledge", mode="before")
    @classmethod
    def normalize_optional_prior_knowledge(
        cls,
        value: list[str] | None,
    ) -> list[str] | None:
        if value is None:
            return None
        return LearnerProfileBase.normalize_prior_knowledge.__func__(cls, value)

    @model_validator(mode="after")
    def enforce_optional_none_exclusivity(self) -> "LearnerProfileUpdate":
        if self.prior_knowledge is not None and "none" in self.prior_knowledge:
            self.prior_knowledge = ["none"]
        return self

    @field_validator("expertise_level", mode="before")
    @classmethod
    def normalize_expertise_level(cls, value: str | None) -> str | None:
        return LearnerProfileBase.normalize_expertise_level.__func__(cls, value)

    @field_validator("expertise_level")
    @classmethod
    def validate_expertise_level(cls, value: str | None) -> str | None:
        return LearnerProfileBase.validate_expertise_level.__func__(cls, value)


class ProfileUpdate(schemas.CreateUpdateDictModel):
    username: str
    first_name: str | None = None
    last_name: str | None = None
    institution: str | None = None

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        if not value:
            raise ValueError("Username is required")
        return value

    @field_validator("first_name", "last_name", "institution", mode="before")
    @classmethod
    def normalize_optional_profile_strings(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class ProfilePasswordUpdate(schemas.CreateUpdateDictModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_min_length(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters")
        return value


ProfileRead.model_rebuild()
