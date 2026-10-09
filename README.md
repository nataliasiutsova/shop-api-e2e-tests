# Shop API E2E Test Framework

Layered API test framework for the **Shop API** (products, cart, orders) built with **Pytest**, **Pydantic v2**, and
**Allure**.
135 tests covering REST API, schema validation, and end-to-end business flows.

![Python](https://img.shields.io/badge/python-3.12-blue)
![pytest](https://img.shields.io/badge/pytest-8.0-green)
![Pydantic](https://img.shields.io/badge/pydantic-v2-red)
![Allure](https://img.shields.io/badge/report-allure-orange)
![Docker](https://img.shields.io/badge/docker-ready-blue)

> ⚠️ **Note:** The sandbox API (`aqa-proka4.org`) enforces a **rate limit of 20 requests per 60 seconds**. The full
> regression suite (135 tests, ~600+ API calls) will **exceed** this limit and return `429 Too Many Requests`.
---

## Architecture

```
┌─────────────────────────────────────────────┐
│              Tests (pytest)                 │
│      tests/products/  tests/cart/           │
│      tests/orders/    tests/e2e/            │
└───────────────────┬─────────────────────────┘
                    │ fixtures (DI)
                    ▼
┌─────────────────────────────────────────────┐
│            Services Layer                   │
│  ProductService  CartService  OrderService  │
│    (encapsulate endpoints and payloads)     │
└───────────────────┬─────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│            RequestClient                    │
│  (HTTP, logging, Allure steps, errors)      │
└───────────────────┬─────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│          Models (Pydantic v2)               │
│  ProductResponse  CartItem  OrderResponse   │
└─────────────────────────────────────────────┘
```

**Design principles:**

- **Tests** verify business logic. They don't know about URLs, HTTP methods, or response formats.
- **Services** encapsulate endpoints, payloads, and query parameters. If an endpoint changes, only one file changes.
- **RequestClient** is the single point for HTTP requests, logging, Allure integration, and error handling.
- **Models** validate every API response against a schema, catching contract changes early.

## Project Structure

```
.
├── client/
│   └── api_client.py          # RequestClient: HTTP, logging, Allure
├── models/
│   ├── product.py             # Pydantic models for products
│   ├── cart.py                # Pydantic models for cart
│   └── order.py               # Pydantic models for orders
├── services/
│   ├── product_service.py
│   ├── category_service.py
│   ├── cart_service.py
│   └── order_service.py
├── tests/
│   ├── products/              # Product API tests (39)
│   ├── cart/                  # Cart API tests (37)
│   ├── orders/                # Order API tests (22)
│   └── e2e/                   # End-to-end flows (9)
├── utils/
│   ├── data_generator.py      # Fake data helpers
│   ├── environment.py         # Docker/CI detection
│   └── logging_utils.py       # Log masking and truncation
├── conftest.py                # Shared fixtures (DI)
├── pytest.ini                 # Markers and configuration
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── run_docker.sh              # Docker runner with Allure report
└── README.md
```

---

## Setup

### 1. Clone the repository

```bash
git clone git@github.com:YOUR_USERNAME/shop-api-e2e-tests.git
cd shop-api-e2e-tests
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate     # macOS / Linux
# .venv\Scripts\activate      # Windows
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
```

Then edit `.env`:

```
BASE_URL=https://aqa-proka4.org/sandbox/api
API_TOKEN=your_token_here
```

### 5. (Optional) Install Allure CLI for report viewing

```bash
brew install allure            # macOS
# or download from https://github.com/allure-framework/allure2/releases
```

---

## Running Tests

### Option A — locally (requires Python + Allure CLI)

```bash
# All tests
pytest

# Smoke tests (fast)
pytest -m smoke

⚠️**See the note about rate limit at the top of the document**
# Regression tests
pytest -m regression

# E2E tests only
pytest -m e2e

# Known bugs only
pytest -m known_bug

# A specific file
pytest tests/cart/test_add_item.py -v

# A specific test
pytest tests/cart/test_add_item.py::test_add_item_success -v

# Stop on first failure
pytest -x

# Re-run only failed tests
pytest --lf
```

### Option B — in Docker (recommended)

**Requirements:** Docker CLI + any container runtime (Docker Desktop, Colima, or OrbStack).

```bash
# Build the image (once)
docker build -t shop-api-tests:latest .

# 2. Make the runner executable (once)
chmod +x run_docker.sh

# 3. Run smoke tests (with Allure report)
./run_docker.sh

# 4. Run other markers explicitly (with Allure report)
./run_docker.sh e2e
./run_docker.sh known_bug

#  5. Run tests in specific folder
./run_docker.sh cart tests/cart
./run_docker.sh products tests/products
./run_docker.sh orders tests/orders

# 6. Run tests in specific file
./run_docker.sh add-item tests/cart/test_add_item.py

```

**What `run_docker.sh` does:**

1. Checks prerequisites (Docker, Allure, `.env`).
2. Builds the image if not present.
3. Runs the specified marker in a container.
4. Restores Allure `history` from the previous run (for Trend).
5. Generates and opens the Allure report.

### Test Markers

| Marker       | Purpose                                   | Run                    |
|:-------------|:------------------------------------------|:-----------------------|
| `smoke`      | Critical tests, run on every commit       | `pytest -m smoke`      |
| `regression` | Full regression suite                     | `pytest -m regression` |
| `e2e`        | End-to-end scenarios across services      | `pytest -m e2e`        |
| `known_bug`  | Tests that fail due to known product bugs | `pytest -m known_bug`  |

---

## Test Coverage

| Service      | Tests   | Scope                                                                           |
|:-------------|:--------|:--------------------------------------------------------------------------------|
| **Products** | 61      | CRUD, filtering, pagination, negative cases                                     |
| **Cart**     | 47      | Add / get / update / delete items, clear cart, stock boundaries, negative cases |
| **Orders**   | 22      | Create from cart / get all / get by id / cancel, negative cases                 |
| **E2E**      | 9       | Full checkout flow, snapshot, cancellation, multi-item orders                   |
| **Total**    | **135** |                                                                                 |

### Common Coverage (all services)

- **Schema validation** — all 10 endpoints that return a response body are covered by dedicated Pydantic v2 tests
- **Negative cases** — `401 Unauthorized`, `404 Not Found`, `422 Unprocessable Entity`, `400 Bad Request`
- **Boundary tests** — max/min values, missing fields, invalid types
- **Allure reporting** — title, description, severity, steps, request/response attachments

---

## Example Test

```python
@allure.title("POST /cart/items — adds a product and returns 201")
@allure.description("Adds a valid product to an empty cart and verifies the response.")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.regression
def test_add_item_success(empty_cart, created_product):
    product_id = created_product["id"]
    quantity = 2

    with allure.step(f"Send POST /cart/items with product_id={product_id}"):
        response = empty_cart.add_item({"product_id": product_id, "quantity": quantity})

    with allure.step(f"Verify status code is 201 (got {response.status_code})"):
        assert response.status_code == 201, (
            f"Expected 201, got {response.status_code}. Body: {response.text[:200]}"
        )

        item = response.json()

    with allure.step(f"Verify product_id={product_id} in response"):
        assert item["product_id"] == product_id
```

---

## Allure Reports

### Locally

```bash
# Run tests with Allure results
pytest -m smoke --alluredir=allure-results-local

# Generate report
allure generate allure-results-local -o allure-report-local --clean

# Open in browser
allure open allure-report-local
```

### In Docker (recommended)

`run_docker.sh` **generates the report automatically** — no extra commands needed.

```bash
# Smoke (default)
./run_docker.sh

# E2E
./run_docker.sh e2e

# Specific folder
./run_docker.sh cart tests/cart

# Specific file
./run_docker.sh add-item tests/cart/test_add_item.py
```

### Report features

- **Suites** — organized by service (Products, Cart, Orders, E2E)
- **Behaviors** — grouped by feature and story
- **Severity** — critical / normal / minor tests marked
- **Steps** — every action is a readable step
- **Attachments** — request and response bodies attached automatically
- **Environment** — base URL, executor, Python version
- **Categories** — failures grouped by type (product defect / test defect / infrastructure)

---

## Design Decisions

**Why a Services layer?**
Tests should not know URLs or payload shapes. Services encapsulate endpoints, so changing `/cart/items` to
`/carts/{id}/items` touches one file, not 20 tests.

**Why Pydantic?**
Validating every response against a schema catches contract changes early. Without Pydantic, a missing field returns
`KeyError` deep inside a test. With Pydantic, it fails at the boundary with a clear error.

**Why separate schema validation tests?**
Business logic tests (e.g. `test_add_item_success`) verify what the API *does*. Schema tests (e.g.
`test_add_item_response_matches_schema`) verify what the API *returns*. Splitting them gives precise diagnostics: a
failing business test means the behavior is wrong; a failing schema test means the contract changed.

**Why no parallel execution?**
The API uses a single shared user and cart. Parallel tests would race for the same cart state. Products could be
parallelized, but the gain (~15 seconds) does not justify the added complexity and flakiness risk.


---

## Roadmap

- [x] API tests for products (61)
- [x] API tests for cart (43)
- [x] API tests for orders (22)
- [x] E2E checkout flow tests (9)
- [x] Pydantic schema validation
- [x] Allure integration (steps, severity, features)
- [x] Docker support (one-command test run)
- [ ] GitHub Actions CI
- [ ] CI badge in README

---

## Author

**Natalya Siutsova**

- GitHub: [@nataliasiutsova](https://github.com/nataliasiutsova)
- LinkedIn: [linkedin.com/in/natalia-siutsova](https://linkedin.com/in/natalia-siutsova)

---

## License

MIT License.

