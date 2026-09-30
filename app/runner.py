import asyncio
import os
import shutil
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple

from .config import settings
from .logger import log_execution_audit
from .schemas import ExecuteRequest, ExecuteResponse


async def check_docker_available() -> bool:
    """Prüft, ob der Docker-Daemon auf dem Host erreichbar ist."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "docker",
            "info",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        returncode = await proc.wait()
        return returncode == 0
    except Exception:
        return False


def _truncate_output(data: bytes, max_bytes: int) -> str:
    """Kürzt die Konsolenausgabe, falls ein Endlos-Log vorliegt."""
    if len(data) <= max_bytes:
        return data.decode("utf-8", errors="replace")
    truncated = data[:max_bytes].decode("utf-8", errors="replace")
    return truncated + f"\n[Hinweis: Ausgabe bei {max_bytes // 1024} KB abgeschnitten (Limit erreicht)]"


async def run_code_in_sandbox(request: ExecuteRequest) -> ExecuteResponse:
    """
    Führt den übergebenen Code in einem isolierten Docker-Container aus.
    Erfüllt die Sicherheitsanforderungen A5 (Isolation, Limits, Timeout)
    und A6 (Audit-Logging ohne Code-Leaks).
    """
    job_id = str(uuid.uuid4())
    container_name = f"runner-job-{job_id}"
    lang_cfg = settings.LANGUAGES[request.language.value]

    job_dir = Path(settings.BASE_TEMP_DIR) / f"job_{job_id}"
    code_file = job_dir / lang_cfg.filename

    start_time = time.perf_counter()
    exit_code = -1
    stdout_str = ""
    stderr_str = ""
    status_label = "unknown"

    try:
        # 1. Ephemeres Verzeichnis erstellen mit Lesezugriff für Non-Root (1000:1000)
        os.makedirs(job_dir, mode=0o755, exist_ok=True)
        # Explizites chmod, da umask das Verzeichnis sonst einschränken könnte
        os.chmod(job_dir, 0o755)

        # 2. Code in Datei schreiben
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(request.code)
        os.chmod(code_file, 0o644)

        # 3. Docker-Run-Befehl nach Anforderung A5 zusammenstellen
        # Für Java kompilieren wir in ein tmpfs (/tmp), damit das Rootfs read-only bleiben kann
        if request.language.value == "java":
            exec_command = ["sh", "-c", "javac -d /tmp /app/Main.java && java -cp /tmp Main"]
        else:
            exec_command = lang_cfg.command

        docker_cmd = [
            "docker",
            "run",
            "--rm",
            "--name",
            container_name,
            "--network",
            "none",  # Strikte Netzwerkisolation (kein Internet / internes Netz)
            "--memory",
            lang_cfg.memory_limit,
            "--memory-swap",
            lang_cfg.memory_swap,
            "--cpus",
            lang_cfg.cpus,
            "--pids-limit",
            str(lang_cfg.pids_limit),  # Schutz vor Fork-Bombs
            "--user",
            lang_cfg.user,  # Non-Root Benutzer (1000:1000)
            "--cap-drop",
            "ALL",  # Alle Kernel-Capabilities entziehen
            "--read-only",  # Schreibgeschütztes Container-Dateisystem
            "--tmpfs",
            "/tmp:rw,exec,size=64m,mode=1777",  # Ephemerer RAM-Speicher für Java-Bytecode
            "-v",
            f"{code_file.resolve()}:/app/{lang_cfg.filename}:ro",  # Read-Only Mount
            lang_cfg.image,
            *exec_command,
        ]

        # 4. Asynchronen Prozess starten
        proc = await asyncio.create_subprocess_exec(
            *docker_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            # 5. Mit Timeout ausführen (Anforderung A5 / settings.TIMEOUT_SECONDS)
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(),
                timeout=settings.TIMEOUT_SECONDS,
            )
            exit_code = proc.returncode if proc.returncode is not None else 1
            stdout_str = _truncate_output(stdout_bytes, settings.MAX_OUTPUT_SIZE_BYTES)
            stderr_str = _truncate_output(stderr_bytes, settings.MAX_OUTPUT_SIZE_BYTES)

            if exit_code == 0:
                status_label = "success"
            else:
                status_label = "runtime_error"

        except asyncio.TimeoutError:
            # Timeout greift: Container sofort stoppen/killen
            exit_code = 124
            status_label = "timeout"
            stderr_str = f"Execution timed out after {settings.TIMEOUT_SECONDS:.1f} seconds (Limit exceeded)"
            
            # Docker killen, falls er noch im Hintergrund hängt
            try:
                kill_proc = await asyncio.create_subprocess_exec(
                    "docker",
                    "kill",
                    container_name,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await kill_proc.wait()
            except Exception:
                pass

            # Prozess beenden
            try:
                proc.kill()
                await proc.wait()
            except Exception:
                pass

    except Exception as exc:
        exit_code = 500
        status_label = "system_error"
        stderr_str = f"Interner Systemfehler bei der Ausführung: {str(exc)}"

    finally:
        # 6. Ephemeren Host-Speicher restlos bereinigen (Lifecycle-Hygiene)
        if job_dir.exists():
            shutil.rmtree(job_dir, ignore_errors=True)

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        timestamp = datetime.now(timezone.utc).isoformat()

        # 7. Audit-Log schreiben (Anforderung A6 - Metadaten only, KEIN Code!)
        log_execution_audit(
            job_id=job_id,
            language=request.language.value,
            duration_ms=duration_ms,
            exit_code=exit_code,
            status=status_label,
        )

    return ExecuteResponse(
        jobId=job_id,
        stdout=stdout_str,
        stderr=stderr_str,
        exitCode=exit_code,
        executionTimeMs=duration_ms,
        timestamp=timestamp,
    )
