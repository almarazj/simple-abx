#!/bin/bash

# Verificamos el argumento
if [ "$1" == "--dev" ]; then
  echo "Entorno seleccionado: Desarrollo"
  TAG="develop"
  SERVICE_NAME="abx-app-dev"
  DOMAIN="develop.abxtest.online"
elif [ "$1" == "--prd" ]; then
  echo "Entorno seleccionado: Producción"
  TAG="latest"
  SERVICE_NAME="abx-app"
  DOMAIN="abxtest.online"
else
  echo "Uso: ./deploy.sh [--dev | --prd]"
  exit 1
fi

# Configuraciones comunes
REGION="us-central1"
PROJECT="simple-abx"
REPO="abx-repo"
IMAGE_NAME="us-central1-docker.pkg.dev/$PROJECT/$REPO/abx-app:$TAG"
SERVICE_ACCOUNT="cloudrun-firestore@$PROJECT.iam.gserviceaccount.com"
PORT="8080"

# Mostrar información del despliegue
echo ""
echo "======================="
echo "Resumen del despliegue:"
echo "======================="
echo " ➤ Entorno:            $TAG"
echo " ➤ Imagen:             $IMAGE_NAME"
echo " ➤ Servicio:           $SERVICE_NAME"
echo " ➤ Región:             $REGION"
echo " ➤ Servicio Account:   $SERVICE_ACCOUNT"
echo " ➤ Dominio esperado:   https://$DOMAIN"
echo ""

# Confirmación interactiva
read -p "¿Deseás continuar con el despliegue? (y/n): " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
  echo "Despliegue cancelado."
  exit 0
fi

# 1. Construir imagen Docker
echo ""
echo "🔧 Construyendo imagen Docker..."
docker build -t $IMAGE_NAME .

# 2. Subir imagen a Artifact Registry
echo "📤 Subiendo imagen a Artifact Registry..."
docker push $IMAGE_NAME

# 3. Desplegar en Cloud Run
echo "🚀 Desplegando en Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image=$IMAGE_NAME \
  --platform=managed \
  --region=$REGION \
  --allow-unauthenticated \
  --service-account=$SERVICE_ACCOUNT \
  --port=$PORT

echo ""
echo "✅ Despliegue completado con éxito para el entorno '$TAG'"
echo "🌐 Accedé en: https://$DOMAIN"
