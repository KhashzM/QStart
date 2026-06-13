import json
with open('data/app_index.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
apps = data['apps']

exts = {}
ext_icon = {}
for a in apps:
    e = a['extension']
    exts[e] = exts.get(e, 0) + 1
    if a.get('icon_data'):
        ext_icon[e] = ext_icon.get(e, 0) + 1

for e in exts:
    print(f"{e}: total={exts[e]}, with_icon={ext_icon.get(e, 0)}")