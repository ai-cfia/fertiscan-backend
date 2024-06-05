from .document_storage import DocumentStorage  # noqa: F401
from .ocr import OCR  # noqa: F401
from .gpt import GPT  # noqa: F401
import requests
          
def curl_file(url:str, path: str):
    img_data = requests.get(url).content
    with open(path, 'wb') as handler:
        handler.write(img_data)  

def save_text_to_file(text: str, output_path: str):
    with open(output_path, 'w') as output_file:
        output_file.write(text)

def save_image_to_file(image_bytes: bytes, output_path: str):
    with open(output_path, 'wb') as output_file:
        output_file.write(image_bytes)