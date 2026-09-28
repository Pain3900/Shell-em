@echo off
cd /d "%~dp0"
set PYTHONPATH=src
python -m shell_emulator %*
