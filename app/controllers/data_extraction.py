from pipeline import GPT, OCR, LabelStorage, analyze

from app.models.label_data import LabelData


def extract_data(
    ocr: OCR,
    gpt: GPT,
    files: list[bytes],
):
    if not files:
        raise ValueError("No files to analyze")

    label_storage = LabelStorage()
    for f in files:
        label_storage.add_image(f)

    data = analyze(label_storage, ocr, gpt)

    return LabelData.model_validate(data.model_dump())
