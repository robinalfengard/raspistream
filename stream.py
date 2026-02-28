from picamera2 import Picamera2
from flask import Flask, Response
import cv2
import threading
import time
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Shared latest JPEG
latest_jpeg = None
latest_lock = threading.Lock()

# Camera state
cam_lock = threading.Lock()
camera = None

FPS = 5.0
FRAME_INTERVAL = 1.0 / FPS
JPEG_QUALITY = 40
STALL_SEC = 5.0


def init_camera():
    global camera
    cam = Picamera2()
    cam.configure(
        cam.create_video_configuration(
            main={"format": "RGB888", "size": (480, 360)},
            controls={"FrameRate": FPS},
        )
    )
    cam.set_controls({"Brightness": 0.1})
    cam.start()
    camera = cam
    logging.info("Camera started")


def stop_camera():
    global camera
    if camera is None:
        return
    try:
        camera.stop()
    except Exception:
        pass
    try:
        camera.close()
    except Exception:
        pass
    camera = None
    logging.info("Camera stopped/closed")


def restart_camera():
    with cam_lock:
        stop_camera()
        time.sleep(0.5)
        init_camera()


def capture_loop():
    global latest_jpeg
    encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
    last_ok = time.time()

    # initial start
    with cam_lock:
        init_camera()

    while True:
        t0 = time.time()
        try:
            with cam_lock:
                frame = camera.capture_array()
            ok, buf = cv2.imencode(".jpg", frame, encode_params)
            if ok:
                with latest_lock:
                    latest_jpeg = buf.tobytes()
                last_ok = time.time()
        except Exception as e:
            logging.exception(f"Capture failed: {e}")

        # stall detection
        if time.time() - last_ok > STALL_SEC:
            logging.error("Camera appears stalled; restarting camera")
            try:
                restart_camera()
            except Exception:
                logging.exception("Camera restart failed")
                time.sleep(2.0)
            last_ok = time.time()

        # pacing
        dt = time.time() - t0
        if dt < FRAME_INTERVAL:
            time.sleep(FRAME_INTERVAL - dt)


def generate_frames():
    try:
        while True:
            with latest_lock:
                jpg = latest_jpeg
            if jpg is None:
                time.sleep(0.1)
                continue
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + jpg + b"\r\n"
            )
            time.sleep(0.05)
    except (GeneratorExit, BrokenPipeError, ConnectionResetError):
        return


@app.route("/")
def video_feed():
    return Response(generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/health")
def health():
    return "ok", 200


if __name__ == "__main__":
    threading.Thread(target=capture_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, threaded=True, use_reloader=False)