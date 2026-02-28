Raspberry Pi PiCamera2 → Flask MJPEG Stream (README)

This project streams live video from a Raspberry Pi camera (PiCamera) to a local web server using Picamera2, OpenCV, and Flask. It exposes an MJPEG stream endpoint that you can open in a browser or embed in other applications on your LAN.

What this does

Initializes a Raspberry Pi camera using Picamera2

Captures frames continuously in a background thread

Encodes frames to JPEG (low bandwidth friendly)

Serves the latest frame as an MJPEG stream over HTTP via Flask

Includes:

/ → MJPEG video stream

/health → health check endpoint

Automatically restarts the camera if captures stall for too long

How it works (architecture)
Threads & shared state

Capture thread (capture_loop)

Reads camera frames at a target FPS

Encodes them to JPEG

Stores only the latest JPEG bytes in latest_jpeg (shared variable)

Flask request thread(s)

Each client hitting / uses generate_frames() (a generator)

The generator repeatedly yields the most recent JPEG in MJPEG format

Concurrency controls

cam_lock: protects camera start/stop/capture operations

latest_lock: protects reading/writing the shared latest_jpeg buffer

Stall detection & recovery

If no successful frame has been produced for STALL_SEC seconds, the camera is restarted.

Endpoints
GET /

Returns an MJPEG stream:

MIME type: multipart/x-mixed-replace; boundary=frame

Suitable for:

Browser viewing

<img src="http://pi.local:5000/"> embedding

Simple viewers like VLC

GET /health

Returns:

200 OK with body: ok

Configuration (tunable constants)
Variable	Meaning	Default
FPS	Target capture framerate	5.0
FRAME_INTERVAL	Derived pacing delay	1.0 / FPS
JPEG_QUALITY	JPEG compression quality (lower = smaller)	40
STALL_SEC	Restart camera if no frames succeeded in this time	5.0
Resolution	Capture size	480 x 360
Brightness	Camera brightness control	0.1

Notes:

Higher FPS increases CPU/bandwidth usage.

Higher resolution increases CPU/bandwidth usage.

JPEG quality is a large lever for network performance.

Requirements
Hardware

Raspberry Pi (you used a Raspberry Pi)

Raspberry Pi Camera module (compatible with Picamera2)

Local network access (LAN/Wi-Fi)

Software

Raspberry Pi OS (Bullseye or newer recommended)

Python 3

System packages for camera + OpenCV

Python packages: flask, opencv-python (or distro OpenCV), picamera2

Step-by-step setup and usage
1) Enable the camera

Connect the camera module to the Pi (CSI ribbon cable).

Enable camera support:

sudo raspi-config

Navigate to Interface Options (or similar)

Enable Camera

Reboot:

sudo reboot

2) Update system packages
sudo apt update && sudo apt upgrade -y
3) Install dependencies

Picamera2 is typically installed via apt on Raspberry Pi OS:

sudo apt install -y python3-flask python3-opencv python3-picamera2

If your distro packaging differs, you may need to adapt, but the project fundamentally needs:

Flask

OpenCV (cv2)

Picamera2

4) Save the script

Create a file, for example:

mkdir -p ~/mjpeg-stream
nano ~/mjpeg-stream/app.py

Paste your code into app.py, save, exit.

5) Run the server
python3 ~/mjpeg-stream/app.py

You should see a log line like:

Camera started

Flask will bind to:

0.0.0.0:5000 (meaning reachable from other devices on your LAN)

6) View the stream from another device

Find your Pi’s IP:

hostname -I

Then open in a browser on your phone/laptop (same network):

http://<PI_IP>:5000/

Health check:

http://<PI_IP>:5000/health

7) Optional: embed the stream in a web page

MJPEG works nicely in a simple <img> tag:

<img src="http://<PI_IP>:5000/" alt="Live stream">
8) Optional: run on boot (systemd)

Create a service file:

sudo nano /etc/systemd/system/mjpeg-stream.service

Example content:

[Unit]
Description=Raspberry Pi MJPEG Stream
After=network.target

[Service]
WorkingDirectory=/home/pi/mjpeg-stream
ExecStart=/usr/bin/python3 /home/pi/mjpeg-stream/app.py
Restart=always
User=pi

[Install]
WantedBy=multi-user.target

Enable + start:

sudo systemctl daemon-reload
sudo systemctl enable mjpeg-stream
sudo systemctl start mjpeg-stream
sudo systemctl status mjpeg-stream
Notes & troubleshooting
Black screen / no camera

Ensure the ribbon cable is seated correctly.

Confirm camera is enabled in raspi-config.

Ensure you’re using a Picamera2-compatible setup (newer Pi OS versions).

Stream loads but is slow

Reduce resolution (e.g., size: (320, 240))

Reduce FPS

Reduce JPEG_QUALITY (but image will degrade)

Multiple viewers

This approach is efficient because:

The capture thread produces one “latest frame”

All clients reuse that latest frame buffer
But more clients still means more HTTP streaming overhead.

Security warning (LAN use)

This is intentionally simple and unauthenticated. Don’t expose it directly to the public internet without adding:

authentication

TLS

a reverse proxy (e.g., nginx)

firewall rules

File overview

app.py – main application

init_camera() – configure & start camera

capture_loop() – capture frames, encode JPEG, detect stalls

generate_frames() – yield MJPEG multipart frames

Flask routes / and /health
