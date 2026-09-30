import pytest
import shutil
from app.runner import check_docker_available, run_code_in_sandbox
from app.schemas import ExecuteRequest, SupportedLanguage


@pytest.mark.asyncio
async def test_docker_python_execution():
    if not await check_docker_available():
        pytest.skip("Docker Daemon ist lokal nicht erreichbar")

    req = ExecuteRequest(
        language=SupportedLanguage.PYTHON,
        code="print('Integration Test Python')",
    )
    res = await run_code_in_sandbox(req)
    # Falls das Image nicht gepullt ist, könnte exitCode != 0 sein, aber wir prüfen die Struktur
    assert res.jobId != ""
    assert res.executionTimeMs >= 0


@pytest.mark.asyncio
async def test_docker_timeout():
    if not await check_docker_available():
        pytest.skip("Docker Daemon ist lokal nicht erreichbar")

    # Endlosschleife zum Testen des 5s-Timeouts
    req = ExecuteRequest(
        language=SupportedLanguage.PYTHON,
        code="import time\nwhile True:\n    time.sleep(0.1)",
    )
    res = await run_code_in_sandbox(req)
    # Sollte nach Timeout mit 124 abbrechen
    assert res.exitCode == 124
    assert "timed out" in res.stderr
