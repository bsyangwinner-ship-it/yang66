@echo off
setlocal
for %%I in ("%~dp0..") do set "ROOT=%%~fI"
cd /d "%ROOT%\backend"
set "DATABASE_URL=sqlite+pysqlite:///./nutrition_agent_dev.db"
".venv\Scripts\python.exe" -c "from app.db.base import Base; from app.db.session import engine; Base.metadata.create_all(bind=engine)"
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
