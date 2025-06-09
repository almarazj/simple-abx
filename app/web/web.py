from fastapi import APIRouter, Request, Depends, Body, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy import select
from app.core.config import settings
from app.database.session import get_db
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
    db=Depends(get_db)
):
    user_id = str(uuid.uuid4())
    test_result = TestResult(
        user_id=user_id,
        participant_info=form.model_dump(),
        start_time=datetime.now(),
        created_at=datetime.now()
    )
    db.add(test_result)
    await db.commit()
    await db.refresh(test_result)
    return RedirectResponse(url=f"/calibration?user_id={user_id}", status_code=303)


@web_router.get("/test", response_class=HTMLResponse)
async def test(request: Request, db=Depends(get_db)):
    # Obtener usuario
    user_id = request.query_params.get("user_id")
    
    # Obtener resultados del test
    result = await db.execute(select(TestResult).where(TestResult.user_id == user_id))
    test_result = result.scalar_one_or_none()
    
    if not test_result or not test_result.test_config:
        generator = ABXTestGenerator()
        comparisons = generator.generate_test_sequence()
        if not test_result:
            # Crea el registro si no existe
            test_result = TestResult(user_id=user_id, test_config={}, responses=[], participant_info={})
            db.add(test_result)
        test_result.test_config = {"comparisons": comparisons}
        await db.commit()
        await db.refresh(test_result)
    else:
        # Si ya existe, obtener las comparaciones
        comparisons = test_result.test_config.get("comparisons", [])
    
    current = len(test_result.responses or [])
    if current < len(comparisons):
        comparison = comparisons[current]
        return templates.TemplateResponse("test.html", 
            {"request": request, "user_id": user_id, "comparison": comparison, "current": current + 1, "total": len(comparisons), "config": settings}
        )
    else:
        comparison = None  # Test terminado
        return RedirectResponse(url=f"/results?user_id={user_id}", status_code=303)
    
        
@web_router.post("/submit_response")
async def submit_response(
    request: Request,
    db=Depends(get_db),
    data: dict = Body(...)
):
    user_id = data.get("user_id")
    response = data.get("response")

    # Buscar el test del usuario
    result = await db.execute(select(TestResult).where(TestResult.user_id == user_id))
    test_result = result.scalar_one_or_none()
    if not test_result:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"status": "error", "message": "Test no encontrado"}
        )

    comparisons = test_result.test_config.get("comparisons", [])
    current = len(test_result.responses or [])
    
    correct = None
    if current < len(comparisons):
        correct_answer = comparisons[current].get("correct_answer")
        correct = (response == correct_answer.lower())
    
    # Agregar la respuesta
    test_result.responses.append({
        "response": response,
        "correct": correct
    })
    
    await db.commit()
    await db.refresh(test_result)

    current += 1

    # Si terminó el test, redirige a resultados
    if current >= len(comparisons):
        return JSONResponse({
            "status": "completed",
            "redirect": f"/results?user_id={user_id}"
        })

    # Si no, continúa al siguiente
    return JSONResponse({
        "status": "continue",
        "next_comparison": comparisons[current],
        "current": current + 1,
        "total": len(comparisons)
    })


@web_router.get("/results", response_class=HTMLResponse)
async def results(request: Request, db=Depends(get_db)):
    user_id = request.query_params.get("user_id")
    # Buscar el test del usuario
    result = await db.execute(select(TestResult).where(TestResult.user_id == user_id))
    test_result = result.scalar_one_or_none()

    # Valores por defecto si no hay resultados
    total_comparisons = 0
    correct_responses = 0
    accuracy_percentage = 0

    if test_result and test_result.responses:
        total_comparisons = len(test_result.responses)
        correct_responses = sum(1 for r in test_result.responses if r.get("correct") is True)
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