import asyncio
import logging
import os
import traceback

from http import HTTPStatus
from dotenv import load_dotenv
from azure.core.exceptions import HttpResponseError
from datastore import ContainerClient, get_user, new_user
from datastore.db import connect_db
from datastore.db.queries.user import is_a_user_id
from datastore.fertiscan import register_analysis, update_inspection
from flasgger import Swagger, swag_from
from flask import Flask, jsonify, request
from flask_cors import cross_origin
from flask_httpauth import HTTPBasicAuth
from pipeline import GPT, OCR, LabelStorage, analyze
from werkzeug.utils import secure_filename

# Load environment variables
load_dotenv()

# fertiscan storage config vars
FERTISCAN_SCHEMA = os.getenv("FERTISCAN_SCHEMA", "fertiscan_0.0.8")
FERTISCAN_DB_URL = os.getenv("FERTISCAN_DB_URL")
FERTISCAN_STORAGE_URL = os.getenv("FERTISCAN_STORAGE_URL")

# Set up logging
log_dir = os.path.join(".", "logs")
log_file_path = os.path.join(log_dir, "app.log")

# Create the directory if it doesn't exist
os.makedirs(log_dir, exist_ok=True)

# Set up logging configuration
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    force=True,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Ensure the directory for uploaded images exists
UPLOAD_FOLDER = os.getenv("UPLOAD_PATH", "uploads")
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
FRONTEND_URL = os.getenv("FRONTEND_URL")

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Swagger UI
swagger = Swagger(app, template_file="docs/swagger/template.yaml")
auth = HTTPBasicAuth()

# Configuration for Azure Form Recognizer
API_ENDPOINT = os.getenv("AZURE_API_ENDPOINT")
API_KEY = os.getenv("AZURE_API_KEY")
ocr = OCR(api_endpoint=API_ENDPOINT, api_key=API_KEY)

# Configuration for OpenAI GPT-4
OPENAI_API_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
OPENAI_API_KEY = os.getenv("AZURE_OPENAI_KEY")
OPENAI_API_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
gpt = GPT(
    api_endpoint=OPENAI_API_ENDPOINT,
    api_key=OPENAI_API_KEY,
    deployment_id=OPENAI_API_DEPLOYMENT,
)


@app.route("/health", methods=["GET"])
@swag_from("docs/swagger/health.yaml")
def ping():
    return jsonify({"message": "Service is alive"}), 200


@app.route("/login", methods=["POST"])
@cross_origin(origins='*')
@swag_from("docs/swagger/login.yaml")
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    return verify_password(username, password)


@app.route("/signup", methods=["POST"])
@cross_origin(origins='*')
@swag_from("docs/swagger/signup.yaml")
def signup(): # pragma: no cover
    username = request.form.get("username")
    _ = request.form.get("password")

    try:
        with connect_db(FERTISCAN_DB_URL, FERTISCAN_SCHEMA) as conn:
            with conn.cursor() as cursor:
                user = asyncio.run(new_user(cursor, username, FERTISCAN_STORAGE_URL))
            conn.commit()
        return jsonify({"user_id": user.get_id()}), 201
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        logger.error("Traceback: " + traceback.format_exc())
        return jsonify({"message": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR


@auth.verify_password
def verify_password(username, password):
    if username is None:
        return jsonify(
            error="Missing email address!",
            message="The request is missing the 'email' parameter. Please provide a valid email address to proceed.",
        ), HTTPStatus.BAD_REQUEST

    try:
        with connect_db(FERTISCAN_DB_URL, FERTISCAN_SCHEMA) as conn:
            with conn.cursor() as cursor:
                # Check if the user exists in the database
                try:
                    is_user_id = is_a_user_id(cursor, username)
                except Exception as e:
                    return jsonify(
                        error="Authentication error!",
                        message=str(e),
                    ), HTTPStatus.UNAUTHORIZED

        if is_user_id:
            return jsonify(
                error="Unknown user!",
                message="The email provided does not match with any known user.",
            ), HTTPStatus.UNAUTHORIZED

        return username
    except Exception as err:
        logger.error(f"Error occurred: {err}")
        logger.error("Traceback: " + traceback.format_exc())
        return jsonify(error="Internal server error!"), HTTPStatus.INTERNAL_SERVER_ERROR


@app.route("/inspections", methods=["POST"])
@auth.login_required
@cross_origin(origins=[FRONTEND_URL, 'localhost'])
@swag_from("docs/swagger/create_inspection.yaml")
def create_form():  # pragma: no cover
    try:
        with connect_db(FERTISCAN_DB_URL, FERTISCAN_SCHEMA) as conn:
            with conn.cursor() as cursor:
                # Sample userId from the database
                username = auth.username()
                logger.info(f"Fetching user ID for username: {username}")
                db_user = asyncio.run(get_user(cursor, username))
                user_id = db_user.id

                container_client = ContainerClient.from_connection_string(
                    FERTISCAN_STORAGE_URL, container_name=f"user-{user_id}"
                )

                # Get JSON form from the request
                form = request.json
                if form is None:
                    logger.warning("Missing form in request")
                    return jsonify(
                        error="Missing fertiliser form!"
                    ), HTTPStatus.BAD_REQUEST

                files = request.files.getlist("images")

                # Collect files in a list
                images = []
                for file in files:
                    if file:
                        logger.info(f"Reading file: {file.filename}")
                        images.append(file.stream.read())

                logger.info(f"Registering analysis for user_id: {user_id}")
                inspection = asyncio.run(
                    register_analysis(
                        cursor=cursor,
                        container_client=container_client,
                        user_id=user_id,
                        analysis_dict=form,
                        hashed_pictures=images,
                    )
                )
                conn.commit()

                logger.info(
                    f"Inspection created successfully with id: {inspection['inspection_id']}"
                )
                return jsonify(inspection), HTTPStatus.CREATED

    except Exception as err:
        logger.error(f"Error occurred: {err}")
        logger.error("Traceback: " + traceback.format_exc())
        return jsonify(error=str(err)), HTTPStatus.INTERNAL_SERVER_ERROR


@app.route("/inspections/<inspection_id>", methods=["PUT"])
@auth.login_required
@swag_from("docs/swagger/update_inspection.yaml")
def update_form(inspection_id):  # pragma: no cover
    try:
        with connect_db(FERTISCAN_DB_URL, FERTISCAN_SCHEMA) as conn:
            with conn.cursor() as cursor:
                # Sample userId from the database
                username = auth.username()
                logger.info(f"Fetching user ID for username: {username}")
                db_user = asyncio.run(get_user(cursor, username))
                
                # Get JSON form from the request
                inspection = request.json
                if inspection is None:
                    return jsonify(
                        error="Missing fertiliser form!"
                    ), HTTPStatus.BAD_REQUEST

                inspection = asyncio.run(
                    update_inspection(
                        cursor,
                        inspection_id,
                        db_user.id,
                        inspection,  # Adjust to match the schema if necessary
                    )
                )
                conn.commit()
                return inspection.model_dump(), HTTPStatus.OK
    except Exception as err:
        logger.error(f"Error occurred: {err}")
        logger.error("Traceback: " + traceback.format_exc())
        return jsonify(error=str(err)), HTTPStatus.INTERNAL_SERVER_ERROR


@app.route("/inspections/<form_id>", methods=["DELETE"])
@auth.login_required
# @swag_from("docs/swagger/discard_inspection.yaml")
def discard_form(form_id):   # pragma: no cover
    return jsonify(error="Not yet implemented!"), HTTPStatus.SERVICE_UNAVAILABLE


@app.route("/inspections", methods=["GET"])
@auth.login_required
@cross_origin(origins=[FRONTEND_URL, 'localhost'])
@swag_from("docs/swagger/search_inspection.yaml")
def search():   # pragma: no cover
    return jsonify(error="Not yet implemented!"), HTTPStatus.SERVICE_UNAVAILABLE
    # try:
    #     # Database cursor
    #     cursor = CONN.cursor()

    #     # The search query used to find the label.
    #     user_id = request.args.get('user_id')
    #     label_id = request.args.get('label_id')
    #     query = SearchQuery(user_id=user_id, label_id=label_id)

    #     # TO-DO Send that search query to the datastore
    #     inspections = inspection.get_all_user_inspection(cursor, query.user_id)
    #     return jsonify(inspections), HTTPStatus.OK
    # except Exception as err:
    #     CONN.rollback()
    # logger.error(f"Error occurred: {err}")
    # logger.error("Traceback: " + traceback.format_exc())
    #     return jsonify(error=str(err)), HTTPStatus.INTERNAL_SERVER_ERROR


@app.route("/analyze", methods=["POST"])
@swag_from("docs/swagger/analyze_document.yaml")
def analyze_document():
    try:
        files = request.files.getlist("images")

        if not files:
            raise ValueError("No files provided for analysis")

        # Initialize the storage for the user
        label_storage = LabelStorage()

        for file in files:
            if file:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(file_path)
                label_storage.add_image(file_path)

        inspection = analyze(label_storage, ocr, gpt)

        return app.response_class(
            response=inspection.model_dump_json(indent=2),
            status=HTTPStatus.OK,
            mimetype="application/json",
        )
    except ValueError as err:
        logger.error(f"images: {err}")
        return jsonify(error=str(err)), HTTPStatus.BAD_REQUEST
    except HttpResponseError as err:
        logger.error(f"azure: {err.message}")
        return jsonify(error=err.message), err.status_code
    except Exception as err:
        logger.error(err)
        return jsonify(error=str(err)), HTTPStatus.INTERNAL_SERVER_ERROR


@app.errorhandler(404)
def not_found(error):  # pragma: no cover
    return jsonify(error="Not Found"), HTTPStatus.NOT_FOUND


@app.errorhandler(500)
def internal_error(error):  # pragma: no cover
    return jsonify(error=str(error)), HTTPStatus.INTERNAL_SERVER_ERROR


if __name__ == "__main__":
    app.run(host='localhost', debug=True)
