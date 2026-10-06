import allure
import pytest
from pydantic import ValidationError

from models.cart import CartItemResponse, CartResponse

pytestmark = [
    allure.feature("Сart"),
    allure.story("Get cart"),
]


@pytest.mark.smoke
@allure.title("GET /api/cart — returns 200 OK")
@allure.description(
    "Verifies that GET /api/cart returns 200 OK"
)
@allure.severity(allure.severity_level.CRITICAL)
def test_get_cart_returns_200(cart_service, empty_cart):
    with allure.step("Send GET /api/cart"):
        response = cart_service.get_cart()

    with allure.step("Verify status code 200"):
        assert response.status_code == 200, f"Expected 200, got {response.status_code}."


@pytest.mark.regression
@allure.title("GET /api/cart — response matches the CartResponse schema")
@allure.description("Validates the GET /api/cart body against CartResponse")
@allure.severity(allure.severity_level.CRITICAL)
def test_get_cart_response_matches_schema(cart_service, cart_with_item):
    with allure.step("Send GET /api/cart"):
        response = cart_service.get_cart()

    with allure.step("Verify status code 200"):
        assert response.status_code == 200, f"Expected 200, got {response.status_code}."

    cart = response.json()

    with allure.step("Validate cart response against CartResponse"):
        try:
            CartResponse.model_validate(cart)
        except ValidationError as e:
            pytest.fail(
                f"Cart response does not match CartResponse schema.\n"
                f"Errors:\n{e}\n"
                f"Raw cart:\n{cart}",
                pytrace=False,
            )

    with allure.step(f"Validate each of {len(cart['items'])} cart items against CartItemResponse"):
        for idx, raw in enumerate(cart["items"]):
            with allure.step(f"Validate cart item at index (product_id={raw.get('product_id', 'N/A')})"):
                try:
                    CartItemResponse.model_validate(raw)
                except ValidationError as e:
                    pytest.fail(
                        f"Cart item at index (product_id={raw.get('product_id', 'N/A')}) "
                        f"does not match CartItemResponse schema.\n"
                        f"Errors:\n{e}\n"
                        f"Raw item:\n{raw}",
                        pytrace=False,
                    )


@pytest.mark.regression
@allure.title("GET /api/cart — empty cart returns count=0, items=[], total=0")
@allure.description(
    "Verifies that after clearing the cart, GET /api/cart returns an empty cart "
    "with count=0, an empty items list, and total=0."
)
@allure.severity(allure.severity_level.NORMAL)
def test_get_cart_empty(cart_service, empty_cart):
    with allure.step("Send GET /api/cart on a clean cart"):
        response = cart_service.get_cart()
        cart_data = response.json()

    with allure.step("Verify status code 200"):
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    with allure.step("Verify the cart is empty"):
        assert cart_data["count"] == 0, f"Expected count=0, got {cart_data['count']}"
        assert cart_data["items"] == [], f"Expected empty items, got {cart_data['items']}"
        assert cart_data["total"] == 0, f"Expected total=0, got {cart_data['total']}"


@pytest.mark.regression
@allure.title("GET /api/cart — returns the item that was added")
@allure.description(
    "Adds a product to the cart and verifies that GET /api/cart returns it "
    "with the correct product_id, quantity, and totals."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_get_cart_contains_added_item(cart_service, cart_with_item):
    product_id = cart_with_item["product_id"]
    expected_quantity = cart_with_item["quantity"]

    with allure.step("Send GET /api/cart"):
        response = cart_service.get_cart()
        cart = response.json()

    with allure.step(f"Find item with product_id={product_id} in the cart"):
        items = [i for i in cart["items"] if i["product_id"] == product_id]

    with allure.step("Verify the item is present exactly once"):
        assert len(items) == 1, (
            f"Expected exactly one item with product_id={product_id}, got {len(items)}. "
            f"Cart items: {cart['items']}"
        )

    with allure.step(f"Verify quantity equals {expected_quantity}"):
        assert items[0]["quantity"] == expected_quantity, (
            f"Expected quantity={expected_quantity}, got {items[0]['quantity']}"
        )

    with allure.step("Verify total = price * quantity for the found item"):
        item = items[0]
        expected_total = round(item["price"] * item["quantity"], 2)
        assert round(item["total"], 2) == expected_total, (
            f"Item total={item['total']} but price*quantity={expected_total}"
        )


@pytest.mark.regression
@allure.title("GET /api/cart — unauthorized request returns 401 Unauthorized")
@allure.description(
    "Attempts to fetch the cart without an authorization token and expects 401."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_get_cart_unauthorized(unauth_cart_service):
    with allure.step("Send GET /api/cart without authorization"):
        response = unauth_cart_service.get_cart(allow_error=True)

    with allure.step("Verify status code 401"):
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}. Body: {response.text[:200]}"
        )
