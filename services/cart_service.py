from client.api_client import RequestClient


class CartService:
    def __init__(self, client: RequestClient):
        self.client = client

    def get_cart(self, allow_error=False):
        return self.client.get("/cart", allow_error=allow_error)

    def add_item(self, payload, *, allow_error=False):
        return self.client.post("/cart/items", json=payload, allow_error=allow_error)

    def update_item(self, item_id, payload, *, allow_error=False):
        return self.client.put(f"/cart/items/{item_id}", json=payload, allow_error=allow_error)

    def delete_item(self, item_id, *, allow_error=False):
        return self.client.delete(f"/cart/items/{item_id}", allow_error=allow_error)

    def clear_cart(self, allow_error=False):
        return self.client.delete("/cart", allow_error=allow_error)
