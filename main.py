#!/usr/bin/env python3
"""Start the FastAPI application that serves the complete web frontend."""

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR / "backend"))


def main():
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
