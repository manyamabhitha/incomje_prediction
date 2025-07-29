import cv2
import numpy as np
import mediapipe as mp
import screen_brightness_control as sbc
from math import hypot
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import threading
import time

class HandControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hand Gesture Control - Windows")
        self.root.geometry("900x600")
        self.root.configure(bg="#2C3E50")

        # User Instructions
        self.user_note = ttk.Label(root, text="CONTROL SYSTEM USING HAND GESTURE",
                                   font=("Arial", 18), style="TLabel", wraplength=850, justify="center")
        self.user_note.pack(pady=10)

        self.video_label = ttk.Label(root)
        self.video_label.pack(padx=20, pady=20)

        # Frame for controls
        self.control_frame = ttk.Frame(root, padding="20", style="TFrame")
        self.control_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.brightness_label = ttk.Label(self.control_frame, text="Brightness: 0%", font=("Arial", 14), style="TLabel")
        self.brightness_label.grid(row=0, column=0, padx=10, pady=10, sticky='w')

        self.volume_label = ttk.Label(self.control_frame, text="Volume: 0%", font=("Arial", 14), style="TLabel")
        self.volume_label.grid(row=1, column=0, padx=10, pady=10, sticky='w')

        self.status_label = ttk.Label(self.control_frame, text="Status: Ready", font=("Arial", 12), style="TLabel")
        self.status_label.grid(row=2, column=0, padx=10, pady=10, sticky='w')

        # Styles
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#34495E")
        self.style.configure("TLabel", background="#34495E", foreground="white")
        self.style.configure("TButton", background="#2980B9", foreground="white", padding="6 12")

        # Video capture
        self.cap = None
        self.initialize_camera()

        # Volume control setup
        try:
            self.devices = AudioUtilities.GetSpeakers()
            self.interface = self.devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self.volume = cast(self.interface, POINTER(IAudioEndpointVolume))
            volRange = self.volume.GetVolumeRange()
            self.minVol, self.maxVol, _ = volRange
            self.volume_available = True
        except Exception as e:
            print(f"Volume control initialization failed: {e}")
            self.volume_available = False

        # MediaPipe hand tracking
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=0.75,
            min_tracking_confidence=0.75,
            max_num_hands=2)

        self.draw = mp.solutions.drawing_utils

        # Control states
        self.brightness_locked = False
        self.volume_locked = False
        self.current_brightness = 50
        self.current_volume = 50

        # Start video processing
        self.running = True
        self.update_video_feed()

        # Instruction note
        self.user_instruction_note = ttk.Label(root, 
            text="Left hand → Brightness | Right hand → Volume\n"
                 "Open hand to adjust, make fist to lock\n"
                 "Move hand left/right for brightness, up/down for volume",
            font=("Arial", 10), style="TLabel", wraplength=850, justify="center")
        self.user_instruction_note.pack(pady=5)

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def initialize_camera(self):
        """Initialize camera with error handling"""
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(1)  # Try second camera
            
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
        except Exception as e:
            print(f"Camera initialization failed: {e}")
            self.cap = None

    def calculate_distance(self, p1, p2):
        """Calculate Euclidean distance between two points"""
        return hypot(p1[0] - p2[0], p1[1] - p2[1])

    def is_fist(self, landmarks):
        """Detect if hand is making a fist gesture"""
        # Get landmark positions
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        index_tip = landmarks[8]
        index_pip = landmarks[6]
        middle_tip = landmarks[12]
        middle_pip = landmarks[10]
        ring_tip = landmarks[16]
        ring_pip = landmarks[14]
        pinky_tip = landmarks[20]
        pinky_pip = landmarks[18]

        # Check if fingertips are below their respective PIP joints (folded)
        fingers_folded = 0
        
        # Thumb (different logic - check if tip is close to palm)
        if thumb_tip.y > thumb_ip.y:
            fingers_folded += 1
            
        # Other fingers
        if index_tip.y > index_pip.y:
            fingers_folded += 1
        if middle_tip.y > middle_pip.y:
            fingers_folded += 1
        if ring_tip.y > ring_pip.y:
            fingers_folded += 1
        if pinky_tip.y > pinky_pip.y:
            fingers_folded += 1

        return fingers_folded >= 4  # At least 4 fingers folded = fist

    def control_brightness(self, hand_landmarks, frame_width):
        """Control brightness based on hand position"""
        if self.brightness_locked:
            return

        # Use wrist position for brightness control
        wrist = hand_landmarks.landmark[0]
        x_pos = int(wrist.x * frame_width)
        
        # Map x position to brightness (0-100)
        brightness = np.interp(x_pos, [50, frame_width - 50], [0, 100])
        brightness = max(0, min(100, brightness))
        
        try:
            sbc.set_brightness(int(brightness))
            self.current_brightness = int(brightness)
            self.brightness_label.config(text=f"Brightness: {int(brightness)}%")
        except Exception as e:
            print(f"Brightness control error: {e}")

    def control_volume(self, hand_landmarks, frame_height):
        """Control volume based on hand position"""
        if self.volume_locked or not self.volume_available:
            return

        # Use wrist position for volume control
        wrist = hand_landmarks.landmark[0]
        y_pos = int(wrist.y * frame_height)
        
        # Map y position to volume (inverted - top = high volume)
        volume_percent = np.interp(y_pos, [50, frame_height - 50], [100, 0])
        volume_percent = max(0, min(100, volume_percent))
        
        try:
            # Convert percentage to volume range
            volume_level = np.interp(volume_percent, [0, 100], [self.minVol, self.maxVol])
            self.volume.SetMasterVolumeLevel(volume_level, None)
            self.current_volume = int(volume_percent)
            self.volume_label.config(text=f"Volume: {int(volume_percent)}%")
        except Exception as e:
            print(f"Volume control error: {e}")

    def update_video_feed(self):
        """Update video feed and process hand gestures"""
        if not self.running:
            return

        if self.cap is None or not self.cap.isOpened():
            # Show error message
            error_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(error_frame, "Camera not available", (150, 240), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            self.display_frame(error_frame)
            self.root.after(100, self.update_video_feed)
            return

        ret, frame = self.cap.read()
        if not ret:
            self.root.after(100, self.update_video_feed)
            return

        # Flip frame horizontally for mirror effect
        frame = cv2.flip(frame, 1)
        frame_height, frame_width, _ = frame.shape

        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)

        # Draw hand landmarks and control system
        if results.multi_hand_landmarks and results.multi_handedness:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                # Draw hand landmarks
                self.draw.draw_landmarks(frame, hand_landmarks, self.mpHands.HAND_CONNECTIONS)
                
                # Get hand label (Left or Right)
                hand_label = handedness.classification[0].label
                
                # Check for fist gesture
                is_fist_gesture = self.is_fist(hand_landmarks.landmark)
                
                # Display hand info
                wrist = hand_landmarks.landmark[0]
                x, y = int(wrist.x * frame_width), int(wrist.y * frame_height)
                
                # Control logic based on hand
                if hand_label == "Left":
                    if is_fist_gesture:
                        self.brightness_locked = True
                        cv2.putText(frame, "Left: LOCKED", (x-50, y-20), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    else:
                        self.brightness_locked = False
                        self.control_brightness(hand_landmarks, frame_width)
                        cv2.putText(frame, "Left: Brightness", (x-50, y-20), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                elif hand_label == "Right":
                    if is_fist_gesture:
                        self.volume_locked = True
                        cv2.putText(frame, "Right: LOCKED", (x-50, y-20), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    else:
                        self.volume_locked = False
                        self.control_volume(hand_landmarks, frame_height)
                        cv2.putText(frame, "Right: Volume", (x-50, y-20), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Update status
        status = []
        if self.brightness_locked:
            status.append("Brightness Locked")
        if self.volume_locked:
            status.append("Volume Locked")
        if not status:
            status.append("Ready")
        
        self.status_label.config(text=f"Status: {', '.join(status)}")

        # Display frame
        self.display_frame(frame)
        
        # Schedule next update
        self.root.after(30, self.update_video_feed)  # ~33 FPS

    def display_frame(self, frame):
        """Convert frame to PhotoImage and display in tkinter"""
        # Resize frame for display
        display_frame = cv2.resize(frame, (640, 480))
        
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image
        pil_image = Image.fromarray(rgb_frame)
        photo = ImageTk.PhotoImage(image=pil_image)
        
        # Update label
        self.video_label.configure(image=photo)
        self.video_label.image = photo  # Keep a reference

    def on_closing(self):
        """Handle application closing"""
        self.running = False
        if self.cap:
            self.cap.release()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = HandControlApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()