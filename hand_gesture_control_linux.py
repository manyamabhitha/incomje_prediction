import cv2
import numpy as np
import mediapipe as mp
import screen_brightness_control as sbc
from math import hypot
import pulsectl
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import subprocess
import sys

class HandControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hand Gesture Control - Linux")
        self.root.geometry("900x600")
        self.root.configure(bg="#2C3E50")

        # User Instructions
        self.user_note = ttk.Label(root, text="CONTROL SYSTEM USING HAND GESTURE.",
                                   font=("Arial", 18), style="TLabel", wraplength=850, justify="center")
        self.user_note.pack(pady=10)

        self.video_label = ttk.Label(root)
        self.video_label.pack(padx=20, pady=20)

        # Frame for controls
        self.control_frame = ttk.Frame(root, padding="20", style="TFrame")
        self.control_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.brightness_label = ttk.Label(self.control_frame, text="Brightness: 0", font=("Arial", 14), style="TLabel")
        self.brightness_label.grid(row=0, column=0, padx=10, pady=10, sticky='w')

        self.volume_label = ttk.Label(self.control_frame, text="Volume: 0", font=("Arial", 14), style="TLabel")
        self.volume_label.grid(row=1, column=0, padx=10, pady=10, sticky='w')

        # Styles
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#34495E")
        self.style.configure("TLabel", background="#34495E", foreground="white")
        self.style.configure("TButton", background="#2980B9", foreground="white", padding="6 12")
        self.style.configure("TProgressbar", thickness=15, length=200, background="#3498DB")

        # Video capture
        self.cap = cv2.VideoCapture(0)
        
        # Check if camera is available
        if not self.cap.isOpened():
            print("Error: Could not open camera")
            sys.exit(1)

        # Volume control setup for Linux using PulseAudio
        try:
            self.pulse = pulsectl.Pulse('hand-gesture-control')
            self.sink = self.pulse.sink_list()[0]  # Get default sink
        except Exception as e:
            print(f"Error initializing PulseAudio: {e}")
            print("Falling back to amixer for volume control")
            self.pulse = None

        # Mediapipe hand tracking
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=0.75,
            min_tracking_confidence=0.75,
            max_num_hands=2)

        self.draw = mp.solutions.drawing_utils

        # Lock states (to "hold" brightness/volume)
        self.brightness_locked = False
        self.volume_locked = False

        # Current values
        self.current_brightness = 50
        self.current_volume = 50

        self.update_video_feed()

        # Instruction note
        self.user_instruction_note = ttk.Label(root, text="Left hand → Brightness | Right hand → Volume\n"
                                                          "Spread fingers to adjust, pinch (thumb+index) to lock value.",
                                                font=("Arial", 12), style="TLabel", wraplength=850, justify="center")
        self.user_instruction_note.pack(pady=10)

    def set_volume_linux(self, volume_percent):
        """Set system volume on Linux using PulseAudio or amixer fallback"""
        try:
            if self.pulse:
                # Using pulsectl
                volume = volume_percent / 100.0
                self.pulse.volume_set_all_chans(self.sink, volume)
            else:
                # Fallback to amixer
                subprocess.run(['amixer', 'set', 'Master', f'{int(volume_percent)}%'], 
                             capture_output=True, check=True)
        except Exception as e:
            print(f"Error setting volume: {e}")

    def update_video_feed(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            frameRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            processed = self.hands.process(frameRGB)

            left_landmark_list, right_landmark_list = self.get_left_right_landmarks(frame, processed)

            # Left hand controls brightness
            if left_landmark_list:
                if self.is_pinch(left_landmark_list):
                    self.brightness_locked = not self.brightness_locked  # Toggle lock when pinched
                if not self.brightness_locked:
                    left_distance = self.get_distance(frame, left_landmark_list)
                    b_level = np.interp(left_distance, [50, 220], [0, 100])
                    try:
                        sbc.set_brightness(int(b_level))
                        self.current_brightness = int(b_level)
                    except Exception as e:
                        print(f"Error setting brightness: {e}")
                    self.brightness_label.config(text=f"Brightness: {self.current_brightness}")

            # Right hand controls volume
            if right_landmark_list:
                if self.is_pinch(right_landmark_list):
                    self.volume_locked = not self.volume_locked  # Toggle lock when pinched
                if not self.volume_locked:
                    right_distance = self.get_distance(frame, right_landmark_list)
                    vol_percentage = np.interp(right_distance, [50, 220], [0, 100])
                    self.set_volume_linux(vol_percentage)
                    self.current_volume = int(vol_percentage)
                    self.volume_label.config(text=f"Volume: {self.current_volume}")

            # Show video feed
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = Image.fromarray(frame)
            frame = frame.resize((640, 480), Image.Resampling.LANCZOS)
            frame = ImageTk.PhotoImage(frame)
            self.video_label.img = frame
            self.video_label.configure(image=frame)

        self.root.after(50, self.update_video_feed)

    def is_pinch(self, landmark_list):
        """Check if thumb and index finger are pinched together to toggle lock."""
        if len(landmark_list) < 2:
            return False
        x1, y1 = landmark_list[0][1], landmark_list[0][2]
        x2, y2 = landmark_list[1][1], landmark_list[1][2]
        distance = hypot(x2 - x1, y2 - y1)
        return distance < 30  # Pinch threshold in pixels

    def get_left_right_landmarks(self, frame, processed):
        left_landmark_list = []
        right_landmark_list = []

        if processed.multi_hand_landmarks:
            for idx, handlm in enumerate(processed.multi_hand_landmarks):
                landmarks = []
                for id_, found_landmark in enumerate(handlm.landmark):
                    height, width, _ = frame.shape
                    x, y = int(found_landmark.x * width), int(found_landmark.y * height)
                    if id_ == 4 or id_ == 8:  # Thumb tip and index tip
                        landmarks.append([id_, x, y])
                if idx == 0:
                    left_landmark_list = landmarks
                elif idx == 1:
                    right_landmark_list = landmarks
                self.draw.draw_landmarks(frame, handlm, self.mpHands.HAND_CONNECTIONS)

        return left_landmark_list, right_landmark_list

    def get_distance(self, frame, landmark_list):
        if len(landmark_list) < 2:
            return 0
        (x1, y1), (x2, y2) = (landmark_list[0][1], landmark_list[0][2]), (landmark_list[1][1], landmark_list[1][2])
        cv2.circle(frame, (x1, y1), 7, (0, 255, 0), cv2.FILLED)
        cv2.circle(frame, (x2, y2), 7, (0, 255, 0), cv2.FILLED)
        cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
        return hypot(x2 - x1, y2 - y1)

    def close(self):
        if self.pulse:
            self.pulse.close()
        self.cap.release()
        cv2.destroyAllWindows()

def main():
    root = tk.Tk()
    app = HandControlApp(root)
    root.protocol("WM_DELETE_WINDOW", app.close)
    root.mainloop()

if __name__ == '__main__':
    main()