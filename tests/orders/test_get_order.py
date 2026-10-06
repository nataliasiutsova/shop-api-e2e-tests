import allure
import pytest
from pydantic import ValidationError

from models.order import OrderResponse

pytestmark = [
    allure.feature("Order"),
    allure.story("Get orders by id"),
]


@pytest.mark.regression
@allure.title("GET /api/orders/{id} — returns 200 OK for an existing orders")
@allure.description("Fetches an existing orders by id and verifies the response ")
@allure.severity(allure.severity_level.CRITICAL)
def test_get_order_by_id_success(order_service, created_order):
    order_id = created_order["id"]

    with allure.step(f"Send GET /api/orders/{order_id}"):
        response = order_service.get_order_by_id(order_id)

    with allure.step(f"Verify status code is 200 (got {response.status_code})"):
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. Body: {response.text[:200]}"
        )

    with allure.step(f"Verify orders id={order_id}"):
        body = response.json()
        assert body["id"] == order_id, (
            f"Expected id={order_id}, got {body['id']}"
        )


@pytest.mark.regression
@allure.title("GET /api/orders/{id} — response matches the OrderResponse schema")
@allure.description(
    "Validates the GET /api/orders/{id} response body against the OrderResponse model."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_get_order_by_id_response_matches_schema(order_service, created_order):
    order_id = created_order["id"]

    with allure.step(f"Send GET /api/orders/{order_id}"):
        response = order_service.get_order_by_id(order_id)

    with allure.step(f"Verify status code is 200 (got {response.status_code})"):
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. Body: {response.text[:200]}"
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
@allure.title("GET /api/orders/{id} — response matches the created orders")
@allure.description(
    "Verifies that the fetched orders has the same items and total as the created one."
)
@allure.severity(allure.severity_level.NORMAL)
def test_get_order_by_id_matches_created(order_service, created_order):
    order_id = created_order["id"]

    with allure.step(f"Send GET /api/orders/{order_id}"):
        response = order_service.get_order_by_id(order_id)
        fetched = response.json()

        fetched_total = round(fetched["total"], 2)
        created_total = round(created_order["total"], 2)

    with allure.step(f"Verify total: fetched {fetched_total} == created {created_total}"):
        assert fetched_total == created_total, f"total mismatch: fetched={fetched_total}, created={created_total}"

        fetched_status = fetched["status"]
        created_status = created_order["status"]

    with allure.step(f"Verify status: fetched '{fetched_status}' == created '{created_status}'"):
        assert fetched_status == created_status, f"status mismatch: fetched='{fetched_status}', created='{created_status}'"

        fetched_items_count = len(fetched["items"])
        created_items_count = len(created_order["items"])

    with allure.step(f"Verify items count: fetched {fetched_items_count} == created {created_items_count}"):
        assert fetched_items_count == created_items_count, (
            f"items count mismatch: fetched={fetched_items_count}, "
            f"created={created_items_count}"
        )


@pytest.mark.regression
@allure.title("GET /api/orders/{id} — non-existent orders returns 404 Not Found")
@allure.description(
    "Attempts to fetch an orders by a non-existent id and expects 404."
)
@allure.severity(allure.severity_level.MINOR)
def test_get_order_by_id_nonexistent_404(order_service):
    nonexistent_id = 999999

    with allure.step(f"Send GET /api/orders/{nonexistent_id}"):
        response = order_service.get_order_by_id(nonexistent_id, allow_error=True)

    with allure.step(f"Verify status code is 404 (got {response.status_code})"):
        assert response.status_code == 404, (
            f"Expected 404, got {response.status_code}. Body: {response.text[:200]}"
        )


@pytest.mark.regression
@allure.title("GET /api/orders/{id} — unauthorized request returns 401 Unauthorized")
@allure.description(
    "Attempts to fetch an orders without a token and expects 401."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_get_order_by_id_unauthorized(unauth_order_service, created_order):
    order_id = created_order["id"]

    with allure.step(f"Send GET /api/orders/{order_id} without authorization"):
        response = unauth_order_service.get_order_by_id(order_id, allow_error=True)

    with allure.step(f"Verify status code is 401 (got {response.status_code})"):
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}. Body: {response.text[:200]}"
        )
