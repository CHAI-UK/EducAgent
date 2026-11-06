# EducAgent-SDK instructions

## Documentation map

- [`README.md`](README.md) is the public entry point for requirements, installation, build, test, and current capabilities.
- [`docs/goal.md`](docs/goal.md) is the canonical product boundary and design guideline.
- [`docs/implementation.md`](docs/implementation.md) is the canonical ordered implementation plan and exit criteria.
- [`docs/roadmap.md`](docs/roadmap.md) is the only source of truth for current progress and completion evidence.
- [`docs/study-protocol.md`](docs/study-protocol.md) freezes the M0 pilot comparison and analysis rules.

Before implementation, read `docs/goal.md`, the active step in `docs/roadmap.md`, and the matching section in `docs/implementation.md`. Keep step IDs synchronized across the two internal documents. Do not use `README.md` as a progress tracker.

## Working rules

- Speak with the user in Chinese. Write code, comments, and documentation in English.
- Use the Conda environment named `educagent-sdk`; do not create a project-local `.venv`.
- Build EducAgent as an agent-first system on Pydantic AI. Use the installed `building-pydantic-ai-agents` skill for Pydantic AI architecture and implementation work.
- Keep the safety kernel and default unit tests provider-independent. Use Pydantic AI `TestModel` or `FunctionModel` in tests; never require live credentials or network access in the default suite.
- Content packs own licensed subject matter, examples, hints, and explanations.
- The tutor agent owns pedagogical reasoning: how to interpret a learner turn and when to elicit, hint, explain, retry, reflect, or request advance.
- The runtime owns state transitions and append-only learning traces.
- The agent must return a typed proposal and must not mutate learner state, award correctness, or advance the curriculum directly.
- Correctness and `Evaluation.accepted` come only from an evaluator/domain extension, never from the tutor. M0 free-form learner text is unscored; the tutor may turn it only into a typed, traceable, non-authoritative hypothesis that affects selection among already-legal moves.
- Give the tutor only frozen value snapshots. Never place an event store, cursor, append callback, mutable session object, or other write capability in `TutorDeps`; treat learner text and retrieved material as low-trust data.
- Keep runtime-only fallback candidates out of `TutorDeps`, and validate candidate scope against `selector_kind` as well as candidate ID.
- Bind progression permission to the current pending accepted scored-evidence event. Unscored input and every non-advance move clear it.
- Ground learner-visible factual claims in released content resources, reviewed claims, or deterministic results.
- Prefer the Python standard library. Add an abstraction after a second real implementation needs it.
- Run `python -m unittest discover -s tests -v` with `PYTHONPATH=src` before handing off changes.

<!-- ASTRYX:START -->
Astryx v0.4.7 · 158 components
CLI: run every command as `npx astryx <cmd>` (shown below as `astryx ...`).

SETUP (once, in your app entry e.g. main.tsx) — without these, components render unstyled:
  import "@astryxdesign/core/reset.css";
  import "@astryxdesign/core/astryx.css";

WORKFLOW — discover, don't guess. Before writing UI:
1. `astryx build "<idea>"` — START HERE: returns a kit (closest [page] + [block]s + [component]s). No args = full playbook.
2. `astryx template <name> [--skeleton]` — scaffold the [page]/[block]s it named, or study their layout. Templates are reference code.
3. `astryx component <Name>` — props + examples for every component you use.

RULES:
- No <div> — components do all layout/spacing, page frame included.
- Frame first: read `astryx docs layout` before writing any page or screen — page frame, region widths, breakpoint behavior.
- Dense data = rows (Table, List/Item), never Card-wrapped list items; Card is for standalone widgets. Status = StatusDot/Token; Badge = counts only.
- Custom styling: component props first; else style/className with tokens — var(--color-*|--spacing-*|--radius-*). No raw hex/px. (No StyleX/Tailwind compiler here — don't use xstyle/utility classes.)
- Tokens for every value (`astryx docs tokens`). Brand/accent belongs in the theme (`astryx theme list` / `theme add <slug>`, or `astryx theme template` for a custom one) — never override --color-* in :root.
- SELF-CHECK before you finish: re-read the file and replace any raw <div>/<span> layout, imported .css/@apply, or hardcoded value (#hex, 16px) with the component or a token (var(--color-*|--spacing-*|…)). If unsure a component/prop exists, run `astryx component <Name>` / `astryx search "<thing>"`; don't hand-roll CSS.

MORE CLI:
  search "<query>"   find any component / hook / doc / template / block
  component --list   158 components by category
  template --list    page + block recipes
  docs <topic>       browser-support, cli-integrations, color, elevation, getting-started, icons, illustrations, internationalization, layout, migration, motion, principles, shape, spacing, styling-libraries, styling, theme, tokens, typography, working-with-ai
  swizzle <Name>     eject component source for deep customization
  upgrade --apply    run after any @astryxdesign/core bump
<!-- ASTRYX:END -->
