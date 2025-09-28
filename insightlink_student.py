# insightlink_student.py
# Final Production Version
# App Name: InsightLink v1.0
# Developed by: Zihad Hasan

import socket, threading, struct, io, time, sys, os, re
from PIL import Image, ImageTk, UnidentifiedImageError
import tkinter as tk
from tkinter import ttk, messagebox

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- Application Constants & Branding ---
APP_NAME = "InsightLink"
DEVELOPER_NAME = "Zihad Hasan"
LOGO_PATH = resource_path("logo.png")
ICON_PATH = resource_path("theme.ico")

# --- Design Language ---
COLOR_PRIMARY_ORANGE = "#f0942e"
COLOR_TEXT_DARK = "#296e48"
COLOR_BACKGROUND = "#fafafa"
FONT_PRIMARY = "Segoe UI"

# --- Network Configuration ---
PORT = 9999
MAX_IMAGE_SIZE = 10 * 1024 * 1024 # 10 MB limit for incoming images

# --- Regular Expressions ---
# Basic regex to validate an IPv4 address format.
IP_ADDRESS_REGEX = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")

class StudentApp:
    """Manages the student's GUI, connection logic, and stream viewing experience."""
    def __init__(self, window):
        self.window = window
        self.is_connected = False
        self.client_socket = None
        self.stream_window = None
        self.stream_label = None

        self._setup_window()
        self._setup_styles()
        self._create_connection_widgets()

    def _setup_window(self):
        """Initializes the main connection window properties."""
        self.window.title(APP_NAME)
        self.window.configure(bg=COLOR_BACKGROUND)
        self.window.protocol("WM_DELETE_WINDOW", self._on_closing)
        try:
            self.window.iconbitmap(ICON_PATH)
        except Exception:
            print("Warning: Could not load theme.ico. Ensure it's in the same folder.")
        try:
            self.logo_image = ImageTk.PhotoImage(Image.open(LOGO_PATH).resize((220, 55), Image.Resampling.LANCZOS))
        except Exception as e:
            self.logo_image = None
            print(f"Warning: Could not load logo.png. Error: {e}")

    def _setup_styles(self):
        """Configures the modern look and feel of the application widgets."""
        style = ttk.Style(self.window)
        style.theme_use("clam")
        style.configure("TFrame", background=COLOR_BACKGROUND)
        style.configure("TLabel", background=COLOR_BACKGROUND, foreground=COLOR_TEXT_DARK, font=(FONT_PRIMARY, 10))
        style.configure("Header.TLabel", font=(FONT_PRIMARY, 12, "bold"))
        style.configure("TButton", font=(FONT_PRIMARY, 10), padding=6)
        style.configure("Accent.TButton", font=(FONT_PRIMARY, 10, "bold"), foreground="white", background=COLOR_PRIMARY_ORANGE)
        style.map("Accent.TButton", background=[("active", "#ffad4f")])

    def _create_connection_widgets(self):
        """Creates and arranges all widgets for the initial connection screen."""
        header = ttk.Frame(self.window, padding=10)
        header.pack(pady=(10, 0))
        if self.logo_image:
            ttk.Label(header, image=self.logo_image).pack()
        else:
            ttk.Label(header, text=APP_NAME, style="Header.TLabel").pack()

        main_frame = ttk.Frame(self.window, padding=25)
        main_frame.pack(expand=True, fill=tk.BOTH)

        ttk.Label(main_frame, text="Enter Teacher's IP Address:", font=(FONT_PRIMARY, 12)).pack(pady=(0, 10))
        
        self.ip_entry = ttk.Entry(main_frame, font=(FONT_PRIMARY, 12), width=25, justify="center")
        self.ip_entry.pack(pady=5)
        self.ip_entry.focus_set()
        self.ip_entry.bind("<Return>", lambda event: self._connect_to_server())

        connect_button = ttk.Button(main_frame, text="Connect to Session", command=self._connect_to_server, style="Accent.TButton")
        connect_button.pack(pady=20)
        
        self.window.update_idletasks()
        width = 450
        height = 250
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        self.window.resizable(False, False)

    def _connect_to_server(self):
        """Handles the logic of connecting to the teacher's server."""
        teacher_ip = self.ip_entry.get().strip()
        if not teacher_ip:
            messagebox.showwarning("Input Required", "Please enter the teacher's IP address.")
            return

        if not IP_ADDRESS_REGEX.match(teacher_ip):
            messagebox.showwarning("Invalid IP", "Please enter a valid IPv4 address (e.g., 192.168.1.10).")
            return

        warning_accepted = messagebox.askokcancel("Session Monitoring Notice",
            "Welcome!\n\nThis session is monitored for security and academic integrity. The stream is dynamically watermarked with your IP address and a timestamp.\n\nThe connection is NOT encrypted. Please use on trusted networks only.\n\nBy clicking 'OK', you agree to these terms.")

        if not warning_accepted:
            return

        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((teacher_ip, PORT))
            self.is_connected = True
        except (socket.gaierror, ConnectionRefusedError, socket.timeout):
            messagebox.showerror("Connection Failed", f"Could not connect to {teacher_ip}.\nPlease check the IP address and ensure the teacher's session is active.")
            if self.client_socket: self.client_socket.close()
            return
        
        self.window.withdraw()
        self._open_stream_window()

        threading.Thread(target=self._receive_stream, daemon=True).start()

    def _open_stream_window(self):
        """Creates the immersive, fullscreen window for viewing the stream."""
        self.stream_window = tk.Toplevel(self.window)
        self.stream_window.title(f"Viewing Session - {APP_NAME}")
        self.stream_window.attributes("-fullscreen", True)
        try:
            self.stream_window.iconbitmap(ICON_PATH)
        except Exception:
            pass # Icon for stream window is less critical if it fails
        
        self.stream_label = ttk.Label(self.stream_window, background="black")
        self.stream_label.pack(fill=tk.BOTH, expand=True)

        self.stream_window.bind("<Escape>", self._handle_escape)
        self.stream_window.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _handle_escape(self, event=None):
        """Allows toggling fullscreen mode with the Escape key."""
        is_fullscreen = self.stream_window.attributes("-fullscreen")
        self.stream_window.attributes("-fullscreen", not is_fullscreen)

    def _receive_stream(self):
        """The core loop for receiving and displaying image data from the server."""
        try:
            while self.is_connected:
                header = self._receive_full_data(8)
                if not header: break
                image_size = struct.unpack(">Q", header)[0]

                if image_size > MAX_IMAGE_SIZE:
                    print(f"Error: Incoming image size ({image_size} bytes) exceeds the limit of {MAX_IMAGE_SIZE} bytes.")
                    break
                
                image_bytes = self._receive_full_data(image_size)
                if not image_bytes: break

                try:
                    pil_img = Image.open(io.BytesIO(image_bytes))
                except (UnidentifiedImageError, OSError) as img_err:
                    print(f"Error parsing image data: {img_err}. Skipping frame.")
                    continue
                
                win_w = self.stream_window.winfo_width()
                win_h = self.stream_window.winfo_height()
                
                if win_w <= 1 or win_h <= 1: 
                    time.sleep(0.1)
                    continue

                img_w, img_h = pil_img.size
                
                ratio = min(win_w / img_w, win_h / img_h)
                new_size = (int(img_w * ratio), int(img_h * ratio))
                
                resized_img = pil_img.resize(new_size, Image.Resampling.LANCZOS)
                tk_image = ImageTk.PhotoImage(resized_img)
                
                self.stream_label.config(image=tk_image)
                self.stream_label.image = tk_image
        except (ConnectionError, OSError) as e:
            print(f"Connection lost: {e}")
        finally:
            self.is_connected = False
            if self.client_socket: self.client_socket.close()
            if self.stream_window and self.stream_window.winfo_exists():
                 self.window.after(0, lambda: messagebox.showinfo("Disconnected", "Connection to the teacher has been closed."))
                 self.window.after(10, self._on_closing)

    def _receive_full_data(self, size):
        """A helper function to ensure the complete data packet is received from the socket."""
        data = bytearray()
        while len(data) < size:
            packet = self.client_socket.recv(size - len(data))
            if not packet: return None
            data.extend(packet)
        return data

    def _on_closing(self):
        """Gracefully handles the closing of the application to prevent errors."""
        self.is_connected = False
        if self.client_socket: self.client_socket.close()
        self.window.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = StudentApp(root)
    root.mainloop()