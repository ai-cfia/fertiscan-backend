import os
from openai import AzureOpenAI

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

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
        request_params = {
            "model": self.model,  # model = "deployment_name".
            "messages": messages,
            "temperature": 0,
        }
        if self.model in MODELS_WITH_RESPONSE_FORMAT:
            request_params["response_format"] = {"type": "json_object"}
        response = self.client.chat.completions.create(**request_params)
        return response.choices[0].message.content
