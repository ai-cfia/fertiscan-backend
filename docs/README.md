# Developer Documentation

([*Le français est disponible au bas de la
page*](#documentation-pour-développeurs-euses))

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

- **Description**: The core analysis pipeline for FertiScan.
- **Repository**: <https://github.com/ai-cfia/fertiscan-pipeline/>

### Database

- **Description**: The database where the information on fertiliser and labels.
 is stored.
- **Repository**: <https://github.com/ai-cfia/ailab-datastore/>

## API Endpoints

The [Swagger UI](https://swagger.io/tools/swagger-ui/) for the API of FertiScan
is available at `/docs`.

v1.0.0

## Instrumentation

For monitoring and logging, refer to the [following
documentation.](./otel/README.md)

--- 

## Documentation pour développeurs-euses

## Workflow pour l'analyse des documents

![workflow](../out/workflow_dss/FertiScan%20Sequence%20Diagram.png)

La route `/analyze` sert à :

- **Téléverser et traiter des documents** : Permet aux clients de téléverser des
  images de documents pour analyse.
- **Extraire et structurer les données** : Utilise Azure Document Intelligence
  pour extraire le texte et les informations de mise en page des documents
  téléversés.
- **Générer des formulaires** : Utilise GPT-4 d'OpenAI pour générer un fichier
  JSON structuré contenant toutes les informations nécessaires extraites du
  document.
- **Fournir des réponses** : Renvoie l'inspection générée au client, facilitant
  les processus d'inspection et de validation en fournissant toutes les données
  pertinentes dans un format structuré.

En résumé, la route `/analyze` automatise l'extraction et la structuration des
données à partir des documents, simplifiant considérablement le flux de travail
pour les utilisateurs devant traiter et analyser le contenu de documents.

## Déploiement

![deployment](../out/deployment/Deployment.png)

### FertiScan Web

- **Description** : L'interface utilisateur de l'application.
- **Dépôt** : <https://github.com/ai-cfia/fertiscan-frontend/>

### FertiScan Serveur

- **Description** : Le service backend principal du système FertiScan.
- **Dépôt** : <https://github.com/ai-cfia/fertiscan-backend/>

### Base de données

- **Description** : La base de données où sont stockées les informations sur les
  engrais et les étiquettes.
- **Dépôt** : <https://github.com/ai-cfia/ailab-datastore/>

## Points de terminaison de l'API

L'[interface Swagger UI](https://swagger.io/tools/swagger-ui/) pour l'API de
FertiScan est disponible à l'adresse `/docs`.

v1.0.0

## Instrumentation

Pour la surveillance et la journalisation, consultez la [documentation
suivante.](./otel/README.md)
