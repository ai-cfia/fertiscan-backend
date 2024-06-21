import os
from dotenv import load_dotenv
from auth import Token, create_label_id
from werkzeug.utils import secure_filename
from backend import OCR, GPT, LabelStorage
from flask import Flask, request, render_template, jsonify
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

# Creating a dictionary to hold the sessions
sessions = {}

@app.route('/')
def main_page():
    return render_template('index.html')

@app.route('/new_label', methods=['POST'])
def new_label():
    auth_header = request.headers.get("Authorization")
    print(auth_header)
    try:
        Token(auth_header)
        return "Succes", 200
    except KeyError:
        return jsonify({
            "label_id": create_label_id()
        })
    except:   # noqa: E722
        return "Unknown user", 404

# Example request
# curl -X POST http://localhost:5000/upload \
#     -H "Authorization: Basic <your_encoded_credentials>" \
#     -F "image=@/path/to/image1.jpg"
@app.route('/upload', methods=['POST'])
def upload_images():
    if 'image' not in request.files:
        return "No file part", 400
    
    file = request.files['image']
    if file.filename == '':
        return "No selected image", 400
    
    # The authorization scheme is still unsure.
    #
    # Current format: user_id:session_id
    # Initialize a token instance from the request authorization header
    auth_header = request.headers.get("Authorization")
    token = Token(auth_header) if request.authorization else Token()

    # Initialize storage if it does not exist for this user and label
    if token not in sessions:
        sessions[token] = LabelStorage()
    
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Add image to document storage
        sessions[token].add_image(file_path)
        
        return "File uploaded successfully", 200

@app.route('/analyze', methods=['GET'])
def analyze_document():
    # The authorization scheme is still unsure.
    #
    # Current format: user_id:session_id
    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Authentication
    auth_header = request.headers.get("Authorization")
    token = Token(auth_header) if request.authorization else Token()

    # For simplicity, only analyze the first label in the session
    label = sessions[token]

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
        mimetype="application/json"
    )

if __name__ == "__main__":
    app.run(debug=True)
