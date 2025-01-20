FROM python:3.12-bullseye

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt
RUN opentelemetry-bootstrap --action=install

EXPOSE 5000

RUN chown -R 1000:1000 /app
RUN mkdir -p /cachedir_joblib && chown -R 1000:1000 /cachedir_joblib
RUN mkdir -p /.dspy_cache && chown -R 1000:1000 /.dspy_cache

USER 1000

CMD ["opentelemetry-instrument", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]
