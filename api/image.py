"""
Main Vercel API handler for Bible verse wallpaper generation.
Handles /api/image endpoint with query parameters 'q' and 'version'.
"""

from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import traceback
import logging
import time
import uuid
import re
from datetime import datetime
from typing import Optional, Dict, Any, Union

# Import our custom modules
from bible_parser import format_for_biblegateway, generate_filename
from bible_scraper import scrape_bible_verse
from image_generator import create_wallpaper_from_verse_data, calculate_optimal_font_size

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Custom Exception Classes
class APIError(Exception):
    """Base exception for API errors"""
    def __init__(self, message: str, status_code: int = 500, error_code: str = "INTERNAL_ERROR"):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)

class ValidationError(APIError):
    """Exception for input validation errors"""
    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message, 400, "VALIDATION_ERROR")

class ScrapingError(APIError):
    """Exception for Bible verse scraping errors"""
    def __init__(self, message: str, verse_ref: str = None, version: str = None):
        self.verse_ref = verse_ref
        self.version = version
        super().__init__(message, 404, "SCRAPING_ERROR")

class ImageGenerationError(APIError):
    """Exception for image generation errors"""
    def __init__(self, message: str):
        super().__init__(message, 500, "IMAGE_GENERATION_ERROR")

class ParameterValidator:
    """Comprehensive parameter validation and sanitization"""
    
    # Supported Bible versions
    SUPPORTED_VERSIONS = {
        'RSVCE', 'NIV', 'ESV', 'NASB', 'NKJV', 'NLT', 'MSG', 'AMP', 'CSB', 'HCSB',
        'NET', 'RSV', 'NRSV', 'CEV', 'GNT', 'NCV', 'ICB', 'NIRV', 'TNIV', 'WEB',
        'YLT', 'DARBY', 'ASV', 'BBE', 'DRA', 'ERV', 'GW', 'ISV', 'JUB', 'LEB',
        'MOUNCE', 'NOG', 'NABRE', 'SBL', 'TLV', 'VOICE', 'WYC', 'RVR60', 'LBLA'
    }
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 500, allow_special_chars: bool = True) -> str:
        """Sanitize string input by removing dangerous characters and limiting length"""
        if not isinstance(value, str):
            raise ValidationError(f"Expected string, got {type(value).__name__}")
        
        # Remove null bytes and control characters (except newlines and tabs if allowed)
        value = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)
        
        # Trim whitespace
        value = value.strip()
        
        # Check length
        if len(value) > max_length:
            raise ValidationError(f"Input too long (max {max_length} characters)")
        
        # Remove potentially dangerous characters if not allowed
        if not allow_special_chars:
            # Only allow alphanumeric, spaces, and basic punctuation
            value = re.sub(r'[^a-zA-Z0-9\s\-_.:,;!?()[\]{}"\']', '', value)
        
        return value
    
    @staticmethod
    def validate_bible_reference(reference: str) -> str:
        """Validate and sanitize Bible reference"""
        if not reference:
            raise ValidationError("Bible reference cannot be empty", "q")
        
        # Sanitize the reference
        reference = ParameterValidator.sanitize_string(reference, max_length=100)
        
        if not reference:
            raise ValidationError("Bible reference cannot be empty after sanitization", "q")
        
        # Basic format validation - should contain at least book name and numbers
        if not re.search(r'[a-zA-Z]+.*\d+', reference):
            raise ValidationError(f"Invalid Bible reference format: '{reference}'", "q")
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'<script',  # Script tags
            r'javascript:',  # JavaScript URLs
            r'data:',  # Data URLs
            r'vbscript:',  # VBScript URLs
            r'on\w+\s*=',  # Event handlers
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, reference, re.IGNORECASE):
                raise ValidationError(f"Invalid characters in Bible reference: '{reference}'", "q")
        
        return reference
    
    @staticmethod
    def validate_version(version: str) -> str:
        """Validate Bible version"""
        if not version:
            return 'RSVCE'  # Default version
        
        # Sanitize and normalize
        version = ParameterValidator.sanitize_string(version, max_length=20, allow_special_chars=False)
        version = version.upper()
        
        if version not in ParameterValidator.SUPPORTED_VERSIONS:
            raise ValidationError(f"Unsupported Bible version: '{version}'. Supported versions: {', '.join(sorted(ParameterValidator.SUPPORTED_VERSIONS))}", "version")
        
        return version
    
    @staticmethod
    def validate_integer(value: Union[str, int], field_name: str, min_val: int = None, max_val: int = None) -> int:
        """Validate and convert integer parameter"""
        if value is None:
            return None
        
        try:
            if isinstance(value, str):
                # Sanitize string first
                value = ParameterValidator.sanitize_string(value, max_length=20, allow_special_chars=False)
                # Remove any non-digit characters except minus sign
                value = re.sub(r'[^\d\-]', '', value)
                if not value or value == '-':
                    raise ValueError("Empty or invalid number")
                int_val = int(value)
            else:
                int_val = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid integer value for {field_name}: '{value}'", field_name)
        
        if min_val is not None and int_val < min_val:
            raise ValidationError(f"{field_name} must be at least {min_val}, got {int_val}", field_name)
        
        if max_val is not None and int_val > max_val:
            raise ValidationError(f"{field_name} must be at most {max_val}, got {int_val}", field_name)
        
        return int_val
    
    @staticmethod
    def validate_float(value: Union[str, float], field_name: str, min_val: float = None, max_val: float = None) -> float:
        """Validate and convert float parameter"""
        if value is None:
            return None
        
        try:
            if isinstance(value, str):
                # Sanitize string first
                value = ParameterValidator.sanitize_string(value, max_length=20, allow_special_chars=False)
                # Remove any non-digit/decimal characters except minus sign
                value = re.sub(r'[^\d\.\-]', '', value)
                if not value or value == '-' or value == '.':
                    raise ValueError("Empty or invalid number")
                float_val = float(value)
            else:
                float_val = float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid float value for {field_name}: '{value}'", field_name)
        
        if min_val is not None and float_val < min_val:
            raise ValidationError(f"{field_name} must be at least {min_val}, got {float_val}", field_name)
        
        if max_val is not None and float_val > max_val:
            raise ValidationError(f"{field_name} must be at most {max_val}, got {float_val}", field_name)
        
        return float_val
    
    @staticmethod
    def validate_percentage(value: Union[str, float], field_name: str) -> float:
        """Validate percentage value (0-100)"""
        return ParameterValidator.validate_float(value, field_name, min_val=0.0, max_val=100.0)

class handler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.request_id = str(uuid.uuid4())[:8]
        self.start_time = time.time()
        super().__init__(*args, **kwargs)
    
    def log_request_start(self, method: str, path: str, query_params: Dict[str, Any]):
        """Log the start of a request with structured information"""
        logger.info(f"[{self.request_id}] {method} {path} - Request started", extra={
            'request_id': self.request_id,
            'method': method,
            'path': path,
            'query_params': {k: v[0] if v else None for k, v in query_params.items()},
            'client_ip': self.client_address[0] if self.client_address else 'unknown',
            'user_agent': self.headers.get('User-Agent', 'unknown')
        })
    
    def log_request_end(self, status_code: int, response_size: int = 0, metrics: Dict[str, float] = None):
        """Log request completion with performance metrics"""
        end_time = time.time()
        duration = end_time - self.start_time
        
        log_data = {
            'request_id': self.request_id,
            'status_code': status_code,
            'duration_ms': round(duration * 1000, 2),
            'response_size_bytes': response_size
        }
        
        # Build metrics string for log message
        metrics_str = ""
        if metrics:
            log_data.update(metrics)
            # Format metrics for display
            metric_parts = []
            for key, value in metrics.items():
                if key.endswith('_ms'):
                    metric_parts.append(f"{key}: {value:.1f}ms")
                elif key.endswith('_length'):
                    metric_parts.append(f"{key}: {value}")
                elif key.endswith('_size'):
                    metric_parts.append(f"{key}: {value}")
                else:
                    metric_parts.append(f"{key}: {value}")
            if metric_parts:
                metrics_str = f" | {', '.join(metric_parts)}"
        
        # Log performance warning for slow requests
        if duration > 10.0:  # More than 10 seconds
            logger.warning(f"[{self.request_id}] Slow request detected - {status_code} ({duration:.3f}s, {response_size} bytes){metrics_str}", extra=log_data)
        else:
            logger.info(f"[{self.request_id}] Request completed - {status_code} ({duration:.3f}s, {response_size} bytes){metrics_str}", extra=log_data)
    
    def log_error(self, error: Exception, context: str = ""):
        """Log errors with structured information and stack traces"""
        error_info = {
            'request_id': self.request_id,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context
        }
        
        if isinstance(error, APIError):
            error_info.update({
                'error_code': error.error_code,
                'status_code': error.status_code
            })
            if hasattr(error, 'field'):
                error_info['field'] = error.field
            if hasattr(error, 'verse_ref'):
                error_info['verse_ref'] = error.verse_ref
            if hasattr(error, 'version'):
                error_info['version'] = error.version
        
        logger.error(f"[{self.request_id}] {context}: {str(error)}", extra=error_info)
        
        # Log full stack trace for debugging
        if not isinstance(error, (ValidationError, ScrapingError)):
            logger.debug(f"[{self.request_id}] Stack trace:\n{traceback.format_exc()}")

    def do_GET(self):
        """Handle GET requests to /api/image"""
        try:
            # Parse the URL and query parameters
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            # Log request start
            self.log_request_start("GET", parsed_url.path, query_params)
            
            if parsed_url.path == '/api/verse-data':
                self._handle_verse_data_request(query_params)
            elif parsed_url.path == '/api/image' or parsed_url.path == '/':
                self._handle_image_request(query_params)
            elif parsed_url.path == '/api/health':
                self._handle_health_check()
            else:
                raise ValidationError(f"Unknown endpoint: {parsed_url.path}")
                
        except APIError as e:
            self.log_error(e, "API Error")
            self.send_error_response(e.status_code, e.message, e.error_code)
        except Exception as e:
            self.log_error(e, "Unexpected Error")
            self.send_error_response(500, f"Internal server error: {str(e)}", "INTERNAL_ERROR")
    
    def _handle_verse_data_request(self, query_params: Dict[str, list]):
        """Handle requests for verse data JSON"""
        logger.debug(f"[{self.request_id}] Processing verse data request")
        
        # Performance timing
        parse_start = time.time()
        
        # Extract and validate parameters using comprehensive validation
        q_raw = query_params.get('q', [None])[0]
        version_raw = query_params.get('version', ['RSVCE'])[0]
        
        # Validate and sanitize parameters
        q = ParameterValidator.validate_bible_reference(q_raw)
        version = ParameterValidator.validate_version(version_raw)
        
        parse_time = time.time() - parse_start
        logger.info(f"[{self.request_id}] Fetching verse data for: {q} ({version})")
        
        # Format the query for BibleGateway
        format_start = time.time()
        try:
            formatted_query = format_for_biblegateway(q)
            if not formatted_query:
                raise ValidationError(f"Could not parse Bible reference: '{q}'", "q")
        except Exception as e:
            raise ValidationError(f"Invalid Bible reference format: '{q}' - {str(e)}", "q")
        format_time = time.time() - format_start
        
        # Get verse data using existing scraper
        scrape_start = time.time()
        try:
            verse_data = scrape_bible_verse(formatted_query, version)
            if not verse_data:
                raise ScrapingError(f"Could not find verse: {formatted_query}", formatted_query, version)
        except Exception as e:
            if isinstance(e, ScrapingError):
                raise
            raise ScrapingError(f"Failed to scrape verse: {str(e)}", formatted_query, version)
        scrape_time = time.time() - scrape_start
        
        # Calculate boundaries and optimal font size
        calc_start = time.time()
        try:
            screen_height = query_params.get('screen_height', [None])[0]
            top_boundary_percent = query_params.get('top_boundary_percent', [None])[0]
            bottom_boundary_percent = query_params.get('bottom_boundary_percent', [None])[0]
            
            if screen_height and top_boundary_percent and bottom_boundary_percent:
                screen_height = int(screen_height)
                top_percent = float(top_boundary_percent)
                bottom_percent = float(bottom_boundary_percent)
                
                top_bound = int(screen_height * (top_percent / 100))
                bottom_bound = int(screen_height * ((100 - bottom_percent) / 100))
                
                optimal_font_size = calculate_optimal_font_size(verse_data['text'], verse_data['reference'], top_bound, bottom_bound)
            else:
                optimal_font_size = calculate_optimal_font_size(verse_data['text'], verse_data['reference'])
                
        except (ValueError, TypeError) as e:
            logger.warning(f"[{self.request_id}] Invalid boundary parameters, using defaults: {str(e)}")
            optimal_font_size = calculate_optimal_font_size(verse_data['text'], verse_data['reference'])
        calc_time = time.time() - calc_start
        
        # Return JSON response
        response_data = {
            'text': verse_data['text'],
            'reference': verse_data['reference'],
            'optimal_font_size': optimal_font_size,
            'request_id': self.request_id
        }
        
        response_body = json.dumps(response_data).encode('utf-8')
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        self.wfile.write(response_body)
        
        # Log with detailed performance metrics
        metrics = {
            'parse_time_ms': round(parse_time * 1000, 2),
            'format_time_ms': round(format_time * 1000, 2),
            'scrape_time_ms': round(scrape_time * 1000, 2),
            'calc_time_ms': round(calc_time * 1000, 2),
            'verse_length': len(verse_data['text']),
            'reference_length': len(verse_data['reference'])
        }
        self.log_request_end(200, len(response_body), metrics)
        
        logger.info(f"[{self.request_id}] Successfully returned verse data for: {verse_data['reference']}")
    
    def _handle_image_request(self, query_params: Dict[str, list]):
        """Handle requests for wallpaper image generation"""
        logger.debug(f"[{self.request_id}] Processing image generation request")
        
        # Performance timing
        parse_start = time.time()
        
        # Extract and validate query parameters using comprehensive validation
        q_raw = query_params.get('q', [None])[0]
        version_raw = query_params.get('version', ['RSVCE'])[0]
        
        # Validate and sanitize parameters
        q = ParameterValidator.validate_bible_reference(q_raw)
        version = ParameterValidator.validate_version(version_raw)
        
        parse_time = time.time() - parse_start
        logger.info(f"[{self.request_id}] Generating wallpaper for: {q} ({version})")
        
        # Format the query for BibleGateway
        format_start = time.time()
        try:
            formatted_query = format_for_biblegateway(q)
            if not formatted_query:
                raise ValidationError(f"Could not parse Bible reference: '{q}'", "q")
        except Exception as e:
            raise ValidationError(f"Invalid Bible reference format: '{q}' - {str(e)}", "q")
        format_time = time.time() - format_start
        
        # Scrape the verse from BibleGateway
        scrape_start = time.time()
        try:
            verse_data = scrape_bible_verse(formatted_query, version)
            if not verse_data:
                raise ScrapingError(f"Failed to fetch verse: '{formatted_query}'", formatted_query, version)
        except Exception as e:
            if isinstance(e, ScrapingError):
                raise
            raise ScrapingError(f"Error while scraping verse: {str(e)}", formatted_query, version)
        scrape_time = time.time() - scrape_start
        
        # Extract and validate boundary parameters
        boundary_start = time.time()
        try:
            top_bound, bottom_bound = self._parse_boundary_parameters(query_params)
        except (ValueError, TypeError) as e:
            logger.warning(f"[{self.request_id}] Invalid boundary parameters, using defaults: {str(e)}")
            top_bound = bottom_bound = None
        boundary_time = time.time() - boundary_start
        
        # Generate the wallpaper image
        image_gen_start = time.time()
        try:
            logger.debug(f"[{self.request_id}] Starting image generation with boundaries: top={top_bound}, bottom={bottom_bound}")
            
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
                
        except Exception as e:
            raise ImageGenerationError(f"Failed to generate wallpaper image: {str(e)}")
        image_gen_time = time.time() - image_gen_start
        
        # Generate filename
        filename_start = time.time()
        try:
            filename = generate_filename(q)
            if not filename:
                filename = "scripture_wallpaper.jpg"
        except Exception as e:
            logger.warning(f"[{self.request_id}] Failed to generate filename, using default: {str(e)}")
            filename = "scripture_wallpaper.jpg"
        filename_time = time.time() - filename_start
        
        # Send the image response
        image_data = img_buffer.getvalue()
        
        self.send_response(200)
        self.send_header('Content-Type', 'image/jpeg')
        self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
        self.send_header('Content-Length', str(len(image_data)))
        
        # Add CORS headers for frontend access
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        
        self.end_headers()
        self.wfile.write(image_data)
        
        # Log with detailed performance metrics
        metrics = {
            'parse_time_ms': round(parse_time * 1000, 2),
            'format_time_ms': round(format_time * 1000, 2),
            'scrape_time_ms': round(scrape_time * 1000, 2),
            'boundary_time_ms': round(boundary_time * 1000, 2),
            'image_gen_time_ms': round(image_gen_time * 1000, 2),
            'filename_time_ms': round(filename_time * 1000, 2),
            'image_size_bytes': len(image_data),
            'verse_length': len(verse_data['text']),
            'reference_length': len(verse_data['reference'])
        }
        self.log_request_end(200, len(image_data), metrics)
        logger.info(f"[{self.request_id}] Successfully generated wallpaper: {filename} ({len(image_data)} bytes)")
    
    def _parse_boundary_parameters(self, query_params: Dict[str, list]) -> tuple:
        """Parse and validate boundary parameters from query string"""
        # Extract raw parameters
        top_boundary_raw = query_params.get('top_boundary', [None])[0]
        bottom_boundary_raw = query_params.get('bottom_boundary', [None])[0]
        screen_height_raw = query_params.get('screen_height', [None])[0]
        top_boundary_percent_raw = query_params.get('top_boundary_percent', [None])[0]
        bottom_boundary_percent_raw = query_params.get('bottom_boundary_percent', [None])[0]
        
        # Validate parameters using ParameterValidator
        try:
            screen_height = ParameterValidator.validate_integer(screen_height_raw, 'screen_height', min_val=100, max_val=10000)
            top_boundary_percent = ParameterValidator.validate_percentage(top_boundary_percent_raw, 'top_boundary_percent')
            bottom_boundary_percent = ParameterValidator.validate_percentage(bottom_boundary_percent_raw, 'bottom_boundary_percent')
            
            if screen_height and top_boundary_percent is not None and bottom_boundary_percent is not None:
                # Calculate from percentages
                top_bound = int(screen_height * (top_boundary_percent / 100))
                bottom_bound = int(screen_height * ((100 - bottom_boundary_percent) / 100))
                
                # Validate calculated boundaries make sense
                if top_bound >= bottom_bound:
                    raise ValidationError("Top boundary must be less than bottom boundary", "boundary")
                
                logger.debug(f"[{self.request_id}] Calculated boundaries from percentages: top={top_bound}, bottom={bottom_bound}")
                return top_bound, bottom_bound
        except ValidationError:
            # If percentage validation fails, fall back to direct pixel values
            pass
        
        # Fall back to direct pixel values
        top_bound = ParameterValidator.validate_integer(top_boundary_raw, 'top_boundary', min_val=0, max_val=5000)
        bottom_bound = ParameterValidator.validate_integer(bottom_boundary_raw, 'bottom_boundary', min_val=0, max_val=5000)
        
        # Validate boundaries make sense if both are provided
        if top_bound is not None and bottom_bound is not None and top_bound >= bottom_bound:
            raise ValidationError("Top boundary must be less than bottom boundary", "boundary")
        
        logger.debug(f"[{self.request_id}] Using pixel boundaries: top={top_bound}, bottom={bottom_bound}")
        return top_bound, bottom_bound

    def _handle_health_check(self):
        """Handle health check requests"""
        logger.debug(f"[{self.request_id}] Processing health check request")
        
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'request_id': self.request_id,
            'version': '1.0.0',
            'services': {
                'bible_scraper': 'operational',
                'image_generator': 'operational',
                'parameter_validator': 'operational'
            }
        }
        
        response_body = json.dumps(health_data).encode('utf-8')
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        self.wfile.write(response_body)
        
        self.log_request_end(200, len(response_body))
        logger.info(f"[{self.request_id}] Health check completed successfully")

    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS preflight"""
        logger.debug(f"[{self.request_id}] Handling CORS preflight request")
        
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        self.log_request_end(200, 0)

    def send_error_response(self, status_code: int, message: str, error_code: str = "UNKNOWN_ERROR"):
        """Send a structured JSON error response"""
        error_data = {
            'error': {
                'message': message,
                'code': error_code,
                'status': status_code,
                'request_id': self.request_id,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        }
        
        response_body = json.dumps(error_data, indent=2).encode('utf-8')
        
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response_body)))
        
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        
        self.end_headers()
        self.wfile.write(response_body)
        
        self.log_request_end(status_code, len(response_body))

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