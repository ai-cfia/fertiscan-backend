from http import HTTPStatus
from typing import Annotated

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse
from pipeline import GPT, OCR, FertilizerInspection

from app.config import lifespan
from app.connection_manager import ConnectionManager
from app.controllers.data_extraction import extract_data
from app.controllers.inspections import read_all
from app.controllers.users import sign_in, sign_up
from app.dependencies import (
    authenticate_user,
    fetch_user,
    get_connection_manager,
    get_gpt,
    get_ocr,
)
from app.exceptions import UserConflictError, UserNotFoundError, log_error
from app.models.inspection import InspectionData
from app.models.monitoring import HealthStatus
from app.models.users import User
from app.sanitization import custom_secure_filename

app = FastAPI(lifespan=lifespan)


@app.exception_handler(Exception)
async def global_exception_handler(_: Request, e: Exception):
    log_error(e)
    return JSONResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, content=str(e))


@app.get("/health", tags=["Monitoring"], response_model=HealthStatus)
async def health_check():
    return HealthStatus()


@app.post("/analyze", response_model=FertilizerInspection, tags=["Pipeline"])
async def analyze_document(
    ocr: OCR = Depends(get_ocr),
    gpt: GPT = Depends(get_gpt),
    files: list[UploadFile] = File(..., min_length=1),
):
    file_dict = {}
    for f in files:
        if f.size == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"File {f.filename} is empty",
            )
        file_dict[custom_secure_filename(f.filename)] = f.file

    return extract_data(file_dict, ocr, gpt)


@app.post("/signup", tags=["Users"], status_code=201, response_model=User)
async def signup(
    cm: Annotated[ConnectionManager, Depends(get_connection_manager)],
    user: User = Depends(authenticate_user),
):
    try:
        return await sign_up(cm, user)
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
