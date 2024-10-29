import re


def custom_secure_filename(filename):
    """
    Sanitize filename by removing paths, replacing spaces, and keeping only safe characters.

    Args:
        filename (str): Input filename.

    Returns:
        str: Sanitized filename.
    """
    # Remove leading path elements
    filename = filename.split("/")[-1].split("\\")[-1]

    # Replace spaces with underscores
    filename = filename.replace(" ", "_")

    # Remove special characters except dot, underscore, and hyphen
    filename = re.sub(r"[^a-zA-Z0-9._-]", "", filename)

    return filename
