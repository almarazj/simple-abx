from fastapi import APIRouter, Request, Depends, Body, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
from app.core.config import settings
from app.schemas.participant_info import ParticipantInfo
from app.crud.results import export_to_csv
from app.crud.test import (
    update_test_results, 
    create_participant_result, 
    get_test_info,
    submit_test_response,
    get_results,
    get_dashboard_data
)

web_router = APIRouter()
templates = Jinja2Templates(directory=settings.TEMPLATES_DIR)


@web_router.get("/sitemap.xml", response_class=FileResponse)
def sitemap():
    return FileResponse("static/sitemap.xml", media_type="application/xml")


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
    stats = get_results(user_id)
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
    dashboard_data = get_dashboard_data()
    return templates.TemplateResponse(
        "admin/dashboard.html", 
        {"request": request, **dashboard_data.model_dump(), "config": settings})


@web_router.get(
    "/admin/export_csv",
    response_class=FileResponse,
    tags=["Admin"],
    summary="Exportar resultados",
    description="Genera y descarga un archivo CSV con los resultados de los tests."
)
def export_csv():
    filepath = export_to_csv()
    return FileResponse(
        path=filepath,
        filename="abx_resultados.csv",
        media_type="text/csv"
    )
