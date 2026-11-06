# EducAgent Workspace Instructions

## Scope

Treat the directory containing this file as the umbrella project root. It contains the static Learning entry, the Portal learning experience, and the Nirvana research-framing prototype.

Communicate with the user in Chinese. Keep code, comments, commit messages, and project documentation in English.

## Start Here

Before changing code, read:

1. `EducAgent-Nirvana/README.md`
2. `EducAgent-Nirvana/docs/portfolio-conclusion.md`
3. The relevant track documentation:
   - Portal: `EducAgent-SDK/AGENTS.md`, then the files it requires.
   - Nirvana: `EducAgent-Nirvana/docs/nirvana-conclusion.md` and `EducAgent-Nirvana/ROADMAP.md`.
   - Shared navigation or integration: `EducAgent-Nirvana/docs/portal-conclusion.md`.

Read `EducAgent-Nirvana/goal.pptx` only when the task concerns the presentation or product direction not already captured in the Markdown documents.

## Project Map

| Area | Canonical source | Generated output |
| --- | --- | --- |
| Learning | `index.html`, `styles.css` | None; the root files are the entry page |
| Portal | `EducAgent-SDK/` and `EducAgent-SDK/web/src/` | `portal/` |
| Nirvana | `EducAgent-Nirvana/demo/` and `EducAgent-Nirvana/demo_server.py` | `nirvana/` |
| Shared media | Source assets under the two projects | `media/` |

Do not directly edit `portal/`, `nirvana/`, or `media/`. They are refreshed by `start-demo.ps1`; edit their canonical sources instead.

## Product Boundaries

- Learning is a compact resource list embedded in the future CHAI site, not a standalone marketing homepage. Preserve the light/dark switcher.
- Portal teaches the already-selected SDK Causality Foundations M0 content. Do not create a separate curriculum unless requested.
- Portal free-text tutoring uses guided local text replies with phase-visible scene context and same-attempt history; the legacy `--unguarded-tutor` flag still selects this path, not the former vanilla baseline or a qualified guarded policy. Scored responses, scene actions, progression, and replay still use the SDK runtime and evaluator.
- Nirvana uses `/api/frame` with a Pydantic AI structured result through shared ELM settings to classify new questions and draft task-specific Brief fields. Follow-up chat proposes field-level diffs requiring Accept/Reject; it must not auto-edit the Brief. Manual edits clear history and proposals, and accepted edits invalidate confirmation. Copy works for drafts as well as reviewed Briefs, preserves review status, and excludes pending proposals. Route shows a causal-applicability summary. `/api/chat` remains a legacy text-only endpoint. There is no persistence, evidence verification, external tool execution, or automatic DG Copilot import.
- Keep Portal learning state and Nirvana research state separate unless an integration task explicitly changes that boundary.

## Local Run

From `C:\Workspace\EducAgent`:

```powershell
rtk powershell -NoProfile -ExecutionPolicy Bypass -File .\start-demo.ps1 -Port 4173
```

Open:

- Learning: `http://127.0.0.1:4173/`
- Portal: `http://127.0.0.1:4173/portal/`
- Nirvana: `http://127.0.0.1:4173/nirvana/`
- Nirvana health: `http://127.0.0.1:8011/api/health`

Do not pass `-Reset` unless the user explicitly asks to clear local Portal progress. Before stopping a server, confirm the exact PID and command line; never kill a port or process family broadly.

## ELM Configuration

Portal and Nirvana share `EducAgent-SDK/.env` through `educagent_sdk.elm.load_elm_settings` and `build_elm_model`.

Expected variables are `BASE_URL`, `MODEL`, and `ELM_API_KEY`. Read the model from the environment rather than hard-coding it. Never print, log, commit, or expose the API key.

Keep default tests provider-independent. Make a live ELM request only when the user explicitly asks for live integration testing.

## Validation

Portal, from `EducAgent-SDK`:

```powershell
rtk conda run -n educagent-sdk cmd /c "set PYTHONPATH=src&& python -m unittest discover -s tests -v"
rtk npm run web:check
rtk npm run web:build
rtk git diff --check
```

Nirvana, from `EducAgent-Nirvana`:

```powershell
rtk conda run -n educagent-sdk python -m unittest discover -s tests -v
rtk node --check demo\app.js
```

For browser verification, use Chrome when it is available. Otherwise state clearly that the in-app Chromium browser was used; do not report it as Chrome. The user explicitly permits normal saved Portal progress for local student walkthroughs (2026-10-15); do not enter Testing preview by default. Use temporary state only when isolation is specifically needed, and remove only temporary artifacts created by the test. Do not reset progress without an explicit reset request.

## Working Rules

- Preserve unrelated changes. The SDK worktree may already be dirty; never reset or revert user work.
- Use `apply_patch` for hand-edited files and `rg` for searches.
- Prefer the smallest working change and existing dependencies over new abstractions or packages.
- Keep the interface compact, accessible, and visually consistent with the CHAI-inspired palette already in use.
- Update the relevant Markdown documentation when behavior, commands, or product boundaries change.
