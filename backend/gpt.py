import os
from openai import AzureOpenAI
from openai.types.chat.completion_create_params import ResponseFormat

# Constants
MODELS_WITH_RESPONSE_FORMAT = [
    "ailab-llm"
]  # List of models that support the response_format option

class GPT:
    def __init__(self, api_endpoint, api_key, deployment="ailab-gpt-35-turbo-16k"):
        if not api_endpoint or not api_key:
            raise ValueError(
                "API endpoint and key are required to instantiate the GPT class."
            )

        self.model = deployment
        self.client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=api_endpoint,  # Your Azure OpenAI resource's endpoint value.
            api_version="2024-02-01",
        )

    def generate_form(self, prompt):

        prompt_file = open(os.getenv("PROMPT_PATH"))
        system_prompt = prompt_file.read()
        prompt_file.close()

        response_format = None
        if self.model in MODELS_WITH_RESPONSE_FORMAT:
            response_format = ResponseFormat(type='json_object')

        response = self.client.chat.completions.create(
            model=self.model, # model = "deployment_name".
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            response_format=response_format,
            temperature=0,
        )
        return response.choices[0].message.content
