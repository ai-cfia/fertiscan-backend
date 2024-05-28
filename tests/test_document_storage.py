import unittest
import os
from PIL import UnidentifiedImageError
from backend.document_storage import DocumentStorage, save_bytes_to_image

class TestDocumentStorage(unittest.TestCase):
    
    def setUp(self):
        self.store = DocumentStorage()
        self.sample_image_path_1 = './samples/label1.png'
        self.sample_image_path_2 = './samples/label2.png'
        self.composite_image_path = './samples/composite_test.png'

    def test_add_image_from_nonexistent_file(self):
        with self.assertRaises(FileNotFoundError):
            self.store.add_image('fake_path')

    def test_add_image_from_bytes(self):
        fake_bytes = b'fake image data'
        with self.assertRaises(UnidentifiedImageError):
            self.store.add_image(fake_bytes)

    def test_add_image_invalid_format(self):
        with self.assertRaises(ValueError):
            self.store.add_image(123)  # Invalid format

    def test_get_document_empty(self):
        with self.assertRaises(ValueError):
            self.store.get_document()    

    def test_add_image(self):
        self.store.add_image(self.sample_image_path_1)
        self.assertEqual(len(self.store.images), 1)

    def test_get_composite_image(self):
        self.store.add_image(self.sample_image_path_1)
        self.store.add_image(self.sample_image_path_2)

        composite_image = self.store.get_document()
        save_bytes_to_image(composite_image, self.composite_image_path)
        self.assertTrue(os.path.exists(self.composite_image_path))

    def tearDown(self):
        # Clean up created files after tests
        if os.path.exists(self.composite_image_path):
            os.remove(self.composite_image_path)
        

if __name__ == '__main__':
    unittest.main()
