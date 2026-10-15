#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "app"))
from lab_loader import load_labs

labs, errors = load_labs()
print(f"{len(labs)} labs discovered")
print(f"{len(errors)} errors")
for e in errors:
    print("  -", e)
sys.exit(1 if errors else 0)
