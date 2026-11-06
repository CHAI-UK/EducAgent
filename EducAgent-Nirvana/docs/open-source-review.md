# Open-source release review

Review date: 2026-11-06. Scope: repository distribution, deployment packaging,
configuration, navigation and provider-independent regression checks for
Learning, Portal and Nirvana. This is not a line-by-line audit of every SDK
module or a scientific review of course content.

## Findings resolved

| Finding | Resolution |
| --- | --- |
| Root ignore rules omitted Learning and its launcher from a fresh clone | Track canonical root assets and launcher; ignore generated mirrors |
| Internal application drafts, acceptance output and learner backups were publication candidates | Exclude private material, traces, archives and runtime state from Git while retaining local copies |
| No umbrella installation guide or shared environment example | Add deployment-first root README and `EducAgent-SDK/.env.example` |
| Package metadata referenced a separate repository and an inconsistent license | Point to CHAI-UK/EducAgent and use the approved MIT software license |
| Release bundles omitted project and Markdown-renderer license notices | Package MIT, third-party notices and micromark license; assert inclusion in deployment tests |
| Learning omitted Nirvana navigation despite the shared-route contract | Restore the compact research-framing route; retain theme behavior |
| Deployment instructions mixed generic setup with historical server details | Publish a concise operations guide; retain the old guide in ignored local output |

Local credentials were compared against every publication candidate without
printing secret values. No matching credentials were found. No candidate file
exceeded 50 MB. Textbook PDFs, extracted full text, learner JSONL, grant drafts,
environment files and generated deployment archives are excluded from Git.
Historical content versions remain because replay and authoring checks use them.

## Validation

- SDK: 493 provider-independent Python tests passed.
- Nirvana: 16 provider-independent Python tests passed.
- Portal: TypeScript check, production build and 80 Node tests passed.
- Nirvana/Learning: JavaScript syntax check and 10 Node tests passed.
- Deployment: six tests passed, including bundle integrity, all six course
  profiles, secret exclusions, route restrictions and required license notices.
- A credential-free three-experience archive was built successfully.

Windows sandbox restrictions prevented loopback HTTP tests and default temporary
files in the first attempts. Successful Python runs used the existing Conda
environment's Python executable, a workspace temporary directory and local
network permissions. No live ELM requests were made.

## Remaining boundaries

Docker was unavailable on the review machine, so container startup and Linux
nginx runtime were not rerun. No browser walkthrough was performed for this
release preparation; navigation, theme and renderer regressions used Node tests.
Public source availability does not supply service authentication, abuse
controls, scientific approval or validated learning effectiveness. Follow the
documented proxy/access-control and single-writer data-directory boundaries.
Third-party quoted material retains its source terms and is excluded from MIT.
