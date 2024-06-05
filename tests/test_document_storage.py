import unittest
import os
import requests
from backend.document_storage import DocumentStorage, save_bytes_to_file

class TestDocumentStorage(unittest.TestCase):
    
    def setUp(self):
        self.store = DocumentStorage()
        self.sample_image_path_1 = './samples/label1.png'
        self.sample_image_path_2 = './samples/label2.png'
        self.composite_image_path = './samples/composite_test.png'
        self.composite_document_path = './samples/composite_test.pdf'

        curl_file('https://lesgranulaines.com/wp-content/uploads/2024/01/IMG-5014-copie.webp', self.sample_image_path_1)
        curl_file('https://tlhort.com/cdn/shop/products/10-52-0MAP.jpg', self.sample_image_path_2)


    def test_add_image_from_nonexistent_file(self):
        with self.assertRaises(FileNotFoundError):
            self.store.add_image('fake_path')

    def test_get_document_empty(self):
        with self.assertRaises(ValueError):
            self.store.get_document()    

    def test_add_image(self):
        self.store.add_image(self.sample_image_path_1)
        self.assertEqual(len(self.store.images), 1)

    def test_get_composite_image(self):
        self.store.add_image(self.sample_image_path_1)
        self.store.add_image(self.sample_image_path_2)

        composite_image = self.store.get_document(format='png')
        save_bytes_to_file(composite_image, self.composite_image_path)
        self.assertTrue(os.path.exists(self.composite_image_path))
    
    def test_get_pdf_document(self):
        self.store.add_image(self.sample_image_path_1)
        self.store.add_image(self.sample_image_path_2)

        doc = self.store.get_document(format='pdf')
        save_bytes_to_file(doc, self.composite_document_path)
        self.assertTrue(os.path.exists(self.composite_document_path))

    def tearDown(self):
        # Clean up created files after tests
        if os.path.exists(self.composite_image_path):
            os.remove(self.composite_image_path)
        if os.path.exists(self.composite_document_path):
            os.remove(self.composite_document_path)
        if os.path.exists(self.sample_image_path_1):
            os.remove(self.sample_image_path_1)
        if os.path.exists(self.sample_image_path_2):
            os.remove(self.sample_image_path_2)
            
def curl_file(url:str, path: str):
    img_data = requests.get(url).content
    with open(path, 'wb') as handler:
        handler.write(img_data)    

if __name__ == '__main__':
    unittest.main()
