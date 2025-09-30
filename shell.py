#       
#   1. Test Color on different monitors to check if it`s not too bright
#
#


import tkinter as tk
from tkinter import ttk, filedialog
import os
import random
import threading
from PIL import Image, ImageTk
import io
import cv2
import librosa
import matplotlib.pyplot as plt
import numpy as np

import body


photo_references = {}

#region Functions

# --- Function ---
def select_file():
    """Opens file choose dialoge"""
    filepath = filedialog.askopenfilename(
        title="Select a file",
        filetypes=(
            ("Media Files", "*.png *.jpg *.mp4 *.mp3 *.wav"),
            ("All files", "*.*")
        )
    )

    if not filepath:
        return

    # Update file name label
    filename = os.path.basename(filepath)
    file_name_label.config(text=filename)
    file_extension = os.path.splitext(filename)[1].lower()

    # Show a loading message
    preview_label.config(image=None, text="Generating preview...")

    if hasattr(preview_label, 'gif_job'):
        preview_label.after_cancel(preview_label.gif_job)

    thread = threading.Thread(target=generate_preview_thread, args=(filepath, file_extension))
    thread.daemon = True
    thread.start()

#region Preview func

def generate_preview_thread(filepath, extension):
    """
    Checks the file extension and calls the appropriate preview generator.
    This function should run in a separate thread.
    """
    if extension in ['.png', '.jpg', '.jpeg']:
        photo = create_image_preview(filepath)
        root.after(0, update_preview_label, photo)
    
    elif extension in ['.mp4', '.avi', '.mov']:
        # For video, we generate a GIF. This returns the GIF's filepath.
        gif_path = create_video_preview(filepath)
        # Schedule the GIF player to run on the main thread
        if gif_path:
            root.after(0, play_gif, gif_path)
            
    elif extension in ['.mp3', '.wav']:
        photo = create_audio_preview(filepath)
        root.after(0, update_preview_label, photo)

    else:
        # If file is not supported, show a message
        root.after(0, update_preview_label, None, "Unsupported format")
        start_btn.config(state="disabled")

def update_preview_label(photo, text=None):
    """Safely updates the preview label from the main thread."""
    if photo:
        preview_label.config(image=photo, text="")
        photo_references['preview'] = photo
        start_btn.config(state="normal")
    else:
        preview_label.config(image=None, text=text or "Preview")
        photo_references.pop('preview', None)

#region Photo

def create_image_preview(filepath):
    """Opens an image, resizes it, and returns a PhotoImage object."""
    try:
        img = Image.open(filepath)
        img.thumbnail((300, 300))
        return ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"Image preview error: {e}")
        return None
    
#region Video

def create_video_preview(filepath):
    """Extracts 10 random frames from a video and saves them as a temporary GIF."""
    try:
        cap = cv2.VideoCapture(filepath)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        frames = []
        # Select 10 random frame indices
        random_indices = sorted(random.sample(range(frame_count), min(10, frame_count)))
        
        for i in random_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                img.thumbnail((300, 300))
                frames.append(img)
        
        cap.release()
        
        if frames:
            # Save frames as an animated GIF in a temporary location
            gif_path = "temp_preview.gif"
            frames[0].save(gif_path, save_all=True, append_images=frames[1:], loop=0, duration=1000)
            return gif_path
    except Exception as e:
        print(f"Video preview error: {e}")
    return None

def play_gif(filepath):
    """Plays an animated GIF in a Tkinter Label."""
    try:
        gif_image = Image.open(filepath)
        frames = []
        for i in range(gif_image.n_frames):
            gif_image.seek(i)
            frame_copy = gif_image.copy()
            frame_copy.thumbnail((300, 300))
            frame_photo = ImageTk.PhotoImage(frame_copy)
            frames.append(frame_photo)
        
        def update_frame(idx):
            frame = frames[idx]
            preview_label.config(image=frame)
            photo_references['gif_frames'] = frames
            photo_references['preview'] = frame
            
            next_idx = (idx + 1) % len(frames)

            # Schedule the next frame update
            preview_label.gif_job = preview_label.after(100, update_frame, next_idx)

        update_frame(0)
        start_btn.config(state="normal")
    except Exception as e:
        print(f"GIF play error: {e}")
        update_preview_label(None, "Could not play GIF")

#region Audio

def create_audio_preview(filepath):
    """Creates a spectrogram from an audio file and returns a PhotoImage."""
    try:
        # Load audio file
        y, sr = librosa.load(filepath, duration=30) 
        # Create a spectrogram
        D = librosa.stft(y)
        S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)
        # Plot using matplotlib
        fig, ax = plt.subplots(figsize=(3, 2), dpi=100)
        librosa.display.specshow(S_db, sr=sr, x_axis='time', y_axis='log', ax=ax)
        # Remove all padding, labels, and axes for a clean image
        ax.set_axis_off()
        fig.tight_layout(pad=0)
        # Save the plot to an in-memory buffer
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0, transparent=True)
        plt.close(fig)
        buf.seek(0)
        # Create a PhotoImage from the buffer
        img = Image.open(buf)
        return ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"Audio preview error: {e}")
        return None

def set_mode(mode):
    """Change the look of mode buttons"""
    if mode == 'hide':
        hide_btn.config(style="Active.TButton")
        extract_btn.config(style="TButton")
        print("Mode set to: Hide")
    elif mode == 'extract':
        extract_btn.config(style="Active.TButton")
        hide_btn.config(style="TButton")
        print("Mode set to: Extract")

#region Main func

def process_enter(filepath, extension):
    """
    Checks the file extension and calls the appropriate transform function.
    This function should run in a separate thread.
    """
    if extension in ['.png', '.jpg', '.jpeg']:
        photo = create_image_preview(filepath)
        root.after(0, update_preview_label, photo)
    
    elif extension in ['.mp4', '.avi', '.mov']:
        # For video, we generate a GIF. This returns the GIF's filepath.
        gif_path = create_video_preview(filepath)
        # Schedule the GIF player to run on the main thread
        if gif_path:
            root.after(0, play_gif, gif_path)
            
    elif extension in ['.mp3', '.wav']:
        photo = create_audio_preview(filepath)
        root.after(0, update_preview_label, photo)

    else:
        # If file is not supported, show a message
        root.after(0, update_preview_label, None, "Unsupported format")
        start_btn.config(state="disabled")

# --- Main Window ---

#region Main window

root = tk.Tk()
root.title("Steganography Tool")
root.geometry("1000x600")
root.resizable(False, False)

style = ttk.Style()
style.theme_use('clam')

#endregion

#region Style

# Define colors for the theme
BG_COLOR = "#18122B"       # A dark space blue/purple
FRAME_COLOR = "#1B1530"    # A slightly different dark blue for frames
TEXT_COLOR = "#BAABED"       # A vibrant color for text, like a distant nebula
BUTTON_COLOR = "#393053"   # A deep blue for buttons
ACTIVE_BUTTON_COLOR = "#443C68" # The text color for emphasis

# Apply background color to the main window
root.configure(bg=BG_COLOR)

# --- Style Configuration ---
style = ttk.Style()

# Changing the theme
style.theme_use('clam')

# Configure the style for Frames
style.configure("TFrame", background=FRAME_COLOR)

# Configure the style for Labels
style.configure("TLabel", background=FRAME_COLOR, foreground=TEXT_COLOR, font=("Arial", 10))

# Configure the style for Buttons
style.configure("TButton",
    background=BUTTON_COLOR,
    foreground="white",
    font=("Arial", 10, "bold"),
    borderwidth=0,
    focuscolor=TEXT_COLOR # Color on focus
)
# What happens when mouse is over the button
style.map("TButton",
    background=[('active', ACTIVE_BUTTON_COLOR)]
)

# Configure the custom style for the ACTIVE mode button
style.configure("Active.TButton",
    background=ACTIVE_BUTTON_COLOR,
    foreground="white"
)

#endregion


# --- Creating Content Frames ---

#region Frames

# Left frame. Fixated width
left_panel = ttk.Frame(root, width=300)
left_panel.pack(side="left", fill="y", padx=5, pady=5)
left_panel.pack_propagate(False) 

# Right frame. Takes remaining space
right_panel = ttk.Frame(root)
right_panel.pack(side="right", expand=True, fill="both", padx=5, pady=5)

#endregion


# --- Left Frame Content ---

#region Left Frame

# 1. File select button
choose_file_btn = ttk.Button(left_panel, text="Choose file", command=select_file)
choose_file_btn.pack(pady=10, padx=10, fill="x")

# 2. File Name Label
file_name_label = ttk.Label(left_panel, text="No file selected", wraplength=180, anchor="center")
file_name_label.pack(pady=5, padx=10, fill="x")

# 3. Preview Frame
preview_frame = ttk.Frame(left_panel, height=300, style="Preview.TFrame")
preview_frame.pack(pady=10, padx=10, fill="x")
preview_frame.pack_propagate(False)

preview_label = ttk.Label(preview_frame, text="Preview", style="Preview.TLabel")
preview_label.pack(expand=True, fill="both", anchor="center")

style.configure("Preview.TFrame", background="#10101a") # A slightly darker background for the preview
style.configure("Preview.TLabel", anchor="center") # Center the "Preview" text

# 4. Changing Mode
hide_btn = ttk.Button(left_panel, text="Hide", command=lambda: set_mode('hide'))
hide_btn.pack(side="bottom", pady=10, padx=10, fill="x")

extract_btn = ttk.Button(left_panel, text="Extract", command=lambda: set_mode('extract'))
extract_btn.pack(side="bottom", pady=5, padx=10, fill="x")

#endregion



# --- Right Frame Content ---

#region Right Frame

# --- Top frame for parameters ---
# We will use the .grid() manager here for easy alignment
params_frame = ttk.Frame(right_panel, style="TFrame")
params_frame.pack(side="top", fill="x", padx=10, pady=10)

# Configure grid columns to have some padding
params_frame.columnconfigure(0, pad=5)
params_frame.columnconfigure(1, pad=5)
params_frame.columnconfigure(2, pad=5)
params_frame.columnconfigure(3, pad=5)

# --- 1. Block Size (p) ---
block_size_label = ttk.Label(params_frame, text="Block Size (p):")
block_size_label.grid(row=0, column=0, sticky="w")

block_size_entry = ttk.Entry(params_frame, width=15)
block_size_entry.grid(row=1, column=0)
block_size_entry.insert(0, "3") # Default value

# --- 2. Depth ---
depth_label = ttk.Label(params_frame, text="Depth:")
depth_label.grid(row=0, column=1, sticky="w")

depth_entry = ttk.Entry(params_frame, width=15)
depth_entry.grid(row=1, column=1)
depth_entry.insert(0, "1") # Default value

# --- 3. Password / Key ---
password_label = ttk.Label(params_frame, text="Password:")
password_label.grid(row=0, column=2, sticky="w")

password_entry = ttk.Entry(params_frame, width=15, show="*")
password_entry.grid(row=1, column=2)
# We can leave this empty or add a placeholder

# --- 4. Stop Sequence ---
stop_label = ttk.Label(params_frame, text="Stop Sequence:")
stop_label.grid(row=0, column=3, sticky="w")

stop_entry = ttk.Entry(params_frame, width=15)
stop_entry.grid(row=1, column=3)
stop_entry.insert(0, "&#@") # Default value

start_btn = ttk.Button(right_panel, text="Start", state="disabled")
start_btn.pack(side="bottom", anchor="se", padx=20, pady=20)

# App start
set_mode('hide')
root.mainloop()