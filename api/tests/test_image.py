import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO
import json

# Add the parent directory to the path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from image import handler


class TestImageHandler:
    """Test cases for the handler class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create a mock handler instance with proper initialization
        # BaseHTTPRequestHandler requires request, client_address, and server
        mock_request = Mock()
        mock_client_address = ('127.0.0.1', 12345)
        mock_server = Mock()
        
        # Mock the handler initialization to avoid BaseHTTPRequestHandler issues
        with patch('image.handler.__init__', return_value=None):
            self.handler = handler.__new__(handler)
        
        # Mock the required methods and attributes
        self.handler.wfile = Mock()
        self.handler.send_response = Mock()
        self.handler.send_header = Mock()
        self.handler.end_headers = Mock()
    
    @patch('image.create_wallpaper_from_verse_data')
    @patch('image.scrape_bible_verse')
    @patch('image.format_for_biblegateway')
    @patch('image.generate_filename')
    def test_do_GET_success(self, mock_filename, mock_format, mock_scrape, mock_create):
        """Test successful GET request with valid parameters."""
        # Mock the path and query
        self.handler.path = "/?q=John%203:16&version=RSVCE"
        
        # Mock the formatting and scraping
        mock_format.return_value = "John+3:16"
        mock_scrape.return_value = {
            'text': 'For God so loved the world...',
            'reference': 'John 3:16',
            'version': 'RSVCE'
        }
        mock_filename.return_value = "John_3_16.jpg"
        
        # Mock image creation - return a BytesIO object
        mock_buffer = BytesIO(b"fake_image_data")
        mock_create.return_value = mock_buffer
        
        # Execute the request
        self.handler.do_GET()
        
        # Verify the response
        self.handler.send_response.assert_called_with(200)
        self.handler.send_header.assert_any_call('Content-Type', 'image/jpeg')
        self.handler.send_header.assert_any_call('Content-Disposition', 'attachment; filename="John_3_16.jpg"')
        self.handler.send_header.assert_any_call('Content-Length', str(len(mock_buffer.getvalue())))
        self.handler.send_header.assert_any_call('Access-Control-Allow-Origin', '*')
        self.handler.end_headers.assert_called_once()
        self.handler.wfile.write.assert_called_with(mock_buffer.getvalue())
    
    def test_do_GET_missing_q_parameter(self):
        """Test GET request with missing q parameter."""
        self.handler.path = "/?version=RSVCE"
        
        self.handler.do_GET()
        
        # Should send error response
        self.handler.send_response.assert_called_with(400)
        self.handler.send_header.assert_any_call('Content-Type', 'application/json')
        self.handler.end_headers.assert_called_once()
        
        # Check that error message was written
        written_data = b''.join(call.args[0] for call in self.handler.wfile.write.call_args_list)
        error_response = json.loads(written_data.decode())
        assert error_response['error'] == "Missing required parameter 'q' (Bible reference)"
    
    @patch('image.format_for_biblegateway')
    def test_do_GET_invalid_verse_format(self, mock_format):
        """Test GET request with invalid verse format."""
        self.handler.path = "/?q=invalid&version=RSVCE"
        mock_format.return_value = None
        
        self.handler.do_GET()
        
        # Should send error response
        self.handler.send_response.assert_called_with(400)
        self.handler.send_header.assert_any_call('Content-Type', 'application/json')
        self.handler.end_headers.assert_called_once()
        
        # Check that error message was written
        written_data = b''.join(call.args[0] for call in self.handler.wfile.write.call_args_list)
        error_response = json.loads(written_data.decode())
        assert error_response['error'] == "Could not parse Bible reference: 'invalid'"
    
    @patch('image.scrape_bible_verse')
    @patch('image.format_for_biblegateway')
    def test_do_GET_verse_not_found(self, mock_format, mock_scrape):
        """Test GET request when verse is not found."""
        self.handler.path = "/?q=John%203:16&version=RSVCE"
        mock_format.return_value = "John+3:16"
        mock_scrape.return_value = None
        
        self.handler.do_GET()
        
        # Should send error response
        self.handler.send_response.assert_called_with(500)
        self.handler.send_header.assert_any_call('Content-Type', 'application/json')
        self.handler.end_headers.assert_called_once()
        
        # Check that error message was written
        written_data = b''.join(call.args[0] for call in self.handler.wfile.write.call_args_list)
        error_response = json.loads(written_data.decode())
        assert error_response['error'] == "Failed to fetch verse: 'John+3:16' (RSVCE)"
    
    @patch('image.create_wallpaper_from_verse_data')
    @patch('image.scrape_bible_verse')
    @patch('image.format_for_biblegateway')
    def test_do_GET_image_generation_error(self, mock_format, mock_scrape, mock_create):
        """Test GET request when image generation fails."""
        self.handler.path = "/?q=John%203:16&version=RSVCE"
        mock_format.return_value = "John+3:16"
        mock_scrape.return_value = {
            'text': 'For God so loved the world...',
            'reference': 'John 3:16',
            'version': 'RSVCE'
        }
        mock_create.side_effect = Exception("Image generation failed")
        
        self.handler.do_GET()
        
        # Should send error response
        self.handler.send_response.assert_called_with(500)
        self.handler.send_header.assert_any_call('Content-Type', 'application/json')
        self.handler.end_headers.assert_called_once()
        
        # Check that error message was written
        written_data = b''.join(call.args[0] for call in self.handler.wfile.write.call_args_list)
        error_response = json.loads(written_data.decode())
        assert error_response['error'] == 'Internal server error: Image generation failed'
    
    @patch('image.create_wallpaper_from_verse_data')
    @patch('image.scrape_bible_verse')
    @patch('image.format_for_biblegateway')
    @patch('image.generate_filename')
    def test_do_GET_with_different_version(self, mock_filename, mock_format, mock_scrape, mock_create):
        """Test GET request with different Bible version."""
        self.handler.path = "/?q=John%203:16&version=NIV"
        mock_format.return_value = "John+3:16"
        mock_scrape.return_value = {
            'text': 'For God so loved the world...',
            'reference': 'John 3:16',
            'version': 'NIV'
        }
        mock_filename.return_value = "John_3_16.jpg"
        
        # Mock image creation
        mock_buffer = BytesIO(b"fake_image_data")
        mock_create.return_value = mock_buffer
        
        self.handler.do_GET()
        
        # Verify that scrape_bible_verse was called with NIV version
        mock_scrape.assert_called_with("John+3:16", "NIV")
        
        # Verify successful response
        self.handler.send_response.assert_called_with(200)
    
    def test_do_GET_with_default_version(self):
        """Test GET request with default version when not specified."""
        with patch('image.format_for_biblegateway') as mock_format, \
             patch('image.scrape_bible_verse') as mock_scrape, \
             patch('image.create_wallpaper_from_verse_data') as mock_create, \
             patch('image.generate_filename') as mock_filename:
            
            self.handler.path = "/?q=John%203:16"
            mock_format.return_value = "John+3:16"
            mock_scrape.return_value = {
                'text': 'For God so loved the world...',
                'reference': 'John 3:16',
                'version': 'RSVCE'
            }
            mock_filename.return_value = "John_3_16.jpg"
            mock_buffer = BytesIO(b"fake_image_data")
            mock_create.return_value = mock_buffer
            
            self.handler.do_GET()
            
            # Verify that scrape_bible_verse was called with default RSVCE version
            mock_scrape.assert_called_with("John+3:16", "RSVCE")
    
    def test_do_OPTIONS(self):
        """Test OPTIONS request for CORS preflight."""
        self.handler.do_OPTIONS()
        
        # Verify CORS headers are set
        self.handler.send_response.assert_called_with(200)
        self.handler.send_header.assert_any_call('Access-Control-Allow-Origin', '*')
        self.handler.send_header.assert_any_call('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.handler.send_header.assert_any_call('Access-Control-Allow-Headers', 'Content-Type')
        self.handler.end_headers.assert_called_once()
    
    def test_send_error_response(self):
        """Test the send_error_response method."""
        self.handler.send_error_response(404, "Not found")
        
        # Verify error response
        self.handler.send_response.assert_called_with(404)
        self.handler.send_header.assert_any_call('Content-Type', 'application/json')
        self.handler.send_header.assert_any_call('Access-Control-Allow-Origin', '*')
        self.handler.end_headers.assert_called_once()
        
        # Check that error message was written
        written_data = b''.join(call.args[0] for call in self.handler.wfile.write.call_args_list)
        error_response = json.loads(written_data.decode())
        assert error_response['error'] == 'Not found'
    
    @patch('image.create_wallpaper_from_verse_data')
    @patch('image.scrape_bible_verse')
    @patch('image.format_for_biblegateway')
    @patch('image.generate_filename')
    def test_do_GET_url_decoding(self, mock_filename, mock_format, mock_scrape, mock_create):
        """Test that URL-encoded verse parameters are properly decoded."""
        # Test with URL-encoded verse (spaces become %20)
        self.handler.path = "/?q=1%20John%203:16&version=RSVCE"
        mock_format.return_value = "1+John+3:16"
        mock_scrape.return_value = {
            'text': 'And this is his command...',
            'reference': '1 John 3:16',
            'version': 'RSVCE'
        }
        mock_filename.return_value = "1_John_3_16.jpg"
        mock_buffer = BytesIO(b"fake_image_data")
        mock_create.return_value = mock_buffer
        
        self.handler.do_GET()
        
        # Verify that format_for_biblegateway was called with decoded verse
        mock_format.assert_called_with("1 John 3:16")
    
    @patch('image.create_wallpaper_from_verse_data')
    @patch('image.scrape_bible_verse')
    @patch('image.format_for_biblegateway')
    @patch('image.generate_filename')
    def test_do_GET_verse_range(self, mock_filename, mock_format, mock_scrape, mock_create):
        """Test GET request with verse range."""
        self.handler.path = "/?q=John%203:16-17&version=RSVCE"
        mock_format.return_value = "John+3:16-17"
        mock_scrape.return_value = {
            'text': 'For God so loved the world... For God did not send...',
            'reference': 'John 3:16-17',
            'version': 'RSVCE'
        }
        mock_filename.return_value = "John_3_16-17.jpg"
        mock_buffer = BytesIO(b"fake_image_data")
        mock_create.return_value = mock_buffer
        
        self.handler.do_GET()
        
        # Verify successful response
        self.handler.send_response.assert_called_with(200)
        self.handler.wfile.write.assert_called_with(mock_buffer.getvalue())
        
        # Verify filename generation for verse range
        self.handler.send_header.assert_any_call('Content-Disposition', 'attachment; filename="John_3_16-17.jpg"')