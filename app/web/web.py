from fastapi import APIRouter, Request, Depends, Body, status, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from app.core.config import settings
from app.database.session import get_firestore_collection
from app.utils.test_config import ABXTestGenerator
from app.database.models import TestResult
from app.models.schemas import ParticipantInfoCreate
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
    return templates.TemplateResponse("welcome.html", {"request": request, "config": settings})


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


@web_router.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    collection = get_firestore_collection()
    
    docs = collection.stream()
    results = []
    
    for doc in docs:
        data = doc.to_dict()
        
        if not data:
            continue
        
        data["user_id"] = doc.id
        
        results.append(data)

        # Datos para gráficos por tipo de estímulo
    from collections import defaultdict
    import re

    def extract_stimulus(variation_id):
        match = re.search(r"(drum|flute|vocal)", variation_id)
        return match.group(1) if match else "unknown"

    def format_variation_id(variation_id):
        match = re.search(r"ovn(\d+)_", variation_id)
        if match:
            return f"{int(match.group(1))} p/s"
        return "formato inválido"

    def extract_variation_number(variation_id):
        match = re.search(r"ovn(\d+)_", variation_id)
        return int(match.group(1)) if match else float('inf') 

    # Inicializar estructura de estadísticas por variation_id
    pair_stats = {}

    for result in results:
        responses = result.get("responses", [])
        comparisons = result.get("test_config", {}).get("comparisons", [])

        for idx, response in enumerate(responses):
            if idx >= len(comparisons):
                continue

            comp = comparisons[idx]
            variation_id = comp.get("pair_info").get("variation_id")
            if not variation_id:
                continue
            
            if variation_id not in pair_stats:
                pair_stats[variation_id] = {"correct": 0, "total": 0}

            pair_stats[variation_id]["total"] += 1
            if response.get("correct") is True:
                pair_stats[variation_id]["correct"] += 1
            if response.get("response") == "tie":
                pair_stats[variation_id]["correct"] += 0.5  # Considerar empate como medio correcto

    # Calcular estadísticas generales
    total_responses = sum(len(result.get("responses", [])) for result in results)
    correct_responses = sum(
        sum(
            1 if r.get("correct") is True else 0.5 if r.get("response") == "tie" else 0
            for r in result.get("responses", [])
        )
        for result in results
    )
    accuracy_percentage = round((correct_responses / total_responses) * 100, 1) if total_responses > 0 else 0

    stats = {
        "total_tests": len(results),
        "total_responses": total_responses,
        "correct_responses": correct_responses,
        "accuracy_percentage": accuracy_percentage
    }
    
    accuracy_data = defaultdict(list)
    response_data = defaultdict(list)

    # Agrupar por estímulo y por variation_id, y ordenarlos
    by_stimulus = defaultdict(list)

    for variation_id, data in pair_stats.items():
        stimulus = extract_stimulus(variation_id)
        acc = (data["correct"] / data["total"]) * 100 if data["total"] > 0 else 0
        number = extract_variation_number(variation_id)
        label = format_variation_id(variation_id)

        by_stimulus[stimulus].append({
            "variation_id": variation_id,
            "label": label,  # por ej. "100 p/s"
            "number": number,
            "accuracy": acc
        })
        accuracy_data[stimulus].append(acc)
        response_data[stimulus].append(data["total"])

    # Ordenar por número ascendente antes de pasar al template
    for stim in by_stimulus:
        by_stimulus[stim] = sorted(by_stimulus[stim], key=lambda x: x["number"])

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "stats": stats,
            "pair_stats": pair_stats,
            "accuracy_data": dict(accuracy_data),
            "response_data": dict(response_data),
            "stimulus_pairs": dict(by_stimulus),
            "results": results,
            "config": settings,
        }
    )
