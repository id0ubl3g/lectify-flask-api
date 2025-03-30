<div align="center">
    <img src=".github/robot-logo.png" alt="Robot Logo" width="130">
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
    - [Setting Up `Docker`](#setting-up-docker)
    - [Browser Installed and Logged In](#browser-installed-and-logged-in)
- [Build and Run Container](#build-and-run-container)
- [API Documentation](#api-documentation)
    - [API Endpoints](#api-endpoints)
        - [1. Lectify Summarize Endpoint](#1-lectify-summarize-endpoint)
            - [Request Body Summarize](#request-body-summarize)
                - [Example Request Summarize](#example-request-summarize)
            - [Successful Response Summarize](#successful-response-summarize)
            - [Error Responses Summarize](#error-responses-summarize)
        - [2. Lectify Questions Endpoint](#2-lectify-questions-endpoint)
            - [Request Body Questions](#request-body-questions)
                - [Example Request Questions](#example-request-questions)
            - [Successful Response Questions](#successful-response-questions)
            - [Error Responses Questions](#error-responses-questions)
    - [Example Use Case](#example-use-case)
        - [Frontend Integration](#frontend-integration)
- [Acknowledgments](#acknowledgments)


## Overview
The Lectify Flask API is a web application developed with Flask, designed to summarize video lectures with detailed insights and generate quiz questions from the provided document. It offers a comprehensive tool for educators and learners to extract key information and test understanding through automatic question generation.

## Project Structure

```plaintext
└── lectify-flask-api/
    ├── .github/
    │   ├── robot-logo.png
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
    │   ├── utils/
    │   │   ├── return_responses.py
    │   │   └── system_utils.py
    ├── config/
    │   ├── path_config.py
    │   └── prompt_config.py
    ├── docs/
    │   └── flasgger.py
    ├── .dockerignore
    ├── .env.example
    ├── gitignore
    ├── Dockerfile
    ├── README.md
    ├── requirements.txt
    └── run.py
```

## Prerequisites

To use Docker for containerizing the Conver Flask API, follow these steps to install Docker on your system.

### Setting Up `Docker`

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

### Browser Installed and Logged In

Ensure a browser is installed in the environment and the user is logged in to avoid cookie-related issues. If no browser is installed, or if you prefer a different one, consider installing one such as [Firefox](https://www.mozilla.org/en-US/firefox/new/), [Chrome](https://www.google.com/chrome/what-you-make-of-it/), [Opera](https://www.opera.com/opera), [Vivaldi](https://vivaldi.com/download/), or others.

## Build and Run Container

```sh
docker build -t conver-flask-api .
docker run -p 5000:5000 conver-flask-api
```

## API Documentation

The Lectify Flask API includes interactive documentation powered by Flasgger. You can explore each endpoint, view parameter details, and test API requests directly from the browser.

Interactive API Documentation: [http://127.0.0.1:5000/apidocs/](http://127.0.0.1:5000/apidocs/)

### API Endpoints

#### 1. Lectify Summarize Endpoint

- **URL**: `/lectify/summarize`
- **Method**: `POST`
- **Description**: Summarizes the audio from a YouTube video by extracting its text content and generating a summary.


##### Request Body Summarize:

- **Content-Type**: `application/json`
- **Request Fields**:
    - `youtube_url`: The YouTube URL of the video to summarize (required).
      - Type: `String`
      - **Example**: `https://www.youtube.com/watch?v=example`
    - `output_format`: The desired output format for the result (required).
      - Type: `String`
      - **Supported Formats**: `md`, `pdf`
    - `language_select`: The language in which the content should be summarized (required).
      - Type: `String`
      - **Supported Languages**: `pt-BR`, `en-US`

###### Example Request Summarize

```sh
curl -X POST "http://127.0.0.1:5000/lectify/summarize" -H "Content-Type: application/json" -d '{"youtube_url": "https://www.youtube.com/watch?v=example", "output_format": "pdf", "language_select": "en-US"}'
```

##### Successful Response Summarize

- **Successful Response**:
    - **Status Code**: `201 OK`
    - **Content-Type**: `application/octet-stream`
    - **Description**: Returns the summary in the requested format (Markdown or PDF).
    - **Headers**:
    ```json
    {
        "..."
        "content-disposition": "attachment; filename=\"filename (hash) (Lectify).pdf\""
        "..."
    }
    ```

##### Error Responses Summarize

- **Bad Request**:
    - **Status Code**: `400 Bad Request`
    - **Content-Type**: `application/json`
    - **Description**: Returned when the request is missing required fields or has invalid values.
    - **Example**:
    ```json
    {
        "error": "No data provided"
    }
    ```
    ```json
    {
        "error": "Missing required fields: {missing_fields_str}"
    }
    ```
    ```json
    {
        "error": "error': 'Missing YouTube URL"
    }
    ```
    ```json
    {
        "error": "Missing YouTube URL"
    }
    ```
    ```json
    {
        "error": "URL exceeds maximum length of 200 characters"
    }
    ```
    ```json
    {
        "error": "Invalid YouTube URL"
    }
    ```
    ```json
    {
        "error": "Invalid format. Supported formats: 'pdf', 'md'"
    }
    ```
    ```json
    {
        "error": "Missing language selection"
    }
    ```
    ```json
    {
        "error": "Invalid format. Supported formats: 'pt-BR', 'en-US'"
    }
    ```
    ```json
    {
        "error": "File not found"
    }
    ```
    ```json
    {
        "error": "Error during document conversion"
    }
    ```
    ```json
    {
        "error": "OS error occurred while handling the file"
    }
    ```
    ```json
    {
        "error": "Error during document building"
    }
    ```
    ```json
    {
        "error": "Error during chat generation"
    }
    ```
    ```json
    {
        "error": "Unable to understand the audio"
    }
    ```
    ```json
    {
        "error": "Error in service request"
    }
    ```
    ```json
    {
        "error": "Error during audio recognition"
    }
    ```
    ```json
    {
        "error": "Download error occurred. Please check the URL and your network connection"
    }
    ```
    ```json
    {
        "error": "Network error. Please check your internet connection"
    }
    ```
    ```json
    {
        "error": "Error during audio downloading"
    }
    ```

- **500 Internal Server Error**:
    - **Status Code**: `500 Internal Server Error`
    - **Content-Type**: `application/json`
    - **Description**: Returned when an internal error occurs.
    - **Example**:
    ```json
    {
        "error": "An error occurred while processing the request"
    }
    ```

#### 2. Lectify Questions Endpoint

- **URL**: `/lectify/questions`
- **Method**: `POST`
- **Description**: Extracts text from a file and generates questions based on the content.

##### Request Body Questions:

- **Content-Type**: `multipart/form-data`
- **Form Fields**:
    - `file`: The document file to extract text from (required).
      - Type: `File`
      - **Accepted Formats**: `pdf`, `md`
      - **Max File Size**: 5 MB

###### Example Request Questions

```sh
curl -X POST "http://127.0.0.1:5000/lectify/questions" \ -F "file=@document.pdf"
```

##### Successful Response Questions

- **Successful Response**:
    - **Status Code**: `200 OK`
    - **Content-Type**: `application/json`
    - **Description**: Returns the generated questions based on the document content.
    - **Response Body**:
    ```json
    {
        "questions": {
            "question1": {
                "question": "What is the capital of France?",
                "options": [
                    "Berlin",
                    "Madrid",
                    "Paris",
                    "Rome"
                ],
                "correct_answer": "Paris",
                "hint": "It's known as the city of love.",
                "justification": "Paris is the capital of France and is widely recognized for its cultural and historical significance."
            }
        }
    }
    ```

##### Error Responses Questions

- **Bad Request**:
    - **Status Code**: `400 Bad Request`
    - **Content-Type**: `application/json`
    - **Description**: Returned when the request is missing required fields or has invalid values.
    - **Example**:
    ```json
    {
        "error": "No files received"
    }
    ```
    ```json
    {
        "error": "File name exceeds the maximum length of 100 characters"
    }
    ```
    ```json
    {
        "error": "Invalid format. Supported formats: 'pdf', 'md'"
    }
    ```
    ```json
    {
        "error": "The filename seems suspicious and contains a blocked extension: '.py', '.sh', '.bat', '.cmd', '.ps1', '.exe', '.js' (...)"
    }
    ```
    ```json
    {
        "error": "Invalid file type. Detected: {detected_mime_type}. Expected: {expected_mime_type}"
    }
    ```
    ```json
    {
        "error": "Error during chat generation"
    }
    ```
    ```json
    {
        "error": "Error during text extraction from the file"
    }
    ```

- **413 Payload Too Large**:
    - **Status Code**: `413 Payload Too Large`
    - **Content-Type**: `application/json`
    - **Description**: Returned when the uploaded file size exceeds 5 MB.
    - **Example**:
    ```json
    {
        "error": "File size exceeds the maximum limit of 5 MB."
    }
    ```

- **500 Internal Server Error**:
    - **Status Code**: `500 Internal Server Error`
    - **Content-Type**: `application/json`
    - **Description**: Returned when an internal error occurs.
    - **Example**:
    ```json
    {
        "error": "An error occurred while processing the request"
    }
    ```

### Example Use Case

#### Frontend Integration

Integrating the Lectify Flask API into a frontend application is straightforward. Below is an example of how to send a request to the API using JavaScript and the fetch function.

```js
import { DataSummarize } from "../types/DataSummarize";
import axios from "axios";

export const summaryRequest = async (data: DataSummarize) => {    
    try  {
        const response  = await axios.post(${process.env.NEXT_PUBLIC_LECTIFY_API_SUMMARY}, data, { responseType: 'blob' });

        const downloadUrl = URL.createObjectURL(response.data); 

        return {
            data: downloadUrl,
            code: response.status,
        }
    } catch (error: any) {
        if (error.response) {
            const { status, data } = error.response;

            if (status === 400) {
                console.log(error)
                return { error: data.error };
            }
        }
        console.log(error)
        return { error: "Processing error" };
    }
}
```

```js
import axios from "axios";
export const quizRequest = async (formData: FormData) => {
    try {
        const response = await axios.post(${process.env.NEXT_PUBLIC_LECTIFY_API_QUESTIONS}, formData);

        return {
            data: response.data,
            code: response.status
        }
    } catch (error: any) {
        if (error.response) {
            const { status, data } = error.response;

            if (status === 413) {
                return { error: "file size exceeds the maximum limit of 5 mb." };
            }

            if (status === 400) {
                return { error: data.error };
            }
        }

        return { error: "Processing error" };
    }
}
```

## Acknowledgments

This project was developed in collaboration with [Francine Cruz](https://github.com/Francine02), who contributed to the frontend part. Her collaboration was essential in integrating the API with a modern interface,  featuring dynamic animations, providing an optimized user experience.

For a live demonstration of the API in action, visit [Lectify](https://lectify.vercel.app/), where the API has been fully integrated into an interactive platform.

## License

This project is licensed under the terms of the [Apache License 2.0](http://www.apache.org/licenses/LICENSE-2.0). See the [LICENSE](./LICENSE) file for details.