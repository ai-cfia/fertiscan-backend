# Developer Documentation

## Document Analysis Workflow

![workflow](../out/workflow_dss/FertiScan%20Sequence%20Diagram.png)

The `/analyze` route serves to:

- **Upload and Process Documents**: Allows clients to upload images of documents
 for analysis.
- **Extract and Structure Data**: Utilizes Azure Document Intelligence to
 extract text and layout information from the uploaded documents.
- **Generate Forms**: Uses OpenAI's GPT-4 to generate a structured JSON
 inspection containing all the necessary information extracted from the
 document.
- **Provide Responses**: Returns the generated inspection to the client,
 facilitating the inspection and validation processes by providing all relevant
 data in a structured format.

In essence, the `/analyze` route automates the extraction and structuring of
 data from documents, significantly simplifying the workflow for users who need
 to process and analyze document content.

## Deployment

![deployment](../out/deployment/Deployment.png)

### FertiScan Web

- **Description**: The user interface of the application.
- **Repository**: <https://github.com/ai-cfia/fertiscan-frontend/>

### FertiScan Server

- **Description**: The core backend service of the FertiScan system.
- **Repository**: <https://github.com/ai-cfia/fertiscan-backend/>

### FertiScan Pipeline

- **Description**: The core analysis pipeline for FertiScan
- **Repository**: <https://github.com/ai-cfia/fertiscan-pipeline/>

### Database

- **Description**: The database where the information on fertiliser and labels
 is stored.
- **Repository**: <https://github.com/ai-cfia/ailab-datastore/>

## API Endpoints

The [Swagger UI](https://swagger.io/tools/swagger-ui/) for the API of FertiScan
is available at docs.

v1.0.0

## Instrumentation

For monitoring and logging, refer to the [following
documentation.](./otel/README.md)
