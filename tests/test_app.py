import unittest
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

    def test_create_inspection(self):
        response = test_client.post('/inspections', headers=self.headers)
        self.assertEqual(response.status_code, 201)
        self.assertIn('inspection_id', response.json)

    def test_update_inspection(self):
        inspection_id = "some_inspection_id"
        response = test_client.put(f'/inspections/{inspection_id}', headers=self.headers, json={"inspection_data": {"key": "value"}})
        self.assertEqual(response.status_code, 503)  # Service Unavailable

    def test_discard_inspection(self):
        inspection_id = "some_inspection_id"
        response = test_client.delete(f'/inspections/{inspection_id}', headers=self.headers)
        self.assertEqual(response.status_code, 503)  # Service Unavailable

    def test_get_inspection(self):
        inspection_id = "some_inspection_id"
        response = test_client.get(f'/inspections/{inspection_id}', headers=self.headers)
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
            content_type='multipart/inspection-data',
            data=data
        )

        # Document Intelligence throws an error
        self.assertEqual(response.status_code, 500)
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

        self.assertEqual(response.status_code, 500)
        self.assertIn('error', response.json)
    def tearDown(self):
        """Executed after reach test"""
        app.testing = False

if __name__ == '__main__':
    unittest.main()
