import os
import sys

from PyQt5.QtGui import QIcon, QPixmap


def get_resource_path(filename):
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "src", filename)
    return os.path.join(os.path.dirname(__file__), filename)


def load_app_icon():
    png_path = get_resource_path("logo.png")
    if os.path.exists(png_path):
        pixmap = QPixmap(png_path)
        if not pixmap.isNull():
            return QIcon(pixmap)
    return None
