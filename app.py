import os
import logging
import datastore.db

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

# Create a real database connection
FERTISCAN_SCHEMA = os.getenv("FERTISCAN_SCHEMA", "fertiscan_0.0.8")
FERTISCAN_DB_URL = os.getenv("FERTISCAN_DB_URL")
conn = datastore.db.connect_db(conn_str=FERTISCAN_DB_URL, schema=FERTISCAN_SCHEMA)

# Set the connection string as an environment variable
connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

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
gpt = GPT(api_endpoint=OPENAI_API_ENDPOINT, api_key=OPENAI_API_KEY, deployment=OPENAI_API_DEPLOYMENT)

@app.route('/ping', methods=['GET'])
@swag_from('docs/swagger/ping.yaml')
def ping():
    return jsonify({"message": "Service is alive"}), 200

@auth.verify_password
def verify_password(user_id, password):
    return user_id

@app.route('/forms', methods=['POST'])
@auth.login_required
@swag_from('docs/swagger/create_form.yaml')
async def create_form():
    # Database cursor
    cursor = conn.cursor()

    username = auth.username()
    if username is None:
        return jsonify(error="Missing username!"), HTTPStatus.BAD_REQUEST
    
    # Sample userId from the database
    user = await datastore.get_user(cursor, username)
    user_id = user.id
    container_client = datastore.ContainerClient.from_connection_string(
        connection_string, container_name=f"user-{user_id}"
    )

    # Get JSON form from the request
    form = request.json
    if form is None:
        return jsonify(error="Missing fertiliser form!"), HTTPStatus.BAD_REQUEST
    
    files = request.files.getlist('images')

    # Initialize the storage for the user
    label_storage = LabelStorage()

    for file in files:
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            label_storage.add_image(file_path)
    
    image = label_storage.get_document(format='png')

    analysis = await datastore.register_analysis(
        cursor=cursor,
        container_client=container_client,
        analysis_dict=form,
        image=image
    )
    return jsonify({"message": "Form created successfully", "form_id": analysis["analysis_id"]}), HTTPStatus.CREATED

@app.route('/forms/<form_id>', methods=['PUT'])
@auth.login_required
@swag_from('docs/swagger/update_form.yaml')
def update_form(form_id):
    form = request.json
    if form is None:
        return jsonify(error="Missing fertiliser form!"), HTTPStatus.BAD_REQUEST
    
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
