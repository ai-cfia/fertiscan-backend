# fertiscan/io/document_storage.py

import os
from PIL import Image
from io import BytesIO

class DocumentStore:
    def __init__(self):
        self.pages = []

    def add_page(self, page):
        if isinstance(page, str):
            if not os.path.exists(page):
                raise FileNotFoundError(f"The file {page} does not exist.")
            file = open(page)
            image = file.read()
            file.close()
        elif isinstance(page, bytes):
            image = page
        else:
            raise ValueError("The document must be a file path (str) or in bytes format.")

        self.pages.append(image)

    def get_document(self) -> bytes:
        # Ensure there are images to merge
        if not self.pages:
            raise ValueError("No images to merge.")

        # Calculate the total height and maximum width of the resulting image
        # total_height = sum(img.height for img in self.pages)
        # max_width = max(img.width for img in self.pages)

        # Create a new image with the calculated dimensions
        # merged_image = Image.new('RGB', (max_width, total_height))

        # Paste all images into the new image
        # y_offset = 0
        # for img in self.pages:
            # merged_image.paste(img, (0, y_offset))
            # y_offset += img.height

        # Save the merged image
        return self.pages[0]
