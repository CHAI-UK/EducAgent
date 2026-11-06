"""Concrete ELM proxy configuration for externally run tutor qualification."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from openai import AsyncOpenAI
from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.openai import OpenAIProvider


ELM_PROXY_BASE_URL = "https://elm.edina.ac.uk/api/v1"
_SETTING_NAMES = ("BASE_URL", "MODEL", "ELM_API_KEY")


@dataclass(frozen=True, repr=False)
class ElmSettings:
    """Validated ELM proxy settings; its representation never exposes the key."""

    base_url: str
    model_name: str
    api_key: str

    def __repr__(self) -> str:
        return (
            "ElmSettings("
            f"base_url={self.base_url!r}, model_name={self.model_name!r}, "
            "api_key='***redacted***')"
        )


def load_elm_settings(
    env_file: Path | None = None,
    *,
    model_name: str | None = None,
) -> ElmSettings:
    """Load ELM settings without mutating the process environment.

    Process environment values take precedence over the optional ``.env`` file.
    Both uppercase names and the lowercase spellings used in local ``.env``
    files are accepted.
    """

    file_values = _read_dotenv(env_file) if env_file is not None else {}
    values = {
        name: _setting_value(name, file_values)
        for name in _SETTING_NAMES
    }
    if model_name is not None:
        values["MODEL"] = model_name.strip()
    missing = tuple(name for name, value in values.items() if not value)
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"missing ELM setting(s): {joined}")

    base_url = values["BASE_URL"].rstrip("/")
    if base_url != ELM_PROXY_BASE_URL:
        raise ValueError(
            "BASE_URL must be the documented ELM proxy URL "
            f"{ELM_PROXY_BASE_URL}"
        )
    parsed = urlparse(base_url)
    if parsed.scheme != "https" or parsed.netloc != "elm.edina.ac.uk":
        raise ValueError("BASE_URL must use the ELM HTTPS proxy")

    return ElmSettings(
        base_url=base_url,
        model_name=values["MODEL"],
        api_key=values["ELM_API_KEY"],
    )


def build_elm_model(settings: ElmSettings) -> Model:
    """Build the Pydantic AI model bound to ELM's OpenAI-compatible proxy."""

    client = AsyncOpenAI(
        base_url=settings.base_url,
        api_key=settings.api_key,
        max_retries=0,
    )
    return OpenAIChatModel(
        settings.model_name,
        provider=OpenAIProvider(openai_client=client),
        settings=_chat_settings(settings.model_name),
    )


def _chat_settings(model_name: str) -> OpenAIChatModelSettings | None:
    """Keep GPT-5 reasoning off when the tutor uses Chat Completions tools.

    ELM's GPT-5 proxy rejects function tools while reasoning is enabled on the
    Chat Completions endpoint. Candidate selection is deliberately small and
    guarded, so disabling reasoning here preserves the compatible structured
    output route without moving correctness into the model.
    """

    if model_name.startswith("gpt-5"):
        return OpenAIChatModelSettings(openai_reasoning_effort="none")
    return None


def _setting_value(name: str, file_values: dict[str, str]) -> str:
    for candidate in (name, name.lower()):
        value = os.environ.get(candidate) or file_values.get(candidate.casefold())
        if value and value.strip():
            return value.strip()
    return ""


def _read_dotenv(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, raw_value = line.partition("=")
        key = key.removeprefix("export ").strip()
        if not separator or key.casefold() not in {
            name.casefold() for name in _SETTING_NAMES
        }:
            continue
        value = raw_value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key.casefold()] = value
    return values
