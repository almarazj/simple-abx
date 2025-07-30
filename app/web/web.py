from fastapi import APIRouter, Request, Depends, Body, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from app.core.config import settings
from app.database.session import collection
from app.models.schemas import ParticipantInfo, DashboardContextSchema
from app.crud.test import (
    update_test_results, 
    create_participant_result, 
    get_test_info,
    submit_test_response
)

web_router = APIRouter()
templates = Jinja2Templates(directory=settings.TEMPLATES_DIR)


@web_router.get(
    "/",
    response_class=HTMLResponse,
    tags=["Público"],
    summary="Página de bienvenida",
    description="Muestra la página de inicio del sistema ABX."
)
def welcome(request: Request):
    return templates.TemplateResponse("welcome.html", {"request": request, "config": settings})


@web_router.get(
    "/calibration",
    response_class=HTMLResponse,
    tags=["Público"],
    summary="Página de calibración",
    description="Permite al usuario calibrar su sistema de audio antes de comenzar el test."
)
def calibration(request: Request):
    return templates.TemplateResponse("calibration.html", {"request": request,  "config": settings})


@web_router.post(
    "/participant_info",
    tags=["Test"],
    summary="Recibe información del participante",
    description="Guarda la información del participante y redirige a la calibración."
)
async def participant_info(
    request: Request,
    form: ParticipantInfo = Depends(ParticipantInfo.as_form),
    background_tasks: BackgroundTasks = None
):
    user_id, result = create_participant_result(form.model_dump())
    background_tasks.add_task(update_test_results, user_id, result)
    return RedirectResponse(url=f"/calibration?user_id={user_id}", status_code=303)


@web_router.get(
    "/test",
    response_class=HTMLResponse,
    tags=["Test"],
    summary="Página de test ABX",
    description="Muestra la interfaz del test ABX para el usuario actual."
)
async def test(
    request: Request, 
):
    user_id = request.query_params.get("user_id")
    current, comparisons = get_test_info(user_id)
    if current < len(comparisons):
        return templates.TemplateResponse("test.html", 
            {"request": request, "user_id": user_id, "comparison": comparisons[current], "current": current + 1, "total": len(comparisons), "config": settings}
        )
    else:
        return RedirectResponse(url=f"/results?user_id={user_id}", status_code=303)


@web_router.post(
    "/submit_response",
    tags=["Test"],
    summary="Envía respuesta de comparación",
    description="Recibe y almacena la respuesta del usuario para una comparación del test."
)
async def submit_response(
    request: Request,
    data: dict = Body(...),
    background_tasks: BackgroundTasks = None
):
    user_id = data.get("user_id")
    response = data.get("response")
    result = submit_test_response(user_id, response)
    if result.status == "completed":
        return JSONResponse(result.model_dump())
    return JSONResponse(result.model_dump())


@web_router.get(
    "/results",
    response_class=HTMLResponse,
    tags=["Resultados"],
    summary="Resultados individuales",
    description="Muestra los resultados individuales del usuario después de completar el test."
)
async def results(request: Request):
    user_id = request.query_params.get("user_id")
    doc = collection.document(user_id).get()
    test_result = doc.to_dict() if doc.exists else None
    total_comparisons = 0
    correct_responses = 0
    accuracy_percentage = 0
    if test_result and test_result.get("responses"):
        total_comparisons = len(test_result["responses"])
        correct_responses = sum(
            1 if r.get("correct") is True else 0.5 if r.get("response") == "tie" else 0
            for r in test_result.get("responses", [])
        )
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


@web_router.get(
    "/admin/dashboard",
    response_class=HTMLResponse,
    tags=["Admin"],
    summary="Dashboard administrativo",
    description="Panel administrativo con estadísticas globales y por estímulo de todos los tests realizados."
)
async def admin_dashboard(request: Request):
    docs = collection.stream()
    results = []

    for doc in docs:
        data = doc.to_dict()
        if not data:
            continue
        data["user_id"] = doc.id
        results.append(data)

    from collections import defaultdict

    pair_stats = {}

    for result in results:
        responses = result.get("responses", [])
        comparisons = result.get("test_config", {}).get("comparisons", [])

        for idx, response in enumerate(responses):
            if idx >= len(comparisons):
                continue

            comp = comparisons[idx]
            pair_info = comp.get("pair_info", {})
            pair_id = pair_info.get("pair_id", "unknown")
            stimulus = pair_info.get("stimulus_type", "unknown")
            pulse_density = pair_info.get("pulse_density", "unknown")

            if pair_id not in pair_stats:
                pair_stats[pair_id] = {
                    "stimulus": stimulus,
                    "pulse_density": pulse_density,
                    "correct": 0,
                    "total": 0
                }

            pair_stats[pair_id]["total"] += 1
            if response.get("correct") is True:
                pair_stats[pair_id]["correct"] += 1
            if response.get("response") == "tie":
                pair_stats[pair_id]["correct"] += 0.5

    # Estadísticas generales
    total_responses = sum(len(r.get("responses", [])) for r in results)
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

    # Datos para gráficos
    accuracy_data = defaultdict(list)
    response_data = defaultdict(list)
    by_stimulus = defaultdict(list)

    for pair_id, data in pair_stats.items():
        stimulus = data["stimulus"]
        density = data["pulse_density"]
        accuracy = (data["correct"] / data["total"]) * 100 if data["total"] > 0 else 0

        by_stimulus[stimulus].append({
            "label": f"{density} p/s",
            "pulse_density": int(density),
            "accuracy": accuracy,
            "pair_id": pair_id
        })
        accuracy_data[stimulus].append(accuracy)
        response_data[stimulus].append(data["total"])

    for stim in by_stimulus:
        by_stimulus[stim] = sorted(by_stimulus[stim], key=lambda x: x["pulse_density"])

    context = DashboardContextSchema(
        request=request,
        stats=stats,
        pair_stats=pair_stats,
        accuracy_data=dict(accuracy_data),
        response_data=dict(response_data),
        stimulus_pairs=dict(by_stimulus),
        results=results,
        config=settings,
    )
    
    return templates.TemplateResponse("admin/dashboard.html", context.model_dump())
