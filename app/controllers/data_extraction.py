import asyncio
from uuid import UUID

from pipeline import GPT, OCR, LabelStorage, analyze
from psycopg_pool import ConnectionPool

from app.controllers.files import create_folder, delete_folder
from app.exceptions import log_error
from app.models.label_data import LabelData


async def extract_data(
    cp: ConnectionPool,
    conn_string: str,
    ocr: OCR,
    gpt: GPT,
    user_id: UUID | str,
    files: list[bytes],
):
    if not files:
        raise ValueError("No files to analyze")

    label_storage = LabelStorage()
    for f in files:
        label_storage.add_image(f)

    t_analyze = asyncio.to_thread(analyze, label_storage, ocr, gpt)
    t_folder = create_folder(cp, conn_string, user_id, files)

    data, folder = await asyncio.gather(t_analyze, t_folder, return_exceptions=True)

    if isinstance(data, Exception):
        if not isinstance(folder, Exception):
            asyncio.create_task(delete_folder(cp, conn_string, user_id, folder.id))
        raise data

    label_data = LabelData.model_validate(data.model_dump())

    if isinstance(folder, Exception):
        log_error(folder)
    else:
        label_data.picture_set_id = folder.id

    return label_data
