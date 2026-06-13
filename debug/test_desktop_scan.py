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
print(f"Desktop path: {desktop}")
print(f"Exists: {os.path.exists(desktop)}")

if os.path.exists(desktop):
    files = os.listdir(desktop)
    print(f"\nTotal files on desktop: {len(files)}")
    
    print("\n--- Searching for WeChat ---")
    wechat_files = [f for f in files if 'wechat' in f.lower() or '微信' in f]
    if wechat_files:
        print(f"Found {len(wechat_files)} WeChat related files:")
        for f in wechat_files:
            print(f"  {f}")
    else:
        print("No WeChat files found on desktop!")