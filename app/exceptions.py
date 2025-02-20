import traceback

from fastapi.logger import logger


class UserError(Exception):
    pass


class UserNotFoundError(UserError):
    pass


class UserConflictError(UserError):
    pass


class MissingUserAttributeError(UserError):
    pass


class InspectionError(Exception):
    pass


class InspectionNotFoundError(InspectionError):
    pass


class FileError(Exception):
    pass


class FileNotFoundError(FileError):
    pass


def log_error(error: Exception):
    """Logs the error message and traceback."""
    logger.error(f"Error occurred: {error}")
    logger.error("Traceback: " + traceback.format_exc())
