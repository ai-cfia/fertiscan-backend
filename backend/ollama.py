import os
import ollama

class Ollama:
    def __init__(self, api_endpoint):
        if not api_endpoint:
            raise ValueError("API endpoint is required to instantiate the Ollama class.")
        
        self.api_endpoint = api_endpoint
    def generate_form(self, prompt):
        prompt_file = open(os.getenv('PROMPT_PATH'))
        setup_prompt = prompt_file.read()
        prompt_file.close()
        response = ollama.chat(
            model="llama3", # model = "deployment_name".
            messages=[
                {"role": "system", "content": setup_prompt},
                {"role": "system", "content": prompt},
            ],
            stream=False
        )
        return response['message']['content']
