import base64
import unittest
import uuid

from fastapi.testclient import TestClient
import requests

from app.main import app
<<<<<<< HEAD
from app.models.items import ItemCreate, ItemResponse
=======
>>>>>>> origin/main


class TestAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Setup credentials and headers
        cls.username = "test-user-10"
        cls.password = "password1"
        encoded_credentials = cls.credentials(cls.username, cls.password)

        cls.headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "*",
        }

        # Fetch and save the JSON data in setUpClass
        with requests.get(
            "https://raw.githubusercontent.com/ai-cfia/fertiscan-pipeline/main/expected.json"
        ) as response:
            cls.analysis_json = response.json()
    
    @classmethod
    def credentials(cls, username, password) -> str:
        credentials = f"{username}:{password}"
        return base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
    
    def setUp(self):
        app.testing = True
        self.client = TestClient(app)
        self.client.headers.update(self.headers)
        self.client.post(
            "/signup",
            headers={
                **self.headers,
                "Authorization": f'Basic {self.credentials(self.username, self.password)}',
            },
        )
        
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

        # Test if the subtype was rolled back (i.e., not found)
        with TestClient(app) as client:
            response = client.get(f"/{self.subtype_id}")
            # Expect a 404 status code, indicating that the subtype was not found
            self.assertEqual(response.status_code, 404)
