#       
#   1. Test Color on different monitors to check if it`s not too bright
#

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import os
import random
import threading
from PIL import Image, ImageTk
import io
import cv2
import librosa
import matplotlib.pyplot as plt
import numpy as np
import queue
import core


photo_references = {}

log_queue = queue.Queue()

input_filepath = ''
output_directory = ''

#region Functions

# --- Function ---
def select_file():
    """Opens file choose dialoge"""
    global input_filepath
    filepath = filedialog.askopenfilename(
        title="Select a file",
        filetypes=(
            ("Media Files", "*.png *.jpg *.mp4 *.mp3 *.wav"),
            ("All files", "*.*")
        )
    )

    if not filepath:
        return
    
    input_filepath = filepath

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
    """Change the look of UI depending on mode"""
    global current_mode
    if mode == 'hide':
        hide_btn.config(style="Active.TButton")
        extract_btn.config(style="TButton")
        message_area.config(state="normal")
        output_frame.grid()
        folder_btn.grid()
        print("Mode set to: Hide")
        current_mode = 'hide'
    elif mode == 'extract':
        extract_btn.config(style="Active.TButton")
        hide_btn.config(style="TButton")
        message_area.delete('1.0', tk.END)
        message_area.config(state="disabled")
        output_frame.grid_remove()
        folder_btn.grid_remove()
        print("Mode set to: Extract")
        current_mode = 'extract'

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

#region Start proccessing
def start_processing():
    """
    Main function that starts work.
    """
    global input_filepath
    global output_directory

    if input_filepath == '':
        messagebox.showerror("Error", "Please choose a file.")
        return
    try:
        p_val = int(block_size_entry.get())
        depth_val = int(depth_entry.get())
        password_val = int(password_entry.get())
    except ValueError:
        messagebox.showerror("Error", "Parameters are invalid.")
        return

    message_val = message_area.get("1.0", tk.END).strip()
    stop_seq_val = stop_entry.get()
    encryption_val = encryption_combo.get()
    hide_method_val = hide_method_combo.get()

    if output_directory == '':
        output_directory = os.path.dirname(input_filepath)
    
    output_filename = "output_" + os.path.basename(input_filepath)
    output_filepath = os.path.join(output_directory, output_filename)

    logs_area.config(state="normal")
    logs_area.delete('1.0', tk.END)
    logs_area.config(state="disabled")
    progress_bar['value'] = 0
    
    thread = threading.Thread(
        target=processing_thread, 
        args=(
            current_mode, input_filepath, message_val, password_val, stop_seq_val,
            encryption_val, hide_method_val, p_val, depth_val, output_filepath, log_queue
        )
    )
    thread.daemon = True
    thread.start()

def prog(value):
    progress_bar['value'] = value

def log(msg):
    """Log function"""
    logs_area.config(state="normal")
    logs_area.insert(tk.END, msg + "\n")
    logs_area.see(tk.END)
    logs_area.config(state="disabled")

def processing_thread(
    mode, filepath, message, password, stop_seq, 
    encryption, hide_method, p, depth, output_path, log_queue
):
    """
    A function that opens main file in another thread.
    """

    try:
        log("Opening file.")
        stego_media = core.ImageMedia(filepath)
        prog(10)

        if mode == 'hide':
            log("Starting message hiding")
            stego_media.hide(message, password, stop_seq, encryption, hide_method, p, depth, output_path, log_queue)
            messagebox.showinfo("Success", f"Message successfuly hiden in:\n{output_path}")

        elif mode == 'extract':
            log("Starting message extracting")
            extracted_message = stego_media.extract(password, stop_seq, encryption, hide_method, p, depth, log_queue)
            
            if extracted_message:
                message_area.config(state="normal")
                message_area.delete('1.0', tk.END)
                message_area.insert('1.0', extracted_message)
                message_area.config(state="disabled")
            else:
                log("Could not extract a message")
                messagebox.showerror("Error", "Could not extract message. Check parameters")

    except Exception as e:
        log(f"Critical error: {e}")
        messagebox.showerror("Critical error", str(e))
    
    prog(0)

def choose_output_folder():
    global output_directory
    path = filedialog.askdirectory(title="Choose folder for saving")
    if path:
        output_directory = path

def process_queue():
    """
    Check the queue for Logs
    """
    try:
        message_type, value = log_queue.get_nowait()
        
        if message_type == 'log':
            log(value)
        elif message_type == 'progress':
            prog(value)
            
    except queue.Empty:
        pass

    root.after(100, process_queue)

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

right_panel.columnconfigure(0, weight=1)
right_panel.columnconfigure(1, weight=100)
right_panel.columnconfigure(2, weight=1)
right_panel.rowconfigure(1, weight=1)

#region Controls
# --- Column 1: Controls ---
controls_frame = ttk.Frame(right_panel, style="TFrame")
controls_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5, rowspan=2)

# 1.1. Hiding methods
hide_method_label = ttk.Label(controls_frame, text="Hide method:")
hide_method_label.pack(pady=(10, 2), padx=10, anchor="w")
hide_method_combo = ttk.Combobox(controls_frame, values=["LSB"], state="readonly")
hide_method_combo.set("LSB")
hide_method_combo.pack(pady=2, padx=10, fill="x")

# 1.2. Data fields
# --- Block Size (p) ---
block_size_label = ttk.Label(controls_frame, text="Block size (p):")
block_size_label.pack(pady=(10, 2), padx=10, anchor="w")
block_size_entry = ttk.Entry(controls_frame)
block_size_entry.insert(0, "3")
block_size_entry.pack(pady=2, padx=10, fill="x")

# --- Depth ---
depth_label = ttk.Label(controls_frame, text="Depth:")
depth_label.pack(pady=(10, 2), padx=10, anchor="w")
depth_entry = ttk.Entry(controls_frame)
depth_entry.insert(0, "1")
depth_entry.pack(pady=2, padx=10, fill="x")

# --- Password / Key ---
password_label = ttk.Label(controls_frame, text="Password(prime number):")
password_label.pack(pady=(10, 2), padx=10, anchor="w")
password_entry = ttk.Entry(controls_frame)
password_entry.pack(pady=2, padx=10, fill="x")

# --- Stop Sequence ---
stop_label = ttk.Label(controls_frame, text="Stop sequence:")
stop_label.pack(pady=(10, 2), padx=10, anchor="w")
stop_entry = ttk.Entry(controls_frame)
stop_entry.insert(0, "#%$")
stop_entry.pack(pady=2, padx=10, fill="x")

# 1.3. Encryption
encryption_label = ttk.Label(controls_frame, text="Encryption:")
encryption_label.pack(pady=(20, 2), padx=10, anchor="w")
encryption_combo = ttk.Combobox(controls_frame, values=["Binary XOR", "None"], state="readonly")
encryption_combo.set("None")
encryption_combo.pack(pady=2, padx=10, fill="x")

#region Message and logs
# --- Column 2: Message and logs ---
center_frame = ttk.Frame(right_panel, style="TFrame")
center_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5, rowspan=2)

center_frame.rowconfigure(0, weight=0) 
center_frame.rowconfigure(1, weight=1)
center_frame.rowconfigure(2, weight=0)
center_frame.rowconfigure(3, weight=1)
center_frame.columnconfigure(0, weight=1)

# 2.1. Message field
message_label = ttk.Label(center_frame, text="Message:")
message_label.grid(row=0, column=0, sticky="nw", padx=10, pady=(5, 0))
message_area = scrolledtext.ScrolledText(center_frame, height=10, wrap=tk.WORD)
message_area.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

# 2.2. Log field
logs_label = ttk.Label(center_frame, text="Logs:")
logs_label.grid(row=2, column=0, sticky="nw", padx=10, pady=(5, 0))
logs_area = scrolledtext.ScrolledText(center_frame, height=10, state="disabled", wrap=tk.WORD)
logs_area.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)

#region Results
# --- Column 3: Results ---
output_frame = ttk.Frame(right_panel, style="TFrame")
output_frame.grid(row=0, column=2, sticky="nsew", padx=5, pady=5, rowspan=2)

# 3.1. Image dropdown
output_view_label = ttk.Label(output_frame, text="Representation:")
output_view_label.pack(pady=(10, 2), padx=10, anchor="w")
output_view_combo = ttk.Combobox(output_frame, values=["Result"], state="readonly")
output_view_combo.set("Result")
output_view_combo.pack(pady=2, padx=10, fill="x")

# 3.2. Result preview
output_preview_label = ttk.Label(output_frame, text="Output", style="Preview.TLabel", anchor="center")
output_preview_label.pack(pady=10, padx=10, expand=True, fill="both")

#region Progress and start
# --- Lower panel: Progress and start ---
bottom_frame = ttk.Frame(right_panel, style="TFrame")
bottom_frame.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
bottom_frame.columnconfigure(0, weight=1)

# 4.1.Progress bar
progress_bar = ttk.Progressbar(bottom_frame, orient="horizontal", length=100, mode="determinate")
progress_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

# 4.2. Buttons
folder_btn = ttk.Button(bottom_frame, text="Choose folder", command=choose_output_folder)
folder_btn.grid(row=0, column=1, padx=10, pady=10)

start_btn = ttk.Button(bottom_frame, text="Start", state="normal", command=start_processing)
start_btn.grid(row=0, column=2, padx=10, pady=10)

# App start
root.after(100, process_queue)
set_mode('hide')
root.mainloop()