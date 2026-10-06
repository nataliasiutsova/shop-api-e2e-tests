from client.api_client import RequestClient


class OrderService:
    def __init__(self, client: RequestClient):
        self.client = client

    def get_all_orders(self, *, allow_error=False):
        return self.client.get("/orders", allow_error=allow_error)

    def get_order_by_id(self, order_id, *, allow_error=False):
        return self.client.get(f"/orders/{order_id}", allow_error=allow_error)

    def create_order(self, *, allow_error=False):
        return self.client.post("/orders", allow_error=allow_error)

    def cancel_order(self, order_id, *, allow_error=False):
        return self.client.put(f"/orders/{order_id}/cancel", allow_error=allow_error)
