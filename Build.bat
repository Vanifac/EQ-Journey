@ECHO OFF

DEL config.ini
DEL Active Character.csv
DEL src\config.ini
DEL dist\config.ini

pyinstaller --onefile src\EQ_Journey.py