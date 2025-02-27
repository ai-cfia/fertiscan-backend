from http import HTTPStatus
from typing import Annotated
from uuid import UUID

import filetype
from fastapi import APIRouter, Depends, HTTPException, Request, Response, UploadFile
from fastapi.responses import RedirectResponse
from pipeline import GPT, OCR
from psycopg_pool import ConnectionPool

from app.config import Settings
from app.controllers.data_extraction import extract_data
from app.controllers.files import (
    create_folder,
    delete_folder,
    read_file,
    read_folder,
    read_folders,
)
from app.controllers.inspections import (
    create_inspection,
    delete_inspection,
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
from app.exceptions import FileNotFoundError, InspectionNotFoundError, UserConflictError
from app.models.files import DeleteFolderResponse, FolderResponse
from app.models.inspections import (
    DeletedInspection,
    InspectionCreate,
    InspectionData,
    InspectionResponse,
    InspectionUpdate,
)
from app.models.label_data import LabelData
from app.models.monitoring import HealthStatus
from app.models.users import User

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
    files: Annotated[list[UploadFile], Depends(validate_files)],
):
    label_images = [await f.read() for f in files]
    return extract_data(ocr, gpt, label_images)


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


@router.post("/inspections", tags=["Inspections"], response_model=InspectionResponse)
async def post_inspection(
    cp: Annotated[ConnectionPool, Depends(get_connection_pool)],
    user: Annotated[User, Depends(fetch_user)],
    data: InspectionCreate,
):
    return await create_inspection(cp, user, data)


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


@router.get("/files", tags=["Files"], response_model=list[FolderResponse])
async def get_folders(
    cp: Annotated[ConnectionPool, Depends(get_connection_pool)],
    user: Annotated[User, Depends(fetch_user)],
):
    return await read_folders(cp, user.id)


@router.get("/files/{folder_id}", tags=["Files"], response_model=FolderResponse)
async def get_folder(
    cp: Annotated[ConnectionPool, Depends(get_connection_pool)],
    user: Annotated[User, Depends(fetch_user)],
    folder_id: UUID,
):
    try:
        return await read_folder(cp, user.id, folder_id)
    except FileNotFoundError:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Folder not found")


@router.post("/files", tags=["Files"], response_model=FolderResponse)
async def create_folder_(
    cp: Annotated[ConnectionPool, Depends(get_connection_pool)],
    user: Annotated[User, Depends(fetch_user)],
    settings: Annotated[Settings, Depends(get_settings)],
    files: Annotated[list[UploadFile], Depends(validate_files)],
):
    label_images = [await f.read() for f in files]
    conn_string = settings.azure_storage_connection_string
    return await create_folder(cp, conn_string, user.id, label_images)


@router.delete(
    "/files/{folder_id}", tags=["Files"], response_model=DeleteFolderResponse
)
async def delete_folder_(
    cp: Annotated[ConnectionPool, Depends(get_connection_pool)],
    user: Annotated[User, Depends(fetch_user)],
    settings: Annotated[Settings, Depends(get_settings)],
    folder_id: UUID,
):
    conn_string = settings.azure_storage_connection_string
    try:
        return await delete_folder(cp, conn_string, user.id, folder_id)
    except FileNotFoundError:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Folder not found")


@router.get("/files/{folder_id}/{file_id}", tags=["Files"], response_class=Response)
async def get_file(
    settings: Annotated[Settings, Depends(get_settings)],
    user: Annotated[User, Depends(fetch_user)],
    folder_id: UUID,
    file_id: UUID,
):
    conn = settings.azure_storage_connection_string
    try:
        binaries = await read_file(conn, user.id, folder_id, file_id)
        kind = filetype.guess(binaries)
        mime_type = kind.mime if kind else "application/octet-stream"
        return Response(content=binaries, media_type=mime_type)
        # in the future, the mimetype should be saved upstream and returned here
    except FileNotFoundError:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="File not found")
