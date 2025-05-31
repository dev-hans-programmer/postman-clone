#!/usr/bin/env python3
"""
API Testing Application - Main Entry Point
A comprehensive REST API testing tool built with CustomTkinter
"""

import customtkinter as ctk
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ui.main_window import MainWindow
from config.settings import AppSettings

def main():
    """Main application entry point"""
    try:
        # Initialize CustomTkinter appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Load application settings
        settings = AppSettings()
        
        # Create and run the main application
        app = MainWindow(settings)
        app.run()
        
    except Exception as e:
        print(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
