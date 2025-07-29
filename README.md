# Hand Gesture Control Application

A computer vision application that allows you to control your system's brightness and volume using hand gestures through your webcam.

## Features

- **Brightness Control**: Move your hand left/right to adjust screen brightness
- **Volume Control**: Move your hand up/down to adjust system volume  
- **Gesture Locking**: Make a fist to lock current brightness/volume settings
- **Real-time Video Feed**: See your hand detection in real-time
- **Linux Compatible**: Uses PulseAudio for volume control on Linux systems

## Requirements

- Python 3.13+
- Webcam
- Linux system with PulseAudio
- Display that supports brightness control

## Installation

1. **Clone or download the project files**

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install opencv-python numpy pillow pulsectl screen-brightness-control
   ```

## Usage

### Running the Application

**Simple Version (Recommended for Python 3.13):**
```bash
source venv/bin/activate
python hand_gesture_control_simple.py
```

**Original Version (Requires MediaPipe - may not work on Python 3.13):**
```bash
source venv/bin/activate
python hand_gesture_control_linux.py
```

### How to Use

1. **Position yourself**: Sit in front of your webcam with good lighting
2. **Wait for calibration**: The background subtractor needs a few seconds to learn the background
3. **Control brightness**: Move your hand left (decrease) or right (increase) to adjust brightness
4. **Control volume**: Move your hand up (increase) or down (decrease) to adjust volume
5. **Lock settings**: Make a fist to lock the current brightness and volume levels
6. **Unlock settings**: Open your hand to resume gesture control

### Gesture Controls

- **Open Hand**: Active control mode - brightness and volume adjust based on hand position
- **Fist**: Lock mode - current brightness and volume settings are locked
- **Hand Position**:
  - Left/Right: Controls brightness (0-100%)
  - Up/Down: Controls volume (0-100%)

## Troubleshooting

### Camera Issues
- Make sure your webcam is connected and not being used by another application
- Try changing the camera index in the code: `cv2.VideoCapture(1)` instead of `cv2.VideoCapture(0)`

### Brightness Control Issues
- Some displays may not support software brightness control
- Try running with sudo if brightness control fails: `sudo python hand_gesture_control_simple.py`

### Volume Control Issues
- Make sure PulseAudio is running: `pulseaudio --check`
- Check if audio devices are detected: `pactl list sinks`

### Hand Detection Issues
- Ensure good lighting conditions
- Move slowly to allow the background subtractor to work properly
- Keep your hand within the camera frame
- Wait a few seconds after starting for background calibration

## Technical Details

### Simple Version Features
- Uses OpenCV's background subtraction for motion detection
- Contour analysis for hand detection
- Solidity calculation for gesture recognition (fist vs open hand)
- PulseAudio integration for Linux volume control
- Screen brightness control via `screen-brightness-control` library

### Dependencies Explained
- **opencv-python**: Computer vision and image processing
- **numpy**: Numerical computations
- **pillow**: Image processing for GUI
- **pulsectl**: PulseAudio control for Linux
- **screen-brightness-control**: Cross-platform brightness control

## File Structure

- `hand_gesture_control_simple.py` - Main application (Python 3.13 compatible)
- `hand_gesture_control_linux.py` - Linux version with MediaPipe (requires older Python)
- `hand_gesture_control.py` - Original Windows version
- `requirements.txt` - Python dependencies
- `README.md` - This documentation

## Known Limitations

- **Python 3.13 Compatibility**: MediaPipe doesn't support Python 3.13 yet, so the simple version uses basic computer vision
- **Lighting Sensitivity**: Works best in consistent lighting conditions
- **Background Movement**: Other moving objects in the background may interfere with detection
- **Single Hand**: Currently detects only one hand at a time

## Future Improvements

- Add support for multiple gesture types
- Implement more sophisticated hand tracking
- Add configuration options for sensitivity
- Support for multiple hands
- Add gesture customization

## License

This project is open source and available under the MIT License.