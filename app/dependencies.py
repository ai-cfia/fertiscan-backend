from fastapi import Request


def get_connection_manager(request: Request):
    """
    Returns the app's ConnectionManager instance.
    """
    return request.app.connection_manager


def get_ocr(request: Request):
    """
    Returns the app's OCR instance.
    """
    return request.app.ocr


def get_gpt(request: Request):
    """
    Returns the app's GPT instance.
    """
    return request.app.gpt
