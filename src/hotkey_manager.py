from PyQt5.QtCore import QObject, pyqtSignal

try:
    import keyboard

    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False


class HotkeySignal(QObject):
    hotkey_triggered = pyqtSignal()


class HotkeyManager:
    def __init__(self, hotkey):
        self.hotkey = hotkey
        self.signal = HotkeySignal()
        self.is_registered = False
        self.hotkey_handle = None

    def start(self):
        if not KEYBOARD_AVAILABLE:
            print("Warning: keyboard module not available")
            return

        if self.is_registered:
            return

        self._register_hotkey()

    def stop(self):
        if not KEYBOARD_AVAILABLE or not self.is_registered:
            return

        self._unregister_hotkey()

    def set_hotkey(self, new_hotkey):
        old_hotkey = self.hotkey
        was_registered = self.is_registered

        if was_registered:
            self._unregister_hotkey()

        self.hotkey = new_hotkey

        if was_registered:
            self._register_hotkey()

        return old_hotkey

    def _register_hotkey(self):
        try:
            self.hotkey_handle = keyboard.add_hotkey(
                self.hotkey,
                self._emit_hotkey,
                suppress=True,
                trigger_on_release=False,
            )
            self.is_registered = True
        except Exception as exc:
            self.hotkey_handle = None
            self.is_registered = False
            print(f"Hotkey error: {exc}")

    def _unregister_hotkey(self):
        try:
            if self.hotkey_handle is not None:
                keyboard.remove_hotkey(self.hotkey_handle)
        except Exception as exc:
            print(f"Hotkey cleanup error: {exc}")
        finally:
            self.hotkey_handle = None
            self.is_registered = False

    def _emit_hotkey(self):
        self.signal.hotkey_triggered.emit()
