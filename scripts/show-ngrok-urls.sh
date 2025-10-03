#!/bin/bash

# Script to display and optionally persist ngrok tunnel URLs
# Works both locally and inside Docker. Requires ngrok dashboard to be exposed
# (default http://localhost:4040 or configurable via NGROK_INSPECT_PORT).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

UPDATE_ENV=false
RELOAD_BACKEND=false

NGROK_MAX_RETRIES=${NGROK_MAX_RETRIES:-15}
NGROK_RETRY_DELAY=${NGROK_RETRY_DELAY:-2}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --update-env)
            UPDATE_ENV=true
            shift
            ;;
        --reload-backend)
            RELOAD_BACKEND=true
            shift
            ;;
        --inspect-port)
            NGROK_INSPECT_PORT="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

NGROK_INSPECT_PORT=${NGROK_INSPECT_PORT:-4040}
INSPECT_URL="http://127.0.0.1:${NGROK_INSPECT_PORT}/api/tunnels"

echo "Fetching ngrok tunnel information from ${INSPECT_URL}..."

if ! command -v curl >/dev/null 2>&1; then
    echo "curl is required for this script" >&2
    exit 1
fi

PYTHON_BIN=${PYTHON_BIN:-python3}
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    PYTHON_BIN=python
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "python or python3 is required for this script" >&2
    exit 1
fi

TUNNELS=""

for attempt in $(seq 1 "$NGROK_MAX_RETRIES"); do
    if RESPONSE=$(curl -s "$INSPECT_URL" 2>/dev/null); then
        if TUNNELS=$(NGROK_TUNNEL_RESPONSE="$RESPONSE" "$PYTHON_BIN" <<'PY'
import json
import os
import sys

raw = os.environ.get("NGROK_TUNNEL_RESPONSE", "")
if not raw:
    sys.exit(2)

try:
    data = json.loads(raw)
except json.JSONDecodeError:
    sys.exit(3)

urls = [
    tunnel.get("public_url")
    for tunnel in data.get("tunnels", [])
    if tunnel.get("proto") == "https" and tunnel.get("public_url")
]

sys.stdout.write("\n".join(urls))
PY
        ); then
            if [ -n "$TUNNELS" ]; then
                break
            fi
        else
            TUNNELS=""
        fi
    fi

    if [ "$attempt" -lt "$NGROK_MAX_RETRIES" ]; then
        echo "  Waiting for ngrok tunnel... (${attempt}/${NGROK_MAX_RETRIES})"
        sleep "$NGROK_RETRY_DELAY"
    fi
done

if [ -z "$TUNNELS" ]; then
    echo "No HTTPS tunnels found after ${NGROK_MAX_RETRIES} attempts. Ensure ngrok is running and inspect API is exposed on ${INSPECT_URL}." >&2
    exit 1
fi

echo "Active ngrok tunnels:"

echo "$TUNNELS" | nl

FRONTEND_URL=$(echo "$TUNNELS" | head -n 1)

echo

echo "Frontend public URL: ${FRONTEND_URL}"

if $UPDATE_ENV; then
    ENV_FILE="$PROJECT_ROOT/.env"
    if [ ! -f "$ENV_FILE" ]; then
        echo ".env file not found at $ENV_FILE" >&2
        exit 1
    fi

    echo "Updating PUBLIC_FRONTEND_URL in .env..."

    awk -v url="$FRONTEND_URL" '
        BEGIN { updated = 0 }
        /^PUBLIC_FRONTEND_URL=/ {
            print "PUBLIC_FRONTEND_URL=" url
            updated = 1
            next
        }
        { print }
        END {
            if (!updated) {
                print "PUBLIC_FRONTEND_URL=" url
            }
        }
    ' "$ENV_FILE" > "$ENV_FILE.tmp"

    mv "$ENV_FILE.tmp" "$ENV_FILE"
    echo ".env updated with PUBLIC_FRONTEND_URL=${FRONTEND_URL}"

    if $RELOAD_BACKEND; then
        echo "Triggering backend container recreation to pick up new CORS settings..."
        if docker compose version >/dev/null 2>&1; then
            docker compose up -d backend >/dev/null 2>&1 || true
        elif command -v docker-compose >/dev/null 2>&1; then
            docker-compose up -d backend >/dev/null 2>&1 || true
        fi
    fi
fi

echo

echo "ngrok tunnel discovery complete."
