# Developer Documentation

## Document Analysis Workflow

![workflow](../out/workflow_dss/FertiScan%20Sequence%20Diagram.png)

The `/analyze` route serves to:

- **Upload and Process Documents**: Allows clients to upload
 images of documents for analysis.
- **Extract and Structure Data**: Utilizes Azure Document Intelligence to
 extract text and layout information from the uploaded documents.
- **Generate Forms**: Uses OpenAI's GPT-4 to generate a structured JSON
 form containing all the necessary information extracted from the document.
- **Provide Responses**: Returns the generated form to the client,
 facilitating the inspection and validation processes
 by providing all relevant data in a structured format.

In essence, the `/analyze` route automates the
 extraction and structuring of data from documents, significantly
 simplifying the workflow for
 users who need to process and analyze document content.

## Deployment

![deployment](../out/deployment/Deployment.png)

### FertiScan Web

- **Description**: The user interface of the application.
- **Repository**: <https://github.com/ai-cfia/fertiscan-frontend/>

### FertiScan Server

- **Description**: The core backend service of the FertiScan system.
- **Repository**: <https://github.com/ai-cfia/fertiscan-backend/>

### Database

- **Description**: The database where the
 information on fertiliser and labels is stored.
- **Repository**: <https://github.com/ai-cfia/nachet-datastore/>

## API Endpoints

### `POST /analyze`

Upload images for analysis and get the results as a JSON form.

![analyze](../out/analyze_dss/Analyze%20DSS.png)

### `POST /forms`

Create a new form and add it to the database.

![create](../out/create_form_dss/FertiScan%20Sequence%20Diagram.png)

### `PUT /forms`

Send the latest state of a form to the database.

![submit](../out/submit_form_dss/FertiScan%20Sequence%20Diagram.png)

### `DELETE /forms`

Remove all transient states of a form.

![discard](../out/discard_form_dss/FertiScan%20Sequence%20Diagram.png)

### `GET /forms`

Retrieve the latest state of a form from the database.

![get](../out/get_form_dss/FertiScan%20Sequence%20Diagram.png)
