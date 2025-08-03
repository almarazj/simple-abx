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