"""
Main Application Class
Initializes and manages the application components
"""
import os
import sys
import tkinter as tk
from typing import Optional

from utils import Config, LoggerSetup
from ui import MainWindow


class PingMonitorApp:
    def __init__(self):
        self.config: Optional[Config] = None
        self.root: Optional[tk.Tk] = None
        self.main_window: Optional[MainWindow] = None

    def initialize(self) -> bool:
        """
        Initialize application components

        Returns:
            bool: True if initialization was successful
        """
        # Check platform
        if os.name != 'nt':
            print("Error: This application is designed for Windows only.")
            return False

        # Initialize configuration
        try:
            self.config = Config()
        except Exception as e:
            print(f"Error initializing configuration: {e}")
            return False

        # Initialize logging
        try:
            logger_setup = LoggerSetup()
            logger_setup.setup()
        except Exception as e:
            print(f"Error setting up logging: {e}")
            return False

        # Initialize main window
        try:
            self.root = tk.Tk()
            self.main_window = MainWindow(self.root)
        except Exception as e:
            print(f"Error creating main window: {e}")
            return False

        return True

    def run(self) -> None:
        """Run the application"""
        if self.root:
            try:
                self.root.mainloop()
            except Exception as e:
                print(f"Error in main loop: {e}")
            finally:
                self.cleanup()

    def cleanup(self) -> None:
        """Cleanup resources"""
        if self.main_window:
            try:
                self.main_window.on_closing()
            except Exception:
                pass

    @staticmethod
    def setup_exception_handler():
        """Setup global exception handler"""
        def handle_exception(exc_type, exc_value, exc_traceback):
            """Handle uncaught exceptions"""
            import traceback
            print("Uncaught exception:")
            traceback.print_exception(exc_type, exc_value, exc_traceback)

            if tk._default_root:
                tk.messagebox.showerror(
                    "Error",
                    "An unexpected error occurred. Please check the logs."
                )

        sys.excepthook = handle_exception
