import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.models.items import ItemCreate, ItemResponse


class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_create_item(self):
        item = ItemCreate(name="Test Item", description="This is a test item")
        response = self.client.post("/items/", json=item.model_dump())
        self.assertEqual(response.status_code, 200)
        data = ItemResponse.model_validate(response.json())
        self.assertEqual(data.name, item.name)
        self.assertEqual(data.description, item.description)
        self.assertIsNotNone(data.id)

    def test_read_items(self):
        response = self.client.get("/items/")
        self.assertEqual(response.status_code, 200)
        items = [ItemResponse.model_validate(item) for item in response.json()]
        self.assertIsInstance(items, list)

    def test_read_item(self):
        # First, create an item to read
        item = ItemCreate(name="Test Item", description="This is a test item")
        create_response = self.client.post("/items/", json=item.model_dump())
        created_item = ItemResponse(**create_response.json())

        # Now, read the item
        response = self.client.get(f"/items/{created_item.id}")
        self.assertEqual(response.status_code, 200)
        data = ItemResponse(**response.json())
        self.assertEqual(data.name, item.name)
        self.assertEqual(data.description, item.description)
        self.assertEqual(data.id, created_item.id)

    def test_read_item_not_found(self):
        response = self.client.get("/items/non_existent_id")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Item not found"})


if __name__ == "__main__":
    unittest.main()
