import pytest
import sys
import os
from unittest.mock import patch, Mock
import responses

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bible_scraper import scrape_bible_verse


class TestScrapeBibleVerse:
    """Test cases for scrape_bible_verse function."""
    
    @responses.activate
    def test_scrape_bible_verse_success(self):
        """Test successful scraping of a Bible verse."""
        # Mock HTML response from Bible Gateway
        mock_html = """
        <html>
        <body>
        <div class="passage-text">
        <div class="passage-content passage-class-0">
        <div class="version-ESV result-text-style-normal text-html">
        <div class="text">
        <p><span class="text John-3-16"><span class="text"><span class="chapternum">16 </span>For God so loved the world, that he gave his only Son, that whoever believes in him should not perish but have eternal life.</span></span></p>
        </div>
        </div>
        </div>
        </div>
        </body>
        </html>
        """
        
        responses.add(
            responses.GET,
            "https://www.biblegateway.com/passage/?search=John+3%3A16&version=RSVCE",
            body=mock_html,
            status=200
        )
        
        result = scrape_bible_verse("John 3:16")
        
        assert result is not None
        assert "text" in result
        assert "reference" in result
        assert "For God so loved the world" in result["text"]
        assert result["reference"] == "John 3:16"
    
    @responses.activate
    def test_scrape_bible_verse_with_end_verse(self):
        """Test scraping a verse range."""
        mock_html = """
        <html>
        <body>
        <div class="passage-text">
        <div class="passage-content passage-class-0">
        <div class="version-ESV result-text-style-normal text-html">
        <div class="text">
        <p><span class="text John-3-16"><span class="text"><span class="chapternum">16 </span>For God so loved the world, that he gave his only Son, that whoever believes in him should not perish but have eternal life. <span class="chapternum">17 </span>For God did not send his Son into the world to condemn the world, but in order that the world might be saved through him.</span></span></p>
        </div>
        </div>
        </div>
        </div>
        </body>
        </html>
        """
        
        responses.add(
            responses.GET,
            "https://www.biblegateway.com/passage/?search=John+3%3A16-17&version=RSVCE",
            body=mock_html,
            status=200
        )
        
        result = scrape_bible_verse("John 3:16-17")
        
        assert result is not None
        assert "text" in result
        assert "reference" in result
        assert "For God so loved the world" in result["text"]
        assert "For God did not send his Son" in result["text"]
        assert result["reference"] == "John 3:16-17"
    
    @responses.activate
    def test_scrape_bible_verse_numbered_book(self):
        """Test scraping from a numbered book."""
        mock_html = """
        <html>
        <body>
        <div class="passage-text">
        <div class="passage-content passage-class-0">
        <div class="version-ESV result-text-style-normal text-html">
        <div class="text">
        <p><span class="text 1Corinthians-13-4"><span class="text"><span class="chapternum">4 </span>Love is patient and kind; love does not envy or boast; it is not arrogant</span></span></p>
        </div>
        </div>
        </div>
        </div>
        </body>
        </html>
        """
        
        responses.add(
            responses.GET,
            "https://www.biblegateway.com/passage/?search=1+Corinthians+13%3A4&version=RSVCE",
            body=mock_html,
            status=200
        )
        
        result = scrape_bible_verse("1 Corinthians 13:4", "RSVCE")
        
        assert result is not None
        assert "text" in result
        assert "reference" in result
        assert "Love is patient and kind" in result["text"]
        assert result["reference"] == "1 Corinthians 13:4"
    
    @responses.activate
    def test_scrape_bible_verse_network_error(self):
        """Test handling of network errors."""
        responses.add(
            responses.GET,
            "https://www.biblegateway.com/passage/?search=John+3%3A16&version=RSVCE",
            body="Network error",
            status=500
        )
        
        result = scrape_bible_verse("John 3:16")
        assert result is None
    
    @responses.activate
    def test_scrape_bible_verse_no_passage_found(self):
        """Test handling when no passage is found in HTML."""
        mock_html = """
        <html>
        <body>
        <div class="no-results">
        No results found
        </div>
        </body>
        </html>
        """
        
        responses.add(
            responses.GET,
            "https://www.biblegateway.com/passage/?search=John+3%3A16&version=RSVCE",
            body=mock_html,
            status=200
        )
        
        result = scrape_bible_verse("John 3:16")
        assert result is None
    
    @responses.activate
    def test_scrape_bible_verse_empty_text(self):
        """Test handling when passage text is empty."""
        mock_html = """
        <html>
        <body>
        <div class="passage-text">
        <div class="passage-content passage-class-0">
        <div class="version-ESV result-text-style-normal text-html">
        <div class="text">
        </div>
        </div>
        </div>
        </div>
        </body>
        </html>
        """
        
        responses.add(
            responses.GET,
            "https://www.biblegateway.com/passage/?search=John+3%3A16&version=RSVCE",
            body=mock_html,
            status=200
        )
        
        result = scrape_bible_verse("John 3:16")
        assert result is None
    
    def test_scrape_bible_verse_invalid_parameters(self):
        """Test handling of invalid parameters."""
        # Test with empty query
        result = scrape_bible_verse("")
        assert result is None
        
        # Test with invalid query format
        result = scrape_bible_verse("invalid query")
        assert result is None
        
        # Test with None query
        result = scrape_bible_verse(None)
        assert result is None
    
    @responses.activate
    def test_scrape_bible_verse_url_encoding(self):
        """Test that URL parameters are properly encoded."""
        mock_html = """
        <html>
        <body>
        <div class="passage-text">
        <div class="passage-content passage-class-0">
        <div class="version-ESV result-text-style-normal text-html">
        <div class="text">
        <p><span class="text"><span class="chapternum">27 </span>Test verse text</span></p>
        </div>
        </div>
        </div>
        </div>
        </body>
        </html>
        """
        
        # Test with book name that needs URL encoding
        responses.add(
            responses.GET,
            "https://www.biblegateway.com/passage/?search=Song+of+Songs+1%3A1&version=RSVCE",
            body=mock_html,
            status=200
        )
        
        result = scrape_bible_verse("Song of Songs 1:1")
        
        assert result is not None
        assert result["reference"] == "Song of Songs 1:1"
    
    @responses.activate
    def test_scrape_bible_verse_text_cleaning(self):
        """Test that scraped text is properly cleaned."""
        mock_html = """
        <html>
        <body>
        <div class="passage-text">
        <div class="passage-content passage-class-0">
        <div class="version-ESV result-text-style-normal text-html">
        <div class="text">
        <p><span class="text John-3-16"><span class="text">   <span class="chapternum">16 </span>For God so loved the world,   that he gave his only Son.   </span></span></p>
        </div>
        </div>
        </div>
        </div>
        </body>
        </html>
        """
        
        responses.add(
            responses.GET,
            "https://www.biblegateway.com/passage/?search=John+3%3A16&version=RSVCE",
            body=mock_html,
            status=200
        )
        
        result = scrape_bible_verse("John 3:16")
        
        assert result is not None
        # Check that extra spaces are cleaned up
        assert "   " not in result["text"]
        # Check that verse numbers are removed
        assert "16 " not in result["text"]
        assert result["text"].startswith("For God so loved")
    
    @responses.activate  
    def test_scrape_bible_verse_connection_timeout(self):
        """Test handling of connection timeout."""
        import requests
        
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout()
            
            result = scrape_bible_verse("John 3:16")
            assert result is None
    
    @responses.activate
    def test_scrape_bible_verse_connection_error(self):
        """Test handling of connection errors."""
        import requests
        
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError()
            
            result = scrape_bible_verse("John 3:16")
            assert result is None