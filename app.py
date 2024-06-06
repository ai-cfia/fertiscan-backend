import os
from dotenv import load_dotenv
from auth import Token
from werkzeug.utils import secure_filename
from backend import OCR, GPT, LabelStorage
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

# Creating a dictionary to hold the sessions with string keys
sessions = {}

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
    
    # The authorization scheme is still unknown.
    #
    # Potential format: user_id:session_id
    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Authentication    
    token = Token()
    header = request.authorization
    if header is not None:
        token = Token(header)
    
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Init the storage if it does not exist
        if token.user_id not in sessions:
            sessions[token.user_id] = {}
            sessions[token.user_id][token.label_id] = LabelStorage()

        # Add image to label storage
        sessions[token.user_id][token.label_id].add_image(file_path)
        
        return "File uploaded successfully", 200

@app.route('/analyze', methods=['GET'])
def analyze_document():
    # The authorization scheme is still unknown.
    #
    # Potential format: user_id:session_id
    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Authentication
    token = Token()
    header = request.authorization
    if header is not None:
        token = Token(header)

    if token.user_id == '':
        return "Unknown user", 404
    
    # For simplicity, only analyze the first label in the session
    label = sessions[token.user_id][token.label_id]

    document = label.get_document()
    if not document:
        return "No documents to analyze", 400
    
    result = ocr.extract_text(document=document)

    # Generate form from extracted text
    form = language_model.generate_form(result.content)
    
    label.clear()

    return app.response_class(
        response=form,
        status=200,
        mimetype='application/json'
    )

if __name__ == "__main__":
    app.run(debug=True)
