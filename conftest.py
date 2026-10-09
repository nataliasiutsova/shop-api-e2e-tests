import json
import os

from dotenv import load_dotenv

load_dotenv()

import pytest
from faker import Faker
import shutil

from client.api_client import RequestClient
from services.cart_service import CartService
from services.category_service import CategoryService
from services.order_service import OrderService
from services.product_service import ProductService
from utils.data_generator import make_product_payload

fake = Faker()


@pytest.fixture(scope="session", autouse=True)
def setup_allure_metadata(request):
    """Populates allure-results with metadata (executor, environment, categories)."""

    # 1. Determine the results directory
    results_dir = request.config.getoption("--alluredir", default=None)
    if not results_dir:
        results_dir = os.getenv("ALLURE_DIR", "allure-results")

    # 2. Try to create it, but don't crash on failure
    try:
        os.makedirs(results_dir, exist_ok=True)
    except (PermissionError, OSError):
        return

    # 3. Check write access
    if not os.access(results_dir, os.W_OK):
        return

    # ---------- Executor ----------
    if os.getenv("GITHUB_ACTIONS") == "true":
        executor = {
            "name": "GitHub Actions",
            "type": "github",
            "buildName": f"CI #{os.getenv('GITHUB_RUN_NUMBER', 'unknown')}",
            "buildUrl": (
                f"{os.getenv('GITHUB_SERVER_URL', 'https://github.com')}/"
                f"{os.getenv('GITHUB_REPOSITORY', 'unknown')}/actions/runs/"
                f"{os.getenv('GITHUB_RUN_ID', 'unknown')}"
            ),
            "reportName": "GitHub Actions Report",
        }
    elif os.path.exists("/.dockerenv"):
        executor = {
            "name": "Docker",
            "type": "docker",
            "buildName": "docker-local",
            "buildUrl": "http://localhost",
            "reportName": "Docker Report",
        }
    else:
        executor = {
            "name": "Local",
            "type": "local",
            "buildName": "local-dev",
            "buildUrl": "http://localhost",
            "reportName": "Local Report",
        }

    try:
        with open(os.path.join(results_dir, "executor.json"), "w", encoding="utf-8") as f:
            f.write(json.dumps(executor, indent=2, ensure_ascii=False))
    except OSError:
        pass

    # ---------- Environment ----------
    environment = {
        "Base.URL": os.getenv("BASE_URL", "https://aqa-proka4.org/sandbox/api"),
        "Environment": "CI" if os.getenv("GITHUB_ACTIONS") == "true"
        else "Docker" if os.path.exists("/.dockerenv")
        else "Local",
        "Executor": executor["name"],
        "Python.Version": os.sys.version.split()[0],
    }

    try:
        with open(os.path.join(results_dir, "environment.properties"), "w", encoding="utf-8") as f:
            for k, v in environment.items():
                f.write(f"{k}={v}\n")
    except OSError:
        pass

    # ---------- Categories ----------
    categories = [
        {"name": "Product defects", "matchedStatuses": ["failed"]},
        {"name": "Test defects", "matchedStatuses": ["broken"]},
        {
            "name": "Infrastructure problems",
            "messageRegex": ".*Timeout.*|.*Connection.*|.*HTTP 5\\d\\d.*",
            "matchedStatuses": ["broken", "failed"],
        },
    ]

    try:
        with open(os.path.join(results_dir, "categories.json"), "w", encoding="utf-8") as f:
            f.write(json.dumps(categories, indent=2, ensure_ascii=False))
    except OSError:
        pass

    # ---------- History (Trend) ----------
    history_source = os.getenv("ALLURE_HISTORY_DIR")
    if history_source and os.path.exists(history_source):
        history_target = os.path.join(results_dir, "history")
        try:
            if os.path.exists(history_target):
                shutil.rmtree(history_target)
            shutil.copytree(history_source, history_target)
        except OSError:
            pass


@pytest.fixture(scope="session")
def auth_client() -> RequestClient:
    token = os.getenv("SANDBOX_TOKEN")
    return RequestClient(token=token)


@pytest.fixture(scope="session")
def unauth_client() -> RequestClient:
    return RequestClient(token=None)


@pytest.fixture
def product_service(auth_client) -> ProductService:
    return ProductService(auth_client)


@pytest.fixture
def unauth_product_service(unauth_client):
    return ProductService(unauth_client)


@pytest.fixture
def category_service(auth_client) -> CategoryService:
    return CategoryService(auth_client)


@pytest.fixture
def cart_service(auth_client) -> CartService:
    return CartService(auth_client)


@pytest.fixture
def unauth_cart_service(unauth_client):
    return CartService(unauth_client)


@pytest.fixture
def order_service(auth_client) -> OrderService:
    return OrderService(auth_client)


@pytest.fixture
def unauth_order_service(unauth_client):
    return OrderService(unauth_client)


@pytest.fixture
def created_category(category_service, product_service):
    payload = {"name": f"Category-{fake.unique.word()}"}
    response = category_service.create_category(payload)
    assert response.status_code == 201, (
        f"Failed to create category: {response.status_code} — {response.text}"
    )

    category = response.json()

    yield category

    products_response = product_service.get_all_products(
        params={"category": category["name"]},
        allow_error=True,
    )

    if products_response.status_code == 200:
        products = products_response.json().get("data", [])
        for p in products:
            product_service.delete_product_by_id(
                p["id"],
                allow_error=True,
            )

    # Cleanup:
    category_service.delete_category_by_id(category["id"])


@pytest.fixture
def created_product(product_service, created_category):
    payload = make_product_payload(category=created_category["name"])
    response = product_service.create_product(payload)

    assert response.status_code == 201, (
        f"Failed to create product: {response.status_code} — {response.text}"
    )

    product = response.json()
    yield product

    # Cleanup:
    product_service.delete_product_by_id(product["id"], allow_error=True)


@pytest.fixture
def created_products(product_service, created_category):
    payload_1 = make_product_payload(category=created_category["name"])
    payload_2 = make_product_payload(category=created_category["name"])

    product_1 = product_service.create_product(payload_1).json()
    product_2 = product_service.create_product(payload_2).json()

    yield [product_1, product_2]

    for p in (product_1, product_2):
        product_service.delete_product_by_id(p["id"], allow_error=True)


@pytest.fixture
def seeded_products(product_service, created_category):
    # Create 3 products with the same category via API.

    created = []

    for i in range(3):
        payload = make_product_payload(
            category=created_category["name"],
            price=100 + i * 50,  # 100, 150, 200, 250, 300
            stock=10 + i,  # 10, 11, 12, 13, 14
            # name, description, image_url — random
        )

        response = product_service.create_product(payload)
        assert response.status_code == 201, (
            f"Failed to create product #{i}: {response.status_code} — {response.text}\n"
            f"Payload: {payload}"
        )

        created.append(response.json())

    yield created

    # Cleanup:
    for p in created:
        product_service.delete_product_by_id(p["id"])


@pytest.fixture
def empty_cart(cart_service):
    """Ensures the cart is empty before and after the test."""
    cart_service.clear_cart(allow_error=True)
    yield cart_service
    cart_service.clear_cart(allow_error=True)


@pytest.fixture
def cart_with_item(cart_service, created_product):
    """Adds one product to the cart, cleans up after."""
    cart_service.clear_cart(allow_error=True)
    product_id = created_product["id"]
    cart_service.clear_cart(allow_error=True)
    response = cart_service.add_item({"product_id": product_id, "quantity": 1})
    item = response.json()
    yield {
        "product": created_product,
        "product_id": product_id,
        "item_id": item["id"],
        "quantity": 1}

    cart_service.clear_cart(allow_error=True)


@pytest.fixture
def cart_with_custom_item(cart_service, created_product):
    cart_service.clear_cart(allow_error=True)

    def _add(quantity):
        response = cart_service.add_item({"product_id": created_product["id"], "quantity": quantity})
        item = response.json()
        return {
            "product_id": created_product["id"],
            "quantity": quantity,
            "item_id": item["id"],
        }

    yield _add

    cart_service.clear_cart(allow_error=True)


@pytest.fixture
def created_order(cart_service, order_service, created_product):
    """Creates an orders from the cart with one product, then cleans up."""
    product_id = created_product["id"]
    cart_service.clear_cart(allow_error=True)
    cart_service.add_item({"product_id": product_id, "quantity": 2})

    response = order_service.create_order()
    order = response.json()

    yield order

    order_service.cancel_order(order["id"], allow_error=True)
