import time

import allure
import pytest
from faker import Faker
from pydantic import ValidationError

from models.product import ProductResponse

pytestmark = [
    allure.feature("Products"),
    allure.story("Update product"),
]

fake = Faker()


@pytest.mark.regression
@allure.title("PUT /products/{id} — updates a single field and returns 200 OK")
@allure.description("Verifies that PUT /products/{id} correctly updates each individual field ")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("field, new_value", [
    ("name", f"Product-{fake.unique.word()}"),
    ("description", fake.sentence(nb_words=6)),
    ("price", round(fake.random.uniform(1, 1000), 2)),
    ("stock", fake.random_int(min=1, max=100)),
])
def test_update_product_single_field(product_service, created_product, field, new_value):
    allure.dynamic.title(f"PUT /products/{{id}} — updates '{field}' and returns 200 OK")
    created_id = created_product["id"]
    with allure.step(f"Update field '{field}' for product id={created_id}"):
        response = product_service.update_product_by_id(created_id, {field: new_value})

    with allure.step(f"Verify status code 200 for field '{field}'"):
        assert response.status_code == 200, f"Update '{field}' failed: {response.status_code}"
    with allure.step(f"Verify that '{field}' in response equals the new value"):
        updated_body = response.json()
        actual = updated_body.get(field)

    assert actual == new_value, f"Field '{field}': expected {new_value!r}, got {actual!r}"


@pytest.mark.regression
@allure.title("PUT /products/{id} — updates multiple fields and returns 200 OK")
@allure.description("Verifies that PUT /products/{id} correctly updates several fields in a single request ")
@allure.severity(allure.severity_level.NORMAL)
def test_update_product_multiple_fields(product_service, created_product):
    created_id = created_product["id"]
    new_values = {
        "name": f"Product-{fake.unique.word()}",
        "price": round(fake.random.uniform(1, 1000), 2),
        "stock": fake.random_int(min=1, max=100),
    }
    with allure.step(f"Update multiple fields: {list(new_values.keys())}"):
        response = product_service.update_product_by_id(created_id, new_values)

    with allure.step("Verify status code 200"):
        assert response.status_code == 200, f"Body: {response.text[:200]}"
    with allure.step("Validate response and compare all updated fields"):
        updated_body = response.json()

    assert updated_body["name"] == new_values["name"]
    assert updated_body["price"] == new_values["price"]
    assert updated_body["stock"] == new_values["stock"]


@pytest.mark.known_bug
@pytest.mark.regression
@allure.title("PUT /products/{id} — response matches the ProductResponse schema")
@allure.description("Verifies that the response matches ProductResponse Pydantic model. ")
@allure.severity(allure.severity_level.CRITICAL)
def test_update_product_response_matches_schema(product_service, created_product):
    product_id = created_product["id"]
    new_price = round(fake.random.uniform(1, 1000), 2)

    with allure.step(f"Update price for product id={product_id} to {new_price}"):
        response = product_service.update_product_by_id(product_id, {"price": new_price})
    with allure.step("Verify status code 200"):
        assert response.status_code == 200, f"Expected 200 for PUT /products/{product_id} "
    with allure.step("Validate response against the ProductResponse schema"):
        try:
            ProductResponse.model_validate(response.json())
        except ValidationError as e:
            pytest.fail(
                f"PUT /products/{product_id} response does not match "
                f"ProductResponse schema.\n"
                f"Errors:\n{e}\n"
                f"Raw response:\n{response.json()}",
                pytrace=False,
            )


@pytest.mark.regression
@allure.title("PUT /products/{id} — changes are persisted and visible via GET")
@allure.description("Updates price via PUT, then fetches the product via GET and verifies ")
@allure.severity(allure.severity_level.CRITICAL)
def test_update_product_is_persisted(product_service, created_product):
    created_id = created_product["id"]
    new_price = round(fake.random.uniform(1, 1000), 2)
    with allure.step(f"Update price to {new_price}"):
        product_service.update_product_by_id(created_id, {"price": new_price})
    with allure.step("Fetch the product again (GET)"):
        response = product_service.get_product_by_id(created_id)

    product_body = response.json()

    with allure.step(f"Verify that price is persisted and equals {new_price}"):
        assert product_body[
                   "price"] == new_price, f"Update not persisted. Expected {new_price}, got {product_body["price"]}"


@pytest.mark.regression
@allure.title("PUT /products/{id} — updated_at is increased after update")
@allure.description("Verifies that after a PUT request the updated_at field increases compared to the previous value")
@allure.severity(allure.severity_level.NORMAL)
def test_update_product_changes_updated_at(product_service, created_product):
    product_id = created_product["id"]

    with allure.step("First update — to initialize updated_at"):
        first_response = product_service.update_product_by_id(product_id,
                                                              {"price": round(fake.random.uniform(1, 1000), 2)})
        first_update = first_response.json()

    with allure.step("Wait 1 second to guarantee different timestamps"):
        time.sleep(1)  # for timestamps diff
    with allure.step("Second update — updated_at should change"):
        second_response = product_service.update_product_by_id(product_id,
                                                               {"price": round(fake.random.uniform(1, 1000), 2)})
        second_update = second_response.json()

    with allure.step("Verify that updated_at increased"):
        assert second_update["updated_at"] > first_update["updated_at"], f"updated_at not changed"


@pytest.mark.regression
@allure.title("PUT /products/{id} — created_at remains unchanged after update")
@allure.description("Verifies that a PUT request does not affect the created_at field")
@allure.severity(allure.severity_level.NORMAL)
def test_update_product_does_not_change_created_at(product_service, created_product):
    before_update = created_product

    with allure.step("Update price to 999.99"):
        response = product_service.update_product_by_id(before_update["id"],
                                                        {"price": round(fake.random.uniform(1, 1000), 2)})
    after_update = response.json()

    with allure.step("Verify that created_at did not change"):
        assert after_update["created_at"] == before_update["created_at"], f"created_at changed!"


@pytest.mark.regression
@allure.title("PUT /products/{id} — invalid field value returns 422 Unprocessable Entity")
@allure.description(
    "Parameterized test: sends invalid values for name, price, stock, "
    "and verifies that the API returns 422 Unprocessable Entity."
)
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("field, invalid_value, case", [
    ("name", "", "empty name"),
    ("price", -10, "negative price"),
    ("price", 0, "zero price"),
    ("price", "abc", "non-numeric price"),
    ("stock", -5, "negative stock"),
    ("stock", "many", "non-int stock")
])
def test_update_product_rejects_invalid_value(product_service, created_product, field, invalid_value, case, ):
    allure.dynamic.title(f"PUT /products/{{id}} — rejects {field} ({case}) with 422")
    product_id = created_product["id"]

    with allure.step(f"Case: {case}. Sending {field}={invalid_value!r}"):
        response = product_service.update_product_by_id(product_id, {field: invalid_value}, allow_error=True)

        with allure.step(f"Expect 422 for {field}={invalid_value!r}"):
            assert (response.status_code == 422), f"[{case}] Expected 422 for {field}={invalid_value!r}, "


@pytest.mark.regression
@allure.title("PUT /products/{id} — non-existent product returns 404 Not Found")
@allure.description("Verifies that PUT /products/{id} returns 404 for a non-existent product ID. ")
@allure.severity(allure.severity_level.NORMAL)
def test_update_nonexistent_product_returns_404(product_service):
    with allure.step("Update a product with non-existent id=999"):
        response = product_service.update_product_by_id(999, {"price": round(fake.random.uniform(1, 1000), 2)},
                                                        allow_error=True)

    with allure.step("Expect status code 404"):
        assert response.status_code == 404, f"Expected 404 for non-existent id, got {response.status_code}"


@pytest.mark.regression
@allure.title("PUT /products/{id} — unauthorized request returns 401 Unauthorized")
@allure.description("Verifies that PUT /products/{id} returns 401 without authentication token. ")
@allure.severity(allure.severity_level.CRITICAL)
def test_update_product_unauthorized(unauth_product_service, created_product):
    product_id = created_product["id"]

    with allure.step(f"Attempt to update product id={product_id} without authorization"):
        response = unauth_product_service.update_product_by_id(product_id,
                                                               {"price": round(fake.random.uniform(1, 1000), 2)},
                                                               allow_error=True)

    with allure.step("Expect status code 401"):
        assert response.status_code == 401, f"Expected 401, got {response.status_code}. "
