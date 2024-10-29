from fastapi import Request
from pipeline import GPT, OCR

from app.connection_manager import ConnectionManager


def get_connection_manager(request: Request) -> ConnectionManager:
    """
    Returns the app's ConnectionManager instance.
    """
    return request.app.connection_manager


def get_ocr(request: Request) -> OCR:
    """
    Returns the app's OCR instance.
    """
    return request.app.ocr


def get_gpt(request: Request) -> GPT:
    """
    Returns the app's GPT instance.
    """
    return request.app.gpt
