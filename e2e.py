import os
import logging
from dotenv import load_dotenv
from backend.document_storage import DocumentStorage
from backend.ocr import OCR
from backend.gpt import GPT
from backend import save_text_to_file
from typing import Dict

load_dotenv()

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


DOCUMENT_INTELLIGENCE_API_ENDPOINT = os.getenv('AZURE_API_ENDPOINT')
DOCUMENT_INTELLIGENCE_API_KEY = os.getenv('AZURE_API_KEY')
OPENAI_API_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
OPENAI_API_KEY = os.getenv('AZURE_OPENAI_KEY')

INPUT_IMAGES_PATH = 'e2e_tests/image_inputs'
OCR_OUTPUTS_PATH = 'e2e_tests/ocr_outputs'
LLM_OUTPUTS_PATH = 'e2e_tests/llm_outputs'


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pipeline.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def process_ocr(ocr_engines: Dict[str, OCR]) -> None:
    for ocr_engine_name, ocr_engine in ocr_engines.items():
        engine_output_dir = os.path.join(OCR_OUTPUTS_PATH, ocr_engine_name)
        os.makedirs(engine_output_dir, exist_ok=True)

        for img in os.listdir(INPUT_IMAGES_PATH):
            image_name, _ = os.path.splitext(os.path.basename(img))
            output_filepath = os.path.join(engine_output_dir, f"ocr_{ocr_engine_name}_{image_name}.md")

            if os.path.exists(output_filepath):
                logger.info(f"OCR output for {img} with {ocr_engine_name} already exists. Skipping processing.")
                continue

            try:
                document_storage.add_image(os.path.join(INPUT_IMAGES_PATH, img))
                document = document_storage.get_document(format='pdf')

                result = ocr_engine.extract_text(document=document)
                save_text_to_file(result.content, output_filepath)

                logger.info(f"Processed OCR for {img} with {ocr_engine_name}")
            except Exception as e:
                logger.error(f"Failed to process {img} with {ocr_engine_name}: {e}", exc_info=True)
            finally:
                document_storage.images = []


def process_llm(ocr_engines: Dict[str, OCR], llm_models: Dict[str, GPT]) -> None:
    for ocr_engine_name, _ in ocr_engines.items():
        ocr_output_dir = os.path.join(OCR_OUTPUTS_PATH, ocr_engine_name)
        for llm_name, llm_model in llm_models.items():
            llm_output_dir = os.path.join(LLM_OUTPUTS_PATH, llm_name)
            os.makedirs(llm_output_dir, exist_ok=True)

            for ocr_output_file in os.listdir(ocr_output_dir):
                ocr_output_file_basename, _ = os.path.splitext(os.path.basename(ocr_output_file))
                output_filename = f"llm_{llm_name}_{ocr_output_file_basename}.json"
                llm_output_path = os.path.join(llm_output_dir, output_filename)

                if os.path.exists(llm_output_path):
                    logger.info(f"LLM output for {ocr_output_file} with {llm_name} already exists. Skipping processing.")
                    continue

                try:
                    ocr_output_path = os.path.join(ocr_output_dir, ocr_output_file)
                    with open(ocr_output_path, 'r') as file:
                        ocr_content = file.read()
                    
                    llm_result = llm_model.generate_form(ocr_content)
                    save_text_to_file(llm_result, llm_output_path)

                    logger.info(f"Processed LLM for {ocr_output_file} with {llm_name}")
                except Exception as e:
                    logger.error(f"Failed to process {ocr_output_file} with {llm_name}: {e}", exc_info=True)


if __name__ == "__main__":
    try:
        validate_env_vars()
        document_storage = DocumentStorage()

        document_intelligence = OCR(api_endpoint=DOCUMENT_INTELLIGENCE_API_ENDPOINT, api_key=DOCUMENT_INTELLIGENCE_API_KEY)

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

        process_llm(ocr_engines, llm_models)
        logger.info("LLM processing completed successfully for all models.")
    except EnvironmentError as e:
        logger.critical(f"Environment setup error: {e}")
    except Exception as e:
        logger.critical(f"An error occurred: {e}", exc_info=True)