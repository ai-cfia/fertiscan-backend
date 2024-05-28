import os
from PIL import Image
from io import BytesIO

class DocumentStorage:
    def __init__(self):
        self.images = []

    def add_image(self, image):
        if isinstance(image, str):
            if not os.path.exists(image):
                raise FileNotFoundError(f"The file {image} does not exist.")
            with open(image, 'rb') as file:
                image = Image.open(BytesIO(file.read()))
        elif isinstance(image, bytes):
            image = Image.open(BytesIO(image))
        else:
            raise ValueError("The document must be a file path (str) or in bytes format.")

        self.images.append(image)

    def _create_composite_image(self) -> bytes:
        # Get dimensions for the composite image
        widths, heights = zip(*(i.size for i in self.images))

        total_height = sum(heights)
        max_width = max(widths)

        composite_image = Image.new('RGB', (max_width, total_height))

        y_offset = 0
        for img in self.images:
            composite_image.paste(img, (0, y_offset))
            y_offset += img.height

        # Save the composite image to bytes
        output = BytesIO()
        composite_image.save(output, format='PNG')
        return output.getvalue()

    def get_document(self) -> bytes:
        # Ensure there are images to merge
        if not self.images:
            raise ValueError("No images to merge.")

        return self._create_composite_image()


def save_bytes_to_image(image_bytes: bytes, output_path: str):
    with open(output_path, 'wb') as output_file:
        output_file.write(image_bytes)