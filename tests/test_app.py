import os
import uuid
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

    def test_health(self):
        response = test_client.get('/health', headers=self.headers)
        self.assertEqual(response.status_code, 200)

    def test_conn(self):
        # Create a real database connection
        FERTISCAN_SCHEMA = os.getenv("FERTISCAN_SCHEMA", "fertiscan_0.0.10")
        FERTISCAN_DB_URL = os.getenv("FERTISCAN_DB_URL")
        try:
            conn = datastore.db.connect_db(conn_str=FERTISCAN_DB_URL, schema=FERTISCAN_SCHEMA)
            conn.close()
        except Exception as e:
            self.fail(f"Database connection failed: {e}")

    def test_missing_username(self):
        response = test_client.post('/login', headers=self.headers)
        self.assertEqual(response.status_code, 400, response.json)

    
    def test_unknow_username(self):
        username = str(uuid.uuid4())
        response = test_client.post('/login', data={'username': username, 'password': 'password1'})
        self.assertEqual(response.status_code, 401, response.json)

    def test_analyze_document_no_files(self):
        response = test_client.post('/analyze', headers=self.headers)
        self.assertEqual(response.status_code, 400, response.json)

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
        self.assertEqual(response.status_code, 500, response.json)
        self.assertIn('error', response.json)

    @patch('app.gpt.create_inspection')
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

        self.assertEqual(response.status_code, 500, response.json)
        self.assertIn('error', response.json)
    def tearDown(self):
        """Executed after reach test"""
        app.testing = False

if __name__ == '__main__':
    unittest.main()
