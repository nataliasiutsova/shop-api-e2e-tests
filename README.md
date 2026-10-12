# Shop API E2E Test Framework

Layered API test framework for the **Shop API** (products, cart, orders) built with **pytest**, **Pydantic v2**, and *
*Allure**.
**135 tests** covering REST API, schema validation, and end-to-end flows.

[![Tests](https://github.com/nataliasiutsova/shop-api-e2e-tests/actions/workflows/tests.yml/badge.svg)](https://github.com/nataliasiutsova/shop-api-e2e-tests/actions)
[![Latest Allure Report](https://img.shields.io/badge/latest_allure_report-orange)](https://nataliasiutsova.github.io/shop-api-e2e-tests/)
![Python](https://img.shields.io/badge/python-3.12-blue)
![pytest](https://img.shields.io/badge/pytest-8.0-green)
![Pydantic](https://img.shields.io/badge/pydantic-v2-red)
![Docker](https://img.shields.io/badge/docker-ready-blue)

> ⚠️ The sandbox API has a rate limit of **20 requests / 60 seconds**. Run **smoke** for quick validation. Full *
*regression** may hit the limit.

---

## Architecture

```
Tests  →  Services  →  RequestClient  →  Models (Pydantic)
```

- **Tests** — business logic only (no HTTP details)
- **Services** — encapsulate endpoints and payloads
- **RequestClient** — single point for HTTP, logging, Allure
- **Models** — validate every response against a schema

---

## Tech Stack

| Layer            | Tool           |
|:-----------------|:---------------|
| Language         | Python 3.12    |
| Test runner      | pytest         |
| HTTP             | requests       |
| Validation       | Pydantic v2    |
| Reporting        | Allure         |
| Test data        | Faker          |
| Containerization | Docker         |
| CI/CD            | GitHub Actions |

---

## Run Tests

### 🤖 1. Via GitHub Actions (no local setup)

1. Open **Actions → Tests**.
2. Click **Run workflow**.
3. Choose marker: `smoke` / `regression` / `e2e` / `known_bug`.
4. Click **Run workflow**.
5. Open the **Summary** tab — direct link to the Allure report.

**→ [Latest report](https://nataliasiutsova.github.io/shop-api-e2e-tests/)**

### 🐳 2. Locally with Docker

**Requirements:** Docker, Allure CLI, Java.

```bash
# 1. Clone the repository
git clone git@github.com:nataliasiutsova/shop-api-e2e-tests.git
cd shop-api-e2e-tests

# 2. Configure environment
cp .env.example .env
# edit .env and add your API_TOKEN
nano .env

# 3. Make the runner executable
chmod +x run_docker.sh

# 4. Build the Docker image
docker build -t shop-api-tests:latest .

# 5. Run smoke tests (report opens automatically)
./run_docker.sh smoke
```

### 🐍 3. Locally without Docker

**Requirements:** Python 3.12, Allure CLI, Java.

```bash
# 1. Clone the repository
git clone git@github.com:nataliasiutsova/shop-api-e2e-tests.git
cd shop-api-e2e-tests

# 2. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# edit .env and add your API_TOKEN
nano .env

# 5. Run smoke tests
pytest -m smoke --alluredir=allure-results

# 6. Open the report
allure serve allure-results
```

### Environment

`.env` file:

```
BASE_URL=https://aqa-proka4.org/sandbox/api
API_TOKEN=your_token_here
```

---

## Test Coverage

| Service      | Tests   | Scope                                                      |
|:-------------|:--------|:-----------------------------------------------------------|
| **Products** | 39      | CRUD, filtering, pagination, negative cases                |
| **Cart**     | 37      | Add / get / update / delete items, clear, stock boundaries |
| **Orders**   | 22      | Create from cart, get all, get by id, cancel               |
| **E2E**      | 9       | Full checkout flow, snapshot, cancellation                 |
| **Total**    | **135** |                                                            |

**Common coverage:** schema validation (all 10 endpoints with body), negative cases (401, 404, 422, 400), boundary
tests, Allure reporting.

---

## Example Test

```python
@allure.title("POST /cart/items — adds a product and returns 201")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.regression
def test_add_item_success(empty_cart, created_product):
    product_id = created_product["id"]

    with allure.step(f"Send POST /cart/items with product_id={product_id}"):
        response = empty_cart.add_item({"product_id": product_id, "quantity": 2})

    with allure.step(f"Verify status code is 201 (got {response.status_code})"):
        assert response.status_code == 201
        item = response.json()

    with allure.step(f"Verify product_id={product_id} in response"):
        assert item["product_id"] == product_id
```

---

## Test Markers

| Marker       | Purpose                           | Run                    |
|:-------------|:----------------------------------|:-----------------------|
| `smoke`      | Critical tests, run on every push | `pytest -m smoke`      |
| `regression` | Full regression suite             | `pytest -m regression` |
| `e2e`        | End-to-end scenarios              | `pytest -m e2e`        |
| `known_bug`  | Tests with known product bugs     | `pytest -m known_bug`  |

---

## Allure Reports

- **Live:** [nataliasiutsova.github.io/shop-api-e2e-tests](https://nataliasiutsova.github.io/shop-api-e2e-tests/)
- **Per marker:** `/e2e/`, `/regression/`, `/known_bug/`
- **Trend:** history preserved across runs
- **Categories:** product defects / test defects / infrastructure

> Reports are cached by the browser. Hard refresh: **Cmd + Shift + R** (macOS) or **Ctrl + Shift + R**.

---

## Design Decisions

**Services layer** — tests don't know URLs or payload shapes. Endpoint changes touch one file.

**Pydantic** — validating every response against a schema catches contract changes early. Without Pydantic, a missing
field returns KeyError deep inside a test.
With Pydantic, it fails at the boundary with a clear error.

**Separate schema tests** — business tests verify *what* the API does; schema tests verify *what* it returns. Precise
diagnostics.

**Docker** — reproducibility. Same Python, same dependencies, same Allure — local and CI.

**No parallel execution** — the API uses a single shared user and cart. Race conditions would cause flaky tests.

---

## Roadmap

- [x] API tests (products, cart, orders) — 98 tests
- [x] E2E checkout flow — 9 tests
- [x] Pydantic schema validation
- [x] Allure reporting (steps, severity, environment, categories, trend)
- [x] Docker support
- [x] GitHub Actions CI (smoke on push, any marker manually)
- [x] Live Allure reports on GitHub Pages

---

## Author

**Natalya Siutsova**

- GitHub: [@nataliasiutsova](https://github.com/nataliasiutsova)
- LinkedIn: [linkedin.com/in/natalia-siutsova](https://linkedin.com/in/natalia-siutsova)

## License

[MIT](LICENSE)