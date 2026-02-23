# Lectify Flask API

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

## Table of Contents
- [Overview](#overview)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setting Up Docker](#setting-up-docker)
- [Build and Run with Docker Compose](#build-and-run-with-docker-compose)
- [API Documentation](#api-documentation)
- [API Endpoints](#api-endpoints)
  - [1. Lectify Summarize Endpoint](#1-lectify-summarize-endpoint)
  - [2. Lectify Questions Endpoint](#2-lectify-questions-endpoint)
  - [3. Check Email Register Endpoint](#3-check-email-register-endpoint)
  - [4. Verify Email Register Endpoint](#4-verify-email-register-endpoint)
  - [5. Register Endpoint](#5-register-endpoint)
  - [6. Login Endpoint](#6-login-endpoint)
  - [7. Profile Endpoint](#7-profile-endpoint)
  - [8. Refresh Token Endpoint](#8-refresh-token-endpoint)
  - [9. Update Profile Endpoint](#9-update-profile-endpoint)
  - [10. Update Image Profile Endpoint](#10-update-image-profile-endpoint)
  - [11. Ping Email Delete Account Endpoint](#11-ping-email-delete-account-endpoint)
  - [12. Pong Email Delete Account Endpoint](#12-pong-email-delete-account-endpoint)
  - [13. Ping Email Reset Password Endpoint](#13-ping-email-reset-password-endpoint)
  - [14. Pong Email Reset Password Endpoint](#14-pong-email-reset-password-endpoint)
  - [15. Checkout Endpoint](#15-checkout-endpoint)
  - [16. Webhook Endpoint](#16-webhook-endpoint)
- [Example Use Case](#example-use-case)
- [Acknowledgments](#acknowledgments)
- [License](#license)

## Overview
The Lectify Flask API is a web application developed with Flask, designed to summarize video lectures with detailed insights and generate quiz questions from the provided document. It offers a comprehensive tool for educators and learners to extract key information and test understanding through automatic question generation.

## Project Structure
```plaintext
└── lectify-flask-api/
    ├── .github/
    │ ├── robot-logo.png
    ├── src/
    │ ├── api/
    │ │ └── app.py
    │ ├── modules/
    │ │ ├── audio_downloader.py
    │ │ ├── audio_recognition.py
    │ │ ├── convert_document.py
    │ │ ├── document_builder.py
    │ │ ├── extract_text.py
    │ │ └── generative_ai.py
    │ ├── utils/
    │ │ ├── return_responses.py
    │ │ ├── send_email_verification.py
    │ │ └── system_utils.py
    ├── config/
    │ ├── headers_config.py
    │ ├── path_config.py
    │ └── prompt_config.py
    ├── docs/
    │ └── flasgger.py
    ├── .dockerignore
    ├── .env.example
    ├── gitignore
    ├── docker-compose.yml
    ├── Dockerfile
    ├── README.md
    ├── requirements.txt
    └── run.py
```

## Prerequisites
To use Docker for containerizing the Lectify Flask API, follow these steps to install Docker on your system.

### Setting Up Docker
Update your system and install Docker with the following commands:
```sh
sudo apt update
sudo apt install apt-transport-https ca-certificates curl software-properties-common -y
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io -y
```
Add your user to the Docker group:
```sh
sudo usermod -aG docker $USER
```
Run the test container to confirm Docker is working:
```sh
docker run hello-world
```
For additional information on how to install Docker on your system, visit the official Docker documentation: [Download Docker](https://docs.docker.com/get-docker/)

## Build and Run with Docker Compose
Instead of manually building and running the container with docker build and docker run, use Docker Compose, as it automatically starts both the server and the Redis service.
```sh
docker compose up --build -d
```

## API Documentation
The Lectify Flask API includes interactive documentation powered by Flasgger. You can explore each endpoint, view parameter details, and test API requests directly from the browser.

Interactive API Documentation: [http://127.0.0.1:5000/apidocs/](http://127.0.0.1:5000/apidocs/)

### API Endpoints

#### 1. Lectify Summarize Endpoint
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
curl -X POST "http://127.0.0.1:5000/lectify/summarize" -H "Content-Type: application/json" -H "Authorization: Bearer {token}" -d '{"youtube_url": "https://www.youtube.com/watch?v=iuPrkzJp20I", "output_format": "pdf", "language_select": "pt-BR"}'
```

##### Successful Response Summarize
- **Status Code**: `201 OK`
- **Content-Type**: `application/octet-stream`
- **Description**: Document generated successfully. Returns the summary in the requested format (MD or PDF).
- **Headers**:
  ```json
  {
    "..."
    "content-disposition": "attachment; filename=\"filename (hash) (Lectify).pdf\""
    "..."
  }
  ```

##### Error Responses Summarize
- **Unauthorized**:
  - **Status Code**: `401 Unauthorized`
  - **Content-Type**: `application/json`
  - **Description**: Unauthorized (invalid JWT token).
- **Bad Request**:
  - **Status Code**: `400 Bad Request`
  - **Content-Type**: `application/json`
  - **Description**: Invalid request.
  - **Examples**:
    ```json
    {"error": "No data provided"}
    ```
    ```json
    {"error": "Missing required fields: youtube_url, output_format"}
    ```
    ```json
    {"error": "Missing YouTube URL"}
    ```
    ```json
    {"error": "URL exceeds maximum length of 200 characters"}
    ```
    ```json
    {"error": "Invalid YouTube URL"}
    ```
    ```json
    {"error": "Missing output format"}
    ```
    ```json
    {"error": "Invalid format. Supported formats: md, pdf"}
    ```
    ```json
    {"error": "Missing language selection"}
    ```
    ```json
    {"error": "Invalid format. Supported formats: pt-BR, en-US"}
    ```
    ```json
    {"error": "Download error occurred. Please check the URL and your network connection"}
    ```
    ```json
    {"error": "Network error. Please check your internet connection"}
    ```
    ```json
    {"error": "Error during audio downloading"}
    ```
    ```json
    {"error": "Error during audio recognition"}
    ```
    ```json
    {"error": "Error during chat generation"}
    ```
    ```json
    {"error": "Error during document building"}
    ```
    ```json
    {"error": "OS error occurred while handling the file"}
    ```
    ```json
    {"error": "Error during document conversion"}
    ```
    ```json
    {"error": "File not found"}
    ```
- **Too Many Requests**:
  - **Status Code**: `429 Too Many Requests`
  - **Content-Type**: `application/json`
  - **Description**: Too many requests or server busy.
  - **Examples**:
    ```json
    {"error": "Server busy. Please try again shortly"}
    ```
    ```json
    {"error": "Too many requests. Please try again later."}
    ```
    ```json
    {"error": "Monthly limit exceeded or you are making too many requests. Please try again later."}
    ```
    ```json
    {"error": "You have been temporarily blocked due to repeated rate limit violations. Please try again in X minute(s)."}
    ```
- **Internal Server Error**:
  - **Status Code**: `500 Internal Server Error`
  - **Content-Type**: `application/json`
  - **Description**: Internal server error.
  - **Example**:
    ```json
    {"error": "An error occurred while processing the request"}
    ```

#### 2. Lectify Questions Endpoint
- **URL**: `/lectify/questions`
- **Method**: `POST`
- **Description**: Generates questions from an MD or PDF file.
- **Security**: Requires JWT Bearer token in Authorization header.

##### Request Body Questions:
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `file`: MD or PDF file for analysis (required).
    - Type: `File`
    - **Accepted Formats**: `md`, `pdf`
    - **Max File Size**: 5 MB

###### Example Request Questions
```sh
curl -X POST "http://127.0.0.1:5000/lectify/questions" -H "Authorization: Bearer {token}" -F "file=@document.pdf"
```

##### Successful Response Questions
- **Status Code**: `200 OK`
- **Content-Type**: `application/json`
- **Description**: Questions generated successfully.
- **Response Body**:
  ```json
  {
    "questao1": [
      {
        "pergunta": "What is the correct statement about Newton's First Law?",
        "alternativas": ["Question A", "Question B"],
        "dica": "Hint for the answer.",
        "justificativa": "Explanation of the correct answer.",
        "resposta_correta": "Question B",
        "Dificuldade": "Easy"
      }
    ]
  }
  ```

##### Error Responses Questions
- **Unauthorized**:
  - **Status Code**: `401 Unauthorized`
  - **Content-Type**: `application/json`
  - **Description**: Unauthorized.
- **Bad Request**:
  - **Status Code**: `400 Bad Request`
  - **Content-Type**: `application/json`
  - **Description**: Invalid request.
  - **Examples**:
    ```json
    {"error": "Exactly one file must be uploaded"}
    ```
    ```json
    {"error": "No files received"}
    ```
    ```json
    {"error": "File name exceeds the maximum length of 200 characters."}
    ```
    ```json
    {"error": "Invalid format. Supported formats: md, pdf"}
    ```
    ```json
    {"error": "The filename seems suspicious and contains a blocked extension: .exe"}
    ```
    ```json
    {"error": "Invalid file type. Detected: text/plain. Expected: application/pdf"}
    ```
    ```json
    {"error": "Error during extraction of Markdown text"}
    ```
    ```json
    {"error": "Error during extraction of PDF text"}
    ```
    ```json
    {"error": "Error during chat generation"}
    ```
- **Payload Too Large**:
  - **Status Code**: `413 Payload Too Large`
  - **Content-Type**: `application/json`
  - **Description**: File too large.
  - **Example**:
    ```json
    {"error": "File size exceeds the maximum limit of 5 MB."}
    ```
- **Too Many Requests**:
  - **Status Code**: `429 Too Many Requests`
  - **Content-Type**: `application/json`
  - **Description**: Too many requests.
  - **Example**:
    ```json
    {"error": "Too many requests. Please try again later."}
    ```
- **Internal Server Error**:
  - **Status Code**: `500 Internal Server Error`
  - **Content-Type**: `application/json`
  - **Description**: Internal error.
  - **Example**:
    ```json
    {"error": "An error occurred while processing the request"}
    ```

#### 3. Check Email Register Endpoint
- **URL**: `/lectify/check_email_register`
- **Method**: `POST`
- **Description**: Sends verification code via email for registration.

##### Request Body:
- **Content-Type**: `application/json`
- **Request Fields**:
  - `email`: Email address (required).
    - Type: `String`
    - **Example**: `user@example.com`

###### Example Request
```sh
curl -X POST "http://127.0.0.1:5000/lectify/check_email_register" -H "Content-Type: application/json" -d '{"email": "user@example.com"}'
```

##### Successful Response
- **Status Code**: `200 OK`
- **Content-Type**: `application/json`
- **Description**: Code sent.
- **Response Body**:
  ```json
  {"message": "Verification code sent to email"}
  ```

##### Error Responses
- **Bad Request**:
  - **Status Code**: `400 Bad Request`
  - **Content-Type**: `application/json`
  - **Description**: Invalid or existing email.
  - **Examples**:
    ```json
    {"error": "Email is required"}
    ```
    ```json
    {"error": "Invalid email format"}
    ```
    ```json
    {"error": "Email already exists"}
    ```
- **Too Many Requests**:
  - **Status Code**: `429 Too Many Requests`
  - **Content-Type**: `application/json`
  - **Description**: Rate limit.
  - **Example**:
    ```json
    {"error": "Too many requests. Please try again later."}
    ```
- **Internal Server Error**:
  - **Status Code**: `500 Internal Server Error`
  - **Content-Type**: `application/json`
  - **Description**: Internal error.
  - **Example**:
    ```json
    {"error": "An error occurred while processing the request"}
    ```

#### 4. Verify Email Register Endpoint
- **URL**: `/lectify/verify_email_register`
- **Method**: `POST`
- **Description**: Verifies email code for registration.

##### Request Body:
- **Content-Type**: `application/json`
- **Request Fields**:
  - `email`: Email address (required).
    - Type: `String`
    - **Example**: `user@example.com`
  - `code`: Verification code (required).
    - Type: `String`
    - **Example**: `ABC123`

###### Example Request
```sh
curl -X POST "http://127.0.0.1:5000/lectify/verify_email_register" -H "Content-Type: application/json" -d '{"email": "user@example.com", "code": "ABC123"}'
```

##### Successful Response
- **Status Code**: `200 OK`
- **Content-Type**: `application/json`
- **Description**: Email verified.
- **Response Body**:
  ```json
  {"message": "Email verified successfully"}
  ```

##### Error Responses
- **Bad Request**:
  - **Status Code**: `400 Bad Request`
  - **Content-Type**: `application/json`
  - **Description**: Invalid code or email not found.
  - **Examples**:
    ```json
    {"error": "Email and code are required"}
    ```
    ```json
    {"error": "Invalid email format"}
    ```
    ```json
    {"error": "Email not found"}
    ```
    ```json
    {"error": "Invalid verification type"}
    ```
    ```json
    {"error": "Invalid verification code"}
    ```
- **Not Found**:
  - **Status Code**: `404 Not Found`
  - **Content-Type**: `application/json`
  - **Description**: Email not found.
  - **Example**:
    ```json
    {"error": "Email not found"}
    ```
- **Too Many Requests**:
  - **Status Code**: `429 Too Many Requests`
  - **Content-Type**: `application/json`
  - **Description**: Rate limit.
- **Internal Server Error**:
  - **Status Code**: `500 Internal Server Error`
  - **Content-Type**: `application/json`
  - **Description**: Internal error.

#### 5. Register Endpoint
- **URL**: `/lectify/register`
- **Method**: `POST`
- **Description**: Registers a new user.

##### Request Body:
- **Content-Type**: `application/json`
- **Request Fields**:
  - `username`: Username (required).
    - Type: `String`
    - **Example**: `user123`
  - `password`: Password (required).
    - Type: `String`
    - **Example**: `password123`
  - `email`: Email address (required).
    - Type: `String`
    - **Example**: `user@example.com`
  - `firstname`: First name (required).
    - Type: `String`
    - **Example**: `John`
  - `lastname`: Last name (required).
    - Type: `String`
    - **Example**: `Doe`

###### Example Request
```sh
curl -X POST "http://127.0.0.1:5000/lectify/register" -H "Content-Type: application/json" -d '{"username": "user123", "password": "password123", "email": "user@example.com", "firstname": "John", "lastname": "Doe"}'
```

##### Successful Response
- **Status Code**: `201 Created`
- **Content-Type**: `application/json`
- **Description**: User registered.
- **Response Body**:
  ```json
  {"message": "User registered successfully"}
  ```

##### Error Responses
- **Bad Request**:
  - **Status Code**: `400 Bad Request`
  - **Content-Type**: `application/json`
  - **Description**: Invalid or duplicate data.
  - **Examples**:
    ```json
    {"error": "Username, password, email, firstname and lastname are required"}
    ```
    ```json
    {"error": "Username already exists"}
    ```
    ```json
    {"error": "Email already exists"}
    ```
    ```json
    {"error": "Email not verified"}
    ```
- **Too Many Requests**:
  - **Status Code**: `429 Too Many Requests`
  - **Content-Type**: `application/json`
  - **Description**: Rate limit.
- **Internal Server Error**:
  - **Status Code**: `500 Internal Server Error`
  - **Content-Type**: `application/json`
  - **Description**: Internal error.

#### 6. Login Endpoint
- **URL**: `/lectify/login`
- **Method**: `POST`
- **Description**: Logs in and returns JWT tokens.

##### Request Body:
- **Content-Type**: `application/json`
- **Request Fields**:
  - `username`: Username (optional if email provided).
    - Type: `String`
    - **Example**: `user123`
  - `email`: Email address (optional if username provided).
    - Type: `String`
    - **Example**: `user@example.com`
  - `password`: Password (required).
    - Type: `String`
    - **Example**: `password123`

###### Example Request
```sh
curl -X POST "http://127.0.0.1:5000/lectify/login" -H "Content-Type: application/json" -d '{"username": "user123", "password": "password123"}'
```

##### Successful Response
- **Status Code**: `200 OK`
- **Content-Type**: `application/json`
- **Description**: Login successful.
- **Response Body**:
  ```json
  {
    "access_token": "jwt_access_token",
    "refresh_token": "jwt_refresh_token"
  }
  ```

##### Error Responses
- **Bad Request**:
  - **Status Code**: `400 Bad Request`
  - **Content-Type**: `application/json`
  - **Description**: Invalid credentials.
  - **Examples**:
    ```json
    {"error": "Invalid email format"}
    ```
    ```json
    {"error": "Password is required"}
    ```
    ```json
    {"error": "You must provide either a username or an email"}
    ```
- **Unauthorized**:
  - **Status Code**: `401 Unauthorized`
  - **Content-Type**: `application/json`
  - **Description**: Incorrect credentials.
  - **Example**:
    ```json
    {"error": "Invalid email or password"}
    ```
- **Not Found**:
  - **Status Code**: `404 Not Found`
  - **Content-Type**: `application/json`
  - **Description**: User not found.
  - **Example**:
    ```json
    {"error": "User not found"}
    ```
- **Too Many Requests**:
  - **Status Code**: `429 Too Many Requests`
  - **Content-Type**: `application/json`
  - **Description**: Rate limit.
- **Internal Server Error**:
  - **Status Code**: `500 Internal Server Error`
  - **Content-Type**: `application/json`
  - **Description**: Internal error.

#### 7. Profile Endpoint
- **URL**: `/lectify/profile`
- **Method**: `GET`
- **Description**: Returns user profile data.
- **Security**: Requires JWT Bearer token in Authorization header.

##### Request Body:
- None

###### Example Request
```sh
curl -X GET "http://127.0.0.1:5000/lectify/profile" -H "Authorization: Bearer {token}"
```

##### Successful Response
- **Status Code**: `200 OK`
- **Content-Type**: `application/json`
- **Description**: Profile loaded.
- **Response Body**:
  ```json
  {
    "username": "user123",
    "email": "user@example.com",
    "firstname": "John",
    "lastname": "Doe",
    "is_free": true,
    "created_at": "2023-01-01T00:00:00",
    "plan": "free",
    "subscription_end": "2024-01-01T00:00:00"
  }
  ```

##### Error Responses
- **Unauthorized**:
  - **Status Code**: `401 Unauthorized`
  - **Content-Type**: `application/json`
  - **Description**: Unauthorized.
- **Not Found**:
  - **Status Code**: `404 Not Found`
  - **Content-Type**: `application/json`
  - **Description**: User not found.
  - **Example**:
    ```json
    {"error": "User not found"}
    ```
- **Too Many Requests**:
  - **Status Code**: `429 Too Many Requests`
  - **Content-Type**: `application/json`
  - **Description**: Rate limit.
- **Internal Server Error**:
  - **Status Code**: `500 Internal Server Error`
  - **Content-Type**: `application/json`
  - **Description**: Internal error.

#### 8. Refresh Token Endpoint
- **URL**: `/lectify/refresh_token`
- **Method**: `POST`
- **Description**: Refreshes access token using refresh token.
- **Security**: Requires JWT Bearer token (refresh token) in Authorization header.

##### Request Body:
- None

###### Example Request
```sh
curl -X POST "http://127.0.0.1:5000/lectify/refresh_token" -H "Authorization: Bearer {refresh_token}"
```

##### Successful Response
- **Status Code**: `200 OK`
- **Content-Type**: `application/json`
- **Description**: Token refreshed.
- **Response Body**:
  ```json
  {"access_token": "new_jwt_access_token"}
  ```

##### Error Responses
- **Unauthorized**:
  - **Status Code**: `401 Unauthorized`
  - **Content-Type**: `application/json`
  - **Description**: Unauthorized.
- **Not Found**:
  - **Status Code**: `404 Not Found`
  - **Content-Type**: `application/json`
  - **Description**: User not found.
- **Too Many Requests**:
  - **Status Code**: `429 Too Many Requests`
  - **Content-Type**: `application/json`
  - **Description**: Rate limit.
- **Internal Server Error**:
  - **Status Code**: `500 Internal Server Error`
  - **Content-Type**: `application/json`
  - **Description**: Internal error.

#### 9. Update Profile Endpoint
- **URL**: `/lectify/update_profile`
- **Method**: `PATCH`
- **Description**: Updates user profile (name or password).
- **Security**: Requires JWT Bearer token in Authorization header.

##### Request Body:
- **Content-Type**: `application/json`
- **Request Fields**:
  - `firstname`: New first name (optional).
    - Type: `String`
    - **Example**: `John`
  - `lastname`: New last name (optional).
    - Type: `String`
    - **Example**: `Doe`
  - `password`: New password (optional).
    - Type: `String`
    - **Example**: `newpassword123`

###### Example Request
```sh
curl -X PATCH "http://127.0.0.1:5000/lectify/update_profile" -H "Content-Type: application/json" -H "Authorization: Bearer {token}" -d '{"firstname": "John", "lastname": "Doe"}'
```

##### Successful Response
- **Status Code**: `200 OK`
- **Content-Type**: `application/json`
- **Description**: Profile updated.
- **Response Body**:
  ```json
  {"message": "Profile updated successfully"}
  ```

##### Error Responses
- **Bad Request**:
  - **Status Code**: `400 Bad Request`
  - **Content-Type**: `application/json`
  - **Description**: Empty or invalid fields.
  - **Examples**:
    ```json
    {"error": "Firstname cannot be empty"}
    ```
    ```json
    {"error": "Lastname cannot be empty"}
    ```
    ```json
    {"error": "Password cannot be empty"}
    ```
    ```json
    {"error": "Firstname is the same as the current one"}
    ```
    ```json
    {"error": "Lastname is the same as the current one"}
    ```
    ```json
    {"error": "No fields to update"}
    ```
- **Unauthorized**:
  - **Status Code**: `401 Unauthorized`
  - **Content-Type**: `application/json`
  - **Description**: Unauthorized.
- **Not Found**:
  - **Status Code**: `404 Not Found`
  - **Content-Type**: `application/json`
  - **Description**: User not found.
- **Too Many Requests**:
  - **Status Code**: `429 Too Many Requests`
  - **Content-Type**: `application/json`
  - **Description**: Rate limit.
- **Internal Server Error**:
  - **Status Code**: `500 Internal Server Error`
  - **Content-Type**: `application/json`
  - **Description**: Internal error.

#### 10. Update Image Profile Endpoint
- **URL**: `/lectify/update_image_profile`
- **Method**: `PUT`
- **Description**: Updates or removes user profile image.
- **Security**: Requires JWT Bearer token in Authorization header.

##### Request Body:
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `file`: Image file to upload (optional; if not provided, removes existing image).
    - Type: `File`
    - **Accepted Formats**: `png`, `jpg`, `jpeg`, `bmp`, `tiff`, `svg`, `webp`, `heic`, `heif`
    - **Max File Size**: 5 MB

###### Example Request (Update)
```sh
curl -X PUT "http://127.0.0.1:5000/lectify/update_image_profile" -H "Authorization: Bearer {token}" -F "file=@profile.jpg"
```

###### Example Request (Remove)
```sh
curl -X PUT "http://127.0.0.1:5000/lectify/update_image_profile" -H "Authorization: Bearer {token}"
```

##### Successful Response
- **Status Code**: `200 OK`
- **Content-Type**: `application/json`
- **Description**: Profile image updated or removed successfully.
- **Response Body (Update)**:
  ```json
  {
    "message": "Profile image updated successfully",
    "image_profile": "https://cloudinary.com/"
  }
  ```
- **Response Body (Remove)**:
  ```json
  {"message": "Profile image removed successfully"}
  ```

##### Error Responses
- **Bad Request**:
  - **Status Code**: `400 Bad Request`
  - **Content-Type**: `application/json`
  - **Description**: Invalid format or suspicious file.
  - **Examples**:
    ```json
    {"error": "Exactly one file must be uploaded"}
    ```
    ```json
    {"error": "No profile image to remove"}
    ```
    ```json
    {"error": "Invalid format. Supported formats: png, jpg, jpeg, bmp, tiff, svg, webp, heic, heif"}
    ```
    ```json
    {"error": "The filename seems suspicious and contains a blocked extension: .exe"}
    ```
    ```json
    {"error": "Invalid file type. Detected: application/octet-stream. Expected: image/jpeg"}
    ```
- **Unauthorized**:
  - **Status Code**: `401 Unauthorized`
  - **Content-Type**: `application/json`
  - **Description**: Unauthorized.
- **Not Found**:
  - **Status Code**: `404 Not Found`
  - **Content-Type**: `application/json`
  - **Description**: User not found.
  - **Example**:
    ```json
    {"error": "User not found"}
    ```
- **Payload Too Large**:
  - **Status Code**: `413 Payload Too Large`
  - **Content-Type**: `application/json`
  - **Description**: File too large.
  - **Example**:
    ```json
    {"error": "File size exceeds the maximum limit of 5 MB."}
    ```
- **Too Many Requests**:
  - **Status Code**: `429 Too Many Requests`
  - **Content-Type**: `application/json`
  - **Description**: Server busy or too many requests.
  - **Examples**:
    ```json
    {"error": "Server busy. Please try again shortly"}
    ```
    ```json
    {"error": "Too many requests. Please try again later."}
    ```
- **Internal Server Error**:
  - **Status Code**: `500 Internal Server Error`
  - **Content-Type**: `application/json`
  - **Description**: Internal server error.
  - **Example**:
    ```json
    {"error": "An error occurred while processing the request"}
    ```

#### 11. Ping Email Delete Account Endpoint
- **URL**: `/lectify/ping_email_delete_account`
- **Method**: `POST`
- **Description**: Sends verification link via email for account deletion.
- **Security**: Requires JWT Bearer token in Authorization header.

##### Request Body:
- **Content-Type**: `application/json`
- **Request Fields**:
  - `base_url`: Base URL (required).
    - Type: `String`
    - **Example**: `https://lectify.vercel.app`
  - `reset_password_page_url`: Reset page URL (required).
    - Type: `String`
    - **Example**: `delete-account`

###### Example Request
```sh
curl -X POST "http://127.0.0.1:5000/lectify/ping_email_delete_account" -H "Content-Type: application/json" -H "Authorization: Bearer {token}" -d '{"base_url": "https://lectify.vercel.app", "reset_password_page_url": "delete-account"}'
```

##### Successful Response
- **Status Code**: `200 OK`
- **Content-Type**: `application/json`
- **Description**: Verification link sent.
- **Response Body**:
  ```json
  {"message": "Verification code sent to email"}
  ```

##### Error Responses
- **Bad Request**:
  - **Status Code**: `400 Bad Request`
  - **Content-Type**: `application/json`
  - **Description**: Missing required fields.
  - **Example**:
    ```json
    {"error": "Base URL and Reset Password Page URL are required"}
    ```
- **Unauthorized**:
  - **Status Code**: `401 Unauthorized`
  - **Content-Type**: `application/json`
  - **Description**: Unauthorized.
- **Not Found**:
  - **Status Code**: `404 Not Found`
  - **Content-Type**: `application/json`
  - **Description**: User not found.
  - **Example**:
    ```json
    {"error": "User not found"}
    ```
- **Too Many Requests**:
  - **Status Code**: `429 Too Many Requests`
  - **Content-Type**: `application/json`
  - **Description**: Rate limit or server busy.
  - **Examples**:
    ```json
    {"error": "Server busy. Please try again shortly"}
    ```
    ```json
    {"error": "Too many requests. Please try again later."}
    ```
- **Internal Server Error**:
  - **Status Code**: `500 Internal Server Error`
  - **Content-Type**: `application/json`
  - **Description**: Internal error.
  - **Example**:
    ```json
    {"error": "An error occurred while processing the request"}
    ```

#### 12. Pong Email Delete Account Endpoint
- **URL**: `/lectify/pong_email_delete_account`
- **Method**: `DELETE`
- **Description**: Verifies token and deletes user account.
- **Security**: Requires JWT Bearer token in Authorization header.

##### Request Body:
- **Content-Type**: `application/json`
- **Request Fields**:
  - `token`: Verification token (required).
    - Type: `String`
    - **Example**: `abc123def456`

###### Example Request
```sh
curl -X DELETE "http://127.0.0.1:5000/lectify/pong_email_delete_account" -H "Content-Type: application/json" -H "Authorization: Bearer {token}" -d '{"token": "abc123def456"}'
```

##### Successful Response
- **Status Code**: `200 OK`
- **Content-Type**: `application/json`
- **Description**: Account deleted.
- **Response Body**:
  ```json
  {"message": "Account deleted successfully"}
  ```

##### Error Responses
- **Bad Request**:
  - **Status Code**: `400 Bad Request`
  - **Content-Type**: `application/json`
  - **Description**: Invalid token or verification.
  - **Examples**:
    ```json
    {"error": "Token is required"}
    ```
    ```json
    {"error": "Email not found"}
    ```
    ```json
    {"error": "Invalid verification type"}
    ```
    ```json
    {"error": "Invalid verification token"}
    ```
- **Unauthorized**:
  - **Status Code**: `401 Unauthorized`
  - **Content-Type**: `application/json`
  - **Description**: Unauthorized.
- **Not Found**:
  - **Status Code**: `404 Not Found`
  - **Content-Type**: `application/json`
  - **Description**: User not found.
  - **Example**:
    ```json
    {"error": "User not found"}
    ```
- **Too Many Requests**:
  - **Status Code**: `429 Too Many Requests`
  - **Content-Type**: `application/json`
  - **Description**: Rate limit or server busy.
  - **Examples**:
    ```json
    {"error": "Server busy. Please try again shortly"}
    ```
    ```json
    {"error": "Too many requests. Please try again later."}
    ```
- **Internal Server Error**:
  - **Status Code**: `500 Internal Server Error`
  - **Content-Type**: `application/json`
  - **Description**: Internal error.
  - **Example**:
    ```json
    {"error": "An error occurred while processing the request"}
    ```

#### 13. Ping Email Reset Password Endpoint
- **URL**: `/lectify/ping_email_reset_password`
- **Method**: `POST`
- **Description**: Sends password reset link via email.

##### Request Body:
- **Content-Type**: `application/json`
- **Request Fields**:
  - `email`: Email address (required).
    - Type: `String`
    - **Example**: `user@example.com`
  - `base_url`: Base URL (required).
    - Type: `String`
    - **Example**: `https://lectify.vercel.app`
  - `reset_password_page_url`: Reset page URL (required).
    - Type: `String`
    - **Example**: `reset-password`

###### Example Request
```sh
curl -X POST "http://127.0.0.1:5000/lectify/ping_email_reset_password" -H "Content-Type: application/json" -d '{"email": "user@example.com", "base_url": "https://lectify.vercel.app", "reset_password_page_url": "reset-password"}'
```

##### Successful Response
- **Status Code**: `200 OK`
- **Content-Type**: `application/json`
- **Description**: Link sent.
- **Response Body**:
  ```json
  {"message": "Verification sent to email"}
  ```

##### Error Responses
- **Bad Request**:
  - **Status Code**: `400 Bad Request`
  - **Content-Type**: `application/json`
  - **Description**: Missing data.
  - **Example**:
    ```json
    {"error": "Email, Base URL and Reset Password Page URL are required"}
    ```
- **Not Found**:
  - **Status Code**: `404 Not Found`
  - **Content-Type**: `application/json`
  - **Description**: Email not found.
  - **Example**:
    ```json
    {"error": "Email not found"}
    ```
- **Too Many Requests**:
  - **Status Code**: `429 Too Many Requests`
  - **Content-Type**: `application/json`
  - **Description**: Rate limit.
- **Internal Server Error**:
  - **Status Code**: `500 Internal Server Error`
  - **Content-Type**: `application/json`
  - **Description**: Internal error.

#### 14. Pong Email Reset Password Endpoint
- **URL**: `/lectify/pong_email_reset_password`
- **Method**: `POST`
- **Description**: Verifies token and updates password.

##### Request Body:
- **Content-Type**: `application/json`
- **Request Fields**:
  - `email`: Email address (required).
    - Type: `String`
    - **Example**: `user@example.com`
  - `token`: Verification token (required).
    - Type: `String`
    - **Example**: `abc123def456`
  - `new_password`: New password (required).
    - Type: `String`
    - **Example**: `newPassword123`

###### Example Request
```sh
curl -X POST "http://127.0.0.1:5000/lectify/pong_email_reset_password" -H "Content-Type: application/json" -d '{"email": "user@example.com", "token": "abc123def456", "new_password": "newPassword123"}'
```

##### Successful Response
- **Status Code**: `200 OK`
- **Content-Type**: `application/json`
- **Description**: Password updated.
- **Response Body**:
  ```json
  {"message": "Password reset successfully"}
  ```

##### Error Responses
- **Bad Request**:
  - **Status Code**: `400 Bad Request`
  - **Content-Type**: `application/json`
  - **Description**: Invalid data.
  - **Examples**:
    ```json
    {"error": "Email, Token, and new password are required"}
    ```
    ```json
    {"error": "Email not found"}
    ```
    ```json
    {"error": "Invalid verification type"}
    ```
    ```json
    {"error": "Invalid verification Token"}
    ```
- **Not Found**:
  - **Status Code**: `404 Not Found`
  - **Content-Type**: `application/json`
  - **Description**: Email not found.
  - **Example**:
    ```json
    {"error": "Email not found"}
    ```
- **Too Many Requests**:
  - **Status Code**: `429 Too Many Requests`
  - **Content-Type**: `application/json`
  - **Description**: Rate limit.
- **Internal Server Error**:
  - **Status Code**: `500 Internal Server Error`
  - **Content-Type**: `application/json`
  - **Description**: Internal error.

#### 15. Checkout Endpoint
- **URL**: `/lectify/checkout`
- **Method**: `POST`
- **Description**: Creates Stripe checkout session for paid plan.
- **Security**: Requires JWT Bearer token in Authorization header.

##### Request Body:
- **Content-Type**: `application/json`
- **Request Fields**:
  - `plan`: Subscription plan (required).
    - Type: `String`
    - **Supported Values**: `1_month`, `6_months`, `1_year`
    - **Example**: `1_month`
  - `success_url`: Success URL (required).
    - Type: `String`
    - **Example**: `https://lectify.vercel.app/success`
  - `cancel_url`: Cancel URL (required).
    - Type: `String`
    - **Example**: `https://lectify.vercel.app/cancel`

###### Example Request
```sh
curl -X POST "http://127.0.0.1:5000/lectify/checkout" -H "Content-Type: application/json" -H "Authorization: Bearer {token}" -d '{"plan": "1_month", "success_url": "https://lectify.vercel.app/success", "cancel_url": "https://lectify.vercel.app/cancel"}'
```

##### Successful Response
- **Status Code**: `200 OK`
- **Content-Type**: `application/json`
- **Description**: Session created.
- **Response Body**:
  ```json
  {"checkout_url": "stripe_checkout_url"}
  ```

##### Error Responses
- **Bad Request**:
  - **Status Code**: `400 Bad Request`
  - **Content-Type**: `application/json`
  - **Description**: Invalid plan or user already paid.
  - **Examples**:
    ```json
    {"error": "Plan is required"}
    ```
    ```json
    {"error": "Invalid plan"}
    ```
    ```json
    {"error": "User already has a paid plan"}
    ```
    ```json
    {"error": "Success and cancel URLs are required"}
    ```
- **Unauthorized**:
  - **Status Code**: `401 Unauthorized`
  - **Content-Type**: `application/json`
  - **Description**: Unauthorized.
- **Not Found**:
  - **Status Code**: `404 Not Found`
  - **Content-Type**: `application/json`
  - **Description**: User not found.
- **Too Many Requests**:
  - **Status Code**: `429 Too Many Requests`
  - **Content-Type**: `application/json`
  - **Description**: Rate limit.
- **Internal Server Error**:
  - **Status Code**: `500 Internal Server Error`
  - **Content-Type**: `application/json`
  - **Description**: Internal error.

#### 16. Webhook Endpoint
- **URL**: `/lectify/webhook`
- **Method**: `POST`
- **Description**: Stripe webhook to process payments (internal).

##### Request Body:
- **Content-Type**: `application/json`
- No specific fields (Stripe payload).

###### Example Request
```sh
curl -X POST "http://127.0.0.1:5000/lectify/webhook" -H "Content-Type: application/json" -d '{stripe_payload}'
```

##### Successful Response
- **Status Code**: `200 OK`
- **Content-Type**: `application/json`
- **Description**: Processed successfully.
- **Response Body**:
  ```json
  {"status": "success"}
  ```

##### Error Responses
- **Bad Request**:
  - **Status Code**: `400 Bad Request`
  - **Content-Type**: `application/json`
  - **Description**: Invalid payload or signature.
  - **Examples**:
    ```json
    {"error": "Invalid payload"}
    ```
    ```json
    {"error": "Invalid signature"}
    ```
- **Internal Server Error**:
  - **Status Code**: `500 Internal Server Error`
  - **Content-Type**: `application/json`
  - **Description**: Internal error.

## License
This project is licensed under the terms of the [Apache License 2.0](http://www.apache.org/licenses/LICENSE-2.0). See the [LICENSE](./LICENSE) file for details.