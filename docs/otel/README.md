# OpenTelemetry Instrumentation

([*Le français est disponible au bas de la
page*](#instrumentation-avec-opentelemetry))

The application is instrumented with
[OpenTelemetry](https://opentelemetry.io/docs/what-is-opentelemetry/) to collect
traces and logs. This setup uses **programmatic instrumentation**, providing
control over how OpenTelemetry is initialized and avoiding potential issues with
zero-code instrumentation. This allows us to send traces and logs from FastAPI
endpoints to an OpenTelemetry collector. The traces and logs can be routed to
[Alloy](https://grafana.com/docs/alloy/latest/) (centralized receiver for logs
and traces sent to Loki and Tempo) or
[Phoenix](https://github.com/Arize-ai/phoenix) (AI observability platform) based
on the configuration.

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

### Phoenix Trace Routing

To enable **Phoenix** as the trace receiver, set the `PHOENIX_ENDPOINT`
environment variable to `http://phoenix:6006/v1/traces`. When this variable is
set, traces are routed to Phoenix; otherwise, the traces will default to
**Alloy-Tempo** instance.

- **Phoenix enabled (default in `docker-compose.yml`)**: Traces are sent to
  Phoenix.
- **Phoenix disabled (remove or comment `PHOENIX_ENDPOINT`)**: Traces route to
  Alloy’s Tempo instance.

### Docker Compose Configuration

The `docker-compose.yml` emulates our production environment, with the
OpenTelemetry collector and related components configured to handle and display
telemetry data. Phoenix’s configuration is included to provide additional AI
observability, dataset versioning, and evaluation functionalities.

You will notice that some services are configured with custom images from our
Docker registry. This is because we have built custom images for these services
to streamline configuration and prevent misconfiguration. Their respective
Dockerfiles can be found in the
[Devops](https://github.com/ai-cfia/devops/tree/main/dockerfiles) repository.

## Running the Application

To start the application and associated services, use the following command:

```bash
# Make sure you run `--build` once, then you can omit it.
docker-compose up --build -d
```

### Accessing Monitoring Tools

After deploying the stack, you can access the following tools for monitoring and
debugging:

- **Grafana (for visualization)**: Visit `http://localhost:3001` and configure
  Grafana to use Tempo and Loki as data sources.
- **Phoenix (for AI observability)**: Visit `http://localhost:6006` to view
  trace data, datasets, and experiment tracking.
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
behavior across services, with optional AI observability through Phoenix.

---

## Instrumentation avec OpenTelemetry

L'application est instrumentée avec
[OpenTelemetry](https://opentelemetry.io/docs/what-is-opentelemetry/) pour
collecter les traces et les journaux. Cette configuration utilise
**l'instrumentation programmatique**, offrant un contrôle précis sur
l'initialisation d'OpenTelemetry et évitant les problèmes potentiels liés à
l'instrumentation sans code. Cela permet d'envoyer les traces et journaux des
points de terminaison FastAPI à un collecteur OpenTelemetry. Les traces et
journaux peuvent ensuite être acheminés vers
[Alloy](https://grafana.com/docs/alloy/latest/) (récepteur centralisé pour les
journaux et traces envoyés à Loki et Tempo) ou
[Phoenix](https://github.com/Arize-ai/phoenix) (plateforme d'observabilité pour
l'IA) en fonction de la configuration.

## Configuration et instrumentation

### Code de l'application FastAPI

Le code ci-dessous montre comment nous configurons, dans `app/config.py`, la
traçabilité et les journaux pour le service `fertiscan-backend` en utilisant
OpenTelemetry. Cette configuration utilise le paramètre `lifespan` de FastAPI,
un gestionnaire de contexte permettant une configuration et un arrêt contrôlés
des ressources (dans ce cas, les fournisseurs de journaux et de traces
d'OpenTelemetry).

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

    # Configuration de la traçabilité
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=c.OTEL_EXPORTER_OTLP_ENDPOINT, insecure=True))
    )
    # Configuration de la journalisation
    logger_provider = LoggerProvider(resource=resource)
    set_logger_provider(logger_provider)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(OTLPLogExporter(endpoint=c.OTEL_EXPORTER_OTLP_ENDPOINT, insecure=True))
    )
    handler = LoggingHandler(logging.NOTSET, logger_provider=logger_provider)
    logger.addHandler(handler)

    # # Retourner le contrôle à FastAPI, indiquant la fin de la configuration
    yield

    [...]

    # Arrêter les fournisseurs de journalisation et de traçabilité
    logger_provider.shutdown()
    tracer_provider.shutdown()
```

Dans ce code:

1. **Attributs de ressources** : `service.name` est défini comme
   "fertiscan-backend" pour taguer les journaux et les traces provenant de ce
   service.
2. **Configuration de la traçabilité** : `TracerProvider` est configuré avec un
   `OTLPSpanExporter` pour envoyer les traces à Alloy sur `http://alloy:4317`.
3. **Configuration de la journalisation** : `LoggerProvider` avec
   `OTLPLogExporter` exporte les journaux vers Alloy au même endpoint.
4. **Gestionnaire de journalisation** : Le `LoggingHandler` s'attache au module
   `logger` de FastAPI, garantissant que tous les journaux sont traités par le
   fournisseur OpenTelemetry.

### Routage des traces vers Phoenix

Pour activer **Phoenix** comme récepteur de traces, définissez la variable
d'environnement `PHOENIX_ENDPOINT` à `http://phoenix:6006/v1/traces`. Si cette
variable est définie, les traces sont routées vers Phoenix ; sinon, elles sont
redirigées par défaut vers l'instance **Alloy-Tempo**.

- **Phoenix activé (par défaut dans `docker-compose.yml`)** : Les traces sont
  envoyées à Phoenix.
- **Phoenix désactivé (supprimez ou commentez `PHOENIX_ENDPOINT`)** : Les traces
  sont redirigées vers l'instance Tempo d'Alloy.

### Configuration Docker Compose

Le fichier `docker-compose.yml` émule notre environnement de production avec le
collecteur OpenTelemetry et les composants associés configurés pour gérer et
afficher les données de télémétrie. La configuration de Phoenix est incluse pour
fournir des fonctionnalités supplémentaires d'observabilité pour l'IA, de
versionnage de datasets, et d'évaluation.

Certains services utilisent des images personnalisées issues de notre registre
Docker. Cela permet d'optimiser la configuration et d'éviter les erreurs. Les
Dockerfiles correspondants sont disponibles dans le dépôt
[Devops](https://github.com/ai-cfia/devops/tree/main/dockerfiles).

## Exécution de l'application

Pour démarrer l'application et les services associés, utilisez la commande
suivante :

```bash
# Assurez-vous d'exécuter `--build` une fois, ensuite vous pouvez l'omettre.
docker-compose up --build -d
```

### Accéder aux outils de surveillance

Après avoir déployé la stack, vous pouvez accéder aux outils suivants pour la
surveillance et le débogage :

- **Grafana (pour la visualisation)** : Rendez-vous sur `http://localhost:3001`
  et configurez Grafana pour utiliser Tempo et Loki comme sources de données.
- **Phoenix (pour l'observabilité de l'IA)** : Rendez-vous sur
  `http://localhost:6006` pour consulter les données de traces, les datasets et
  le suivi des expériences.
- **Prometheus (pour les métriques)** : Accessible à `http://localhost:9090`.
- **pgAdmin (pour la gestion des bases de données)** : Accessible à
  `http://localhost:5050`.

### Configuration des sources de données dans Grafana

1. **Loki** : Ajoutez Loki comme source de données dans Grafana pour la
   visualisation des journaux. Utilisez `http://loki:3100` comme URL de la
   source de données.
2. **Tempo** : Ajoutez Tempo comme source de données pour la visualisation des
   traces, en utilisant `http://tempo:3200` comme URL.
3. **Prometheus (optionnel)** : Connectez Prometheus à Grafana pour les
   métriques en pointant vers `http://prometheus:9090`.

Cette configuration garantit que les journaux, traces et métriques sont
correctement collectés et visualisés, offrant une vue complète des performances
et du comportement de l'application à travers les services.
