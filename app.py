import logging
import os
import traceback
from werkzeug.utils import secure_filename
from http import HTTPStatus

from azure.core.exceptions import HttpResponseError
from datastore import ContainerClient, fertiscan, get_user, new_user
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pipeline import GPT, OCR, LabelStorage, analyze
from psycopg_pool import ConnectionPool
from backend.connection_manager import ConnectionManager

# Load environment variables
load_dotenv()

# fertiscan storage config vars
FERTISCAN_SCHEMA = os.getenv("FERTISCAN_SCHEMA")
FERTISCAN_DB_URL = os.getenv("FERTISCAN_DB_URL")
FERTISCAN_STORAGE_URL = os.getenv("FERTISCAN_STORAGE_URL")

# Set up logging
log_dir = os.path.join(".", "logs")
log_filename = os.getenv("LOG_FILENAME")
log_file = os.path.join(log_dir, log_filename) if log_filename else None

# Create the directory if it doesn't exist
os.makedirs(log_dir, exist_ok=True)

# Set up logging configuration
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    force=True,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Ensure the directory for uploaded images exists
UPLOAD_FOLDER = os.getenv("UPLOAD_PATH", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
FRONTEND_URL = os.getenv("FRONTEND_URL", "*")

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

auth = HTTPBasic()

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

# Set up the database connection pool with default values and the manager
pool = ConnectionPool(
    conninfo=FERTISCAN_DB_URL,
    open=True,
    kwargs={"options": f"-c search_path={FERTISCAN_SCHEMA},public"},
)
connection_manager = ConnectionManager(app, pool)


@app.get("/")
async def main_page():
    return {"message": "Welcome to the FastAPI application."}


@app.get("/health")
async def ping():
    return {"message": "Service is alive"}


@app.post("/login")
async def login(credentials: HTTPBasicCredentials = Depends(auth)):
    username = credentials.username
    password = "password1"  # Change this logic as per your requirements

    return await verify_password(username, password)


@app.post("/signup")
async def signup(credentials: HTTPBasicCredentials = Depends(auth)):
    username = credentials.username

    if not username:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Missing email address!")

    try:
        async with connection_manager as manager:
            async with manager.get_cursor() as cursor:
                logger.info(f"Creating user: {username}")
                user = await new_user(cursor, username, FERTISCAN_STORAGE_URL)
            manager.commit()
        return {"user_id": user.get_id()}

    except Exception as e:
        logger.error(f"Error occurred: {e}")
        logger.error("Traceback: " + traceback.format_exc())
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Failed to create user!")


async def verify_password(username: str, password: str):
    if not username:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Missing email address!")

    try:
        async with connection_manager as manager:
            async with manager.get_cursor() as cursor:
                try:
                    user = await get_user(cursor, username)
                except Exception as e:
                    logger.error(f"Error occurred: {e}")
                    logger.error("Traceback: " + traceback.format_exc())
                    raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Authentication error!")

        if user is None:
            raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Unknown user!")

        return {"user_id": user.get_id()}

    except Exception as err:
        logger.error(f"Error occurred: {err}")
        logger.error("Traceback: " + traceback.format_exc())
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Internal server error!")


@app.post("/inspections")
async def create_inspection(form: dict, files: list[UploadFile] = File(...), credentials: HTTPBasicCredentials = Depends(auth)):
    try:
        async with connection_manager as manager:
            async with manager.get_cursor() as cursor:
                username = credentials.username
                logger.info(f"Fetching user ID for username: {username}")
                db_user = await get_user(cursor, username)
                user_id = db_user.id

                container_client = ContainerClient.from_connection_string(
                    FERTISCAN_STORAGE_URL, container_name=f"user-{user_id}"
                )

                if form is None:
                    raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Missing fertiliser form!")

                # Collect files in a list
                images = [await file.read() for file in files if file]

                logger.info(f"Registering analysis for user_id: {user_id}")
                inspection = await fertiscan.register_analysis(
                    cursor=cursor,
                    container_client=container_client,
                    user_id=user_id,
                    analysis_dict=form,
                    hashed_pictures=images,
                )

                logger.info(f"Inspection created successfully with id: {inspection['inspection_id']}")
                return inspection

    except Exception as err:
        logger.error(f"Error occurred: {err}")
        logger.error("Traceback: " + traceback.format_exc())
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(err))


@app.put("/inspections/{inspection_id}")
async def update_inspection(inspection_id: str, inspection: dict, credentials: HTTPBasicCredentials = Depends(auth)):
    try:
        async with connection_manager as manager:
            async with manager.get_cursor() as cursor:
                username = credentials.username
                logger.info(f"Fetching user ID for username: {username}")
                db_user = await get_user(cursor, username)

                inspection = await fertiscan.update_inspection(
                    cursor, inspection_id, db_user.id, inspection
                )
                return inspection.model_dump_json(indent=2)

    except Exception as err:
        logger.error(f"Error occurred: {err}")
        logger.error("Traceback: " + traceback.format_exc())
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(err))


@app.delete("/inspections/{inspection_id}")
async def discard_inspection(inspection_id: str, credentials: HTTPBasicCredentials = Depends(auth)):
    raise HTTPException(status_code=HTTPStatus.SERVICE_UNAVAILABLE, detail="Not yet implemented!")


@app.get("/inspections")
async def get_inspections(credentials: HTTPBasicCredentials = Depends(auth)):
    try:
        async with connection_manager as manager:
            async with manager.get_cursor() as cursor:
                username = credentials.username
                logger.info(f"Fetching user ID for username: {username}")
                db_user = await get_user(cursor, username)

                inspections = await fertiscan.get_user_analysis_by_verified(cursor, db_user.id, False)

                return inspections

    except Exception as err:
        logger.error(f"Error occurred: {err}")
        logger.error("Traceback: " + traceback.format_exc())
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(err))


@app.get("/inspections/{inspection_id}")
async def get_inspection_by_id(inspection_id: str, credentials: HTTPBasicCredentials = Depends(auth)):
    try:
        async with connection_manager as manager:
            async with manager.get_cursor() as cursor:
                username = credentials.username
                logger.info(f"Fetching user ID for username: {username}")
                db_user = await get_user(cursor, username)

                inspection = await fertiscan.get_full_inspection_json(
                    cursor, inspection_id, db_user.get_id()
                )

                return inspection

    except Exception as err:
        logger.error(f"Error occurred: {err}")
        logger.error("Traceback: " + traceback.format_exc())
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(err))


@app.post("/analyze")
async def analyze_document(files: list[UploadFile] = File(...)):
    try:
        if not files:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="No files provided for analysis")

        # Initialize the storage for the user
        label_storage = LabelStorage()

        for file in files:
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            with open(file_path, "wb") as f:
                f.write(await file.read())
            label_storage.add_image(file_path)

        inspection = analyze(label_storage, ocr, gpt)

        return inspection.model_dump_json(indent=2)

    except ValueError as err:
        logger.error(f"images: {err}")
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(err))
    except HttpResponseError as err:
        logger.error(f"azure: {err.message}")
        raise HTTPException(status_code=err.status_code, detail=err.message)
    except Exception as err:
        logger.error(err)
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(err))


@app.exception_handler(404)
async def not_found_handler(request, exc):
    return HTTPException(detail="Not Found", status_code=404)


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return HTTPException(detail="Not Found", status_code=500)


if __name__ == "__main__":
    # Check if the required environment variables are set
    if FERTISCAN_DB_URL is None:
        raise ValueError("FERTISCAN_DB_URL is not set")
    if FERTISCAN_SCHEMA is None:
        raise ValueError("FERTISCAN_SCHEMA is not set")
    if FERTISCAN_STORAGE_URL is None:
        raise ValueError("FERTISCAN_STORAGE_URL is not set")

    app.run(app, host="0.0.0.0", port=8000, log_level="info")

