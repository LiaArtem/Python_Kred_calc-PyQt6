@ECHO OFF
set PYTHONPATH="c:\Users\artem\AppData\Local\Programs\Python\Python311"

rd /s /q build
rd /s /q dist
del /q main.spec

pyinstaller --noconfirm --noconsole --onefile --icon=icon.ico main.py

pause
