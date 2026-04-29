import os

APP_NAME = "QStart"
VERSION = "1.0.0"

HOTKEY = "ctrl + space"

SEARCH_PATHS = [
    os.path.expanduser("~/AppData/Roaming/Microsoft/Windows/Start Menu/Programs"),
    os.path.expanduser("~/Desktop"),
    "C:/ProgramData/Microsoft/Windows/Start Menu/Programs",
    "C:/Program Files",
    "C:/Program Files (x86)",
    os.path.expanduser("~/AppData/Local/Programs"),
]

EXCLUDED_PATHS = [
    "Windows",
    "System32",
    "WinSxS",
    "Temp",
    "Temporary",
    "node_modules",
    "__pycache__",
    ".git",
    ".svn",
    "pip",
    "Python",
    "Anaconda",
    "Miniconda",
    "NVIDIA",
    "AMD",
    "Intel",
    "Common Files",
    "Microsoft.NET",
    "Windows Defender",
    "Windows Kits",
    "WindowsPowerShell",
    "VMware",
    "Oracle",
    "Java",
    "MySQL",
    "PostgreSQL",
    "MongoDB",
]

APP_EXTENSIONS = [".exe", ".lnk"]

WINDOW_WIDTH = 600
WINDOW_HEIGHT = 400

MAX_RESULTS = 10

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
SHORTCUTS_DIR = os.path.join(os.path.dirname(__file__), "..", "shortcuts")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SHORTCUTS_DIR, exist_ok=True)