#!/usr/bin/env bash

set -euo pipefail

BRANCH="${1:-main}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

log() {
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1"
}

require_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        log "Missing required command: $1"
        exit 1
    fi
}

require_cmd git
require_cmd docker

cd "${PROJECT_ROOT}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    log "Not inside a git repository: ${PROJECT_ROOT}"
    exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
    log "Working tree has local changes. Commit/stash before updating."
    exit 1
fi

log "Fetching origin/${BRANCH}"
git fetch origin "${BRANCH}"

LOCAL_SHA="$(git rev-parse HEAD)"
REMOTE_SHA="$(git rev-parse "origin/${BRANCH}")"
BASE_SHA="$(git merge-base HEAD "origin/${BRANCH}")"

if [[ "${LOCAL_SHA}" == "${REMOTE_SHA}" ]]; then
    log "Already up to date at ${LOCAL_SHA}"
elif [[ "${LOCAL_SHA}" == "${BASE_SHA}" ]]; then
    log "Fast-forwarding to origin/${BRANCH}"
    git checkout "${BRANCH}"
    git pull --ff-only origin "${BRANCH}"
elif [[ "${REMOTE_SHA}" == "${BASE_SHA}" ]]; then
    log "Local branch is ahead of origin/${BRANCH}; not deploying."
    exit 1
else
    log "Local and origin/${BRANCH} have diverged; manual intervention required."
    exit 1
fi

log "Rebuilding and restarting containers"
docker compose up -d --build --remove-orphans

log "Update completed successfully"
