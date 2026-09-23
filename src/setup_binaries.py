"""Utility to download and set up MediaMTX and verify FFmpeg on Windows."""

from __future__ import annotations

import io
import json
import os
from pathlib import Path
import shutil
import sys
import urllib.request
import zipfile

SIMULATOR_DIR = Path(__file__).resolve().parents[1]
MEDIAMTX_DIR = SIMULATOR_DIR / "mediamtx"
MEDIAMTX_EXE = MEDIAMTX_DIR / "mediamtx.exe"

GITHUB_API_URL = "https://api.github.com/repos/bluenviron/mediamtx/releases/latest"
FALLBACK_ZIP_URL = "https://github.com/bluenviron/mediamtx/releases/download/v1.21.1/mediamtx_v1.21.1_windows_amd64.zip"


def download_mediamtx(target_path: Path | None = None) -> Path:
    """Download the official Windows MediaMTX binary and extract mediamtx.exe."""
    dest = target_path or MEDIAMTX_EXE
    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.is_file():
        print(f"[MediaMTX] Found existing executable: {dest}")
        return dest

    print("[MediaMTX] Locating latest Windows release from GitHub...")
    download_url = None
    try:
        req = urllib.request.Request(GITHUB_API_URL, headers={"User-Agent": "KAVACH-RTSP-Setup"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            for asset in data.get("assets", []):
                name = asset.get("name", "")
                if "windows_amd64" in name and name.endswith(".zip"):
                    download_url = asset.get("browser_download_url")
                    break
    except Exception as exc:
        print(f"[MediaMTX] GitHub API lookup note: {exc}. Using fallback URL.")

    if not download_url:
        download_url = FALLBACK_ZIP_URL

    print(f"[MediaMTX] Downloading from: {download_url}")
    req = urllib.request.Request(download_url, headers={"User-Agent": "KAVACH-RTSP-Setup"})
    with urllib.request.urlopen(req, timeout=60) as response:
        content = response.read()

    print("[MediaMTX] Extracting mediamtx.exe...")
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        for member in archive.namelist():
            if Path(member).name.lower() == "mediamtx.exe":
                with archive.open(member) as source, open(dest, "wb") as target:
                    shutil.copyfileobj(source, target)
                break

    if not dest.is_file():
        raise RuntimeError("mediamtx.exe was not found in the downloaded archive.")

    print(f"[MediaMTX] Successfully installed to: {dest}")
    return dest


def check_ffmpeg() -> bool:
    """Check if FFmpeg is available on PATH or locally."""
    ffmpeg_in_path = shutil.which("ffmpeg") is not None
    local_ffmpeg = (SIMULATOR_DIR / "ffmpeg.exe").is_file()
    if ffmpeg_in_path:
        print("[FFmpeg] Found FFmpeg in system PATH.")
        return True
    if local_ffmpeg:
        print(f"[FFmpeg] Found local FFmpeg at: {SIMULATOR_DIR / 'ffmpeg.exe'}")
        return True
    print("[FFmpeg] WARNING: FFmpeg was not found in PATH or rtsp_simulator/ directory.")
    print("         To publish MP4 streams, install FFmpeg or place ffmpeg.exe in:")
    print(f"         {SIMULATOR_DIR / 'ffmpeg.exe'}")
    print("         You can install it via: winget install Gyan.FFmpeg")
    return False


def main() -> int:
    print("========================================")
    print("KAVACH RTSP Simulator — Binary Setup")
    print("========================================")
    try:
        download_mediamtx()
    except Exception as exc:
        print(f"ERROR: Failed to download MediaMTX: {exc}", file=sys.stderr)
        return 1

    check_ffmpeg()
    print("Setup check completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
