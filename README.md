# Bouncing Ball WebRTC Project

This project demonstrates a simple WebRTC application where a ball bounces within a frame, and its coordinates are tracked and sent between a server and a client. The application uses Python, aiortc for WebRTC connections, OpenCV for video processing, and Docker for containerization.

## Table of Contents

- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Deployment](#deployment)
- [Usage](#usage)

## Project Structure

- `server.py`: The server code for generating video frames with a bouncing ball and handling WebRTC connections.
- `client.py`: The client code for receiving video frames and processing them to detect the ball's coordinates.
- `test_server.py`: Tests for the server functionality.
- `test_client.py`: Tests for the client functionality.
- `requirements.txt`: Python dependencies required for the project.
- `Dockerfile.server`: Dockerfile for the server container.
- `Dockerfile.client`: Dockerfile for the client container.
- `server-deployment.yaml`: Kubernetes deployment configuration for the server.
- `client-deployment.yaml`: Kubernetes deployment configuration for the client.
- `deploy.md`: Instructions for deploying the application on Kubernetes.

## Prerequisites

- Python 3.8+
- OpenCV
- Docker
- Kubernetes (optional, for deployment)

## Running the Application

### Using Docker

1. Build the Docker images:
    ```sh
    docker build -t server-image -f Dockerfile.server .
    docker build -t client-image -f Dockerfile.client .
    ```

2. Run the Docker containers:
    ```sh
    docker run -d --name server-container -p 8080:8080 server-image
    docker run -d --name client-container -p 8081:8081 client-image
    ```

### Locally

1. Run the server:
    ```sh
    python server.py offer --verbose
    ```

2. In a separate terminal, run the client:
    ```sh
    python client.py answer --verbose
    ```

## Testing

Run the tests using pytest:
```sh
pytest test_server.py
pytest test_client.py
```

## Deployment

For detailed deployment instructions, refer to `deploy.md`.

### Kubernetes

1. Apply the server deployment:
    ```sh
    kubectl apply -f server-deployment.yaml
    ```

2. Apply the client deployment:
    ```sh
    kubectl apply -f client-deployment.yaml
    ```

## Usage

The server generates video frames with a bouncing ball and sends them to the client via a WebRTC connection. The client receives the frames, processes them to detect the ball, and calculates its coordinates. The coordinates are then sent back to the server to calculate the error between the real and calculated positions.