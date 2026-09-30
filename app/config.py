import os
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class LanguageConfig:
    image: str
    filename: str
    command: List[str]
    memory_limit: str = "128m"
    memory_swap: str = "128m"
    cpus: str = "0.5"
    pids_limit: int = 64
    user: str = "1000:1000"


class Settings:
    # Server-Konfiguration
    HOST: str = os.getenv("RUNNER_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("RUNNER_PORT", "8080"))
    
    # Sicherheitslimits (Anforderung A5, synchronisiert mit test.tfvars)
    TIMEOUT_SECONDS: float = float(os.getenv("RUNNER_TIMEOUT_SECONDS", "10.0"))
    MAX_CODE_SIZE_BYTES: int = int(os.getenv("RUNNER_MAX_CODE_BYTES", str(64 * 1024)))  # 64 KB
    MAX_OUTPUT_SIZE_BYTES: int = int(os.getenv("RUNNER_MAX_OUTPUT_BYTES", str(64 * 1024)))  # 64 KB
    
    # Temporäres Verzeichnis auf dem Host
    BASE_TEMP_DIR: str = os.getenv("RUNNER_TEMP_DIR", "/tmp/runner")

    # Sprachdefinitionen & Container-Vorgaben
    LANGUAGES: Dict[str, LanguageConfig] = {
        "python": LanguageConfig(
            image=os.getenv("IMAGE_PYTHON", "python:3.11-alpine"),
            filename="main.py",
            command=["python3", "/app/main.py"],
            memory_limit=os.getenv("RUNNER_MEMORY_LIMIT", "512m"),
            memory_swap=os.getenv("RUNNER_MEMORY_LIMIT", "512m"),
            cpus=os.getenv("RUNNER_CPUS", "1.0"),
            pids_limit=int(os.getenv("RUNNER_PIDS", "64")),
            user="1000:1000",
        ),
        "javascript": LanguageConfig(
            image=os.getenv("IMAGE_JAVASCRIPT", "node:20-alpine"),
            filename="index.js",
            command=["node", "/app/index.js"],
            memory_limit=os.getenv("RUNNER_MEMORY_LIMIT", "512m"),
            memory_swap=os.getenv("RUNNER_MEMORY_LIMIT", "512m"),
            cpus=os.getenv("RUNNER_CPUS", "1.0"),
            pids_limit=int(os.getenv("RUNNER_PIDS", "64")),
            user="1000:1000",
        ),
        "java": LanguageConfig(
            image=os.getenv("IMAGE_JAVA", "eclipse-temurin:21-alpine"),
            filename="Main.java",
            command=["sh", "-c", "javac /app/Main.java && java -cp /app Main"],
            memory_limit=os.getenv("RUNNER_MEMORY_LIMIT", "512m"),
            memory_swap=os.getenv("RUNNER_MEMORY_LIMIT", "512m"),
            cpus=os.getenv("RUNNER_CPUS", "1.0"),
            pids_limit=int(os.getenv("RUNNER_PIDS", "64")),
            user="1000:1000",
        ),
    }


settings = Settings()
