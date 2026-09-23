# KAVACH — RTSP CCTV Simulation Subproject Manual

This subproject provides a real, standalone **RTSP CCTV simulation server** for demonstrating the KAVACH AI Surveillance Platform with multiple simulated CCTV cameras over a Local Area Network (LAN) or local loopback.

---

## 1. What RTSP Is

**RTSP (Real-Time Streaming Protocol)** is an application-level network protocol designed for controlling real-time multimedia delivery. 
- It acts as an "electronic remote control" for multimedia streams, handling commands such as `DESCRIBE`, `SETUP`, `PLAY`, `PAUSE`, and `TEARDOWN`.
- The actual video payload is transmitted using RTP (Real-time Transport Protocol). In our CCTV simulation architecture, we use **RTSP-over-TCP** on port **8554**.
- RTSP-over-TCP interleaves RTP video packets directly into the TCP connection, preventing UDP packet loss over Wi-Fi/LAN, maintaining stream synchronization, and greatly simplifying firewall traversal.

---

## 2. Why KAVACH Uses It

In real-world security deployments:
- Commercial IP cameras (Hikvision, Dahua, Axis, Hanwha, Uniview) and NVRs/DVRs do not send raw video files or browser WebSockets; they stream high-definition H.264 video over **RTSP**.
- KAVACH's `CameraManager` connects directly to these RTSP endpoints using OpenCV (`cv2.VideoCapture`) with low-latency TCP buffering (`OPENCV_FFMPEG_CAPTURE_OPTIONS = "rtsp_transport;tcp"`).
- By running this simulation server, KAVACH connects to simulated RTSP URLs (e.g. `rtsp://192.168.1.50:8554/camera1`) **identically** to physical IP cameras. No code changes or fake frontend mocks are required.

---

## 3. How to Install MediaMTX

**MediaMTX** (formerly `rtsp-simple-server`) is a zero-dependency, high-performance RTSP server and routing proxy.

### Option A: Automatic Download (Recommended)
Open a terminal in `rtsp_simulator/` and run:
```cmd
python -m src.setup_binaries
```
or double-click:
```cmd
rtsp_simulator\scripts\download_mediamtx.bat
```
This automatically fetches the official Windows 64-bit release from GitHub and unpacks `mediamtx.exe` into `rtsp_simulator/mediamtx/mediamtx.exe`.

### Option B: Manual Installation
1. Go to the [MediaMTX Releases page](https://github.com/bluenviron/mediamtx/releases).
2. Download `mediamtx_vX.Y.Z_windows_amd64.zip`.
3. Extract `mediamtx.exe` into:
   ```
   AI-Surveillance/rtsp_simulator/mediamtx/mediamtx.exe
   ```

### FFmpeg Installation (for the Simulator Laptop)
The simulation laptop uses FFmpeg to publish MP4 files to MediaMTX.
- Check if FFmpeg is installed:
  ```cmd
  ffmpeg -version
  ```
- If not installed, install it via Windows Package Manager:
  ```cmd
  winget install Gyan.FFmpeg
  ```
  Or place `ffmpeg.exe` directly into `rtsp_simulator/` or in your system `PATH`.

---

## 4. How to Place Videos

Place your prerecorded CCTV MP4 videos into `rtsp_simulator/videos/`:

```
rtsp_simulator/
├── videos/
│   ├── camera1.mp4   <-- Entrance (Normal movement)
│   ├── camera2.mp4   <-- Parking (Weapon footage)
│   ├── camera3.mp4   <-- Building (Fire/Smoke footage)
│   ├── camera4.mp4   <-- Hall (Violence/Fight footage)
│   └── camera5.mp4   <-- Gate (Normal crowd footage)
```

### Quick Synthetic Video Generation
If you don't have custom footage yet, run:
```cmd
python -m src.generate_test_videos
```
or double-click `scripts\generate_videos.bat`. This automatically generates 5 high-definition 720p CCTV test videos with timestamps and simulated scene activity.

---

## 5. How to Configure Cameras

Open `rtsp_simulator/config.yaml`:

```yaml
server:
  host: 0.0.0.0
  port: 8554
  advertise_host: auto   # Automatically detects LAN IPv4; or specify e.g. 192.168.1.50
  transport: tcp

tools:
  mediamtx_path: mediamtx/mediamtx.exe
  ffmpeg_path: ffmpeg

publisher:
  video_codec: copy      # 'copy' (fastest, zero CPU) or 'libx264' (re-encode)
  preset: veryfast
  crf: 23
  log_level: warning

cameras:
  - id: camera_1
    name: Entrance Camera
    source: videos/camera1.mp4
    stream_path: camera1
    enabled: true

  - id: camera_2
    name: Parking Camera
    source: videos/camera2.mp4
    stream_path: camera2
    enabled: true

  - id: camera_3
    name: Building Camera
    source: videos/camera3.mp4
    stream_path: camera3
    enabled: true

  - id: camera_4
    name: Hall Camera
    source: videos/camera4.mp4
    stream_path: camera4
    enabled: true

  - id: camera_5
    name: Gate Camera
    source: videos/camera5.mp4
    stream_path: camera5
    enabled: true
```

---

## 6. How to Start the RTSP Server

To start only the MediaMTX routing server:
```cmd
cd rtsp_simulator
scripts\start_server.bat
```
or:
```cmd
python -m src.main server
```

---

## 7. How to Start the Five Streams

To start the server and all 5 camera publishers together:
```cmd
cd rtsp_simulator
start_rtsp_simulator.bat
```
or:
```cmd
python -m src.main start
```

You will see:
```text
KAVACH RTSP SIMULATOR
=====================
Server: 192.168.1.50
Port: 8554 (RTSP over TCP)

Streams:
  Entrance Camera [camera_1] -> rtsp://192.168.1.50:8554/camera1
  Parking Camera [camera_2]  -> rtsp://192.168.1.50:8554/camera2
  Building Camera [camera_3] -> rtsp://192.168.1.50:8554/camera3
  Hall Camera [camera_4]     -> rtsp://192.168.1.50:8554/camera4
  Gate Camera [camera_5]     -> rtsp://192.168.1.50:8554/camera5
```

The streams loop continuously. When a video reaches the end, FFmpeg restarts it automatically from frame 1 (`-stream_loop -1`).

---

## 8. How to Find the Simulator Laptop IP

On the Simulator Laptop:
1. Open PowerShell or Command Prompt.
2. Run:
   ```cmd
   ipconfig
   ```
3. Locate your active Wi-Fi or Ethernet adapter:
   ```text
   Wireless LAN adapter Wi-Fi:
      IPv4 Address. . . . . . . . . . . : 192.168.1.50
   ```
4. Note this address (e.g. `192.168.1.50`).

---

## 9. How to Configure KAVACH

On the KAVACH Laptop:
1. Open the KAVACH Dashboard in your browser (`http://localhost:5173` or your frontend port).
2. Navigate to **Cameras** -> Click **Add Camera**.
3. Fill in the details:
   - **Camera Name**: Entrance Camera
   - **Camera Type**: RTSP Stream
   - **Source URL**: `rtsp://192.168.1.50:8554/camera1`
   - **Target FPS**: 25 or 30
   - **AI Model Toggles**: Select desired models (Weapon, Fire, Violence)
4. Click **Add Camera**. Repeat for cameras 2 through 5:
   - `rtsp://192.168.1.50:8554/camera2` (Parking — Weapon)
   - `rtsp://192.168.1.50:8554/camera3` (Building — Fire)
   - `rtsp://192.168.1.50:8554/camera4` (Hall — Violence)
   - `rtsp://192.168.1.50:8554/camera5` (Gate — Normal crowd)

---

## 10. Windows Firewall Requirements

On the Simulator Laptop, Windows Firewall must allow inbound TCP connections on port **8554**.

### Automatic Configuration
Right-click `rtsp_simulator\scripts\allow_firewall.bat` and select **Run as administrator**.

### Manual Command (PowerShell as Administrator)
```powershell
New-NetFirewallRule -DisplayName "KAVACH_RTSP_8554" -Direction Inbound -LocalPort 8554 -Protocol TCP -Action Allow
```
Or via CMD:
```cmd
netsh advfirewall firewall add rule name="KAVACH_RTSP_8554" dir=in action=allow protocol=TCP localport=8554
```

---

## 11. How to Test Connectivity

You can test connectivity from either the simulator laptop or the KAVACH laptop:

### From the Simulator Laptop
```cmd
python -m src.main health
```
Expected output:
```text
RTSP server 192.168.1.50:8554: CONNECTED - TCP connection established
camera1: CONNECTED - RTSP video frame received
camera2: CONNECTED - RTSP video frame received
camera3: CONNECTED - RTSP video frame received
camera4: CONNECTED - RTSP video frame received
camera5: CONNECTED - RTSP video frame received
```

### From the KAVACH Laptop (Testing Remote Simulator)
```cmd
python -m src.main health --host 192.168.1.50
```
or double-click `rtsp_simulator\scripts\test_network.bat` and enter the simulator IP.

---

## 12. How to Stop Streams

- In the console window running `start_rtsp_simulator.bat`, simply press **Ctrl+C**.
- The simulator will cleanly terminate all FFmpeg publisher subprocesses and stop MediaMTX.

---

## 13. Troubleshooting

| Problem | Cause | Solution |
| :--- | :--- | :--- |
| `MediaMTX executable not found` | `mediamtx.exe` missing | Run `scripts\download_mediamtx.bat`. |
| `TCP connection failed: [WinError 10061]` | Server not running or blocked | Verify `start_rtsp_simulator.bat` is running; run `allow_firewall.bat`. |
| Camera shows `OFFLINE` in KAVACH | Stream disconnected or wrong IP | Check simulator console; run `python -m src.main health --host <IP>`. |
| High CPU usage on simulator | Re-encoding with libx264 | Ensure `publisher.video_codec: copy` in `config.yaml`. |
| KAVACH cannot decode stream | Unusual video container format | Change `publisher.video_codec: libx264` in `config.yaml` to standardize to H.264 yuv420p. |

---

## 14. How to Add a Sixth Camera

1. Add a video file: `rtsp_simulator/videos/camera6.mp4`.
2. Open `rtsp_simulator/config.yaml` and add an entry under `cameras:`:
   ```yaml
     - id: camera_6
       name: Rooftop Camera
       source: videos/camera6.mp4
       stream_path: camera6
       enabled: true
   ```
3. Restart the simulator:
   ```cmd
   start_rtsp_simulator.bat
   ```
4. In KAVACH, add Camera 6 with URL:
   `rtsp://<SIMULATOR_IP>:8554/camera6`
