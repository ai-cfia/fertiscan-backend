# fertiscan/llm/language_model.py

from openai import AzureOpenAI

class LanguageModel:
    def __init__(self, api_endpoint, api_key):
        if not api_endpoint or not api_key:
            raise ValueError("API endpoint and key are required to instantiate the LanguageModel class.")
        
        self.client = AzureOpenAI(
            api_key = api_key,  
            api_version = "2024-02-01",
            azure_endpoint = api_endpoint  # Your Azure OpenAI resource's endpoint value.
        )

    def generate_form(self, prompt):
        conversation=[{"role": "system", "content": prompt}]
        response = self.client.completions.create(
            engine="gpt-4",
            messages=conversation
            # max_tokens=1500,  # Adjust as needed
            # n=1,
            # stop=None,
            # temperature=0.7  # Adjust as needed
        )
        return response.choices[0].text.strip()
