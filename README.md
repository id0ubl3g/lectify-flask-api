# Lectify Flask API

<!-- markdownlint-disable MD033 -->

<div align="center">
  <img src=".github/book-logo.png" alt="Robot Logo" width="130">
  <h1><b>Lectify Flask API</b></h1>
  <p>AI-powered Flask API to summarize video lectures with detailed insights. </p>
  <p>
    <img src="https://img.shields.io/github/last-commit/id0ubl3g/lectify-flask-api?style=flat&logo=git&logoColor=white&color=0080ff" alt="Last Commit">
    <img src="https://img.shields.io/github/languages/top/id0ubl3g/lectify-flask-api?style=flat&color=0080ff" alt="Top Language">
    <img src="https://img.shields.io/github/languages/count/id0ubl3g/lectify-flask-api?style=flat&color=0080ff" alt="Languages Count">
  </p>
</div>

<!-- markdownlint-enable MD033 -->

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Manual Installation (Ubuntu/Debian)](#manual-installation-ubuntudebian)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Endpoints](#endpoints)
- [Core Endpoints](#core-endpoints)
  - [Lectify Summarize Endpoint](#lectify-summarize-endpoint)
  - [Lectify Check Summarize Endpoint](#lectify-check-summarize-endpoint)
- [Example Use Case](#example-use-case)
  - [Frontend Integration Summarize](#frontend-integration-summarize)
- [Acknowledgments](#acknowledgments)
- [License](#license)

## Overview

The Lectify Flask API is a web application developed with Flask, designed to summarize video lectures with detailed insights and generate quiz questions from the provided document. It offers a comprehensive tool for educators and learners to extract key information and test understanding through automatic question generation.

## Features

- YouTube video transcription + AI summarization (supports pt-BR and en-US)
- RabbitMQ-based asynchronous summarize processing
- Automatic quiz generation from PDF/Markdown files
- JWT-based authentication & refresh tokens
- Email verification, password reset & account deletion flows
- Profile management (including image upload via Cloudinary)
- Stripe subscription integration (monthly, 6 months, yearly plans)
- Rate limiting & Redis caching
- Interactive API docs with Flasgger

## Project Structure

```plaintext
└── lectify-flask-api/
  ├── .github
  │ ├── robot-logo.png
  ├── config/
  │     └── providers/
  │       ├── initialize_cloudinary.py
  │       ├── initialize_mongodb.py
  │       ├── initialize_redis.py
  │       └── initialize_stripe.py
  │   ├── file_config.py
  │   ├── input_config.py
  │   ├── path_config.py
  │   ├── prompt_config.py
  ├── docs/
  │   └── flasgger.py
  ├── src/
  │   ├── api/
  │   │   └── app.py
  │   ├── modules/
  │   │   ├── audio_downloader.py
  │   │   ├── audio_recognition.py
  │   │   ├── convert_document.py
  │   │   ├── document_builder.py
  │   │   ├── extract_text.py
  │   │   └── generative_ai.py
  │   ├── rabbitmq/
  │   │   ├── connection.py
  │   │   └── publisher.py
  │   ├── utils/
  │   │   ├── return_responses.py
  │   │   ├── send_email_verification.py
  │   │   └── system_utils.py
  │   └── workers/
  │       └── summarize_worker.py
  ├── .dockerignore
  ├── .env.example
  ├── .gitignore
  ├── docker-compose.yml
  ├── LICENSE
  ├── README.md
  ├── requirements.txt
  ├── run.py
  └── start.sh
```

## Prerequisites

To run the Lectify Flask API, use Ubuntu 20.04, 22.04, or 24.04 (or a similar Debian-based system) with Python 3.10 or higher. The environment must include Docker and Docker Compose for containerized services, Redis for caching and rate limiting, RabbitMQ for asynchronous queue processing, FFmpeg for media processing, and internet access for external services such as AI APIs, email SMTP, Stripe, Cloudinary, and Google Cloud services. Ensure all dependencies are properly installed before running the application.

### Manual Installation (Ubuntu/Debian)

Update system & install base dependencies

```sh
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
    python3 python3-venv python3-pip git ffmpeg \
    libmagic1 file libglib2.0-dev libpango1.0-dev \
    libpangocairo-1.0-0 libcairo2 libffi-dev shared-mime-info
```

### Install Docker

Follow the official Docker installation guide:

[https://docs.docker.com/engine/install/](https://docs.docker.com/engine/install/)

Configure environment variables

```sh
cp .env.example .env
```

Edit .env (use nano .env or your editor) and fill in:

- SECRET_KEY
- API keys (YouTube, Gemini, etc.)
- RabbitMQ user and password
- Email SMTP settings
- Stripe keys
- MongoDB connection
- Cloudinary (for profile images)
Base URLs, etc.

To enable the Speech-to-Text feature, it is required to configure the Google Cloud service account JSON file.

Place the file inside the config/ directory:

```plaintext
config/google_credentials.json
```

Then set the environment variable pointing to this file:

```sh
path_google_application_credentials_json=config/google_credentials.json
```

## Running the Application

```sh
git clone https://github.com/id0ubl3g/lectify-flask-api
cd lectify-flask-api
chmod +x start.sh
./start.sh
```

The `start.sh` script automatically handles virtual environment, dependencies installation, Docker services, Flask API and the Summarize Worker.

## API Documentation

The Lectify Flask API includes interactive documentation powered by Flasgger. You can explore each endpoint, view parameter details, and test API requests directly from the browser.

Interactive API Documentation: [http://127.0.0.1:5000/apidocs/](http://127.0.0.1:5000/apidocs/)

### Endpoints

| Method   | Endpoint                             | Description                                                 |
| -------- | ------------------------------------ | ----------------------------------------------------------- |
| `POST`   | `/lectify/summarize`                 | Generates a summary of a YouTube video in MD or PDF format. |
| `POST`   | `/lectify/check_summarize`           | Checks the status of a summarization request.               |
| `POST`   | `/lectify/questions`                 | Generates questions from an MD or PDF file.                 |
| `POST`   | `/lectify/check_email_register`      | Sends verification code via email for registration.         |
| `POST`   | `/lectify/verify_email_register`     | Verifies email code for registration.                       |
| `POST`   | `/lectify/register`                  | Registers a new user.                                       |
| `POST`   | `/lectify/login`                     | Logs in and returns JWT tokens.                             |
| `GET`    | `/lectify/profile`                   | Returns user profile data.                                  |
| `POST`   | `/lectify/refresh_token`             | Refreshes access token using refresh token.                 |
| `PATCH`  | `/lectify/update_profile`            | Updates user profile (name or password).                    |
| `PUT`    | `/lectify/update_image_profile`      | Updates or removes user profile image.                      |
| `POST`   | `/lectify/ping_email_delete_account` | Sends verification link via email for account deletion.     |
| `DELETE` | `/lectify/pong_email_delete_account` | Verifies token and deletes user account.                    |
| `POST`   | `/lectify/ping_email_reset_password` | Sends password reset link via email.                        |
| `POST`   | `/lectify/pong_email_reset_password` | Verifies token and updates password.                        |
| `POST`   | `/lectify/checkout`                  | Creates Stripe checkout session for paid plans.             |
| `POST`   | `/lectify/webhook`                   | Stripe webhook to process payments internally.              |


### Core Endpoints

#### Lectify Summarize Endpoint

- **URL**: `/lectify/summarize`
- **Method**: `POST`
- **Description**: Generates a summary of a YouTube video in MD or PDF format.
- **Security**: Requires JWT Bearer token in Authorization header.

##### Request Body Summarize:

- **Content-Type**: `application/json`
- **Request Fields**:
  - `youtube_url`: YouTube video URL (required).
    - Type: `String`
    - **Example**: `https://www.youtube.com/watch?v=iuPrkzJp20I`
  - `output_format`: Desired output format (required).
    - Type: `String`
    - **Supported Formats**: `md`, `pdf`
    - **Example**: `pdf`
  - `language_select`: Language for recognition and summarization (required).
    - Type: `String`
    - **Supported Languages**: `pt-BR`, `en-US`
    - **Example**: `pt-BR`

###### Example Request Summarize

```sh
curl -X POST "http://127.0.0.1:5000/lectify/summarize" \
-H "Content-Type: application/json" \
-H "Authorization: Bearer {token}" \
-d '{"youtube_url": "https://www.youtube.com/watch?v=iuPrkzJp20I", "output_format": "pdf", "language_select": "pt-BR"}'
```

#### Lectify Check Summarize Endpoint

* **URL**: `/lectify/check_summarize`
* **Method**: `POST`
* **Description**: Checks the status of a summarize request in the processing queue.
* **Security**: Requires JWT Bearer token in Authorization header.

##### Request Body Check Summarize:

* **Content-Type**: `application/json`
* **Request Fields**:
  - `youtube_url`: YouTube video URL (required).
    - Type: `String`
    - **Example**: `https://www.youtube.com/watch?v=iuPrkzJp20I`
  - `output_format`: Desired output format (required).
    - Type: `String`
    - **Supported Formats**: `md`, `pdf`
    - **Example**: `pdf`
  - `language_select`: Language used during summarization (required).
    - Type: `String`
    - **Supported Languages**: `pt-BR`, `en-US`
    - **Example**: `pt-BR`

###### Example Request Check Summarize

```sh
curl -X POST "http://127.0.0.1:5000/lectify/check_summarize" \
-H "Content-Type: application/json" \
-H "Authorization: Bearer {token}" \
-d '{"youtube_url": "https://www.youtube.com/watch?v=iuPrkzJp20I", "output_format": "pdf", "language_select": "pt-BR"}'
```

### Example Use Case

#### Frontend Integration Summarize

```ts

```

## Acknowledgments

This project was developed in collaboration with [Francine Cruz](https://github.com/Francine02), who contributed to the frontend part. Her collaboration was essential in integrating the API with a modern interface, featuring dynamic animations, providing an optimized user experience.

The complete frontend implementation of the platform can be found in the repository: [https://github.com/Francine02/Lectify](https://github.com/Francine02/Lectify)

## License

This project is licensed under the terms of the [Apache License 2.0](http://www.apache.org/licenses/LICENSE-2.0). See the [LICENSE](./LICENSE) file for details.