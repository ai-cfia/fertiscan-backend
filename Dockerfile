FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

ARG ARG_AZURE_API_ENDPOINT
ARG ARG_AZURE_API_KEY
ARG ARG_AZURE_OPENAI_API_ENDPOINT
ARG ARG_AZURE_OPENAI_API_KEY
ARG ARG_AZURE_OPENAI_DEPLOYMENT
ARG ARG_PROMPT_PATH
ARG ARG_UPLOAD_PATH
ARG ARG_FRONTEND_URL
ARG ARG_FERTISCAN_DB_URL
ARG ARG_FERTISCAN_SCHEMA

ENV AZURE_API_ENDPOINT=${ARG_AZURE_API_ENDPOINT:-your_azure_form_recognizer_endpoint}
ENV AZURE_API_KEY=${ARG_AZURE_API_KEY:-your_azure_form_recognizer_key}
ENV AZURE_OPENAI_API_ENDPOINT=${ARG_AZURE_OPENAI_API_ENDPOINT:-your_azure_openai_endpoint}
ENV AZURE_OPENAI_API_KEY=${ARG_AZURE_OPENAI_API_KEY:-your_azure_openai_key}
ENV AZURE_OPENAI_DEPLOYMENT=${ARG_AZURE_OPENAI_API_KEY:-your_azure_openai_key}
ENV PROMPT_PATH=${ARG_PROMPT_PATH:-path/to/file}
ENV UPLOAD_PATH=${ARG_UPLOAD_PATH:-path/to/file}
ENV FRONTEND_URL=${ARG_FRONTEND_URL:-http://url.to_frontend/}
ENV FERTISCAN_DB_URL=${ARG_FERTISCAN_DB_URL:-your_fertiscan_db_url}
ENV FERTISCAN_SCHEMA=${ARG_FERTISCAN_SCHEMA:-your_fertiscan_schema}

EXPOSE 5000

RUN chown -R 1000:1000 /app

USER 1000

CMD ["python", "app.py"]
