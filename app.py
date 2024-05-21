# server.py

from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import os
import json
from io import BytesIO
from dotenv import load_dotenv
from backend import DocumentStore, OCR, LanguageModel

# Load environment variables
load_dotenv()

# Ensure the directory for uploaded images exists
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configuration for Azure Form Recognizer
API_ENDPOINT = os.getenv('AZURE_API_ENDPOINT')
API_KEY = os.getenv('AZURE_API_KEY')
ocr = OCR(api_endpoint=API_ENDPOINT, api_key=API_KEY)

# Configuration for OpenAI GPT-4
OPENAI_API_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
OPENAI_API_KEY = os.getenv('AZURE_OPENAI_KEY')
language_model = LanguageModel(api_endpoint=OPENAI_API_ENDPOINT, api_key=OPENAI_API_KEY)

# Document storage
document_store = DocumentStore()

@app.route('/')
def main_page():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return "No file part", 400
    
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Add image to document storage
        with open(file_path, 'rb') as f:
            document_store.add_page(f.read())
        
        return "File uploaded successfully", 200

@app.route('/analyze', methods=['GET'])
def analyze_document():
    document = document_store.get_document()
    if not document:
        return "No documents to analyze", 400
    
    # For simplicity, only analyze the first document
    result = ocr.extract_text(document=document)
    
    # Generate form from extracted text
    dict = result.to_dict()
    dict.pop('documents')
    dict.pop('pages')
    dict.pop('styles')
    dict.pop('tables')
    dict.pop('paragraphs')
    # form = language_model.generate_form(json.dumps(dict))
    form = language_model.generate_form(dict['content'])
    
    return jsonify({'form': form}), 200

if __name__ == "__main__":
    app.run(debug=True)
