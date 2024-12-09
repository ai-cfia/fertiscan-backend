FROM python:3.12-bullseye

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt
RUN opentelemetry-bootstrap --action=install

ARG ARG_AZURE_API_KEY
ARG ARG_AZURE_OPENAI_KEY
ARG ARG_FERTISCAN_STORAGE_URL
ARG ARG_FERTISCAN_DB_URL

ENV AZURE_API_KEY=${ARG_AZURE_API_KEY:-your_azure_form_recognizer_key}
ENV AZURE_OPENAI_KEY=${ARG_AZURE_OPENAI_KEY:-your_azure_openai_key}
ENV FERTISCAN_STORAGE_URL=${ARG_FERTISCAN_STORAGE_URL:-your_fertiscan_storage_url}
ENV FERTISCAN_DB_URL=${ARG_FERTISCAN_DB_URL:-your_fertiscan_db_url}

EXPOSE 5000

RUN chown -R 1000:1000 /app
RUN mkdir -p /cachedir_joblib && chown -R 1000:1000 /cachedir_joblib
RUN mkdir -p /.dspy_cache && chown -R 1000:1000 /.dspy_cache

USER 1000

CMD ["opentelemetry-instrument", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]
