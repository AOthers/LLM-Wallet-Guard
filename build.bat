@echo off
echo === DeepSeek UI - Build ===

pip install pyinstaller pywin32 -i https://pypi.tuna.tsinghua.edu.cn/simple

echo.
echo === Building ===

python tools\generate_icon.py

pyinstaller --onefile --noconsole --name "LLMWalletGuard" --icon "assets\app_icon.ico" --hidden-import PyQt6.QtCore --hidden-import PyQt6.QtGui --hidden-import PyQt6.QtWidgets --hidden-import PyQt6.QtNetwork --hidden-import win32com.client main.py

echo.
echo === Done ===
echo Output: dist\LLMWalletGuard.exe
echo Place config.json next to the exe.
pause
