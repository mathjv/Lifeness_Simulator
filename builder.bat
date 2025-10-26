@echo off
echo ========================================
echo     Lifeness Simulator - Exe Builder
echo ========================================
echo.

REM Activar entorno
cd "C:\Lifeness Project\lifeness_simulator\life"
call matth\Scripts\activate

REM Limpiar compilaciones previas
rmdir /s /q dist
rmdir /s /q build
del Life.spec

REM Crear el ejecutable
pyinstaller --noconsole --onefile --icon=assets\icons\ico2.ico --add-data "assets;assets" --add-data "docs;docs" --name "Life" life.py

echo.
echo ==========================================================================================
echo     Matthias, your executable was Successfully created!
echo     You can find it in: "C:\Lifeness Project\lifeness_simulator\life\dist\Life.exe"
echo ==========================================================================================
pause
