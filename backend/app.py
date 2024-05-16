# import libraries
import os
import json
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient

load_dotenv()

# set `<your-endpoint>` and `<your-key>` variables with the values from the Azure portal
endpoint = os.getenv('API_ENDPOINT')
key = os.getenv('API_KEY')

def format_polygon(polygon):
    if not polygon:
        return "N/A"
    return ", ".join(["[{}, {}]".format(p.x, p.y) for p in polygon])

def analyze_layout():
    # sample document
    form = open('./samples/image.png', mode='rb')
    formBytes = form.read()
    form.close()

    document_analysis_client = DocumentAnalysisClient(
        endpoint=endpoint, credential=AzureKeyCredential(key)
    )

    poller = document_analysis_client.begin_analyze_document(
            "prebuilt-layout", formBytes)
    result = poller.result()

    
    # Serialize the result variable to JSON and save it to a file
    with open('./samples/image.json', 'w') as json_file:
        dict = result.to_dict()
        dict.pop('documents')
        dict.pop('pages')
        dict.pop('styles')
        dict.pop('paragraphs')
        json.dump(dict, json_file, indent=4)

if __name__ == "__main__":
    analyze_layout()
