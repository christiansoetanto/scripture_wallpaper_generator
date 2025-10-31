#!/usr/bin/env python3
"""
Test script to generate wallpapers with both mobile-safe and traditional layouts
for comparison purposes.
"""

import os
import sys
from image_generator import generate_wallpaper

def test_layouts():
    """Generate test wallpapers with both layout types."""
    
    # Test verse
    verse_text = "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life."
    reference = "John 3:16"
    
    # Create tests directory if it doesn't exist
    test_dir = "tests"
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
    
    print("Generating test wallpapers...")
    
    # Generate mobile-safe layout
    print("1. Generating mobile-safe layout...")
    mobile_safe_buffer = generate_wallpaper(verse_text, reference, mobile_safe=True)
    mobile_safe_path = os.path.join(test_dir, "john_3_16_mobile_safe.jpg")
    with open(mobile_safe_path, 'wb') as f:
        f.write(mobile_safe_buffer.getvalue())
    print(f"   Saved: {mobile_safe_path}")
    
    # Generate traditional layout
    print("2. Generating traditional layout...")
    traditional_buffer = generate_wallpaper(verse_text, reference, mobile_safe=False)
    traditional_path = os.path.join(test_dir, "john_3_16_traditional.jpg")
    with open(traditional_path, 'wb') as f:
        f.write(traditional_buffer.getvalue())
    print(f"   Saved: {traditional_path}")
    
    print("\nComparison files generated successfully!")
    print("Mobile-safe layout: Text positioned in upper 60% of image (avoiding app icons)")
    print("Traditional layout: Text centered in full image area")
    
    return mobile_safe_path, traditional_path

if __name__ == "__main__":
    test_layouts()