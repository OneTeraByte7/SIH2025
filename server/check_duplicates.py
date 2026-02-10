#!/usr/bin/env python3
"""Check for duplicate route definitions"""

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines in app.py: {len(lines)}")
print("\nSearching for 'def get_algorithms'...")

matches = []
for i, line in enumerate(lines, 1):
    if 'def get_algorithms' in line:
        matches.append((i, line.strip()))

if matches:
    print(f"\nFound {len(matches)} occurrence(s):")
    for line_num, text in matches:
        print(f"  Line {line_num}: {text}")
        # Show context (5 lines before and after)
        print(f"  Context:")
        start = max(0, line_num - 6)
        end = min(len(lines), line_num + 5)
        for j in range(start, end):
            marker = ">>>" if j == line_num - 1 else "   "
            print(f"    {marker} {j+1}: {lines[j].rstrip()}")
        print()
else:
    print("No 'def get_algorithms' found")

print("\nSearching for '@app.route' with 'algorithms'...")
route_matches = []
for i, line in enumerate(lines, 1):
    if '@app.route' in line and 'algorithms' in line:
        route_matches.append((i, line.strip()))

if route_matches:
    print(f"\nFound {len(route_matches)} route(s):")
    for line_num, text in route_matches:
        print(f"  Line {line_num}: {text}")
else:
    print("No algorithm routes found")
