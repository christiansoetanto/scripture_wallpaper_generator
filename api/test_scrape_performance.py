#!/usr/bin/env python3
"""
Performance test for Bible scraping to identify bottlenecks.
"""

import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from bible_scraper import scrape_bible_verse, extract_verse_text, extract_reference

def test_scrape_performance(query: str, version: str = "RSVCE"):
    """Test the performance of different scraping components."""
    print(f"\n=== Testing: {query} ({version}) ===")
    
    # Total time
    total_start = time.time()
    
    # URL encoding time
    encode_start = time.time()
    encoded_query = quote_plus(query)
    url = f"https://www.biblegateway.com/passage/?search={encoded_query}&version={version}"
    encode_time = time.time() - encode_start
    
    # HTTP request time
    request_start = time.time()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        request_time = time.time() - request_start
        
        # HTML parsing time
        parse_start = time.time()
        soup = BeautifulSoup(response.content, 'html.parser')
        parse_time = time.time() - parse_start
        
        # Text extraction time
        extract_start = time.time()
        verse_text = extract_verse_text(soup)
        reference = extract_reference(soup, query)
        extract_time = time.time() - extract_start
        
        total_time = time.time() - total_start
        
        # Results
        print(f"URL Encoding: {encode_time*1000:.2f}ms")
        print(f"HTTP Request: {request_time*1000:.2f}ms")
        print(f"HTML Parsing: {parse_time*1000:.2f}ms")
        print(f"Text Extraction: {extract_time*1000:.2f}ms")
        print(f"Total Time: {total_time*1000:.2f}ms")
        print(f"Response Size: {len(response.content)} bytes")
        
        if verse_text:
            print(f"Success: {reference}")
            print(f"Text: {verse_text[:100]}...")
        else:
            print("Failed to extract verse text")
            
    except requests.RequestException as e:
        request_time = time.time() - request_start
        print(f"Request failed after {request_time*1000:.2f}ms: {e}")
    except Exception as e:
        print(f"Error: {e}")

def test_multiple_verses():
    """Test performance across multiple verses."""
    test_verses = [
        ("John 3:16", "RSVCE"),
        ("Psalm 23:1", "NIV"),
        ("Romans 8:28", "ESV"),
        ("Matthew 5:3-4", "RSVCE")
    ]
    
    print("=== Bible Scraping Performance Test ===")
    
    for query, version in test_verses:
        test_scrape_performance(query, version)
        time.sleep(1)  # Be respectful to the server

if __name__ == "__main__":
    test_multiple_verses()