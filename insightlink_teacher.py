# insightlink_teacher.py
# Final Production Version
# App Name: InsightLink v1.0
# Developed by: Zihad Hasan

import socket, threading, struct, io, time, sys, os, re
import mss
from PIL import Image, ImageDraw, ImageFont, ImageTk, UnidentifiedImageError
import tkinter as tk
from tkinter import ttk, messagebox, Listbox, END

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- Application Constants & Branding ---
APP_NAME = "InsightLink Teacher"
APP_VERSION = "1.0"
DEVELOPER_NAME = "Zihad Hasan"
LOGO_PATH = resource_path("logo.png")
ICON_PATH = resource_path("theme.ico")
# NOTE: The 'arial.ttf' font file must be present in the same directory as the script
# or included in the PyInstaller build for the watermark feature to work correctly.
WATERMARK_FONT_PATH = resource_path("arial.ttf")


# --- Design Language ---
COLOR_PRIMARY_ORANGE = "#f0942e"
COLOR_TEXT_DARK = "#296e48"
COLOR_BACKGROUND = "#fafafa"
COLOR_FRAME_BG = "#ffffff"
FONT_PRIMARY = "Segoe UI"

# --- Network Configuration ---
HOST = '0.0.0.0'
PORT = 9999
QUALITY_SETTINGS = {
    "High (LAN)": {"quality": 90, "delay": 0.03},
    "Medium (Wi-Fi)": {"quality": 75, "delay": 0.05},
    "Low (Slow Net)": {"quality": 50, "delay": 0.1}
}
MAX_IMAGE_SIZE = 10 * 1024 * 1024 # 10 MB limit for incoming images

class ScreenSharingServer:
    """Manages all backend server logic: connections, streaming, and client handling."""
    def __init__(self, app_instance):
        self.app = app_instance
        self.is_running = False
        self.is_paused = False
        self.clients = {}
        self.clients_lock = threading.Lock()
        self.server_thread = None
        self.server_socket = None
        self.quality_profile = QUALITY_SETTINGS["Medium (Wi-Fi)"]

    def start(self, quality_profile_name):
        self.quality_profile = QUALITY_SETTINGS[quality_profile_name]
        self.is_running = True
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((HOST, PORT))
            self.server_socket.listen()
        except OSError:
            self.app.show_error("Server Error", f"Port {PORT} is already in use.\nPlease close other applications and try again.")
            self.is_running = False
            return False
        
        self.server_thread = threading.Thread(target=self._listen_for_clients)
        self.server_thread.daemon = True
        self.server_thread.start()
        self.app.update_status(f"Server is LIVE on {get_local_ip()}:{PORT}")
        return True

    def stop(self):
        self.is_running = False
        if self.server_socket:
            # Unblock the server socket accept() call
            try:
                socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((get_local_ip(), PORT))
            except:
                pass
            self.server_socket.close()

        with self.clients_lock:
            for conn in self.clients.values():
                conn.close()
            self.clients.clear()
        
        self.app.update_status("Server stopped. Ready to start a new session.")
        self.app.clear_client_list()

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        status = "paused" if self.is_paused else "resumed"
        self.app.update_status(f"Streaming {status}.")
        return self.is_paused

    def kick_client(self, client_address):
        with self.clients_lock:
            if client_address in self.clients:
                self.clients[client_address].close()

    def _listen_for_clients(self):
        while self.is_running:
            try:
                connection, address = self.server_socket.accept()
                if not self.is_running: break

                client_address_str = f"{address[0]}:{address[1]}"
                with self.clients_lock:
                    self.clients[client_address_str] = connection
                
                self.app.add_client_to_list(client_address_str)
                
                client_thread = threading.Thread(target=self._handle_client, args=(connection, client_address_str))
                client_thread.daemon = True
                client_thread.start()
            except OSError:
                if self.is_running: print("Error: Server socket closed unexpectedly.")
                break

    def _handle_client(self, connection, address_str):
        print(f"[CONNECTED] {address_str}")
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                while True:
                    with self.clients_lock:
                        if not self.is_running or address_str not in self.clients:
                            break
                    
                    if self.is_paused:
                        time.sleep(0.5)
                        continue

                    img = sct.grab(monitor)
                    pil_img = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
                    
                    draw = ImageDraw.Draw(pil_img, "RGBA")
                    try:
                        font_size = max(12, int(pil_img.height * 0.03))
                        font = ImageFont.truetype(WATERMARK_FONT_PATH, font_size)
                    except IOError:
                        font = ImageFont.load_default()
                        print(f"Warning: Could not load '{WATERMARK_FONT_PATH}'. Using default font.")
                    
                    watermark_text = f"VIEWER: {address_str.split(':')[0]} | {time.strftime('%Y-%m-%d %H:%M:%S')}"
                    draw.text((15, 15), watermark_text, font=font, fill=(255, 255, 255, 128))
                    
                    with io.BytesIO() as mem_file:
                        quality = self.quality_profile['quality']
                        pil_img.save(mem_file, 'JPEG', quality=quality)
                        image_bytes = mem_file.getvalue()

                    connection.sendall(struct.pack(">Q", len(image_bytes)))
                    connection.sendall(image_bytes)
                    time.sleep(self.quality_profile['delay'])
        except (ConnectionError, OSError) as e:
            print(f"[DISCONNECTED] {address_str} (Reason: {e})")
        finally:
            connection.close()
            with self.clients_lock:
                if address_str in self.clients:
                    del self.clients[address_str]
            self.app.remove_client_from_list(address_str)

class TeacherApp:
    """Manages the entire graphical user interface and user interactions."""
    def __init__(self, window):
        self.window = window
        self.server = ScreenSharingServer(self)
        self._setup_window()
        self._setup_styles()
        self._create_widgets()
        
    def _setup_window(self):
        self.window.title(f"{APP_NAME} v{APP_VERSION}")
        self.window.geometry("600x600")
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
        style = ttk.Style(self.window)
        style.theme_use("clam")
        style.configure("TFrame", background=COLOR_BACKGROUND)
        style.configure("TLabel", background=COLOR_BACKGROUND, foreground=COLOR_TEXT_DARK, font=(FONT_PRIMARY, 10))
        style.configure("Header.TLabel", font=(FONT_PRIMARY, 12, "bold"))
        style.configure("TLabelframe", background=COLOR_FRAME_BG, bordercolor="#e0e0e0")
        style.configure("TLabelframe.Label", background=COLOR_FRAME_BG, foreground=COLOR_TEXT_DARK, font=(FONT_PRIMARY, 11, "bold"))
        style.configure("TButton", font=(FONT_PRIMARY, 10), padding=6)
        style.configure("Accent.TButton", font=(FONT_PRIMARY, 10, "bold"), foreground="white", background=COLOR_PRIMARY_ORANGE)
        style.map("Accent.TButton", background=[("active", "#ffad4f")])
        style.configure("Stop.TButton", font=(FONT_PRIMARY, 10, "bold"), foreground="white", background="#d32f2f")
        style.map("Stop.TButton", background=[("active", "#ef5350")])
        style.configure("Status.TLabel", background="#333333", foreground="white", padding=5, font=(FONT_PRIMARY, 9))

    def _create_widgets(self):
        header = ttk.Frame(self.window, padding=10)
        header.pack(fill=tk.X)
        if self.logo_image:
            ttk.Label(header, image=self.logo_image).pack()
        else:
            ttk.Label(header, text=APP_NAME, style="Header.TLabel").pack()

        main_frame = ttk.Frame(self.window, padding=(20, 10))
        main_frame.pack(fill=tk.BOTH, expand=True)

        controls_frame = ttk.LabelFrame(main_frame, text="Session Controls", padding=15)
        controls_frame.pack(fill=tk.X)
        controls_frame.columnconfigure(1, weight=1)

        ttk.Label(controls_frame, text="Stream Quality:", font=(FONT_PRIMARY, 10)).grid(row=0, column=0, padx=(0, 10), pady=10, sticky="w")
        self.quality_var = tk.StringVar(value=list(QUALITY_SETTINGS.keys())[1])
        self.quality_menu = ttk.OptionMenu(controls_frame, self.quality_var, None, *QUALITY_SETTINGS.keys())
        self.quality_menu.grid(row=0, column=1, columnspan=2, padx=5, pady=10, sticky="ew")

        self.start_button = ttk.Button(controls_frame, text="Start Sharing", command=self._start_server, style="Accent.TButton", width=15)
        self.start_button.grid(row=1, column=0, padx=(0, 5), pady=10)
        self.stop_button = ttk.Button(controls_frame, text="Stop Sharing", command=self._stop_server, style="Stop.TButton", state=tk.DISABLED, width=15)
        self.stop_button.grid(row=1, column=1, padx=5, pady=10)
        self.pause_button = ttk.Button(controls_frame, text="Pause Stream", command=self._toggle_pause, state=tk.DISABLED, width=15)
        self.pause_button.grid(row=1, column=2, padx=(5, 0), pady=10)

        clients_frame = ttk.LabelFrame(main_frame, text="Student Management", padding=15)
        clients_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        clients_frame.rowconfigure(0, weight=1)
        clients_frame.columnconfigure(0, weight=1)
        
        self.client_listbox = Listbox(clients_frame, font=("Courier New", 10), height=8, bg=COLOR_FRAME_BG, relief=tk.FLAT, highlightthickness=1, highlightbackground="#cccccc")
        self.client_listbox.grid(row=0, column=0, sticky="nsew")
        self.client_listbox.bind("<<ListboxSelect>>", self._on_client_select)

        kick_button_frame = ttk.Frame(clients_frame, style="TFrame", padding=(10,0))
        kick_button_frame.grid(row=0, column=1, sticky="ns")
        self.kick_button = ttk.Button(kick_button_frame, text="Kick Student", command=self._kick_selected_client, state=tk.DISABLED)
        self.kick_button.pack(anchor="center")
        
        self.status_var = tk.StringVar(value=f"Ready. Your IP is {get_local_ip()}")
        ttk.Label(self.window, textvariable=self.status_var, style="Status.TLabel").pack(side=tk.BOTTOM, fill=tk.X)

    def _start_server(self):
        if self.server.start(self.quality_var.get()):
            self.start_button.config(state=tk.DISABLED)
            self.quality_menu.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.pause_button.config(state=tk.NORMAL)
    
    def _stop_server(self):
        self.server.stop()
        self.start_button.config(state=tk.NORMAL)
        self.quality_menu.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.DISABLED, text="Pause Stream")
        self.kick_button.config(state=tk.DISABLED)

    def _toggle_pause(self):
        is_paused = self.server.toggle_pause()
        self.pause_button.config(text="Resume Stream" if is_paused else "Pause Stream")

    def _kick_selected_client(self):
        if not self.client_listbox.curselection(): return
        client_address = self.client_listbox.get(self.client_listbox.curselection()[0])
        self.server.kick_client(client_address)

    def _on_client_select(self, event):
        self.kick_button.config(state=tk.NORMAL if self.client_listbox.curselection() else tk.DISABLED)

    def _on_closing(self):
        if self.server.is_running and messagebox.askyesno("Confirm Exit", "A sharing session is active. Exiting will disconnect all students.\nAre you sure you want to exit?"):
            self.server.stop()
            self.window.destroy()
        elif not self.server.is_running:
            self.window.destroy()
            
    def update_status(self, text): self.window.after(0, lambda: self.status_var.set(text))
    def show_error(self, title, msg): self.window.after(0, lambda: messagebox.showerror(title, msg))
    def add_client_to_list(self, addr): self.window.after(0, lambda: self.client_listbox.insert(END, addr))
    def clear_client_list(self): self.window.after(0, lambda: self.client_listbox.delete(0, END))
    def remove_client_from_list(self, addr):
        def _remove():
            try:
                items = self.client_listbox.get(0, END)
                self.client_listbox.delete(items.index(addr))
            except (ValueError, tk.TclError): pass
        self.window.after(0, _remove)

def get_local_ip():
    """Finds the local IP address of the machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

if __name__ == "__main__":
    root = tk.Tk()
    app = TeacherApp(root)
    root.mainloop()