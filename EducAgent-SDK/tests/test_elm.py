"""Tests for the concrete ELM proxy boundary without making network requests."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from educagent_sdk import (
    ELM_PROXY_BASE_URL,
    ElmSettings,
    build_elm_model,
    load_elm_settings,
)
from educagent_sdk.elm import _chat_settings, _read_dotenv


class ElmSettingsTests(unittest.TestCase):
    def test_loads_uppercase_dotenv_settings_without_changing_environment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text(
                "BASE_URL=https://elm.edina.ac.uk/api/v1/\n"
                "MODEL=meta-llama/Llama-3.3-70B-Instruct\n"
                "ELM_API_KEY='elm-example-key'\n",
                encoding="utf-8",
            )
            with patch.dict(os.environ, {}, clear=True):
                settings = load_elm_settings(path)

        self.assertEqual(settings.base_url, ELM_PROXY_BASE_URL)
        self.assertEqual(settings.model_name, "meta-llama/Llama-3.3-70B-Instruct")
        self.assertNotIn("elm-example-key", repr(settings))

    def test_environment_takes_precedence_and_model_can_be_overridden(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text(
                "base_url=https://invalid.example/v1\n"
                "model=wrong-model\n"
                "elm_api_key=wrong-key\n",
                encoding="utf-8",
            )
            environment = {
                "BASE_URL": ELM_PROXY_BASE_URL,
                "MODEL": "configured-model",
                "ELM_API_KEY": "elm-environment-key",
            }
            with patch.dict(os.environ, environment, clear=True):
                settings = load_elm_settings(path, model_name="one-off-model")

        self.assertEqual(settings.model_name, "one-off-model")
        self.assertEqual(settings.api_key, "elm-environment-key")

    def test_rejects_missing_or_non_elm_base_url_without_echoing_values(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "BASE_URL, MODEL, ELM_API_KEY"):
                load_elm_settings()
        with patch.dict(
            os.environ,
            {
                "BASE_URL": "https://not-elm.example/v1",
                "MODEL": "configured-model",
                "ELM_API_KEY": "elm-secret-value",
            },
            clear=True,
        ):
            with self.assertRaisesRegex(ValueError, "documented ELM proxy URL") as raised:
                load_elm_settings()
        self.assertNotIn("elm-secret-value", str(raised.exception))

    def test_parser_ignores_unrelated_values_and_accepts_export(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text(
                "UNRELATED=ignored\nexport MODEL=usable-model\n",
                encoding="utf-8",
            )
            values = _read_dotenv(path)

        self.assertEqual(values, {"model": "usable-model"})

    def test_gpt_five_chat_uses_non_reasoning_tool_compatibility_mode(self) -> None:
        self.assertEqual(
            _chat_settings("gpt-5.6-luna"),
            {"openai_reasoning_effort": "none"},
        )
        self.assertIsNone(_chat_settings("meta-llama/Llama-3.3-70B-Instruct"))
        model = build_elm_model(
            ElmSettings(
                base_url=ELM_PROXY_BASE_URL,
                model_name="gpt-5.6-luna",
                api_key="elm-example-key",
            )
        )
        self.assertEqual(
            getattr(model, "settings"),
            {"openai_reasoning_effort": "none"},
        )


if __name__ == "__main__":
    unittest.main()
