import cv2
import numpy as np
import screen_brightness_control as sbc
from math import hypot
import pulsectl
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import subprocess
import sys
import threading
import time

class HandControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hand Gesture Control - Simple")
        self.root.geometry("900x600")
        self.root.configure(bg="#2C3E50")

        # User Instructions
        self.user_note = ttk.Label(root, text="CONTROL SYSTEM USING HAND GESTURE - SIMPLE VERSION",
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

        self.gesture_label = ttk.Label(self.control_frame, text="Gesture: None", font=("Arial", 14), style="TLabel")
        self.gesture_label.grid(row=2, column=0, padx=10, pady=10, sticky='w')

        # Styles
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#34495E")
        self.style.configure("TLabel", background="#34495E", foreground="white")
        self.style.configure("TButton", background="#2980B9", foreground="white", padding="6 12")

        # Video capture
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Could not open camera")
            return

        # Volume control setup (Linux with PulseAudio)
        try:
            self.pulse = pulsectl.Pulse('hand-gesture-control')
            self.sink = self.pulse.sink_list()[0]  # Get default sink
        except Exception as e:
            print(f"Warning: Could not initialize audio control: {e}")
            self.pulse = None

        # Motion detection setup
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(detectShadows=True)
        
        # Control states
        self.brightness_locked = False
        self.volume_locked = False
        self.current_brightness = 50
        self.current_volume = 50
        
        # Get initial brightness
        try:
            self.current_brightness = sbc.get_brightness()[0] if sbc.get_brightness() else 50
        except:
            self.current_brightness = 50

        # Get initial volume
        if self.pulse:
            try:
                self.current_volume = int(self.sink.volume.value_flat * 100)
            except:
                self.current_volume = 50

        self.update_video_feed()

        # Instruction note
        self.user_instruction_note = ttk.Label(root, text="Move your hand left/right to control brightness\n"
                                                          "Move your hand up/down to control volume\n"
                                                          "Make a fist to lock current setting",
                                               font=("Arial", 12), style="TLabel", wraplength=850, justify="center")
        self.user_instruction_note.pack(pady=10)

    def detect_hand_gesture(self, frame):
        """Simple hand gesture detection using motion and contour analysis"""
        # Apply background subtraction
        fg_mask = self.bg_subtractor.apply(frame)
        
        # Remove noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None, frame
            
        # Find the largest contour (assumed to be the hand)
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Filter out small contours
        if cv2.contourArea(largest_contour) < 1000:
            return None, frame
            
        # Get bounding rectangle
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        # Draw bounding rectangle
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # Calculate center point
        center_x = x + w // 2
        center_y = y + h // 2
        
        # Draw center point
        cv2.circle(frame, (center_x, center_y), 5, (255, 0, 0), -1)
        
        # Simple gesture recognition based on contour properties
        hull = cv2.convexHull(largest_contour)
        hull_area = cv2.contourArea(hull)
        contour_area = cv2.contourArea(largest_contour)
        
        # Calculate solidity (how "solid" the shape is)
        solidity = contour_area / hull_area if hull_area > 0 else 0
        
        # Determine gesture type
        gesture = "open_hand" if solidity > 0.8 else "fist"
        
        return {
            'center': (center_x, center_y),
            'gesture': gesture,
            'area': contour_area,
            'solidity': solidity
        }, frame

    def control_brightness_volume(self, hand_data, frame_width, frame_height):
        """Control brightness and volume based on hand position"""
        if not hand_data:
            return
            
        center_x, center_y = hand_data['center']
        gesture = hand_data['gesture']
        
        # Normalize coordinates (0-1)
        norm_x = center_x / frame_width
        norm_y = 1 - (center_y / frame_height)  # Invert Y axis
        
        # Control brightness based on X position (left-right)
        if not self.brightness_locked:
            brightness_value = int(norm_x * 100)
            brightness_value = max(10, min(100, brightness_value))  # Clamp between 10-100
            
            try:
                sbc.set_brightness(brightness_value)
                self.current_brightness = brightness_value
            except Exception as e:
                print(f"Error setting brightness: {e}")
        
        # Control volume based on Y position (up-down)
        if not self.volume_locked and self.pulse:
            volume_value = norm_y  # 0-1 range for PulseAudio
            volume_value = max(0.0, min(1.0, volume_value))
            
            try:
                self.pulse.volume_set_all_chans(self.sink, volume_value)
                self.current_volume = int(volume_value * 100)
            except Exception as e:
                print(f"Error setting volume: {e}")
        
        # Lock/unlock based on gesture
        if gesture == "fist":
            self.brightness_locked = True
            self.volume_locked = True
        else:
            self.brightness_locked = False
            self.volume_locked = False

    def update_video_feed(self):
        """Update the video feed and process gestures"""
        ret, frame = self.cap.read()
        if not ret:
            self.root.after(30, self.update_video_feed)
            return
            
        # Flip frame horizontally for mirror effect
        frame = cv2.flip(frame, 1)
        frame_height, frame_width = frame.shape[:2]
        
        # Detect hand gestures
        hand_data, processed_frame = self.detect_hand_gesture(frame)
        
        # Control brightness and volume
        self.control_brightness_volume(hand_data, frame_width, frame_height)
        
        # Update UI labels
        self.brightness_label.config(text=f"Brightness: {self.current_brightness}%")
        self.volume_label.config(text=f"Volume: {self.current_volume}%")
        
        gesture_text = hand_data['gesture'] if hand_data else "None"
        lock_status = " (LOCKED)" if (self.brightness_locked or self.volume_locked) else ""
        self.gesture_label.config(text=f"Gesture: {gesture_text}{lock_status}")
        
        # Convert frame to display in tkinter
        processed_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
        processed_frame = cv2.resize(processed_frame, (640, 480))
        
        # Convert to PIL Image and then to PhotoImage
        pil_image = Image.fromarray(processed_frame)
        photo = ImageTk.PhotoImage(image=pil_image)
        
        # Update video label
        self.video_label.configure(image=photo)
        self.video_label.image = photo  # Keep a reference
        
        # Schedule next update
        self.root.after(30, self.update_video_feed)

    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'cap'):
            self.cap.release()
        if hasattr(self, 'pulse') and self.pulse:
            self.pulse.close()

def main():
    # Create main window
    root = tk.Tk()
    
    # Create and run the application
    app = HandControlApp(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Application stopped by user")
    finally:
        # Cleanup
        if hasattr(app, 'cap'):
            app.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()