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

all_files = os.listdir(desktop)
print(f"Total files via listdir: {len(all_files)}")

visible_files = [f for f in all_files if not f.startswith('.')]
print(f"Visible files (not starting with .): {len(visible_files)}")

exists_files = []
not_exists_files = []

for f in all_files:
    filepath = os.path.join(desktop, f)
    if os.path.exists(filepath):
        exists_files.append(f)
    else:
        not_exists_files.append(f)

print(f"Existing files: {len(exists_files)}")
print(f"Non-existent files: {len(not_exists_files)}")

if not_exists_files:
    print("\n--- Non-existent files ---")
    for f in not_exists_files:
        print(f"  {f}")

print("\n--- Checking for any special directories ---")
special_paths = [
    os.path.join(desktop, 'All Users'),
    os.path.join(os.path.dirname(desktop), 'All Users', 'Desktop'),
    r'C:\Users\Public\Desktop'
]

for path in special_paths:
    if os.path.exists(path):
        files = os.listdir(path)
        print(f"{path}: {len(files)} files")
        for f in files[:5]:
            print(f"  {f}")