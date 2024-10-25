import os
import unittest
import uuid

from fastapi.testclient import TestClient

from app.main import app


class TestAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Set up the environment variable to indicate testing mode
        os.environ["TESTING"] = "True"

    def setUp(self):
        # Generate unique IDs and values for each test run
        self.subtype_id = uuid.uuid4()
        self.type_en = uuid.uuid4().hex
        self.type_fr = uuid.uuid4().hex

    def test_rollbacks(self):
        # Test inserting a new subtype
        with TestClient(app) as client:
            response = client.post(
                "/subtypes",
                params={
                    "id": self.subtype_id,
                    "type_en": self.type_en,
                    "type_fr": self.type_fr,
                },
            )
            # Check if the POST request was successful
            self.assertEqual(response.status_code, 200)

            # Validate the response content
            results = response.json().get("message")
            self.assertIsNotNone(results)

            # Check if the inserted subtype matches the expected values
            response = client.get(f"/subtypes/{self.subtype_id}")
            self.assertEqual(response.status_code, 200)
            # Validate the response content
            results = response.json().get("message")
            self.assertIsNotNone(results)
            self.assertEqual(results[0], str(self.subtype_id))
            self.assertEqual(results[1], self.type_fr)
            self.assertEqual(results[2], self.type_en)

        # Test if the subtype was rolled back (i.e., not found)
        with TestClient(app) as client:
            response = client.get(f"/{self.subtype_id}")
            # Expect a 404 status code, indicating that the subtype was not found
            self.assertEqual(response.status_code, 404)
