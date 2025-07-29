@echo off
echo Starting Hand Gesture Control...

REM Activate virtual environment and run the application
call venv\Scripts\activate.bat
python hand_gesture_control_windows.py

pause