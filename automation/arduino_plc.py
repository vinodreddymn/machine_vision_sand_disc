"""
Arduino Nano PLC Controller

Communication Protocol
----------------------
PC -> Arduino

GOOD
REJECT
RUNNING
STOPPED
RESET
FAULT

Arduino -> PC

START
STOP
RESET
FAULT
"""

from __future__ import annotations

import logging
import time
from typing import Optional

import serial
from serial import SerialException

from automation.plc import (
    PLCController,
    PLCStatus,
    DeviceState,
    PLCMode,
)

logger = logging.getLogger(__name__)


class ArduinoNanoController(PLCController):

    def __init__(
        self,
        port: str = "COM4",
        baudrate: int = 115200,
        timeout: float = 0.1,
    ) -> None:

        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

        self.serial_conn: Optional[serial.Serial] = None

        self.status = PLCStatus(
            run_status=DeviceState.STOPPED,
            mode=PLCMode.MANUAL,
            plc_connected=False,
        )

        self._last_event: str | None = None

        self.connect()

    # --------------------------------------------------
    # Connection Management
    # --------------------------------------------------

    def connect(self) -> None:

        try:

            self.serial_conn = serial.Serial(
                self.port,
                self.baudrate,
                timeout=self.timeout,
            )

            time.sleep(2)

            self.status.plc_connected = True

            logger.info(
                "Arduino connected on %s",
                self.port,
            )

        except Exception as exc:

            logger.error(
                "Failed to connect Arduino: %s",
                exc,
            )

            self.status.plc_connected = False

    def disconnect(self) -> None:

        if self.serial_conn:

            try:
                self.serial_conn.close()
            except Exception:
                pass

        self.status.plc_connected = False

    # --------------------------------------------------
    # Internal Helpers
    # --------------------------------------------------

    def _send_command(self, command: str) -> None:

        if not self.serial_conn:
            return

        try:

            self.serial_conn.write(
                f"{command}\n".encode()
            )

        except SerialException:

            logger.exception(
                "Arduino communication error"
            )

            self.status.plc_connected = False

    # --------------------------------------------------
    # PLC Actions
    # --------------------------------------------------

    def reject_part(
        self,
        station_name: str,
    ) -> None:

        logger.info(
            "Reject part requested by %s",
            station_name,
        )

        self._send_command("REJECT")

    def release_to_flipper(self) -> None:

        self.release_to_good_bin()

    def release_to_good_bin(self) -> None:

        self._send_command("GOOD")

    def start_request(self) -> None:

        self._send_command("RUNNING")

        self.status.run_status = (
            DeviceState.RUNNING
        )

        self.status.inspection_running = True

    def stop_request(self) -> None:

        self._send_command("STOPPED")

        self.status.run_status = (
            DeviceState.STOPPED
        )

        self.status.inspection_running = False

    def reset_request(self) -> None:

        self._send_command("RESET")

        self.status.run_status = (
            DeviceState.READY
        )

    # --------------------------------------------------
    # Event Handling
    # --------------------------------------------------

    def _read_serial_events(self) -> None:

        if not self.serial_conn:
            return

        try:

            while self.serial_conn.in_waiting:

                msg = (
                    self.serial_conn.readline()
                    .decode(errors="ignore")
                    .strip()
                )

                if not msg:
                    continue

                self._last_event = msg

                logger.debug(
                    "Arduino Event: %s",
                    msg,
                )

                if msg == "START":

                    self.status.run_status = (
                        DeviceState.RUNNING
                    )

                elif msg == "STOP":

                    self.status.run_status = (
                        DeviceState.STOPPED
                    )

                elif msg == "FAULT":

                    self.status.fault_active = True

        except Exception:

            logger.exception(
                "Error reading Arduino serial data"
            )

            self.status.plc_connected = False

    # --------------------------------------------------
    # PLC Status
    # --------------------------------------------------

    def read_status(self) -> PLCStatus:

        self._read_serial_events()

        self.status.last_heartbeat_at = time.time()

        return self.status

    # --------------------------------------------------
    # External Event Access
    # --------------------------------------------------

    def get_event(self) -> str | None:

        self._read_serial_events()

        event = self._last_event

        self._last_event = None

        return event

    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------

    def __del__(self) -> None:

        try:
            self.disconnect()
        except Exception:
            pass