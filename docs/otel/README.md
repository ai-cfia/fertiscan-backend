# OpenTelemetry Instrumentation

The application is instrumented with
[OpenTelemetry](https://opentelemetry.io/docs/what-is-opentelemetry/) to collect
traces and logs. This setup uses **programmatic instrumentation**, providing
control over how OpenTelemetry is initialized and avoiding potential issues with
zero-code instrumentation. This allows us to send traces and logs from FastAPI
endpoints to an OpenTelemetry collector, where
[Alloy](https://grafana.com/docs/alloy/latest/) acts as the centralized
receiver, forwarding logs to Loki and traces to Tempo.

---

## Configuration and Instrumentation

### FastAPI Application Code

The code below demonstrates how we set up in `app/config.py` tracing and logging
in the `fertiscan-backend` service using OpenTelemetry. This configuration uses
FastAPI's `lifespan` parameter, a context manager that allows controlled setup
and shutdown of resources (in this case, OpenTelemetry's logging and tracing
providers).

```python
from contextlib import asynccontextmanager

[...]

from opentelemetry import trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

@asynccontextmanager
async def lifespan(app: FastAPI):
   [...]

    resource = Resource.create(
        {
            "service.name": "fertiscan-backend",
        }
    )

    # Tracing setup
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=c.OTEL_EXPORTER_OTLP_ENDPOINT, insecure=True))
    )
    # Logging setup
    logger_provider = LoggerProvider(resource=resource)
    set_logger_provider(logger_provider)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(OTLPLogExporter(endpoint=c.OTEL_EXPORTER_OTLP_ENDPOINT, insecure=True))
    )
    handler = LoggingHandler(logging.NOTSET, logger_provider=logger_provider)
    logger.addHandler(handler)

    # Yield control back to FastAPI, indicating setup completion
    yield

    [...]

    # Shutdown the logging and tracing providers
    logger_provider.shutdown()
    tracer_provider.shutdown()
```

In this code:

1. **Resource Attributes**: `service.name` is set as "fertiscan-backend" to tag
   logs and traces from this service.
2. **Tracing Configuration**: `TracerProvider` is set with an `OTLPSpanExporter`
   to send traces to Alloy at `http://alloy:4317`.
3. **Logging Configuration**: `LoggerProvider` with `OTLPLogExporter` exports
   logs to Alloy at the same endpoint.
4. **Logging Handler**: The `LoggingHandler` attaches to FastAPI’s `logger`
   module, ensuring all logs are processed by OpenTelemetry's provider.

### Docker Compose Configuration

The `docker-compose.yml` emulates our production environment, with the
OpenTelemetry collector and related components configured to handle and display
telemetry data.

You will notice that some services are configured with custom image from our
Docker registry. This is because we have built custom images for these services
with their respective configuration as mean to prevent any misconfiguration and
cluttering the current repository. Their respective Dockerfiles can be found in
the repository
[Devops](https://github.com/ai-cfia/devops/tree/main/dockerfiles).

## Running the Application

To start the application and associated services, use the following command:

```bash
# Make sure you run `--build` once. then yoy can omit it.
docker-compose up --build -d
```

### Accessing Monitoring Tools

After deploying the stack, you can access the following tools for monitoring and
debugging:

- **Grafana (for visualization)**: Visit `http://localhost:3001` and configure
  Grafana to use Tempo and Loki as data sources.
- **Prometheus (for metrics)**: Accessible at `http://localhost:9090`.
- **pgAdmin (for database management)**: Accessible at `http://localhost:5050`.

### Connecting Data Sources in Grafana

1. **Loki**: Add Loki as a data source in Grafana for log visualization. Point
   to `http://loki:3100` as the data source URL.
2. **Tempo**: Add Tempo as a data source for trace visualization, using
   `http://tempo:3200` as the URL.
3. **Prometheus (Optional)**: Connect Prometheus to Grafana for metrics by
   pointing to `http://prometheus:9090`.

This setup ensures that logs, traces, and metrics are correctly collected and
visualized, providing a comprehensive view of application performance and
behavior across services.