import threading
import time
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
        self.listening = False
        self.thread = None
        self.signal = HotkeySignal()
    
    def start(self):
        if not KEYBOARD_AVAILABLE:
            print("Warning: keyboard module not available")
            return
        
        if not self.listening:
            self.listening = True
            self.thread = threading.Thread(target=self.listen, daemon=True)
            self.thread.start()
    
    def stop(self):
        self.listening = False
        if self.thread:
            self.thread.join(timeout=1)
    
    def set_hotkey(self, new_hotkey):
        old_hotkey = self.hotkey
        self.hotkey = new_hotkey
        
        if self.listening:
            self.stop()
            self.start()
        
        return old_hotkey
    
    def listen(self):
        while self.listening:
            try:
                keyboard.wait(self.hotkey, suppress=True)
                if self.listening:
                    self.signal.hotkey_triggered.emit()
            except Exception as e:
                print(f"Hotkey error: {e}")
                time.sleep(0.5)