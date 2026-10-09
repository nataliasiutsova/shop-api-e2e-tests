#!/bin/bash
set -e

# ---------- Args ----------
# First arg is a label for output folders (and default marker).
# Remaining args are passed directly to pytest.
#
# Usage:
#   ./run_docker.sh                                   # smoke (default)
#   ./run_docker.sh e2e                               # -m e2e
#   ./run_docker.sh cart tests/cart                   # folder
#   ./run_docker.sh add-item tests/cart/test_add_item.py
#   ./run_docker.sh test-success tests/cart/test_add_item.py::test_add_item_success

LABEL=${1:-smoke}
shift || true

# If no pytest args provided — default to marker regression
if [ $# -eq 0 ]; then
    set -- -m smoke
fi

SAFE_LABEL="${LABEL//_/-}"
IMAGE="shop-api-tests:latest"
RESULTS_DIR="allure-results-${SAFE_LABEL}"
REPORT_DIR="allure-report-${SAFE_LABEL}"

# ---------- Preflight checks ----------
echo "▶ Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed."
    echo "   Install: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker daemon is not running."
    echo "   Start Docker Desktop or Colima."
    exit 1
fi

if ! command -v allure &> /dev/null; then
    echo "❌ Allure CLI is not installed."
    echo "   Install: brew install allure"
    exit 1
fi

if [ ! -f ".env" ]; then
    echo "❌ .env file not found."
    echo "   Copy from example: cp .env.example .env"
    exit 1
fi

if ! docker image inspect "$IMAGE" &> /dev/null; then
    echo "▶ Image $IMAGE not found. Building..."
    docker build -t "$IMAGE" .
fi

# ---------- Prepare results dir ----------
echo "▶ Label:    $LABEL"
echo "▶ Results:  $RESULTS_DIR"
echo "▶ Report:   $REPORT_DIR"
echo "▶ Pytest:   pytest $*"

mkdir -p "$RESULTS_DIR"
find "$RESULTS_DIR" -mindepth 1 -delete

# Restore history from previous report (for Trend)
if [ -d "$REPORT_DIR/history" ]; then
    echo "▶ Restoring history from previous report..."
    cp -r "$REPORT_DIR/history" "$RESULTS_DIR/history"
else
    echo "▶ No previous report — starting fresh history"
fi

# ---------- Run tests ----------
echo "▶ Running tests in Docker..."

docker run --rm \
    --user "$(id -u):$(id -g)" \
    --env-file .env \
    -v "$(pwd)/$RESULTS_DIR:/app/allure-results" \
    "$IMAGE" \
    pytest "$@" --alluredir=allure-results -v

# ---------- Generate report ----------
echo "▶ Generating Allure report..."
allure generate "$RESULTS_DIR" -o "$REPORT_DIR" --clean

# ---------- Open report ----------
echo "▶ Opening report..."
allure open "$REPORT_DIR"