from __future__ import annotations

from pathlib import Path

from src.agents.passive.markers import parse_image_marker
from src.agents.passive.run import render_markdown
from src.agents.passive.text_normalization import normalize_llm_payload


def test_parse_image_marker_supports_typed_and_legacy_markers() -> None:
    assert parse_image_marker("[CONTEXT_IMAGE: A busy lab bench]") == (
        "CONTEXT_IMAGE",
        "A busy lab bench",
    )
    assert parse_image_marker("[PEDAGOGICAL_IMAGE: Split-screen diagram]") == (
        "PEDAGOGICAL_IMAGE",
        "Split-screen diagram",
    )
    assert parse_image_marker("[IMAGE: Legacy marker]") == (
        "PEDAGOGICAL_IMAGE",
        "Legacy marker",
    )


def test_normalize_llm_payload_decodes_overescaped_markdown() -> None:
    payload = [
        {
            "section": "Intro",
            "content": '> Line one\\n> Line two\\n\\nMath: $\\\\mathcal{C}$ and \\"quoted\\" text.',
            "markers": [],
        }
    ]

    normalized = normalize_llm_payload(payload)
    content = normalized[0]["content"]

    assert "> Line one\n> Line two" in content
    assert "\\n" not in content
    assert '\\"' not in content
    assert "$\\mathcal{C}$" in content


def test_render_markdown_normalizes_existing_overescaped_sections() -> None:
    result = {
        "concept_ctx": {"concept_id": "counterfactuals"},
        "nodes": [
            {
                "sections": [
                    {
                        "section": "Intro",
                        "content": "> Line one\\n> Line two\\n\\nEquation: $\\\\alpha$",
                        "markers": [],
                    }
                ]
            }
        ],
        "image_refs": [],
    }

    rendered = render_markdown(result, Path("."))

    assert "> Line one\n> Line two" in rendered
    assert "Equation: $\\alpha$" in rendered
    assert "\\n" not in rendered


def test_render_markdown_rewrites_user_asset_paths_to_api_outputs() -> None:
    course_dir = Path("data/user/learner_40/passive_courses/counterfactuals")
    result = {
        "concept_ctx": {"concept_id": "counterfactuals"},
        "nodes": [
            {
                "sections": [
                    {
                        "section": "Intro",
                        "content": "[CONTEXT_IMAGE: example figure]",
                        "markers": ["[CONTEXT_IMAGE: example figure]"],
                    }
                ]
            }
        ],
        "image_refs": [
            {
                "description": "example figure",
                "kind": "CONTEXT_IMAGE",
                "url": "/data/users/yyx/onProject/CHAI/EducAgent/data/user/learner_40/passive_courses/counterfactuals/imgs/img_00.png",
            }
        ],
    }

    rendered = render_markdown(result, course_dir)

    assert "![example figure](imgs/img_00.png)" in rendered
    assert "/data/users/yyx/onProject/CHAI/EducAgent" not in rendered
    assert "*example figure*" not in rendered


def test_normalize_llm_payload_mermaid_labels_use_html_breaks() -> None:
    payload = [
        {
            "section": "The Landscape of Causal Expressiveness",
            "content": (
                "```mermaid\n"
                "flowchart TD\n"
                "    A[Observational Distribution\n"
                "P(X)] -->|adds conditional\n"
                "independencies| B[Causal Graphical Model\n"
                "DAG + Markov Condition]\n"
                "```\n"
            ),
            "markers": [],
        }
    ]

    normalized = normalize_llm_payload(payload)
    content = normalized[0]["content"]

    assert "A[Observational Distribution<br/>P(X)]" in content
    assert "-->|adds conditional<br/>independencies|" in content
    assert "B[Causal Graphical Model<br/>DAG + Markov Condition]" in content


def test_normalize_llm_payload_standardizes_quiz_option_markers() -> None:
    payload = [
        {
            "section": "Check Your Understanding",
            "content": (
                "1. First question?\n\n"
                "   A) First option\n"
                "   B. Second option\n"
                "   C) Third option\n"
                "   D. Fourth option\n"
            ),
            "markers": [],
        }
    ]

    normalized = normalize_llm_payload(payload)
    content = normalized[0]["content"]

    assert "A. First option" in content
    assert "B. Second option" in content
    assert "C. Third option" in content
    assert "D. Fourth option" in content
    assert "A)" not in content
    assert "C)" not in content
