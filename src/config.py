"""Configuration loading and validation for the RTSP simulator."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import socket
from typing import Any

import yaml


SIMULATOR_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = SIMULATOR_DIR / "config.yaml"


class ConfigError(ValueError):
    """Raised when simulator configuration is invalid."""


@dataclass(frozen=True)
class ServerConfig:
    host: str
    port: int
    advertise_host: str
    transport: str

    @property
    def listen_address(self) -> str:
        """MediaMTX listener syntax for the configured TCP RTSP endpoint."""
        return f":{self.port}" if self.host in {"", "0.0.0.0"} else f"{self.host}:{self.port}"


@dataclass(frozen=True)
class ToolsConfig:
    mediamtx_path: Path
    ffmpeg_path: str


@dataclass(frozen=True)
class PublisherConfig:
    video_codec: str
    preset: str
    crf: int
    log_level: str


@dataclass(frozen=True)
class CameraConfig:
    id: str
    name: str
    source: Path
    stream_path: str
    enabled: bool


@dataclass(frozen=True)
class SimulatorConfig:
    root: Path
    server: ServerConfig
    tools: ToolsConfig
    publisher: PublisherConfig
    cameras: tuple[CameraConfig, ...]

    @property
    def enabled_cameras(self) -> tuple[CameraConfig, ...]:
        return tuple(camera for camera in self.cameras if camera.enabled)

    def advertised_host(self) -> str:
        configured = self.server.advertise_host.strip()
        if configured and configured.lower() != "auto":
            return configured
        return discover_lan_ip()

    def stream_url(self, camera: CameraConfig, host: str | None = None) -> str:
        return f"rtsp://{host or self.advertised_host()}:{self.server.port}/{camera.stream_path}"


def discover_lan_ip() -> str:
    """Return a likely LAN IPv4 address without hard-coding one."""
    try:
        candidates = socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)
        for candidate in candidates:
            address = candidate[4][0]
            if not address.startswith("127."):
                return address
    except OSError:
        pass
    return "127.0.0.1"


def _as_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"'{label}' must be a YAML mapping.")
    return value


def _resolve_path(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (root / path).resolve()


def load_config(path: str | Path | None = None) -> SimulatorConfig:
    """Load, normalize, and validate a simulator YAML configuration."""
    config_path = Path(path).resolve() if path else DEFAULT_CONFIG_PATH
    if not config_path.is_file():
        raise ConfigError(f"Configuration file not found: {config_path}")

    try:
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in {config_path}: {exc}") from exc

    root = config_path.parent
    server_raw = _as_mapping(payload.get("server", {}), "server")
    tools_raw = _as_mapping(payload.get("tools", {}), "tools")
    publisher_raw = _as_mapping(payload.get("publisher", {}), "publisher")
    cameras_raw = payload.get("cameras")

    try:
        port = int(server_raw.get("port", 8554))
    except (TypeError, ValueError) as exc:
        raise ConfigError("server.port must be an integer.") from exc
    if not 1 <= port <= 65535:
        raise ConfigError("server.port must be between 1 and 65535.")

    transport = str(server_raw.get("transport", "tcp")).lower()
    if transport != "tcp":
        raise ConfigError("Only RTSP-over-TCP is supported by this LAN simulator configuration.")

    codec = str(publisher_raw.get("video_codec", "copy")).lower()
    if codec not in {"copy", "libx264"}:
        raise ConfigError("publisher.video_codec must be 'copy' or 'libx264'.")

    if not isinstance(cameras_raw, list) or not cameras_raw:
        raise ConfigError("'cameras' must contain at least one camera entry.")

    cameras: list[CameraConfig] = []
    ids: set[str] = set()
    paths: set[str] = set()
    for index, raw in enumerate(cameras_raw, start=1):
        item = _as_mapping(raw, f"cameras[{index}]")
        camera_id = str(item.get("id", "")).strip()
        name = str(item.get("name", "")).strip()
        source_value = str(item.get("source", "")).strip()
        stream_path = str(item.get("stream_path", "")).strip().strip("/")
        if not camera_id or not name or not source_value or not stream_path:
            raise ConfigError(f"cameras[{index}] requires id, name, source, and stream_path.")
        if any(ch in stream_path for ch in " ?#\\"):
            raise ConfigError(f"cameras[{index}].stream_path contains unsupported characters.")
        if camera_id in ids:
            raise ConfigError(f"Duplicate camera id: {camera_id}")
        if stream_path in paths:
            raise ConfigError(f"Duplicate stream path: {stream_path}")
        ids.add(camera_id)
        paths.add(stream_path)
        cameras.append(
            CameraConfig(
                id=camera_id,
                name=name,
                source=_resolve_path(root, source_value),
                stream_path=stream_path,
                enabled=bool(item.get("enabled", True)),
            )
        )

    mediamtx_value = str(tools_raw.get("mediamtx_path", "mediamtx/mediamtx.exe")).strip()
    if not mediamtx_value:
        raise ConfigError("tools.mediamtx_path cannot be blank.")
    raw_ffmpeg = str(tools_raw.get("ffmpeg_path", "ffmpeg")).strip() or "ffmpeg"
    ffmpeg_candidate = _resolve_path(root, raw_ffmpeg)
    if ffmpeg_candidate.is_file():
        ffmpeg_path = str(ffmpeg_candidate)
    elif (root / "ffmpeg.exe").is_file():
        ffmpeg_path = str(root / "ffmpeg.exe")
    elif (root / "mediamtx" / "ffmpeg.exe").is_file():
        ffmpeg_path = str(root / "mediamtx" / "ffmpeg.exe")
    else:
        ffmpeg_path = raw_ffmpeg

    return SimulatorConfig(
        root=root,
        server=ServerConfig(
            host=str(server_raw.get("host", "0.0.0.0")).strip() or "0.0.0.0",
            port=port,
            advertise_host=str(server_raw.get("advertise_host", "auto")).strip() or "auto",
            transport=transport,
        ),
        tools=ToolsConfig(
            mediamtx_path=_resolve_path(root, mediamtx_value),
            ffmpeg_path=ffmpeg_path,
        ),
        publisher=PublisherConfig(
            video_codec=codec,
            preset=str(publisher_raw.get("preset", "veryfast")).strip() or "veryfast",
            crf=int(publisher_raw.get("crf", 23)),
            log_level=str(publisher_raw.get("log_level", "warning")).strip() or "warning",
        ),
        cameras=tuple(cameras),
    )


def validate_local_assets(config: SimulatorConfig) -> list[str]:
    """Return human-readable local prerequisite errors without starting processes."""
    errors: list[str] = []
    if not config.tools.mediamtx_path.is_file():
        errors.append(f"MediaMTX executable not found: {config.tools.mediamtx_path}")
    for camera in config.enabled_cameras:
        if not camera.source.is_file():
            errors.append(f"{camera.id}: source video not found: {camera.source}")
    return errors
