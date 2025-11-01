import pytest
import sys
import os
import json
import time
from unittest.mock import Mock, patch, MagicMock
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import threading
import subprocess
import requests

# Add the parent directory to the path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from image import handler


class TestTextEditorIntegration:
    """Integration tests for the text editor functionality."""
    
    @classmethod
    def setup_class(cls):
        """Set up test environment before running tests."""
        cls.frontend_server = None
        cls.api_server = None
        cls.driver = None
        
        # Start frontend server
        cls.start_frontend_server()
        
        # Start API server
        cls.start_api_server()
        
        # Set up Chrome driver
        cls.setup_webdriver()
        
        # Wait for servers to be ready
        time.sleep(3)
    
    @classmethod
    def teardown_class(cls):
        """Clean up after all tests."""
        if cls.driver:
            cls.driver.quit()
        if cls.frontend_server:
            cls.frontend_server.terminate()
        if cls.api_server:
            cls.api_server.terminate()
    
    @classmethod
    def start_frontend_server(cls):
        """Start the frontend HTTP server."""
        try:
            cls.frontend_server = subprocess.Popen(
                ['python3', '-m', 'http.server', '3001'],
                cwd=os.path.join(os.path.dirname(os.path.dirname(__file__)), '..'),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except Exception as e:
            print(f"Failed to start frontend server: {e}")
    
    @classmethod
    def start_api_server(cls):
        """Start the API server."""
        try:
            cls.api_server = subprocess.Popen(
                ['python3', 'image.py'],
                cwd=os.path.dirname(os.path.dirname(__file__)),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except Exception as e:
            print(f"Failed to start API server: {e}")
    
    @classmethod
    def setup_webdriver(cls):
        """Set up Chrome WebDriver for testing."""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Run in headless mode
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.driver.implicitly_wait(10)
        except Exception as e:
            print(f"Failed to setup WebDriver: {e}")
            # Fallback to non-headless mode for debugging
            try:
                cls.driver = webdriver.Chrome()
                cls.driver.implicitly_wait(10)
            except Exception as e2:
                print(f"Failed to setup WebDriver in non-headless mode: {e2}")
                cls.driver = None
    
    def test_page_loads_successfully(self):
        """Test that the main page loads without errors."""
        if not self.driver:
            pytest.skip("WebDriver not available")
        
        self.driver.get("http://localhost:3001")
        
        # Check that the page title is correct
        assert "Scripture Wallpaper Generator" in self.driver.title
        
        # Check that key elements are present
        canvas = self.driver.find_element(By.ID, "wallpaper-canvas")
        assert canvas is not None
        
        verse_input = self.driver.find_element(By.ID, "canvas-verse-input")
        assert verse_input is not None
        
        fetch_btn = self.driver.find_element(By.ID, "fetch-verse-btn")
        assert fetch_btn is not None
    
    def test_text_editor_initially_hidden(self):
        """Test that the text editor is initially hidden."""
        if not self.driver:
            pytest.skip("WebDriver not available")
        
        self.driver.get("http://localhost:3001")
        
        # Text editor section should be hidden initially
        text_editor_section = self.driver.find_element(By.ID, "text-editor-section")
        assert not text_editor_section.is_displayed()
    
    @patch('image.scrape_bible_verse')
    def test_verse_fetch_shows_text_editor(self, mock_scrape):
        """Test that fetching a verse shows the text editor."""
        if not self.driver:
            pytest.skip("WebDriver not available")
        
        # Mock the verse scraping
        mock_scrape.return_value = {
            'text': 'For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life.',
            'reference': 'John 3:16',
            'version': 'RSVCE'
        }
        
        self.driver.get("http://localhost:3001")
        
        # Enter a verse reference
        verse_input = self.driver.find_element(By.ID, "canvas-verse-input")
        verse_input.clear()
        verse_input.send_keys("John 3:16")
        
        # Click fetch button
        fetch_btn = self.driver.find_element(By.ID, "fetch-verse-btn")
        fetch_btn.click()
        
        # Wait for the text editor to become visible
        wait = WebDriverWait(self.driver, 10)
        text_editor_section = wait.until(
            EC.visibility_of_element_located((By.ID, "text-editor-section"))
        )
        
        # Check that text editor is now visible
        assert text_editor_section.is_displayed()
        
        # Check that text editor contains the verse text
        text_editor = self.driver.find_element(By.ID, "verse-text-editor")
        assert "For God so loved the world" in text_editor.get_attribute("value")
    
    def test_text_editor_positioning(self):
        """Test that the text editor is positioned correctly below the canvas."""
        if not self.driver:
            pytest.skip("WebDriver not available")
        
        self.driver.get("http://localhost:3001")
        
        # Get canvas position
        canvas_container = self.driver.find_element(By.CLASS_NAME, "canvas-preview-container")
        canvas_rect = canvas_container.rect
        
        # Simulate verse fetch to show text editor
        verse_input = self.driver.find_element(By.ID, "canvas-verse-input")
        verse_input.send_keys("John 3:16")
        
        fetch_btn = self.driver.find_element(By.ID, "fetch-verse-btn")
        fetch_btn.click()
        
        # Wait for text editor to appear
        wait = WebDriverWait(self.driver, 10)
        text_editor_section = wait.until(
            EC.visibility_of_element_located((By.ID, "text-editor-section"))
        )
        
        # Get text editor position
        editor_rect = text_editor_section.rect
        
        # Text editor should be below the canvas
        assert editor_rect['y'] > canvas_rect['y'] + canvas_rect['height']
    
    def test_real_time_text_editing(self):
        """Test that editing text in the editor updates the canvas in real-time."""
        if not self.driver:
            pytest.skip("WebDriver not available")
        
        self.driver.get("http://localhost:3001")
        
        # Fetch a verse first
        verse_input = self.driver.find_element(By.ID, "canvas-verse-input")
        verse_input.send_keys("John 3:16")
        
        fetch_btn = self.driver.find_element(By.ID, "fetch-verse-btn")
        fetch_btn.click()
        
        # Wait for text editor to appear
        wait = WebDriverWait(self.driver, 10)
        text_editor = wait.until(
            EC.visibility_of_element_located((By.ID, "verse-text-editor"))
        )
        
        # Get initial canvas state
        canvas = self.driver.find_element(By.ID, "wallpaper-canvas")
        initial_canvas_data = self.driver.execute_script(
            "return arguments[0].toDataURL();", canvas
        )
        
        # Edit the text
        text_editor.clear()
        text_editor.send_keys("This is edited text for testing.")
        
        # Wait a moment for the canvas to update
        time.sleep(1)
        
        # Get updated canvas state
        updated_canvas_data = self.driver.execute_script(
            "return arguments[0].toDataURL();", canvas
        )
        
        # Canvas should have changed
        assert initial_canvas_data != updated_canvas_data
    
    def test_canvas_reset_hides_text_editor(self):
        """Test that resetting the canvas hides the text editor."""
        if not self.driver:
            pytest.skip("WebDriver not available")
        
        self.driver.get("http://localhost:3001")
        
        # Fetch a verse to show text editor
        verse_input = self.driver.find_element(By.ID, "canvas-verse-input")
        verse_input.send_keys("John 3:16")
        
        fetch_btn = self.driver.find_element(By.ID, "fetch-verse-btn")
        fetch_btn.click()
        
        # Wait for text editor to appear
        wait = WebDriverWait(self.driver, 10)
        text_editor_section = wait.until(
            EC.visibility_of_element_located((By.ID, "text-editor-section"))
        )
        
        # Verify text editor is visible
        assert text_editor_section.is_displayed()
        
        # Click reset button
        reset_btn = self.driver.find_element(By.ID, "reset-canvas-btn")
        reset_btn.click()
        
        # Wait for text editor to be hidden
        wait.until(EC.invisibility_of_element_located((By.ID, "text-editor-section")))
        
        # Verify text editor is now hidden
        assert not text_editor_section.is_displayed()
    
    def test_text_editor_preserves_formatting(self):
        """Test that the text editor preserves line breaks and formatting."""
        if not self.driver:
            pytest.skip("WebDriver not available")
        
        self.driver.get("http://localhost:3001")
        
        # Fetch a verse
        verse_input = self.driver.find_element(By.ID, "canvas-verse-input")
        verse_input.send_keys("John 3:16")
        
        fetch_btn = self.driver.find_element(By.ID, "fetch-verse-btn")
        fetch_btn.click()
        
        # Wait for text editor
        wait = WebDriverWait(self.driver, 10)
        text_editor = wait.until(
            EC.visibility_of_element_located((By.ID, "verse-text-editor"))
        )
        
        # Add text with line breaks
        multiline_text = "Line 1\nLine 2\nLine 3"
        text_editor.clear()
        text_editor.send_keys(multiline_text)
        
        # Verify the text is preserved
        editor_value = text_editor.get_attribute("value")
        assert "Line 1" in editor_value
        assert "Line 2" in editor_value
        assert "Line 3" in editor_value
    
    def test_multiple_bible_versions(self):
        """Test text editor functionality with different Bible versions."""
        if not self.driver:
            pytest.skip("WebDriver not available")
        
        self.driver.get("http://localhost:3001")
        
        # Test with different versions
        versions = ["RSVCE", "ESV", "NABRE"]
        
        for version in versions:
            # Select version
            version_select = self.driver.find_element(By.ID, "canvas-version-select")
            version_select.send_keys(version)
            
            # Enter verse
            verse_input = self.driver.find_element(By.ID, "canvas-verse-input")
            verse_input.clear()
            verse_input.send_keys("John 3:16")
            
            # Fetch verse
            fetch_btn = self.driver.find_element(By.ID, "fetch-verse-btn")
            fetch_btn.click()
            
            # Wait for text editor
            wait = WebDriverWait(self.driver, 10)
            text_editor = wait.until(
                EC.visibility_of_element_located((By.ID, "verse-text-editor"))
            )
            
            # Verify text editor has content
            assert len(text_editor.get_attribute("value")) > 0
            
            # Reset for next iteration
            reset_btn = self.driver.find_element(By.ID, "reset-canvas-btn")
            reset_btn.click()
            time.sleep(1)


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])