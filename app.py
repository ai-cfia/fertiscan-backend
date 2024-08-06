import os
import logging
import uuid

from http import HTTPStatus
from dotenv import load_dotenv
from flask_httpauth import HTTPBasicAuth
from azure.core.exceptions import HttpResponseError
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify
from flask_cors import CORS
from flasgger import Swagger, swag_from
from pipeline import OCR, GPT, LabelStorage, analyze

# Load environment variables
load_dotenv()

# Set up logging
log_file_path = './logs/app.log'
if not os.path.exists(os.path.dirname(log_file_path)):
    os.mkdir(os.path.dirname(log_file_path))

logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    force=True,
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

# Swagger UI
swagger = Swagger(app, template_file='docs/swagger/template.yaml')
auth = HTTPBasicAuth()

# Configuration for Azure Form Recognizer
API_ENDPOINT = os.getenv('AZURE_API_ENDPOINT')
API_KEY = os.getenv('AZURE_API_KEY')
ocr = OCR(api_endpoint=API_ENDPOINT, api_key=API_KEY)

# Configuration for OpenAI GPT-4
OPENAI_API_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
OPENAI_API_KEY = os.getenv('AZURE_OPENAI_KEY')
OPENAI_API_DEPLOYMENT = os.getenv('AZURE_OPENAI_DEPLOYMENT')
gpt = GPT(api_endpoint=OPENAI_API_ENDPOINT, api_key=OPENAI_API_KEY, deployment_id=OPENAI_API_DEPLOYMENT)

@app.route('/health', methods=['GET'])
@swag_from('docs/swagger/ping.yaml')
def ping():
    return jsonify({"message": "Service is alive"}), 200

@auth.verify_password
def verify_password(user_id, password):
    return user_id

@app.route('/forms', methods=['POST'])
@auth.login_required
@swag_from('docs/swagger/create_form.yaml')
def create_form():
    form_id = uuid.uuid4()
    return jsonify({"message": "Form created successfully", "form_id": form_id}), HTTPStatus.CREATED

@app.route('/forms/<form_id>', methods=['PUT'])
@auth.login_required
@swag_from('docs/swagger/update_form.yaml')
def update_form(form_id):
    return jsonify(error="Not yet implemented!"), HTTPStatus.SERVICE_UNAVAILABLE

@app.route('/forms/<form_id>', methods=['DELETE'])
@auth.login_required
@swag_from('docs/swagger/discard_form.yaml')
def discard_form(form_id):
    return jsonify(error="Not yet implemented!"), HTTPStatus.SERVICE_UNAVAILABLE

@app.route('/forms/<form_id>', methods=['GET'])
@auth.login_required
@swag_from('docs/swagger/get_form.yaml')
def get_form(form_id):
    return jsonify(error="Not yet implemented!"), HTTPStatus.SERVICE_UNAVAILABLE

@app.route('/analyze', methods=['POST'])
@swag_from('docs/swagger/analyze_document.yaml')
def analyze_document():
    try:
        files = request.files.getlist('images')
        
        if not files:
            raise ValueError("No files provided for analysis")

        # Initialize the storage for the user
        label_storage = LabelStorage()

        for file in files:
            if file:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                label_storage.add_image(file_path)

        form = analyze(label_storage, ocr, gpt)

        return app.response_class(
            response=form.model_dump_json(indent=2),
            status=HTTPStatus.OK,
            mimetype="application/json"
        )
    except ValueError as err:
        logger.error(f"document: {err}")
        return jsonify(error=str(err)), HTTPStatus.BAD_REQUEST
    except HttpResponseError as err:
        logger.error(f"azure: {err.message}")
        return jsonify(error=err.message), err.status_code
    except Exception as err:
        logger.error(err)
        return jsonify(error=str(err)), HTTPStatus.INTERNAL_SERVER_ERROR

@app.errorhandler(404)
def not_found(error): # pragma: no cover
    return jsonify(error="Not Found"), HTTPStatus.NOT_FOUND

@app.errorhandler(500)
def internal_error(error): # pragma: no cover
    return jsonify(error=str(error)), HTTPStatus.INTERNAL_SERVER_ERROR

if __name__ == "__main__":
    # CORS configuration limited to the frontend URL
    cors = CORS(app, resources={"*", FRONTEND_URL})
    app.config['CORS_HEADERS'] = 'Content-Type'

    app.run(host='0.0.0.0', debug=True)
