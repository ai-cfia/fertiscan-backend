# fertiscan-backend

A flask-based backend for FertiScan.

## Setup for Development

### Prerequisites
- Python 3.8 or higher
- [pip](https://pip.pypa.io/en/stable/installation/)
- [virtualenv](https://virtualenv.pypa.io/en/stable/installation/)
- Azure Document Intelligence and OpenAI API keys

### Running

```sh
cd fertiscan-backend
pip install -r requirements.txt
python ./app.py
```

### Environment Variables

Create a `.env` file in the root directory from `.env.template`:

```plaintext
AZURE_API_ENDPOINT=your_azure_form_recognizer_endpoint
AZURE_API_KEY=your_azure_form_recognizer_key
AZURE_OPENAI_API_ENDPOINT=your_azure_openai_endpoint
AZURE_OPENAI_API_KEY=your_azure_openai_key
PROMPT_PATH=path/to/file
UPLOAD_PATH=path/to/file
FRONTEND_URL=http://url.to_frontend/
```

## API Endpoints

* `POST /upload`: Upload an image to be analyzed.
* `GET /analyze`: Analyze the uploaded image and returns the form.
