import json
import logging
from app.logger import JsonFormatter, log_execution_audit, setup_logger


def test_json_formatter_sanitizes_secrets():
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test execution message",
        args=(),
        exc_info=None,
    )
    # Metadaten mit sensiblen Schlüsseln anhängen
    record.audit_data = {
        "jobId": "test-uuid-123",
        "durationMs": 150,
        "exitCode": 0,
        "code": "print('sensitive secret code')",
        "token": "secret-token-xyz",
        "password": "super-secret-password",
    }

    formatted = formatter.format(record)
    data = json.loads(formatted)

    assert data["message"] == "Test execution message"
    assert "audit" in data
    audit = data["audit"]

    # Erlaubte Metadaten müssen vorhanden sein
    assert audit["jobId"] == "test-uuid-123"
    assert audit["durationMs"] == 150
    assert audit["exitCode"] == 0

    # Geheimnisse & Code dürfen NIEMALS im Audit-Log landen (Anforderung A6)
    assert "code" not in audit
    assert "token" not in audit
    assert "password" not in audit
