from fastapi import Request


def get_connection_manager(request: Request):
    """
    Returns the app's ConnectionManager instance.
    """
    return request.app.connection_manager
