import os

desktop = os.path.expanduser("~/Desktop")

all_files = []
hidden_files = []
excluded_files = []

for filename in os.listdir(desktop):
    filepath = os.path.join(desktop, filename)
    
    if filename.startswith('.'):
        hidden_files.append(filename)
        continue
    
    if not os.path.exists(filepath):
        excluded_files.append(filename)
        continue
    
    all_files.append(filename)

print(f"Total files on desktop: {len(os.listdir(desktop))}")
print(f"Hidden files (starting with .): {len(hidden_files)}")
print(f"Non-existent files: {len(excluded_files)}")
print(f"Files that would be indexed: {len(all_files)}")

if hidden_files:
    print("\n--- Hidden files ---")
    for f in hidden_files:
        print(f"  {f}")

if excluded_files:
    print("\n--- Non-existent files ---")
    for f in excluded_files:
        print(f"  {f}")