from faker import Faker
from models.product import ProductCreate

fake = Faker()


def make_product_payload(**overrides) -> dict:

    defaults = {
        "name": f"Product-{fake.unique.word()}",
        "description": fake.sentence(nb_words=6),
        "category": "Electronics",
        "price": round(fake.random.uniform(1, 1000), 2),
        "stock": fake.random_int(min=1, max=100),
        "image_url": "https://via.placeholder.com/300",
    }

    payload = ProductCreate(**{**defaults, **overrides})
    return payload.model_dump(mode="json")