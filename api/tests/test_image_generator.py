import pytest
import sys
import os
import io
from unittest.mock import patch, Mock, MagicMock
from PIL import Image, ImageFont, ImageDraw

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from image_generator import (
    load_font, 
    wrap_text, 
    calculate_text_height, 
    generate_wallpaper, 
    create_wallpaper_from_verse_data,
    IMAGE_WIDTH,
    IMAGE_HEIGHT,
    BACKGROUND_COLOR,
    TEXT_COLOR,
    FONT_PATH,
    MAIN_FONT_SIZE,
    REFERENCE_FONT_SIZE
)


class TestLoadFont:
    """Test cases for load_font function."""
    
    def test_load_font_success(self):
        """Test successful font loading."""
        # This test will only pass if the actual font file exists
        if os.path.exists(FONT_PATH):
            font = load_font(24)
            assert isinstance(font, ImageFont.FreeTypeFont)
            assert font.size == 24
    
    @patch('image_generator.ImageFont.truetype')
    def test_load_font_file_not_found(self, mock_truetype):
        """Test font loading when file is not found."""
        mock_truetype.side_effect = OSError("Font file not found")
        
        with pytest.raises(RuntimeError) as exc_info:
            load_font(24)
        
        assert "Failed to load Montserrat Light font" in str(exc_info.value)
        assert FONT_PATH in str(exc_info.value)
    
    @patch('image_generator.ImageFont.truetype')
    def test_load_font_io_error(self, mock_truetype):
        """Test font loading with IO error."""
        mock_truetype.side_effect = IOError("Permission denied")
        
        with pytest.raises(RuntimeError) as exc_info:
            load_font(24)
        
        assert "Failed to load Montserrat Light font" in str(exc_info.value)
    
    def test_load_font_different_sizes(self):
        """Test loading fonts with different sizes."""
        if os.path.exists(FONT_PATH):
            font_12 = load_font(12)
            font_24 = load_font(24)
            font_48 = load_font(48)
            
            assert font_12.size == 12
            assert font_24.size == 24
            assert font_48.size == 48


class TestWrapText:
    """Test cases for wrap_text function."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock font for testing
        self.mock_font = Mock(spec=ImageFont.FreeTypeFont)
    
    @patch('image_generator.Image.new')
    @patch('image_generator.ImageDraw.Draw')
    def test_wrap_text_single_line(self, mock_draw_class, mock_image_new):
        """Test wrapping text that fits on a single line."""
        mock_draw = Mock()
        mock_draw_class.return_value = mock_draw
        mock_draw.textbbox.return_value = (0, 0, 100, 20)  # Text fits within max_width
        
        mock_font = Mock(spec=ImageFont.FreeTypeFont)
        
        result = wrap_text("Short text", mock_font, 200)
        
        assert result == ["Short text"]
        mock_draw.textbbox.assert_called()
    
    @patch('image_generator.Image.new')
    @patch('image_generator.ImageDraw.Draw')
    def test_wrap_text_multiple_lines(self, mock_draw_class, mock_image_new):
        """Test wrapping text that requires multiple lines."""
        mock_draw = Mock()
        mock_draw_class.return_value = mock_draw
        
        # Mock textbbox to return different widths based on text length
        def mock_textbbox(pos, text, font):
            # Simulate that each word is about 50 pixels wide
            word_count = len(text.split())
            return (0, 0, word_count * 50, 20)
        
        mock_draw.textbbox.side_effect = mock_textbbox
        mock_font = Mock(spec=ImageFont.FreeTypeFont)
        
        result = wrap_text("This is a long text that should wrap", mock_font, 150)
        
        # Should wrap into multiple lines since total width would exceed 150px
        assert len(result) > 1
        assert isinstance(result, list)
        assert all(isinstance(line, str) for line in result)
    
    @patch('image_generator.Image.new')
    @patch('image_generator.ImageDraw.Draw')
    def test_wrap_text_single_long_word(self, mock_draw_class, mock_image_new):
        """Test wrapping with a single word that's too long."""
        mock_draw = Mock()
        mock_draw_class.return_value = mock_draw
        mock_draw.textbbox.return_value = (0, 0, 300, 20)  # Word is too long
        
        mock_font = Mock(spec=ImageFont.FreeTypeFont)
        
        result = wrap_text("Supercalifragilisticexpialidocious", mock_font, 100)
        
        # Should force the long word on its own line
        assert result == ["Supercalifragilisticexpialidocious"]
    
    @patch('image_generator.Image.new')
    @patch('image_generator.ImageDraw.Draw')
    def test_wrap_text_empty_string(self, mock_draw_class, mock_image_new):
        """Test wrapping empty string."""
        mock_draw = Mock()
        mock_draw_class.return_value = mock_draw
        mock_font = Mock(spec=ImageFont.FreeTypeFont)
        
        result = wrap_text("", mock_font, 100)
        
        assert result == []


class TestCalculateTextHeight:
    """Test cases for calculate_text_height function."""
    
    def test_calculate_text_height_single_line(self):
        """Test height calculation for single line."""
        mock_font = Mock(spec=ImageFont.FreeTypeFont)
        mock_font.getbbox.return_value = (0, 0, 100, 20)  # height = 20
        
        lines = ["Single line"]
        height = calculate_text_height(lines, mock_font, 1.2)
        
        assert height == 20  # Single line, no spacing
    
    def test_calculate_text_height_multiple_lines(self):
        """Test height calculation for multiple lines."""
        mock_font = Mock(spec=ImageFont.FreeTypeFont)
        mock_font.getbbox.return_value = (0, 0, 100, 20)  # height = 20 per line
        
        lines = ["Line 1", "Line 2", "Line 3"]
        height = calculate_text_height(lines, mock_font, 1.5)
        
        # 3 lines * 20 height + 2 spacings * (20 * 0.5)
        expected_height = 3 * 20 + 2 * (20 * 0.5)
        assert height == expected_height
    
    def test_calculate_text_height_empty_lines(self):
        """Test height calculation for empty lines list."""
        mock_font = Mock(spec=ImageFont.FreeTypeFont)
        
        lines = []
        height = calculate_text_height(lines, mock_font, 1.2)
        
        assert height == 0


class TestGenerateWallpaper:
    """Test cases for generate_wallpaper function."""
    
    @patch('image_generator.load_font')
    @patch('image_generator.wrap_text')
    @patch('image_generator.calculate_text_height')
    @patch('image_generator.Image.new')
    @patch('image_generator.ImageDraw.Draw')
    def test_generate_wallpaper_success(self, mock_draw_class, mock_image_new, 
                                       mock_calc_height, mock_wrap, mock_load_font):
        """Test successful wallpaper generation."""
        # Setup mocks
        mock_font = Mock(spec=ImageFont.FreeTypeFont)
        mock_load_font.return_value = mock_font
        
        mock_wrap.side_effect = [
            ["For God so loved", "the world"],  # verse text wrapped
            ["John 3:16"]  # reference wrapped
        ]
        
        mock_calc_height.side_effect = [100, 30]  # heights for verse and reference
        
        mock_image = Mock()
        mock_image_new.return_value = mock_image
        
        mock_draw = Mock()
        mock_draw.textbbox.return_value = (0, 0, 100, 30)  # Mock textbbox return value
        mock_draw_class.return_value = mock_draw
        
        # Mock the save method to return bytes
        mock_buffer = io.BytesIO()
        mock_image.save = Mock(side_effect=lambda buf, format, **kwargs: buf.write(b'fake_image_data'))
        
        result = generate_wallpaper("For God so loved the world", "John 3:16")
        
        # Verify function calls
        assert mock_load_font.call_count == 2  # Called for main and reference fonts
        assert mock_wrap.call_count >= 1  # Called at least once for verse text
        assert mock_calc_height.call_count >= 1  # Called for verse text (may be called multiple times if text is too tall)
        
        # Verify image creation
        mock_image_new.assert_called_with('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), BACKGROUND_COLOR)
        
        # Verify result is BytesIO
        assert isinstance(result, io.BytesIO)
    
    @patch('image_generator.load_font')
    def test_generate_wallpaper_font_load_failure(self, mock_load_font):
        """Test wallpaper generation when font loading fails."""
        mock_load_font.side_effect = RuntimeError("Font loading failed")
        
        with pytest.raises(RuntimeError):
            generate_wallpaper("Test verse", "Test reference")
    
    @patch('image_generator.load_font')
    @patch('image_generator.wrap_text')
    @patch('image_generator.calculate_text_height')
    @patch('image_generator.Image.new')
    @patch('image_generator.ImageDraw.Draw')
    def test_generate_wallpaper_empty_text(self, mock_draw_class, mock_image_new, mock_calc_height, 
                                          mock_wrap, mock_load_font):
        """Test wallpaper generation with empty text."""
        mock_font = Mock(spec=ImageFont.FreeTypeFont)
        mock_load_font.return_value = mock_font
        
        mock_wrap.side_effect = [[], []]  # Empty wrapped text
        mock_calc_height.side_effect = [0, 0]  # Zero heights
        
        mock_image = Mock()
        mock_image_new.return_value = mock_image
        mock_image.save = Mock(side_effect=lambda buf, format, **kwargs: buf.write(b'fake_image_data'))
        
        mock_draw = Mock()
        mock_draw.textbbox.return_value = (0, 0, 100, 30)  # Mock textbbox return value
        mock_draw_class.return_value = mock_draw
        
        result = generate_wallpaper("", "")
        
        assert isinstance(result, io.BytesIO)


class TestCreateWallpaperFromVerseData:
    """Test cases for create_wallpaper_from_verse_data function."""
    
    @patch('image_generator.generate_wallpaper')
    def test_create_wallpaper_from_verse_data_success(self, mock_generate):
        """Test successful wallpaper creation from verse data."""
        mock_buffer = io.BytesIO(b'fake_image_data')
        mock_generate.return_value = mock_buffer
        
        verse_data = {
            'text': 'For God so loved the world',
            'reference': 'John 3:16'
        }
        
        result = create_wallpaper_from_verse_data(verse_data)
        
        mock_generate.assert_called_once_with('For God so loved the world', 'John 3:16', True)
        assert result == mock_buffer
    
    @patch('image_generator.generate_wallpaper')
    def test_create_wallpaper_from_verse_data_missing_text(self, mock_generate):
        """Test wallpaper creation with missing text field."""
        verse_data = {
            'reference': 'John 3:16'
        }
        
        mock_buffer = io.BytesIO(b'fake_image_data')
        mock_generate.return_value = mock_buffer
        
        result = create_wallpaper_from_verse_data(verse_data)
        
        mock_generate.assert_called_once_with('', 'John 3:16', True)  # Empty text, reference present
        assert result == mock_buffer
    
    @patch('image_generator.generate_wallpaper')
    def test_create_wallpaper_from_verse_data_missing_reference(self, mock_generate):
        """Test wallpaper creation with missing reference field."""
        verse_data = {
            'text': 'For God so loved the world'
        }
        
        mock_buffer = io.BytesIO(b'fake_image_data')
        mock_generate.return_value = mock_buffer
        
        result = create_wallpaper_from_verse_data(verse_data)
        
        mock_generate.assert_called_once_with('For God so loved the world', '', True)  # Text present, empty reference
        assert result == mock_buffer
    
    @patch('image_generator.generate_wallpaper')
    def test_create_wallpaper_from_verse_data_empty_dict(self, mock_generate):
        """Test wallpaper creation with empty dictionary."""
        verse_data = {}
        
        mock_buffer = io.BytesIO(b'fake_image_data')
        mock_generate.return_value = mock_buffer
        
        result = create_wallpaper_from_verse_data(verse_data)
        
        mock_generate.assert_called_once_with('', '', True)  # Both empty strings
        assert result == mock_buffer
    
    @patch('image_generator.generate_wallpaper')
    def test_create_wallpaper_from_verse_data_none_values(self, mock_generate):
        """Test wallpaper creation with None values."""
        mock_buffer = io.BytesIO(b'fake_image_data')
        mock_generate.return_value = mock_buffer
        
        verse_data = {
            'text': None,
            'reference': None
        }
        
        result = create_wallpaper_from_verse_data(verse_data)
        
        mock_generate.assert_called_once_with(None, None, True)
        assert result == mock_buffer


class TestConstants:
    """Test cases for module constants."""
    
    def test_image_dimensions(self):
        """Test that image dimensions are properly defined."""
        assert IMAGE_WIDTH == 1280
        assert IMAGE_HEIGHT == 1280
        assert isinstance(IMAGE_WIDTH, int)
        assert isinstance(IMAGE_HEIGHT, int)
    
    def test_colors(self):
        """Test that colors are properly defined."""
        assert BACKGROUND_COLOR == (0, 0, 0)  # Black
        assert TEXT_COLOR == (255, 255, 255)  # White
        assert len(BACKGROUND_COLOR) == 3
        assert len(TEXT_COLOR) == 3
        assert all(0 <= c <= 255 for c in BACKGROUND_COLOR)
        assert all(0 <= c <= 255 for c in TEXT_COLOR)
    
    def test_font_sizes(self):
        """Test that font sizes are properly defined."""
        assert MAIN_FONT_SIZE == 48
        assert REFERENCE_FONT_SIZE == 32
        assert isinstance(MAIN_FONT_SIZE, int)
        assert isinstance(REFERENCE_FONT_SIZE, int)
        assert MAIN_FONT_SIZE > 0
        assert REFERENCE_FONT_SIZE > 0
    
    def test_font_path(self):
        """Test that font path is properly constructed."""
        assert FONT_PATH.endswith('Montserrat-Light.ttf')
        assert 'assets' in FONT_PATH
        assert 'fonts' in FONT_PATH