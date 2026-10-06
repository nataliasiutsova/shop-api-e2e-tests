
from client.api_client import RequestClient

class CategoryService:
    def __init__(self, client: RequestClient):
        self.client = client

    def create_category(self, payload):
        return self.client.post("/categories", json=payload)

    def get_all_categories(self):
        return self.client.get("/categories")

    def get_category_by_id(self, category_id):
        return self.client.get(f"/categories/{category_id}")

    def update_category_by_id(self, payload, category_id):
        return self.client.put(f"/categories/{category_id}", json=payload)

    def delete_category_by_id(self, category_id):
        return self.client.delete(f"/categories/{category_id}")