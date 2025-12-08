"""
Force clean restart script - clears Python cache
"""

import sys
import os
import shutil

print("="*70)
print("CLEAN RESTART - CLEARING PYTHON CACHE")
print("="*70)

# Remove __pycache__ directories
cache_dirs = []
for root, dirs, files in os.walk('.'):
    if '__pycache__' in dirs:
        cache_path = os.path.join(root, '__pycache__')
        cache_dirs.append(cache_path)

if cache_dirs:
    print(f"\nFound {len(cache_dirs)} cache directories:")
    for cache_dir in cache_dirs:
        print(f"  Removing: {cache_dir}")
        try:
            shutil.rmtree(cache_dir)
            print(f"  ✓ Deleted")
        except Exception as e:
            print(f"  ✗ Error: {e}")
else:
    print("\nNo cache directories found")

# Remove .pyc files
pyc_files = []
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.pyc'):
            pyc_path = os.path.join(root, file)
            pyc_files.append(pyc_path)

if pyc_files:
    print(f"\nFound {len(pyc_files)} .pyc files:")
    for pyc_file in pyc_files:
        print(f"  Removing: {pyc_file}")
        try:
            os.remove(pyc_file)
            print(f"  ✓ Deleted")
        except Exception as e:
            print(f"  ✗ Error: {e}")
else:
    print("\nNo .pyc files found")

print("\n" + "="*70)
print("CACHE CLEARED!")
print("="*70)
print("\nNow run: python app.py")
print("="*70)
