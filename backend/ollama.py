import os
from ollama import Client

class Ollama:
    def __init__(self, api_endpoint):
        if not api_endpoint:
            raise ValueError("API endpoint is required to instantiate the Ollama class.")
        self.client = Client(host=api_endpoint)
    def generate_form(self, prompt):
        prompt_file = open(os.getenv('PROMPT_PATH'))
        system_prompt = prompt_file.read()
        prompt_file.close()
        response = self.client.chat(
            model="llama3", # model = "deployment_name".
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            stream=False
        )
        return response['message']['content']
