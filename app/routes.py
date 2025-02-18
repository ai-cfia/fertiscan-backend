from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from pipeline import GPT, OCR
from psycopg_pool import ConnectionPool

from app.config import Settings
from app.controllers.data_extraction import extract_data
from app.controllers.inspections import (
    create_inspection,
    delete_inspection,
    get_pictures,
    read_all_inspections,
    read_inspection,
    update_inspection,
)
from app.controllers.users import sign_up
from app.dependencies import (
    authenticate_user,
    fetch_user,
    get_connection_pool,
    get_gpt,
    get_ocr,
    get_settings,
    validate_files,
)
from app.exceptions import InspectionNotFoundError, UserConflictError
from app.models.inspections import (
    DeletedInspection,
    InspectionData,
    InspectionResponse,
    InspectionUpdate,
)
from app.models.label_data import LabelData
from app.models.monitoring import HealthStatus
from app.models.users import User
from app.sanitization import custom_secure_filename

router = APIRouter()


@router.get("/", tags=["Home"])
async def home(request: Request):
    return RedirectResponse(url=request.app.docs_url)


@router.get("/health", tags=["Monitoring"], response_model=HealthStatus)
async def health_check():
    return HealthStatus()


@router.post("/analyze", response_model=LabelData, tags=["Pipeline"])
async def analyze_document(
    ocr: Annotated[OCR, Depends(get_ocr)],
    gpt: Annotated[GPT, Depends(get_gpt)],
    # settings: Annotated[Settings, Depends(get_settings)],
    files: Annotated[list[UploadFile], Depends(validate_files)],
):
    file_dict = {custom_secure_filename(f.filename): f.file for f in files}
    return extract_data(file_dict, ocr, gpt)


@router.post("/signup", tags=["Users"], status_code=201, response_model=User)
async def signup(
    cp: Annotated[ConnectionPool, Depends(get_connection_pool)],
    user: Annotated[User, Depends(authenticate_user)],
    settings: Annotated[Settings, Depends(get_settings)],
):
    try:
        return await sign_up(cp, user, settings.azure_storage_connection_string)
    except UserConflictError:
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail="User exists!")


@router.post("/login", tags=["Users"], status_code=200, response_model=User)
async def login(user: User = Depends(fetch_user)):
    return user


@router.get("/inspections", tags=["Inspections"], response_model=list[InspectionData])
async def get_inspections(
    cp: Annotated[ConnectionPool, Depends(get_connection_pool)],
    user: User = Depends(fetch_user),
):
    return await read_all_inspections(cp, user)


@router.get(
    "/inspections/{id}", tags=["Inspections"], response_model=InspectionResponse
)
async def get_inspection(
    cp: Annotated[ConnectionPool, Depends(get_connection_pool)],
    user: Annotated[User, Depends(fetch_user)],
    id: UUID,
):
    try:
        return await read_inspection(cp, user, id)
    except InspectionNotFoundError:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Inspection not found"
        )

@router.get("/files/{id}/pictures", tags=["Files"]) # TODO: Could be a separate endpoint
async def get_inspection_pictures(
    cp: Annotated[ConnectionPool, Depends(get_connection_pool)],
    user: Annotated[User, Depends(fetch_user)],
    id: UUID,
):
    try:
        return await get_pictures(cp, id)
    except InspectionNotFoundError:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Pictures not found"
        )
    
@router.post("/files/{id}/pictures", tags=["Files"]) # TODO: Could be a separate endpoint
async def post_pictures(
    cp: Annotated[ConnectionPool, Depends(get_connection_pool)],
    user: Annotated[User, Depends(fetch_user)],
    id: UUID,
):
    # try:
    #     pass
    # except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail=str("This endpoint is not implemented")
        )

@router.post("/inspections", tags=["Inspections"], response_model=InspectionResponse)
async def post_inspection(
    cp: Annotated[ConnectionPool, Depends(get_connection_pool)],
    user: Annotated[User, Depends(fetch_user)],
    settings: Annotated[Settings, Depends(get_settings)],
    label_data: Annotated[LabelData, Form(...)],
    files: Annotated[list[UploadFile], Depends(validate_files)],
):
    label_images = [await f.read() for f in files]
    conn_string = settings.azure_storage_connection_string
    return await create_inspection(cp, user, label_data, label_images, conn_string)


@router.put(
    "/inspections/{id}", tags=["Inspections"], response_model=InspectionResponse
)
async def put_inspection(
    cp: Annotated[ConnectionPool, Depends(get_connection_pool)],
    user: Annotated[User, Depends(fetch_user)],
    id: UUID,
    inspection: InspectionUpdate,
):
    try:
        return await update_inspection(cp, user, id, inspection)
    except InspectionNotFoundError:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Inspection not found"
        )


@router.delete(
    "/inspections/{id}", tags=["Inspections"], response_model=DeletedInspection
)
async def delete_inspection_(
    cp: Annotated[ConnectionPool, Depends(get_connection_pool)],
    user: Annotated[User, Depends(fetch_user)],
    settings: Annotated[Settings, Depends(get_settings)],
    id: UUID,
):
    try:
        conn_string = settings.azure_storage_connection_string
        return await delete_inspection(cp, user, id, conn_string)
    except InspectionNotFoundError:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Inspection not found"
        )
