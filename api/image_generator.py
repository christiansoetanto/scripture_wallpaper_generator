"""
Image generator for Bible verse wallpapers.
Creates 1280x1280 JPEG images with centered text using Montserrat Light font.
"""

import os
from PIL import Image, ImageDraw, ImageFont
from typing import Tuple, List
import textwrap
import io

# Image dimensions
IMAGE_WIDTH = 1080  # Samsung Galaxy S25 width
IMAGE_HEIGHT = 2340  # Samsung Galaxy S25 height
BACKGROUND_COLOR = (0, 0, 0)  # Black background
TEXT_COLOR = (255, 255, 255)  # White text

# Font settings - increased for better readability on mobile
FONT_PATH = os.path.join(os.path.dirname(__file__), 'assets', 'fonts', 'Montserrat-Light.ttf')
MAIN_FONT_SIZE = 64  # Increased from 48 for better mobile readability
REFERENCE_FONT_SIZE = 42  # Increased from 32 for better mobile readability

# Layout settings
MARGIN = 80  # Margin from edges
LINE_SPACING = 1.3  # Line spacing for readability
SPACING_BETWEEN_VERSE_AND_REFERENCE = 40  # Space between verse and reference

# Text boundary settings (based on 14.5cm phone height, text area 5.5-10cm)
# Default boundaries: 5.5cm = ~890px, 10cm = ~1620px (at 162 DPI)
DEFAULT_TOP_BOUNDARY = 890  # pixels from top
DEFAULT_BOTTOM_BOUNDARY = 1620  # pixels from top
BOUNDARY_MARGIN = 40  # Additional margin inside boundaries

def load_font(size: int) -> ImageFont.FreeTypeFont:
    """
    Load the Montserrat Light font at the specified size.
    
    Args:
        size: Font size in pixels
        
    Returns:
        ImageFont.FreeTypeFont: The loaded font
        
    Raises:
        RuntimeError: If Montserrat Light font cannot be loaded
    """
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except (OSError, IOError) as e:
        raise RuntimeError(f"Failed to load Montserrat Light font from {FONT_PATH}: {e}")

def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    """
    Wrap text to fit within the specified width.
    
    Args:
        text: Text to wrap
        font: Font to use for measuring
        max_width: Maximum width in pixels
    
    Returns:
        List of wrapped lines
    """
    # Create a temporary image to measure text
    temp_img = Image.new('RGB', (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        # Test if adding this word would exceed the width
        test_line = ' '.join(current_line + [word])
        bbox = temp_draw.textbbox((0, 0), test_line, font=font)
        text_width = bbox[2] - bbox[0]
        
        if text_width <= max_width:
            current_line.append(word)
        else:
            # If current line is not empty, save it and start a new line
            if current_line:
                lines.append(' '.join(current_line))
                current_line = [word]
            else:
                # Single word is too long, force it on its own line
                lines.append(word)
    
    # Add the last line if it's not empty
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

def calculate_text_height(lines: List[str], font: ImageFont.FreeTypeFont, line_spacing: float) -> int:
    """
    Calculate the total height of wrapped text.
    
    Args:
        lines: List of text lines
        font: Font to use for measuring
        line_spacing: Line spacing multiplier
    
    Returns:
        Total height in pixels
    """
    if not lines:
        return 0
    
    # Create a temporary image to measure text
    temp_img = Image.new('RGB', (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    
    # Get the height of a single line
    bbox = temp_draw.textbbox((0, 0), lines[0], font=font)
    line_height = bbox[3] - bbox[1]
    
    # Calculate total height with line spacing
    total_height = line_height * len(lines)
    if len(lines) > 1:
        total_height += line_height * (line_spacing - 1) * (len(lines) - 1)
    
    return int(total_height)

def generate_wallpaper(verse_text: str, reference: str, top_boundary: int = DEFAULT_TOP_BOUNDARY, bottom_boundary: int = DEFAULT_BOTTOM_BOUNDARY) -> io.BytesIO:
    """
    Generate a wallpaper image with the given verse text and reference.
    Uses specified top and bottom boundaries for text positioning.
    
    Args:
        verse_text: The Bible verse text
        reference: The Bible reference (e.g., "John 3:16")
        top_boundary: Top boundary for text area in pixels from top of image
        bottom_boundary: Bottom boundary for text area in pixels from top of image
    
    Returns:
        BytesIO object containing the JPEG image data
    """
    # Create the image
    img = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Load fonts
    main_font = load_font(MAIN_FONT_SIZE)
    reference_font = load_font(REFERENCE_FONT_SIZE)
    
    # Calculate available space for text using boundaries
    available_width = IMAGE_WIDTH - (2 * MARGIN)
    text_area_top = top_boundary + BOUNDARY_MARGIN
    text_area_bottom = bottom_boundary - BOUNDARY_MARGIN
    available_height = text_area_bottom - text_area_top
    
    # Get reference dimensions
    ref_bbox = draw.textbbox((0, 0), reference, font=reference_font)
    ref_height = ref_bbox[3] - ref_bbox[1]
    
    # Wrap the main text
    wrapped_lines = wrap_text(verse_text, main_font, available_width)
    
    # Calculate text height
    text_height = calculate_text_height(wrapped_lines, main_font, LINE_SPACING)
    
    # Total content height (verse + spacing + reference)
    total_content_height = text_height + SPACING_BETWEEN_VERSE_AND_REFERENCE + ref_height
    
    # If content is too tall, try smaller font sizes
    current_font_size = MAIN_FONT_SIZE
    while total_content_height > available_height and current_font_size > 20:
        current_font_size -= 2
        main_font = load_font(current_font_size)
        wrapped_lines = wrap_text(verse_text, main_font, available_width)
        text_height = calculate_text_height(wrapped_lines, main_font, LINE_SPACING)
        total_content_height = text_height + SPACING_BETWEEN_VERSE_AND_REFERENCE + ref_height
    
    # Calculate starting Y position to center content within boundaries
    start_y = text_area_top + (available_height - total_content_height) // 2
    
    # Draw the main text
    current_y = start_y
    
    # Get line height once (all lines should have the same height with the same font)
    if wrapped_lines:
        bbox = draw.textbbox((0, 0), wrapped_lines[0], font=main_font)
        line_height = bbox[3] - bbox[1]
    
    for i, line in enumerate(wrapped_lines):
        # Get line dimensions for centering
        bbox = draw.textbbox((0, 0), line, font=main_font)
        line_width = bbox[2] - bbox[0]
        
        # Center horizontally
        x = (IMAGE_WIDTH - line_width) // 2
        
        # Draw the line
        draw.text((x, current_y), line, font=main_font, fill=TEXT_COLOR)
        
        # Move to next line (add line height + spacing, but not for the last line)
        if i < len(wrapped_lines) - 1:
            current_y += line_height + int(line_height * (LINE_SPACING - 1))
        else:
            current_y += line_height
    
    # Draw the reference below the verse text
    ref_bbox = draw.textbbox((0, 0), reference, font=reference_font)
    ref_width = ref_bbox[2] - ref_bbox[0]
    ref_x = (IMAGE_WIDTH - ref_width) // 2
    ref_y = current_y + SPACING_BETWEEN_VERSE_AND_REFERENCE
    
    draw.text((ref_x, ref_y), reference, font=reference_font, fill=TEXT_COLOR)
    
    # Save to BytesIO
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='JPEG', quality=90, optimize=True)
    img_buffer.seek(0)
    
    return img_buffer

def create_wallpaper_from_verse_data(verse_data: dict, top_boundary: int = DEFAULT_TOP_BOUNDARY, bottom_boundary: int = DEFAULT_BOTTOM_BOUNDARY) -> io.BytesIO:
    """
    Create a wallpaper from verse data dictionary.
    
    Args:
        verse_data: Dictionary with 'text' and 'reference' keys
        top_boundary: Top boundary for text area in pixels from top of image
        bottom_boundary: Bottom boundary for text area in pixels from top of image
    
    Returns:
        BytesIO object containing the JPEG image data
    """
    verse_text = verse_data.get('text', '')
    reference = verse_data.get('reference', '')
    
    return generate_wallpaper(verse_text, reference, top_boundary, bottom_boundary)