# CONTRIBUTING

([_Le français est disponible au bas de la page_](#comment-contribuer))

Thank you for your interest in contributing to the FertiScan backend! Your
contributions help make this project better for everyone. This guide will help
you get started with contributing.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [How to Contribute](#how-to-contribute)
   - [Reporting Bugs](#reporting-bugs)
   - [Suggesting Enhancements](#suggesting-enhancements)
   - [Submitting Pull Requests](#submitting-pull-requests)
3. [Development Setup](#development-setup)
   - [Prerequisites](#prerequisites)
   - [Running Locally](#running-locally)
   - [Running with Docker](#running-with-docker)
   - [Environment Variables](#environment-variables)
4. [Style Guides](#style-guides)
   - [Python Style Guide](#python-style-guide)
   - [Git Commit Messages](#git-commit-messages)
5. [Additional Resources](#additional-resources)

## Code of Conduct

This project adheres to the [Code of
Conduct](https://www.canada.ca/fr/gouvernement/systeme/gouvernement-numerique/normes-numeriques-gouvernement-canada.html).
By participating, you are expected to uphold this code.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue and provide detailed information about
the bug, including steps to reproduce it, the expected behavior, and the actual
behavior.

### Suggesting Enhancements

We welcome suggestions for new features and enhancements. Please create an issue
to discuss your ideas and explain the benefits and potential use cases.

### Submitting Pull Requests

Follow the guidelines in
[dev-rel-docs](https://github.com/ai-cfia/dev-rel-docs/blob/main/TRAINING.md).

## Development Setup

### Prerequisites

- Python 3.11+
- [pip](https://pip.pypa.io/en/stable/installation/)
- [virtualenv](https://virtualenv.pypa.io/en/latest/installation.html)
- Azure Document Intelligence and OpenAI API keys

### Running Locally

1. Clone the repository:

   ```sh
   git clone https://github.com/ai-cfia/fertiscan-backend.git
   cd fertiscan-backend
   ```

2. Install dependencies:

   ```sh
   pip install -r requirements.txt
   ```

3. Start the server in development mode:

   ```sh
   fastapi dev app/main.py --port 5000
   ```

### Running with Docker

1. Build the Docker image:

   ```sh
   docker build -t fertiscan-backend \
   --build-arg ARG_AZURE_API_ENDPOINT=your_azure_form_recognizer_endpoint \
   --build-arg ARG_AZURE_API_KEY=your_azure_form_recognizer_key \
   --build-arg ARG_AZURE_OPENAI_API_ENDPOINT=your_azure_openai_endpoint \
   --build-arg ARG_AZURE_OPENAI_API_KEY=your_azure_openai_key \
   --build-arg ARG_PROMPT_PATH=path/to/prompt_file \
   --build-arg ARG_UPLOAD_PATH=path/to/upload_file \
   --build-arg ALLOWED_ORIGINS=["http://url.to_frontend/"] \
   .
   ```

2. Run the Docker container:

   ```sh
   docker run -p 5000:5000 fertiscan-backend
   ```

### Environment Variables

Create a `.env` file from `.env.secrets.template`:

```ini
AZURE_API_ENDPOINT=your_azure_form_recognizer_endpoint
AZURE_API_KEY=your_azure_form_recognizer_key
AZURE_OPENAI_API_ENDPOINT=your_azure_openai_endpoint
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_DEPLOYMENT=your_azure_openai_deployment

FERTISCAN_DB_URL=your_fertiscan_db_url
FERTISCAN_SCHEMA=your_fertiscan_schema

UPLOAD_PATH=path/to/file
ALLOWED_ORIGINS=["http://url.to_frontend/"]
```

## Style Guides

### Python Style Guide

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code.
- Use [black](https://github.com/psf/black) for code formatting.

### Git Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)
for writing commit messages.

## Additional Resources

- [Developer Documentation](./docs/README.md)

Thank you for contributing to FertiScan!

---

## Contributions

Merci de votre intérêt pour contribuer au backend de FertiScan ! Vos
contributions aident à améliorer ce projet pour tout le monde. Ce guide vous
aidera à commencer.

## Table des matières

1. [Code de conduite](#code-de-conduite)
2. [Comment contribuer](#comment-contribuer)
   - [Signaler des bugs](#signaler-des-bugs)
   - [Suggérer des améliorations](#suggérer-des-améliorations)
   - [Soumettre des Pull Requests](#soumettre-des-pull-requests)
3. [Configuration pour le développement](#configuration-pour-le-développement)
   - [Prérequis](#prérequis)
   - [Exécution locale](#exécution-locale)
   - [Exécution avec Docker](#exécution-avec-docker)
   - [Variables d'environnement](#variables-denvironnement)
4. [Guides de style](#guides-de-style)
   - [Guide de style Python](#guide-de-style-python)
   - [Messages de commit Git](#messages-de-commit-git)
5. [Ressources supplémentaires](#ressources-supplémentaires)

## Code de conduite

Ce projet adhère au [Code de
conduite](https://www.canada.ca/fr/gouvernement/systeme/gouvernement-numerique/normes-numeriques-gouvernement-canada.html).
En participant, vous vous engagez à respecter ce code.

## Comment contribuer

### Signaler des bugs

Si vous trouvez un bug, veuillez créer une issue et fournir des informations
détaillées sur le problème, y compris les étapes pour le reproduire, le
comportement attendu et le comportement réel.

### Suggérer des améliorations

Nous accueillons avec plaisir les suggestions pour de nouvelles fonctionnalités
et améliorations. Veuillez créer une issue pour discuter de vos idées et
expliquer les avantages et cas d'utilisation potentiels.

### Soumettre des Pull Requests

Suivez les directives dans
[dev-rel-docs](https://github.com/ai-cfia/dev-rel-docs/blob/main/TRAINING.md).

## Configuration pour le développement

### Prérequis

- Python 3.11+
- [pip](https://pip.pypa.io/en/stable/installation/)
- [virtualenv](https://virtualenv.pypa.io/en/latest/installation.html)
- Clés API Azure Document Intelligence et OpenAI

### Exécution locale

1. Clonez le dépôt :

   ```sh
   git clone https://github.com/ai-cfia/fertiscan-backend.git
   cd fertiscan-backend
   ```

2. Installez les dépendances :

   ```sh
   pip install -r requirements.txt
   ```

3. Lancez le serveur en mode développement :

   ```sh
   fastapi dev app/main.py --port 5000
   ```

### Exécution avec Docker

1. Construisez l'image Docker :

   ```sh
   docker build -t fertiscan-backend \
   --build-arg ARG_AZURE_API_ENDPOINT=your_azure_form_recognizer_endpoint \
   --build-arg ARG_AZURE_API_KEY=your_azure_form_recognizer_key \
   --build-arg ARG_AZURE_OPENAI_API_ENDPOINT=your_azure_openai_endpoint \
   --build-arg ARG_AZURE_OPENAI_API_KEY=your_azure_openai_key \
   --build-arg ARG_PROMPT_PATH=path/to/prompt_file \
   --build-arg ARG_UPLOAD_PATH=path/to/upload_file \
   --build-arg ALLOWED_ORIGINS=["http://url.to_frontend/"] \
   .
   ```

2. Lancez le conteneur Docker :

   ```sh
   docker run -p 5000:5000 fertiscan-backend
   ```

### Variables d'environnement

Créez un fichier `.env` à partir de `.env.secrets.template` :

```ini
AZURE_API_ENDPOINT=your_azure_form_recognizer_endpoint
AZURE_API_KEY=your_azure_form_recognizer_key
AZURE_OPENAI_API_ENDPOINT=your_azure_openai_endpoint
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_DEPLOYMENT=your_azure_openai_deployment

PROMPT_PATH=path/to/file
UPLOAD_PATH=path/to/file
ALLOWED_ORIGINS=["http://url.to_frontend/"]
```

## Guides de style

### Guide de style Python

- Suivez [PEP 8](https://www.python.org/dev/peps/pep-0008/) pour le code Python.
- Utilisez [black](https://github.com/psf/black) pour le formatage du code.

### Messages de commit Git

Suivez [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)
pour rédiger les messages de commit.

## Ressources supplémentaires

- [Documentation développeur](./docs/README.md)

Merci de contribuer à FertiScan !
