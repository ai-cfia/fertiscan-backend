import os
from PIL import Image
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

class LabelStorage:
    def __init__(self):
        self.images = []

    def add_image(self, image: str):
        if not os.path.exists(image):
            raise FileNotFoundError(f"The file {image} does not exist.")
        self.images.append(image)

    def _create_composite_image(self) -> Image:
        if not self.images:
            raise ValueError("No images to merge.")

        # Open images and get their dimensions
        opened_images = [Image.open(image_path) for image_path in self.images]
        widths, heights = zip(*(img.size for img in opened_images))

        total_height = sum(heights)
        max_width = max(widths)

        # Create a new blank image with the appropriate size
        composite_image = Image.new('RGB', (max_width, total_height))

        y_offset = 0
        for img in opened_images:
            composite_image.paste(img, (0, y_offset))
            y_offset += img.height

        return composite_image
    
    def _create_pdf_document(self) -> BytesIO:
        pdf_buffer = BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=letter)

        for image in self.images:
            # Add image to the PDF page
            c.drawImage(image=image, x=0, y=0, width=letter[0], height=letter[1])
            c.showPage()  # End the current page and start a new one

        c.save()
        pdf_buffer.seek(0)

        return pdf_buffer
    
    def clear(self):
        for image_path in self.images:
            os.remove(image_path)

        self.images = []

    def get_document(self, format='pdf') -> bytes:
        # Ensure there are images to merge
        if not self.images:
            raise ValueError("No images to merge.")
        
        output = BytesIO()
        
        if format == 'pdf':
            output = self._create_pdf_document()
        elif format == 'png':
            composite_image = self._create_composite_image()
            composite_image.save(output, format='PNG')
        else:
            raise ValueError("Unknown document format output.")

        return output.getvalue()
