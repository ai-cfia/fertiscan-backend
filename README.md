# FertiScan Backend

([*Le français est disponible au bas de la page*](#fertiscan-backend-fr))

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
    --build-arg ARG_ALLOWED_ORIGINS=["http://url.to_frontend/"] \
    --build-arg OTEL_EXPORTER_OTLP_ENDPOINT=your_phoenix_endpoint \
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
ALLOWED_ORIGINS=["http://url.to_frontend/"]
```

## API Endpoints

The [Swagger UI](https://swagger.io/tools/swagger-ui/) for the API of FertiScan
is available at `/docs`.

More details in the developer [documentation](./docs/README.md).

---

## FertiScan Backend (FR)

FertiScan aide les inspecteurs à analyser et traiter les étiquettes d'engrais en
extrayant du texte et en générant des formulaires structurés.

## Aperçu

Ce dépôt contient le backend de FertiScan, un serveur basé sur FastAPI conçu
pour fonctionner avec le
[frontend](https://github.com/ai-cfia/fertiscan-frontend/). Il gère les
téléversements d'images, l'analyse de documents à l'aide de
l'[OCR](https://fr.wikipedia.org/wiki/Reconnaissance_optique_de_caract%C3%A8res)
et la génération de formulaires à l'aide d'un
[LLM](https://fr.wikipedia.org/wiki/Mod%C3%A8le_de_langage).

![workflow](./out/workflow_dss/FertiScan%20Sequence%20Diagram.png)

## Configuration pour le développement

### Prérequis

- Python 3.11+
- [pip](https://pip.pypa.io/en/stable/installation/)
- [virtualenv](https://virtualenv.pypa.io/en/latest/installation.html)
- Clés API Azure Document Intelligence et OpenAI

### Exécution locale

1. Clonez le dépôt :

    ```sh
    git clone https://github.com/ai-cfia/fertiscan-backend.git
    cd fertiscan-backend
    ```

2. Installez les dépendances :

    ```sh
    pip install -r requirements.txt
    ```

3. Démarrez le serveur en mode développement :

    ```sh
    fastapi dev app/main.py --port 5000
    ```

### Exécution avec Docker

1. Construisez l'image Docker :

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
    --build-arg ARG_ALLOWED_ORIGINS=["http://url.to_frontend/"] \
    --build-arg OTEL_EXPORTER_OTLP_ENDPOINT=your_phoenix_endpoint \
    --build-arg ARG_PROMPT_PATH=path/to/file \
    --build-arg ARG_UPLOAD_PATH=path/to/file \
    .
    ```

2. Lancez le conteneur Docker :

    ```sh
    docker run -p 5000:5000 fertiscan-backend
    ```

#### Docker-Compose

1. Créez un fichier `.env` à partir du fichier [.env.template](./.env.template).
   Incluez les variables d'environnement suivantes :

    ```ini
    FERTISCAN_DB_URL=postgresql://postgres:postgres@postgres:5432/fertiscan
    BB_URL=bytebase_url
    BB_SERVICE_ACCOUNT=your-bytebase-sa@service.bytebase.com
    BB_SERVICE_KEY=your-bytebase-sa-key
    BB_INSTANCE_ID=your-bytebase-instance-id
    BB_DATABASE_ID=your-bytebase-database-id
    ```

    Vous pouvez trouver leurs valeurs dans notre coffre-fort sous fertiscan-dev.

2. Lancez le conteneur Docker :

    ```sh
    docker-compose up --build
    ```

> **Note** : Si vous êtes sur une machine ARM, vous devrez construire l'image
> avec la commande `docker-compose build --build-arg TARGETARCH=arm64`.

L'application sera disponible sur `http://localhost:80`. La base de données sera
construite dynamiquement en fonction du dernier schéma depuis Bytebase.

Pour utiliser pgAdmin, accédez à `http://localhost:5050` et connectez-vous avec
`admin@example.com` et `admin`. Vous pourrez alors enregistrer un nouveau
serveur avec les détails suivants :

- Hôte : `postgres`
- Port : `5432`
- Utilisateur : `postgres`
- Mot de passe : `postgres`
- Base de données : `fertiscan`

### Variables d'environnement

Créez un fichier `.env` à partir du fichier [.env.template](./.env.template).

```ini
AZURE_API_ENDPOINT=your_azure_form_recognizer_endpoint
AZURE_API_KEY=your_azure_form_recognizer_key
AZURE_OPENAI_API_ENDPOINT=your_azure_openai_endpoint
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_DEPLOYMENT=your_azure_openai_deployment

FERTISCAN_DB_URL=your_fertiscan_db_url
FERTISCAN_SCHEMA=your_fertiscan_schema

UPLOAD_PATH=path/to/file
ALLOWED_ORIGINS=["http://url.to_frontend/"]
```

## Points de terminaison de l'API

L'[interface Swagger UI](https://swagger.io/tools/swagger-ui/) pour l'API de
FertiScan est disponible à l'adresse `/docs`.

Pour plus de détails, consultez la [documentation pour les
développeurs](./docs/README.md).
