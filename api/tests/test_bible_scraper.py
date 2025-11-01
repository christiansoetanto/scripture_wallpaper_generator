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

    @responses.activate
    def test_psalm1_exact_text_output(self):
        """Test that Psalm 1 produces the exact expected text after cleaning."""
        # Expected exact text as specified by the user
        expected_text = """Blessed is the man who walks not in the counsel of the wicked,
nor stands in the way of sinners,
nor sits in the seat of scoffers;

but his delight is in the law of the Lord,
and on his law he meditates day and night.

He is like a tree planted by streams of water,
that yields its fruit in its season,
and its leaf does not wither.
In all that he does, he prospers.

The wicked are not so,
but are like chaff which the wind drives away.

Therefore the wicked will not stand in the judgment,
nor sinners in the congregation of the righteous;

for the Lord knows the way of the righteous,
but the way of the wicked will perish."""
        
        # Mock HTML response that simulates what Bible Gateway might return for Psalm 1
        # This includes the "manwho" issue and verse numbers that need to be cleaned
        mock_html = """
        <html>
        <body>
        <div class="passage-text">
        <div class="passage-content passage-class-0">
        <div class="version-RSVCE result-text-style-normal text-html">
        <div class="text">
        <h3>BOOK I</h3>
        <h4>TheTwoWays</h4>
        <p class="chapter-1">
        <span class="text Ps-1-1">
        <sup class="versenum">1 </sup>Blessed is the man who walks not in the counsel of the wicked,<br>
        nor stands in the way of sinners,<br>
        nor sits in the seat of scoffers;<br>
        </span>
        <span class="text Ps-1-2">
        <sup class="versenum">2 </sup>but his delight is in the law of the <span class="small-caps">Lord</span>,<br>
        and on his law he meditates day and night.<br>
        </span>
        <span class="text Ps-1-3">
        <sup class="versenum">3 </sup>He is like a tree planted by streams of water,<br>
        that yields its fruit in its season,<br>
        and its leaf does not wither.<br>
        In all that he does, he prospers.<br>
        </span>
        <span class="text Ps-1-4">
        <sup class="versenum">4 </sup>The wicked are not so,<br>
        but are like chaff which the wind drives away.<br>
        </span>
        <span class="text Ps-1-5">
        <sup class="versenum">5 </sup>Therefore the wicked will not stand in the judgment,<br>
        nor sinners in the congregation of the righteous;<br>
        </span>
        <span class="text Ps-1-6">
        <sup class="versenum">6 </sup>for the <span class="small-caps">Lord</span> knows the way of the righteous,<br>
        but the way of the wicked will perish.<br>
        </span>
        </p>
        </div>
        </div>
        </div>
        </div>
        </body>
        </html>
        """
        
        responses.add(
            responses.GET,
            "https://www.biblegateway.com/passage/?search=Psalm+1&version=RSVCE",
            body=mock_html,
            status=200
        )
        
        result = scrape_bible_verse("Psalm 1")
        
        # Verify the result structure
        assert result is not None, "scrape_bible_verse should return a result"
        assert "text" in result, "Result should contain 'text' key"
        assert "reference" in result, "Result should contain 'reference' key"
        
        # Verify the reference
        assert result["reference"] == "Psalm 1", f"Expected reference 'Psalm 1', got '{result['reference']}'"
        
        # Verify the exact text matches
        actual_text = result["text"].strip()
        
        # Additional checks to ensure specific issues are resolved
        assert "Blessed" in actual_text, "Text should contain 'Blessed'"
        assert "manwho" not in actual_text, "Text should not contain 'manwho' (should be fixed to 'man who')"
        assert "man who" in actual_text, "Text should contain 'man who' (fixed from 'manwho')"
        assert not actual_text.startswith("is the man"), "Text should not start with 'is the man' (Blessed should be preserved)"
        
        # Final assertion for exact match
        assert actual_text == expected_text, f"Text does not match exactly.\nExpected: {repr(expected_text)}\nActual: {repr(actual_text)}"