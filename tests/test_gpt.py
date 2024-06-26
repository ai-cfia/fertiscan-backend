import os
import unittest
import json
from tests import levenshtein_similarity
from dotenv import load_dotenv
from backend.form import FertiliserForm
from backend.gpt import GPT

class TestLanguageModel(unittest.TestCase):
    def setUp(self):
        load_dotenv()

        gpt_api_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        gpt_api_key = os.getenv("AZURE_OPENAI_KEY")

        self.gpt = GPT(api_endpoint=gpt_api_endpoint, api_key=gpt_api_key)

        self.prompt = """
        GreenGrow Fertilizers Inc.
        123 Greenway Blvd
        Springfield IL 62701 USA
        www.greengrowfertilizers.com
        +1 800 555 0199
        AgroTech Industries Ltd.
        456 Industrial Park Rd
        Oakville ON L6H 5V4 Canada
        www.agrotechindustries.com
        +1 416 555 0123
        SuperGrow 20-20-20 
        Registration Number F12345678
        Lot L987654321
        25 kg
        55 lb
        1.2 g/cm³
        20.8 L
        Warranty: Guaranteed analysis of nutrients.
        Total Nitrogen (N) 20%
        Available Phosphate (P2O5) 20%
        Soluble Potash (K2O) 20%
        Micronutrients:
        Iron (Fe) 0.10%
        Zinc (Zn) 0.05%
        Manganese (Mn) 0.05%
        Organic Ingredients:
        Bone meal 5%
        Seaweed extract 3%
        Humic acid 2%
        Inert Ingredients:
        Clay
        Sand
        Perlite
        Specifications:
        Humidity 10%
        pH 6.5
        Solubility 100%
        Precautions:
        Keep out of reach of children.
        Avoid contact with skin and eyes.
        Instructions:
        1. Dissolve 50g in 10L of water.
        2. Apply every 2 weeks.
        3. Store in a cool, dry place.
        Cautions:
        Wear protective gloves when handling.
        First Aid:
        In case of contact with eyes, rinse immediately with plenty of water and seek medical advice.
        En cas de contact avec les yeux, rincer immédiatement à grande eau et consulter un médecin.
        Précautions:
        Tenir hors de portée des enfants.
        Éviter le contact avec la peau et les yeux.
        Instructions:
        1. Dissoudre 50g dans 10L d'eau.
        2. Appliquer toutes les 2 semaines.
        3. Conserver dans un endroit frais et sec.
        Cautions:
        Porter des gants de protection lors de la manipulation.
        First Aid:
        En cas de contact avec les yeux, rincer immédiatement à grande eau et consulter un médecin.
        """
    
    def check_json(self, extracted_info):
        expected_json = {
            "company_name": "GreenGrow Fertilizers Inc.",
            "company_address": "123 Greenway Blvd, Springfield, IL 62701, USA",
            "company_website": "www.greengrowfertilizers.com",
            "company_phone_number": "+1 800 555 0199",
            "manufacturer_name": "AgroTech Industries Ltd.",
            "manufacturer_address": "456 Industrial Park Rd, Oakville, ON L6H 5V4, Canada",
            "manufacturer_website": "www.agrotechindustries.com",
            "manufacturer_phone_number": "+1 416 555 0123",
            "fertiliser_name": "SuperGrow 20-20-20",
            "registration_number": "F12345678",
            "lot_number": "L987654321",
            "weight_kg": "25 kg",
            "weight_lb": "55 lb",
            "density": "1.2 g/cm³",
            "volume": "20.8 L",
            "warranty": "Guaranteed analysis of nutrients.",
            "npk": "20-20-20",
            "instructions_en": [
                "Dissolve 50g in 10L of water.",
                "Apply every 2 weeks.",
                "Store in a cool, dry place."
            ],
            "micronutrients_en": [
                {"name": "Iron (Fe)", "percentage": "0.10%"},
                {"name": "Zinc (Zn)", "percentage": "0.05%"},
                {"name": "Manganese (Mn)", "percentage": "0.05%"}
            ],
            "organic_ingredients_en": [
                {"name": "Bone meal", "percentage": "5%"},
                {"name": "Seaweed extract", "percentage": "3%"},
                {"name": "Humic acid", "percentage": "2%"}
            ],
            "inert_ingredients_en": ["Clay", "Sand", "Perlite"],
            "specifications_en": [
                {"humidity": "10%", "ph": "6.5", "solubility": "100%"}
            ],
            "cautions_en": [
                "Wear protective gloves when handling.",
                "Keep out of reach of children. Avoid contact with skin and eyes."
            ],
            "first_aid_en": ["In case of contact with eyes, rinse immediately with plenty of water and seek medical advice."],
            "cautions_fr": [
                "Tenir hors de portée des enfants. Éviter le contact avec la peau et les yeux.",
                "Porter des gants de protection lors de la manipulation.",
            ],
            "instructions_fr": [
                "Dissoudre 50g dans 10L d'eau.",
                "Appliquer toutes les 2 semaines.",
                "Conserver dans un endroit frais et sec."
            ],
            "micronutrients_fr": [
                {"name": "Fer (Fe)", "percentage": "0.10%"},
                {"name": "Zinc (Zn)", "percentage": "0.05%"},
                {"name": "Manganèse (Mn)", "percentage": "0.05%"}
            ],
            "organic_ingredients_fr": [
                {"name": "Farine d'os", "percentage": "5%"},
                {"name": "Extrait d'algues", "percentage": "3%"},
                {"name": "Acide humique", "percentage": "2%"}
            ],
            "inert_ingredients_fr": ["Argile", "Sable", "Perlite"],
            "specifications_fr": [
                {"humidity": "10%", "ph": "6.5", "solubility": "100%"}
            ],
            "first_aid_fr": ["En cas de contact avec les yeux, rincer immédiatement à grande eau et consulter un médecin."],
            "guaranteed_analysis": [
                {"nutrient": "Total Nitrogen (N)", "percentage": "20%"},
                {"nutrient": "Available Phosphate (P2O5)", "percentage": "20%"},
                {"nutrient": "Soluble Potash (K2O)", "percentage": "20%"}
            ]
        }
        # Check if all keys are present
        for key in expected_json.keys():
            assert key in extracted_info, f"Key '{key}' is missing in the extracted information"

        # Check if the json matches the format
        FertiliserForm(**expected_json)

        # Check if values match
        for key, expected_value in expected_json.items():
            assert levenshtein_similarity(str(extracted_info[key]), str(expected_value)) > 0.9, f"Value for key '{key}' does not match. Expected '{expected_value}', got '{extracted_info[key]}'"

    def test_generate_form_gpt(self):
        prediction = self.gpt.generate_form(self.prompt)
        print(prediction.form)
        result_json = json.loads(prediction.form)
        self.check_json(result_json)


if __name__ == '__main__':
    unittest.main()
