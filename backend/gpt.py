import os
import dspy
from openai import AzureOpenAI
from openai.types.chat.completion_create_params import ResponseFormat

MODELS_WITH_RESPONSE_FORMAT = ["ailab-llm"]

class CheckCitationFaithfulness(dspy.Signature):
    """Verify that the text is based on the provided context."""

    context = dspy.InputField(desc="facts here are assumed to be true")
    text = dspy.InputField()
    faithfulness = dspy.OutputField(desc="True/False indicating if text is faithful to context")

class ProduceLabelForm:
    """Put the text of a document into multiple keyed fields."""
    
    context = dspy.InputField(desc="You are provided with text extracted from an image.")
    text = dspy.InputField()
    form = dspy.OutputField(desc="JSON with all fields occupied. If there's no data for a field set it to null.")

class GPT:
    def __init__(self, api_endpoint, api_key, deployment="ailab-gpt-35-turbo-16k"):
        if not api_endpoint or not api_key:
            raise ValueError("API endpoint and key are required to instantiate the GPT class.")
        
        # self.client = dspy.AzureOpenAI(
        #     api_base=api_endpoint,
        #     api_key=api_key,
        #     model=deployment,
        #     api_version="2024-02-01",
        # )

        self.model = deployment
        self.client = AzureOpenAI(
            api_key = api_key,  
            azure_endpoint = api_endpoint,  # Your Azure OpenAI resource's endpoint value.
            api_version = "2024-02-01",
        )

    def generate_form(self, prompt):
        prompt_file = open(os.getenv('PROMPT_PATH'))
        system_prompt = prompt_file.read()
        prompt_file.close()

        response_format = None
        if self.model in MODELS_WITH_RESPONSE_FORMAT:
            response_format = ResponseFormat(type='json_object')

        # output = dspy.ChainOfThought(Classify)
        # prediction = output(context=system_prompt, text=prompt)

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
