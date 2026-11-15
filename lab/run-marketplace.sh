#!/usr/bin/env bash
# Release rehearsal using the hosted runner and disposable HA storage.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
LAB=$(mktemp -d)
trap 'rm -rf -- "$LAB"' EXIT
IMAGE=ghcr.io/home-assistant/home-assistant@sha256:c6c1ca9931036bf3a2c4cc088d8db25dfea3b33935a5ecc83c40349462e2f69e
BASELINE=$1
CANDIDATE=$2

docker pull "$IMAGE"
mkdir "$LAB/upgrade" "$LAB/clean"

run_ha() {
  local config=$1
  shift
  local network=$1
  shift
  local credentials=()
  if [[ "$network" == bridge ]]; then
    credentials=(-e ECM_LAB_GITHUB_TOKEN)
  fi
  timeout 240 docker run --rm --user "$(id -u):$(id -g)" \
    --network "$network" --cpus 2 --memory 2g --pids-limit 256 \
    --cap-drop ALL --security-opt no-new-privileges --read-only \
    --tmpfs /tmp:rw,size=128m -e PYTHONDONTWRITEBYTECODE=1 "${credentials[@]}" \
    -v "$ROOT:/repo:ro" -v "$LAB/$config:/config" \
    --entrypoint python "$IMAGE" "$@"
}

run_ha upgrade bridge /repo/lab/marketplace_package.py "$BASELINE"
run_ha upgrade none /repo/lab/ha_smoke.py create
run_ha upgrade bridge /repo/lab/marketplace_package.py "$CANDIDATE" /repo/custom_components/energy_cost_monitor
run_ha upgrade none /repo/lab/ha_smoke.py restart
run_ha clean bridge /repo/lab/marketplace_package.py "$CANDIDATE" /repo/custom_components/energy_cost_monitor
run_ha clean none /repo/lab/ha_smoke.py create
