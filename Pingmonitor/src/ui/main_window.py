"""
Main Window Component
Main application window that combines all UI components
"""
import tkinter as tk
from tkinter import ttk, messagebox
import os
from datetime import datetime
from typing import Optional

from services import PingService
from .stats_frame import StatsFrame
from .log_frame import LogFrame
from .menu import MenuBuilder
from utils.validators import is_valid_host


class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Ping Monitor")
        self.root.geometry("520x480")
        self.root.resizable(False, False)
        self.root.configure(bg="#f0f4f7")

        # Initialize service
        self.ping_service = PingService()
        self.setup_service_callbacks()

        # Setup UI components
        self.setup_ui()
        self.setup_menu()

        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_service_callbacks(self) -> None:
        """Setup callbacks for the ping service"""
        self.ping_service.on_status_change = self.on_status_change
        self.ping_service.on_stats_update = self.on_stats_update
        self.ping_service.on_error = self.on_error

    def setup_ui(self) -> None:
        """Setup the main UI components"""
        # Input frame
        self.setup_input_frame()

        # Statistics frame
        self.stats_frame = StatsFrame(self.root)
        self.stats_frame.pack(fill=tk.X, padx=5)

        # Log frame
        self.log_frame = LogFrame(self.root)
        self.log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def setup_input_frame(self) -> None:
        """Setup the input controls frame"""
        input_frame = ttk.Frame(self.root, padding="5")
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        # Host input
        ttk.Label(input_frame, text="Host:").grid(
            row=0, column=0, padx=5, pady=5)
        self.host_entry = ttk.Entry(input_frame, width=30)
        self.host_entry.grid(row=0, column=1, padx=5, pady=5)
        self.host_entry.insert(0, "8.8.8.8")

        # Interval input
        ttk.Label(input_frame, text="Interval (sec):").grid(
            row=0, column=2, padx=5, pady=5)
        self.interval_entry = ttk.Entry(input_frame, width=7)
        self.interval_entry.grid(row=0, column=3, padx=5, pady=5)
        self.interval_entry.insert(0, "2")

        # Start/Stop button
        self.start_button = ttk.Button(
            input_frame,
            text="Start",
            command=self.toggle_monitoring
        )
        self.start_button.grid(row=0, column=4, padx=5, pady=5)

    def setup_menu(self) -> None:
        """Setup the application menu"""
        menu_builder = MenuBuilder(self.root)

        menu_builder.add_file_menu(
            save_callback=self.save_log,
            clear_callback=self.clear_log,
            exit_callback=self.on_closing
        )

        menu_builder.add_edit_menu(
            copy_callback=self.log_frame.copy_selection,
            copy_all_callback=self.log_frame.copy_all
        )

        menu_builder.add_help_menu(
            about_callback=self.show_about
        )

        menu_builder.build()

    def toggle_monitoring(self) -> None:
        """Toggle monitoring state"""
        if self.ping_service.stop_event.is_set():  # If stopped
            self.start_monitoring()
        else:  # If running
            self.stop_monitoring()

    def start_monitoring(self) -> None:
        """Start monitoring"""
        host = self.host_entry.get().strip()
        try:
            interval = max(1, int(self.interval_entry.get()))
        except ValueError:
            self.on_error("Interval must be a positive integer")
            return

        if self.ping_service.start_monitoring(host, interval):
            self.start_button.configure(text="Stop")
            self.host_entry.configure(state='disabled')
            self.interval_entry.configure(state='disabled')
            self.log_frame.add_message(
                f"Started monitoring {host} (interval: {interval}s)",
                "info"
            )

    def stop_monitoring(self) -> None:
        """Stop monitoring"""
        self.ping_service.stop_monitoring()
        self.start_button.configure(text="Start")
        self.host_entry.configure(state='normal')
        self.interval_entry.configure(state='normal')
        self.log_frame.add_message("Monitoring stopped", "info")

    def on_status_change(self, is_up: bool) -> None:
        """Handle status change events"""
        if not is_up:
            self.play_alert()

    def on_stats_update(self) -> None:
        """Handle statistics update events"""
        self.stats_frame.update_stats(self.ping_service.stats)

    def on_error(self, message: str) -> None:
        """Handle error events"""
        messagebox.showerror("Error", message)
        self.log_frame.add_message(message, "error")

    def play_alert(self) -> None:
        """Play alert sound"""
        if os.name == 'nt':  # Windows only
            try:
                import winsound
                winsound.PlaySound(
                    'SystemHand',
                    winsound.SND_ASYNC | winsound.SND_ALIAS
                )
            except Exception:
                pass

    def save_log(self) -> None:
        """Save log to file"""
        filename = f"ping_monitor_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        if self.log_frame.save_to_file(filename):
            messagebox.showinfo("Success", f"Log saved to: {filename}")
        else:
            messagebox.showerror("Error", "Failed to save log")

    def clear_log(self) -> None:
        """Clear log contents"""
        if messagebox.askyesno("Confirm", "Clear all log entries?"):
            self.log_frame.clear()

    def show_about(self) -> None:
        """Show about dialog"""
        messagebox.showinfo(
            "About Ping Monitor",
            "Ping Monitor v1.1\n\n"
            "A simple tool for monitoring host availability\n"
            "Author: Artur A."
        )

    def on_closing(self) -> None:
        """Handle application closing"""
        if not self.ping_service.stop_event.is_set():
            if messagebox.askyesno("Confirm", "Stop monitoring and exit?"):
                self.stop_monitoring()
                self.root.quit()
        else:
            self.root.quit()
