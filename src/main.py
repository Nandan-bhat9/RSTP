"""Command-line entry point for the KAVACH RTSP CCTV simulator."""

from __future__ import annotations

import argparse
import signal
import sys
import time

from .config import ConfigError, load_config, validate_local_assets
from .health_check import local_source_checks, run_checks
from .stream_publisher import ProcessStartError, SimulatorProcesses


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="KAVACH RTSP CCTV simulator")
    parser.add_argument("--config", default=None, help="Path to simulator config.yaml")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate", help="Validate configuration and local video/binary prerequisites")
    subparsers.add_parser("server", help="Start only MediaMTX; stop with Ctrl+C")
    subparsers.add_parser("streams", help="Start configured publishers; MediaMTX must already be running")
    subparsers.add_parser("start", help="Start MediaMTX and all enabled cameras; stop with Ctrl+C")
    health = subparsers.add_parser("health", help="Test server TCP reachability and every RTSP stream")
    health.add_argument("--host", default=None, help="Simulator LAN host/IP to test")
    return parser


def _print_banner(config) -> None:
    host = config.advertised_host()
    print("\nKAVACH RTSP SIMULATOR\n=====================")
    print(f"Server: {host}")
    print(f"Port: {config.server.port} (RTSP over TCP)\n")
    print("Streams:")
    for camera in config.enabled_cameras:
        print(f"  {camera.name} [{camera.id}] -> {config.stream_url(camera, host)}")
    print()


def _run_managed(processes: SimulatorProcesses, start_server: bool, start_publishers: bool) -> int:
    if start_server:
        processes.start_server()
        time.sleep(1.0)
        if not processes.server or not processes.server.running:
            raise ProcessStartError("MediaMTX exited during startup; inspect its console output.")
    if start_publishers:
        processes.start_publishers()
    print("All requested processes have been started. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(2.0)
            if processes.server is not None and not processes.server.running:
                raise ProcessStartError(f"MediaMTX stopped (exit code {processes.server.exit_code}).")
            for camera_id in processes.restart_stopped_publishers():
                print(f"{camera_id}: publisher restarted after an unexpected exit")
    except KeyboardInterrupt:
        print("\nStopping simulator processes...")
        return 0
    finally:
        processes.stop_all()


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"CONFIGURATION ERROR: {exc}", file=sys.stderr)
        return 2

    if args.command == "validate":
        errors = validate_local_assets(config)
        for result in local_source_checks(config):
            status = "OK" if result.ok else "FAILED"
            print(f"{result.label}: {status} - {result.detail}")
        if errors:
            for error in errors:
                print(f"FAILED: {error}", file=sys.stderr)
            return 1
        print("Configuration and local assets are valid.")
        return 0

    if args.command == "health":
        any_failed = False
        for result in run_checks(config, args.host):
            status = "CONNECTED" if result.ok else "FAILED"
            print(f"{result.label}: {status} - {result.detail}")
            any_failed = any_failed or not result.ok
        return 1 if any_failed else 0

    _print_banner(config)
    processes = SimulatorProcesses(config)
    try:
        if args.command == "server":
            return _run_managed(processes, start_server=True, start_publishers=False)
        if args.command == "streams":
            return _run_managed(processes, start_server=False, start_publishers=True)
        return _run_managed(processes, start_server=True, start_publishers=True)
    except ProcessStartError as exc:
        print(f"STARTUP ERROR: {exc}", file=sys.stderr)
        processes.stop_all()
        return 1


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.default_int_handler)
    raise SystemExit(main())
