from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .logger import setup_logger
from .runner import check_docker_available, run_code_in_sandbox
from .schemas import ExecuteRequest, ExecuteResponse, HealthResponse

service_logger = setup_logger("service")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    docker_ok = await check_docker_available()
    if docker_ok:
        service_logger.info("Docker Daemon erfolgreich erkannt und einsatzbereit.")
    else:
        service_logger.warning("WARNUNG: Docker Daemon ist aktuell nicht erreichbar!")
    yield
    service_logger.info("Code Execution Service wird heruntergefahren.")


app = FastAPI(
    title="Code Execution Service",
    description="Isolierte Codeausführungsumgebung für die Hetzner-Cloud-Praxisarbeit",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS erlauben für lokale Entwicklung und direkte Frontend-Anbindung
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Info"])
async def root_info() -> dict:
    return {
        "service": "Code Execution Service",
        "description": "Isolierte Sandbox-Ausführung für Python, JavaScript und Java",
        "version": "1.0.0",
        "endpoints": {
            "execute": "POST /execute",
            "health": "GET /health",
            "docs": "/docs",
        },
    }


@app.post(
    "/execute",
    response_model=ExecuteResponse,
    status_code=status.HTTP_200_OK,
    tags=["Execution"],
    summary="Führt Code in einem isolierten Docker-Container aus",
)
@app.post(
    "/api/execute",
    response_model=ExecuteResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def execute_code(request: ExecuteRequest) -> ExecuteResponse:
    """
    Nimmt Code entgegen, führt ihn in einer sicheren Docker-Sandbox aus
    und liefert stdout, stderr, exitCode sowie Ausführungsdauer zurück.
    """
    try:
        response = await run_code_in_sandbox(request)
        return response
    except Exception as exc:
        service_logger.error(f"Unerwarteter Fehler bei /execute: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Interner Verarbeitungsfehler: {str(exc)}",
        )


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Prüft den Zustand des Ausführungsdienstes und des Docker-Daemons",
)
@app.get(
    "/api/health",
    response_model=HealthResponse,
    include_in_schema=False,
)
async def health_check() -> HealthResponse:
    docker_available = await check_docker_available()
    overall_status = "healthy" if docker_available else "degraded"
    message = (
        "Dienst und Docker-Sandbox sind einsatzbereit."
        if docker_available
        else "Dienst läuft, aber Docker-Daemon ist nicht erreichbar."
    )

    return HealthResponse(
        status=overall_status,
        service="execution-runner",
        supportedLanguages=list(settings.LANGUAGES.keys()),
        dockerAvailable=docker_available,
        message=message,
    )
