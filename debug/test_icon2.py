import sys, os, ctypes, ctypes.wintypes, base64
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtCore import QByteArray, QBuffer, QIODevice, Qt

app = QApplication(sys.argv)

import json
with open('data/app_index.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
apps = data['apps']

test_path = None
for a in apps:
    if a["extension"] == ".exe":
        test_path = a["path"]
        break

if not test_path:
    test_path = apps[0]["path"]

print(f"Testing: {test_path}")

shell32 = ctypes.windll.shell32
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

icon_handle = shell32.ExtractIconW(None, test_path, 0)
print(f"icon_handle: {icon_handle}")

if icon_handle and icon_handle > 1:
    size = 32
    hdc = user32.GetDC(0)
    hdc_mem = gdi32.CreateCompatibleDC(hdc)
    hbmp = gdi32.CreateCompatibleBitmap(hdc, size, size)
    gdi32.SelectObject(hdc_mem, hbmp)
    
    result = user32.DrawIconEx(hdc_mem, 0, 0, icon_handle, size, size, 0, None, 0x0001)
    print(f"DrawIconEx result: {result}")
    
    class BIH(ctypes.Structure):
        _fields_ = [
            ("biSize", ctypes.c_uint),
            ("biWidth", ctypes.c_int),
            ("biHeight", ctypes.c_int),
            ("biPlanes", ctypes.c_ushort),
            ("biBitCount", ctypes.c_ushort),
            ("biCompression", ctypes.c_uint),
            ("biSizeImage", ctypes.c_uint),
            ("biXPelsPerMeter", ctypes.c_int),
            ("biYPelsPerMeter", ctypes.c_int),
            ("biClrUsed", ctypes.c_uint),
            ("biClrImportant", ctypes.c_uint),
        ]
    
    bih = BIH()
    bih.biSize = ctypes.sizeof(BIH)
    bih.biWidth = size
    bih.biHeight = -size
    bih.biPlanes = 1
    bih.biBitCount = 32
    bih.biCompression = 0
    
    pixel_count = size * size
    pixel_data = ctypes.create_string_buffer(pixel_count * 4)
    
    result2 = gdi32.GetDIBits(hdc_mem, hbmp, 0, size, pixel_data, ctypes.byref(bih), 0)
    print(f"GetDIBits result: {result2}")
    
    if result2:
        img = QImage(pixel_data, size, size, size * 4, QImage.Format_ARGB32)
        print(f"Image null: {img.isNull()}, size: {img.width()}x{img.height()}")
        
        ba = QByteArray()
        buf = QBuffer(ba)
        buf.open(QIODevice.WriteOnly)
        save_result = img.save(buf, "PNG")
        buf.close()
        print(f"Save result: {save_result}, data size: {ba.size()}")
        
        if save_result and ba.size() > 0:
            b64 = base64.b64encode(ba.data()).decode('ascii')
            print(f"Base64 length: {len(b64)}")
            print("SUCCESS!")
        else:
            print("Save failed")
    
    gdi32.DeleteObject(hbmp)
    gdi32.DeleteDC(hdc_mem)
    user32.ReleaseDC(0, hdc)
    user32.DestroyIcon(icon_handle)
else:
    print("No icon handle returned")