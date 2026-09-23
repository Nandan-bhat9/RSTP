"""Network and RTSP reachability checks for the simulator presentation."""

from __future__ import annotations

from dataclasses import dataclass
import shutil
import socket
import subprocess
from typing import Iterable

from .config import CameraConfig, SimulatorConfig


@dataclass(frozen=True)
class CheckResult:
    label: str
    ok: bool
    detail: str


def tcp_check(host: str, port: int, timeout: float = 4.0) -> CheckResult:
    label = f"RTSP server {host}:{port}"
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return CheckResult(label, True, "TCP connection established")
    except OSError as exc:
        return CheckResult(label, False, f"TCP connection failed: {exc}")


def stream_check(url: str, ffmpeg_path: str, timeout: float = 12.0) -> CheckResult:
    """Ask FFmpeg or OpenCV to receive a short RTSP video frame sample over TCP."""
    label = url.rsplit("/", 1)[-1]
    has_ffmpeg = (shutil.which(ffmpeg_path) is not None) or __import__("pathlib").Path(ffmpeg_path).is_file()

    if has_ffmpeg:
        command = [
            ffmpeg_path, "-hide_banner", "-loglevel", "error", "-rtsp_transport", "tcp",
            "-i", url, "-map", "0:v:0", "-frames:v", "1", "-f", "null", "-",
        ]
        try:
            completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return CheckResult(label, False, f"Timed out after {timeout:.0f}s waiting for a video frame")
        if completed.returncode == 0:
            return CheckResult(label, True, "RTSP video frame received (via FFmpeg)")
        detail = (completed.stderr or completed.stdout or "FFmpeg exited without details").strip().splitlines()
        return CheckResult(label, False, detail[-1] if detail else "FFmpeg could not read stream")

    # Fallback to OpenCV if FFmpeg binary is absent (e.g. running check from KAVACH laptop)
    try:
        import os
        import cv2
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
        cap = cv2.VideoCapture(url)
        if not cap.isOpened():
            return CheckResult(label, False, "OpenCV could not connect to RTSP endpoint")
        ret, frame = cap.read()
        cap.release()
        if ret and frame is not None:
            return CheckResult(label, True, f"RTSP video frame received (via OpenCV: {frame.shape[1]}x{frame.shape[0]})")
        return CheckResult(label, False, "Connected but failed to decode video frame")
    except Exception as exc:
        return CheckResult(label, False, f"Stream probe error: {exc}")


def run_checks(config: SimulatorConfig, host: str | None = None) -> Iterable[CheckResult]:
    target_host = host or config.advertised_host()
    server = tcp_check(target_host, config.server.port)
    yield server
    if not server.ok:
        return
    for camera in config.enabled_cameras:
        yield stream_check(config.stream_url(camera, target_host), config.tools.ffmpeg_path)


def local_source_checks(config: SimulatorConfig) -> Iterable[CheckResult]:
    for camera in config.enabled_cameras:
        if camera.source.is_file():
            yield CheckResult(camera.id, True, f"Source present: {camera.source}")
        else:
            yield CheckResult(camera.id, False, f"Missing source: {camera.source}")
