import allure
import pytest

pytestmark = [
    allure.feature("Сart"),
    allure.story("Update item to cart"),
]


@pytest.mark.regression
@allure.title("PUT /cart/items/{id} — updates quantity and returns 200 OK")
@allure.description(
    "Updates the quantity of an existing cart item and verifies that "
    "the response has status 200 with an empty body."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_update_cart_item_success(cart_service, cart_with_custom_item):
    new_quantity = 7
    ctx = cart_with_custom_item(quantity=5)
    item_id = ctx["item_id"]

    with allure.step(f"Send PUT /cart/items/{item_id} with quantity={new_quantity}"):
        response = cart_service.update_item(item_id, {"quantity": new_quantity})

    with allure.step(f"Verify status code is 200 (got {response.status_code})"):
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. "


@pytest.mark.regression
@allure.title("PUT /cart/items/{id} — updated quantity is persisted in GET /api/cart")
@allure.description(
    "Updates quantity via PUT and verifies that GET /api/cart returns the new quantity."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_update_cart_item_is_persisted(cart_service, cart_with_custom_item):
    ctx = cart_with_custom_item(quantity=5)
    item_id = ctx["item_id"]
    product_id = ctx["product_id"]
    new_quantity = 9

    with allure.step(f"Update product id={item_id} to quantity={new_quantity}"):
        response = cart_service.update_item(item_id, {"quantity": new_quantity})
        assert response.status_code == 200, f"Update failed: {response.status_code}."

    with allure.step("Send GET /api/cart"):
        cart_response = cart_service.get_cart()
        cart = cart_response.json()

    with allure.step(f"Find item with product_id={product_id}"):
        items = [i for i in cart["items"] if i["product_id"] == ctx["product_id"]]

    with allure.step("Verify the item is present exactly once"):
        assert len(items) == 1, (
            f"Expected one item with product_id={product_id}, got {len(items)}. "
            f"Cart items: {cart['items']}"
        )

    with allure.step(f"Verify quantity equals {new_quantity}"):
        assert items[0]["quantity"] == new_quantity, (
            f"Expected quantity={new_quantity}, got {items[0]['quantity']}"
        )


@pytest.mark.regression
@allure.title("PUT /cart/items/{id} — cart total is recalculated after update")
@allure.description(
    "Verifies that after updating quantity, the cart-level total is recalculated "
    "and equals the sum of item totals."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_update_cart_item_recalculates_total(cart_service, cart_with_custom_item):
    ctx = cart_with_custom_item(quantity=5)
    item_id = ctx["item_id"]
    product_id = ctx["product_id"]
    new_quantity = 10

    with allure.step(f"Update product id={item_id} to quantity={new_quantity}"):
        cart_service.update_item(item_id, {"quantity": new_quantity})

    with allure.step("Send GET /api/cart"):
        cart = cart_service.get_cart().json()
        expected_total = round(sum(i["total"] for i in cart["items"]), 2)
        actual_total = round(cart["total"], 2)

    with allure.step(f"Verify cart total = {actual_total} equals sum of item totals = {expected_total}"):
        assert actual_total == expected_total, (
            f"cart.total={actual_total} but sum(items.total)={expected_total}"
        )

        item = next(i for i in cart["items"] if i["product_id"] == product_id)
        expected_item_total = round(item["price"] * new_quantity, 2)
        actual_item_total = round(item["total"], 2)

    with allure.step(f"Verify item total = {actual_item_total} equals "
                     f"price {item['price']} * quantity {new_quantity} = {expected_item_total}"
                     ):
        assert actual_item_total == expected_item_total, (
            f"Item total={actual_item_total} but "
            f"price*quantity={expected_item_total}"
        )


@pytest.mark.regression
@allure.title("PUT /cart/items/{id} — non-existent cart item returns 404 Not Found")
@allure.description(
    "Attempts to update a product that is not in the cart and expects 404."
)
@allure.severity(allure.severity_level.NORMAL)
def test_update_nonexistent_cart_item_404(empty_cart):
    nonexistent_id = 999999

    with allure.step(f"Send PUT /cart/items/{nonexistent_id} with quantity=2"):
        response = empty_cart.update_item(nonexistent_id, {"quantity": 2}, allow_error=True)

    with allure.step(f"Verify status code is 404 (got {response.status_code})"):
        assert response.status_code == 404, f"Expected 404, got {response.status_code}."


@pytest.mark.regression
@allure.title("PUT /cart/items/{id} — invalid quantity returns 422 Unprocessable Entity")
@allure.description(
    "Parameterized check of invalid quantity values: 0, -1, and a non-numeric string."
)
@allure.severity(allure.severity_level.MINOR)
@pytest.mark.parametrize("quantity, case", [
    (0, "zero quantity"),
    (-1, "negative quantity"),
    ("abc", "non-numeric quantity"),
])
def test_update_cart_item_invalid_quantity(cart_service, cart_with_item, quantity, case):
    allure.dynamic.title(f"PUT /cart/items/{{id}} — rejects {case} with 422")

    item_id = cart_with_item["item_id"]

    with allure.step(f"Case: {case}. Send PUT with quantity={quantity!r}"):
        response = cart_service.update_item(item_id, {"quantity": quantity}, allow_error=True)

    with allure.step(f"Verify status code is 422 for {case} (got {response.status_code})"):
        assert response.status_code == 422, (
            f"[{case}] Expected 422, got {response.status_code}. "
            f"Body: {response.text[:200]}"
        )


@pytest.mark.regression
@allure.title("PUT /cart/items/{id} — missing quantity field returns 400")
@allure.description(
    "Sends a PUT payload without the 'quantity' field and expects 400."
)
@allure.severity(allure.severity_level.MINOR)
def test_update_cart_item_missing_quantity(cart_service, cart_with_item):
    item_id = cart_with_item["item_id"]

    with allure.step(f"Send PUT /cart/items/{item_id} with empty payload {{}}"):
        response = cart_service.update_item(item_id, {}, allow_error=True)

    with allure.step(f"Verify status code is 400 (got {response.status_code})"):
        assert response.status_code == 400, (
            f"Expected 400, got {response.status_code}. "
            f"Body: {response.text[:200]}"
        )


@pytest.mark.regression
@allure.title("PUT /cart/items/{id} — unauthorized request returns 401 Unauthorized")
@allure.description(
    "Attempts to update a cart item without an authorization token and expects 401."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_update_cart_item_unauthorized(unauth_cart_service, cart_service, cart_with_item):
    item_id = cart_with_item["item_id"]

    with allure.step(f"Send PUT /cart/items/{item_id} without authorization"):
        response = unauth_cart_service.update_item(item_id, {"quantity": 2}, allow_error=True)

    with allure.step(f"Verify status code is 401 (got {response.status_code})"):
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}. "
            f"Body: {response.text[:200]}"
        )


@pytest.mark.regression
@allure.title("PUT /cart/items/{id} — quantity greater than stock returns 400")
@allure.description(
    "Sets the cart item quantity to a value exceeding the product stock "
    "and verifies the API rejects it with 400 and leaves the cart unchanged."
)
@allure.severity(allure.severity_level.NORMAL)
def test_update_cart_item_quantity_exceeds_stock(cart_service, cart_with_custom_item, created_product):
    stock = created_product["stock"]
    initial_quantity = 1
    too_much = stock + 1

    ctx = cart_with_custom_item(quantity=initial_quantity)
    product_id = ctx["product_id"]
    item_id = ctx["item_id"]

    with allure.step(f"Send PUT /cart/items/{item_id} with quantity={too_much} (stock={stock})"):
        response = cart_service.update_item(item_id, {"quantity": too_much}, allow_error=True)

    with allure.step(f"Verify status code is 400 (got {response.status_code})"):
        assert response.status_code == 400, (
            f"Expected 400, got {response.status_code}. Body: {response.text[:200]}"
        )

    with allure.step("Verify the cart item quantity was NOT changed"):
        cart = cart_service.get_cart().json()
        item = next(
            (i for i in cart["items"] if i["product_id"] == product_id),
            None,
        )
        assert item is not None, (
            f"Product id={product_id} not found in cart after failed update. "
            f"Cart items: {cart['items']}"
        )
        assert item["quantity"] == initial_quantity, (
            f"Quantity should remain {initial_quantity} after rejected update, "
            f"got {item['quantity']}"
        )
