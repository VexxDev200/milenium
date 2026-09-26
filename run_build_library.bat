@echo off
chcp 65001 >nul
cd /d C:\Users\smird\Downloads\milenium
python build_library.py --min-size-mb 50 --max-files 200
pause
