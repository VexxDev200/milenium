@echo off
chcp 65001 >nul
cd /d C:\Users\smird\Downloads\milenium
python -m milenium.cli library sync --folder "бд"
pause
