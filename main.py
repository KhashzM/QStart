import sys
import os
import ctypes
import base64

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QStyle
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt

from config import HOTKEY, APP_NAME
from app_indexer import AppIndexer
from main_window import MainWindow
from hotkey_manager import HotkeyManager
from progress_dialog import ProgressDialog
from settings_dialog import SettingsDialog


def get_resource_path(filename):
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, 'src', filename)
    return os.path.join(os.path.dirname(__file__), filename)


def load_icon_from_png():
    png_path = get_resource_path('logo.png')
    if os.path.exists(png_path):
        pixmap = QPixmap(png_path)
        if not pixmap.isNull():
            return QIcon(pixmap)
    return None


class QStartApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        self.indexer = AppIndexer()
        self.apps = self.indexer.get_apps()

        if not self.apps:
            self.indexer.build_index()
            self.apps = self.indexer.get_apps()

        self.load_custom_apps()

        self.main_window = MainWindow(self.apps)
        self.main_window.hide()

        from PyQt5.QtCore import QSettings
        settings = QSettings('QStart', 'QStart')
        self.open_hotkey = settings.value('open_hotkey', HOTKEY)
        self.run_hotkey = settings.value('run_hotkey', 'enter')
        self.window_x = int(settings.value('window_x', 0))
        self.window_y = int(settings.value('window_y', 0))

        self.main_window.set_run_hotkey(self.run_hotkey)
        self.main_window.center_window(self.window_x, self.window_y)

        self.hotkey_manager = HotkeyManager(self.open_hotkey)
        self.hotkey_manager.signal.hotkey_triggered.connect(self.toggle_window)
        self.hotkey_manager.start()

        self.setup_tray()

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self.app)

        icon = load_icon_from_png()
        if icon:
            self.tray_icon.setIcon(icon)
        else:
            self.tray_icon.setIcon(self.app.style().standardIcon(QStyle.SP_DesktopIcon))

        self.tray_icon.setToolTip(f"{APP_NAME} - 按 Ctrl+Space 打开")

        tray_menu = QMenu()

        show_action = QAction("显示窗口", self.app)
        show_action.triggered.connect(self.show_window)
        tray_menu.addAction(show_action)

        tray_menu.addSeparator()

        refresh_action = QAction("刷新索引", self.app)
        refresh_action.triggered.connect(self.rebuild_index)
        tray_menu.addAction(refresh_action)

        settings_action = QAction("设置", self.app)
        settings_action.triggered.connect(self.show_settings)
        tray_menu.addAction(settings_action)

        tray_menu.addSeparator()

        quit_action = QAction("退出", self.app)
        quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        self.tray_icon.activated.connect(self.on_tray_click)

    def on_tray_click(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.toggle_window()

    def toggle_window(self):
        if self.main_window.isVisible():
            self.main_window.hide()
        else:
            self.show_window()

    def show_window(self):
        self.main_window.center_window()
        self.main_window.show()
        self.main_window.activateWindow()
        self.main_window.search_bar.setFocus()

    def rebuild_index(self):
        self.tray_icon.setToolTip(f"{APP_NAME} - 正在刷新索引...")

        dialog = ProgressDialog()
        self.indexer.set_progress_callback(dialog.update_progress)
        dialog.show()

        self.indexer.build_index()
        self.apps = self.indexer.get_apps()

        self.load_custom_apps()

        self.main_window.refresh_signal.emit(self.apps)

        dialog.close()
        self.tray_icon.setToolTip(f"{APP_NAME} - 按 Ctrl+Space 打开")

    def load_custom_apps(self):
        from PyQt5.QtCore import QSettings

        settings = QSettings('QStart', 'QStart')
        custom_items = settings.value('custom_items', [])

        if custom_items:
            existing_names = {app['name'].lower() for app in self.apps}

            for item in custom_items:
                if os.path.exists(item['path']) and item['name'].lower() not in existing_names:
                    icon_data = self.indexer.get_icon_from_file(item['path'])
                    self.apps.append({
                        'name': item['name'],
                        'path': item['path'],
                        'extension': os.path.splitext(item['path'])[1].lower(),
                        'icon_data': icon_data,
                        'source': 'Custom'
                    })

    def show_settings(self):
        dialog = SettingsDialog()
        dialog.settings_changed.connect(self.on_settings_changed)
        dialog.exec_()

    def on_settings_changed(self, theme, opacity, custom_items, open_hotkey=None, run_hotkey=None, window_x=None, window_y=None):
        self.main_window.set_theme(theme)
        self.main_window.set_opacity(opacity / 100.0)

        if open_hotkey and open_hotkey != self.open_hotkey:
            self.open_hotkey = open_hotkey
            self.hotkey_manager.set_hotkey(open_hotkey)
            self.tray_icon.setToolTip(f"{APP_NAME} - 按 {open_hotkey} 打开")

        if run_hotkey and run_hotkey != self.run_hotkey:
            self.run_hotkey = run_hotkey
            self.main_window.set_run_hotkey(run_hotkey)

        if window_x is not None and window_y is not None:
            self.window_x = window_x
            self.window_y = window_y
            self.main_window.set_position(window_x, window_y)

        custom_apps = []
        for item in custom_items:
            if os.path.exists(item['path']):
                icon_data = self.indexer.get_icon_from_file(item['path'])
                custom_apps.append({
                    'name': item['name'],
                    'path': item['path'],
                    'extension': os.path.splitext(item['path'])[1].lower(),
                    'icon_data': icon_data,
                    'source': 'Custom'
                })

        if custom_apps:
            self.apps = [app for app in self.apps if app.get('source') != 'Custom']
            existing_names = {app['name'].lower() for app in self.apps}

            for app in custom_apps:
                if app['name'].lower() not in existing_names:
                    self.apps.append(app)

            self.main_window.refresh_signal.emit(self.apps)

    def quit_app(self):
        self.hotkey_manager.stop()
        self.tray_icon.hide()
        self.app.quit()

    def run(self):
        return self.app.exec_()

def main():
    if sys.platform == "win32":
        myappid = f"qstart.app.1.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    qstart = QStartApp()
    sys.exit(qstart.run())

if __name__ == "__main__":
    main()
