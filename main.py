"""Application entry point for DiskVisionInspector."""

from __future__ import annotations

import sys
import argparse
import subprocess
import socket
import os
from pathlib import Path

from config.settings import API_HOST, API_PORT
from utils.logger import configure_logging

PROJECT_ROOT = Path(__file__).resolve().parent
WEB_DIR = PROJECT_ROOT / "web"
WEB_DIST = WEB_DIR / "dist" / "index.html"


def run_gui() -> int:
    """Start the desktop application."""
    from PySide6.QtWidgets import QApplication

    from gui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("DiskVisionInspector")
    window = MainWindow()
    window.show()
    return app.exec()


def run_web() -> int:
    """Start the LAN-accessible backend service."""
    import uvicorn

    from services.api import create_app

    _ensure_web_dashboard_built()
    app = create_app()
    port = _choose_port(API_HOST, API_PORT)
    if port != API_PORT:
        print(f"Port {API_PORT} is busy, starting web server on port {port} instead.")
    print(f"DiskVisionInspector web dashboard: http://{_display_host(API_HOST)}:{port}")
    uvicorn.run(app, host=API_HOST, port=port)
    return 0


def _ensure_web_dashboard_built() -> None:
    """Build the React dashboard when missing or stale.

    Set DISK_VISION_FORCE_WEB_BUILD=1 to always rebuild.
    Set DISK_VISION_SKIP_WEB_BUILD=1 to skip build checks.
    """
    if not WEB_DIR.exists():
        return
    if os.getenv("DISK_VISION_SKIP_WEB_BUILD", "0") == "1":
        return
    if os.getenv("DISK_VISION_FORCE_WEB_BUILD", "0") == "1":
        _build_web_dashboard()
        return
    if WEB_DIST.exists() and not _web_sources_newer_than_dist():
        return
    _build_web_dashboard()


def _build_web_dashboard() -> None:
    """Execute npm install/build for the dashboard."""
    npm_command = "npm.cmd" if sys.platform.startswith("win") else "npm"
    node_modules = WEB_DIR / "node_modules"
    if not node_modules.exists():
        subprocess.run([npm_command, "install"], cwd=WEB_DIR, check=True)
    subprocess.run([npm_command, "run", "build"], cwd=WEB_DIR, check=True)


def _web_sources_newer_than_dist() -> bool:
    """Return True when web source/config files changed after the built bundle."""
    if not WEB_DIST.exists():
        return True
    dist_mtime = WEB_DIST.stat().st_mtime
    watch_roots = [WEB_DIR / "src"]
    watch_files = [WEB_DIR / "index.html", WEB_DIR / "package.json", WEB_DIR / "tsconfig.json", WEB_DIR / "vite.config.ts"]

    for root in watch_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.stat().st_mtime > dist_mtime:
                return True

    for path in watch_files:
        if path.exists() and path.stat().st_mtime > dist_mtime:
            return True

    return False


def _choose_port(host: str, preferred_port: int, max_tries: int = 20) -> int:
    """Return the preferred port, or the next available one."""
    for port in range(preferred_port, preferred_port + max_tries):
        if _port_is_available(host, port):
            return port
    raise RuntimeError(f"No free port found in range {preferred_port}-{preferred_port + max_tries - 1}.")


def _port_is_available(host: str, port: int) -> bool:
    test_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((test_host, port))
        except OSError:
            return False
    return True


def _display_host(host: str) -> str:
    return "127.0.0.1" if host == "0.0.0.0" else host


def main() -> int:
    """Start DiskVisionInspector in GUI or headless mode."""
    configure_logging()
    parser = argparse.ArgumentParser(description="DiskVisionInspector runtime")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--gui", action="store_true", help="Start the PySide6 desktop GUI.")
    mode.add_argument("--web", action="store_true", help="Start the FastAPI backend and browser dashboard.")
    mode.add_argument("--headless", action="store_true", help="Start the browser dashboard without desktop GUI.")
    args = parser.parse_args()
    if args.headless or args.web:
        return run_web()
    return run_gui()


if __name__ == "__main__":
    raise SystemExit(main())
