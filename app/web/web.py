from fastapi import APIRouter, Request, Depends, Body, status, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from app.core.config import settings
from app.database.session import get_firestore_collection
from app.utils.test_config import ABXTestGenerator
from app.database.models import TestResult
from app.models.schemas import ParticipantInfoCreate
from app.models.enums import AudioExperience, HeadphonesType, ListeningEnvironment, AgeRange
import uuid
from datetime import datetime

web_router = APIRouter()
templates = Jinja2Templates(directory=settings.TEMPLATES_DIR)

def get_templates() -> Jinja2Templates:
    return templates


def save_response_background(collection, user_id, test_result):
    collection.document(user_id).set(test_result)


@web_router.get("/", response_class=HTMLResponse)
def welcome(request: Request):
    return templates.TemplateResponse(
        "welcome.html",
        {
            "request": request,
            "config": settings,
            "age_range_options": list(AgeRange),
            "audio_experience_options": list(AudioExperience),
            "headphones_type_options": list(HeadphonesType),
            "listening_environment_options": list(ListeningEnvironment),
        }
    )


@web_router.get("/calibration", response_class=HTMLResponse)
def calibration(request: Request):
    return templates.TemplateResponse("calibration.html", {"request": request,  "config": settings})


@web_router.post("/participant_info")
async def participant_info(
    request: Request,
    form: ParticipantInfoCreate = Depends(ParticipantInfoCreate.as_form),
    background_tasks: BackgroundTasks = None
):
    user_id = str(uuid.uuid4())
    test_result = TestResult(
        user_id=user_id,
        participant_info=form.model_dump(),
        start_time=datetime.now(),
        created_at=datetime.now(),
        end_time=None,
        responses=[],
        test_config={},
        statistics={}
    )
    collection = get_firestore_collection()
    result = test_result.to_dict()
    background_tasks.add_task(save_response_background, collection, user_id, result)
    return RedirectResponse(url=f"/calibration?user_id={user_id}", status_code=303)


@web_router.get("/test", response_class=HTMLResponse)
async def test(request: Request, background_tasks: BackgroundTasks = None):
    user_id = request.query_params.get("user_id")
    collection = get_firestore_collection()
    doc = collection.document(user_id).get()
    test_result = doc.to_dict() if doc.exists else None

    if not test_result or not test_result.get("test_config"):
        generator = ABXTestGenerator()
        comparisons = generator.generate_test_sequence()
        if not test_result:
            test_result = TestResult(user_id=user_id, test_config={}, responses=[], participant_info={}).to_dict()
        test_result["test_config"] = {"comparisons": comparisons}
        background_tasks.add_task(save_response_background, collection, user_id, test_result)
    else:
        comparisons = test_result["test_config"].get("comparisons", [])

    current = len(test_result.get("responses", []))
    if current < len(comparisons):
        comparison = comparisons[current]
        return templates.TemplateResponse("test.html", 
            {"request": request, "user_id": user_id, "comparison": comparison, "current": current + 1, "total": len(comparisons), "config": settings}
        )
    else:
        return RedirectResponse(url=f"/results?user_id={user_id}", status_code=303)


@web_router.post("/submit_response")
async def submit_response(
    request: Request,
    data: dict = Body(...),
    background_tasks: BackgroundTasks = None
):
    user_id = data.get("user_id")
    response = data.get("response")
    collection = get_firestore_collection()
    doc = collection.document(user_id).get()
    test_result = doc.to_dict() if doc.exists else None
    if not test_result:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"status": "error", "message": "Test no encontrado"}
        )
    comparisons = test_result["test_config"].get("comparisons", [])
    current = len(test_result.get("responses", []))
    correct = None
    if current < len(comparisons):
        correct_answer = comparisons[current].get("correct_answer")
        correct = (response == correct_answer.lower())
    test_result["responses"].append({
        "response": response,
        "correct": correct
    })
    background_tasks.add_task(save_response_background, collection, user_id, test_result)
    current += 1
    if current >= len(comparisons):
        return JSONResponse({
            "status": "completed",
            "redirect": f"/results?user_id={user_id}",
            "current": current,
            "total": len(comparisons)
        })
    return JSONResponse({
        "status": "continue",
        "next_comparison": comparisons[current],
        "current": current + 1,
        "total": len(comparisons)
    })


@web_router.get("/results", response_class=HTMLResponse)
async def results(request: Request):
    user_id = request.query_params.get("user_id")
    collection = get_firestore_collection()
    doc = collection.document(user_id).get()
    test_result = doc.to_dict() if doc.exists else None
    total_comparisons = 0
    correct_responses = 0
    accuracy_percentage = 0
    if test_result and test_result.get("responses"):
        total_comparisons = len(test_result["responses"])
        correct_responses = sum(1 for r in test_result["responses"] if r.get("correct") is True)
        accuracy_percentage = round((correct_responses / total_comparisons) * 100, 1) if total_comparisons > 0 else 0
    stats = {
        "total_comparisons": total_comparisons,
        "correct_responses": correct_responses,
        "accuracy_percentage": accuracy_percentage
    }
    return templates.TemplateResponse(
        "results.html",
        {"request": request, "stats": stats, "config": settings}
    )