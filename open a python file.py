import os
import sys
import tkinter as tk
from tkinter import filedialog
import subprocess

def open_in_idle():
    folder = os.path.dirname(os.path.abspath(__file__))

    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(
        title="Select a Python file",
        initialdir=folder,
        filetypes=[("Python Files", "*.py")]
    )

    root.destroy()

    if not file_path:
        return

    # ✅ Launch IDLE in a way that Windows treats it as foreground
    subprocess.Popen(
        f'"{sys.executable}" -m idlelib "{file_path}"',
        shell=True
    )

    # ✅ Exit immediately so our script can’t steal focus back
    sys.exit()

if __name__ == "__main__":
    open_in_idle()
