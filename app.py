import os
import json
import logging
from http import HTTPStatus
from dotenv import load_dotenv
from auth import Token
from backend.form import FertiliserForm
from azure.core.exceptions import HttpResponseError
from werkzeug.utils import secure_filename
from backend import OCR, GPT, LabelStorage, save_text_to_file
from datetime import datetime
from flask import Flask, request, render_template, jsonify
from flask_cors import CORS

# Load environment variables
load_dotenv()

# Set up logging
log_file_path = './logs/app.log'
if not os.path.exists(os.path.dirname(log_file_path)):
    os.makedirs(os.path.dirname(log_file_path))

logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure the directory for uploaded images exists
UPLOAD_FOLDER = os.getenv('UPLOAD_PATH')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
FRONTEND_URL = os.getenv('FRONTEND_URL')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# CORS configuration limited to the frontend URL
cors = CORS(app, resources={"*", FRONTEND_URL})
app.config['CORS_HEADERS'] = 'Content-Type'

# Configuration for Azure Form Recognizer
API_ENDPOINT = os.getenv('AZURE_API_ENDPOINT')
API_KEY = os.getenv('AZURE_API_KEY')
ocr = OCR(api_endpoint=API_ENDPOINT, api_key=API_KEY)

# Configuration for OpenAI GPT-4
OPENAI_API_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
OPENAI_API_KEY = os.getenv('AZURE_OPENAI_KEY')
language_model = GPT(api_endpoint=OPENAI_API_ENDPOINT, api_key=OPENAI_API_KEY)

@app.route('/')
def main_page():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_document():
    try:
        files = request.files.getlist('images')
        
        if not files:
            raise ValueError("No files provided for analysis")

        # The authorization scheme is still unsure.
        auth_header = request.headers.get("Authorization")
        Token(auth_header) if request.authorization else Token()
        
        # Initialize the storage for the user
        label_storage = LabelStorage()

        for file in files:
            if file:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                label_storage.add_image(file_path)

        document = label_storage.get_document()
        result = ocr.extract_text(document=document)

        # Logs the results from document intelligence
        now = datetime.now()
        save_text_to_file(result.content, f"./logs/{now}.md")

        # Generate form from extracted text
        prediction = language_model.generate_form(result.content)

        # Logs the results from GPT
        save_text_to_file(prediction.form, f"./logs/{now}.json")
        save_text_to_file(prediction.rationale, f"./logs/{now}.txt")

        # Check the conformity of the JSON
        form = FertiliserForm(**json.loads(prediction.form))

        # Clear the label cache
        label_storage.clear()

        # Delete the logs if there's no error
        os.remove(f"./logs/{now}.md")   
        os.remove(f"./logs/{now}.txt")     
        os.remove(f"./logs/{now}.json")

        return app.response_class(
            response=form.model_dump_json(indent=2),
            status=HTTPStatus.OK,
            mimetype="application/json"
        )
    except ValueError as err:
        logger.error(f"document: {err}")
        return jsonify(error=str(err)), HTTPStatus.BAD_REQUEST
    except HttpResponseError as err:
        logger.error(f"document_intelligence: {err.message}")
        return jsonify(error=err.message), err.status_code
    except Exception as err:
        logger.error(f"json_parse: {err}")
        return jsonify(error=str(err)), HTTPStatus.INTERNAL_SERVER_ERROR

@app.errorhandler(404)
def not_found(error):
    return jsonify(error="Not Found"), HTTPStatus.NOT_FOUND

@app.errorhandler(500)
def internal_error(error):
    return jsonify(error=str(error)), HTTPStatus.INTERNAL_SERVER_ERROR

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
