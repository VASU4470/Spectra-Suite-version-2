import sys
import os
import ctypes
import multiprocessing  # Launches each workspace (ir.main / xrd.main) as an isolated process
import tkinter as tk
from tkinter import messagebox
import ir
import xrd
import general
from version import check_and_notify_new_version

# --- ADDED HELPER FUNCTION ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
# -----------------------------

# --- THEME (ported 1:1 from the old PySide6 QSS palette) ---
COLOR_BG = "#1e1e2e"
COLOR_TEXT = "#cdd6f4"
COLOR_TITLE = "#89b4fa"
COLOR_SUBTITLE = "#a6adc8"
COLOR_BTN_BG = "#313244"
COLOR_BTN_BORDER = "#45475a"
COLOR_BTN_HOVER_BG = "#45475a"
COLOR_BTN_HOVER_BORDER = "#89b4fa"
COLOR_BTN_PRESSED = "#585b70"


class WelcomeDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Analytical Spectroscopy Suite")
        self.geometry("700x500")
        self.configure(bg=COLOR_BG)
        self.open_windows = {}  # Stores running multiprocessing.Process objects, keyed by module name

        try:
            app_icon = tk.PhotoImage(file=resource_path('icon.png'))
            self.iconphoto(True, app_icon)
            self._icon_ref = app_icon  # keep a reference so it isn't garbage-collected
        except Exception:
            pass

        self.modules = [
            ("FT-IR\nSpectroscopy", "ir", "📈"),
            ("XRD\nAnalysis", "xrd", "📊"),
            ("General\nPlotter", "general", "📉"),
        ]

        self._setup_ui()

    def _setup_ui(self):
        container = tk.Frame(self, bg=COLOR_BG)
        container.pack(fill="both", expand=True, padx=40, pady=40)

        title = tk.Label(container, text="Analytical Spectroscopy Suite",
                          font=("Arial", 26, "bold"), fg=COLOR_TITLE, bg=COLOR_BG)
        title.pack(pady=(0, 8))

        subtitle = tk.Label(container, text="Select a workspace to begin",
                             font=("Arial", 14), fg=COLOR_SUBTITLE, bg=COLOR_BG)
        subtitle.pack(pady=(0, 20))

        grid_frame = tk.Frame(container, bg=COLOR_BG)
        grid_frame.pack(fill="both", expand=True)

        cols = 3  # matches the old QGridLayout's `i // 3, i % 3` placement
        for col in range(cols):
            grid_frame.columnconfigure(col, weight=1)

        self.buttons = {}
        for i, (name, target, icon) in enumerate(self.modules):
            btn = self._make_dashboard_button(grid_frame, name, icon)
            btn.grid(row=i // cols, column=i % cols, padx=10, pady=10, sticky="nsew")

            if target in ("ir", "xrd", "general"):
                btn.configure(command=lambda b=btn, t=target, n=name, ic=icon: self.launch_app(b, t, n, ic))
            else:
                btn.configure(command=self.coming_soon)

            self.buttons[target] = btn

        footer = tk.Label(container, text="Version 1.0", font=("Arial", 10),
                           fg=COLOR_SUBTITLE, bg=COLOR_BG)
        footer.pack(pady=(20, 0))

    def _make_dashboard_button(self, parent, name, icon):
        """Plain tk.Button (not ttk) so we get exact, cross-platform-consistent
        colors -- ttk's native theme on Windows/macOS often ignores background
        color overrides, which would break the dark dashboard look."""
        btn = tk.Button(
            parent,
            text=f"{icon}\n\n{name}",
            font=("Arial", 16, "bold"),
            fg=COLOR_TEXT,
            bg=COLOR_BTN_BG,
            activebackground=COLOR_BTN_PRESSED,
            activeforeground=COLOR_TEXT,
            relief="flat",
            bd=2,
            highlightthickness=2,
            highlightbackground=COLOR_BTN_BORDER,
            highlightcolor=COLOR_BTN_BORDER,
            cursor="hand2",
            padx=15, pady=15,
            wraplength=180,
            justify="center",
        )
        btn.configure(height=5)

        def on_enter(e):
            if btn["state"] != "disabled":
                btn.configure(bg=COLOR_BTN_HOVER_BG, highlightbackground=COLOR_BTN_HOVER_BORDER)

        def on_leave(e):
            if btn["state"] != "disabled":
                btn.configure(bg=COLOR_BTN_BG, highlightbackground=COLOR_BTN_BORDER)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def launch_app(self, btn, module_name, original_name, icon):
        # 1. Check if the PROCESS is already running
        if module_name in self.open_windows:
            process = self.open_windows[module_name]
            if process.is_alive():
                messagebox.showwarning("Already Running", f"{original_name} is already open.", parent=self)
                return

        btn.configure(text="⏳\n\nStarting...", state="disabled", cursor="watch")
        self.update_idletasks()

        try:
            # 2. Launch the module's main() function in a completely separate process
            # NOTE: target is each module's run() wrapper, not main() directly.
            # main() alone has no crash handling once invoked via
            # multiprocessing (see the comment in ir.py's run() for why) --
            # run() adds a try/except so a bug in a workspace produces a
            # CRASH_REPORT_*.txt on the Desktop instead of the window just
            # silently never appearing.
            module_entry_points = {"ir": ir.run, "xrd": xrd.run, "general": general.run}
            entry_point = module_entry_points.get(module_name)
            if entry_point:
                p = multiprocessing.Process(target=entry_point)
                p.start()
                self.open_windows[module_name] = p

        except Exception as e:
            messagebox.showerror("Launch Error", f"Could not start {original_name}.\nError: {e}", parent=self)

        self.after(3000, lambda: self.reset_button(btn, original_name, icon))

    def reset_button(self, btn, original_name, icon):
        btn.configure(text=f"{icon}\n\n{original_name}", state="normal", cursor="hand2")

    def coming_soon(self):
        messagebox.showinfo("Module In Development",
                             "This workspace is currently being built. Please check back in the next version!",
                             parent=self)


if __name__ == "__main__":
    # --- CRITICAL FOR WINDOWS .EXE BUILDS ---
    multiprocessing.freeze_support()
    # ----------------------------------------

    try:
        myappid = 'analytical.spectroscopy.suite.1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    window = WelcomeDashboard()
    # Offline "What's New" notification -- no network call, just compares the
    # built-in version string against a local marker file. Delayed slightly
    # so it doesn't fight the dashboard window for initial focus.
    window.after(400, lambda: check_and_notify_new_version(window))
    window.mainloop()
