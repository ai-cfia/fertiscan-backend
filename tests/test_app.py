import os
import unittest
import datastore

from io import BytesIO
from app import app
from unittest.mock import patch, MagicMock

test_client = app.test_client()

class APITestCase(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic ' + 'user1:password1'
        }

    def test_ping(self):
        response = test_client.get('/ping', headers=self.headers)
        self.assertEqual(response.status_code, 200)

    def test_conn(self):
        # Create a real database connection
        FERTISCAN_SCHEMA = os.getenv("FERTISCAN_SCHEMA", "fertiscan_0.0.8")
        FERTISCAN_DB_URL = os.getenv("FERTISCAN_DB_URL")
        try:
            conn = datastore.db.connect_db(conn_str=FERTISCAN_DB_URL, schema=FERTISCAN_SCHEMA)
            conn.close()
        except Exception as e:
            self.fail(f"Database connection failed: {e}")

    def test_create_form(self):
        response = test_client.post('/forms', headers=self.headers)
        self.assertEqual(response.status_code, 201)
        self.assertIn('form_id', response.json)

    def test_update_form(self):
        form_id = "some_form_id"
        response = test_client.put(f'/forms/{form_id}', headers=self.headers, json={"form_data": {"key": "value"}})
        self.assertEqual(response.status_code, 503)  # Service Unavailable

    def test_discard_form(self):
        form_id = "some_form_id"
        response = test_client.delete(f'/forms/{form_id}', headers=self.headers)
        self.assertEqual(response.status_code, 503)  # Service Unavailable

    def test_get_form(self):
        headers = { **self.headers, 'label_id': 'some_label_id' }
        response = test_client.get('/forms', headers=headers)
        self.assertEqual(response.status_code, 503)  # Service Unavailable

    def test_analyze_document_no_files(self):
        response = test_client.post('/analyze', headers=self.headers)
        self.assertEqual(response.status_code, 400)

    def test_analyze_invalid_document(self):
        # Create a sample file to upload
        data = {
            'images': (BytesIO(b"sample image content"), 'test_image.png')
        }
        
        response = test_client.post(
            '/analyze',
            content_type='multipart/form-data',
            data=data
        )

        # Document Intelligence throws an error
        self.assertEqual(response.status_code, 500)
        self.assertIn('error', response.json)

    @patch('app.gpt.generate_form')
    @patch('app.ocr.extract_text')
    def test_analyze_document_gpt_error(self, mock_ocr, mock_gpt):
        mock_ocr.return_value = MagicMock(content="OCR result")
        mock_gpt.side_effect = Exception("GPT error")

        data = {
            'images': (BytesIO(b"sample image content"), 'test_image.png')
        }

        response = test_client.post(
            '/analyze',
            content_type='multipart/form-data',
            data=data
        )

        self.assertEqual(response.status_code, 500)
        self.assertIn('error', response.json)
    def tearDown(self):
        """Executed after reach test"""
        app.testing = False

if __name__ == '__main__':
    unittest.main()
