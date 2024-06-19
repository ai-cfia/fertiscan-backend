import os
import dspy
from openai.types.chat.completion_create_params import ResponseFormat

MODELS_WITH_RESPONSE_FORMAT = ["ailab-llm"]

class ProduceLabelForm(dspy.Signature):
    """You are a fertilizer label inspector working for the Canadian Food Inspection Agency. Your task is to classify all information present in the provided text using the specified keys. Your response should be accurate, formatted in JSON, and contain all the text from the provided text without modifications."""
    
    text = dspy.InputField(desc="The text of fertilizer label extracted using an OCR.")
    specification = dspy.InputField(desc="Follow this specification.")
    form = dspy.OutputField(desc="A complete JSON with all fields occupied. Do not return any note or additional text that isn't in the JSON.")

class GPT:
    def __init__(self, api_endpoint, api_key, deployment="ailab-gpt-35-turbo-16k"):
        if not api_endpoint or not api_key:
            raise ValueError("API endpoint and key are required to instantiate the GPT class.")

        # self.model = deployment

        response_format = None
        if deployment in MODELS_WITH_RESPONSE_FORMAT:
            response_format = ResponseFormat(type='json_object')   

        self.dspy_client = dspy.AzureOpenAI(
            api_base=api_endpoint,
            api_key=api_key,
            model=deployment,
            api_version="2024-02-01",
            max_tokens=12000,
            response_format=response_format,
        )

    def generate_form(self, prompt):
        prompt_file = open(os.getenv('PROMPT_PATH'))
        system_prompt = prompt_file.read()
        prompt_file.close()

        dspy.configure(lm=self.dspy_client)
        signature = dspy.ChainOfThought(ProduceLabelForm)
        prediction = signature(specification=system_prompt, text=prompt)

        # print(prediction)
        return prediction.form
