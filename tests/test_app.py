import base64
import os
import unittest
import uuid

from fastapi.testclient import TestClient
import requests

from app.main import app
from app.models.items import ItemCreate, ItemResponse


class TestAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Setup credentials and headers
        cls.username = "test-user-1"
        cls.password = "password1"
        encoded_credentials = cls.credentials(cls.username, cls.password)

        cls.headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "*",
        }

        os.environ["TESTING"] = "True"

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
        
    def test_health_check(self):
        with TestClient(app) as client:
            response = client.get("/health")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"status": "ok"})

    def test_create_item(self):
        with TestClient(app) as client:
            item = ItemCreate(name="Test Item", description="This is a test item")
            response = client.post("/items/", json=item.model_dump())
            self.assertEqual(response.status_code, 200)
            data = ItemResponse.model_validate(response.json())
            self.assertEqual(data.name, item.name)
            self.assertEqual(data.description, item.description)
            self.assertIsNotNone(data.id)

    def test_read_items(self):
        with TestClient(app) as client:
            response = client.get("/items/")
            self.assertEqual(response.status_code, 200)
            items = [ItemResponse.model_validate(item) for item in response.json()]
            self.assertIsInstance(items, list)

    def test_read_item(self):
        with TestClient(app) as client:
            # First, create an item to read
            item = ItemCreate(name="Test Item", description="This is a test item")
            create_response = client.post("/items/", json=item.model_dump())
            created_item = ItemResponse(**create_response.json())

            # Test if the subtype was rolled back (i.e., not found)
            response = client.get(f"/{created_item.id}")
            # Expect a 404 status code, indicating that the subtype was not found
            self.assertEqual(response.status_code, 404)

    def test_user_signup_missing_username(self):
        with TestClient(app) as client:
            response = client.post(
                "/signup",
                headers={
                    **self.headers,
                    "Authorization": f'Basic {self.credentials("", self.password)}',
                },
            )
            self.assertEqual(response.status_code, 400, response.json())

    def test_user_signup(self):
        with TestClient(app) as client:
            username = str(uuid.uuid4())
            response = client.post(
                "/signup",
                headers={
                    **self.headers,
                    "Authorization": f'Basic {self.credentials(username, self.password)}',
                },
            )
            self.assertEqual(response.status_code, 201, response.json())

    def test_user_login_missing_username(self):
        with TestClient(app) as client:
            response = client.post(
                "/login",
                headers={
                    **self.headers,
                    "Authorization": f'Basic {self.credentials("", self.password)}',
                },
            )
            self.assertEqual(response.status_code, 400, response.json())
    def test_user_login(self):
        with TestClient(app) as client:
            client.post(
                "/signup",
                headers={
                    **self.headers,
                    "Authorization": f'Basic {self.credentials(self.username, self.password)}',
                },
            )
            response = client.post(
                "/login",
                headers={
                    **self.headers,
                    "Authorization": f'Basic {self.credentials(self.username, self.password)}',
                },
            )
            self.assertEqual(response.status_code, 200, response.json())