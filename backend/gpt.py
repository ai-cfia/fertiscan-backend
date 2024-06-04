import os
from openai import AzureOpenAI

class GPT:
    def __init__(self, api_endpoint, api_key, model="gpt-4"):
        if not api_endpoint or not api_key:
            raise ValueError("API endpoint and key are required to instantiate the GPT class.")
        
        self.model = model
        self.client = AzureOpenAI(
            api_key = api_key,  
            azure_endpoint = api_endpoint,  # Your Azure OpenAI resource's endpoint value.
            api_version = "2024-02-01",
        )

    def generate_form(self, prompt):
        prompt_file = open(os.getenv('PROMPT_PATH'))
        setup_prompt = prompt_file.read()
        prompt_file.close()
        response = self.client.chat.completions.create(
            model=self.model, # model = "deployment_name".
            messages=[
                {"role": "system", "content": setup_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
