"""Generate 5 synthetic CCTV MP4 video feeds for the simulation demo.

These videos allow testing all 5 RTSP streams end-to-end immediately without
requiring external footage downloads.
"""

from __future__ import annotations

import math
from pathlib import Path
import cv2
import numpy as np

SIMULATOR_DIR = Path(__file__).resolve().parents[1]
VIDEOS_DIR = SIMULATOR_DIR / "videos"

CAMERAS_META = [
    {
        "filename": "camera1.mp4",
        "title": "CAM 01 - MAIN ENTRANCE",
        "subtitle": "NORMAL CCTV FOOTAGE",
        "bg_color": (32, 38, 46),
        "accent": (80, 180, 100),
        "mode": "entrance",
    },
    {
        "filename": "camera2.mp4",
        "title": "CAM 02 - PARKING SECTOR B",
        "subtitle": "WEAPON THREAT SIMULATION",
        "bg_color": (30, 30, 48),
        "accent": (70, 70, 220),
        "mode": "weapon",
    },
    {
        "filename": "camera3.mp4",
        "title": "CAM 03 - BUILDING NORTH WING",
        "subtitle": "FIRE / SMOKE SIMULATION",
        "bg_color": (28, 36, 42),
        "accent": (40, 120, 230),
        "mode": "fire",
    },
    {
        "filename": "camera4.mp4",
        "title": "CAM 04 - RECEPTION HALL",
        "subtitle": "VIOLENCE / FIGHT SIMULATION",
        "bg_color": (36, 28, 38),
        "accent": (140, 60, 210),
        "mode": "fight",
    },
    {
        "filename": "camera5.mp4",
        "title": "CAM 05 - PERIMETER GATE 3",
        "subtitle": "CROWD / PATROL FOOTAGE",
        "bg_color": (34, 38, 34),
        "accent": (120, 190, 80),
        "mode": "crowd",
    },
]


def create_cctv_frame(
    width: int,
    height: int,
    frame_idx: int,
    total_frames: int,
    meta: dict,
) -> np.ndarray:
    """Render a realistic CCTV-styled frame with timestamps, telemetry, and motion."""
    frame = np.full((height, width, 3), meta["bg_color"], dtype=np.uint8)

    # Subtle grid lines simulating tiles/floor
    for y in range(120, height - 60, 70):
        cv2.line(frame, (40, y), (width - 40, y), (45, 52, 60), 1)
    for x in range(80, width - 40, 120):
        cv2.line(frame, (x, 120), (x, height - 60), (45, 52, 60), 1)

    t = (frame_idx / total_frames) * 2 * math.pi
    mode = meta["mode"]

    if mode == "entrance":
        # Smooth horizontal patrol motion
        cx = int(width / 2 + math.sin(t) * (width * 0.3))
        cy = int(height * 0.55 + math.cos(t * 2) * 20)
        cv2.circle(frame, (cx, cy), 32, meta["accent"], -1)
        cv2.circle(frame, (cx, cy), 36, (200, 220, 200), 2)
        cv2.putText(frame, "PATROL-01", (cx - 38, cy + 50), cv2.FONT_HERSHEY_PLAIN, 1.1, (200, 220, 200), 1)

    elif mode == "weapon":
        # Target area with simulated moving focal entity
        cx = int(width * 0.45 + math.cos(t) * 120)
        cy = int(height * 0.58 + math.sin(t) * 30)
        cv2.rectangle(frame, (cx - 30, cy - 60), (cx + 30, cy + 60), meta["accent"], -1)
        cv2.circle(frame, (cx, cy - 80), 20, meta["accent"], -1)
        # Simulated held object
        cv2.line(frame, (cx + 25, cy - 20), (cx + 70, cy - 20), (0, 0, 240), 4)
        cv2.putText(frame, "SIMULATED THREAT", (cx - 60, cy + 85), cv2.FONT_HERSHEY_PLAIN, 1.1, (100, 100, 255), 1)

    elif mode == "fire":
        # Expanding thermal / smoke plume
        center_x, center_y = int(width * 0.52), int(height * 0.65)
        for i in range(5):
            radius = int(25 + i * 14 + math.sin(t * 3 + i) * 8)
            offset_y = -int(i * 26 + math.cos(t * 2 + i) * 6)
            alpha = max(0.2, 1.0 - (i * 0.18))
            color = (
                int(20 + 30 * i),
                int(60 + 35 * i * alpha),
                int(230 - 30 * i),
            )
            cv2.circle(frame, (center_x + int(math.sin(t + i) * 15), center_y + offset_y), radius, color, -1)
        cv2.putText(frame, "THERMAL ANOMALY", (center_x - 70, center_y + 40), cv2.FONT_HERSHEY_PLAIN, 1.1, (50, 150, 255), 1)

    elif mode == "fight":
        # Rapid, oscillating interactions between two entities
        cx1 = int(width * 0.46 + math.sin(t * 4) * 55)
        cx2 = int(width * 0.54 - math.sin(t * 4) * 55)
        cy = int(height * 0.55 + math.cos(t * 6) * 15)
        cv2.circle(frame, (cx1, cy), 28, (60, 60, 200), -1)
        cv2.circle(frame, (cx2, cy), 28, (200, 120, 60), -1)
        cv2.line(frame, (cx1, cy), (cx2, cy), (180, 80, 220), 3)
        cv2.putText(frame, "HIGH AGITATION", (int(width * 0.43), cy + 60), cv2.FONT_HERSHEY_PLAIN, 1.1, (180, 80, 220), 1)

    elif mode == "crowd":
        # Multiple walking dots
        for i in range(6):
            phase = t + (i * math.pi / 3)
            px = int((width * 0.25) + ((i * 120 + math.sin(phase) * 80) % (width * 0.5)))
            py = int((height * 0.45) + ((i * 35 + math.cos(phase) * 30) % (height * 0.3)))
            cv2.circle(frame, (px, py), 16, meta["accent"], -1)
        cv2.putText(frame, "CROWD FLOW", (int(width * 0.45), int(height * 0.85)), cv2.FONT_HERSHEY_PLAIN, 1.1, (180, 220, 150), 1)

    # CCTV HUD Overlays
    # Top bar
    cv2.rectangle(frame, (0, 0), (width, 42), (18, 22, 26), -1)
    cv2.putText(frame, "KAVACH SURVEILLANCE NETWORK", (20, 27), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (230, 230, 230), 2)
    cv2.putText(frame, "REC [LIVE]", (width - 130, 27), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (50, 220, 80), 2)
    cv2.circle(frame, (width - 145, 22), 6, (50, 220, 80), -1)

    # Sub-header
    cv2.putText(frame, meta["title"], (30, 80), cv2.FONT_HERSHEY_DUPLEX, 0.75, (255, 255, 255), 1)
    cv2.putText(frame, meta["subtitle"], (30, 105), cv2.FONT_HERSHEY_PLAIN, 1.0, meta["accent"], 1)

    # Bottom bar
    sec = (frame_idx // 25) % 60
    msec = int(((frame_idx % 25) / 25) * 1000)
    timestamp_str = f"2026-09-24 14:30:{sec:02d}.{msec:03d} UTC+05:30"
    cv2.rectangle(frame, (0, height - 34), (width, height), (18, 22, 26), -1)
    cv2.putText(frame, timestamp_str, (20, height - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (180, 190, 200), 1)
    fps_badge = "25.0 FPS | 720p | RTSP STREAM"
    cv2.putText(frame, fps_badge, (width - 290, height - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (160, 170, 180), 1)

    return frame


def generate_all(output_dir: Path | None = None, frames: int = 125, fps: int = 25) -> list[Path]:
    """Generate all 5 synthetic MP4 CCTV test clips."""
    dest_dir = output_dir or VIDEOS_DIR
    dest_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    width, height = 1280, 720
    # Try common cross-platform mp4 codecs
    fourcc_options = [
        ("avc1", ".mp4"),
        ("mp4v", ".mp4"),
        ("MJPG", ".avi"),
    ]

    for meta in CAMERAS_META:
        target_path = dest_dir / meta["filename"]
        print(f"[Generate] Rendering {meta['title']} -> {target_path.name} ({frames} frames)...")

        writer = None
        used_codec = None
        for codec_str, _ in fourcc_options:
            fourcc = cv2.VideoWriter_fourcc(*codec_str)
            test_writer = cv2.VideoWriter(str(target_path), fourcc, fps, (width, height))
            if test_writer.isOpened():
                writer = test_writer
                used_codec = codec_str
                break

        if writer is None or not writer.isOpened():
            raise RuntimeError(f"Could not open VideoWriter for {target_path} with supported codecs.")

        for i in range(frames):
            frame = create_cctv_frame(width, height, i, frames, meta)
            writer.write(frame)

        writer.release()
        size_kb = target_path.stat().st_size / 1024
        print(f"           Done ({used_codec}, {size_kb:.1f} KB)")
        generated.append(target_path)

    print(f"\nAll {len(generated)} simulation test videos generated in: {dest_dir}")
    return generated


if __name__ == "__main__":
    generate_all()
