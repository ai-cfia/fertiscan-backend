# CONTRIBUTING.md

Thank you for your interest in contributing to the FertiScan backend project!
 Your contributions help make this project better for everyone.
 This guide will help you get started with contributing.

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

This project adheres to the ~~Contributor Covenant~~ Code of Conduct.
 By participating, you are expected to uphold this code.
  Please report any unacceptable behavior to [insert contact email].

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue and provide detailed information about the bug,
 including steps to reproduce it, the expected behavior, and the actual behavior.

### Suggesting Enhancements

We welcome suggestions for new features and enhancements.
 Please create an issue to discuss your ideas and explain the benefits and potential use cases.

### Submitting Pull Requests

Follow the guidelines in [dev-rel-docs](https://github.com/ai-cfia/dev-rel-docs/blob/main/TRAINING.md).

## Development Setup

### Prerequisites

- Python 3.8+
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

3. Start the server:

    ```sh
    python ./app.py
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
    --build-arg ARG_FRONTEND_URL=http://url.to_frontend/ \
    .
    ```

2. Run the Docker container:

    ```sh
    docker run -p 5000:5000 fertiscan-backend
    ```

### Environment Variables

Create a `.env` file from `.env.template`:

```ini
AZURE_API_ENDPOINT=your_azure_form_recognizer_endpoint
AZURE_API_KEY=your_azure_form_recognizer_key
AZURE_OPENAI_API_ENDPOINT=your_azure_openai_endpoint
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_DEPLOYMENT=your_azure_openai_deployment

PROMPT_PATH=path/to/file
UPLOAD_PATH=path/to/file
FRONTEND_URL=http://url.to_frontend/
```

## Style Guides

### Python Style Guide

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code.
- Use [black](https://github.com/psf/black) for code formatting.

### Git Commit Messages

Follow the [conventional commit](https://www.conventionalcommits.org/en/v1.0.0/) specification.

## Additional Resources

- [API Endpoints](./docs/swagger)
- [Developer Documentation](./docs/README.md)

Thank you for contributing to FertiScan!
