import allure
import pytest
from pydantic import ValidationError

from models.product import ProductResponse

pytestmark = [
    allure.feature("Products"),
    allure.story("Get all products"),
]


@pytest.mark.smoke
@allure.title("GET /products — returns 200 OK")
@allure.description("Verifies that GET /products endpoint is available and returns 200. ")
@allure.severity(allure.severity_level.BLOCKER)
def test_get_products_returns_200(product_service):
    with allure.step("Send GET /products"):
        response = product_service.get_all_products()

    with allure.step(f"Verify status code is 200 (got {response.status_code})"):
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. "


@pytest.mark.smoke
@allure.title("GET /products — 'data' field is a list")
@allure.description("Verifies that the response contains a 'data' field and it is a list. ")
@allure.severity(allure.severity_level.BLOCKER)
def test_get_products_returns_list(product_service):
    with allure.step("Send GET /products"):
        response = product_service.get_all_products()

    products_list = response.json()["data"]
    with allure.step(f"Verify 'data' is a list (got {type(products_list).__name__})"):
        assert isinstance(products_list, list), f"Expected 'data' to be list, got {type(products_list).__name__}. "


@pytest.mark.regression
@allure.title("GET /products — returns non-empty list")
@allure.description("Verifies that the product list is not empty when seeded data exists. ")
@allure.severity(allure.severity_level.CRITICAL)
def test_get_products_returns_non_empty_list(product_service, seeded_products):
    with allure.step("Send GET /products"):
        response = product_service.get_all_products()
    with allure.step("Parse products from response"):
        products = response.json()["data"]

    with allure.step(f"Verify list is not empty (got {len(products)} products)"):
        assert len(products) > 0, f"Expected non-empty list, got empty. "


@pytest.mark.regression
@pytest.mark.known_bug
@allure.title("GET /products — response matches schema")
@allure.description("Verifies that every product in the list matches the ProductResponse Pydantic model. ")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("known-bug")
def test_get_products_response_matches_schema(product_service, seeded_products):
    with allure.step("Send GET /products"):
        response = product_service.get_all_products()

    with allure.step(f"Verify status code is 200 (got {response.status_code})"):
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. "
            f"Body: {response.text[:200]}"
        )

        products = response.json()["data"]

    with allure.step(f"Validate each of {len(products)} products against ProductResponse"):
        for idx, raw in enumerate(products):
            with allure.step(f"Validate product at index (id={raw.get('id', 'N/A')})"):
                try:
                    ProductResponse.model_validate(raw)
                except ValidationError as e:
                    pytest.fail(
                        f"Product at index (id={raw.get('id', 'N/A')}) "
                        f"Does not match ProductResponse schema.\n"
                        f"Errors:\n{e}\n"
                        f"Raw product:\n{raw}",
                        pytrace=False,
                    )


@pytest.mark.regression
@allure.title("GET /products?category={category} — filter by category")
@allure.description("Verifies that filtering by category returns only products from that category. ")
@allure.severity(allure.severity_level.CRITICAL)
def test_get_products_filter_by_category(product_service, seeded_products):
    category = seeded_products[0]["category"]

    with allure.step(f"Send GET /products with category='{category}'"):
        response = product_service.get_all_products(params={"category": category})
        products = response.json()["data"]

    with (allure.step(f"Verify all products are in category '{category}'")):
        assert not [p for p in products if
                    p[
                        "category"] != category], f"Filter by category='{category}' returned products from other categories."


@pytest.mark.regression
@allure.title("GET /products?search={product_name} — search by full name")
@allure.description("Verifies that searching by full product name returns the target product and only it. ")
@allure.severity(allure.severity_level.CRITICAL)
def test_search_product_by_full_name(product_service, created_product):
    target_name = created_product["name"]
    target_id = created_product["id"]
    with allure.step(f"Get target product: id={target_id}, name='{target_name}'"):
        allure.attach(
            str(created_product),
            name="Target product",
            attachment_type=allure.attachment_type.JSON,
        )
    with allure.step(f"Send GET /products with search='{target_name}'"):
        response = product_service.get_all_products(params={"search": target_name})

    with allure.step(f"Verify status code is 200 (got {response.status_code})"):
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        results = response.json()["data"]
        result_ids = [p["id"] for p in results]

    with allure.step(f"Verify target id={target_id} is in results"):
        assert target_id in result_ids, f"id={target_id} not in {result_ids}"

    with allure.step("Verify no non-matching products"):
        wrong = [p["name"] for p in results if target_name.lower() not in p["name"].lower()]
        if wrong:
            allure.attach(
                str(wrong),
                name="Non-matching products",
                attachment_type=allure.attachment_type.TEXT,
            )
        assert not wrong, f"Non-matching products: {wrong}"


@pytest.mark.regression
@allure.title("GET /products?sort=price_asc — sort ascending")
@allure.description("Verifies that sorting by price (ascending) works correctly. ")
@allure.severity(allure.severity_level.NORMAL)
def test_sort_products_by_price_asc(product_service, seeded_products):
    with allure.step("Send GET /products with sort=price_asc"):
        response = product_service.get_all_products(params={"sort": "price_asc"})

    with allure.step(f"Verify status code is 200 (got {response.status_code})"):
        assert response.status_code == 200, f"Sort failed: {response.text[:200]}"

    with allure.step("Parse prices from response"):
        results = response.json()["data"]
        prices = [p["price"] for p in results]

        allure.attach(
            str(prices),
            name="Prices orders",
            attachment_type=allure.attachment_type.TEXT,
        )

    with allure.step("Verify prices are sorted ascending"):
        assert prices == sorted(prices), f"Not sorted asc: {prices}"


@pytest.mark.regression
@allure.title("GET /products?sort=price_desc — sort descending")
@allure.description("Verifies that sorting by price (descending) works correctly.")
@allure.severity(allure.severity_level.NORMAL)
def test_sort_products_by_price_desc(product_service, seeded_products):
    with allure.step("Send GET /products with sort=price_desc"):
        response = product_service.get_all_products(params={"sort": "price_desc"})

    with allure.step(f"Verify status code is 200 (got {response.status_code})"):
        assert response.status_code == 200, f"Sort failed: {response.text[:200]}"

    with allure.step("Parse prices from response"):
        results = response.json()["data"]
        prices = [p["price"] for p in results]
        allure.attach(
            str(prices),
            name="Prices orders",
            attachment_type=allure.attachment_type.TEXT,
        )
    with allure.step("Verify prices are sorted descending"):
        assert prices == sorted(prices, reverse=True), f"Not sorted desc: {prices}"


@pytest.mark.regression
@allure.title("GET /products?limit=20 — pagination limit")
@allure.description("Verifies that limit=20 returns at most 20 products. ")
@allure.severity(allure.severity_level.NORMAL)
def test_pagination_limit(product_service, seeded_products):
    limit = 20
    with allure.step(f"Send GET /products with limit={limit}, offset=0"):
        response = product_service.get_all_products(params={"limit": limit, "offset": 0})

    with allure.step(f"Verify status code is 200 (got {response.status_code})"):
        assert response.status_code == 200, f"Pagination failed: {response.text[:200]}"

    with allure.step("Parse results"):
        results = response.json()["data"]
        allure.attach(
            str(len(results)),
            name="Returned count",
            attachment_type=allure.attachment_type.TEXT,
        )
    with allure.step(f"Verify count ≤ {limit} (got {len(results)})"):
        assert len(results) <= 20, f"Expected ≤ 20, got {len(results)}"
