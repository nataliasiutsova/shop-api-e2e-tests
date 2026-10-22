#!/bin/bash
set -e

LABEL="${1:-smoke}"
shift
PYTEST_ARGS=("$@")
[ ${#PYTEST_ARGS[@]} -eq 0 ] && PYTEST_ARGS=(-m "$LABEL")

SAFE_LABEL="${LABEL//_/-}"
RESULTS="allure-results-${SAFE_LABEL}"
REPORT="allure-report-${SAFE_LABEL}"
IMAGE="shop-api-tests:latest"

command -v docker >/dev/null || { echo "❌ Docker not installed"; exit 1; }
docker info >/dev/null 2>&1     || { echo "❌ Docker not running"; exit 1; }
command -v allure >/dev/null    || { echo "❌ Allure CLI not installed"; exit 1; }
[ -f .env ]                     || { echo "❌ .env not found"; exit 1; }

docker image inspect "$IMAGE" >/dev/null 2>&1 || docker build -t "$IMAGE" .

mkdir -p "$RESULTS"
find "$RESULTS" -mindepth 1 -delete
[ -d "$REPORT/history" ] && cp -r "$REPORT/history" "$RESULTS/history"

set +e
docker run --rm \
    --user "$(id -u):$(id -g)" \
    --env-file .env \
    -v "$(pwd)/$RESULTS:/app/allure-results" \
    "$IMAGE" \
    pytest "${PYTEST_ARGS[@]}" --alluredir=allure-results -v

PYTEST_EXIT_CODE=$?

set -e

allure generate "$RESULTS" -o "$REPORT" --clean
allure open "$REPORT"

exit $PYTEST_EXIT_CODE