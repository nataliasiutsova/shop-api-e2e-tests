import allure
import pytest
from pydantic import ValidationError

from models.product import ProductResponse
from utils.data_generator import make_product_payload

pytestmark = [
    allure.feature("Products"),
    allure.story("Create product"),
]


@pytest.mark.smoke
@allure.title("POST /products — creates product successfully")
@allure.description("Verifies that POST /products creates a product and returns 201 with a valid id. ")
@allure.severity(allure.severity_level.BLOCKER)
def test_create_product_success(product_service, created_category):
    with allure.step(f"Prepare payload for category '{created_category['name']}'"):
        payload = make_product_payload(category=created_category["name"])

    with allure.step("Send POST /products"):
        response = product_service.create_product(payload)

    with allure.step(f"Verify status code is 201 (got {response.status_code})"):
        assert response.status_code == 201, f"Create failed: {response.text[:200]}"

    body = response.json()
    assert "id" in body, f"Response missing 'id'. Body: {body}"

    try:
        assert body["id"] > 0
    finally:
        product_service.delete_product_by_id(body["id"])


@pytest.mark.known_bug
@pytest.mark.regression
@allure.title("POST /products — response matches ProductResponse schema")
@allure.description("Verifies that the response matches ProductResponse Pydantic model. ")
@allure.severity(allure.severity_level.CRITICAL)
def test_create_product_response_matches_schema(created_product):
    with allure.step("Validate created product against schema"):
        try:
            ProductResponse.model_validate(created_product)
        except ValidationError as e:
            pytest.fail(
                f"Product does not match ProductResponse schema.\n"
                f"Errors:\n{e}\n"
                f"Raw product:\n{created_product}",
                pytrace=False,
            )


@pytest.mark.regression
@allure.title("POST /products — created product is retrievable")
@allure.description(
    "Verifies that the created product is saved in DB and available via GET /products/{id}.")
@allure.severity(allure.severity_level.CRITICAL)
def test_created_product_is_retrievable(product_service, created_product):
    created_id = created_product["id"]
    with allure.step(f"Send GET /products/{created_id}"):
        response = product_service.get_product_by_id(created_id)

    with allure.step(f"Verify status code is 200 (got {response.status_code})"):
        assert response.status_code == 200, f"Created product id={created_id} not retrievable. "

    product = response.json()
    with allure.step(f"Verify id equals '{created_product['id']}'"):
        assert product["id"] == created_product[
            "id"], f"id mismatch: expected {created_product['id']}, got {product["id"]}"

    with allure.step(f"Verify name equals '{created_product['name']}'"):
        assert product["name"] == created_product[
            "name"], f"name mismatch: expected '{created_product['name']}', got '{product["name"]}"

    with allure.step(f"Verify price equals '{created_product['price']}'"):
        assert product["price"] == created_product[
            "price"], f"price mismatch: expected {created_product['price']}, got {product["price"]}"


@pytest.mark.regression
@allure.title("POST /products — created product appears in list")
@allure.description("Verifies that the created product appears in GET /products response.")
@allure.severity(allure.severity_level.CRITICAL)
def test_created_product_appears_in_list(product_service, created_product):
    created_id = created_product["id"]
    with allure.step("Send GET /products"):
        response = product_service.get_all_products()

    with allure.step(f"Verify status code is 200 (got {response.status_code})"):
        assert response.status_code == 200, f"Got {response.status_code}"

    with allure.step("Extract product ids from response"):
        result_ids = [p["id"] for p in response.json()["data"]]
        allure.attach(
            str(result_ids),
            name="Returned ids",
            attachment_type=allure.attachment_type.TEXT,
        )
    with allure.step(f"Verify created id={created_id} is in the list"):
        assert created_id in result_ids, f"Created product id={created_id} not in list."


@pytest.mark.regression
@allure.title("POST /products — rejects invalid payload")
@allure.description(
    "Verifies that POST /products rejects invalid payloads with 422. "
    "Cases: negative price, zero price, empty name, non-numeric price, "
    "missing fields, negative stock, non-int stock."
)
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("invalid_payload, case", [
    ({"name": "Phone", "price": -10}, "negative price"),
    ({"name": "Phone", "price": 0}, "zero price"),
    ({"name": "", "price": 100}, "empty name"),
    ({"name": "Phone", "price": "abc"}, "non-numeric price"),
    ({"name": "Phone"}, "missing price"),
    ({"price": 100}, "missing name"),
    ({}, "empty payload"),
    ({"name": "Phone", "price": 100, "stock": -5}, "negative stock"),
    ({"name": "Phone", "price": 100, "stock": "many"}, "non-int stock"),
])
def test_create_product_validation_errors(product_service, created_category, invalid_payload, case):
    allure.dynamic.title(f"POST /products — rejects {case}")
    with allure.step(f"Prepare invalid payload ({case})"):
        payload = {**invalid_payload, "category": created_category["name"]}

    with allure.step("Send POST /products"):
        response = product_service.create_product(payload, allow_error=True)

    with allure.step(f"Verify status code is 422 (got {response.status_code})"):
        assert response.status_code == 422, f"[{case}] Expected 422, got {response.status_code}. "


@pytest.mark.known_bug
@pytest.mark.regression
@allure.title("POST /products — rejects non-existent category")
@allure.description("Verifies that POST /products rejects a non-existent category with 4xx.")
@allure.severity(allure.severity_level.CRITICAL)
def test_create_product_rejects_nonexistent_category(product_service):
    fake_category = "ThisCategoryDoesNotExist12345"
    with allure.step(f"Prepare payload with fake category='{fake_category}'"):
        payload = make_product_payload(category=fake_category)

    with allure.step("Send POST /products"):
        response = product_service.create_product(payload, allow_error=True)

    with allure.step(f"Verify status code is 4xx (got {response.status_code})"):
        assert response.status_code in (
            400, 404, 422), f"Expected 4xx for non-existent category, got {response.status_code}. "


@pytest.mark.regression
@allure.title("POST /products — rejects missing required field")
@allure.description(
    "Verifies that POST /products rejects payloads without required fields "
    "(name, price, category) with 4**."
)
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("missing_field", [
    "name",
    "price",
    "category",
])
def test_create_product_rejects_missing_required_field(product_service, created_category, missing_field):
    allure.dynamic.title(f"POST /products — rejects missing '{missing_field}'")
    with allure.step(f"Prepare payload without '{missing_field}'"):
        payload = make_product_payload(category=created_category["name"])
        payload.pop(missing_field)

    with allure.step("Send POST /products"):
        response = product_service.create_product(payload, allow_error=True)

    with allure.step(f"Verify status code is 422 (got {response.status_code})"):
        assert response.status_code == 422, f"Expected 422 for non-existent category, got {response.status_code}. "


@pytest.mark.regression
@allure.title("POST /products — requires authentication (401)")
@allure.description("Verifies that POST /products returns 401 without authentication token. ")
@allure.severity(allure.severity_level.CRITICAL)
def test_create_product_unauthorized(unauth_product_service, created_category):
    payload = make_product_payload(category=created_category["name"])
    with allure.step("Send POST /products WITHOUT auth token"):
        response = unauth_product_service.create_product(payload, allow_error=True)

    with allure.step(f"Verify status code is 401 (got {response.status_code})"):
        assert response.status_code == 401, f"Expected 401, got {response.status_code}. "
