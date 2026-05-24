@echo off
echo === DeepSeek UI - Build ===

pip install pyinstaller pywin32 -i https://pypi.tuna.tsinghua.edu.cn/simple

echo.
echo === Building ===

python tools\generate_icon.py

pyinstaller --onefile --noconsole --name "DeepSeekUI" --icon "assets\app_icon.ico" --hidden-import PyQt6.QtCore --hidden-import PyQt6.QtGui --hidden-import PyQt6.QtWidgets --hidden-import win32com.client main.py

echo.
echo === Done ===
echo Output: dist\DeepSeekUI.exe
echo Place config.json next to the exe.
pause
