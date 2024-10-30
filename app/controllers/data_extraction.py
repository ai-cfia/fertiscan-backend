import os
from typing import BinaryIO

from pipeline import FertilizerInspection, LabelStorage, analyze

from app.constants import UPLOAD_FOLDER


def extract_data(files: dict[str, BinaryIO], ocr, gpt) -> FertilizerInspection:
    """
    Extracts data from provided image files using OCR and GPT.

    Args:
        files (dict[str, BinaryIO]): A dictionary where keys are filenames
            and values are file-like binary objects.
        ocr: An OCR processing object or function for extraction.
        gpt: A GPT-based model or function for extraction.

    Raises:
        ValueError: If no files are provided.

    Returns:
        Extracted data results from the `analyze` function.
    """
    if not files:
        raise ValueError("No files to analyze")

    # TODO: should probably validate file type

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    label_storage = LabelStorage()

    for filename in files:
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        with open(file_path, "wb") as f:
            f.write(files[filename].read())
        label_storage.add_image(file_path)

    return analyze(label_storage, ocr, gpt)
