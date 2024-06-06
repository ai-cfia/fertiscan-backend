import os
import logging
from dotenv import load_dotenv
from backend.document_storage import DocumentStorage
from backend.ocr import OCR
from backend.gpt import GPT
from backend import save_text_to_file
from typing import Dict

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pipeline.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
DOCUMENT_INTELLIGENCE_API_ENDPOINT = os.getenv('AZURE_API_ENDPOINT')
DOCUMENT_INTELLIGENCE_API_KEY = os.getenv('AZURE_API_KEY')
OPENAI_API_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
OPENAI_API_KEY = os.getenv('AZURE_OPENAI_KEY')

INPUT_IMAGES_PATH = 'e2e_tests/image_inputs'
OCR_OUTPUTS_PATH = 'e2e_tests/ocr_outputs'
LLM_OUTPUTS_PATH = 'e2e_tests/llm_outputs'


def process_ocr(ocr_engines: Dict[str, OCR]) -> None:
    for engine_name, ocr_engine in ocr_engines.items():
        engine_output_dir = os.path.join(OCR_OUTPUTS_PATH, engine_name)
        os.makedirs(engine_output_dir, exist_ok=True)

        for img in os.listdir(INPUT_IMAGES_PATH):
            try:
                image_name, _ = os.path.splitext(os.path.basename(img))

                document_storage.add_image(os.path.join(INPUT_IMAGES_PATH, img))
                document = document_storage.get_document(format='pdf')

                result = ocr_engine.extract_text(document=document)
                output_filepath = os.path.join(engine_output_dir, f"ocr_{engine_name}_{image_name}.md")
                save_text_to_file(result.content, output_filepath)

                logger.info(f"Processed OCR for {img} with {engine_name}")
            except Exception as e:
                logger.error(f"Failed to process {img} with {engine_name}: {e}", exc_info=True)
            finally:
                document_storage.images = []


def validate_env_vars():
    required_vars = [
        'AZURE_API_ENDPOINT', 
        'AZURE_API_KEY', 
        'AZURE_OPENAI_ENDPOINT', 
        'AZURE_OPENAI_KEY'
    ]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")


if __name__ == "__main__":
    try:
        validate_env_vars()
        document_storage = DocumentStorage()

        # OCR Engines
        document_intelligence = OCR(api_endpoint=DOCUMENT_INTELLIGENCE_API_ENDPOINT, api_key=DOCUMENT_INTELLIGENCE_API_KEY)

        # LLMs
        gpt35 = GPT(api_endpoint=OPENAI_API_ENDPOINT, api_key=OPENAI_API_KEY, deployment='ailab-gpt-35-turbo-16k')
        gpt4 = GPT(api_endpoint=OPENAI_API_ENDPOINT, api_key=OPENAI_API_KEY, deployment="ailab-llm")

        ocr_engines = {
            "document_intelligence": document_intelligence,
        }

        llm_models = {
            "gpt-35": gpt35,
            "gpt-4": gpt4,
        }

        process_ocr(ocr_engines)
        logger.info("OCR processing completed successfully for all engines.")
    except EnvironmentError as e:
        logger.critical(f"Environment setup error: {e}")
    except Exception as e:
        logger.critical(f"An error occurred: {e}", exc_info=True)