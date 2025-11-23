#!/usr/bin/env python3
"""
Pneumatik-Prüfstand Software
Main application entry point
"""
import sys
from PyQt5.QtWidgets import QApplication
from src.gui.main_window import TestStandMainWindow


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern cross-platform style

    # Create and show main window
    window = TestStandMainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
