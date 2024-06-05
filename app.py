import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from backend import DocumentStorage, OCR, GPT
from flask import Flask, request, render_template
from flask_cors import CORS

# Load environment variables
load_dotenv()

# Ensure the directory for uploaded images exists
UPLOAD_FOLDER = os.getenv('UPLOAD_PATH')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
FRONTEND_URL = os.getenv('FRONTEND_URL')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# CORS configuration limited to the frontend URL
cors = CORS(app,resources={"*",FRONTEND_URL}) 
app.config['CORS_HEADERS'] = 'Content-Type'
# Configuration for Azure Form Recognizer
API_ENDPOINT = os.getenv('AZURE_API_ENDPOINT')
API_KEY = os.getenv('AZURE_API_KEY')
ocr = OCR(api_endpoint=API_ENDPOINT, api_key=API_KEY)

# Configuration for OpenAI GPT-4
OPENAI_API_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
OPENAI_API_KEY = os.getenv('AZURE_OPENAI_KEY')
language_model = GPT(api_endpoint=OPENAI_API_ENDPOINT, api_key=OPENAI_API_KEY)

# Document storage
document_storage = DocumentStorage()

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
        document_storage.add_image(file_path)
        
        return "File uploaded successfully", 200

@app.route('/analyze', methods=['GET'])
def analyze_document():
    document = document_storage.get_document()
    if not document:
        return "No documents to analyze", 400
    
    # For simplicity, only analyze the first document
    result = ocr.extract_text(document=document)

    # Generate form from extracted text
    form = language_model.generate_form(result.content)
    
    document_storage.clear()

    return app.response_class(
        response=form,
        status=200,
        mimetype='application/json'
    )

if __name__ == "__main__":
    app.run(debug=True)
