from google.cloud import storage
from fastapi import APIRouter
from datetime import timedelta

storage_router = APIRouter()

@storage_router.get("/audio-url")
def get_signed_audio_url(filename: str):
    client = storage.Client()
    bucket = client.bucket("abxtest-files")
    blob = bucket.blob(f"velvet-noise-test/{filename}")

    url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=60),
        method="GET",
    )
    return {"url": url}


@storage_router.post("/move_results")
def move_results(
    document_id: str
): 
    from google.cloud import firestore
    
    client = firestore.Client()
    source_collection = client.collection("test-results-dev")
    destination_collection = client.collection("test-results-3.0")
    
    doc_ref = source_collection.document(document_id)
    doc = doc_ref.get()
    
    if not doc.exists:
        return {"error": "Document not found"}, 404
    
    data = doc.to_dict()
    
    destination_ref = destination_collection.document(document_id)
    destination_ref.set(data)
    
    print(f"Document {document_id} moved successfully.")
    return {"message": f"Document {document_id} moved successfully."}