from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
VENV_SITE_PACKAGES = [
    ROOT / "backend" / ".venv" / "Lib" / "site-packages",
    ROOT
    / "backend"
    / ".venv"
    / "lib"
    / f"python{sys.version_info.major}.{sys.version_info.minor}"
    / "site-packages",
]
for site_packages in VENV_SITE_PACKAGES:
    if site_packages.exists():
        sys.path.insert(1, str(site_packages))

os.environ.setdefault("ENV", "local")
os.environ.setdefault("JWT_SECRET", "x" * 32)
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://x:x@localhost/x")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")


def _run_with_backend_venv_if_available() -> None:
    if os.environ.get("OPENAPI_EXPORT_BACKEND_VENV") == "1":
        return

    candidates = [
        ROOT / "backend" / ".venv" / "Scripts" / "python.exe",
        ROOT / "backend" / ".venv" / "bin" / "python",
    ]
    for candidate in candidates:
        if candidate.exists() and Path(sys.executable).resolve() != candidate.resolve():
            env = os.environ.copy()
            env["OPENAPI_EXPORT_BACKEND_VENV"] = "1"
            completed = subprocess.run(
                [str(candidate), str(Path(__file__).resolve()), *sys.argv[1:]],
                check=False,
                env=env,
            )
            raise SystemExit(completed.returncode)


_run_with_backend_venv_if_available()

from app.main import create_app  # noqa: E402


def main() -> None:
    schema = create_app().openapi()
    output_path = ROOT / "docs" / "openapi.json"
    output_path.write_text(
        json.dumps(schema, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    generated_at = datetime.now(UTC).isoformat()
    version = schema.get("info", {}).get("version", "unknown")
    print(f"generated_at={generated_at} version={version} output={output_path}")


if __name__ == "__main__":
    main()
