# fertiscan/io/document_storage.py

import os
from PIL import Image
from io import BytesIO

class DocumentStore:
    def __init__(self):
        self.pages = []

    def add_page(self, document):
        if isinstance(document, str):
            if not os.path.exists(document):
                raise FileNotFoundError(f"The file {document} does not exist.")
            image = Image.open(document)
        elif isinstance(document, bytes):
            image = Image.open(BytesIO(document))
        else:
            raise ValueError("The document must be a file path (str) or in bytes format.")

        self.pages.append(image)

    def get_document(self) -> Image:
        # Ensure there are images to merge
        if not self.documents:
            raise ValueError("No images to merge.")

        # Calculate the total height and maximum width of the resulting image
        total_height = sum(img.height for img in self.documents)
        max_width = max(img.width for img in self.documents)

        # Create a new image with the calculated dimensions
        merged_image = Image.new('RGB', (max_width, total_height))

        # Paste all images into the new image
        y_offset = 0
        for img in self.documents:
            merged_image.paste(img, (0, y_offset))
            y_offset += img.height

        # Save the merged image
        return merged_image
