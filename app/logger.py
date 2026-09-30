import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class JsonFormatter(logging.Formatter):
    """
    Formatierer für strukturiertes JSON-Audit-Logging (Anforderung A6).
    Protokolliert strikt nur Metadaten (Job-ID, Dauer, Exit-Code, Sprache)
    und verhindert, dass Quelltexte oder Geheimnisse im Log landen.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Falls strukturierte Metadaten im LogRecord übergeben wurden
        if hasattr(record, "audit_data") and isinstance(record.audit_data, dict):
            # Streng darauf achten: Keine 'code' oder 'secret' Keys!
            sanitized_data = {
                k: v
                for k, v in record.audit_data.items()
                if k not in ("code", "payload", "token", "key", "secret", "password")
            }
            log_obj["audit"] = sanitized_data

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj, ensure_ascii=False)


def setup_logger(name: str = "execution_service") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)

    logger.propagate = False
    return logger


audit_logger = setup_logger("audit")


def log_execution_audit(
    job_id: str,
    language: str,
    duration_ms: int,
    exit_code: int,
    status: str,
    details: Optional[str] = None,
) -> None:
    """
    Protokolliert ein Ausführungsereignis strikt nach Anforderung A6.
    """
    audit_data = {
        "jobId": job_id,
        "language": language,
        "durationMs": duration_ms,
        "exitCode": exit_code,
        "status": status,
    }
    if details:
        audit_data["details"] = details

    audit_logger.info(
        f"Execution finished for job {job_id} with exit code {exit_code}",
        extra={"audit_data": audit_data},
    )
