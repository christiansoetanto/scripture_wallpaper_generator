#!/usr/bin/env python3
"""
Manual test script for the image generator.
Run this to generate sample wallpapers for visual testing.
"""

import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from image_generator import create_wallpaper_from_verse_data

def test_generate_sample_wallpapers():
    """Generate sample wallpapers for manual testing."""
    
    test_verses = [
        {
            'text': 'For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life.',
            'reference': 'John 3:16',
            'filename': 'test_john_3_16.jpg'
        },
        {
            'text': 'The Lord is my shepherd, I lack nothing. He makes me lie down in green pastures, he leads me beside quiet waters, he refreshes my soul.',
            'reference': 'Psalm 23:1-3',
            'filename': 'test_psalm_23.jpg'
        },
        {
            'text': 'Trust in the Lord with all your heart and lean not on your own understanding; in all your ways submit to him, and he will make your paths straight.',
            'reference': 'Proverbs 3:5-6',
            'filename': 'test_proverbs_3.jpg'
        }
    ]
    
    print("Generating sample wallpapers...")
    
    for verse in test_verses:
        print(f"Creating {verse['filename']}...")
        img_buffer = create_wallpaper_from_verse_data(verse)
        
        # Save test image in tests directory
        output_path = os.path.join(os.path.dirname(__file__), verse['filename'])
        with open(output_path, 'wb') as f:
            f.write(img_buffer.getvalue())
        
        print(f"✓ Saved: {output_path}")
    
    print(f"\nAll sample wallpapers generated in: {os.path.dirname(__file__)}")

if __name__ == "__main__":
    test_generate_sample_wallpapers()