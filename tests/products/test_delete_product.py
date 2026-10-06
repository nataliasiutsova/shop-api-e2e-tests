import allure
import pytest

pytestmark = [
    allure.feature("Products"),
    allure.story("Delete product"),
]


@pytest.mark.regression
@allure.title("DELETE /products/{id} — deletes an existing product and returns 200/204")
@allure.description("Verifies that DELETE /products/{id} successfully removes an existing product ")
@allure.severity(allure.severity_level.CRITICAL)
def test_delete_product_success(product_service, created_product):
    product_id = created_product["id"]
    with allure.step(f"Delete product id={product_id}"):
        response = product_service.delete_product_by_id(product_id)

    with allure.step("Verify status code is 200 or 204"):
        assert response.status_code in (200, 204), f"Delete failed: {response.status_code} — {response.text[:200]}"


@pytest.mark.regression
@allure.title("DELETE /products/{id} — deleted product is no longer retrievable (404)")
@allure.description(
    "Deletes a product and then attempts to fetch it via GET /products/{id}, "
    "verifying that the API returns 404 Not Found."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_deleted_product_not_retrievable(product_service, created_product):
    product_id = created_product["id"]

    # Remove
    with allure.step(f"Delete product id={product_id}"):
        delete_response = product_service.delete_product_by_id(product_id)

    assert delete_response.status_code in (200, 204), f"Delete failed: {delete_response.status_code}"

    # Try to get
    with allure.step(f"Try to GET deleted product id={product_id}"):
        get_response = product_service.get_product_by_id(product_id, allow_error=True)

    with allure.step("Verify status code is 404"):
        assert get_response.status_code == 404, f"Deleted product id={product_id} still retrievable! "


@pytest.mark.regression
@allure.title("DELETE /products/{id} — deleted product is not present in the list")
@allure.description(
    "Verifies that after a DELETE request, the product is no longer returned "
    "by GET /products."
)
@allure.severity(allure.severity_level.NORMAL)
def test_deleted_product_not_in_list(product_service, created_product):
    product_id = created_product["id"]

    # Check created_product before removing
    with allure.step(f"Verify product id={product_id} is in the list before delete"):
        before = product_service.get_all_products().json()["data"]
        before_ids = [p["id"] for p in before]

        assert product_id in before_ids, f"Product id={product_id} not in list before delete. "

    # Remove
    with allure.step(f"Delete product id={product_id}"):
        response = product_service.delete_product_by_id(product_id)

        assert response.status_code in (200, 204), f"Delete failed: {response.status_code}"

    # Check that product are not in the products list
    with allure.step(f"Verify product id={product_id} is not in the list after delete"):
        after = product_service.get_all_products().json()["data"]
        after_ids = [p["id"] for p in after]
        allure.attach(
            str(after_ids),
            name="Product IDs after delete",
            attachment_type=allure.attachment_type.TEXT,
        )

    assert product_id not in after_ids, (
        f"Deleted product id={product_id} still in list!\n"
        f"List after: {after_ids}"
    )


@pytest.mark.regression
@allure.title("DELETE /products/{id} — deleting the same product twice returns 404")
@allure.description(
    "Deletes a product successfully, then attempts to delete it again "
    "and verifies that the second call returns 404 Not Found."
)
@allure.severity(allure.severity_level.NORMAL)
def test_delete_product_twice_returns_404(product_service, created_product):
    product_id = created_product["id"]

    # Remove1-success
    with allure.step(f"First delete of product id={product_id} — expect 200/204"):
        first = product_service.delete_product_by_id(product_id)

    assert first.status_code in (200, 204), (
        f"First delete failed: {first.status_code}"
    )

    # Remove2 — 404
    with allure.step(f"Second delete of product id={product_id} — expect 404"):
        second = product_service.delete_product_by_id(product_id, allow_error=True)

    assert second.status_code == 404, (
        f"Second delete expected 404, got {second.status_code}.\n"
        f"Body: {second.text[:200]}"
    )


@pytest.mark.regression
@allure.title("DELETE /products/{id} — non-existent product returns 404 Not Found")
@allure.description(
    "Sends a DELETE request to id=999, which does not exist in the system, "
    "and verifies that the API returns 404 Not Found."
)
@allure.severity(allure.severity_level.NORMAL)
def test_delete_nonexistent_product_returns_404(product_service):
    nonexistent_id = 999
    with allure.step(f"DELETE product with non-existent id={nonexistent_id}"):
        response = product_service.delete_product_by_id(nonexistent_id, allow_error=True)

    with allure.step("Verify status code is 404"):
        assert response.status_code == 404, f"Expected 404 for id={nonexistent_id}, got {response.status_code}."


@pytest.mark.regression
@allure.title("DELETE /products/{id} — unauthorized request returns 401 Unauthorized")
@allure.description("Attempts to delete a product without an authorization token and verifies ")
@allure.severity(allure.severity_level.CRITICAL)
def test_delete_product_unauthorized(unauth_product_service, created_product):
    product_id = created_product["id"]

    with allure.step(f"Attempt to DELETE product id={product_id} without authorization"):
        response = unauth_product_service.delete_product_by_id(product_id, allow_error=True)

    with allure.step("Verify status code is 401"):
        assert response.status_code == 401, f"Expected 401, got {response.status_code}."
