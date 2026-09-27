@echo off
title SquadSync Launcher
echo Starting SquadSync Development Servers...
if exist "backend\.venv\Scripts\python.exe" (
    "backend\.venv\Scripts\python.exe" run.py
) else (
    python run.py
)
pause
