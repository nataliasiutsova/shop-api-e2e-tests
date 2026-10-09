import allure
import pytest
from pydantic import ValidationError

from models.product import ProductResponse

pytestmark = [
    allure.feature("Products"),
    allure.story("Get product by id"),
]


@pytest.mark.smoke
@allure.title("GET /products/{id} — returns 200 OK")
@allure.description("Verifies that GET /products/{id} is available and returns 200 for an existing product.")
@allure.severity(allure.severity_level.BLOCKER)
def test_get_product_returns_200(product_service, created_product):
    product_id = created_product["id"]

    with allure.step(f"Send GET /products/{product_id}"):
        response = product_service.get_product_by_id(product_id)
    with allure.step(f"Verify status code is 200 (got {response.status_code})"):
        assert response.status_code == 200, f"Expected 200 for product id={product_id}, got {response.status_code}."


@pytest.mark.smoke
@allure.title("GET /products/{id} — returns object (dict)")
@allure.description("Verifies that GET /products/{id} returns a JSON object (dict), not a list. ")
@allure.severity(allure.severity_level.CRITICAL)
def test_get_product_by_id_returns_object(product_service, created_product):
    product_id = created_product["id"]

    with allure.step(f"Send GET /products/{product_id}"):
        response = product_service.get_product_by_id(product_id)

    product_data = response.json()
    with allure.step(f"Verify response is dict (got {type(product_data).__name__})"):
        assert isinstance(product_data,
                          dict), f"Expected dict for product id={product_id}, got {type(product_data).__name__}. "


@pytest.mark.known_bug
@pytest.mark.regression
@allure.title("GET /products/{id} — response matches ProductResponse schema")
@allure.description("Verifies that the response matches ProductResponse Pydantic model. ")
@allure.severity(allure.severity_level.CRITICAL)
def test_get_product_by_id_response_matches_schema(product_service, created_product):
    product_id = created_product["id"]

    with allure.step(f"Send GET /products/{product_id}"):
        response = product_service.get_product_by_id(product_id)

    with allure.step(f"Verify status code is 200 (got {response.status_code})"):
        assert response.status_code == 200, (
            f"Expected 200 for id={product_id}, got {response.status_code}.\n"
            f"Body: {response.text[:200]}"
        )
    with allure.step("Validate response against ProductResponse model"):
        try:
            ProductResponse.model_validate(response.json())
        except ValidationError as e:
            pytest.fail(
                f"Response for id={product_id} does not match ProductResponse schema.\n"
                f"Errors:\n{e}\n"
                f"Raw response:\n{response.json()}",
                pytrace=False,
            )


@pytest.mark.regression
@allure.title("GET /products/{id} — returns correct persisted data")
@allure.description("Verifies that GET /products/{id} returns exactly the same data that was created.")
@allure.severity(allure.severity_level.CRITICAL)
def test_get_product_by_id_returns_correct_data(product_service, created_product):
    product_id = created_product["id"]

    with allure.step(f"Send GET /products/{product_id}"):
        response = product_service.get_product_by_id(product_id)
    with allure.step("Parse response"):
        product = response.json()
        allure.attach(
            str(product),
            name="Fetched product",
            attachment_type=allure.attachment_type.JSON,
        )
        allure.attach(
            str(created_product),
            name="Created product",
            attachment_type=allure.attachment_type.JSON,
        )
    with allure.step(f"Verify id equals '{created_product['id']}'"):
        assert product["id"] == created_product["id"], f"Expected id={created_product['id']}, got id={product["id"]}."

    with allure.step(f"Verify name equals '{created_product['name']}'"):
        assert product["name"] == created_product[
            "name"], f"Expected name='{created_product['name']}, got name={product["name"]}."

    with allure.step(f"Verify description equals '{created_product['description']}'"):
        assert product["description"] == created_product[
            "description"], f"Expected description='{created_product['description']}, got name={product["description"]}."

    with allure.step(f"Verify price equals '{created_product['price']}'"):
        assert product["price"] == created_product[
            "price"], f"Expected price={created_product['price']}, got price={product["price"]}. "

    with allure.step(f"Verify category equals '{created_product['category']}'"):
        assert product["category"] == created_product[
            "category"], f"Expected price={created_product['category']}, got category={product["category"]}. "

    with allure.step(f"Verify stock equals '{created_product['stock']}'"):
        assert product["stock"] == created_product[
            "stock"], f"Expected stock={created_product['stock']}, got stock={product["stock"]}. "


@pytest.mark.known_bug
@pytest.mark.regression
@allure.title("GET /products/{id} — new product defaults rating=0, reviews=0")
@allure.description("Verifies that a newly created product has default values: rating=0 and reviews_count=0.")
@allure.severity(allure.severity_level.CRITICAL)
def test_get_new_product_default_rating_zero(product_service, created_product):
    product_id = created_product["id"]
    with allure.step(f"Send GET /products/{product_id}"):
        response = product_service.get_product_by_id(product_id)
        product = response.json()

    with allure.step("Verify API returns 'rating' field"):
        assert "rating" in product, (
            f"API does not return 'rating'. "
            f"Actual keys: {list(product.keys())}. Known bug BACKEND."
        )

    with allure.step(f"Verify rating is 0 (got {product['rating']})"):
        assert product["rating"] == 0

    with allure.step("Verify API returns 'reviews_count' field"):
        assert "reviews_count" in product, (
            f"API does not return 'reviews_count'. "
            f"Actual keys: {list(product.keys())}. Known bug BACKEND."
        )

    with allure.step(f"Verify reviews_count is 0 (got {product['reviews_count']})"):
        assert product["reviews_count"] == 0


@pytest.mark.regression
@allure.title("GET /products/{id} — returns 404 for non-existent product")
@allure.description("Verifies that GET /products/{id} returns 404 for a non-existent product ID. ")
@allure.severity(allure.severity_level.CRITICAL)
def test_get_nonexistent_product_returns_404(product_service):
    nonexistent_id = 9999
    with allure.step(f"Send GET /products/{nonexistent_id} (allow_error=True)"):
        response = product_service.get_product_by_id(nonexistent_id, allow_error=True)

    with allure.step(f"Verify status code is 404 (got {response.status_code})"):
        assert response.status_code == 404, f"Expected 404 for id={nonexistent_id}, got {response.status_code}. "


@pytest.mark.regression
@allure.title("GET /products/{id} — rejects invalid ID format")
@allure.description(
    "Verifies that GET /products/{id} rejects invalid ID formats (non-numeric, float, negative, empty, null) with 4xx."
)
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("invalid_id", [
    "abc",
    "1.5",
    "-1",
    "",
    "null",
])
def test_get_product_with_invalid_id_format(product_service, invalid_id):
    allure.dynamic.title(f"GET /products/{invalid_id!r} — rejects invalid ID")
    with allure.step(f"Send GET /products/{invalid_id!r}"):
        response = product_service.get_product_by_id(invalid_id, allow_error=True)
    with allure.step(f"Verify status code is 4xx (got {response.status_code})"):
        assert response.status_code in (
            400, 404, 422), f"Expected 4xx for id='{invalid_id}', got {response.status_code}. "
