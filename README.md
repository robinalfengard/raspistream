# Raspberry Pi PiCamera2 → Flask MJPEG Stream

This project streams live video from a Raspberry Pi camera (PiCamera) to a local web server using **Picamera2**, **OpenCV**, and **Flask**. It exposes an **MJPEG** stream endpoint that you can open in a browser or embed in other applications on your LAN.

---

## Overview

This application:

- Initializes a Raspberry Pi camera using Picamera2
- Captures frames continuously in a background thread
- Encodes frames to JPEG (bandwidth-efficient)
- Serves the latest frame as an MJPEG stream over HTTP via Flask
- Provides:
  - `/` → MJPEG video stream
  - `/health` → health check endpoint
- Automatically restarts the camera if frame capture stalls

---

## Architecture

### Thread Model

**1. Capture Thread (`capture_loop`)**
- Captures frames at a target FPS
- Encodes frames to JPEG
- Stores only the latest JPEG bytes in shared memory

**2. Flask Thread(s)**
- Each client hitting `/` receives frames from `generate_frames()`
- The generator continuously yields the latest JPEG in MJPEG format

---

### Concurrency Controls

- `cam_lock` → Protects camera start/stop/capture operations
- `latest_lock` → Protects access to the shared `latest_jpeg` buffer

---

### Stall Detection

If no frame has been successfully captured for `STALL_SEC` seconds:
- The camera is automatically restarted

---

## Endpoints

### `GET /`

Returns an MJPEG stream:

- MIME type: `multipart/x-mixed-replace; boundary=frame`
- Can be viewed directly in a browser
- Can be embedded using an `<img>` tag
- Can be consumed by tools like VLC

---

## Configuration

The following constants can be tuned:

| Variable        | Description                                  | Default |
|---------------|----------------------------------------------|---------|
| `FPS`         | Target capture framerate                     | 5.0     |
| `JPEG_QUALITY`| JPEG compression quality (lower = smaller)   | 40      |
| `STALL_SEC`   | Restart camera if stalled beyond this time   | 5.0     |
| Resolution    | Frame size                                   | 480x360 |
| Brightness    | Camera brightness control                    | 0.1     |

### Performance Notes

- Increasing `FPS` increases CPU usage.
- Higher resolution increases CPU and bandwidth usage.
- Lower `JPEG_QUALITY` reduces bandwidth at the cost of image quality.

---

# Setup Guide (Step-by-Step)

## 1. Hardware Requirements

- Raspberry Pi (Bullseye or newer recommended)
- Raspberry Pi Camera Module
- Network connection (LAN or Wi-Fi)

---

## 2. Enable Camera

bash
sudo raspi-config

Navigate to Interface Options

Enable Camera

Reboot:

sudo reboot

## 3. Update System
sudo apt update && sudo apt upgrade -y
4. Install Dependencies
sudo apt install -y python3-flask python3-opencv python3-picamera2
5. Create Project Directory
mkdir -p ~/mjpeg-stream
nano ~/mjpeg-stream/app.py

Paste your Python script into app.py.

6. Run the Server
python3 ~/mjpeg-stream/app.py

Flask will bind to:

0.0.0.0:5000

This makes it accessible from other devices on the same network.

7. Access the Stream

Find your Raspberry Pi IP:

hostname -I

Open in a browser (same network):

http://<PI_IP>:5000/

Health endpoint:

http://<PI_IP>:5000/health
8. Embed in HTML
<img src="http://<PI_IP>:5000/" alt="Live Stream">
9. Run Automatically at Boot (Optional)

Create a systemd service:

sudo nano /etc/systemd/system/mjpeg-stream.service

Add:

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

Enable and start:

sudo systemctl daemon-reload
sudo systemctl enable mjpeg-stream
sudo systemctl start mjpeg-stream
sudo systemctl status mjpeg-stream
Troubleshooting
Black Screen / No Camera

Verify ribbon cable is properly seated

Ensure camera is enabled via raspi-config

Confirm compatible Raspberry Pi OS version

Slow Stream

Try:

Reducing resolution (e.g., 320x240)

Lowering FPS

Reducing JPEG_QUALITY

Multiple Viewers

The design is efficient because:

Only one capture thread runs

All clients reuse the latest frame buffer

However, each client still consumes HTTP bandwidth.

Security Notice

This server:

Has no authentication

Uses plain HTTP

Is intended for LAN usage only

Do not expose it directly to the internet without:

Authentication

TLS (HTTPS)

Reverse proxy (e.g., Nginx)

Firewall rules

File Structure
mjpeg-stream/
│
├── app.py
└── README.md
Summary

This project provides a lightweight, robust MJPEG streaming server using:

Picamera2

OpenCV

Flask

Multi-threaded capture loop

Automatic stall recovery

It is ideal for local monitoring, prototyping, robotics projects, and embedded systems on Raspberry Pi.
