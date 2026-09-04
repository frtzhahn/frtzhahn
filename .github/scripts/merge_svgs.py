#!/usr/bin/env python3
"""
merge_svgs.py
Legacy wrapper redirecting to update_waka_svg.py.
Pure Native SVG architecture generated via .github/scripts/update_waka_svg.py.
"""
import sys
import os

# Add script dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from update_waka_svg import main

if __name__ == '__main__':
    main()
