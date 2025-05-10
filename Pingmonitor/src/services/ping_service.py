"""
Ping Service Module
Handles ping operations and monitoring functionality
"""
import subprocess
import threading
from datetime import datetime
from typing import Optional, Callable
import logging

from models import PingStats
from utils.validators import is_valid_host


class PingService:
    def __init__(self):
        self.stop_event = threading.Event()
        self.stop_event.set()  # Initially stopped
        self.monitoring_thread: Optional[threading.Thread] = None
        self.stats = PingStats()
        self.logger = logging.getLogger('PingMonitor')

        # Callbacks
        self.on_status_change: Optional[Callable[[bool], None]] = None
        self.on_stats_update: Optional[Callable[[], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None

    def start_monitoring(self, host: str, interval: int) -> bool:
        """
        Start monitoring a host

        Args:
            host: Host to monitor
            interval: Ping interval in seconds

        Returns:
            bool: True if monitoring started successfully
        """
        # Validate parameters
        valid, error_msg = is_valid_host(host)
        if not valid:
            self.logger.error(f"Invalid host: {error_msg}")
            if self.on_error:
                self.on_error(f"Invalid host: {error_msg}")
            return False

        if interval < 1:
            self.logger.error("Interval must be at least 1 second")
            if self.on_error:
                self.on_error("Interval must be at least 1 second")
            return False

        # Check if already running
        if not self.stop_event.is_set() or (self.monitoring_thread and self.monitoring_thread.is_alive()):
            self.logger.error("Monitoring is already running")
            if self.on_error:
                self.on_error("Monitoring is already running")
            return False

        # Initialize monitoring
        self.stop_event.clear()
        self.stats.reset()
        self.stats.start_time = datetime.now()
        self.stats.current_status = "Running"

        # Start monitoring thread
        self.monitoring_thread = threading.Thread(
            target=self._monitor_loop,
            args=(host, interval),
            daemon=True
        )
        self.monitoring_thread.start()

        self.logger.info(
            f"Monitoring started for host {host} (interval {interval} sec)")
        return True

    def stop_monitoring(self) -> None:
        """Stop monitoring"""
        self.stop_event.set()
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=2.0)
            if self.monitoring_thread.is_alive():
                self.logger.warning(
                    "Failed to stop monitoring thread properly")

        self.stats.current_status = "Stopped"
        if self.on_stats_update:
            self.on_stats_update()

    def _monitor_loop(self, host: str, interval: int) -> None:
        """
        Main monitoring loop

        Args:
            host: Host to monitor
            interval: Ping interval in seconds
        """
        failed_attempts = 0

        while not self.stop_event.is_set():
            self.stats.total_pings += 1
            is_successful = self._ping_host(host)

            if not is_successful:
                failed_attempts += 1
                self.stats.failed_pings += 1
                self.stats.last_failure = datetime.now()

                self.logger.error(
                    f"Host {host} is unreachable (attempt {failed_attempts})")
                if self.on_status_change:
                    self.on_status_change(False)
            else:
                if failed_attempts > 0:
                    self.logger.info(f"Connection to {host} restored")
                    if self.on_status_change:
                        self.on_status_change(True)
                failed_attempts = 0

            if self.on_stats_update:
                self.on_stats_update()

            self.stop_event.wait(interval)

        self.logger.info("Monitoring stopped")

    def _ping_host(self, host: str) -> bool:
        """
        Execute ping command safely

        Args:
            host: Host to ping

        Returns:
            bool: True if ping was successful
        """
        try:
            command = ['ping', '-n', '1', '-w', '1000', host]

            # Hide console window on Windows
            startupinfo = None
            if hasattr(subprocess, 'STARTUPINFO'):
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            result = subprocess.run(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                startupinfo=startupinfo,
                timeout=5
            )
            return result.returncode == 0

        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            self.logger.error(f"Ping error: {str(e)}")
            return False
