# Python_Kred_calc-PyQt6
Python PyQt6 project PyCharm - Credit calculator (real estate, auto) (annuity, the classics, installment), with SQLite.

IDE - PyCharm Community Edition

- Перевірка якості кода ruff check
-> pip install ruff
-> ruff check main.py

У командному рядку терміналу IDE
1) Додаємо бібліотеки
-> pip install PyQt6
-> pip install python-dateutil
-> pip install xmltodict

2) Qt Designer
Окремо встановлюємо:
-> https://build-system.fman.io/qt-designer-download
або:
-> pip install pyqt6-tools
   Запускаємо -> pyqt6-tools designer

3) Перетворення *.ui файлу у файл типу *.py
-> pyuic6 MainWindow.ui -o ui_MainWindow.py

---------------------------------------------------
Оновлення пакетів у IDE PyCharm Community Edition:
-> Settings -> Project:Kred_calc -> Python Interpreter -> Upgrade

---------------------------------------------------
Створення EXE файла
1) Ставимо pyinstaller
-> pip install pyinstaller

2) Запускаємо файл .\Kred_calc_create_EXE_file.bat для автоматичної збірки exe файла
Сформований файл буде розташований у каталозі \dist\

PyCharm Community Edition -> Off message Typo: In word 'XXXXX'
IDE in Settings -> Editor -> Inspections -> Proofreading -> Typo.
Зняти галки з "Process code" та "Process literals" та "Process comments"