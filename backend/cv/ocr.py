# fertiscan/cv/ocr.py

from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient, AnalyzeResult

class OCR:
    def __init__(self, api_endpoint, api_key):
        if not api_endpoint or not api_key:
            raise ValueError("API endpoint and key are required to instantiate the OCR class.")
        
        self.client = DocumentAnalysisClient(
            endpoint=api_endpoint,
            credential=AzureKeyCredential(api_key)
        )

    def extract_text(self, document) -> AnalyzeResult:
        poller = self.client.begin_analyze_document(
            model="prebuilt-layout", document=document, outputContentFormat='markdown'
        )
        result = poller.result()
        return result
