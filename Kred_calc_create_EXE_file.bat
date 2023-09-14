@ECHO OFF

rd /s /q build
rd /s /q dist
del /q main.spec

cd %cd%
"%cd%\venv\Scripts\pyinstaller.exe" --noconfirm --noconsole --onefile --icon=icon.ico main.py

pause
