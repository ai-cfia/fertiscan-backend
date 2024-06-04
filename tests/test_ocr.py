import os
import unittest
import Levenshtein
import json
from dotenv import load_dotenv
from backend.ocr import OCR, save_text_to_file
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

    def test_extract_text(self):
        # Prepare the document bytes
        with open(self.sample_image_path_1, 'rb') as f:
            document_bytes = f.read()

        # Extract text
        result = self.ocr.extract_text(document_bytes)
        
        # Extract content from result
        extracted_text = result.as_dict()["content"]

        # Define patterns for each word
        patterns = [
            r'\bCAMERON\b',
            r'\bPOIDS\b',
            r'\bengrais\b',
            r'\birritation\b',
            r'\bZinc\b',
            r'\bRESPONSABILITÉ\b'
        ]
        
        # Check if each pattern matches the extracted text
        for pattern in patterns:
            self.assertRegex(text=extracted_text, expected_regex=pattern)

        self.assertIn("CAMERON", extracted_text)
    
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
        extracted_text = result.content

        # Verify that the extracted text contains the text from both sample images
        with open(self.sample_image_path_1, 'rb') as f:
            document_bytes_1 = f.read()
        with open(self.sample_image_path_2, 'rb') as f:
            document_bytes_2 = f.read()

        result_1 = self.ocr.extract_text(document_bytes_1)
        result_2 = self.ocr.extract_text(document_bytes_2)

        extracted_text_1 = result_1.content
        extracted_text_2 = result_2.content

        distance = levenshtein_similarity(extracted_text, extracted_text_1 + " " + extracted_text_2)

        self.assertGreater(distance, 0.9, "The distance between the merged text and individual extractions is too great!")

    def tearDown(self):
        # Clean up created files after tests
        if os.path.exists(self.composite_image_path):
            os.remove(self.composite_image_path)
