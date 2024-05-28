import os
import unittest
import json
from dotenv import load_dotenv
from backend.language_model import LanguageModel

class TestLanguageModel(unittest.TestCase):
    def setUp(self):
        load_dotenv()
        self.api_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_key = os.getenv("AZURE_OPENAI_KEY")

        self.model = LanguageModel(api_endpoint=self.api_endpoint, api_key=self.api_key)

    def test_generate_form(self):
        prompt = """
        Fertilizer Label:
        Compagny Name: Example Fertilizer Co.
        Compagny Address: 1234 Green St, Fertile City, FC 56789
        Compagny Website: www.examplefertilizer.com
        Compagny Phone Number: 123-456-7890
        Fertilizer NPK: 10-10-10
        Fertilizer First Aid (FR): In case of ingestion, contact poison control.
        Fertilizer Weight: 20kg
        """
        result = self.model.generate_form(prompt)
        result_json = json.loads(result)

        # Check that the expected fields are correctly populated
        self.assertIn("compagny_name", result_json)
        self.assertIn("compagny_address", result_json)
        self.assertIn("compagny_website", result_json)
        self.assertIn("compagny_phone_number", result_json)

        # Check that the expected fields are "null"
        self.assertIn("fertiliser_NPK", result_json)
        self.assertIsNone(result_json["fertiliser_NPK"])
        self.assertIn("fertiliser_first_aid_FR", result_json)
        self.assertIsNone(result_json["fertiliser_first_aid_FR"])
        self.assertIn("fertiliser_weight", result_json)
        self.assertIsNone(result_json["fertiliser_weight"])


if __name__ == '__main__':
    unittest.main()
