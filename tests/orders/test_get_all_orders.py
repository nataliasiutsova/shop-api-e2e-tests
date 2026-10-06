import allure
import pytest
from pydantic import ValidationError

from models.order import OrderResponse

pytestmark = [
    allure.feature("Order"),
    allure.story("Get all orders"),
]


@pytest.mark.regression
@allure.title("GET /api/orders — returns 200 OK and a list of orders")
@allure.description(
    "Verifies that GET /api/orders returns 200 and a JSON array."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_get_orders_returns_200(order_service):
    with allure.step("Send GET /api/orders"):
        response = order_service.get_all_orders()

    with allure.step(f"Verify status code is 200 (got {response.status_code})"):
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. Body: {response.text[:200]}"
        )

    with allure.step("Verify the body is a list"):
        body = response.json()
        assert isinstance(body, list), (
            f"Expected list, got {type(body).__name__}: {body}"
        )


@pytest.mark.regression
@allure.title("GET /api/orders — each orders matches the OrderResponse schema")
@allure.description(
    "Validates each orders in the list against the OrderResponse model."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_get_orders_response_matches_schema(order_service, created_order):
    with allure.step("Send GET /api/orders"):
        response = order_service.get_all_orders()

    with allure.step(f"Verify status code is 200 (got {response.status_code})"):
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. Body: {response.text[:200]}"
        )

        orders = response.json()

    with allure.step(f"Validate each of {len(orders)} orders against OrderResponse"):
        for idx, raw in enumerate(orders):
            with allure.step(f"Validate orders at index {idx} (id={raw.get('id', 'N/A')})"):
                try:
                    OrderResponse.model_validate(raw)
                except ValidationError as e:
                    pytest.fail(
                        f"Order at index {idx} (id={raw.get('id', 'N/A')}) "
                        f"does not match OrderResponse schema.\n"
                        f"Errors:\n{e}\n"
                        f"Raw orders:\n{raw}",
                        pytrace=False,
                    )


@pytest.mark.regression
@allure.title("GET /api/orders — contains the newly created orders")
@allure.description(
    "Creates an orders and verifies it appears in GET /api/orders."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_get_orders_contains_created_order(order_service, created_order):
    order_id = created_order["id"]

    with allure.step(f"Send GET /api/orders (expect orders id={order_id} present)"):
        response = order_service.get_all_orders()
        orders = response.json()

    with allure.step(f"Verify orders id={order_id} is in the list"):
        order_ids = [o["id"] for o in orders]
        assert order_id in order_ids, (
            f"Created orders id={order_id} not found in list. "
            f"Order ids: {order_ids}"
        )


@pytest.mark.regression
@allure.title("GET /api/orders — unauthorized request returns 401 Unauthorized")
@allure.description(
    "Attempts to list orders without an authorization token and expects 401."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_get_orders_unauthorized(unauth_order_service):
    with allure.step("Send GET /api/orders without authorization"):
        response = unauth_order_service.get_all_orders(allow_error=True)

    with allure.step(f"Verify status code is 401 (got {response.status_code})"):
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}. Body: {response.text[:200]}"
        )
