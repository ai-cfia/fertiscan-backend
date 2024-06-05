import os
import unittest
import Levenshtein
import json
from backend import curl_file, save_text_to_file
from dotenv import load_dotenv
from backend.ocr import OCR
from backend.document_storage import DocumentStorage

def levenshtein_similarity(str1, str2):
    # Calculate the Levenshtein distance
    distance = Levenshtein.distance(str1, str2)
    
    # Determine the maximum possible length
    max_len = max(len(str1), len(str2))
    
    if max_len == 0:
        return 100.0  # If both strings are empty, they are identical
    
    # Calculate the similarity as a percentage
    similarity_percentage = (1 - (distance / max_len)) * 100
    
    return similarity_percentage

class TestOCR(unittest.TestCase):
    def setUp(self):
        load_dotenv()
        api_endpoint = os.getenv("AZURE_API_ENDPOINT")
        api_key = os.getenv("AZURE_API_KEY")

        self.ocr = OCR(api_endpoint, api_key)
        self.sample_image_path_1 = './samples/label1.png'
        self.sample_image_path_2 = './samples/label2.png'
        self.composite_image_path = './samples/composite_test.png'

        curl_file('https://scotts.com/dw/image/v2/BGFS_PRD/on/demandware.static/-/Sites-consolidated-master-catalog/default/dw5764839e/images/hi-res/scotts_01291_1_2000x2000.jpg?', self.sample_image_path_1)
        curl_file('https://tlhort.com/cdn/shop/products/10-52-0MAP.jpg', self.sample_image_path_2)

    def test_extract_text(self):
        # Prepare the document bytes
        with open(self.sample_image_path_2, 'rb') as f:
            document_bytes = f.read()

        # Extract text
        result = self.ocr.extract_text(document_bytes)
        
        # Extract content from result
        extracted_text = result.to_dict()["content"]

        # Define patterns for each word
        patterns = [
            r'\bAmmonium\b',
            r'\bPhosphate\b',
            r'\bGranular\b',
            r'\b25\b',
            r'\bTerraLink\b',
            r'\bCAUTION\b'
        ]
        
        # Check if each pattern matches the extracted text
        for pattern in patterns:
            self.assertRegex(text=extracted_text, expected_regex=pattern)

    def test_composite_image_text_extraction(self):
        # Create a DocumentStorage instance and add images
        doc_storage = DocumentStorage()
        doc_storage.add_image(self.sample_image_path_1)
        doc_storage.add_image(self.sample_image_path_2)

        # Get the composite image bytes
        composite_image_bytes = doc_storage.get_document()

        # Save the composite image bytes to a file
        # save_bytes_to_image(composite_image_bytes, self.composite_image_path)

        # Extract text from the composite image
        result = self.ocr.extract_text(composite_image_bytes)

        # Extract content from result
        extracted_text = result.to_dict()["content"]

        # Verify that the extracted text contains the text from both sample images
        with open(self.sample_image_path_1, 'rb') as f:
            document_bytes_1 = f.read()
        with open(self.sample_image_path_2, 'rb') as f:
            document_bytes_2 = f.read()

        result_1 = self.ocr.extract_text(document_bytes_1)
        result_2 = self.ocr.extract_text(document_bytes_2)
        
        save_text_to_file(json.dumps(result_1.to_dict(), indent=4), output_path=self.sample_image_path_1.replace(".png",".json"))
        save_text_to_file(json.dumps(result_2.to_dict(), indent=4), output_path=self.sample_image_path_2.replace(".png",".json"))

        extracted_text_1 = result_1.to_dict()["content"]
        extracted_text_2 = result_2.to_dict()["content"]


        distance = levenshtein_similarity(extracted_text, extracted_text_1 + " " + extracted_text_2)

        self.assertGreater(distance, 0.9, "The distance between the merged text and individual extractions is too great!")

    def tearDown(self):
        # Clean up created files after tests
        if os.path.exists(self.composite_image_path):
            os.remove(self.composite_image_path)
        if os.path.exists(self.sample_image_path_1):
            os.remove(self.sample_image_path_1)
        if os.path.exists(self.sample_image_path_2):
            os.remove(self.sample_image_path_2)  
