import os
import unittest
import json
from dotenv import load_dotenv
from backend.gpt import GPT
from backend.ollama import Ollama

class TestLanguageModel(unittest.TestCase):
    def setUp(self):
        load_dotenv()

        gpt_api_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        gpt_api_key = os.getenv("AZURE_OPENAI_KEY")

        ollama_api_endpoint = os.getenv("OLLAMA_API_ENDPOINT")

        self.gpt = GPT(api_endpoint=gpt_api_endpoint, api_key=gpt_api_key)
        self.ollama = Ollama(api_endpoint=ollama_api_endpoint)

        self.prompt = """
        Fertilizer Label:
        Example Fertilizer Co. is located at 1234 Green St, Fertile City, FC 56789. Visit us at www.examplefertilizer.com or call 123-456-7890.
        Manufactured by Example Manufacturer Inc., located at 5678 Blue St, Fertile City, FC 12345. Visit www.examplemanufacturer.com or call 987-654-3210.
        Our product, SuperGrow, has a registration number of 12345-678 and a lot number Lot 54321. The NPK ratio is 10-10-10.
        Precautionary statements include: Tenir hors de portée des enfants (FR) and Keep out of reach of children (EN).
        Instructions: Appliquer uniformément sur le sol (FR) and Apply evenly on the soil (EN).
        Ingredients: Azote, Phosphore, Potassium (FR) and Nitrogen, Phosphorus, Potassium (EN).
        Specifications: Conforme aux normes (FR) and Meets standards (EN).
        Cautions: Éviter tout contact avec la peau (FR) and Avoid contact with skin (EN).
        Recommendation: Utiliser deux fois par mois (FR) and Use twice a month (EN).
        First Aid: En cas d'ingestion, contacter le centre antipoison (FR) and In case of ingestion, contact poison control (EN).
        Warranty: Garantie de satisfaction (FR) and Satisfaction guaranteed (EN).
        Danger: Danger d'explosion (FR) and Explosion hazard (EN).
        Guaranteed Analysis: Azote 10%, Phosphore 10%, Potassium 10%.
        The product weighs 20kg, has a density of 1.2g/cm³, and a volume of 16L.
        Other label text in French: Ce produit est conforme aux exigences de sécurité.
        Other label text in English: This product meets safety requirements.
        """
    
    def check_json(self, result_json: str):
        # Check that the expected fields are correctly populated
        self.assertIn("company_name", result_json)
        self.assertEqual(result_json["company_name"], "Example Fertilizer Co.")
        
        self.assertIn("company_address", result_json)
        self.assertEqual(result_json["company_address"], "1234 Green St, Fertile City, FC 56789")

        self.assertIn("company_website", result_json)
        self.assertEqual(result_json["company_website"], "www.examplefertilizer.com")

        self.assertIn("company_phone_number", result_json)
        self.assertEqual(result_json["company_phone_number"], "123-456-7890")

        self.assertIn("fertiliser_npk", result_json)
        self.assertEqual(result_json["fertiliser_npk"], "10-10-10")

        self.assertIn("fertiliser_weight", result_json)
        self.assertEqual(result_json["fertiliser_weight"], "20kg")

        # Check that the expected fields are "null" for missing data
        self.assertIn("manufacturer_address", result_json)
        self.assertEqual(result_json["manufacturer_address"], "5678 Blue St, Fertile City, FC 12345")
        self.assertIn("manufacturer_website", result_json)
        self.assertEqual(result_json["manufacturer_website"], "www.examplemanufacturer.com")
        self.assertIn("manufacturer_phone_number", result_json)
        self.assertEqual(result_json["manufacturer_phone_number"], "987-654-3210")

    def test_generate_form_gpt(self):
        result = self.gpt.generate_form(self.prompt)
        result_json = json.loads(result)
        self.check_json(result_json)


    def test_generate_form_ollama(self):
        result = self.ollama.generate_form(self.prompt)
        result_json = json.loads(result)
        self.check_json(result_json)


if __name__ == '__main__':
    unittest.main()
