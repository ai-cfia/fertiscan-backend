import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from backend import DocumentStorage, OCR, LanguageModel
from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
from threading import Thread
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
cors = CORS(app,resources={"*","*"}) 
app.config['CORS_HEADERS'] = 'Content-Type'
# Configuration for Azure Form Recognizer
API_ENDPOINT = os.getenv('AZURE_API_ENDPOINT')
API_KEY = os.getenv('AZURE_API_KEY')
ocr = OCR(api_endpoint=API_ENDPOINT, api_key=API_KEY)

# Configuration for OpenAI GPT-4
OPENAI_API_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
OPENAI_API_KEY = os.getenv('AZURE_OPENAI_KEY')
language_model = LanguageModel(api_endpoint=OPENAI_API_ENDPOINT, api_key=OPENAI_API_KEY)

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
        
        
        global SHOULD_GET_DATA 
        SHOULD_GET_DATA = False
        global data 
        data = ""
        
        return "File uploaded successfully", 200



def get_data(document):
    
    global SHOULD_GET_DATA
    SHOULD_GET_DATA = True

    # For simplicity, only analyze the first document
    result = ocr.extract_text(document=document)
    
    # Generate form from extracted text
    dict = result.to_dict()
    # dict.pop('documents')
    # dict.pop('pages')
    # dict.pop('styles')
    # dict.pop('tables')
    # dict.pop('paragraphs')
    # form = language_model.generate_form(json.dumps(dict))
    
    global data
    data = language_model.generate_form(dict['content'])

@app.route('/analyze', methods=['GET'])
def analyze_document():
    
    document = document_storage.get_document()
    if not document:
        return "No documents to analyze", 400
    
    
    
    print(f"data from route pov : {data}")
    if data == "":
        if not SHOULD_GET_DATA :
            Thread(target=lambda x=document: get_data(x)).start()

        response = {
            "Retry-after":10,
        }
        return jsonify(response)
    
    else:
        return app.response_class(
            response=data,
            status=200,
            mimetype='application/json'
        )
    
    
    # return jsonify(form), 200

if __name__ == "__main__":
    app.run(debug=True)
