from typing import Annotated

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from pipeline import GPT, OCR, FertilizerInspection
from pydantic import UUID4

from app.config import lifespan
from app.connection_manager import ConnectionManager
from app.controllers.items import create, read, read_all
from app.controllers.data_extraction import extract_data
from app.dependencies import get_connection_manager, get_gpt, get_ocr
from app.models.items import ItemCreate, ItemResponse
from app.sanitization import custom_secure_filename

app = FastAPI(lifespan=lifespan)


@app.get("/health", tags=["Monitoring"])
async def health_check():
    return {"status": "ok"}


@app.post("/analyze", response_model=FertilizerInspection, tags=["Pipeline"])
async def analyze_document(
    ocr: OCR = Depends(get_ocr),
    gpt: GPT = Depends(get_gpt),
    files: list[UploadFile] = File(...),
):
    files = {custom_secure_filename(f.filename): f.file for f in files}
    return extract_data(files, ocr, gpt)


# Just for demonstration
@app.post("/items/", response_model=ItemResponse, tags=["Items"])
async def create_item(item: ItemCreate):
    return create(item)


# Just for demonstration
@app.get("/items/", response_model=list[ItemResponse], tags=["Items"])
async def read_items():
    return read_all()


# Just for demonstration
@app.get(
    "/items/{item_id}",
    responses={
        400: {"description": "Invalid token header"},
        404: {"description": "Item not found"},
    },
    response_model=ItemResponse,
    tags=["Items"],
)
async def read_item(item_id: str):
    try:
        return read(item_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Item not found")


# Just for demonstration
@app.post("/subtypes")
async def insert(
    cm: Annotated[ConnectionManager, Depends(get_connection_manager)],
    id: UUID4 | str,
    type_fr: str,
    type_en: str,
):
    with cm as connection_manager:
        with connection_manager.get_cursor() as cur:
            cur.execute(
                "INSERT INTO sub_type VALUES (%s, %s, %s) returning *",
                (id, type_fr, type_en),
            )
            result = cur.fetchone()

    return {"message": result}


# Just for demonstration
@app.get("/subtypes/{id}")
async def get_subtype(
    cm: Annotated[ConnectionManager, Depends(get_connection_manager)],
    id: UUID4 | str,
):
    with cm as connection_manager:
        with connection_manager.get_cursor() as cur:
            cur.execute("SELECT * FROM sub_type WHERE id = %s", (id,))
            result = cur.fetchone()

            if not result:
                raise HTTPException(status_code=404, detail="Subtype not found")

    return {"message": result}
