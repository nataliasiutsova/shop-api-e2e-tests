import uuid

import allure
import pytest

pytestmark = [
    pytest.mark.e2e,
    allure.feature("E2E")
]


@pytest.mark.smoke
@allure.title("E2E — create product, add to cart, place orders")
@allure.description(
    "Full checkout flow across three services:\n"
    "1. Create a product (POST /products)\n"
    "2. Add it to the cart (POST /cart/items)\n"
    "3. Place an orders (POST /orders)\n"
    "4. Verify the orders is created with the correct items and total"
)
@allure.severity(allure.severity_level.CRITICAL)
def test_checkout_flow(cart_service, order_service, empty_cart, created_product):
    product_id = created_product["id"]
    quantity = 2
    expected_total = round(created_product["price"] * quantity, 2)

    with allure.step(f"Add product id={product_id} with quantity={quantity} to the cart"):
        response = cart_service.add_item({"product_id": product_id, "quantity": quantity})
        assert response.status_code == 201, (
            f"Add to cart failed: {response.status_code}. Body: {response.text[:200]}"
        )

    with allure.step("Verify the cart has one item with the correct total"):
        cart = cart_service.get_cart().json()
        assert cart["count"] == 1, f"Expected count=1, got {cart['count']}"
        assert round(cart["total"], 2) == expected_total, (
            f"Cart total={cart['total']} but expected={expected_total}"
        )

    with allure.step("Place an orders (POST /orders)"):
        response = order_service.create_order()
        assert response.status_code == 201, (
            f"Order creation failed: {response.status_code}. Body: {response.text[:200]}"
        )
        order = response.json()
        order_id = order["id"]

    with allure.step("Verify the orders total and status"):
        assert round(order["total"], 2) == expected_total, (
            f"Order total={order['total']} but expected={expected_total}"
        )
        assert order["status"] == "pending", (
            f"Expected status='pending', got '{order['status']}'"
        )

    with allure.step("Verify the orders contains the product we added"):
        product_ids = [item["product_id"] for item in order["items"]]
        assert product_id in product_ids, (
            f"Product id={product_id} not found in orders items: {product_ids}"
        )


@pytest.mark.regression
@allure.title("E2E — cart is cleared after placing an orders")
@allure.description(
    "Verifies that after a successful POST /orders, the cart becomes empty."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_cart_is_cleared_after_checkout(
        cart_service, order_service, empty_cart, created_product
):
    product_id = created_product["id"]

    with allure.step(f"Add product id={product_id} to the cart"):
        cart_service.add_item({"product_id": product_id, "quantity": 1})

    with allure.step("Place an orders"):
        response = order_service.create_order()
        assert response.status_code == 201, (
            f"Order creation failed: {response.status_code}. Body: {response.text[:200]}"
        )
        order_id = response.json()["id"]

    with allure.step("Send GET /cart and verify it is empty"):
        cart = cart_service.get_cart().json()
        allure.attach(
            str(cart),
            name="Cart after orders",
            attachment_type=allure.attachment_type.TEXT,
        )

    with allure.step("Verify count=0"):
        assert cart["count"] == 0, f"Expected count=0, got {cart['count']}"

    with allure.step("Verify items=[]"):
        assert cart["items"] == [], f"Expected empty items, got {cart['items']}"


@pytest.mark.regression
@allure.title("E2E — orders keeps a snapshot of the product data")
@allure.description(
    "Places an orders, then updates the product price and name.\n"
    "Verifies the orders keeps the original values — it's a snapshot, "
    "not a live reference to the product."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_order_keeps_product_snapshot(
        cart_service, order_service, product_service, empty_cart, created_product
):
    product_id = created_product["id"]
    original_price = created_product["price"]
    original_name = created_product["name"]

    with allure.step(f"Add product id={product_id} to the cart"):
        cart_service.add_item({"product_id": product_id, "quantity": 1})

    with allure.step("Place an orders"):
        order = order_service.create_order().json()
        order_id = order["id"]
        item = order["items"][0]

    with allure.step(
            f"Verify the orders item has original values: "
            f"price={original_price}, name='{original_name}'"
    ):
        assert item["price"] == original_price, (
            f"Order item price={item['price']} but original={original_price}"
        )
        assert item["product_name"] == original_name, (
            f"Order item name='{item['product_name']}' but original='{original_name}'"
        )

    with allure.step("Update the product: change name and price"):
        product_service.update_product_by_id(
            product_id,
            {"name": f"Updated-{uuid.uuid4().hex[:6]}", "price": 999.99},
        )

    with allure.step(f"Fetch orders id={order_id} again and verify it did NOT change"):
        order_after = order_service.get_order_by_id(order_id).json()
        item_after = order_after["items"][0]
        allure.attach(
            str(order_after),
            name="Order after product update",
            attachment_type=allure.attachment_type.TEXT,
        )

    with allure.step("Verify orders still has original price"):
        assert item_after["price"] == original_price, (
            f"Order price changed after product update: "
            f"{item_after['price']} vs {original_price}"
        )

    with allure.step("Verify orders still has original name"):
        assert item_after["product_name"] == original_name, (
            f"Order name changed after product update: "
            f"'{item_after['product_name']}' vs '{original_name}'"
        )


@pytest.mark.smoke
@allure.title("E2E — placing an orders with an empty cart returns 400")
@allure.description(
    "Verifies that POST /orders fails with 400 when the cart is empty."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_checkout_empty_cart_400(order_service, empty_cart):
    with allure.step("Ensure the cart is empty"):
        cart = empty_cart.get_cart().json()
        assert cart["count"] == 0, (
            f"Cart should be empty for this test, got count={cart['count']}"
        )

    with allure.step("Send POST /orders with empty cart"):
        response = order_service.create_order(allow_error=True)
        allure.attach(
            response.text[:1000],
            name="Response for empty cart",
            attachment_type=allure.attachment_type.JSON,
        )

    with allure.step(f"Verify status code is 400 (got {response.status_code})"):
        assert response.status_code == 400, (
            f"Expected 400, got {response.status_code}. Body: {response.text[:200]}"
        )


@pytest.mark.regression
@allure.title("E2E — cannot add more than available stock to the cart")
@allure.description(
    "Verifies that adding a quantity greater than product stock fails with 400."
)
@allure.severity(allure.severity_level.NORMAL)
def test_cannot_exceed_stock(cart_service, empty_cart, created_product):
    product_id = created_product["id"]
    stock = created_product["stock"]
    too_much = stock + 1

    allure.attach(
        f"product_id={product_id}, stock={stock}, requested={too_much}",
        name="Test data",
        attachment_type=allure.attachment_type.TEXT,
    )

    with allure.step(f"Add quantity={too_much} (stock={stock}) to the cart"):
        response = cart_service.add_item(
            {"product_id": product_id, "quantity": too_much},
            allow_error=True,
        )
        allure.attach(
            response.text[:1000],
            name="Response for exceeding stock",
            attachment_type=allure.attachment_type.JSON,
        )

    with allure.step(f"Verify status code is 400 (got {response.status_code})"):
        assert response.status_code == 400, (
            f"Expected 400, got {response.status_code}. Body: {response.text[:200]}"
        )

    with allure.step("Verify the cart is still empty"):
        cart = cart_service.get_cart().json()
        assert cart["count"] == 0, (
            f"Cart should be empty after rejected add, got count={cart['count']}"
        )


@pytest.mark.regression
@allure.title("E2E — orders with multiple different products")
@allure.description(
    "Adds two different products to the cart, places an orders, "
    "and verifies both items are included with the correct totals."
)
@allure.severity(allure.severity_level.NORMAL)
def test_multi_item_order(
        cart_service, order_service, empty_cart, created_products
):
    product_1, product_2 = created_products

    with allure.step("Add both products to the cart"):
        cart_service.add_item({"product_id": product_1["id"], "quantity": 1})
        cart_service.add_item({"product_id": product_2["id"], "quantity": 2})

    with allure.step("Verify the cart has 2 items"):
        cart = cart_service.get_cart().json()
        assert cart["count"] == 2, f"Expected count=2, got {cart['count']}"
        cart_total = round(cart["total"], 2)

    with allure.step("Place an orders"):
        order = order_service.create_order().json()
        order_id = order["id"]
        allure.attach(
            str(order),
            name="Created orders",
            attachment_type=allure.attachment_type.TEXT,
        )

    with allure.step("Verify the orders has 2 items and the same total as the cart"):
        assert len(order["items"]) == 2, (
            f"Expected 2 items, got {len(order['items'])}"
        )
        assert round(order["total"], 2) == cart_total, (
            f"Order total={order['total']} but cart total={cart_total}"
        )

    with allure.step("Verify both product ids are present in the orders"):
        order_product_ids = sorted(i["product_id"] for i in order["items"])
        expected_product_ids = sorted([product_1["id"], product_2["id"]])
        assert order_product_ids == expected_product_ids, (
            f"Expected {expected_product_ids}, got {order_product_ids}"
        )

    with allure.step("Cleanup: cancel the created orders (best-effort)"):
        order_service.cancel_order(order_id, allow_error=True)


@pytest.mark.smoke
@allure.title("E2E — cancel an orders and verify it stays cancelled")
@allure.description(
    "Places an orders, cancels it via PUT /orders/{id}/cancel, "
    "and verifies the status is 'cancelled' via both response and GET /orders/{id}."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_cancel_order_flow(cart_service, order_service, empty_cart, created_product):
    product_id = created_product["id"]

    with allure.step(f"Add product id={product_id} to the cart"):
        cart_service.add_item({"product_id": product_id, "quantity": 2})

    with allure.step("Place an orders"):
        order = order_service.create_order().json()
        order_id = order["id"]
        assert order["status"] == "pending", (
            f"Expected fresh orders status='pending', got '{order['status']}'"
        )

    with allure.step(f"Cancel orders id={order_id}"):
        response = order_service.cancel_order(order_id)
        assert response.status_code == 200, (
            f"Cancel failed: {response.status_code}. Body: {response.text[:200]}"
        )

    with allure.step("Verify the cancel response has status 'cancelled'"):
        cancelled = response.json()
        cancelled_status = cancelled["status"]
        cancelled_id = cancelled["id"]

        assert cancelled_status == "cancelled", (
            f"Expected status='cancelled', got '{cancelled_status}'"
        )
        assert cancelled_id == order_id, (
            f"Expected id={order_id}, got {cancelled_id}"
        )

    with allure.step(f"Send GET /orders/{order_id} and verify status is 'cancelled'"):
        order_after = order_service.get_order_by_id(order_id).json()
        order_after_status = order_after["status"]

        assert order_after_status == "cancelled", (
            f"Status not persisted: got '{order_after_status}'"
        )


@pytest.mark.regression
@allure.title("E2E — cancelling an already cancelled orders returns 400")
@allure.description(
    "Cancels an orders, then attempts to cancel it again and expects 400."
)
@allure.severity(allure.severity_level.NORMAL)
def test_cancel_order_twice(cart_service, order_service, empty_cart, created_product):
    product_id = created_product["id"]

    with allure.step("Place an orders"):
        cart_service.add_item({"product_id": product_id, "quantity": 1})
        order = order_service.create_order().json()
        order_id = order["id"]

    with allure.step(f"First cancel of orders id={order_id} — expect 200"):
        first = order_service.cancel_order(order_id)
        assert first.status_code == 200, (
            f"First cancel failed: {first.status_code}. Body: {first.text[:200]}"
        )

    with allure.step(f"Second cancel of orders id={order_id} — expect 400"):
        second = order_service.cancel_order(order_id, allow_error=True)
        allure.attach(
            second.text[:1000],
            name="Second cancel response",
            attachment_type=allure.attachment_type.JSON,
        )
        assert second.status_code == 400, (
            f"Expected 400, got {second.status_code}. Body: {second.text[:200]}"
        )


@pytest.mark.regression
@allure.title("E2E — cancelling an orders does not return items to the cart")
@allure.description(
    "Places an orders, cancels it, and verifies the cart remains empty."
)
@allure.severity(allure.severity_level.NORMAL)
def test_cancel_order_does_not_refill_cart(
        cart_service, order_service, empty_cart, created_product
):
    product_id = created_product["id"]

    with allure.step("Add product to cart and place an orders"):
        cart_service.add_item({"product_id": product_id, "quantity": 2})
        order = order_service.create_order().json()
        order_id = order["id"]

    with allure.step("Verify cart is empty after orders creation"):
        cart = cart_service.get_cart().json()
        assert cart["count"] == 0, (
            f"Cart should be empty after orders, got count={cart['count']}"
        )

    with allure.step(f"Cancel orders id={order_id}"):
        response = order_service.cancel_order(order_id)
        assert response.status_code == 200, (
            f"Cancel failed: {response.status_code}. Body: {response.text[:200]}"
        )

    with allure.step("Verify cart is still empty after cancel"):
        cart = cart_service.get_cart().json()
        allure.attach(
            str(cart),
            name="Cart after cancel",
            attachment_type=allure.attachment_type.TEXT,
        )
        assert cart["count"] == 0, (
            f"Cancel should not refill the cart, got count={cart['count']}"
        )
        assert cart["items"] == [], (
            f"Cancel should not refill the cart, got items={cart['items']}"
        )
