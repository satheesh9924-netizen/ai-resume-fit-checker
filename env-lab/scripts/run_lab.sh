#!/usr/bin/env bash
# Builds a throw-away copy of one deployment model, runs the suite against one target profile
# inside that environment, then destroys it (also on failure).
#
#   usage: bash env-lab/scripts/run_lab.sh <saas|onprem-acme> <target-profile> [pytest args...]
#   e.g.:  bash env-lab/scripts/run_lab.sh saas saas-tenant-a
#          bash env-lab/scripts/run_lab.sh onprem-acme onprem-acme -m "tenant or capability"
set -euo pipefail

STACK="${1:?usage: run_lab.sh <saas|onprem-acme> <target-profile> [pytest args...]}"
TARGET="${2:?usage: run_lab.sh <saas|onprem-acme> <target-profile> [pytest args...]}"
shift 2

LAB="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT="itlab-${STACK}-${RUN_ID:-$(date +%s)-$RANDOM}"

compose() { docker compose -p "$PROJECT" -f "$LAB/compose/base.yml" -f "$LAB/compose/${STACK}.yml" "$@"; }
cleanup() { echo "Destroying $PROJECT"; compose down -v --remove-orphans || true; }
trap cleanup EXIT

mkdir -p "$LAB/target"
export LAB_TARGET="$TARGET"

echo "Starting $PROJECT (stack=$STACK, target=$TARGET)"
compose up -d --wait
compose build tests
compose run --rm tests pytest --junitxml="target/surefire-reports/TEST-${TARGET}.xml" "$@"
