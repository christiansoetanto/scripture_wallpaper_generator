#!/usr/bin/env python3
"""
Test potential optimizations for Bible scraping performance.
"""

import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import concurrent.futures
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_optimized_session():
    """Create a requests session with optimizations."""
    session = requests.Session()
    
    # Connection pooling and keep-alive
    adapter = HTTPAdapter(
        pool_connections=10,
        pool_maxsize=20,
        max_retries=Retry(
            total=2,
            backoff_factor=0.1,
            status_forcelist=[500, 502, 503, 504]
        )
    )
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    # Optimized headers
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    
    return session

def test_with_session_reuse():
    """Test performance with session reuse."""
    print("\n=== Testing with Session Reuse ===")
    
    session = create_optimized_session()
    verses = [
        ("John 3:16", "RSVCE"),
        ("Psalm 23:1", "NIV"),
        ("Romans 8:28", "ESV")
    ]
    
    total_start = time.time()
    
    for query, version in verses:
        start = time.time()
        
        try:
            encoded_query = quote_plus(query)
            url = f"https://www.biblegateway.com/passage/?search={encoded_query}&version={version}"
            
            response = session.get(url, timeout=8)
            response.raise_for_status()
            
            request_time = time.time() - start
            print(f"{query} ({version}): {request_time*1000:.2f}ms - {len(response.content)} bytes")
            
        except Exception as e:
            request_time = time.time() - start
            print(f"{query} ({version}): FAILED after {request_time*1000:.2f}ms - {e}")
        
        time.sleep(0.5)  # Small delay between requests
    
    total_time = time.time() - total_start
    print(f"Total time with session reuse: {total_time*1000:.2f}ms")
    
    session.close()

def test_concurrent_requests():
    """Test concurrent requests (be careful with rate limiting)."""
    print("\n=== Testing Concurrent Requests (Limited) ===")
    
    verses = [
        ("John 3:16", "RSVCE"),
        ("Psalm 23:1", "NIV")
    ]
    
    def fetch_verse(query_version):
        query, version = query_version
        session = create_optimized_session()
        
        try:
            start = time.time()
            encoded_query = quote_plus(query)
            url = f"https://www.biblegateway.com/passage/?search={encoded_query}&version={version}"
            
            response = session.get(url, timeout=8)
            response.raise_for_status()
            
            request_time = time.time() - start
            session.close()
            
            return f"{query} ({version}): {request_time*1000:.2f}ms - {len(response.content)} bytes"
            
        except Exception as e:
            session.close()
            return f"{query} ({version}): FAILED - {e}"
    
    start = time.time()
    
    # Use only 2 concurrent requests to be respectful
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(fetch_verse, verses))
    
    total_time = time.time() - start
    
    for result in results:
        print(result)
    print(f"Total concurrent time: {total_time*1000:.2f}ms")

def test_response_compression():
    """Test if response compression helps."""
    print("\n=== Testing Response Compression ===")
    
    query, version = "John 3:16", "RSVCE"
    encoded_query = quote_plus(query)
    url = f"https://www.biblegateway.com/passage/?search={encoded_query}&version={version}"
    
    # Test with compression
    headers_compressed = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept-Encoding': 'gzip, deflate, br'
    }
    
    # Test without compression
    headers_uncompressed = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept-Encoding': 'identity'
    }
    
    for name, headers in [("Compressed", headers_compressed), ("Uncompressed", headers_uncompressed)]:
        try:
            start = time.time()
            response = requests.get(url, headers=headers, timeout=8)
            response.raise_for_status()
            request_time = time.time() - start
            
            print(f"{name}: {request_time*1000:.2f}ms - {len(response.content)} bytes")
            
        except Exception as e:
            print(f"{name}: FAILED - {e}")
        
        time.sleep(1)

if __name__ == "__main__":
    print("=== Bible Scraping Optimization Tests ===")
    
    test_with_session_reuse()
    test_concurrent_requests()
    test_response_compression()
    
    print("\n=== Recommendations ===")
    print("1. Session reuse can provide marginal improvements")
    print("2. Concurrent requests should be limited to avoid rate limiting")
    print("3. The main bottleneck is BibleGateway's server response time")
    print("4. Consider caching frequently requested verses")
    print("5. Alternative: Use a Bible API instead of scraping")