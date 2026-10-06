import allure
import pytest
from pydantic import ValidationError

from models.order import OrderCancelResponse

pytestmark = [
    allure.feature("Order"),
    allure.story("Cancel orders"),
]


@pytest.mark.regression
@allure.title("PUT /api/orders/{id}/cancel — cancels a pending orders and returns 200 OK")
@allure.description(
    "Cancels a pending orders and verifies the response matches "
    "OrderCancelResponse with status 'cancelled'."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_cancel_order_success(order_service, created_order):
    order_id = created_order["id"]

    with allure.step(f"Send PUT /api/orders/{order_id}/cancel"):
        response = order_service.cancel_order(order_id)

    with allure.step(f"Verify status code is 200 (got {response.status_code})"):
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Body: {response.text[:200]}"

    body = response.json()

    with allure.step(f"Verify orders id={order_id}"):
        assert body["id"] == order_id, f"Expected id={order_id}, got {body['id']}"

    with allure.step(f"Verify status is 'cancelled' (got '{body['status']}')"):
        assert body["status"] == "cancelled", f"Expected status='cancelled', got '{body['status']}'"


@pytest.mark.regression
@allure.title("PUT /api/orders/{id}/cancel — response matches the OrderCancelResponse schema")
@allure.description(
    "Validates that the PUT /api/orders/{id}/cancel response body can be parsed "
    "via the OrderCancelResponse model."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_cancel_order_response_matches_schema(order_service, created_order):
    order_id = created_order["id"]

    with allure.step(f"Send PUT /api/orders/{order_id}/cancel"):
        response = order_service.cancel_order(order_id)

    with allure.step(f"Verify status code is 200 (got {response.status_code})"):
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. Body: {response.text[:200]}"
        )

    body = response.json()

    with allure.step("Validate response against OrderCancelResponse schema"):
        try:
            OrderCancelResponse.model_validate(body)
        except ValidationError as e:
            pytest.fail(
                f"Response does not match OrderCancelResponse schema.\n"
                f"Errors:\n{e}\n"
                f"Raw response:\n{body}",
                pytrace=False,
            )


@pytest.mark.regression
@allure.title("PUT /api/orders/{id}/cancel — cancelled status is persisted")
@allure.description(
    "Cancels an orders and verifies GET /api/orders/{id} returns status 'cancelled'."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_cancel_order_is_persisted(order_service, created_order):
    order_id = created_order["id"]

    with allure.step(f"Cancel orders id={order_id}"):
        response = order_service.cancel_order(order_id)
        assert response.status_code == 200, (
            f"Cancel failed: {response.status_code}. Body: {response.text[:200]}"
        )

    with allure.step(f"Send GET /api/orders/{order_id} and verify status='cancelled'"):
        get_response = order_service.get_order_by_id(order_id)
        order = get_response.json()

    with allure.step("Verify status is 'cancelled'"):
        assert order["status"] == "cancelled", (
            f"Expected status='cancelled', got '{order['status']}'"
        )


@pytest.mark.regression
@allure.title("PUT /api/orders/{id}/cancel — cancelling twice returns 400")
@allure.description(
    "Cancels an orders, then attempts to cancel it again and expects 400."
)
@allure.severity(allure.severity_level.NORMAL)
def test_cancel_order_twice_400(order_service, created_order):
    order_id = created_order["id"]

    with allure.step(f"First cancel of orders id={order_id} — expect 200"):
        first = order_service.cancel_order(order_id)
        assert first.status_code == 200, (
            f"First cancel failed: {first.status_code}. Body: {first.text[:200]}"
        )

    with allure.step(f"Second cancel of orders id={order_id} — expect 400"):
        second = order_service.cancel_order(order_id, allow_error=True)

    with allure.step(f"Verify second cancel returns 400 (got {second.status_code})"):
        assert second.status_code == 400, (
            f"Expected 400, got {second.status_code}. Body: {second.text[:200]}"
        )


@pytest.mark.regression
@allure.title("PUT /api/orders/{id}/cancel — non-existent orders returns 404 Not Found")
@allure.description(
    "Attempts to cancel a non-existent orders and expects 404."
)
@allure.severity(allure.severity_level.MINOR)
def test_cancel_nonexistent_order_404(order_service):
    nonexistent_id = 999999

    with allure.step(f"Send PUT /api/orders/{nonexistent_id}/cancel"):
        response = order_service.cancel_order(nonexistent_id, allow_error=True)

    with allure.step(f"Verify status code is 404 (got {response.status_code})"):
        assert response.status_code == 404, (
            f"Expected 404, got {response.status_code}. Body: {response.text[:200]}"
        )


@pytest.mark.regression
@allure.title("PUT /api/orders/{id}/cancel — unauthorized request returns 401 Unauthorized")
@allure.description(
    "Attempts to cancel an orders without a token and expects 401."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_cancel_order_unauthorized(unauth_order_service, created_order):
    order_id = created_order["id"]

    with allure.step(f"Send PUT /api/orders/{order_id}/cancel without authorization"):
        response = unauth_order_service.cancel_order(order_id, allow_error=True)

    with allure.step(f"Verify status code is 401 (got {response.status_code})"):
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}. Body: {response.text[:200]}"
        )


@pytest.mark.regression
@allure.title("PUT /api/orders/{id}/cancel — unauthorized request does not cancel the orders")
@allure.description(
    "Attempts an unauthorized cancel and verifies the orders status is still 'pending'."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_cancel_order_unauthorized_does_not_cancel(
        order_service, unauth_order_service, created_order
):
    order_id = created_order["id"]

    with allure.step(f"Attempt unauthorized cancel of orders id={order_id}"):
        response = unauth_order_service.cancel_order(order_id, allow_error=True)
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}. Body: {response.text[:200]}"
        )

    with allure.step("Send GET /api/orders/{id} and verify status is still 'pending'"):
        order = order_service.get_order_by_id(order_id).json()
        allure.attach(
            str(order),
            name="Order after unauthorized cancel",
            attachment_type=allure.attachment_type.TEXT,
        )

    with allure.step("Verify status is 'pending'"):
        assert order["status"] == "pending", (
            f"Order was cancelled by unauthorized request! "
            f"Status: {order['status']}"
        )
