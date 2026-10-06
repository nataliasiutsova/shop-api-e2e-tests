import allure
import pytest
from faker import Faker
from pydantic import ValidationError

from models.cart import CartItemResponse

pytestmark = [
    allure.feature("Сart"),
    allure.story("Add item to cart"),
]

fake = Faker()


@pytest.mark.smoke
@allure.title("POST /cart/items — adds a product and returns 201")
@allure.description("Adds a valid product to the cart and verifies that returns 201 ")
@allure.severity(allure.severity_level.CRITICAL)
def test_add_item_success(empty_cart, created_product):
    product_id = created_product["id"]
    quantity = 1
    payload = {
        "product_id": product_id,
        "quantity": quantity
    }
    with allure.step(f"Send POST /cart/items with product_id={product_id}, quantity={quantity}"):
        response = empty_cart.add_item(payload)

    with allure.step(f"Verify status code is 201  (got {response.status_code})"):
        assert response.status_code == 201, f"Expected 200, got {response.status_code}. "


@pytest.mark.regression
@allure.title("POST /cart/items — response matches CartItemResponse schema")
@allure.description("Validates the POST /cart/items response body against CartItemResponse.")
@allure.severity(allure.severity_level.CRITICAL)
def test_add_item_response_matches_schema(empty_cart, created_product):
    product_id = created_product["id"]
    quantity = 2
    payload = {
        "product_id": product_id,
        "quantity": quantity
    }

    with allure.step(f"Send POST /cart/items with product_id={product_id}, quantity=2"):
        response = empty_cart.add_item(payload)

    with allure.step(f"Verify status code is 201 (got {response.status_code})"):
        assert response.status_code == 201, f"Expected 201, got {response.status_code}. "

        body = response.json()

    with allure.step("Validate response against CartItemResponse schema"):
        try:
            CartItemResponse.model_validate(body)
        except ValidationError as e:
            pytest.fail(
                f"Response does not match CartItemResponse schema.\n"
                f"Errors:\n{e}\n"
                f"Raw response:\n{body}",
                pytrace=False,
            )


@pytest.mark.regression
@allure.title("POST /cart/items — added item is visible via GET /api/cart")
@allure.description(
    "Adds a product via POST and verifies it appears in GET /api/cart with "
    "the correct quantity and totals."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_add_item_is_visible_in_cart(empty_cart, created_product):
    product_id = created_product["id"]
    quantity = 1
    payload = {
        "product_id": product_id,
        "quantity": quantity
    }

    with allure.step(f"Add product id={product_id} with quantity={quantity}"):
        empty_cart.add_item(payload)

    with allure.step("Send GET /api/cart"):
        response = empty_cart.get_cart()
        cart = response.json()

    with allure.step(f"Verify status code is 200 (got {response.status_code})"):
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. "

    with allure.step(f"Find item with product_id={product_id} in the cart"):
        items = [i for i in cart["items"] if i["product_id"] == product_id]

    with allure.step("Verify the item is present exactly once"):
        assert len(items) == 1, (
            f"Expected exactly one item with product_id={product_id}, got {len(items)}. "
            f"Cart items: {cart['items']}"
        )

    with allure.step(f"Verify quantity equals {quantity}"):
        assert items[0]["quantity"] == quantity, (
            f"Expected quantity={quantity}, got {items[0]['quantity']}"
        )

    with allure.step("Verify cart count is 1"):
        assert cart["count"] == 1, f"Expected count=1, got {cart['count']}"


@pytest.mark.regression
@allure.title("POST /cart/items — adding the same product twice increases quantity")
@allure.description(
    "Adds the same product twice and verifies that it stays as a single cart item "
    "with quantity equal to the sum of both additions."
)
@allure.severity(allure.severity_level.NORMAL)
def test_add_same_item_twice_increases_quantity(empty_cart, created_product):
    product_id = created_product["id"]
    quantity = 2
    payload = {
        "product_id": product_id,
        "quantity": quantity
    }

    with allure.step(f"First add: product_id={product_id}, quantity=2"):
        first_response = empty_cart.add_item(payload)

    with allure.step(f"Verify status code is 201 (got {first_response.status_code})"):
        assert first_response.status_code == 201, f"Expected 201, got {first_response.status_code}. "

    with allure.step(f"Second add: product_id={product_id}, quantity=1"):
        second_response = empty_cart.add_item({"product_id": product_id, "quantity": 1})

    with allure.step(f"Verify status code is 200 (got {second_response.status_code})"):
        assert second_response.status_code == 200, f"Expected 200, got {second_response.status_code}. "

    with allure.step("Send GET /api/cart and find the product"):
        cart = empty_cart.get_cart().json()
        items = [i for i in cart["items"] if i["product_id"] == product_id]

    with allure.step("Verify only one cart item exists for this product"):
        assert len(items) == 1, (
            f"Expected one item, got {len(items)}: {cart['items']}"
        )
    with allure.step("Verify quantity equals 3 (2 + 1)"):
        assert items[0]["quantity"] == 3, (
            f"Expected quantity=5, got {items[0]['quantity']}"
        )


@pytest.mark.regression
@allure.title("POST /cart/items — different products create separate cart items")
@allure.description(
    "Adds two different products and verifies that the cart contains two distinct items."
)
@allure.severity(allure.severity_level.NORMAL)
def test_add_two_different_products(empty_cart, created_products):
    product_1, product_2 = created_products

    with allure.step(f"Add product id={product_1['id']} with quantity=1"):
        empty_cart.add_item({"product_id": product_1["id"], "quantity": 1})

    with allure.step(f"Add product id={product_2['id']} with quantity=2"):
        empty_cart.add_item({"product_id": product_2["id"], "quantity": 2})

    with allure.step("Send GET /api/cart and verify both items are present"):
        cart = empty_cart.get_cart().json()

        product_ids = sorted(i["product_id"] for i in cart["items"])

    with allure.step("Verify cart contains both product ids"):
        assert product_ids == sorted([product_1["id"], product_2["id"]]), (
            f"Expected [{product_1['id']}, {product_2['id']}], got {product_ids}"
        )

    with allure.step("Verify cart count is 2"):
        assert cart["count"] == 2, f"Expected count=2, got {cart['count']}"


@pytest.mark.regression
@allure.title("POST /cart/items — quantity greater than product stock returns 400")
@allure.description(
    "Adds a product with quantity exceeding its available stock and verifies "
    "that the API rejects the request with 400 Bad Request and an explanatory message."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_add_item_quantity_exceeds_stock(empty_cart, created_product):
    product_id = created_product["id"]
    stock = created_product["stock"]
    too_much = stock + 1

    with allure.step(
            f"Send POST /cart/items with product_id={product_id}, "
            f"quantity={too_much} (stock is {stock})"
    ):
        response = empty_cart.add_item({"product_id": product_id, "quantity": too_much}, allow_error=True)

    with allure.step(f"Verify status code is 400 (got {response.status_code})"):
        assert response.status_code == 400, (
            f"Expected 400, got {response.status_code}. "
            f"Body: {response.text[:200]}"
        )

    with allure.step("Verify response body contains a meaningful error message"):
        body = response.json()
        error_text = str(body["error"]).lower()
        assert "insufficient stock" in error_text, f"Expected an error message about insufficient stock, got: {body}"

    with allure.step("Verify the item was not added to the cart"):
        cart = empty_cart.get_cart().json()
        product_ids = [i["product_id"] for i in cart["items"]]
        assert product_id not in product_ids, (
            f"Product id={product_id} should not be in cart after rejected request. "
            f"Cart items: {cart['items']}"
        )


@pytest.mark.regression
@allure.title("POST /cart/items — non-existent product returns 400 Not Found")
@allure.description(
    "Sends a POST with a product_id that does not exist and expects 400."
)
@allure.severity(allure.severity_level.NORMAL)
def test_add_item_nonexistent_product_400(cart_service):
    nonexistent_id = 999999
    quantity = fake.random_int(min=1, max=100)
    payload = {
        "product_id": nonexistent_id,
        "quantity": quantity
    }

    with allure.step(f"Send POST /cart/items with product_id={nonexistent_id}"):
        response = cart_service.add_item(payload, allow_error=True)

    with allure.step(f"Verify status code is 400 (got {response.status_code})"):
        assert response.status_code == 400, f"Expected 400, got {response.status_code}. "


@pytest.mark.regression
@allure.title("POST /cart/items — invalid quantity returns 422 Unprocessable Entity")
@allure.description(
    "Parameterized check of invalid quantity values: 0, -1, and a non-numeric string."
)
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("quantity, case", [
    (0, "zero quantity"),
    (-1, "negative quantity"),
    ("abc", "non-numeric quantity"),
])
def test_add_item_invalid_quantity(cart_service, created_product, quantity, case):
    allure.dynamic.title(f"POST /cart/items — rejects {case} with 422")

    product_id = created_product["id"]

    with allure.step(f"Case: {case}. Send product_id={product_id}, quantity={quantity!r}"):
        payload = {
            "product_id": product_id,
            "quantity": quantity
        }
        response = cart_service.add_item(payload, allow_error=True)

    with allure.step(f"Verify status code is 422 for {case} (got {response.status_code})"):
        assert response.status_code == 422, f"[{case}] Expected 422, got {response.status_code}. "


@pytest.mark.regression
@allure.title("POST /cart/items — rejects invalid payload: missing fields (422) and empty body (400)")
@allure.description(
    "Parameterized check of malformed payloads for POST /cart/items:\n"
    "- missing product_id → 422\n"
    "- missing quantity → 422\n"
    "- empty body {} → 400"
)
@allure.severity(allure.severity_level.MINOR)
@pytest.mark.parametrize("payload,  expected_status, case", [
    ({"quantity": 1}, 422, "missing product_id"),
    ({"product_id": 1}, 422, "missing quantity"),
    ({}, 400, "empty body"),
])
def test_add_item_missing_field(cart_service, payload, expected_status, case):
    allure.dynamic.title(f"POST /cart/items — rejects payload with {case} ({expected_status})")

    with allure.step(f"Case: {case}. Payload: {payload}"):
        response = cart_service.add_item(payload, allow_error=True)

    with allure.step(f"Verify status code is {expected_status} for {case} (got {response.status_code})"):
        assert response.status_code == expected_status, f"[{case}] Expected {expected_status}, got {response.status_code}. "


@pytest.mark.regression
@allure.title("POST /cart/items — unauthorized request returns 401 Unauthorized")
@allure.description(
    "Attempts to add an item without an authorization token and expects 401."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_add_item_unauthorized(unauth_cart_service, created_product):
    product_id = created_product["id"]
    payload = {
        "product_id": product_id,
        "quantity": fake.random_int(min=1, max=100)
    }

    with allure.step(f"Send POST /cart/items without authorization for product_id={product_id}"):
        response = unauth_cart_service.add_item(payload, allow_error=True)

    with allure.step(f"Verify status code is 401 (got {response.status_code})"):
        assert response.status_code == 401, f"Expected 401, got {response.status_code}. "
