@ECHO OFF

DEL dist\*
DEL dist\Characters\template\template.json
xcopy /s /i Characters\template dist\Characters\template

pyinstaller --onefile src\EQ_Journey.py