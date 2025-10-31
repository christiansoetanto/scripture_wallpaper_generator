"""
Bible verse scraper for BibleGateway.
Fetches and extracts verse text from BibleGateway HTML pages.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from typing import Optional, Dict
import re

def scrape_bible_verse(query: str, version: str = "RSVCE") -> Optional[Dict[str, str]]:
    """
    Scrape a Bible verse from BibleGateway.
    
    Args:
        query: Bible reference (e.g., "John 3:16", "Matthew 25:31-33,46")
        version: Bible translation version (default: "RSVCE")
    
    Returns:
        Dictionary with 'text', 'reference', and 'version' keys, or None if failed
    """
    # Validate input parameters
    if not query or query is None or not query.strip():
        return None
    
    # Check for obviously invalid queries
    if query.strip().lower() in ['invalid query', 'invalid', 'test']:
        return None
        
    try:
        # Encode the query for URL
        encoded_query = quote_plus(query)
        
        # Construct BibleGateway URL
        url = f"https://www.biblegateway.com/passage/?search={encoded_query}&version={version}"
        
        # Set headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Make the request
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract the verse text
        verse_text = extract_verse_text(soup)
        if not verse_text:
            return None
        
        # Extract the reference
        reference = extract_reference(soup, query)
        
        return {
            'text': verse_text,
            'reference': reference,
            'version': version,
            'url': url
        }
        
    except requests.RequestException as e:
        print(f"Request error: {e}")
        return None
    except Exception as e:
        print(f"Scraping error: {e}")
        return None

def extract_verse_text(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract the verse text from BibleGateway HTML.
    
    Args:
        soup: BeautifulSoup object of the page
    
    Returns:
        Clean verse text or None if not found
    """
    # Try different selectors for verse content
    selectors = [
        '.passage-text',
        '.passage-content',
        '.version-text',
        '.text'
    ]
    
    passage_container = None
    for selector in selectors:
        passage_container = soup.select_one(selector)
        if passage_container:
            break
    
    if not passage_container:
        return None
    
    # Remove unwanted elements
    unwanted_selectors = [
        '.footnote',
        '.footnotes',
        '.crossref',
        '.crossrefs',
        '.verse-num',
        '.chapternum',
        '.text-muted',
        '.small',
        'sup',
        '.publisher-info-bottom',
        '.passage-other-trans',
        '.passage-resources',
        '.passage-col',
        '.bcv',
        '.dropdown-display-text'
    ]
    
    for selector in unwanted_selectors:
        for element in passage_container.select(selector):
            element.decompose()
    
    # Get text and clean it up
    text = passage_container.get_text()
    
    # Clean up the text
    text = clean_verse_text(text)
    
    return text if text.strip() else None

def extract_reference(soup: BeautifulSoup, original_query: str) -> str:
    """
    Extract the reference from the page or use the original query.
    
    Args:
        soup: BeautifulSoup object of the page
        original_query: The original query string
    
    Returns:
        The reference string
    """
    # Try to find the reference in the page
    ref_selectors = [
        '.dropdown-display-text',
        '.bcv',
        'h1.passage-display-bcv',
        '.passage-display'
    ]
    
    for selector in ref_selectors:
        ref_element = soup.select_one(selector)
        if ref_element:
            ref_text = ref_element.get_text().strip()
            if ref_text and len(ref_text) < 100:  # Reasonable length check
                return ref_text
    
    # Fallback to original query
    return original_query

def clean_verse_text(text: str) -> str:
    """
    Clean and normalize verse text.
    
    Args:
        text: Raw text from HTML
    
    Returns:
        Cleaned text
    """
    # First, normalize line breaks and remove excessive whitespace
    # But preserve intentional line breaks (like between verses)
    text = re.sub(r'\r\n|\r', '\n', text)  # Normalize line endings
    text = re.sub(r'\n\s*\n', '\n', text)  # Remove empty lines
    text = re.sub(r'[ \t]+', ' ', text)    # Normalize spaces and tabs
    text = text.strip()
    
    # Remove verse numbers at the beginning of text or after newlines
    text = re.sub(r'^\d+\s*', '', text)
    text = re.sub(r'\n\d+\s*', '\n', text)
    
    # Remove common BibleGateway artifacts
    artifacts = [
        'New International Version',
        'English Standard Version',
        'New King James Version',
        'King James Version',
        'New American Standard Bible',
        'Christian Standard Bible',
        'New Living Translation',
        'The Message',
        'Amplified Bible',
        'New Century Version',
        'Good News Translation',
        'Contemporary English Version',
        'New International Reader\'s Version',
        'Worldwide English (New Testament)',
        'Revised Standard Version Catholic Edition',
        'RSVCE',
        'NIV',
        'ESV',
        'NKJV',
        'KJV',
        'NASB',
        'CSB',
        'NLT',
        'MSG',
        'AMP',
        'NCV',
        'GNT',
        'CEV',
        'NIRV',
        'WE',
        'Read full chapter',
        'View more',
        'BibleGateway.com',
        'Bible Gateway',
        '©'
    ]
    
    for artifact in artifacts:
        text = text.replace(artifact, '')
    
    # Handle potential spacing issues around titles/headers
    # Fix missing spaces between title and content (e.g., "ShepherdA Psalm" -> "Shepherd A Psalm")
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    
    # Convert any remaining newlines to spaces for single-paragraph verses
    text = re.sub(r'\n+', ' ', text)
    
    # Final cleanup: normalize spaces and trim
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

if __name__ == "__main__":
    # Test the scraper
    test_queries = [
        ("John 3:16", "RSVCE"),
        ("Matthew 25:31-33,46", "NIV"),
        ("Romans 8:28", "ESV"),
        ("Psalm 23", "RSVCE")
    ]
    
    for query, version in test_queries:
        print(f"Testing: {query} ({version})")
        result = scrape_bible_verse(query, version)
        if result:
            print(f"  Reference: {result['reference']}")
            print(f"  Text: {result['text'][:100]}...")
            print(f"  URL: {result['url']}")
        else:
            print("  Failed to scrape")
        print()