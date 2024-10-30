import base64
import os
import unittest
import uuid

import requests
from fastapi.testclient import TestClient

from app.main import app


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

    def test_health_check(self):
        with TestClient(app) as client:
            response = client.get("/health")
            self.assertEqual(response.status_code, 200)
            self.assertDictEqual(response.json(), {"status": "ok"})

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

    def test_user_signup_conflict(self):
        with TestClient(app) as client:
            response = client.post(
                "/signup",
                headers={
                    **self.headers,
                    "Authorization": f"Basic {self.credentials(self.username, self.password)}",
                },
            )
            self.assertEqual(response.status_code, 201, response.json())

            response = client.post(
                "/signup",
                headers={
                    **self.headers,
                    "Authorization": f"Basic {self.credentials(self.username, self.password)}",
                },
            )
            self.assertEqual(response.status_code, 409, response.json())

    def test_user_signup(self):
        with TestClient(app) as client:
            username = str(uuid.uuid4())
            response = client.post(
                "/signup",
                headers={
                    **self.headers,
                    "Authorization": f"Basic {self.credentials(username, self.password)}",
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
                    "Authorization": f"Basic {self.credentials(self.username, self.password)}",
                },
            )
            response = client.post(
                "/login",
                headers={
                    **self.headers,
                    "Authorization": f"Basic {self.credentials(self.username, self.password)}",
                },
            )
            self.assertEqual(response.status_code, 200, response.json())

    def test_user_login_not_found(self):
        new_username = uuid.uuid4().hex
        with TestClient(app) as client:
            response = client.post(
                "/login",
                headers={
                    **self.headers,
                    "Authorization": f"Basic {self.credentials(new_username, self.password)}",
                },
            )
            self.assertEqual(response.status_code, 404, response.json())
