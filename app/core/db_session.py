from google.cloud import firestore
from app.core.config import settings

# Inicializar cliente Firestore
firestore_client = firestore.Client(project=settings.GOOGLE_PROJECT_ID)

collection = firestore_client.collection(settings.FIRESTORE_COLLECTION)