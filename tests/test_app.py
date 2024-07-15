import unittest
from io import BytesIO
from app import app
from unittest.mock import patch, MagicMock

class APITestCase(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.client = app.test_client()
        self.headers = {
            'Authorization': 'Basic ' + 'user1:password1'
        }

    def test_ping(self):
        response = self.client.get('/ping', headers=self.headers)
        self.assertEqual(response.status_code, 200)

    def test_create_form(self):
        response = self.client.post('/forms', headers=self.headers)
        self.assertEqual(response.status_code, 201)
        self.assertIn('form_id', response.json)

    def test_update_form(self):
        form_id = "some_form_id"
        response = self.client.put(f'/forms/{form_id}', headers=self.headers, json={"form_data": {"key": "value"}})
        self.assertEqual(response.status_code, 503)  # Service Unavailable

    def test_discard_form(self):
        form_id = "some_form_id"
        response = self.client.delete(f'/forms/{form_id}', headers=self.headers)
        self.assertEqual(response.status_code, 503)  # Service Unavailable

    def test_get_form(self):
        form_id = "some_form_id"
        response = self.client.get(f'/forms/{form_id}', headers=self.headers)
        self.assertEqual(response.status_code, 503)  # Service Unavailable

    def test_analyze_document_no_files(self):
        response = self.client.post('/analyze', headers=self.headers)
        self.assertEqual(response.status_code, 400)

    def test_analyze_invalid_document(self):
        # Create a sample file to upload
        data = {
            'images': (BytesIO(b"sample image content"), 'test_image.png')
        }
        
        response = self.client.post(
            '/analyze',
            content_type='multipart/form-data',
            data=data
        )

        # Document Intelligence throws an error
        self.assertEqual(response.status_code, 500)
        self.assertIn('error', response.json)

    @patch('app.language_model.generate_form')
    @patch('app.ocr.extract_text')
    def test_analyze_document_gpt_error(self, mock_ocr, mock_gpt):
        mock_ocr.return_value = MagicMock(content="OCR result")
        mock_gpt.side_effect = Exception("GPT error")

        data = {
            'images': (BytesIO(b"sample image content"), 'test_image.png')
        }

        response = self.client.post(
            '/analyze',
            content_type='multipart/form-data',
            data=data
        )

        self.assertEqual(response.status_code, 500)
        self.assertIn('error', response.json)

if __name__ == '__main__':
    unittest.main()
