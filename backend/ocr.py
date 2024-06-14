from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult, ContentFormat, AnalyzeDocumentRequest
from azure.core.credentials import AzureKeyCredential

class OCR:
    def __init__(self, api_endpoint, api_key):
        if not api_endpoint or not api_key:
            raise ValueError("API endpoint and key are required to instantiate the OCR class.")
        
        self.client = DocumentIntelligenceClient(
            endpoint=api_endpoint,
            credential=AzureKeyCredential(api_key)
        )

    def extract_text(self, document: bytes) -> AnalyzeResult:
        poller = self.client.begin_analyze_document(
            model_id="prebuilt-layout",
            analyze_request=AnalyzeDocumentRequest(bytes_source=document),
            output_content_format=ContentFormat.MARKDOWN
        )
        result = poller.result()
        return result
