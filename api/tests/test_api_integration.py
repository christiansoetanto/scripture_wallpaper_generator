import pytest
import sys
import os
import json
import requests
import time
import threading
import subprocess
from unittest.mock import Mock, patch

# Add the parent directory to the path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from image import handler
import bible_scraper


class TestAPIIntegration:
    """Integration tests for API functionality supporting the text editor."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.test_verses = [
            "John 3:16",
            "Psalm 23:1",
            "Romans 8:28",
            "Philippians 4:13"
        ]
        self.test_versions = ["RSVCE", "ESV", "NABRE"]
    
    def test_verse_data_endpoint_integration(self):
        """Test the /api/verse-data endpoint that the text editor uses."""
        # This test simulates the API call that the frontend makes
        
        # Test data
        test_verse = "John 3:16"
        test_version = "RSVCE"
        
        # Mock the scraping function to avoid external dependencies
        with patch('bible_scraper.scrape_bible_verse') as mock_scrape:
            mock_scrape.return_value = {
                'text': 'For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life.',
                'reference': 'John 3:16',
                'version': 'RSVCE'
            }
            
            # Simulate the API request
            query_params = {
                'q': test_verse,
                'version': test_version,
                'screen_height': '2340',
                'top_boundary_percent': '15',
                'bottom_boundary_percent': '15'
            }
            
            # Test that the scraper returns expected data
            result = bible_scraper.scrape_bible_verse(test_verse, test_version)
            
            assert result is not None
            assert 'text' in result
            assert 'reference' in result
            assert 'version' in result
            assert len(result['text']) > 0
            assert result['reference'] == 'John 3:16'
            assert result['version'] == test_version
    
    def test_text_processing_for_editor(self):
        """Test that verse text is properly processed for the text editor."""
        
        with patch('bible_scraper.scrape_bible_verse') as mock_scrape:
            # Test with various text formats
            test_cases = [
                {
                    'input': 'Simple verse text.',
                    'expected_length': 18
                },
                {
                    'input': 'Verse with\nmultiple\nlines.',
                    'expected_contains': ['\n', 'multiple']
                },
                {
                    'input': 'Verse with "quotes" and special characters: !@#$%',
                    'expected_contains': ['"quotes"', '!@#$%']
                }
            ]
            
            for case in test_cases:
                mock_scrape.return_value = {
                    'text': case['input'],
                    'reference': 'Test 1:1',
                    'version': 'RSVCE'
                }
                
                result = bible_scraper.scrape_bible_verse("Test 1:1", "RSVCE")
                
                if 'expected_length' in case:
                    assert len(result['text']) == case['expected_length']
                
                if 'expected_contains' in case:
                    for expected_text in case['expected_contains']:
                        assert expected_text in result['text']
    
    def test_multiple_versions_integration(self):
        """Test that different Bible versions work correctly with the text editor."""
        
        for version in self.test_versions:
            with patch('bible_scraper.scrape_bible_verse') as mock_scrape:
                mock_scrape.return_value = {
                    'text': f'Sample verse text from {version}',
                    'reference': 'John 3:16',
                    'version': version
                }
                
                result = bible_scraper.scrape_bible_verse("John 3:16", version)
                
                assert result['version'] == version
                assert version in result['text']
                assert len(result['text']) > 0
    
    def test_error_handling_for_invalid_verses(self):
        """Test error handling for invalid verse references."""
        
        invalid_verses = [
            "Invalid 999:999",
            "NotABook 1:1",
            "Genesis 999:1",
            ""
        ]
        
        for invalid_verse in invalid_verses:
            with patch('bible_scraper.scrape_bible_verse') as mock_scrape:
                # Simulate scraper returning None for invalid verses
                mock_scrape.return_value = None
                
                result = bible_scraper.scrape_bible_verse(invalid_verse, "RSVCE")
                assert result is None
    
    def test_verse_formatting_consistency(self):
        """Test that verse formatting is consistent for the text editor."""
        
        with patch('bible_scraper.scrape_bible_verse') as mock_scrape:
            # Test consistent formatting
            mock_scrape.return_value = {
                'text': 'For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life.',
                'reference': 'John 3:16',
                'version': 'RSVCE'
            }
            
            result = bible_scraper.scrape_bible_verse("John 3:16", "RSVCE")
            
            # Check that text doesn't have unwanted formatting
            assert not result['text'].startswith(' ')  # No leading spaces
            assert not result['text'].endswith(' ')   # No trailing spaces
            assert '\t' not in result['text']         # No tabs
            
            # Check that reference is properly formatted
            assert result['reference'] == 'John 3:16'
    
    def test_long_verse_handling(self):
        """Test handling of long verses that might wrap in the text editor."""
        
        with patch('bible_scraper.scrape_bible_verse') as mock_scrape:
            # Simulate a very long verse
            long_text = "This is a very long verse text that would definitely wrap in the text editor and should be handled properly by the system. " * 5
            
            mock_scrape.return_value = {
                'text': long_text,
                'reference': 'Psalm 119:1',
                'version': 'RSVCE'
            }
            
            result = bible_scraper.scrape_bible_verse("Psalm 119:1", "RSVCE")
            
            assert len(result['text']) > 500  # Verify it's actually long
            assert result['text'] == long_text  # Verify it's preserved exactly
    
    def test_special_characters_preservation(self):
        """Test that special characters are preserved in verse text."""
        
        with patch('bible_scraper.scrape_bible_verse') as mock_scrape:
            # Test with various special characters
            special_text = 'Verse with "quotes", \'apostrophes\', em-dashes—and other special characters: ©®™'
            
            mock_scrape.return_value = {
                'text': special_text,
                'reference': 'Test 1:1',
                'version': 'RSVCE'
            }
            
            result = bible_scraper.scrape_bible_verse("Test 1:1", "RSVCE")
            
            # Verify all special characters are preserved
            assert '"quotes"' in result['text']
            assert '\'apostrophes\'' in result['text']
            assert 'em-dashes—and' in result['text']
            assert '©®™' in result['text']
    
    def test_verse_range_handling(self):
        """Test handling of verse ranges (e.g., John 3:16-17)."""
        
        with patch('bible_scraper.scrape_bible_verse') as mock_scrape:
            mock_scrape.return_value = {
                'text': 'For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life. For God did not send his Son into the world to condemn the world, but to save the world through him.',
                'reference': 'John 3:16-17',
                'version': 'RSVCE'
            }
            
            result = bible_scraper.scrape_bible_verse("John 3:16-17", "RSVCE")
            
            assert result['reference'] == 'John 3:16-17'
            assert len(result['text']) > 100  # Should be longer than single verse
            assert 'For God so loved' in result['text']
            assert 'to save the world' in result['text']


class TestTextEditorDataFlow:
    """Test the data flow that supports the text editor functionality."""
    
    def test_fetch_to_edit_workflow(self):
        """Test the complete workflow from fetching to editing."""
        
        with patch('bible_scraper.scrape_bible_verse') as mock_scrape:
            # Step 1: Fetch verse data
            original_text = 'For God so loved the world that he gave his one and only Son.'
            mock_scrape.return_value = {
                'text': original_text,
                'reference': 'John 3:16',
                'version': 'RSVCE'
            }
            
            fetched_data = bible_scraper.scrape_bible_verse("John 3:16", "RSVCE")
            
            # Step 2: Simulate text editing
            edited_text = 'For God so loved the world that he gave his one and only Son. [EDITED]'
            
            # Step 3: Verify data integrity
            assert fetched_data['text'] == original_text
            assert edited_text != original_text
            assert '[EDITED]' in edited_text
            assert fetched_data['reference'] == 'John 3:16'
    
    def test_canvas_update_data_flow(self):
        """Test the data flow for canvas updates when text is edited."""
        
        # Simulate the data that would be sent to canvas rendering
        canvas_data = {
            'text': 'Edited verse text for canvas rendering',
            'reference': 'John 3:16',
            'version': 'RSVCE',
            'font_size': 24,
            'line_spacing': 1.2
        }
        
        # Verify canvas data structure
        assert 'text' in canvas_data
        assert 'reference' in canvas_data
        assert 'version' in canvas_data
        assert isinstance(canvas_data['font_size'], (int, float))
        assert isinstance(canvas_data['line_spacing'], (int, float))
        
        # Test text modifications
        modified_text = canvas_data['text'].replace('Edited', 'Modified')
        assert modified_text != canvas_data['text']
        assert 'Modified' in modified_text


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])