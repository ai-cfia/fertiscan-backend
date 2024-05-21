import unittest
from unittest.mock import patch, mock_open, MagicMock
from io import BytesIO
import os
from backend import DocumentStore  # Replace 'your_module_path' with the actual module path

class TestDocumentStore(unittest.TestCase):
    
    def setUp(self):
        self.store = DocumentStore()

    @patch('builtins.open', new_callable=mock_open, read_data="fake image data")
    @patch('os.path.exists', return_value=True)
    def test_add_page_from_file(self, mock_exists, mock_open):
        self.store.add_page('fake_path')
        self.assertEqual(self.store.get_document(), 'fake image data')

    @patch('os.path.exists', return_value=False)
    def test_add_page_from_nonexistent_file(self, mock_exists):
        with self.assertRaises(FileNotFoundError):
            self.store.add_page('fake_path')

    def test_add_page_from_bytes(self):
        fake_bytes = b'fake image data'
        self.store.add_page(fake_bytes)
        self.assertEqual(self.store.get_document(), fake_bytes)

    def test_add_page_invalid_format(self):
        with self.assertRaises(ValueError):
            self.store.add_page(123)  # Invalid format

    def test_get_document_empty(self):
        with self.assertRaises(ValueError):
            self.store.get_document()

if __name__ == '__main__':
    unittest.main()
