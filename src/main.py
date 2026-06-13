import ctypes
import os
import sys

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QAction, QApplication, QMenu, QStyle, QSystemTrayIcon

from app_icon import load_app_icon
from app_indexer import AppIndexer
from config import APP_NAME, HOTKEY
from hotkey_manager import HotkeyManager
from main_window import MainWindow
from plugin_manager import PluginManager
from plugin_manager_dialog import PluginManagerDialog
from progress_dialog import ProgressDialog
from settings_dialog import SettingsDialog

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))



class QStartApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.app_icon = load_app_icon()
        if self.app_icon:
            self.app.setWindowIcon(self.app_icon)

        self.settings = QSettings("QStart", "QStart")
        self.indexer = AppIndexer()
        self.apps = self.indexer.get_apps()

        if not self.apps:
            self.indexer.build_index()
            self.apps = self.indexer.get_apps()

        self.sync_custom_apps()
        self.pinned_apps = self.build_pinned_apps()

        # 初始化插件管理器
        self.plugin_manager = PluginManager()
        loaded_plugins = self.plugin_manager.load_plugins()
        print(f"[QStart] 已加载 {len(loaded_plugins)} 个插件: {loaded_plugins}")

        self.main_window = MainWindow(self.apps, plugin_manager=self.plugin_manager)
        self.main_window.set_pinned_apps(self.pinned_apps)
        self.main_window.hide()

        self.open_hotkey = self.settings.value("open_hotkey", HOTKEY)
        self.run_hotkey = self.settings.value("run_hotkey", "enter")
        self.window_x = int(self.settings.value("window_x", 0))
        self.window_y = int(self.settings.value("window_y", 0))

        self.main_window.set_run_hotkey(self.run_hotkey)
        self.main_window.set_position(self.window_x, self.window_y)
        if self.window_x == 0 and self.window_y == 0:
            self._center_main_window()

        self.hotkey_manager = HotkeyManager(self.open_hotkey)
        self.hotkey_manager.signal.hotkey_triggered.connect(self.toggle_window)
        self.hotkey_manager.start()

        self.setup_tray()

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self.app)

        icon = self.app_icon
        if icon:    
            self.tray_icon.setIcon(icon)
        else:
            self.tray_icon.setIcon(self.app.style().standardIcon(QStyle.SP_DesktopIcon))

        self.update_tray_tooltip()

        tray_menu = QMenu()

        show_action = QAction("显示窗口", self.app)
        show_action.triggered.connect(self.show_window)
        tray_menu.addAction(show_action)

        tray_menu.addSeparator()

        refresh_action = QAction("刷新索引", self.app)
        refresh_action.triggered.connect(self.rebuild_index)
        tray_menu.addAction(refresh_action)

        plugin_mgr_action = QAction("插件管理", self.app)
        plugin_mgr_action.triggered.connect(self.show_plugin_manager)
        tray_menu.addAction(plugin_mgr_action)

        reload_plugins_action = QAction("重载插件", self.app)
        reload_plugins_action.triggered.connect(self.reload_plugins)
        tray_menu.addAction(reload_plugins_action)

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

    def update_tray_tooltip(self, custom_text=None):
        if custom_text:
            self.tray_icon.setToolTip(f"{APP_NAME} - {custom_text}")
            return
        self.tray_icon.setToolTip(f"{APP_NAME} - 按 {self.open_hotkey} 打开")

    def on_tray_click(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.toggle_window()

    def toggle_window(self):
        if self.main_window.isVisible():
            self.main_window.hide()
        else:
            self.show_window()

    def show_window(self):
        if self.window_x == 0 and self.window_y == 0:
            self._center_main_window()
        else:
            self.main_window.move(self.window_x, self.window_y)

        self.main_window.show()
        self.main_window.activateWindow()
        self.main_window.search_bar.setFocus()

    def rebuild_index(self):
        self.update_tray_tooltip("正在刷新索引...")

        dialog = ProgressDialog()
        self.indexer.set_progress_callback(dialog.update_progress)
        dialog.show()

        self.indexer.build_index()
        self.apps = self.indexer.get_apps()
        self.sync_custom_apps()
        self.pinned_apps = self.build_pinned_apps()
        self.main_window.refresh_signal.emit(self.apps)
        self.main_window.set_pinned_apps(self.pinned_apps)

        dialog.close()
        self.update_tray_tooltip()

    def sync_custom_apps(self, custom_items=None):
        if custom_items is None:
            custom_items = self.settings.value("custom_items", [])

        base_apps = [app for app in self.apps if app.get("source") != "Custom"]
        existing_names = {app["name"].lower() for app in base_apps}
        custom_apps = []

        for item in custom_items:
            app = self._build_app_item(item, "Custom")
            if not app:
                continue

            normalized_name = app["name"].lower()
            if normalized_name in existing_names:
                continue

            existing_names.add(normalized_name)
            custom_apps.append(app)

        self.apps = base_apps + custom_apps

    def build_pinned_apps(self, pinned_items=None):
        if pinned_items is None:
            pinned_items = self.settings.value("pinned_items", [])

        pinned_apps = []
        existing_paths = set()
        for item in pinned_items:
            app = self._build_app_item(item, "Pinned")
            if not app:
                continue

            normalized_path = app["path"].lower()
            if normalized_path in existing_paths:
                continue

            existing_paths.add(normalized_path)
            pinned_apps.append(app)

        return pinned_apps

    def _build_app_item(self, item, source):
        item_path = item.get("path")
        item_name = item.get("name", "").strip()
        if not item_name or not item_path or not os.path.exists(item_path):
            return None

        return {
            "name": item_name,
            "path": item_path,
            "extension": os.path.splitext(item_path)[1].lower(),
            "icon_data": self.indexer.get_icon_from_file(item_path),
            "source": source,
        }

    def show_settings(self):
        dialog = SettingsDialog(self.apps)
        if self.app_icon:
            dialog.setWindowIcon(self.app_icon)
        dialog.settings_changed.connect(self.on_settings_changed)
        dialog.exec_()

    def on_settings_changed(
        self,
        theme,
        opacity,
        custom_items,
        pinned_items,
        open_hotkey=None,
        run_hotkey=None,
        window_x=None,
        window_y=None,
    ):
        self.main_window.set_theme(theme)
        self.main_window.set_opacity(opacity / 100.0)

        if open_hotkey and open_hotkey != self.open_hotkey:
            self.open_hotkey = open_hotkey
            self.hotkey_manager.set_hotkey(open_hotkey)
            self.update_tray_tooltip()

        if run_hotkey and run_hotkey != self.run_hotkey:
            self.run_hotkey = run_hotkey
            self.main_window.set_run_hotkey(run_hotkey)

        if window_x is not None and window_y is not None:
            self.window_x = window_x
            self.window_y = window_y
            self.main_window.set_position(window_x, window_y)

        self.sync_custom_apps(custom_items)
        self.pinned_apps = self.build_pinned_apps(pinned_items)
        self.main_window.refresh_signal.emit(self.apps)
        self.main_window.set_pinned_apps(self.pinned_apps)

    def show_plugin_manager(self):
        dialog = PluginManagerDialog(self.plugin_manager)
        if self.app_icon:
            dialog.setWindowIcon(self.app_icon)
        dialog.exec_()

    def reload_plugins(self):
        self.update_tray_tooltip("正在重载插件...")
        loaded = self.plugin_manager.reload_plugins()
        print(f"[QStart] 已重载 {len(loaded)} 个插件: {loaded}")
        self.update_tray_tooltip()

    def quit_app(self):
        self.plugin_manager.unload_all()
        self.hotkey_manager.stop()
        self.tray_icon.hide()
        self.app.quit()

    def run(self):
        return self.app.exec_()

    def _center_main_window(self):
        screen_geo = QApplication.desktop().screenGeometry()
        window_geo = self.main_window.frameGeometry()
        x = (screen_geo.width() - window_geo.width()) // 2
        y = (screen_geo.height() - window_geo.height()) // 2
        self.main_window.move(x, y)


def main():
    if sys.platform == "win32":
        myappid = "qstart.app.1.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    qstart = QStartApp()
    sys.exit(qstart.run())


if __name__ == "__main__":
    main()
