"""
Menu Builder Component
Creates and manages application menus
"""
import tkinter as tk
from typing import Callable, Dict, Optional


class MenuBuilder:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.menubar = tk.Menu(root)
        self.callbacks: Dict[str, Callable] = {}

    def add_file_menu(self,
                      save_callback: Optional[Callable] = None,
                      clear_callback: Optional[Callable] = None,
                      exit_callback: Optional[Callable] = None) -> None:
        """Add File menu to menubar"""
        file_menu = tk.Menu(self.menubar, tearoff=0)

        if save_callback:
            file_menu.add_command(label="Save Log...", command=save_callback)

        if clear_callback:
            file_menu.add_command(label="Clear Log", command=clear_callback)

        if save_callback or clear_callback:
            file_menu.add_separator()

        file_menu.add_command(
            label="Exit",
            command=exit_callback if exit_callback else self.root.quit
        )

        self.menubar.add_cascade(label="File", menu=file_menu)

    def add_edit_menu(self,
                      copy_callback: Optional[Callable] = None,
                      copy_all_callback: Optional[Callable] = None) -> None:
        """Add Edit menu to menubar"""
        edit_menu = tk.Menu(self.menubar, tearoff=0)

        if copy_callback:
            edit_menu.add_command(label="Copy Selected", command=copy_callback)

        if copy_all_callback:
            edit_menu.add_command(label="Copy All", command=copy_all_callback)

        self.menubar.add_cascade(label="Edit", menu=edit_menu)

    def add_help_menu(self, about_callback: Optional[Callable] = None) -> None:
        """Add Help menu to menubar"""
        help_menu = tk.Menu(self.menubar, tearoff=0)

        if about_callback:
            help_menu.add_command(label="About", command=about_callback)

        self.menubar.add_cascade(label="Help", menu=help_menu)

    def build(self) -> None:
        """Apply menubar to root window"""
        self.root.config(menu=self.menubar)
