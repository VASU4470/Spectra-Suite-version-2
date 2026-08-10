import sys
import os
import subprocess
import ctypes
import multiprocessing # <-- Added to safely launch Tkinter from PySide6
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, 
                               QGridLayout, QPushButton, QLabel, QMessageBox)
from PySide6.QtCore import Qt, QTimer
import ir
import xrd

# --- ADDED HELPER FUNCTION ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
# -----------------------------

class WelcomeDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analytical Spectroscopy Suite")
        self.resize(700, 500)
        self.open_windows = {} # Will now store running processes, not window objects
        
        self.setStyleSheet("""
            QWidget { background-color: #1e1e2e; color: #cdd6f4; }
            QLabel#Title { font-size: 26px; font-weight: bold; color: #89b4fa; }
            QLabel#Subtitle { font-size: 14px; color: #a6adc8; }
            QPushButton { background-color: #313244; border: 2px solid #45475a; border-radius: 15px; font-size: 16px; font-weight: bold; padding: 15px; }
            QPushButton:hover { background-color: #45475a; border: 2px solid #89b4fa; }
            QPushButton:pressed { background-color: #585b70; }
        """)
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        title = QLabel("Analytical Spectroscopy Suite")
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Select a workspace to begin")
        subtitle.setObjectName("Subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        grid = QGridLayout()
        grid.setSpacing(20)

        self.modules = [
            ("FT-IR\nSpectroscopy", "ir", "📈"),
            ("XRD\nAnalysis", "xrd", "📊"),
        ]

        for i, (name, target, icon) in enumerate(self.modules):
            btn = QPushButton(f"{icon}\n\n{name}")
            btn.setMinimumHeight(120)
            btn.setCursor(Qt.PointingHandCursor)
            
            if target in ["ir", "xrd"]:
                btn.clicked.connect(lambda checked=False, b=btn, t=target, n=name, ic=icon: self.launch_app(b, t, n, ic))
            else:
                btn.clicked.connect(self.coming_soon)
                
            grid.addWidget(btn, i // 3, i % 3)

        layout.addLayout(grid)
        footer = QLabel("Version 1.0")
        footer.setObjectName("Subtitle")
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)

    def launch_app(self, btn, module_name, original_name, icon):
        # 1. Check if the PROCESS is already running
        if module_name in self.open_windows:
            process = self.open_windows[module_name]
            if process.is_alive(): 
                QMessageBox.warning(self, "Already Running", f"{original_name} is already open.")
                return

        btn.setText("⏳\n\nStarting...")
        btn.setEnabled(False)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        
        try:
            # 2. Launch the module's main() function in a completely separate process
            if module_name == "ir":
                p = multiprocessing.Process(target=ir.main)
                p.start()
                self.open_windows["ir"] = p 
                
            elif module_name == "xrd":
                # Assuming xrd.py also has a main() function like ir.py
                p = multiprocessing.Process(target=xrd.main)
                p.start()
                self.open_windows["xrd"] = p 
                
        except Exception as e:
            QMessageBox.critical(self, "Launch Error", f"Could not start {original_name}.\nError: {e}")
            
        QTimer.singleShot(3000, lambda: self.reset_button(btn, original_name, icon))

    def reset_button(self, btn, original_name, icon):
        btn.setText(f"{icon}\n\n{original_name}")
        btn.setEnabled(True)
        QApplication.restoreOverrideCursor()

    def coming_soon(self):
        QMessageBox.information(self, "Module In Development", "This workspace is currently being built. Please check back in the next version!")

if __name__ == "__main__":
    # --- CRITICAL FOR WINDOWS .EXE BUILDS ---
    multiprocessing.freeze_support() 
    # ----------------------------------------

    try:
        myappid = 'analytical.spectroscopy.suite.1.0' 
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass 

    app = QApplication(sys.argv)
    
    # Use resource_path for the icon!
    app.setWindowIcon(QIcon(resource_path("icon.png"))) 
    
    window = WelcomeDashboard()
    window.show()
    sys.exit(app.exec())