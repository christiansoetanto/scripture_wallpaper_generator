import pytest
import sys
import os

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bible_parser import normalize_book_name, parse_bible_reference, format_for_biblegateway, generate_filename


class TestNormalizeBookName:
    """Test cases for normalize_book_name function."""
    
    def test_normalize_book_name_full_names(self):
        """Test normalization of full book names."""
        assert normalize_book_name("Genesis") == "Genesis"
        assert normalize_book_name("Exodus") == "Exodus"
        assert normalize_book_name("Matthew") == "Matthew"
        assert normalize_book_name("Revelation") == "Revelation"
    
    def test_normalize_book_name_abbreviations(self):
        """Test normalization of book abbreviations."""
        assert normalize_book_name("Gen") == "Genesis"
        assert normalize_book_name("Ex") == "Exodus"
        assert normalize_book_name("Matt") == "Matthew"
        assert normalize_book_name("Rev") == "Revelation"
    
    def test_normalize_book_name_case_insensitive(self):
        """Test that normalization is case insensitive."""
        assert normalize_book_name("genesis") == "Genesis"
        assert normalize_book_name("GENESIS") == "Genesis"
        assert normalize_book_name("GeNeSiS") == "Genesis"
        assert normalize_book_name("gen") == "Genesis"
        assert normalize_book_name("GEN") == "Genesis"
    
    def test_normalize_book_name_with_spaces(self):
        """Test normalization with extra spaces."""
        assert normalize_book_name(" Genesis ") == "Genesis"
        assert normalize_book_name("  Gen  ") == "Genesis"
        assert normalize_book_name("1 Kings") == "1 Kings"
        assert normalize_book_name(" 1 Kings ") == "1 Kings"
    
    def test_normalize_book_name_numbered_books(self):
        """Test normalization of numbered books."""
        assert normalize_book_name("1 Kings") == "1 Kings"
        assert normalize_book_name("2 Kings") == "2 Kings"
        assert normalize_book_name("1 Chronicles") == "1 Chronicles"
        assert normalize_book_name("2 Chronicles") == "2 Chronicles"
        assert normalize_book_name("1 Corinthians") == "1 Corinthians"
        assert normalize_book_name("2 Corinthians") == "2 Corinthians"
    
    def test_normalize_book_name_numbered_abbreviations(self):
        """Test normalization of numbered book abbreviations."""
        assert normalize_book_name("1 Kgs") == "1 Kings"
        assert normalize_book_name("2 Kgs") == "2 Kings"
        assert normalize_book_name("1 Chr") == "1 Chronicles"
        assert normalize_book_name("2 Chr") == "2 Chronicles"
        assert normalize_book_name("1 Cor") == "1 Corinthians"
        assert normalize_book_name("2 Cor") == "2 Corinthians"
    
    def test_normalize_book_name_invalid_book(self):
        """Test normalization with invalid book names."""
        assert normalize_book_name("InvalidBook") is None
        assert normalize_book_name("NotABook") is None
        assert normalize_book_name("") is None
    
    def test_normalize_book_name_special_cases(self):
        """Test special cases and edge cases."""
        assert normalize_book_name("Psalms") == "Psalms"  # Some use Psalm vs Psalms
        assert normalize_book_name("Song of Songs") == "Song of Songs"
        assert normalize_book_name("Song of Solomon") == "Song of Songs"  # Alternative name


class TestParseBibleReference:
    """Test cases for parse_bible_reference function."""
    
    def test_parse_simple_reference(self):
        """Test parsing simple book chapter:verse references."""
        result = parse_bible_reference("John 3:16")
        assert result[0] == "John"
        assert result[1] == "3"
        assert result[2] == "16"
    
    def test_parse_verse_range(self):
        """Test parsing verse ranges."""
        result = parse_bible_reference("John 3:16-17")
        assert result[0] == "John"
        assert result[1] == "3"
        assert result[2] == "16-17"
    
    def test_parse_with_abbreviations(self):
        """Test parsing with book abbreviations."""
        result = parse_bible_reference("Gen 1:1")
        assert result[0] == "Genesis"
        assert result[1] == "1"
        assert result[2] == "1"
    
    def test_parse_numbered_books(self):
        """Test parsing numbered books."""
        result = parse_bible_reference("1 Kings 8:27")
        assert result[0] == "1 Kings"
        assert result[1] == "8"
        assert result[2] == "27"
    
    def test_parse_numbered_book_abbreviations(self):
        """Test parsing numbered book abbreviations."""
        result = parse_bible_reference("1 Cor 13:4-7")
        assert result[0] == "1 Corinthians"
        assert result[1] == "13"
        assert result[2] == "4-7"
    
    def test_parse_case_insensitive(self):
        """Test that parsing is case insensitive."""
        result = parse_bible_reference("john 3:16")
        assert result[0] == "John"
        assert result[1] == "3"
        assert result[2] == "16"
    
    def test_parse_with_extra_spaces(self):
        """Test parsing with extra spaces."""
        result = parse_bible_reference("  John   3:16  ")
        assert result[0] == "John"
        assert result[1] == "3"
        assert result[2] == "16"
    
    def test_parse_invalid_format(self):
        """Test parsing invalid reference formats."""
        result = parse_bible_reference("Invalid Reference")
        assert result == (None, None, None)
        
        result = parse_bible_reference("John")
        assert result == (None, None, None)
        
        result = parse_bible_reference("3:16")
        assert result == (None, None, None)
    
    def test_parse_chapter_only(self):
        """Test parsing chapter-only references."""
        result = parse_bible_reference("John 3")
        assert result[0] == "John"
        assert result[1] == "3"
        assert result[2] is None
    
    def test_parse_edge_cases(self):
        """Test edge cases."""
        # Single chapter books (like Obadiah, Philemon, 2 John, 3 John, Jude)
        result = parse_bible_reference("Jude 1:3")
        assert result[0] == "Jude"
        assert result[1] == "1"
        assert result[2] == "3"
        
        # Large chapter/verse numbers
        result = parse_bible_reference("Psalms 119:176")
        assert result[0] == "Psalms"
        assert result[1] == "119"
        assert result[2] == "176"


class TestFormatForBiblegateway:
    """Test cases for format_for_biblegateway function."""
    
    def test_format_simple_reference(self):
        """Test formatting simple references."""
        assert format_for_biblegateway("John 3:16") == "John 3:16"
        assert format_for_biblegateway("Genesis 1:1") == "Genesis 1:1"
    
    def test_format_with_abbreviations(self):
        """Test formatting with book abbreviations."""
        assert format_for_biblegateway("Gen 1:1") == "Genesis 1:1"
        assert format_for_biblegateway("Matt 5:3") == "Matthew 5:3"
    
    def test_format_numbered_books(self):
        """Test formatting numbered books."""
        assert format_for_biblegateway("1 Kings 8:27") == "1 Kings 8:27"
        assert format_for_biblegateway("2 Cor 5:17") == "2 Corinthians 5:17"
    
    def test_format_verse_ranges(self):
        """Test formatting verse ranges."""
        assert format_for_biblegateway("John 3:16-17") == "John 3:16-17"
        assert format_for_biblegateway("Matt 5:3-12") == "Matthew 5:3-12"
    
    def test_format_chapter_only(self):
        """Test formatting chapter-only references."""
        assert format_for_biblegateway("Psalm 23") == "Psalms 23"
        assert format_for_biblegateway("John 3") == "John 3"
    
    def test_format_invalid_reference(self):
        """Test formatting invalid references."""
        assert format_for_biblegateway("Invalid Reference") is None
        assert format_for_biblegateway("") is None
        assert format_for_biblegateway("John") is None


class TestGenerateFilename:
    """Test cases for generate_filename function."""
    
    def test_generate_filename_simple(self):
        """Test generating filename for simple references."""
        assert generate_filename("John 3:16") == "john_3_16.jpg"
        assert generate_filename("Genesis 1:1") == "genesis_1_1.jpg"
    
    def test_generate_filename_with_abbreviations(self):
        """Test generating filename with book abbreviations."""
        assert generate_filename("Gen 1:1") == "genesis_1_1.jpg"
        assert generate_filename("Matt 5:3") == "matthew_5_3.jpg"
    
    def test_generate_filename_numbered_books(self):
        """Test generating filename for numbered books."""
        assert generate_filename("1 Kings 8:27") == "1_kings_8_27.jpg"
        assert generate_filename("2 Cor 5:17") == "2_corinthians_5_17.jpg"
    
    def test_generate_filename_verse_ranges(self):
        """Test generating filename for verse ranges."""
        assert generate_filename("John 3:16-17") == "john_3_16_17.jpg"
        assert generate_filename("Matt 5:3-12") == "matthew_5_3_12.jpg"
    
    def test_generate_filename_complex_verses(self):
        """Test generating filename for complex verse references."""
        assert generate_filename("Matt 25:31-33,46") == "matthew_25_31_33_46.jpg"
    
    def test_generate_filename_chapter_only(self):
        """Test generating filename for chapter-only references."""
        assert generate_filename("Psalm 23") == "psalms_23.jpg"
        assert generate_filename("John 3") == "john_3.jpg"
    
    def test_generate_filename_special_characters(self):
        """Test generating filename with special book names."""
        assert generate_filename("Song of Songs 1:1") == "song_of_songs_1_1.jpg"
        assert generate_filename("1 Chronicles 16:11") == "1_chronicles_16_11.jpg"
    
    def test_generate_filename_invalid_reference(self):
        """Test generating filename for invalid references."""
        assert generate_filename("Invalid Reference") is None
        assert generate_filename("") is None
        assert generate_filename("John") is None