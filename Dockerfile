FROM python:3.11-slim

RUN groupadd -r fertiscangroup && useradd -r -g fertiscangroup fertiscanuser 

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
ARG ARG_PROMPT_PATH
ARG ARG_UPLOAD_PATH
ARG ARG_FRONTEND_URL

ENV AZURE_API_ENDPOINT=${ARG_AZURE_API_ENDPOINT:-your_azure_form_recognizer_endpoint}
ENV AZURE_API_KEY=${ARG_AZURE_API_KEY:-your_azure_form_recognizer_key}
ENV AZURE_OPENAI_API_ENDPOINT=${ARG_AZURE_OPENAI_API_ENDPOINT:-your_azure_openai_endpoint}
ENV AZURE_OPENAI_API_KEY=${ARG_AZURE_OPENAI_API_KEY:-your_azure_openai_key}
ENV PROMPT_PATH=${ARG_PROMPT_PATH:-path/to/file}
ENV UPLOAD_PATH=${ARG_UPLOAD_PATH:-path/to/file}
ENV FRONTEND_URL=${FRONTEND_URL:-http://url.to_frontend/}

EXPOSE 5000

RUN chown -R fertiscanuser:fertiscangroup /app

USER fertiscanuser

CMD ["python", "app.py"]
