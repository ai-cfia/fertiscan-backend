from http import HTTPStatus
from typing import Annotated

from fastapi import Depends, FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.concurrency import asynccontextmanager
from fastapi.responses import JSONResponse
from pipeline import GPT, OCR
from pydantic import UUID4

from app.config import Settings, configure
from app.connection_manager import ConnectionManager
from app.controllers.data_extraction import extract_data
from app.controllers.inspections import create, read, read_all
from app.controllers.users import sign_in, sign_up
from app.dependencies import (
    authenticate_user,
    fetch_user,
    get_connection_manager,
    get_gpt,
    get_ocr,
    get_settings,
    validate_files,
)
from app.exceptions import (
    InspectionNotFoundError,
    UserConflictError,
    UserNotFoundError,
    log_error,
)
from app.models.inspections import Inspection, InspectionData
from app.models.label_data import LabelData
from app.models.monitoring import HealthStatus
from app.models.users import User
from app.sanitization import custom_secure_filename


@asynccontextmanager
async def lifespan(app: FastAPI):
    app = configure(app, get_settings())
    app.connection_manager.pool.open()
    yield
    app.connection_manager.pool.close()


app = FastAPI(lifespan=lifespan)


@app.exception_handler(Exception)
async def global_exception_handler(_: Request, e: Exception):
    log_error(e)
    return JSONResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, content=str(e))


@app.get("/health", tags=["Monitoring"], response_model=HealthStatus)
async def health_check():
    return HealthStatus()


@app.post("/analyze", response_model=LabelData, tags=["Pipeline"])
async def analyze_document(
    ocr: Annotated[OCR, Depends(get_ocr)],
    gpt: Annotated[GPT, Depends(get_gpt)],
    settings: Annotated[Settings, Depends(get_settings)],
    files: Annotated[list[UploadFile], Depends(validate_files)],
):
    file_dict = {custom_secure_filename(f.filename): f.file for f in files}
    return extract_data(file_dict, ocr, gpt, settings.upload_folder)


@app.post("/signup", tags=["Users"], status_code=201, response_model=User)
async def signup(
    cm: Annotated[ConnectionManager, Depends(get_connection_manager)],
    user: Annotated[User, Depends(authenticate_user)],
    settings: Annotated[Settings, Depends(get_settings)],
):
    try:
        return await sign_up(cm, user, settings.fertiscan_storage_url)
    except UserConflictError:
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail="User exists!")


@app.post("/login", tags=["Users"], status_code=200, response_model=User)
async def login(
    cm: Annotated[ConnectionManager, Depends(get_connection_manager)],
    user: User = Depends(authenticate_user),
):
    try:
        return await sign_in(cm, user)
    except UserNotFoundError:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid username or password"
        )


@app.get("/inspections", tags=["Inspections"], response_model=list[InspectionData])
async def get_inspections(
    cm: Annotated[ConnectionManager, Depends(get_connection_manager)],
    user: User = Depends(fetch_user),
):
    return await read_all(cm, user)


@app.get("/inspections/{id}", tags=["Inspections"], response_model=Inspection)
async def get_inspection(
    cm: Annotated[ConnectionManager, Depends(get_connection_manager)],
    user: Annotated[User, Depends(fetch_user)],
    id: UUID4,
):
    try:
        return await read(cm, user, id)
    except InspectionNotFoundError:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Inspection not found"
        )


@app.post("/inspections", tags=["Inspections"], response_model=Inspection)
async def create_inspection(
    cm: Annotated[ConnectionManager, Depends(get_connection_manager)],
    user: Annotated[User, Depends(fetch_user)],
    settings: Annotated[Settings, Depends(get_settings)],
    label_data: Annotated[LabelData, Form(...)],
    files: Annotated[list[UploadFile], Depends(validate_files)],
):
    # Note: later on, we might handle label images as their own domain
    label_images = [await f.read() for f in files]
    conn_string = settings.fertiscan_storage_url
    return await create(cm, user, label_data, label_images, conn_string)
