import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import cv2
import pyaudio
import wave
import numpy as np
import threading
import os
import torch
from PIL import ImageGrab

class ScreenRecorderApp(tk.Tk):
    def __init__(self,
                 temp_video_path="temp_output.mp4",
                 temp_audio_path="temp_audio.wav",
                 output_video_path="output.mp4"):
        super().__init__()
        self.temp_video_path = temp_video_path
        self.temp_audio_path = temp_audio_path

        # Initialize necessary attributes for audio recording
        self.channels = 2
        self.sample_rate = 44100
        self.chunk = 1024
        self.audio_format = pyaudio.paInt16
        self.audio = pyaudio.PyAudio()
        self.title("Screen Recorder")
        self.geometry("600x400")
        self.configure(bg="white")
        self.create_widgets()

        # Create a variable to store the recording status
        self.is_recording = False

        
    
    def create_widgets(self):
        # Create and place the Start Recording button in the center of the window
        self.start_button = ttk.Button(self, text="Start", command=self.start_recording)
        self.start_button.pack(pady=10)

        # put the button in the center of the window, shift it up by 50 pixels
        self.start_button.place(relx=0.5, rely=0.5, anchor="center", y=-20)

        # Create and place the Stop Recording button
        self.stop_button = ttk.Button(self, text="Stop", command=self.stop_recording, state="disabled")
        self.stop_button.pack(pady=10)
        self.stop_button.place(relx=0.5, rely=0.5, anchor="center", y=20)
        
        # Other widgets for options such as resolution, frame rate, and audio input can be created and placed here.
        self.resolution_label = ttk.Label(self, text="Resolution:")
        
        # place the label in the bottom left side of the window (leave enough space for the dropdown menu)
        self.resolution_label.place(relx=0.5, rely=0.5, anchor="center", x=-200, y=115)

        # create a string variable to store the resolution
        self.resolution = tk.StringVar(value="1080p")

        # create a dropdown menu for resolution
        self.resolution_menu = ttk.OptionMenu(self, self.resolution, "480p", "720p", "1080p", "4k")
        
        # place the dropdown menu on the left side of the window, under the label
        self.resolution_menu.place(relx=0.5, rely=0.5, anchor="center", x=-200, y=145)

        # create a label for the frame rate
        self.frame_rate_label = ttk.Label(self, text="Frame Rate:")
        
        # place the label on the right side of the window
        self.frame_rate_label.place(relx=0.5, rely=0.5, anchor="center", x=-100, y=115)
        
        # create a string variable to store the frame rate
        self.frame_rate = tk.StringVar(value="30")

        # create a dropdown menu for frame rate
        self.frame_rate_menu = ttk.OptionMenu(self, self.frame_rate, "30", "60", "90", "120")
        self.frame_rate_menu.pack(pady=10)

        # place the dropdown menu on the right side of the window, under the label
        self.frame_rate_menu.place(relx=0.5, rely=0.5, anchor="center", x=-100, y=145)

        # create a label for the audio input
        self.audio_input_label = ttk.Label(self, text="Audio Input:")
        
        # place the label on the right side of the window
        self.audio_input_label.place(relx=0.5, rely=0.5, anchor="center", x=200, y=115)

        # create a string variable to store the audio input
        self.audio_input = tk.StringVar(value="Both")

        # create a dropdown menu for audio input
        self.audio_input_menu = ttk.OptionMenu(self, self.audio_input, "Both", "Microphone", "System Audio")
        
        # place the dropdown menu on the right side of the window, under the label
        self.audio_input_menu.place(relx=0.5, rely=0.5, anchor="center", x=200, y=145)

        # create a label for the audio format
        self.audio_format_label = ttk.Label(self, text="Audio Format:")

        # place the label on the right side of the window
        self.audio_format_label.place(relx=0.5, rely=0.5, anchor="center", x=100, y=115)

        # create a string variable to store the audio format
        self.audio_format = tk.StringVar(value="wav")

        # create a dropdown menu for audio format
        self.audio_format_menu = ttk.OptionMenu(self, self.audio_format, "wav", "mp3", "aac")

        # place the dropdown menu on the right side of the window, under the label
        self.audio_format_menu.place(relx=0.5, rely=0.5, anchor="center", x=100, y=145)


        # Create and place the Help button
        self.help_button = ttk.Button(self, text="Help", command=self.show_help)
        self.help_button.pack(pady=10)
        self.help_button.place(relx=0.5, rely=0.5, anchor="center", y=60)

       
    def start_recording(self):
        # Get the resolution, frame rate, and audio input from the dropdown menus
        self.resolution = self.resolution.get()
        self.frame_rate = int(self.frame_rate.get())
        self.audio_input = self.audio_input.get()
        self.audio_format = self.audio_format.get()
        
        # Map the audio_format string to the corresponding PyAudio format constant
        audio_format_mapping = {
            "wav": pyaudio.paInt16,
            "mp3": pyaudio.paInt16,  # PyAudio does not support MP3 natively
            "aac": pyaudio.paInt16   # PyAudio does not support AAC natively
        }
        self.audio_format = audio_format_mapping[self.audio_format]


        # Activate the Stop button and deactivate the Start button
        self.start_button["state"] = "disabled"
        self.stop_button["state"] = "normal"
        
        # Start the video and audio recording
        self.record_video_thread = threading.Thread(target=self.record_video)
        self.record_audio_thread = threading.Thread(target=self.record_audio)
        self.record_video_thread.start()
        self.record_audio_thread.start()

        

    def stop_recording(self):
        # Stop the video and audio recording
        self.is_recording = False
        self.record_video_thread.join()
        self.record_audio_thread.join()
        
        # Prompt user to save or discard the recording
        self.prompt_save_or_discard()

    def prompt_save_or_discard(self):
        # Create and display a save/discard dialog
        self.save_discard_dialog = tk.Toplevel(self)
        self.save_discard_dialog.title("Save or Discard")
        label = ttk.Label(self.save_discard_dialog, text="Save or discard the recording?")
        label.pack(pady=10)
        save_button = ttk.Button(self.save_discard_dialog, text="Save", command=self.save_recording)
        save_button.pack(side="left", padx=10)
        discard_button = ttk.Button(self.save_discard_dialog, text="Discard", command=self.discard_recording)
        discard_button.pack(side="right", padx=10)

    def save_recording(self):
        # Merge audio and video streams
        self.merge_streams()

        # Open a file select dialog box
        file_path = filedialog.asksaveasfilename(defaultextension=".mp4")
        
        # Save the file
        os.rename(self.temp_video_path, file_path)

        # Close the save/discard dialog
        self.save_discard_dialog.destroy()

    def discard_recording(self):
        # Delete the temporary recording files
        os.remove(self.temp_video_path)
        os.remove(self.temp_audio_path)

        # Close the save/discard dialog
        self.save_discard_dialog.destroy()

    def record_video(self):
        # Set up the video recording using OpenCV
        screen_resolution = self.get_screen_resolution()
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(self.temp_video_path, fourcc, self.frame_rate, screen_resolution)

        # Record the video
        self.is_recording = True
        while self.is_recording:
            img = self.capture_screen()
            out.write(img)
            cv2.waitKey(1)
        out.release()
        cv2.destroyAllWindows()

    def show_help(self):
        help_window = tk.Toplevel(self)
        help_window.title("Help")
        help_text = tk.Text(help_window, wrap="word")
        help_text.insert("insert", "Help and documentation content here.")
        help_text.pack(expand=True, fill="both")


    def record_audio(self):
        # Set up the audio recording using PyAudio
        audio = pyaudio.PyAudio()
        stream = audio.open(format=self.audio_format,
                            channels=self.channels,
                            rate=self.sample_rate,
                            input=True,
                            frames_per_buffer=self.chunk)

        # Record the audio
        frames = []
        self.is_recording = True
        while self.is_recording:
            data = stream.read(self.chunk)
            frames.append(data)
        stream.stop_stream()
        stream.close()
        audio.terminate()

        # Save the audio to a temporary file
        wave_file = wave.open(self.temp_audio_path, "wb")
        wave_file.setnchannels(self.channels)
        wave_file.setsampwidth(audio.get_sample_size(self.audio_format))
        wave_file.setframerate(self.sample_rate)
        wave_file.writeframes(b"".join(frames))
        wave_file.close()

    def merge_streams(self):
        # Merge the video and audio streams using FFMPEG
        command = f"ffmpeg -i {self.temp_video_path} -i {self.temp_audio_path} -c copy {self.temp_video_path}"
        os.system(command)

    # Add methods for capturing the screen, getting screen resolution, 
    # applying computer vision models, and indexing the content.

    def capture_screen(self):
        screen = np.array(ImageGrab.grab())
        return cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
    
    def get_screen_resolution(self):
        # Add the desired screen resolutions here
        resolutions = {
            "480p": (854, 480),
            "720p": (1280, 720),
            "1080p": (1920, 1080),
            "4k": (3840, 2160),
        }

        # Get the resolution based on the user's choice
        return resolutions[self.resolution]

    



if __name__ == "__main__":
    app = ScreenRecorderApp()
    app.mainloop()