"""
Statistics Frame Component
Displays monitoring statistics
"""
import tkinter as tk
from tkinter import ttk
from typing import Dict
from models import PingStats


class StatsFrame(ttk.Frame):
    def __init__(self, parent: tk.Widget, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.stats_labels: Dict[str, ttk.Label] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the statistics display"""
        # Configure styles
        style = ttk.Style()
        style.configure("Error.TLabel", foreground="red")
        style.configure("Success.TLabel", foreground="green")

        # Create labels for each statistic
        labels = [
            ("status", "Status:"),
            ("total", "Total pings:"),
            ("failed", "Failed:"),
            ("success_rate", "Success rate:"),
            ("uptime", "Uptime:"),
            ("last_failure", "Last failure:")
        ]

        for i, (key, text) in enumerate(labels):
            ttk.Label(self, text=text).grid(
                row=i, column=0, sticky='w', padx=5, pady=2)
            self.stats_labels[key] = ttk.Label(self, text="-")
            self.stats_labels[key].grid(
                row=i, column=1, sticky='w', padx=5, pady=2)

    def update_stats(self, stats: PingStats) -> None:
        """
        Update statistics display

        Args:
            stats: PingStats object containing current statistics
        """
        # Update status with appropriate style
        self.stats_labels["status"].configure(
            text=stats.current_status,
            style="Success.TLabel" if stats.current_status == "Running" else ""
        )

        # Update basic stats
        self.stats_labels["total"].configure(text=str(stats.total_pings))

        # Update failed stats with error style if needed
        self.stats_labels["failed"].configure(
            text=str(stats.failed_pings),
            style="Error.TLabel" if stats.failed_pings > 0 else ""
        )

        # Update success rate
        success_rate = ((stats.total_pings - stats.failed_pings) /
                        max(stats.total_pings, 1)) * 100
        self.stats_labels["success_rate"].configure(
            text=f"{success_rate:.1f}%"
        )

        # Update uptime
        self.stats_labels["uptime"].configure(text=stats.uptime)

        # Update last failure
        last_failure_text = (stats.last_failure.strftime('%Y-%m-%d %H:%M:%S')
                             if stats.last_failure else "-")
        self.stats_labels["last_failure"].configure(text=last_failure_text)
