# Python_Kred_calc-PyQt6
Python PyQt6 project PyCharm - Credit calculator (real estate, auto) (annuity, the classics, installment), with SQLite.

IDE - PyCharm Community Edition

У командному рядку терміналу IDE
1) Додаємо бібліотеки
-> pip install PyQt6
-> pip install pyqt6-tools
-> pip install python-dateutil
-> pip install xmltodict

2) Qt Designer
Запускаємо
-> pyqt6-tools designer або окремо встановлюємо:
   https://build-system.fman.io/qt-designer-download

3) Перетворення *.ui файлу у файл типу *.py
-> pyuic6 MainWindow.ui -o ui_MainWindow.py

---------------------------------------------------
Оновлення пакетів у IDE PyCharm Community Edition:
-> Settings -> Project:Kred_calc -> Python Interpreter -> Upgrade

---------------------------------------------------
Створення EXE файла
1) Ставимо pyinstaller
-> pip install pyinstaller

2) Build один EXE файл без консолі зі своєю іконкою (збірка буде у папці \dist\)
-> pyinstaller -F -w -i icon.ico main.py

Перед кожною збіркою відаляємо \dist\ та \build\ та main.spec