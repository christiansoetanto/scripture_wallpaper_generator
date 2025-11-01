"""
Main Vercel API handler for Bible verse wallpaper generation.
Handles /api/image endpoint with query parameters 'q' and 'version'.
"""

from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import traceback

# Import our custom modules
from bible_parser import format_for_biblegateway, generate_filename
from bible_scraper import scrape_bible_verse
from image_generator import create_wallpaper_from_verse_data, calculate_optimal_font_size

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests to /api/image"""
        try:
            # Parse the URL and query parameters
            parsed_url = urlparse(self.path)
            
            if parsed_url.path == '/api/verse-data':
                # Return verse data as JSON for Canvas editor
                query_params = parse_qs(parsed_url.query)
                q = query_params.get('q', [None])[0]
                version = query_params.get('version', ['NIV'])[0]
                top_boundary = query_params.get('top_boundary', [None])[0]
                bottom_boundary = query_params.get('bottom_boundary', [None])[0]
                
                if not q:
                    self.send_error_response(400, "Missing 'q' parameter")
                    return
                
                # Get verse data using existing scraper
                verse_data = scrape_bible_verse(q, version)
                
                if not verse_data:
                    self.send_error_response(404, f"Could not find verse: {q}")
                    return
                
                # Calculate boundaries (same logic as image generation)
                try:
                    # Check if percentage parameters are provided
                    screen_height = query_params.get('screen_height', [None])[0]
                    top_boundary_percent = query_params.get('top_boundary_percent', [None])[0]
                    bottom_boundary_percent = query_params.get('bottom_boundary_percent', [None])[0]
                    
                    if screen_height and top_boundary_percent and bottom_boundary_percent:
                        # Calculate from percentages
                        screen_height = int(screen_height)
                        top_percent = float(top_boundary_percent)
                        bottom_percent = float(bottom_boundary_percent)
                        
                        top_bound = int(screen_height * (top_percent / 100))
                        bottom_bound = int(screen_height * ((100 - bottom_percent) / 100))
                    else:
                        # Fall back to direct pixel values
                        top_bound = int(top_boundary) if top_boundary else None
                        bottom_bound = int(bottom_boundary) if bottom_boundary else None
                        
                except (ValueError, TypeError):
                    top_bound = None
                    bottom_bound = None
                
                # Use default boundaries if not provided
                from image_generator import DEFAULT_TOP_BOUNDARY, DEFAULT_BOTTOM_BOUNDARY
                if top_bound is None:
                    top_bound = DEFAULT_TOP_BOUNDARY
                if bottom_bound is None:
                    bottom_bound = DEFAULT_BOTTOM_BOUNDARY
                
                # Calculate optimal font size
                optimal_font_size = calculate_optimal_font_size(
                    verse_data['text'], 
                    verse_data['reference'], 
                    top_bound, 
                    bottom_bound
                )
                
                # Return JSON response
                response_data = {
                    'text': verse_data['text'],
                    'reference': verse_data['reference'],
                    'optimal_font_size': optimal_font_size
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()
                
                self.wfile.write(json.dumps(response_data).encode('utf-8'))
                return
            
            query_params = parse_qs(parsed_url.query)
            
            # Extract query parameters
            q = query_params.get('q', [None])[0]
            version = query_params.get('version', ['RSVCE'])[0]
            top_boundary = query_params.get('top_boundary', [None])[0]
            bottom_boundary = query_params.get('bottom_boundary', [None])[0]
            
            # Validate required parameters
            if not q:
                self.send_error_response(400, "Missing required parameter 'q' (Bible reference)")
                return
            
            # Format the query for BibleGateway
            formatted_query = format_for_biblegateway(q)
            if not formatted_query:
                self.send_error_response(400, f"Could not parse Bible reference: '{q}'")
                return
            
            # Scrape the verse from BibleGateway
            verse_data = scrape_bible_verse(formatted_query, version)
            if not verse_data:
                self.send_error_response(500, f"Failed to fetch verse: '{formatted_query}' ({version})")
                return
            
            # Extract boundary parameters (support both percentage and pixel modes)
            try:
                # Check if percentage parameters are provided
                screen_height = query_params.get('screen_height', [None])[0]
                top_boundary_percent = query_params.get('top_boundary_percent', [None])[0]
                bottom_boundary_percent = query_params.get('bottom_boundary_percent', [None])[0]
                
                if screen_height and top_boundary_percent and bottom_boundary_percent:
                    # Calculate from percentages
                    screen_height = int(screen_height)
                    top_percent = float(top_boundary_percent)
                    bottom_percent = float(bottom_boundary_percent)
                    
                    top_bound = int(screen_height * (top_percent / 100))
                    bottom_bound = int(screen_height * ((100 - bottom_percent) / 100))
                else:
                    # Fall back to direct pixel values
                    top_bound = int(top_boundary) if top_boundary else None
                    bottom_bound = int(bottom_boundary) if bottom_boundary else None
                    
            except (ValueError, TypeError):
                top_bound = None
                bottom_bound = None
            
            # Generate the wallpaper image with boundaries
            if top_bound is not None and bottom_bound is not None:
                img_buffer = create_wallpaper_from_verse_data(verse_data, top_bound, bottom_bound)
            elif top_bound is not None:
                from image_generator import DEFAULT_BOTTOM_BOUNDARY
                img_buffer = create_wallpaper_from_verse_data(verse_data, top_bound, DEFAULT_BOTTOM_BOUNDARY)
            elif bottom_bound is not None:
                from image_generator import DEFAULT_TOP_BOUNDARY
                img_buffer = create_wallpaper_from_verse_data(verse_data, DEFAULT_TOP_BOUNDARY, bottom_bound)
            else:
                img_buffer = create_wallpaper_from_verse_data(verse_data)
            
            # Generate filename
            filename = generate_filename(q)
            if not filename:
                filename = "scripture_wallpaper.jpg"
            
            # Send the image response
            self.send_response(200)
            self.send_header('Content-Type', 'image/jpeg')
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            self.send_header('Content-Length', str(len(img_buffer.getvalue())))
            
            # Add CORS headers for frontend access
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            
            self.end_headers()
            
            # Write the image data
            self.wfile.write(img_buffer.getvalue())
            
        except Exception as e:
            print(f"Error in handler: {e}")
            print(traceback.format_exc())
            self.send_error_response(500, f"Internal server error: {str(e)}")
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def send_error_response(self, status_code: int, message: str):
        """Send a JSON error response"""
        error_data = {
            'error': message,
            'status': status_code
        }
        
        response_body = json.dumps(error_data).encode('utf-8')
        
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response_body)))
        
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        
        self.end_headers()
        self.wfile.write(response_body)

# For local testing
if __name__ == "__main__":
    from http.server import HTTPServer
    import sys
    
    # Simple local test server
    class LocalHandler(handler):
        def log_message(self, format, *args):
            print(f"[{self.address_string()}] {format % args}")
    
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Invalid port number, using default 8000")
    
    server = HTTPServer(('localhost', port), LocalHandler)
    print(f"Starting local test server on http://localhost:{port}")
    print(f"Test URL: http://localhost:{port}?q=John%203:16&version=RSVCE")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()