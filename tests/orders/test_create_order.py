import allure
import pytest
from pydantic import ValidationError

from models.order import OrderResponse

pytestmark = [
    allure.feature("Order"),
    allure.story("Сreate orders"),
]


@pytest.mark.smoke
@allure.title("POST /api/orders — creates an orders and returns 201 Created")
@allure.description("Creates an orders from a non-empty cart and verifies the response ")
@allure.severity(allure.severity_level.CRITICAL)
def test_create_order_success(order_service, cart_service, created_product):
    product_id = created_product["id"]

    with allure.step("Prepare a non-empty cart"):
        cart_service.clear_cart(allow_error=True)
        cart_service.add_item({"product_id": product_id, "quantity": 2})

    with allure.step("Send POST /api/orders"):
        response = order_service.create_order()

    with allure.step(f"Verify status code is 201 (got {response.status_code})"):
        assert response.status_code == 201, (
            f"Expected 201, got {response.status_code}. Body: {response.text[:200]}"
        )

    body = response.json()
    order_status = body["status"]

    with allure.step(f"Verify status is 'pending' (got '{order_status}')"):
        assert order_status == "pending", (
            f"Expected status='pending', got '{order_status}'"
        )


@pytest.mark.regression
@allure.title("POST /api/orders — response matches the OrderResponse schema")
@allure.description(
    "Validates that the POST /api/orders response body can be parsed "
    "via the OrderResponse model."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_create_order_response_matches_schema(order_service, cart_service, created_product):
    product_id = created_product["id"]

    with allure.step("Prepare a non-empty cart"):
        cart_service.clear_cart(allow_error=True)
        cart_service.add_item({"product_id": product_id, "quantity": 2})

    with allure.step("Send POST /api/orders"):
        response = order_service.create_order()

    with allure.step(f"Verify status code is 201 (got {response.status_code})"):
        assert response.status_code == 201, (
            f"Expected 201, got {response.status_code}. Body: {response.text[:200]}"
        )

        body = response.json()

    with allure.step("Validate response against OrderResponse schema"):
        try:
            OrderResponse.model_validate(body)
        except ValidationError as e:
            pytest.fail(
                f"Response does not match OrderResponse schema.\n"
                f"Errors:\n{e}\n"
                f"Raw response:\n{body}",
                pytrace=False,
            )


@pytest.mark.regression
@allure.title("POST /api/orders — clears the cart after orders creation")
@allure.description("Verifies that POST /api/orders empties the cart.")
@allure.severity(allure.severity_level.CRITICAL)
def test_create_order_clears_cart(order_service, cart_service, created_product):
    product_id = created_product["id"]

    with allure.step("Prepare a non-empty cart"):
        cart_service.clear_cart(allow_error=True)
        cart_service.add_item({"product_id": product_id, "quantity": 2})

    with allure.step("Send POST /api/orders"):
        response = order_service.create_order()
        assert response.status_code == 201, (
            f"Order creation failed: {response.status_code}. "
            f"Body: {response.text[:200]}"
        )

    with allure.step("Send GET /api/cart and verify it is empty"):
        cart_response = cart_service.get_cart()
        cart = cart_response.json()

    with allure.step("Verify count=0"):
        assert cart["count"] == 0, f"Expected count=0, got {cart['count']}"

    with allure.step("Verify items=[]"):
        assert cart["items"] == [], f"Expected empty items, got {cart['items']}"

    with allure.step("Verify total=0"):
        assert cart["total"] == 0, f"Expected total=0, got {cart['total']}"


@pytest.mark.regression
@allure.title("POST /api/orders — created orders is retrievable via GET /api/orders/{id}")
@allure.description(
    "Creates an orders and verifies it can be fetched back by id."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_create_order_is_retrievable(order_service, cart_service, created_product):
    product_id = created_product["id"]

    with allure.step("Prepare a non-empty cart"):
        cart_service.clear_cart(allow_error=True)
        cart_service.add_item({"product_id": product_id, "quantity": 1})

    with allure.step("Send POST /api/orders"):
        create_response = order_service.create_order()
        assert create_response.status_code == 201, (
            f"Order creation failed: {create_response.status_code}. "
            f"Body: {create_response.text[:200]}"
        )
        created_id = create_response.json()["id"]

    with allure.step(f"Send GET /api/orders/{created_id}"):
        get_response = order_service.get_order_by_id(created_id)

    with allure.step(f"Verify GET returns 200 and id={created_id}"):
        assert get_response.status_code == 200, (
            f"Expected 200, got {get_response.status_code}. "
            f"Body: {get_response.text[:200]}"
        )
        assert get_response.json()["id"] == created_id, (
            f"Expected id={created_id}, got {get_response.json()['id']}"
        )


@pytest.mark.regression
@allure.title("POST /api/orders — empty cart returns 400 Bad Request")
@allure.description(
    "Attempts to create an orders with an empty cart and expects 400."
)
@allure.severity(allure.severity_level.NORMAL)
def test_create_order_empty_cart_400(order_service, cart_service):
    with allure.step("Ensure the cart is empty"):
        cart_service.clear_cart(allow_error=True)

    with allure.step("Send POST /api/orders with empty cart"):
        response = order_service.create_order(allow_error=True)

    with allure.step(f"Verify status code is 400 (got {response.status_code})"):
        assert response.status_code == 400, (
            f"Expected 400, got {response.status_code}. Body: {response.text[:200]}"
        )


@pytest.mark.regression
@allure.title("POST /api/orders — unauthorized request returns 401 Unauthorized")
@allure.description(
    "Attempts to create an orders without a token and expects 401."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_create_order_unauthorized(unauth_order_service):
    with allure.step("Send POST /api/orders without authorization"):
        response = unauth_order_service.create_order(allow_error=True)

    with allure.step(f"Verify status code is 401 (got {response.status_code})"):
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}. Body: {response.text[:200]}"
        )
