# fertiscan/llm/language_model.py

import openai

class LanguageModel:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("API key is required to instantiate the LanguageModel class.")
        
        openai.api_key = api_key

    def generate_form(self, prompt):
        response = openai.Completion.create(
            engine="gpt-4",
            prompt=prompt,
            max_tokens=1500,  # Adjust as needed
            n=1,
            stop=None,
            temperature=0.  # Adjust as needed
        )
        return response.choices[0].text.strip()