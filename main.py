"""Application entry point for DiskVisionInspector."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow
from utils.logger import configure_logging


def main() -> int:
    """Start the desktop application."""
    configure_logging()
    app = QApplication(sys.argv)
    app.setApplicationName("DiskVisionInspector")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
