from client.api_client import RequestClient


class ProductService:
    def __init__(self, client: RequestClient):
        self.client = client

    def create_product(self, payload, *, allow_error=False):
        return self.client.post("/products", json=payload, allow_error=allow_error)

    def get_all_products(self, params=None, *, allow_error=False):
        return self.client.get("/products", params=params, allow_error=allow_error)

    def get_product_by_id(self, product_id, *, allow_error=False):
        return self.client.get(f"/products/{product_id}", allow_error=allow_error)

    def update_product_by_id(self, product_id, payload, *, allow_error=False):
        return self.client.put(f"/products/{product_id}", json=payload, allow_error=allow_error)

    def delete_product_by_id(self, product_id, *, allow_error=False):
        return self.client.delete(f"/products/{product_id}", allow_error=allow_error)
