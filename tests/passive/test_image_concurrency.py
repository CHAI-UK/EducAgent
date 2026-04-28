"""Tests for parallel image generation (image.concurrency, fallback, ordering)."""

from __future__ import annotations

import asyncio
import base64
from pathlib import Path

import pytest

from src.agents.passive import graph as graph_mod

# A tiny valid 1x1 PNG — just used so the decode + file-write paths exercise
# real bytes. Content doesn't matter, only that it's non-empty.
_PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
)
_PNG_1X1_B64 = base64.b64encode(_PNG_1X1).decode()
_DATA_URL = f"data:image/png;base64,{_PNG_1X1_B64}"


class _FakeUsage:
    prompt_tokens = 5
    completion_tokens = 3
    total_tokens = 8


class _FakeMessage:
    def __init__(self, images: list[dict] | None) -> None:
        self.content = ""
        self.images = images

    def model_dump(self) -> dict:
        return {"content": self.content, "images": self.images}


class _FakeChoice:
    def __init__(self, images: list[dict] | None) -> None:
        self.finish_reason = "stop"
        self.message = _FakeMessage(images)


class _FakeResponse:
    def __init__(self, images: list[dict] | None) -> None:
        self.choices = [_FakeChoice(images)]
        self.usage = _FakeUsage()


class _TrackingImageClient:
    """Fake OpenAI client for the image path — tracks concurrency.

    Each call sleeps for ``delays_by_desc[desc]`` seconds (default 0) and
    returns a canned data URL. ``current_active`` / ``max_active`` expose the
    concurrency observed during the run.
    """

    def __init__(
        self,
        *,
        delays_by_desc: dict[str, float] | None = None,
        primary_returns_empty_for: set[str] | None = None,
    ) -> None:
        self.delays_by_desc = delays_by_desc or {}
        self.primary_returns_empty_for = primary_returns_empty_for or set()
        self.chat = self
        self.completions = self
        self.current_active = 0
        self.max_active = 0
        self.calls_by_model: dict[str, int] = {}
        self.calls_by_desc: dict[str, int] = {}

    async def create(self, *, messages, model, **kwargs):  # type: ignore[no-untyped-def]
        user = next(m["content"] for m in messages if m["role"] == "user")
        # The image_generation_brief embeds the description somewhere in the
        # prompt text — we don't care about exact shape, we just key on
        # substring match over desc.
        desc = next(
            (
                d
                for d in list(self.delays_by_desc) + list(self.primary_returns_empty_for)
                if d in user
            ),
            user[:40],
        )
        self.calls_by_model[model] = self.calls_by_model.get(model, 0) + 1
        self.calls_by_desc[desc] = self.calls_by_desc.get(desc, 0) + 1

        self.current_active += 1
        self.max_active = max(self.max_active, self.current_active)
        try:
            await asyncio.sleep(self.delays_by_desc.get(desc, 0))
            if model == "primary" and desc in self.primary_returns_empty_for:
                return _FakeResponse(images=None)
            return _FakeResponse(images=[{"image_url": {"url": _DATA_URL}}])
        finally:
            self.current_active -= 1


def _base_state(descs: list[str], user_id: str = "u_test", concept_id: str = "c_test") -> dict:
    return {
        "user_id": user_id,
        "concept_ctx": {"concept_id": concept_id},
        "image_prompts": [
            {
                "node_title": f"Node {i}",
                "description": d,
                "kind": "PEDAGOGICAL_IMAGE",
                "section": "",
            }
            for i, d in enumerate(descs)
        ],
    }


def _base_config(*, concurrency: int, fallback_model: str | None = None) -> dict:
    return {
        "api_key_env": "OPENROUTER_API_KEY",
        "base_url_env": "OPENROUTER_BASE_URL",
        "base_url_default": "https://openrouter.ai/api/v1",
        "request_timeout_s": 300,
        "heartbeat_interval_s": 15,
        "max_wait_s": 360,
        "outline": {"model": "x"},
        "content": {"model": "x"},
        "fact_check": {"enabled": False},
        "image": {
            "enabled": True,
            "mode": "inline",
            "model": "primary",
            "fallback_model": fallback_model,
            "concurrency": concurrency,
        },
    }


def test_image_concurrency_respected(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """With concurrency=2 and 4 slow prompts, max_active should stay at 2."""
    monkeypatch.setattr(graph_mod, "_config", _base_config(concurrency=2))
    monkeypatch.setattr(
        graph_mod,
        "get_passive_images_dir",
        lambda user_id, concept_id: tmp_path / user_id / concept_id / "imgs",
    )
    client = _TrackingImageClient(delays_by_desc={"d0": 0.05, "d1": 0.05, "d2": 0.05, "d3": 0.05})
    monkeypatch.setattr(graph_mod, "_get_client", lambda: client)

    out = asyncio.run(graph_mod.image_generator(_base_state(["d0", "d1", "d2", "d3"])))

    assert len(out["image_refs"]) == 4
    assert client.max_active == 2
    assert client.calls_by_model.get("primary") == 4


def test_image_concurrency_one_preserves_serial(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """concurrency=1 must keep max_active=1 (previous serial behavior)."""
    monkeypatch.setattr(graph_mod, "_config", _base_config(concurrency=1))
    monkeypatch.setattr(
        graph_mod,
        "get_passive_images_dir",
        lambda user_id, concept_id: tmp_path / user_id / concept_id / "imgs",
    )
    client = _TrackingImageClient(delays_by_desc={"d0": 0.02, "d1": 0.02, "d2": 0.02})
    monkeypatch.setattr(graph_mod, "_get_client", lambda: client)

    out = asyncio.run(graph_mod.image_generator(_base_state(["d0", "d1", "d2"])))

    assert len(out["image_refs"]) == 3
    assert client.max_active == 1


def test_image_output_order_matches_input_even_when_first_is_slow(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Prompt 0 is slowest but its image_ref / filename must still come first."""
    monkeypatch.setattr(graph_mod, "_config", _base_config(concurrency=3))
    monkeypatch.setattr(
        graph_mod,
        "get_passive_images_dir",
        lambda user_id, concept_id: tmp_path / user_id / concept_id / "imgs",
    )
    # Prompt 0 sleeps longest → it will finish last, but must still be img_00.
    client = _TrackingImageClient(
        delays_by_desc={"slow_one": 0.10, "fast_one": 0.01, "medium_one": 0.05}
    )
    monkeypatch.setattr(graph_mod, "_get_client", lambda: client)

    out = asyncio.run(
        graph_mod.image_generator(_base_state(["slow_one", "fast_one", "medium_one"]))
    )
    refs = out["image_refs"]

    assert [r["description"] for r in refs] == ["slow_one", "fast_one", "medium_one"]
    assert [Path(r["url"]).name for r in refs] == ["img_00.png", "img_01.png", "img_02.png"]


def test_image_fallback_still_fires_under_concurrency(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Primary returning empty images triggers fallback, counted in metrics."""
    monkeypatch.setattr(
        graph_mod, "_config", _base_config(concurrency=2, fallback_model="fallback")
    )
    monkeypatch.setattr(
        graph_mod,
        "get_passive_images_dir",
        lambda user_id, concept_id: tmp_path / user_id / concept_id / "imgs",
    )
    # Primary returns no images for "d_bad" → fallback must pick it up.
    client = _TrackingImageClient(primary_returns_empty_for={"d_bad"})
    monkeypatch.setattr(graph_mod, "_get_client", lambda: client)

    out = asyncio.run(graph_mod.image_generator(_base_state(["d_ok", "d_bad"])))

    assert len(out["image_refs"]) == 2
    models_used = sorted(r["model"] for r in out["image_refs"])
    assert models_used == ["fallback", "primary"]
    assert client.calls_by_model.get("fallback") == 1
    assert client.calls_by_model.get("primary") == 2


def test_image_survives_malformed_response_shapes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Provider can return ``choices=None``, ``image_url=None``, etc. — must not crash.

    Reproduces the learner_1/interventions run symptom where gpt-5.4-image-2
    intermittently returned malformed response shapes and our loop raised
    `'NoneType' object is not subscriptable` before falling back.
    """
    monkeypatch.setattr(
        graph_mod, "_config", _base_config(concurrency=2, fallback_model="fallback")
    )
    monkeypatch.setattr(
        graph_mod,
        "get_passive_images_dir",
        lambda user_id, concept_id: tmp_path / user_id / concept_id / "imgs",
    )

    class _NullChoices:
        """Response whose ``choices`` attr is literally None."""

        def __init__(self) -> None:
            self.choices = None

    class _ImageUrlIsNone:
        """Response whose ``message.images[0].image_url`` is explicitly None."""

        def __init__(self) -> None:
            msg = _FakeMessage(images=[{"image_url": None}])
            self.choices = [type("C", (), {"finish_reason": "stop", "message": msg})()]
            self.usage = _FakeUsage()

    class _MixedClient(_TrackingImageClient):
        """Primary returns malformed shapes; fallback succeeds."""

        async def create(self, *, messages, model, **kwargs):  # type: ignore[no-untyped-def]
            self.calls_by_model[model] = self.calls_by_model.get(model, 0) + 1
            self.current_active += 1
            self.max_active = max(self.max_active, self.current_active)
            try:
                if model == "primary":
                    # Alternate shape so both pathological branches are exercised
                    # across a run.
                    calls = self.calls_by_model[model]
                    return _NullChoices() if calls % 2 == 1 else _ImageUrlIsNone()
                return _FakeResponse(images=[{"image_url": {"url": _DATA_URL}}])
            finally:
                self.current_active -= 1

    client = _MixedClient()
    monkeypatch.setattr(graph_mod, "_get_client", lambda: client)

    out = asyncio.run(graph_mod.image_generator(_base_state(["d_a"])))
    # Primary returned malformed shapes twice, then fallback produced a valid
    # image. The single prompt should still end up as a success, never a crash.
    assert len(out["image_refs"]) == 1
    assert out["run_metrics"]["image"]["failed_count"] == 0


def test_image_failed_prompt_goes_to_failed_list(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """When both primary and fallback return no data, the prompt is marked failed."""
    monkeypatch.setattr(
        graph_mod, "_config", _base_config(concurrency=2, fallback_model="fallback")
    )
    monkeypatch.setattr(
        graph_mod,
        "get_passive_images_dir",
        lambda user_id, concept_id: tmp_path / user_id / concept_id / "imgs",
    )

    class _AlwaysEmpty(_TrackingImageClient):
        async def create(self, *, messages, model, **kwargs):  # type: ignore[no-untyped-def]
            self.current_active += 1
            self.max_active = max(self.max_active, self.current_active)
            try:
                return _FakeResponse(images=None)
            finally:
                self.current_active -= 1

    client = _AlwaysEmpty()
    monkeypatch.setattr(graph_mod, "_get_client", lambda: client)

    out = asyncio.run(graph_mod.image_generator(_base_state(["d_a"])))

    assert out["image_refs"] == []
    run_metrics = out["run_metrics"]["image"]
    assert run_metrics["failed_count"] == 1
    assert run_metrics["failed_prompts"][0]["description"] == "d_a"
