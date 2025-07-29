# Hand Gesture Control Application - Windows

A computer vision application that allows you to control your system's brightness and volume using hand gestures through your webcam on Windows systems.

## Features

- **Real-time Hand Detection**: Uses MediaPipe for accurate hand tracking
- **Brightness Control**: Use your left hand to control screen brightness
- **Volume Control**: Use your right hand to control system volume
- **Gesture Locking**: Make a fist to lock current brightness/volume settings
- **Intuitive Interface**: Clean, modern GUI with real-time feedback
- **Windows Native**: Uses Windows APIs for system control

## How It Works

### Hand Controls
- **Left Hand**: Controls screen brightness
  - Move hand left/right to decrease/increase brightness
  - Make a fist to lock brightness at current level
  
- **Right Hand**: Controls system volume
  - Move hand up/down to increase/decrease volume
  - Make a fist to lock volume at current level

### Gestures
- **Open Hand**: Active control mode
- **Fist**: Lock current setting (prevents accidental changes)

## Requirements

- **Operating System**: Windows 10/11
- **Python**: 3.8 or higher
- **Webcam**: Any USB or built-in camera
- **Hardware**: Minimum 4GB RAM, decent CPU for real-time processing

## Installation

### Option 1: Automatic Setup (Recommended)

1. **Download all files** to a folder on your computer

2. **Run the setup script**:
   - Double-click `setup_windows.bat`
   - Wait for the installation to complete

3. **Run the application**:
   - Double-click `run_windows.bat`

### Option 2: Manual Setup

1. **Install Python** (if not already installed):
   - Download from [python.org](https://www.python.org/downloads/)
   - Make sure to check "Add Python to PATH" during installation

2. **Create virtual environment**:
   ```cmd
   python -m venv venv
   ```

3. **Activate virtual environment**:
   ```cmd
   venv\Scripts\activate.bat
   ```

4. **Install dependencies**:
   ```cmd
   pip install -r requirements_windows.txt
   ```

5. **Run the application**:
   ```cmd
   python hand_gesture_control_windows.py
   ```

## Usage Instructions

1. **Start the application** using one of the methods above

2. **Position yourself** in front of your webcam:
   - Sit about 2-3 feet from the camera
   - Ensure good lighting
   - Keep your hands visible in the camera frame

3. **Control brightness** with your left hand:
   - Hold your left hand open in front of the camera
   - Move it left to decrease brightness
   - Move it right to increase brightness
   - Make a fist to lock the current brightness

4. **Control volume** with your right hand:
   - Hold your right hand open in front of the camera
   - Move it up to increase volume
   - Move it down to decrease volume
   - Make a fist to lock the current volume

5. **View status** in the application window:
   - Current brightness and volume percentages
   - Lock status for each control
   - Real-time camera feed with hand tracking

## Troubleshooting

### Camera Issues
- **Camera not detected**: Try closing other applications using the camera
- **Poor detection**: Improve lighting or clean camera lens
- **Multiple cameras**: The app will try camera 0, then camera 1

### Permission Issues
- **Brightness control fails**: Some laptops require administrator privileges
- **Volume control fails**: Check Windows audio service is running

### Performance Issues
- **Laggy response**: Close other resource-intensive applications
- **High CPU usage**: Lower the frame rate by modifying the code (change `self.root.after(30, ...)` to a higher value)

### Dependencies Issues
- **Import errors**: Make sure virtual environment is activated
- **MediaPipe issues**: Try reinstalling: `pip uninstall mediapipe && pip install mediapipe`

## Customization

You can modify the following in `hand_gesture_control_windows.py`:

- **Sensitivity**: Adjust detection confidence in MediaPipe initialization
- **Control ranges**: Modify the mapping ranges in `control_brightness()` and `control_volume()`
- **Frame rate**: Change the timer value in `update_video_feed()`
- **UI colors**: Modify the color scheme in the style configuration

## Technical Details

### Dependencies
- **OpenCV**: Computer vision and camera handling
- **MediaPipe**: Hand detection and tracking
- **NumPy**: Numerical computations
- **pycaw**: Windows audio control
- **screen-brightness-control**: Display brightness control
- **Pillow**: Image processing for GUI
- **tkinter**: GUI framework

### Architecture
- Main GUI thread handles the interface
- Video processing runs in the main loop with timer callbacks
- Hand detection uses MediaPipe's machine learning models
- System controls use Windows-specific APIs

## Security & Privacy

- **No data collection**: All processing happens locally
- **No internet required**: Works completely offline
- **Camera access**: Only used for hand detection, no recording
- **System access**: Only brightness and volume controls

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Ensure all requirements are met
3. Try running from command line to see error messages
4. Check that your camera and audio devices are working properly

## License

This project is for educational and personal use. Please respect the licenses of the included dependencies.

---

**Note**: This application requires a webcam and works best in good lighting conditions. The first run may take longer as MediaPipe downloads its models.