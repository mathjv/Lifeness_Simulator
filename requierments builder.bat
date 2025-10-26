@echo off
cd "C:\Lifeness Project\lifeness_simulator\life"
call matth\Scripts\activate

REM Asegurese de instalar a continuacion solo en caso de perdida injustificada de las librerias o en caso de reinstalacion.

pip install --upgrade pip
pip install PySide6 PyOpenGL python-docx pillow numpy matplotlib platformdirs
pip install pyinstaller
