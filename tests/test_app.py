import base64
import os
import unittest
import uuid
from io import BytesIO
from unittest.mock import MagicMock, patch

import datastore
import datastore.db
import requests
from azure.storage.blob import BlobServiceClient

from app import app

test_client = app.test_client()

class APITestCase(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        app.testing = True
        
        self.username = 'test'
        self.password = 'password1'
        self.inspection = None
        self.inspection_id = None
        encoded_credentials = self.credentials(self.username, self.password)

        unittest.TestLoader.sortTestMethodsUsing = None

        self.headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Methods': '*',
        }
        
    @classmethod
    def credentials(self, username, password) -> str:
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        
        return encoded_credentials

    def test_health(self):
        response = test_client.get('/health', headers=self.headers)
        self.assertEqual(response.status_code, 200)

    def test_conn(self):
        # Create a real database connection
        FERTISCAN_SCHEMA = os.getenv("FERTISCAN_SCHEMA", "fertiscan_0.0.11")
        FERTISCAN_DB_URL = os.getenv("FERTISCAN_DB_URL")
        try:
            conn = datastore.db.connect_db(conn_str=FERTISCAN_DB_URL, schema=FERTISCAN_SCHEMA)
            cursor = conn.cursor()
            datastore.db.create_search_path(conn, cursor, FERTISCAN_SCHEMA)
            cursor.execute(f"""SELECT 1 from "{FERTISCAN_SCHEMA}".users""")
            cursor.fetchall()
            conn.close()
        except Exception as e:
            self.fail(f"Database connection failed: {str(e)}")

    def test_blob_conn(self):
        FERTISCAN_STORAGE_URL = os.getenv("FERTISCAN_STORAGE_URL")
        self.assertIsNotNone(
            FERTISCAN_STORAGE_URL,
            "FERTISCAN_STORAGE_URL environment variable is not set.",
        )
        blob_service_client = BlobServiceClient.from_connection_string(
            FERTISCAN_STORAGE_URL
        )
        service_properties = blob_service_client.get_service_properties()
        self.assertIsNotNone(
            service_properties, "Failed to retrieve service properties."
        )

    def test_signup_missing_username(self):
        response = test_client.post(
            '/signup',
            headers={ **self.headers,  'Authorization': f'Basic {self.credentials("", self.password)}'},
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 400, response.json)
    
    def test_signup(self):
        response = test_client.post(\
            '/signup',
            headers=self.headers,
            content_type='application/x-www-form-urlencoded',
        )
        if response.json['message'] != "User already exists":
            self.assertEqual(response.status_code, 201, response.json)

    def test_login_missing_username(self):
        response = test_client.post('/login', headers={ **self.headers,  'Authorization': f'Basic {self.credentials("", self.password)}'},)
        self.assertEqual(response.status_code, 400, response.json)
    
    def test_login_unknow_username(self):
        username = str(uuid.uuid4())
        response = test_client.post(\
            '/login',
            headers={ **self.headers,  'Authorization': f'Basic {self.credentials(username, self.password)}'},
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 401, response.json)

    def test_login(self):
        response = test_client.post(
            '/login',
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200, response.json)

    def test_create_empty_inspection(self):
        response = test_client.post('/inspections', headers=self.headers)
        self.assertEqual(response.status_code, 500, response.json)

    # If the inspection is created, it should at least return a message testifying that.
    def test_create_inspection(self):
        with requests.get('https://raw.githubusercontent.com/ai-cfia/fertiscan-pipeline/main/expected.json') as response:
            json_data = response.json()
            response = test_client.post(
                '/inspections', 
                headers=self.headers,
                content_type='application/json',
                json=json_data
            )
            self.assertEqual(response.status_code, 201, response.json)
            self.__class__.inspection_id = response.json['inspection_id']
            self.__class__.inspection = response.json
            
    def test_update_empty_inspection(self):
        inspection_id = str(uuid.uuid4())
        response = test_client.put(f'/inspections/{inspection_id}', headers=self.headers)
        self.assertEqual(response.status_code, 500, response.json)

    # Requires the database schema
    def test_update_inspection_fake_id(self):
        # Ensure that `test_create_inspection` has run and set the inspection data
        self.assertIsNotNone(self.inspection, "Inspection data should not be None")
      
        inspection_id = str(uuid.uuid4()) # Should fail since the inspection with this id does not exist
        response = test_client.put(
            f'/inspections/{inspection_id}', 
            headers=self.headers,
            content_type='application/json',
            json=self.inspection
        )
        self.assertEqual(response.status_code, 500, response.json)

    # Requires the database schema
    def test_update_inspection(self):
        # Ensure that `test_create_inspection` has run and set the inspection data
        self.assertIsNotNone(self.inspection_id, "Inspection ID should not be None")
        self.assertIsNotNone(self.inspection, "Inspection data should not be None")
        
        response = test_client.put(
            f'/inspections/{self.inspection_id}', 
            headers=self.headers,
            content_type='application/json',
            json=self.inspection
        )
        self.assertEqual(response.status_code, 200, response.json)
    
    def test_get_inspection_from_unknown_user(self):
        username = str(uuid.uuid4())
        response = test_client.get(
            '/inspections',
            headers={ **self.headers,  'Authorization': f'Basic {self.credentials(username, self.password)}'},
        )
        self.assertEqual(response.status_code, 500, response.json)

    def test_get_inspection(self):
        response = test_client.get(\
            '/inspections', 
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200, response.json)

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
