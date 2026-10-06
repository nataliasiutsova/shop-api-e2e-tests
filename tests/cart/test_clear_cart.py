import allure
import pytest

pytestmark = [
    allure.feature("Сart"),
    allure.story("Clear the cart"),
]


@pytest.mark.regression
@allure.title("DELETE /cart — clears the cart and returns 204 No Content")
@allure.description("Sends DELETE /cart with items in the cart and verifies the response is 204")
@allure.severity(allure.severity_level.CRITICAL)
def test_clear_cart_success(cart_service, cart_with_custom_item):
    cart_with_custom_item(quantity=3)

    with allure.step("Send DELETE /cart"):
        response = cart_service.clear_cart()

    with allure.step(f"Verify status code is 204 (got {response.status_code})"):
        assert response.status_code == 204, (
            f"Expected 204, got {response.status_code}. "
            f"Body: {response.text[:200]}"
        )


@pytest.mark.regression
@allure.title("DELETE /cart — cart is empty after clearing")
@allure.description(
    "Clears the cart and verifies GET /api/cart returns an empty cart: "
    "count=0, items=[], total=0."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_clear_cart_empties_cart(cart_service, cart_with_custom_item):
    cart_with_custom_item(quantity=3)

    with allure.step("Send DELETE /cart"):
        response = cart_service.clear_cart()
        assert response.status_code == 204, (
            f"Clear failed: {response.status_code}. Body: {response.text[:200]}"
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
@allure.title("DELETE /cart — clears multiple items at once")
@allure.description(
    "Adds two different products and verifies DELETE /cart removes all of them."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_clear_cart_with_multiple_items(cart_service, empty_cart, created_products):
    product_1, product_2 = created_products

    with allure.step("Add both products to the cart"):
        cart_service.add_item({"product_id": product_1["id"], "quantity": 1})
        cart_service.add_item({"product_id": product_2["id"], "quantity": 2})

    with allure.step("Verify the cart has 2 items before clearing"):
        cart_before = cart_service.get_cart().json()
        assert cart_before["count"] == 2, (
            f"Expected count=2 before clear, got {cart_before['count']}. "
            f"Items: {cart_before['items']}"
        )

    with allure.step("Send DELETE /cart"):
        response = cart_service.clear_cart()

        assert response.status_code == 204, (
            f"Clear failed: {response.status_code}. Body: {response.text[:200]}"
        )

    with allure.step("Send GET /api/cart and verify all items were removed"):
        cart_after = cart_service.get_cart().json()

        assert cart_after["count"] == 0, f"Expected count=0, got {cart_after['count']}"
        assert cart_after["items"] == [], f"Expected empty items, got {cart_after['items']}"
        assert cart_after["total"] == 0, f"Expected total=0, got {cart_after['total']}"


@pytest.mark.regression
@allure.title("DELETE /cart — clearing an already empty cart returns 204")
@allure.description(
    "Verifies that DELETE /cart on an empty cart does not raise an error "
    "and returns 204 No Content."
)
@allure.severity(allure.severity_level.MINOR)
def test_clear_empty_cart(cart_service, empty_cart):
    with allure.step("Send DELETE /cart on an empty cart"):
        response = cart_service.clear_cart(allow_error=True)

    with allure.step(f"Verify status code is 204 (got {response.status_code})"):
        assert response.status_code == 204, (
            f"Expected 204, got {response.status_code}. "
            f"Body: {response.text[:200]}"
        )


@pytest.mark.regression
@allure.title("DELETE /cart — unauthorized request returns 401 Unauthorized")
@allure.description(
    "Attempts to clear the cart without an authorization token and expects 401."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_clear_cart_unauthorized(unauth_cart_service):
    with allure.step("Send DELETE /cart without authorization"):
        response = unauth_cart_service.clear_cart(allow_error=True)

    with allure.step(f"Verify status code is 401 (got {response.status_code})"):
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}. Body: {response.text[:200]}"
        )


@pytest.mark.regression
@allure.title("DELETE /cart — unauthorized request does not clear the cart")
@allure.description(
    "Attempts an unauthorized clear and verifies the cart items are still present."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_clear_cart_unauthorized_does_not_clear(
        cart_service, cart_with_custom_item, unauth_cart_service
):
    ctx = cart_with_custom_item(quantity=2)
    product_id = ctx["product_id"]

    with allure.step("Attempt to clear the cart without authorization"):
        response = unauth_cart_service.clear_cart(allow_error=True)
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}. Body: {response.text[:200]}"
        )

    with allure.step("Send GET /api/cart and verify the item is still present"):
        cart = cart_service.get_cart().json()
        product_ids = [i["product_id"] for i in cart["items"]]

    with allure.step(f"Verify product id={product_id} is still in the cart"):
        assert product_id in product_ids, (
            f"Product id={product_id} was removed by unauthorized request! "
            f"Cart items: {cart['items']}"
        )
