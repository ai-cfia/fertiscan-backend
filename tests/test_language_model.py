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
        result = self.model.generate_form(prompt)
        result_json = json.loads(result)

        # Check that the expected fields are correctly populated
        self.assertIn("compagny_name", result_json)
        self.assertEqual(result_json["compagny_name"], "Example Fertilizer Co.")
        
        self.assertIn("compagny_address", result_json)
        self.assertEqual(result_json["compagny_address"], "1234 Green St, Fertile City, FC 56789")

        self.assertIn("compagny_website", result_json)
        self.assertEqual(result_json["compagny_website"], "www.examplefertilizer.com")

        self.assertIn("compagny_phone_number", result_json)
        self.assertEqual(result_json["compagny_phone_number"], "123-456-7890")

        self.assertIn("fertiliser_NPK", result_json)
        self.assertEqual(result_json["fertiliser_NPK"], "10-10-10")

        self.assertIn("fertiliser_first_aid_FR", result_json)
        self.assertEqual(result_json["fertiliser_first_aid_FR"], "En cas d'ingestion, contacter le centre antipoison")

        self.assertIn("fertiliser_weight", result_json)
        self.assertEqual(result_json["fertiliser_weight"], "20kg")

        # Check that the expected fields are "null" for missing data
        self.assertIn("manufacturer_name", result_json)
        self.assertEqual(result_json["manufacturer_name"], "Example Manufacturer Inc.")
        self.assertIn("manufacturer_address", result_json)
        self.assertEqual(result_json["manufacturer_address"], "5678 Blue St, Fertile City, FC 12345")
        self.assertIn("manufacturer_website", result_json)
        self.assertEqual(result_json["manufacturer_website"], "www.examplemanufacturer.com")
        self.assertIn("manufacturer_phone_number", result_json)
        self.assertEqual(result_json["manufacturer_phone_number"], "987-654-3210")

if __name__ == '__main__':
    unittest.main()