# fertiscan-backend

A flask-based backend for FertiScan.

## Setup for Development

### Prerequisites

- Python 3.8 or higher
- [pip](https://pip.pypa.io/en/stable/installation/)
- [virtualenv](https://virtualenv.pypa.io/en/stable/installation/)
- Azure Document Intelligence and OpenAI API keys

### Running

#### Locally

```sh
cd fertiscan-backend
pip install -r requirements.txt
python ./app.py
```

#### With docker

1. Build the docker image

    ```bash
    docker build -t fertiscan-backend \
    --build-arg ARG_AZURE_API_ENDPOINT=your_actual_azure_form_recognizer_endpoint \
    --build-arg ARG_AZURE_API_KEY=your_actual_azure_form_recognizer_key \
    --build-arg ARG_AZURE_OPENAI_API_ENDPOINT=your_actual_azure_openai_endpoint \
    --build-arg ARG_AZURE_OPENAI_API_KEY=your_actual_azure_openai_key \
    --build-arg ARG_PROMPT_PATH=actual_path/to/prompt_file \
    --build-arg ARG_UPLOAD_PATH=actual_path/to/upload_file \
    .
    ```

2. Run the docker image

    ```bash
    docker run -p 5000:5000 fertiscan-backend
    ```

3. Test the application

Go to `http://localhost:5000` and test the application.

#### With docker-compose

Coming soon...

### Environment Variables

Create a `.env` file in the root directory from `.env.template`:

```plaintext
AZURE_API_ENDPOINT=your_azure_form_recognizer_endpoint
AZURE_API_KEY=your_azure_form_recognizer_key
AZURE_OPENAI_API_ENDPOINT=your_azure_openai_endpoint
AZURE_OPENAI_API_KEY=your_azure_openai_key
PROMPT_PATH=path/to/file
UPLOAD_PATH=path/to/file
```

## API Endpoints

* `POST /upload`: Upload an image to be analyzed.
* `GET /analyze`: Analyze the uploaded image and returns the form.
