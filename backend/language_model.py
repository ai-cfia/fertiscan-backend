# fertiscan/llm/language_model.py

from openai import AzureOpenAI

prompt_file = open('./prompt.txt')
SETUP_PROMPT = prompt_file.read()
prompt_file.close()

class LanguageModel:
    def __init__(self, api_endpoint, api_key):
        if not api_endpoint or not api_key:
            raise ValueError("API endpoint and key are required to instantiate the LanguageModel class.")
        
        self.client = AzureOpenAI(
            api_key = api_key,  
            azure_endpoint = api_endpoint,  # Your Azure OpenAI resource's endpoint value.
            api_version = "2024-02-01",
        )

    def generate_form(self, prompt):
        response = self.client.chat.completions.create(
            model="gpt-4", # model = "deployment_name".
            messages=[
                {"role": "system", "content": SETUP_PROMPT},
                {"role": "system", "content": prompt},
            ]
        )
        return response.choices[0].message.content
