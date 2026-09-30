from enum import Enum
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class SupportedLanguage(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"


class ExecuteRequest(BaseModel):
    language: SupportedLanguage = Field(
        ...,
        description="Programmiersprache des auszuführenden Codes ('python', 'javascript', 'java')",
    )
    code: str = Field(
        ...,
        min_length=1,
        max_length=65536,
        description="Auszuführender Quellcode (maximal 64 KB)",
    )


class ExecuteResponse(BaseModel):
    jobId: str = Field(..., description="Eindeutige UUID des Ausführungsauftrags")
    stdout: str = Field(..., description="Standardausgabe des Programms")
    stderr: str = Field(..., description="Fehlerausgabe des Programms oder Laufzeitfehler")
    exitCode: int = Field(..., description="Prozess-Exit-Code (0 = Erfolg, >0 = Fehler, 124 = Timeout)")
    executionTimeMs: int = Field(..., description="Reine Ausführungsdauer in Millisekunden")
    timestamp: str = Field(..., description="ISO-8601 Zeitstempel des Abschlusses")


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"] = Field(..., description="Gesamtstatus des Dienstes")
    service: str = Field(default="execution-runner", description="Name des Dienstes")
    supportedLanguages: List[str] = Field(..., description="Liste der konfigurierten Sprachen")
    dockerAvailable: bool = Field(..., description="Gibt an, ob der Docker-Daemon ansprechbar ist")
    message: Optional[str] = Field(None, description="Zusätzliche Diagnose- oder Statusmeldung")
