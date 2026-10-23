#!/usr/bin/env bash
# Disposable real HA, synthetic data only. Never mount a production config.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
LAB=$(mktemp -d)
CONTAINER="ecm-lab-$$"
cleanup() {
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
  rm -rf -- "$LAB"
}
trap cleanup EXIT
mkdir "$LAB/config"
cp -r "$ROOT/custom_components" "$LAB/config/"
IMAGE=ghcr.io/home-assistant/home-assistant@sha256:33afb0659d786213264c2211f8d91c5fe87461c56eba6a3a546eb05fc71e89f4
for phase in create restart; do
  timeout 180 docker run --rm --name "$CONTAINER" --user "$(id -u):$(id -g)" \
    --network none --cpus 1 --memory 1536m --pids-limit 128 \
    --cap-drop ALL --security-opt no-new-privileges --read-only \
    --tmpfs /tmp:rw,size=128m -e PYTHONDONTWRITEBYTECODE=1 \
    -v "$ROOT:/repo:ro" -v "$LAB/config:/config" \
    --entrypoint python "$IMAGE" /repo/lab/ha_smoke.py "$phase"
done
