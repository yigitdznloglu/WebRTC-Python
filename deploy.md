# AIORTC Communication Deployment

## Prerequisites

- Docker
- Minikube
- kubectl

## Starting Minikube

1. Start Minikube with the Docker driver:
    ```sh
    minikube start --driver=docker
    ```

2. Set up the Docker environment to build images within Minikube:
    ```sh
    eval $(minikube -p minikube docker-env)
    ```

## Building Docker Images

1. Build the Docker image for the server:
    ```sh
    docker build -t myapp-server -f Dockerfile.server .
    ```

2. Build the Docker image for the client:
    ```sh
    docker build -t myapp-client -f Dockerfile.client .
    ```

## Deploying to Kubernetes

1. Apply the server deployment and service:
    ```sh
    kubectl apply -f server-deployment.yaml
    ```

2. Apply the client deployment:
    ```sh
    kubectl apply -f client-deployment.yaml
    ```

## Verifying the Deployment

1. Check the status of the deployments:
    ```sh
    kubectl get deployments
    ```

2. Check the status of the pods:
    ```sh
    kubectl get pods
    ```

3. To view logs of the server or client pod:
    ```sh
    kubectl logs <pod-name>
    ```

## Cleanup

To delete the deployments and services:
```sh
kubectl delete -f server-deployment.yaml
kubectl delete -f client-deployment.yaml
