import allure
import pytest

pytestmark = [
    allure.feature("Сart"),
    allure.story("Delete item from cart"),
]


@pytest.mark.regression
@allure.title("DELETE /cart/items/{id} — removes the item and returns 204")
@allure.description("Removes an existing cart item and verifies the response status is 204 No Content.")
@allure.severity(allure.severity_level.CRITICAL)
def test_delete_cart_item_success(cart_service, cart_with_custom_item):
    ctx = cart_with_custom_item(quantity=3)
    item_id = ctx["item_id"]

    with allure.step(f"Send DELETE /cart/items/{item_id}"):
        response = cart_service.delete_item(item_id)

    with allure.step(f"Verify status code is 204 (got {response.status_code})"):
        assert response.status_code == 204, (
            f"Expected 204, got {response.status_code}. "
            f"Body: {response.text[:200]}"
        )


@pytest.mark.regression
@allure.title("DELETE /cart/items/{id} — deleted item is no longer in the cart")
@allure.description(
    "Deletes a cart item and verifies it disappears from GET /api/cart."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_delete_cart_item_removed_from_cart(cart_service, cart_with_custom_item):
    ctx = cart_with_custom_item(quantity=3)
    item_id = ctx["item_id"]
    product_id = ctx["product_id"]

    with allure.step(f"Delete product id={item_id} from the cart"):
        response = cart_service.delete_item(item_id)
        assert response.status_code == 204, (
            f"Delete failed: {response.status_code}. Body: {response.text[:200]}"
        )

    with allure.step("Send GET /api/cart and verify item is gone"):
        cart_response = cart_service.get_cart()
        cart = cart_response.json()
        product_ids = [i["product_id"] for i in cart["items"]]

    with allure.step(f"Verify product id={product_id} is not in the cart"):
        assert product_id not in product_ids, (
            f"Product id={product_id} still in cart after delete. "
            f"Cart items: {cart['items']}"
        )

    with allure.step("Verify cart count decreased to 0"):
        assert cart["count"] == 0, f"Expected count=0, got {cart['count']}"


@pytest.mark.regression
@allure.title("DELETE /cart/items/{id} — deleting one item keeps the other items")
@allure.description(
    "Adds two different products, deletes one, and verifies the other remains in the cart."
)
@allure.severity(allure.severity_level.NORMAL)
def test_delete_one_of_two_items(cart_service, empty_cart, created_products):
    product_1, product_2 = created_products

    with allure.step("Add both products to the cart"):
        response_1 = cart_service.add_item({"product_id": product_1["id"], "quantity": 1})
        response_2 = cart_service.add_item({"product_id": product_2["id"], "quantity": 2})

        item_id_1 = response_1.json()["id"]
        item_id_2 = response_2.json()["id"]

    with allure.step(f"Delete cart item id={item_id_1} (product_id={product_1['id']})"):
        response = cart_service.delete_item(item_id_1)
        assert response.status_code == 204, (
            f"Delete failed: {response.status_code}. Body: {response.text[:200]}"
        )

    with allure.step("Send GET /api/cart"):
        cart = cart_service.get_cart().json()
        product_ids = [i["product_id"] for i in cart["items"]]

    with allure.step(f"Verify product id={product_1['id']} is gone"):
        assert product_1["id"] not in product_ids, (
            f"Deleted product id={product_1['id']} still in cart: {product_ids}"
        )

    with allure.step(f"Verify product id={product_2['id']} is still present"):
        assert product_2["id"] in product_ids, (
            f"Product id={product_2['id']} should remain in cart, got {product_ids}"
        )

    with allure.step("Verify cart count is 1"):
        assert cart["count"] == 1, f"Expected count=1, got {cart['count']}"


@pytest.mark.regression
@allure.title("DELETE /cart/items/{id} — cart total is recalculated after delete")
@allure.description(
    "Deletes an item and verifies the cart-level total equals the sum of remaining items."
)
@allure.severity(allure.severity_level.NORMAL)
def test_delete_cart_item_recalculates_total(cart_service, empty_cart, created_products):
    product_1, product_2 = created_products

    with allure.step("Add both products to the cart"):
        response_1 = cart_service.add_item({"product_id": product_1["id"], "quantity": 1})
        response_2 = cart_service.add_item({"product_id": product_2["id"], "quantity": 2})

        item_id_1 = response_1.json()["id"]

    with allure.step(f"Delete cart item id={item_id_1} (product_id={product_1['id']})"):
        response = cart_service.delete_item(item_id_1)
        assert response.status_code == 204, (
            f"Delete failed: {response.status_code}. Body: {response.text[:200]}"
        )

    with allure.step("Send GET /api/cart"):
        cart = cart_service.get_cart().json()

        expected_total = round(sum(i["total"] for i in cart["items"]), 2)
        actual_total = round(cart["total"], 2)

    with allure.step(
            f"Verify cart total = {actual_total} equals sum of item totals = {expected_total}"
    ):
        assert actual_total == expected_total, (
            f"cart.total={actual_total} but sum(items.total)={expected_total}"
        )


@pytest.mark.regression
@allure.title("DELETE /cart/items/{id} — deleting the same item twice returns 404")
@allure.description(
    "Deletes a cart item, then tries to delete it again and expects 404 Not Found."
)
@allure.severity(allure.severity_level.NORMAL)
def test_delete_cart_item_twice_returns_404(cart_service, cart_with_custom_item):
    ctx = cart_with_custom_item(quantity=2)
    item_id = ctx["item_id"]

    with allure.step(f"First delete of product id={item_id} — expect 204"):
        first = cart_service.delete_item(item_id)

        assert first.status_code == 204, (
            f"First delete failed: {first.status_code}. Body: {first.text[:200]}"
        )

    with allure.step(f"Second delete of item id={item_id} — expect 404"):
        second = cart_service.delete_item(item_id, allow_error=True)

    with allure.step(f"Verify second delete returns 404 (got {second.status_code})"):
        assert second.status_code == 404, (
            f"Expected 404, got {second.status_code}. Body: {second.text[:200]}"
        )


@pytest.mark.regression
@allure.title("DELETE /cart/items/{id} — non-existent cart item returns 404 Not Found")
@allure.description(
    "Attempts to delete a product that is not in the cart and expects 404."
)
@allure.severity(allure.severity_level.MINOR)
def test_delete_nonexistent_cart_item_404(cart_service, empty_cart):
    nonexistent_id = 999999

    with allure.step(f"Send DELETE /cart/items/{nonexistent_id}"):
        response = cart_service.delete_item(nonexistent_id, allow_error=True)

    with allure.step(f"Verify status code is 404 (got {response.status_code})"):
        assert response.status_code == 404, (
            f"Expected 404, got {response.status_code}. Body: {response.text[:200]}"
        )


@pytest.mark.regression
@allure.title("DELETE /cart/items/{id} — unauthorized request returns 401 Unauthorized")
@allure.description(
    "Attempts to delete a cart item without an authorization token and expects 401."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_delete_cart_item_unauthorized(unauth_cart_service, cart_with_item, created_product):
    item_id = cart_with_item["item_id"]

    with allure.step(f"Send DELETE /cart/items/{item_id} without authorization"):
        response = unauth_cart_service.delete_item(item_id, allow_error=True)

    with allure.step(f"Verify status code is 401 (got {response.status_code})"):
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}. Body: {response.text[:200]}"
        )


@pytest.mark.regression
@allure.title("DELETE /cart/items/{id} — unauthorized request does not remove the item")
@allure.description(
    "Attempts an unauthorized delete and verifies the cart item is still present."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_delete_cart_item_unauthorized_does_not_remove(cart_service, unauth_cart_service, cart_with_item, ):
    item_id = cart_with_item["item_id"]
    product_id = cart_with_item["product_id"]

    with allure.step(f"Attempt to delete product id={item_id} without authorization"):
        response = unauth_cart_service.delete_item(item_id, allow_error=True)
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}. Body: {response.text[:200]}"
        )

    with allure.step("Send GET /api/cart and verify item is still present"):
        cart = cart_service.get_cart().json()
        product_ids = [i["product_id"] for i in cart["items"]]

    with allure.step(f"Verify product id={product_id} is still in the cart"):
        assert product_id in product_ids, (
            f"Product id={product_id} was removed by unauthorized request! "
            f"Cart items: {cart['items']}"
        )
