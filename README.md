# Festiscan Backend

FertiScan helps inspectors analyze and process fertilizer labels by extracting
text and generating structured forms.

## Overview

This repository contains the backend for FertiScan, a FastAPI-based server
designed to work with the
[frontend](https://github.com/ai-cfia/fertiscan-frontend/). It handles image
uploads, document analysis using
[OCR](https://en.wikipedia.org/wiki/Optical_character_recognition), and form
generation using an [LLM](https://en.wikipedia.org/wiki/Large_language_model).

![workflow](./out/workflow_dss/FertiScan%20Sequence%20Diagram.png)

## Setup for Development

### Prerequisites

- Python 3.11+
- [pip](https://pip.pypa.io/en/stable/installation/)
- [virtualenv](https://virtualenv.pypa.io/en/latest/installation.html)
- Azure Document Intelligence and OpenAI API keys

### Running Locally

1. Clone the repository:

    ```sh
    git clone https://github.com/ai-cfia/fertiscan-backend.git
    cd fertiscan-backend
    ```

2. Install dependencies:

    ```sh
    pip install -r requirements.txt
    ```

3. Start the server in development mode:

    ```sh
    fastapi dev app/main.py --port 5000
    ```

### Running with Docker

1. Build the Docker image:

    ```sh
    docker build -t fertiscan-backend \
    --build-arg ARG_AZURE_API_ENDPOINT=your_azure_form_recognizer_endpoint \
    --build-arg ARG_AZURE_API_KEY=your_azure_form_recognizer_key \
    --build-arg ARG_AZURE_OPENAI_DEPLOYMENT=your_azure_openai_deployment \
    --build-arg ARG_AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint \
    --build-arg ARG_AZURE_OPENAI_KEY=your_azure_openai_key \
    --build-arg ARG_FERTISCAN_STORAGE_URL=your_fertiscan_storage_url \
    --build-arg ARG_FERTISCAN_DB_URL=your_fertiscan_db_url \
    --build-arg ARG_FERTISCAN_SCHEMA=your_fertiscan_schema \
    --build-arg ARG_FRONTEND_URL=http://url.to_frontend/ \
    --build-arg ARG_PROMPT_PATH=path/to/file \
    --build-arg ARG_UPLOAD_PATH=path/to/file \
    .
    ```

2. Run the Docker container:

    ```sh
    docker run -p 5000:5000 fertiscan-backend
    ```

#### Docker Compose

1. Create a `.env` file from [.env.template](./.env.template). Include the
   following environment variables:

    ```ini
    FERTISCAN_DB_URL=postgresql://postgres:postgres@postgres:5432/fertiscan
    BB_URL=bytebase_url
    BB_SERVICE_ACCOUNT=your-bytebase-sa@service.bytebase.com
    BB_SERVICE_KEY=your-bytebase-sa-key
    BB_INSTANCE_ID=your-bytebase-instance-id
    BB_DATABASE_ID=your-bytebase-database-id
    ```

    You can find their values in our vault under fertiscan-dev.

2. Start the Docker container:

    ```sh
    docker-compose up --build
    ```

> **Side note:** If you are on an ARM-based machine, you will need to build the
> image with the `docker-compose build --build-arg TARGETARCH=arm64` command.

The application will be available at `http://localhost:80`. The database should
be dynamically built based on the latest schema from Bytebase.

To use pgAdmin, navigate to `http://localhost:5050` and log in with
`admin@example.com` and `admin`. You can then register a new server with the
following details:

- Host: `postgres`
- Port: `5432`
- Username: `postgres`
- Password: `postgres`
- Database: `fertiscan`

### Environment Variables

Create a `.env` file from [.env.template](./.env.template).

```ini
AZURE_API_ENDPOINT=your_azure_form_recognizer_endpoint
AZURE_API_KEY=your_azure_form_recognizer_key
AZURE_OPENAI_API_ENDPOINT=your_azure_openai_endpoint
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_DEPLOYMENT=your_azure_openai_deployment

FERTISCAN_DB_URL=your_fertiscan_db_url
FERTISCAN_SCHEMA=your_fertiscan_schema

UPLOAD_PATH=path/to/file
FRONTEND_URL=http://url.to_frontend/
```

## API Endpoints

The [Swagger UI](https://swagger.io/tools/swagger-ui/) for the API of FertiScan
is available at `/docs`.

More details in the developer [documentation](./docs/README.md).
