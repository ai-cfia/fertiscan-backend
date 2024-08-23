import os
import uuid
import json
import unittest
import base64
import requests
import datastore

from io import BytesIO

import datastore.db
from app import app
from azure.storage.blob import BlobServiceClient
from unittest.mock import patch, MagicMock

test_client = app.test_client()

class APITestCase(unittest.TestCase):
    def setUp(self):
        app.testing = True
        
        username = 'test'
        password = 'password1'
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        
        self.headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Methods': '*',
        }


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

        try:
            # Create the BlobServiceClient object which will be used to create a container client
            blob_service_client = BlobServiceClient.from_connection_string(FERTISCAN_STORAGE_URL)

            # List all containers to test the connection
            containers = blob_service_client.list_containers()

            for container in containers:
                print(container.name)

        except Exception as e:
            self.fail("Connection failed:", str(e))

    def test_create_user_missing_username(self):
        response = test_client.post(
            '/signup',
            headers=self.headers,
            content_type='application/x-www-form-urlencoded',
            data={'password': 'password1'}
        )
        self.assertEqual(response.status_code, 400, response.json)

    def test_login(self):
        response = test_client.post(
            '/login',
            headers=self.headers,
            content_type='application/x-www-form-urlencoded',
            data={'username': 'test-bryan', 'password': 'password1'}
        )
        self.assertEqual(response.status_code, 200, response.json)

    
    def test_signup(self):
        response = test_client.post(\
            '/signup',
            headers=self.headers,
            content_type='application/x-www-form-urlencoded',
            data={'username': 'test', 'password': 'password1'}
        )
        if response.json['message'] != "User already exists":
            self.assertEqual(response.status_code, 201, response.json)

    def test_missing_username(self):
        response = test_client.post('/login', headers=self.headers)
        self.assertEqual(response.status_code, 400, response.json)
    
    def test_unknow_username(self):
        username = str(uuid.uuid4())
        response = test_client.post(\
            '/login',
            headers=self.headers,
            content_type='application/x-www-form-urlencoded',
            data={'username': username, 'password': 'password1'}
        )
        self.assertEqual(response.status_code, 401, response.json)

    def test_create_inspection(self):
        with requests.get('https://raw.githubusercontent.com/ai-cfia/fertiscan-pipeline/main/expected.json') as response:
            json_data = str(response.content)
            response = test_client.post(
                '/inspections', 
                headers=self.headers,
                content_type='application/json',
                json=json_data
            )
            self.assertEqual(response.status_code, 201, response.json)

    def test_create_empty_inspection(self):
        response = test_client.post('/inspections', headers=self.headers)
        self.assertEqual(response.status_code, 500, response.json)

    # I think it requires an object with the format the datastore expects.
    def test_update_inspection(self):
        with requests.get('https://raw.githubusercontent.com/ai-cfia/fertiscan-pipeline/main/expected.json') as response:
            inspection_id = str(uuid.uuid4())
            json_data = str(response.content)
            response = test_client.put(
                f'/inspections/{inspection_id}', 
                headers=self.headers,
                content_type='application/json',
                json=json_data
            )
            self.assertEqual(response.status_code, 201, response.json)

    def test_update_empty_inspection(self):
        inspection_id = str(uuid.uuid4())
        response = test_client.put(f'/inspections/{inspection_id}', headers=self.headers)
        self.assertEqual(response.status_code, 500, response.json)

    def test_get_inspection_from_none(self):
        response = test_client.get('/inspections', content_type='application/json', headers=self.headers)
        self.assertEqual(response.status_code, 500, response.json)
    
    def test_get_inspection_from_unknown_user(self):
        username = str(uuid.uuid4())
        response = test_client.get(
            '/inspections',
            headers=self.headers, 
            content_type='application/json',
            data={'username': username, 'password': 'password1'}
        )
        self.assertEqual(response.status_code, 500, response.json)

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
