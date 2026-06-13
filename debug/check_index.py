import json
import os

data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
index_file = os.path.join(data_dir, 'app_index.json')

if os.path.exists(index_file):
    with open(index_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    apps = data.get('apps', [])
    print(f"Total apps in index: {len(apps)}")
    print("\n--- Searching for WeChat/微信 ---")
    
    wechat_apps = [a for a in apps if 'wechat' in a['name'].lower() or '微信' in a['name']]
    
    if wechat_apps:
        print(f"Found {len(wechat_apps)} WeChat app(s):")
        for app in wechat_apps:
            print(f"  Name: {app['name']}")
            print(f"  Path: {app['path']}")
            print(f"  Extension: {app['extension']}")
            print(f"  Source: {app.get('source', 'Unknown')}")
            print()
    else:
        print("WeChat not found in index!")
        
    print("\n--- All apps (first 20) ---")
    for i, app in enumerate(apps[:20], 1):
        print(f"{i}. {app['name']} - {app['path']}")
        
else:
    print("Index file not found!")