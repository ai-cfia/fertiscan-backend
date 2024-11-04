import os
from typing import BinaryIO

from pipeline import GPT, OCR, LabelStorage, analyze

from app.models.label_data import LabelData


def extract_data(files: dict[str, BinaryIO], ocr: OCR, gpt: GPT, folder_name: str):
    """
    Extracts data from provided image files using OCR and GPT.

    Args:
        files (dict[str, BinaryIO]): A dictionary with filenames as keys
            and file-like binary objects as values.
        ocr: OCR processing tool or function used for text extraction.
        gpt: GPT-based model or function used for data analysis.
        folder_name (str): Folder path to save the temporary image files.

    Raises:
        ValueError: If no files are provided for analysis.

    Returns:
        LabelData: A `LabelData` object populated with extracted and validated data.
    """
    if not files:
        raise ValueError("No files to analyze")

    # TODO: Validate file types if necessary

    os.makedirs(folder_name, exist_ok=True)

    label_storage = LabelStorage()

    for filename in files:
        file_path = os.path.join(folder_name, filename)
        with open(file_path, "wb") as f:
            f.write(files[filename].read())
        label_storage.add_image(file_path)

    data = analyze(label_storage, ocr, gpt)

    return LabelData.model_validate(data.model_dump())
