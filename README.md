# EducAgent

| Route | Experience | Canonical source |
| --- | --- | --- |
| `/` | Learning: a compact resource directory with light/dark themes | `index.html`, `styles.css` |
| `/portal/` | Portal: causal reasoning courses in General and Medical contexts | `EducAgent-Portal/` |
| `/nirvana/` | Nirvana: research-question framing and an editable Causal Research Brief | `EducAgent-Nirvana/` |

Portal learning records and Nirvana research drafts remain separate. This is a
research prototype: completion is not validated mastery or scientific approval.
Nirvana proposes edits for acceptance; it does not verify evidence or execute
downstream tools.

## Install and configure

Requirements: Python 3.12+ (3.13 recommended), Conda, pip, Node.js 22.12+ and npm.
Linux deployment additionally requires Docker Engine and Docker Compose v2.
Model-backed features require an ELM account.

```sh
git clone https://github.com/CHAI-UK/EducAgent.git
cd EducAgent
conda create -n educagent-sdk python=3.13 pip -y
conda activate educagent-sdk
python -m pip install --upgrade pip
python -m pip install --build-constraint EducAgent-Portal/build-constraints.txt -c EducAgent-Portal/constraints.txt -e ./EducAgent-Portal
cd EducAgent-Portal
npm ci
cd ..
```

Copy `EducAgent-Portal/.env.example` to `EducAgent-Portal/.env` and edit:

```dotenv
BASE_URL=https://elm.edina.ac.uk/api/v1
MODEL=CHANGE_ME
ELM_API_KEY=CHANGE_ME
```

Use your assigned ELM model identifier and API key. Both apps share these
settings; environment variables override the file. The current adapter requires
the ELM URL above rather than an arbitrary OpenAI-compatible endpoint. Keep keys
on the server, out of browser configuration and Git.

## Run locally on Windows

Run from the repository root in PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\start-demo.ps1 -Port 4173
```

Open [Learning](http://127.0.0.1:4173/),
[Portal](http://127.0.0.1:4173/portal/) or
[Nirvana](http://127.0.0.1:4173/nirvana/).
The launcher builds Portal, stages public assets in `.demo-site/`, starts the
Nirvana API on port 8011 and serves the site on port 4173. Stop with Ctrl+C.
Use `-Reset` only when you intend to clear local Portal progress. Generated
`portal/`, `nirvana/` and `media/` directories are not source files.

## Deploy all three experiences on Linux

After installing dependencies, build a credential-free archive from the source
repository root on Windows or Linux:

```sh
python EducAgent-Nirvana/deploy/build_bundle.py --output output --name educagent-release
```

This type-checks and builds Portal, packages runtime/public files, and writes an
integrity manifest and SHA-256 checksum. Use a new name per release. Transfer the
archive and checksum to your host, then run:

```sh
sha256sum -c educagent-release.tar.gz.sha256
tar -xzf educagent-release.tar.gz
cd educagent-release
cp config/elm.env.example config/elm.env
chmod 600 config/elm.env
# Edit config/elm.env with real ELM settings before continuing.
docker compose build
docker compose run --rm --no-deps educagent python run.py --check-config --data-dir /tmp/educagent-preflight
docker compose up -d
docker compose exec educagent python check.py --url http://127.0.0.1:9090
```

Run Compose inside the extracted bundle, not the source `deploy/` directory.
The entrance binds to `127.0.0.1:9090`, with all three routes under that origin
and Nirvana's API at `/nirvana/api/`. For remote review, use an SSH tunnel and
open `http://127.0.0.1:9090/`:

```sh
ssh -L 9090:127.0.0.1:9090 user@your-server
```

For shared access, place an HTTPS reverse proxy with institutional access
control in front of the loopback port. Set `SESSION_COOKIE_SECURE=1` in the
Compose environment when serving over HTTPS. The application supplies no login,
rate limiting or public-service abuse controls.

### State and operations

- Portal stores records in the `portal-data` Docker volume. Run one process per
  data directory. Anonymous browser cookies isolate sessions; tabs in one
  browser profile share progress. There is no account recovery.
- Nirvana drafts and chat live in browser memory. Copy a Brief before refresh.
- Use `docker compose logs --tail 100` for logs and `docker compose down` to
  stop. `docker compose down -v` deletes progress.
- Back up the whole Portal data directory while stopped before updates. Keep
  the volume and previous image for rollback; do not restore old progress over
  newer learning records during a code rollback.

The [operations guide](EducAgent-Nirvana/deploy/README.md) also covers native
Linux/systemd, backups and rollback.

## Build checks

From PowerShell, with the `educagent-sdk` environment activated:

```powershell
cd EducAgent-Portal
npm run web:check
npm run web:build
cd ../EducAgent-Nirvana
node --check demo/app.js
cd ..
git diff --check
```

## License

Edit canonical sources, keep documentation and code in English, and exclude
credentials, learner traces, backups, textbook PDFs and internal drafts from Git.
Project-authored software uses [MIT](LICENSE); third-party works retain their
own terms. See [third-party notices](THIRD_PARTY_NOTICES.md) and
[Sources & rights](EducAgent-Portal/web/public/sources.html).
