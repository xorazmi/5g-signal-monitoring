@echo off
echo ============================================
echo   5G Signal Analyzer - EXE yaratish
echo ============================================
echo.

echo [1/3] PyInstaller o'rnatilmoqda...
pip install pyinstaller --quiet

echo [2/3] EXE yaratilmoqda (biroz vaqt ketadi)...
pyinstaller --onefile --windowed --name "SignalAnalyzer" signal_analyzer.py

echo [3/3] Tayyor!
echo.
echo EXE fayl: dist\SignalAnalyzer.exe
echo.
pause
