#!/bin/bash

# Configuraciones
IMAGE_NAME="us-central1-docker.pkg.dev/simple-abx/abx-repo/abx-app:latest"
SERVICE_NAME="abx-app"
REGION="us-central1"
SERVICE_ACCOUNT="cloudrun-firestore@simple-abx.iam.gserviceaccount.com"
PORT="8080"

# 1. Reconstruir la imagen
echo "Building docker image..."
docker build -t $IMAGE_NAME .

# 2. Subir la imagen a Artifact Registry
echo "Pushing image..."
docker push $IMAGE_NAME

# 3. Desplegar en Cloud Run
echo "Deploying in cloud run..."
gcloud run deploy $SERVICE_NAME \
  --image=$IMAGE_NAME \
  --platform=managed \
  --region=$REGION \
  --allow-unauthenticated \
  --service-account=$SERVICE_ACCOUNT \
  --port=$PORT

echo "Deploy complete."