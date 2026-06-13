import os
import winreg

def get_desktop_path():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")
        desktop_path = winreg.QueryValueEx(key, "Desktop")[0]
        winreg.CloseKey(key)
        return os.path.expandvars(desktop_path)
    except Exception:
        return os.path.expanduser("~/Desktop")

desktop = get_desktop_path()
print(f"Desktop path from registry: {desktop}")
print(f"Standard desktop path: {os.path.expanduser('~/Desktop')}")
print(f"Are they the same? {desktop == os.path.expanduser('~/Desktop')}")

if os.path.exists(desktop):
    files = os.listdir(desktop)
    print(f"\nFiles in registry desktop: {len(files)}")
    
    print("\n--- First 20 files ---")
    for f in files[:20]:
        print(f"  {f}")
else:
    print("Registry desktop path does not exist!")