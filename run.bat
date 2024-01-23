@echo off
cd ./backend
if not exist ".venv" (
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
)
start cmd /k "python -m flask run"

cd ../frontend
call npm install
call npm run electron:serve