"""Launcher local do Gnzl Achados.

Uso:
    python app.py

Sobe a API em http://127.0.0.1:8000. Durante o desenvolvimento, a interface
roda separada com `npm run dev` em frontend/ e usa o proxy /api do Vite.
"""

import sys
from pathlib import Path

import uvicorn

ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import get_settings  # noqa: E402
from app.main import create_app  # noqa: E402


def main() -> None:
    settings = get_settings()
    settings.ensure_data_dir()
    app = create_app(settings)

    print(f"gnzl achados - provedor: {settings.provider}")
    print(f"API: http://{settings.host}:{settings.port}/api/docs")

    uvicorn.run(app, host=settings.host, port=settings.port, log_level="info")


if __name__ == "__main__":
    main()
