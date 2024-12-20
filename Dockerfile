FROM python:3.12-bullseye

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt
RUN opentelemetry-bootstrap --action=install

ARG ARG_AZURE_API_ENDPOINT
ARG ARG_AZURE_API_KEY
ARG ARG_AZURE_OPENAI_DEPLOYMENT
ARG ARG_AZURE_OPENAI_ENDPOINT
ARG ARG_AZURE_OPENAI_KEY
ARG ARG_FERTISCAN_STORAGE_URL
ARG ARG_FERTISCAN_DB_URL
ARG ARG_FERTISCAN_SCHEMA
ARG ARG_ALLOWED_ORIGINS
ARG ARG_PROMPT_PATH
ARG ARG_UPLOAD_PATH

ENV AZURE_API_ENDPOINT=${ARG_AZURE_API_ENDPOINT:-your_azure_form_recognizer_endpoint}
ENV AZURE_API_KEY=${ARG_AZURE_API_KEY:-your_azure_form_recognizer_key}
ENV AZURE_OPENAI_DEPLOYMENT=${ARG_AZURE_OPENAI_DEPLOYMENT:-your_azure_openai_deployment}
ENV AZURE_OPENAI_ENDPOINT=${ARG_AZURE_OPENAI_ENDPOINT:-your_azure_openai_endpoint}
ENV AZURE_OPENAI_KEY=${ARG_AZURE_OPENAI_KEY:-your_azure_openai_key}
ENV FERTISCAN_STORAGE_URL=${ARG_FERTISCAN_STORAGE_URL:-your_fertiscan_storage_url}
ENV FERTISCAN_DB_URL=${ARG_FERTISCAN_DB_URL:-your_fertiscan_db_url}
ENV FERTISCAN_SCHEMA=${ARG_FERTISCAN_SCHEMA:-your_fertiscan_schema}
ENV ALLOWED_ORIGINS=${ARG_ALLOWED_ORIGINS:-["http://url.to_frontend/"]}
ENV PROMPT_PATH=${ARG_PROMPT_PATH:-path/to/file}
ENV UPLOAD_PATH=${ARG_UPLOAD_PATH:-path/to/file}

EXPOSE 5000

RUN chown -R 1000:1000 /app
RUN mkdir -p /cachedir_joblib && chown -R 1000:1000 /cachedir_joblib
RUN mkdir -p /.dspy_cache && chown -R 1000:1000 /.dspy_cache

USER 1000

CMD ["opentelemetry-instrument", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]
