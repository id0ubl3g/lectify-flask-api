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
- Automatic quiz generation from PDF/Markdown files or from a stored summary, cached per user
- 7-day retention for summaries and generated questions
- JWT-based authentication & refresh tokens
- Email verification, password reset & account deletion flows
- Profile management (including image upload via Cloudinary)
- Mercado Pago subscription integration (monthly, 6 months, yearly plans)
- MongoDB Atlas-based data persistence
- Redis Cloud caching and rate limiting

## Project Structure

```plaintext
└── lectify-flask-api/
    ├── .github/
    │   └── book-logo.png
    ├── config/
    │   ├── providers/
    │   │   ├── initialize_cloudinary.py
    │   │   ├── initialize_mercadopago.py
    │   │   ├── initialize_mongodb.py
    │   │   └── initialize_redis.py
    │   ├── file_config.py
    │   ├── input_config.py
    │   ├── limits_config.py
    │   ├── path_config.py
    │   └── prompt_config.py
    ├── src/
    │   ├── api/
    │   │   └── app.py
    │   ├── modules/
    │   │   ├── audio_downloader.py
    │   │   ├── audio_recognition.py
    │   │   ├── convert_document.py
    │   │   ├── document_builder.py
    │   │   ├── extract_text.py
    │   │   ├── retention.py
    │   │   ├── transcript_fetcher.py
    │   │   └── vertex_ai.py
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
    ├── install.sh
    ├── LICENSE
    ├── makefile
    ├── README.md
    ├── requirements.txt
    └── run.py
```

## Prerequisites

To run the Lectify Flask API, use Ubuntu 20.04, 22.04, or 24.04 (or a similar Debian-based system) with Python 3.10 or higher. The environment must include Docker and Docker Compose for containerized services, Redis Cloud for caching and rate limiting, MongoDB Atlas, RabbitMQ for asynchronous queue processing, FFmpeg for media processing, and internet access for external services such as AI APIs, email SMTP, Mercado Pago, Cloudinary, and Google Cloud services. Ensure all dependencies are properly installed before running the application.

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

## Environment Configuration

Configure environment variables

```sh
cp .env.example .env
```

Configure the required environment variables in `.env`, including:

- SECRET_KEY
- API keys (YouTube, Gemini, etc.)
- RabbitMQ user and password
- Email SMTP settings
- Mercado Pago keys
- MongoDB connection
- Redis Cloud configuration
- Cloudinary (for profile images)
Base URLs, etc.

Sensitive credentials should not be committed to the repository.

Vertex AI (summaries and quiz generation) and Speech-to-Text both authenticate with a Google Cloud service account.

Set the path where the credentials file lives. This is the only variable that points to it, and both the API and the worker read it:

```sh
GOOGLE_APPLICATION_CREDENTIALS=config/google_credentials.json
```

The file is written at startup from the `GOOGLE_*` variables in `.env`, so you do not need to place it there yourself. If those variables are absent, an existing file at that path is reused instead.

Vertex AI also requires the project and region:

```sh
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
```

## Running the Application

```sh
git clone https://github.com/id0ubl3g/lectify-flask-api
cd lectify-flask-api
chmod +x install.sh
make run
```

The `make run` command automatically sets up the virtual environment, installs dependencies, starts Docker services, launches the Flask API, and runs the Summarize Worker.

## API Documentation

### Endpoints

| Method   | Endpoint                             | Description                                                 |
| -------- | ------------------------------------ | ----------------------------------------------------------- |
| `GET`    | `/health`                            | Liveness probe. Returns service status. No authentication.  |
| `POST`   | `/lectify/summarize`                 | Generates a summary of a YouTube video in MD or PDF format. |
| `POST`   | `/lectify/check_summarize`           | Checks the status of a summarization request.               |
| `GET`    | `/lectify/summarize/files`           | List all summarized files of the current user.              |
| `GET`    | `/lectify/summarize/files/<file_id>` | Download a specific summarized file by ID.                  |
| `DELETE` | `/lectify/summarize/files/<file_id>` | Delete a summarized file and the questions generated from it. |
| `POST`   | `/lectify/questions`                 | Generates questions from an uploaded MD or PDF file, or from a stored summary via `file_id`. Cached results are returned without consuming quota. |
| `GET`    | `/lectify/questions`                 | List the quizzes of the current user, newest first, without the question payload. |
| `GET`    | `/lectify/questions/<question_id>`   | Return a single quiz with all its questions.                |
| `POST`   | `/lectify/check_email_register`      | Sends verification code via email for registration.         |
| `POST`   | `/lectify/verify_email_register`     | Verifies email code for registration.                       |
| `POST`   | `/lectify/register`                  | Registers a new user.                                       |
| `POST`   | `/lectify/login`                     | Logs in and returns JWT tokens.                             |
| `GET`    | `/lectify/profile`                   | Returns user profile data.                                  |
| `GET`    | `/lectify/usage`                     | Returns the current plan and its remaining quota per feature. |
| `POST`   | `/lectify/refresh_token`             | Refreshes access token using refresh token.                 |
| `PATCH`  | `/lectify/update_profile`            | Updates user profile (name or password).                    |
| `PUT`    | `/lectify/update_image_profile`      | Updates or removes user profile image.                      |
| `POST`   | `/lectify/ping_email_delete_account` | Sends verification link via email for account deletion.     |
| `DELETE` | `/lectify/pong_email_delete_account` | Verifies token and deletes user account.                    |
| `POST`   | `/lectify/ping_email_reset_password` | Sends password reset link via email.                        |
| `POST`   | `/lectify/pong_email_reset_password` | Verifies token and updates password.                        |
| `POST`   | `/lectify/checkout`                  | Creates checkout session for paid plan.              |
| `POST`   | `/lectify/webhook`                   | Mercado Pago webhook to process payments (internal).        |


### Data Retention

Summaries are kept for **7 days** from the moment they are generated, regardless of plan.
Questions inherit the expiry of the summary they were generated from, and questions
generated from an uploaded file get their own 7-day window. Users are expected to download
what they want to keep.

Expired data is removed by a purge that runs inside the summarize worker, at startup and
every 6 hours after that. Deletion is not handled by a MongoDB TTL index, because removing
a GridFS entry that way would leave its binary chunks orphaned. This means the purge only
runs while the worker is running.

Deleting a summary, either through `DELETE /lectify/summarize/files/<file_id>` or by
deleting the account, also removes the questions generated from it.

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

##### Responses Summarize:

- `201` — the request was queued. This is the only response that spends plan quota.
- `200` — the user already had this summary. Returns the file itself, spends no quota.
- `409` — this exact request is already being processed.
- `429` — quota or rate limit reached. Four of these within five minutes trigger a 30 minute block.

The API prepends `https://` to a URL that does not have it and stores the normalized value, so
normalize it on the client as well before looking the file up in `/lectify/summarize/files`. The
same video can be summarized in more than one format and language, so filter by `youtube_url`,
`filetype` and `language` before picking the newest entry.

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

A summarize request either returns the file straight away, when the user already has it, or
queues the job so it can be polled until it completes.

```ts
const API = `${process.env.NEXT_PUBLIC_BASE_URL}/lectify`;
const headers = { Authorization: `Bearer ${accessToken}` };

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

const normalizeUrl = (url: string) => (url.startsWith('https://') ? url : `https://${url}`);

export async function summarize(
  youtube_url: string,
  output_format: 'pdf' | 'md',
  language_select: 'pt-BR' | 'en-US' = 'pt-BR',
) {
  const body = { youtube_url: normalizeUrl(youtube_url), output_format, language_select };

  try {
    const res = await axios.post<Blob>(`${API}/summarize`, body, { headers, responseType: 'blob' });

    if (res.status === 200 && ['application/pdf', 'text/markdown'].includes(res.data.type)) {
      return { blob: res.data, consumedQuota: false };
    }
  } catch (error) {
    if (error.response?.status !== 409) throw error;
  }

  for (let attempt = 0; attempt < 60; attempt++) {
    await delay(10_000);

    const { data } = await axios.post(`${API}/check_summarize`, body, { headers });

    if (data.status === 'error') throw new Error('The summary could not be generated for this video.');
    if (data.status !== 'success') continue;

    const { data: files } = await axios.get(`${API}/summarize/files`, { headers });

    const file = files
      .filter(
        (f) =>
          f.youtube_url === body.youtube_url &&
          f.filetype === output_format &&
          f.language === language_select,
      )
      .sort((a, b) => +new Date(b.summary_at) - +new Date(a.summary_at))[0];

    const { data: blob } = await axios.get<Blob>(`${API}/summarize/files/${file.id}`, {
      headers,
      responseType: 'blob',
    });

    return { blob, file, consumedQuota: true };
  }

  throw new Error('The summary is taking longer than expected.');
}
```

## Acknowledgments

This project was developed in collaboration with [Francine Cruz](https://github.com/Francine02), who contributed to the frontend part. Her collaboration was essential in integrating the API with a modern interface, featuring dynamic animations, providing an optimized user experience.

The complete frontend implementation of the platform can be found in the repository: [https://github.com/Francine02/Lectify](https://github.com/Francine02/Lectify)

## License

This project is licensed under the terms of the [Apache License 2.0](http://www.apache.org/licenses/LICENSE-2.0). See the [LICENSE](./LICENSE) file for details.