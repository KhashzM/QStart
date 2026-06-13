import os
import json
import base64
import winreg
from datetime import datetime
from config import SEARCH_PATHS, EXCLUDED_PATHS, APP_EXTENSIONS, DATA_DIR

def get_desktop_path():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")
        desktop_path = winreg.QueryValueEx(key, "Desktop")[0]
        winreg.CloseKey(key)
        return os.path.expandvars(desktop_path)
    except Exception:
        return os.path.expanduser("~/Desktop")

class AppIndexer:
    def __init__(self):
        self.index_file = os.path.join(DATA_DIR, "app_index.json")
        self.apps = []
        self.progress_callback = None
        self.current_progress = 0

    def set_progress_callback(self, callback):
        self.progress_callback = callback

    def update_progress(self, message, value=None):
        if self.progress_callback:
            if value is not None:
                self.current_progress = value
            self.progress_callback(message, self.current_progress)

    def is_excluded(self, path):
        for excluded in EXCLUDED_PATHS:
            if excluded.lower() in path.lower():
                return True
        return False

    def get_icon_from_file(self, path):
        try:
            from PyQt5.QtWidgets import QFileIconProvider
            from PyQt5.QtCore import QFileInfo, QByteArray, QBuffer, QIODevice
            from PyQt5.QtGui import QPixmap
            
            provider = QFileIconProvider()
            file_info = QFileInfo(path)
            icon = provider.icon(file_info)
            
            if not icon.isNull():
                pixmap = icon.pixmap(32, 32)
                ba = QByteArray()
                buf = QBuffer(ba)
                buf.open(QIODevice.WriteOnly)
                pixmap.save(buf, "PNG")
                buf.close()
                return base64.b64encode(ba.data()).decode('utf-8')
        except Exception:
            pass
        return None

    def scan_directory(self, root_dir):
        apps = []
        visited = set()
        total_files = 0
        
        for dirpath, dirnames, filenames in os.walk(root_dir):
            if self.is_excluded(dirpath):
                continue
            
            dirnames[:] = [d for d in dirnames if not self.is_excluded(os.path.join(dirpath, d))]
            
            for filename in filenames:
                if filename.startswith('.'):
                    continue
                
                filepath = os.path.join(dirpath, filename)
                
                if self.is_excluded(filepath):
                    continue
                
                _, ext = os.path.splitext(filename.lower())
                
                if ext in APP_EXTENSIONS or ext == '.url':
                    app_name = os.path.splitext(filename)[0]
                    
                    normalized_name = app_name.lower().strip()
                    normalized_path = filepath.lower()
                    
                    if (normalized_name, normalized_path) in visited:
                        continue
                    visited.add((normalized_name, normalized_path))
                    
                    icon_data = self.get_icon_from_file(filepath)
                    
                    apps.append({
                        "name": app_name,
                        "path": filepath,
                        "extension": ext,
                        "icon_data": icon_data,
                        "source": os.path.basename(root_dir)
                    })
                
                total_files += 1
                if total_files % 50 == 0:
                    self.update_progress(f"Scanning {root_dir}...")
        
        return apps

    def scan_desktop(self):
        desktops = [
            get_desktop_path(),
            r'C:\Users\Public\Desktop'
        ]
        apps = []
        visited = set()
        
        total_files = 0
        for desktop in desktops:
            if os.path.exists(desktop):
                files = os.listdir(desktop)
                total_files += len(files)
        
        processed = 0
        for desktop in desktops:
            if os.path.exists(desktop):
                files = os.listdir(desktop)
                for filename in files:
                    if filename.startswith('.'):
                        continue
                    
                    filepath = os.path.join(desktop, filename)
                    
                    if not os.path.exists(filepath):
                        continue
                    
                    normalized_name = filename.lower().strip()
                    
                    if normalized_name in visited:
                        continue
                    visited.add(normalized_name)
                    
                    if os.path.isdir(filepath):
                        icon_data = self.get_icon_from_file(filepath)
                        apps.append({
                            "name": filename,
                            "path": filepath,
                            "extension": "",
                            "icon_data": icon_data,
                            "source": "Desktop"
                        })
                    else:
                        _, ext = os.path.splitext(filename.lower())
                        
                        icon_data = self.get_icon_from_file(filepath)
                        apps.append({
                            "name": os.path.splitext(filename)[0],
                            "path": filepath,
                            "extension": ext,
                            "icon_data": icon_data,
                            "source": "Desktop"
                        })
                    
                    processed += 1
                    progress = int(processed / total_files * 20)
                    self.update_progress(f"Scanning desktop... {processed}/{total_files}", progress)
        
        return apps

    def build_index(self):
        all_apps = []
        self.current_progress = 0
        
        self.update_progress("Starting index build...", 0)
        
        self.update_progress("Scanning desktop...", 5)
        desktop_apps = self.scan_desktop()
        all_apps.extend(desktop_apps)
        
        paths = [p for p in SEARCH_PATHS if os.path.exists(p)]
        path_count = len(paths)
        progress_step = 75 // path_count if path_count > 0 else 0
        current_progress = 20
        
        for i, search_path in enumerate(paths):
            self.update_progress(f"Scanning {os.path.basename(search_path)}...", current_progress)
            apps = self.scan_directory(search_path)
            all_apps.extend(apps)
            current_progress += progress_step
        
        self.update_progress("Removing duplicates...", 95)
        all_apps = self.remove_duplicates(all_apps)
        
        self.apps = all_apps
        
        self.update_progress("Saving index...", 98)
        self.save_index()
        
        self.update_progress(f"Completed! Indexed {len(all_apps)} applications", 100)
        
        return all_apps

    def remove_duplicates(self, apps):
        seen = set()
        unique = []
        
        for app in apps:
            key = app["name"].lower()
            if key not in seen:
                seen.add(key)
                unique.append(app)
        
        return unique

    def save_index(self):
        index_data = {
            "version": "1.0",
            "updated_at": datetime.now().isoformat(),
            "apps": self.apps
        }
        
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

    def load_index(self):
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                    self.apps = index_data.get("apps", [])
            except Exception:
                self.apps = []
        return self.apps

    def get_apps(self):
        if not self.apps:
            if os.path.exists(self.index_file):
                self.load_index()
            else:
                self.build_index()
        return self.apps

    def remove_invalid(self):
        valid = []
        removed = 0
        for app in self.apps:
            if os.path.exists(app["path"]):
                valid.append(app)
            else:
                removed += 1
        self.apps = valid
        if removed > 0:
            self.save_index()
        return removed