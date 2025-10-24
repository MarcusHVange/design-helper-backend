set windows-shell := ["cmd.exe", "/C"] 
set shell := ["bash", "-c"]

start:
   uv run uvicorn src.api.main:app

dev:
    uv run uvicorn src.api.main:app --reload