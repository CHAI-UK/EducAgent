# EducAgent Portal

Portal provides three causal reasoning courses, each in General and Medical
contexts: Causality foundations, Effect of an intervention, and Robust prediction
or generation. Activities combine questions, explanations, deterministic
experiments and a guided tutor. The runtime evaluates scored answers and records
progress; tutor dialogue does not award credit.

See the [main README](../README.md) for installation, shared ELM configuration,
local startup and deployment together with Learning and Nirvana.

## Structure

- `src/educagent_sdk/`: Python runtime, evaluation, tutor and HTTP service.
- `content/modules.json`: current course registry and content paths.
- `web/src/`: Portal frontend.
- `web/public/`: public illustrations and source notices.
- `examples/playable_demo.py`: service entry point.

From this directory, run `npm run web:check` to check frontend types and
`npm run web:build` to build the frontend. Do not edit `web/dist/` directly.

Portal uses anonymous browser-session progress, not user accounts. Keep its
data directory private and run one writer per directory. Course material is
educational and does not establish scientific approval or validated mastery.
