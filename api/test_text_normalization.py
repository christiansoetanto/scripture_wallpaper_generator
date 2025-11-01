#!/usr/bin/env python3
"""
Unit tests for text normalization in bible_scraper.py
Focuses on preserving verse line breaks while cleaning text.
"""

import unittest
import re
from bible_scraper import clean_verse_text


class TestTextNormalization(unittest.TestCase):
    
    def setUp(self):
        """Set up test data with Psalm 1 and other examples."""
        # Psalm 1 with proper verse breaks (how it should appear)
        self.psalm_1_expected = """Blessed is the one
who does not walk in step with the wicked
or stand in the way that sinners take
or sit in the company of mockers,
but whose delight is in the law of the Lord,
and who meditates on his law day and night.
That person is like a tree planted by streams of water,
which yields its fruit in season
and whose leaf does not wither—
whatever they do prospers.
Not so the wicked!
They are like chaff
that the wind blows away.
Therefore the wicked will not stand in the judgment,
nor sinners in the assembly of the righteous.
For the Lord watches over the way of the righteous,
but the way of the wicked leads to destruction."""

        # Psalm 1 as it might come from HTML (with various formatting issues)
        self.psalm_1_raw_html = """1 Blessed is the one
who does not walk in step with the wicked
or stand in the way that sinners take
or sit in the company of mockers,

2 but whose delight is in the law of the Lord,
and who meditates on his law day and night.

3 That person is like a tree planted by streams of water,
which yields its fruit in season
and whose leaf does not wither—
whatever they do prospers.

4 Not so the wicked!
They are like chaff
that the wind blows away.

5 Therefore the wicked will not stand in the judgment,
nor sinners in the assembly of the righteous.

6 For the Lord watches over the way of the righteous,
but the way of the wicked leads to destruction."""

        # Another test case with different formatting issues
        self.messy_text = """1 In the beginning was the Word,\r\n\r\n2 and the Word was with God,\n\n\n3 and the Word was God.\t\t\n\n4 He was with God in the beginning."""
        
        self.expected_clean_text = """In the beginning was the Word,
and the Word was with God,
and the Word was God.
He was with God in the beginning."""

    def test_psalm_1_verse_separation(self):
        """Test that Psalm 1 verses are properly separated after cleaning."""
        cleaned = clean_verse_text(self.psalm_1_raw_html)
        
        # Check that verse numbers are removed
        self.assertNotIn('1 Blessed', cleaned)
        self.assertNotIn('2 but', cleaned)
        self.assertNotIn('3 That', cleaned)
        
        # Check that verses start properly
        self.assertTrue(cleaned.startswith('Blessed is the one'))
        
        # Check that line breaks between verses are preserved
        lines = cleaned.split('\n')
        self.assertGreater(len(lines), 1, "Text should have multiple lines")
        
        # Verify specific verse beginnings are on separate lines
        verse_beginnings = [
            'Blessed is the one',
            'but whose delight is in the law',
            'That person is like a tree',
            'Not so the wicked!',
            'Therefore the wicked will not stand',
            'For the Lord watches over'
        ]
        
        text_lines = [line.strip() for line in lines if line.strip()]
        found_beginnings = []
        
        for line in text_lines:
            for beginning in verse_beginnings:
                if line.startswith(beginning):
                    found_beginnings.append(beginning)
                    break
        
        print(f"Found verse beginnings: {found_beginnings}")
        print(f"Cleaned text lines: {text_lines}")
        
        # Should find multiple verse beginnings
        self.assertGreaterEqual(len(found_beginnings), 3, 
                               f"Should find at least 3 verse beginnings, found: {found_beginnings}")

    def test_current_normalization_problem(self):
        """Test that demonstrates the current problem with line break removal."""
        # This test shows what's currently happening (the bug)
        cleaned = clean_verse_text(self.psalm_1_raw_html)
        
        # Print for debugging
        print(f"\nOriginal text:\n{self.psalm_1_raw_html}")
        print(f"\nCleaned text:\n{cleaned}")
        print(f"\nNumber of lines in cleaned text: {len(cleaned.split('\\n'))}")
        
        # The problem: verses might be running together
        # This test documents the current behavior
        lines = cleaned.split('\n')
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        
        print(f"Non-empty lines: {non_empty_lines}")
        
        # If there's only 1 line, then verses are being merged incorrectly
        if len(non_empty_lines) == 1:
            self.fail("Verses are being merged into a single line - this is the bug!")

    def test_excessive_whitespace_removal(self):
        """Test that excessive whitespace is properly removed."""
        cleaned = clean_verse_text(self.messy_text)
        
        # Should not have multiple consecutive newlines
        self.assertNotIn('\n\n', cleaned)
        
        # Should not have carriage returns
        self.assertNotIn('\r', cleaned)
        
        # Should not have multiple spaces
        self.assertNotIn('  ', cleaned)
        
        # Should not have tabs
        self.assertNotIn('\t', cleaned)

    def test_verse_number_removal(self):
        """Test that verse numbers are properly removed."""
        test_text = "1 In the beginning\n2 was the Word\n3 and the Word was God"
        cleaned = clean_verse_text(test_text)
        
        # Verse numbers should be removed
        self.assertNotIn('1 In', cleaned)
        self.assertNotIn('2 was', cleaned)
        self.assertNotIn('3 and', cleaned)
        
        # But the text should remain
        self.assertIn('In the beginning', cleaned)
        self.assertIn('was the Word', cleaned)
        self.assertIn('and the Word was God', cleaned)

    def test_preserve_intentional_line_breaks(self):
        """Test that intentional line breaks within verses are preserved."""
        test_text = """1 Blessed is the one
who does not walk in step with the wicked
or stand in the way that sinners take

2 but whose delight is in the law of the Lord,
and who meditates on his law day and night."""
        
        cleaned = clean_verse_text(test_text)
        
        # Should preserve line breaks within verses
        self.assertIn('Blessed is the one\nwho does not walk', cleaned)
        self.assertIn('but whose delight is in the law of the Lord,\nand who meditates', cleaned)

    def test_empty_and_whitespace_lines(self):
        """Test handling of empty lines and whitespace-only lines."""
        test_text = "Line 1\n\n\n   \n\nLine 2\n\t\n\nLine 3"
        cleaned = clean_verse_text(test_text)
        
        # Should not have multiple consecutive newlines
        self.assertNotIn('\n\n', cleaned)
        
        # Should have proper line separation
        lines = [line for line in cleaned.split('\n') if line.strip()]
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], 'Line 1')
        self.assertEqual(lines[1], 'Line 2') 
        self.assertEqual(lines[2], 'Line 3')


def run_diagnostic_test():
    """Run a diagnostic to show the current behavior."""
    print("=== DIAGNOSTIC TEST FOR TEXT NORMALIZATION ===\n")
    
    # Test with a simple multi-verse example
    test_input = """1 Blessed is the one who does not walk in step with the wicked

2 but whose delight is in the law of the Lord,

3 That person is like a tree planted by streams of water"""
    
    print("Input text:")
    print(repr(test_input))
    print("\nInput text (formatted):")
    print(test_input)
    
    cleaned = clean_verse_text(test_input)
    
    print(f"\nCleaned text:")
    print(repr(cleaned))
    print(f"\nCleaned text (formatted):")
    print(cleaned)
    
    print(f"\nNumber of lines in output: {len(cleaned.split(chr(10)))}")
    print(f"Lines: {cleaned.split(chr(10))}")


if __name__ == '__main__':
    # Run diagnostic first
    run_diagnostic_test()
    
    print("\n" + "="*50)
    print("RUNNING UNIT TESTS")
    print("="*50)
    
    # Run unit tests
    unittest.main(verbosity=2)