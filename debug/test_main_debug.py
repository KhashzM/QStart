import sys
import os
import ctypes

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/src')

print("Starting QStart debug mode...")

try:
    from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QStyle
    from PyQt5.QtGui import QIcon
    from PyQt5.QtCore import Qt
    print("✓ PyQt5 imported")
except Exception as e:
    print(f"✗ PyQt5 import error: {e}")
    sys.exit(1)

try:
    from config import HOTKEY, APP_NAME
    print(f"✓ config imported - Hotkey: {HOTKEY}")
except Exception as e:
    print(f"✗ config error: {e}")
    sys.exit(1)

try:
    from app_indexer import AppIndexer
    print("✓ app_indexer imported")
except Exception as e:
    print(f"✗ app_indexer error: {e}")
    sys.exit(1)

try:
    from main_window import MainWindow
    print("✓ main_window imported")
except Exception as e:
    print(f"✗ main_window error: {e}")
    sys.exit(1)

try:
    from hotkey_manager import HotkeyManager
    print("✓ hotkey_manager imported")
except Exception as e:
    print(f"✗ hotkey_manager error: {e}")
    sys.exit(1)

print("\nCreating QApplication...")
app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)
print("✓ QApplication created")

print("\nLoading app index...")
indexer = AppIndexer()
apps = indexer.get_all_apps()
if not apps:
    print("Building index...")
    indexer.build_index()
    apps = indexer.get_all_apps()
print(f"✓ Loaded {len(apps)} apps")

print("\nCreating main window...")
main_window = MainWindow(apps)
main_window.hide()
print("✓ Main window created")

print("\nCreating hotkey manager...")
def toggle_window():
    print("Hotkey pressed!")
    main_window.toggle_signal.emit()

hotkey_manager = HotkeyManager(HOTKEY, toggle_window)
hotkey_manager.start()
print(f"✓ Hotkey manager started with: {HOTKEY}")

print("\nSetting up tray...")
tray_icon = QSystemTrayIcon(app)
tray_icon.setIcon(app.style().standardIcon(QStyle.SP_DesktopIcon))
tray_icon.setToolTip(f"{APP_NAME} - Debug Mode")

tray_menu = QMenu()
show_action = QAction("显示窗口", app)
show_action.triggered.connect(toggle_window)
tray_menu.addAction(show_action)

quit_action = QAction("退出", app)
quit_action.triggered.connect(app.quit)
tray_menu.addAction(quit_action)

tray_icon.setContextMenu(tray_menu)
tray_icon.show()
print("✓ Tray icon set up")

print("\n=== QStart is running! ===")
print("Press Ctrl+Space to show window")
print("Right-click tray icon for menu")

sys.exit(app.exec_())