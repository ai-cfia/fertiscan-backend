FROM python:3.10

WORKDIR /app

COPY . .

# Install git (required for opentelemetry-instrumentation-aiohttp-server installation)
RUN apt-get install -y git

RUN pip install --no-cache-dir -r requirements.txt
RUN opentelemetry-bootstrap -a install

ARG ARG_AZURE_API_ENDPOINT
ARG ARG_AZURE_API_KEY
ARG ARG_AZURE_OPENAI_ENDPOINT
ARG ARG_AZURE_OPENAI_KEY
ARG ARG_PROMPT_PATH
ARG ARG_UPLOAD_PATH
ARG ARG_FRONTEND_URL
ARG ARG_OTEL_EXPORTER_OTLP_TRACES_ENDPOINT

# Application env variables
ENV AZURE_API_ENDPOINT=${ARG_AZURE_API_ENDPOINT:-your_azure_form_recognizer_endpoint}
ENV AZURE_API_KEY=${ARG_AZURE_API_KEY:-your_azure_form_recognizer_key}
ENV AZURE_OPENAI_ENDPOINT=${ARG_AZURE_OPENAI_ENDPOINT:-your_azure_openai_endpoint}
ENV AZURE_OPENAI_KEY=${ARG_AZURE_OPENAI_KEY:-your_azure_openai_key}
ENV PROMPT_PATH=${ARG_PROMPT_PATH:-path/to/file}
ENV UPLOAD_PATH=${ARG_UPLOAD_PATH:-path/to/file}
ENV FRONTEND_URL=${FRONTEND_URL:-http://url.to_frontend/}

# OTEL env variables
ENV OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true
ENV OTEL_SERVICE_NAME=fertiscan-backend
ENV OTEL_TRACES_EXPORTER=console,otlp
ENV OTEL_METRICS_EXPORTER=console,otlp
ENV OTEL_LOGS_EXPORTER=console,otlp
ENV OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=${OTEL_EXPORTER_OTLP_TRACES_ENDPOINT:-0.0.0.0:4317}

EXPOSE 5000

CMD ["opentelemetry-instrument", "python", "app.py"]
