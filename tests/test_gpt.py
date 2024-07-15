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

        self.gpt35 = GPT(api_endpoint=gpt_api_endpoint, api_key=gpt_api_key)
        self.gpt4 = GPT(api_endpoint=gpt_api_endpoint, api_key=gpt_api_key, deployment="ailab-llm")


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
        file = open('./docs/expected.json')
        expected_json = json.load(file)

        # Check if all keys are present
        for key in expected_json.keys():
            assert key in extracted_info, f"Key '{key}' is missing in the extracted information"

        # Check if the json matches the format
        FertiliserForm(**expected_json)

        # Check if values match
        for key, expected_value in expected_json.items():
            assert levenshtein_similarity(str(extracted_info[key]), str(expected_value)) > 0.9, f"Value for key '{key}' does not match. Expected '{expected_value}', got '{extracted_info[key]}'"

    def test_generate_form_gpt35(self):
        prediction = self.gpt35.generate_form(self.prompt)
        print(prediction.form)
        result_json = json.loads(prediction.form)
        self.check_json(result_json)

    # Not currently used and expensive.
    # def test_generate_form_gpt4(self):
    #     prediction = self.gpt4.generate_form(self.prompt)
    #     print(prediction.form)
    #     result_json = json.loads(prediction.form)
    #     self.check_json(result_json)


if __name__ == '__main__':
    unittest.main()
