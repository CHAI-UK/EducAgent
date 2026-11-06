# EducAgent deployment operations

Start with the [repository README](../../README.md) for installation,
configuration, release packaging and Docker Compose commands. Run the commands
below inside an extracted credential-free release bundle.

## Architecture

```text
Browser -> HTTPS/access-control proxy -> 127.0.0.1:9090 (nginx)
                                        /              Learning
                                        /portal/       Portal UI
                                        /api/          Portal API (9091)
                                        /nirvana/      Nirvana UI
                                        /nirvana/api/  Nirvana API (9092)
```

Both Python APIs bind to loopback. Static serving is limited to `site/`;
configuration, runtime source, answer keys and traces are not web resources.
Editor and developer preview endpoints are blocked by nginx. This prototype
has no built-in authentication or public abuse controls. Use an institutional
HTTPS/access-control proxy or an SSH tunnel.

## Release files and secrets

`build_bundle.py` copies allowlisted runtime sources and public assets, writes
`MANIFEST.json`, and produces an archive and SHA-256 checksum. Credentials are
excluded by default. Do not use `--include-env` for public releases. Never
distribute `config/elm.env`, cookies, private traces or backups.

Copy `config/elm.env.example` to `config/elm.env`, fill in all settings and apply
`chmod 600 config/elm.env`. Docker reads it at runtime; `.dockerignore` excludes
it from the image. Set `SESSION_COOKIE_SECURE=1` for HTTPS.

## Validate and monitor

```sh
docker compose run --rm --no-deps educagent python run.py --check-config --data-dir /tmp/educagent-preflight
docker compose exec educagent python check.py --url http://127.0.0.1:9090
docker compose ps
docker compose logs --tail 100
```

These checks make no live ELM requests. Container health uses liveness only;
run the complete check after updates to verify the manifest, routes and session
isolation. Browser walkthroughs and live model testing are separate activities.

## State, backup and rollback

Portal uses opaque anonymous session cookies (`HttpOnly`, `SameSite=Lax`). Tabs
in one browser profile share progress. Cookies are not accounts; losing a
cookie neither deletes records nor provides recovery. Administrators own
retention and deletion. Nirvana drafts and chat remain in browser memory.

Run one process per data directory. Docker uses the `portal-data` named volume.
Preserve the Compose project name across release folders (`educagent-review`
in `compose.yaml`). `docker compose down -v` deletes all stored progress.

Stop the service before a consistent whole-Portal backup:

```sh
docker compose stop
mkdir -p /secure/backup/educagent-release
docker compose cp educagent:/data/portal /secure/backup/educagent-release/portal
docker compose start
```

Choose a new private backup directory each time and restrict access. Retain
the previous image, configuration and release checksums. Preserve the volume,
proxy and TLS configuration during updates. A code rollback must not restore
older progress over newer records. For data recovery, stop the service and
restore a separately selected compatible backup.

## Native Linux alternative

Install nginx using the host package manager, then run:

```sh
conda create -n educagent-server python=3.13 pip -y
conda activate educagent-server
python -m pip install -c constraints.txt ./EducAgent-Portal
python run.py --check-config --data-dir /tmp/educagent-preflight
python run.py --data-dir /srv/educagent-data
```

Give the service user read access to the release and private configuration and
write access to the data directory. Ports 9090, 9091 and 9092 must be free.
Ctrl+C stops this launcher's children. Do not kill unrelated port owners. Use
one persistent data directory across releases.

For systemd, edit `systemd/educagent.service` with the absolute release path,
Conda Python executable and data directory. It is a user service:

```sh
mkdir -p "$HOME/.config/systemd/user"
cp systemd/educagent.service "$HOME/.config/systemd/user/educagent.service"
systemctl --user daemon-reload
systemctl --user enable --now educagent.service
systemctl --user status educagent.service
journalctl --user -u educagent.service -n 100 --no-pager
```

Check foreground startup first; do not run a second copy alongside systemd.
Arrange lingering with the administrator if startup after logout is required.
Do not run the app as root.
