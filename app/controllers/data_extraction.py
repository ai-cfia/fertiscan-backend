import io
from typing import BinaryIO
from PIL import Image

from pipeline import analyze, Settings
from app.models.label_data import LabelData

def extract_data(files: dict[str, BinaryIO], settings: Settings):
    """
    Extracts data from provided image files using OCR and GPT.

    Args:
        files (dict[str, BinaryIO]): A dictionary with filenames as keys
            and file-like binary objects as values.
        ocr: OCR processing tool or function used for text extraction.
        gpt: GPT-based model or function used for data analysis.

    Raises:
        ValueError: If no files are provided for analysis.

    Returns:
        LabelData: A `LabelData` object populated with extracted and validated data.
    """
    if not files:
        raise ValueError("No files to analyze")

    # TODO: Validate file types if necessary

    images = []
    for filename in files:
        images.append(Image.open(io.BytesIO(files[filename].read())))

    data = analyze(images, settings)

    return LabelData.model_validate(data.model_dump())
