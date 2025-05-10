"""
Log Frame Component
Handles the display and management of log messages
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime
from typing import Optional


class LogFrame(ttk.Frame):
    def __init__(self, parent: tk.Widget, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.max_lines = 1000
        self._setup_ui()
        self._create_context_menu()

    def _setup_ui(self) -> None:
        """Setup the log text widget"""
        self.log_text = scrolledtext.ScrolledText(
            self,
            width=60,
            height=15,
            font=("Consolas", 10),
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Configure tags for different message types
        self.log_text.tag_configure("error", foreground="red")
        self.log_text.tag_configure("success", foreground="green")
        self.log_text.tag_configure("info", foreground="blue")

    def _create_context_menu(self) -> None:
        """Create right-click context menu"""
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(
            label="Copy", command=self.copy_selection)
        self.context_menu.add_command(label="Copy All", command=self.copy_all)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Clear", command=self.clear)

        self.log_text.bind("<Button-3>", self._show_context_menu)

    def _show_context_menu(self, event: tk.Event) -> None:
        """Show context menu on right click"""
        self.context_menu.post(event.x_root, event.y_root)

    def add_message(self, message: str, level: str = "info") -> None:
        """
        Add a message to the log

        Args:
            message: Message to add
            level: Message level (info, error, success)
        """
        self.log_text.configure(state='normal')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}\n"

        self.log_text.insert(tk.END, log_message, level)

        # Limit log size
        lines = self.log_text.get('1.0', tk.END).splitlines()
        if len(lines) > self.max_lines:
            self.log_text.delete('1.0', f"{len(lines) - self.max_lines}.0")

        self.log_text.see(tk.END)
        self.log_text.configure(state='disabled')

    def copy_selection(self) -> None:
        """Copy selected text to clipboard"""
        try:
            selected_text = self.log_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.clipboard_clear()
            self.clipboard_append(selected_text)
        except tk.TclError:
            pass  # Nothing selected

    def copy_all(self) -> None:
        """Copy all text to clipboard"""
        text = self.log_text.get(1.0, tk.END)
        self.clipboard_clear()
        self.clipboard_append(text)

    def clear(self) -> None:
        """Clear all text from log"""
        self.log_text.configure(state='normal')
        self.log_text.delete('1.0', tk.END)
        self.log_text.configure(state='disabled')

    def save_to_file(self, filename: str) -> bool:
        """
        Save log contents to file

        Args:
            filename: Path to save file

        Returns:
            bool: True if save was successful
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.log_text.get('1.0', tk.END))
            return True
        except Exception:
            return False
