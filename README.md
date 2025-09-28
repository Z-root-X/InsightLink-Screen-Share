# InsightLink: Real-Time Educational Screen Sharing

<p align="center">
  <img src="logo.png" alt="InsightLink Logo" width="400"/>
</p>

<p align="center">
  <strong>A secure and efficient screen sharing application designed for the modern classroom.</strong>
  <br />
  <a href="#features">Features</a> •
  <a href="#getting-started">Getting Started</a> •
  <a href="#usage">Usage</a> •
  <a href="#security-considerations">Security</a> •
  <a href="#license">License</a>
</p>

---

InsightLink is a real-time, high-performance screen sharing tool built for educators. It provides a simple and effective way for a teacher to broadcast their screen to multiple students across a local network. With features focused on security and classroom management, InsightLink ensures a stable and controlled learning environment.

## Features

### Teacher Application (`insightlink_teacher.py`)

- 🖥️ **Effortless Streaming:** Start and stop the screen sharing session with a single click.
- ⏸️ **Stream Control:** Pause and resume the broadcast at any time without disconnecting students.
- 📶 **Adaptive Quality:** Choose from High, Medium, or Low stream quality to match your network's performance.
- 👥 **Student Management:** Monitor all connected students in a clear list and selectively disconnect them if necessary.
- 💧 **Dynamic Watermarking:** For academic integrity, each student's stream is automatically watermarked with their IP address and a live timestamp.
- 🌐 **Easy IP Discovery:** The teacher's local IP address is displayed directly in the app, making it simple for students to connect.

### Student Application (`insightlink_student.py`)

- 🔌 **Simple Connection:** Students can join a session by entering the teacher's IP address—no complex setup required.
- 🖼️ **Immersive Viewing:** The application automatically enters a distraction-free, fullscreen mode.
- ⌨️ **Fullscreen Toggle:** Students can press the `Esc` key to easily enter or exit fullscreen mode.
- 🔒 **Informed Consent:** Before connecting, students are notified that the session is monitored and watermarked.

## Getting Started

Follow these instructions to get InsightLink running on your local network.

### Prerequisites

- Python 3.7 or newer.
- The required Python libraries, which can be found in `requirements.txt`.

### Installation

1.  **Clone the repository to your local machine:**
    ```sh
    git clone https://github.com/your-username/your-repository-name.git
    cd your-repository-name
    ```

2.  **Set up a Python virtual environment (recommended):**
    ```sh
    # Create a virtual environment
    python -m venv venv

    # Activate it
    # On Windows:
    venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install the required dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

4.  **Ensure Required Assets are Present:**
    The following files must be in the same directory as the Python scripts for the application to run correctly:
    - `logo.png` (Application logo)
    - `theme.ico` (Window icon)
    - `arial.ttf` (Font for the watermark feature)

## Usage

1.  **Launch the Teacher Application:**
    Run the `insightlink_teacher.py` script.
    ```sh
    python insightlink_teacher.py
    ```
    - Take note of the IP address shown at the bottom of the window.
    - Choose your desired stream quality and click **"Start Sharing"**.

2.  **Launch the Student Application:**
    On a student's machine (on the same network), run the `insightlink_student.py` script.
    ```sh
    python insightlink_student.py
    ```
    - Enter the teacher's IP address that you noted earlier.
    - Click **"Connect to Session"** and accept the monitoring notice to start viewing.

## Security Considerations

- ⚠️ **No Encryption:** This application **does not encrypt** the screen sharing data. It is designed for use on trusted networks only (e.g., a private school LAN or a home network). **Do not use on public or untrusted Wi-Fi.**
- **Input Validation:** The student application validates the IP address format to prevent errors.
- **Denial-of-Service (DoS) Protection:** The student client limits the size of incoming image data to prevent a malicious server from crashing the application.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.