"""
Bible reference parser and normalizer.
Handles common abbreviations and formats Bible references for BibleGateway URLs.
"""

import re
from typing import Tuple, Optional

# Common Bible book abbreviations mapping
BOOK_ABBREVIATIONS = {
    # Old Testament
    'gen': 'Genesis', 'genesis': 'Genesis',
    'ex': 'Exodus', 'exod': 'Exodus', 'exodus': 'Exodus',
    'lev': 'Leviticus', 'leviticus': 'Leviticus',
    'num': 'Numbers', 'numbers': 'Numbers',
    'deut': 'Deuteronomy', 'dt': 'Deuteronomy', 'deuteronomy': 'Deuteronomy',
    'josh': 'Joshua', 'joshua': 'Joshua',
    'judg': 'Judges', 'judges': 'Judges',
    'ruth': 'Ruth',
    '1sam': '1 Samuel', '1 sam': '1 Samuel', '1 samuel': '1 Samuel',
    '2sam': '2 Samuel', '2 sam': '2 Samuel', '2 samuel': '2 Samuel',
    '1kings': '1 Kings', '1 kings': '1 Kings', '1 kgs': '1 Kings',
    '2kings': '2 Kings', '2 kings': '2 Kings', '2 kgs': '2 Kings',
    '1chr': '1 Chronicles', '1 chronicles': '1 Chronicles',
    '2chr': '2 Chronicles', '2 chronicles': '2 Chronicles',
    'ezra': 'Ezra',
    'neh': 'Nehemiah', 'nehemiah': 'Nehemiah',
    'esth': 'Esther', 'esther': 'Esther',
    'job': 'Job',
    'ps': 'Psalms', 'psa': 'Psalms', 'psalm': 'Psalms', 'psalms': 'Psalms',
    'prov': 'Proverbs', 'proverbs': 'Proverbs',
    'eccl': 'Ecclesiastes', 'ecc': 'Ecclesiastes', 'ecclesiastes': 'Ecclesiastes',
    'song': 'Song of Songs', 'sos': 'Song of Songs', 'song of songs': 'Song of Songs', 'song of solomon': 'Song of Songs',
    'isa': 'Isaiah', 'is': 'Isaiah', 'isaiah': 'Isaiah',
    'jer': 'Jeremiah', 'jeremiah': 'Jeremiah',
    'lam': 'Lamentations', 'lamentations': 'Lamentations',
    'ezek': 'Ezekiel', 'eze': 'Ezekiel', 'ezekiel': 'Ezekiel',
    'dan': 'Daniel', 'daniel': 'Daniel',
    'hos': 'Hosea', 'hosea': 'Hosea',
    'joel': 'Joel',
    'amos': 'Amos',
    'obad': 'Obadiah', 'obadiah': 'Obadiah',
    'jonah': 'Jonah',
    'mic': 'Micah', 'micah': 'Micah',
    'nah': 'Nahum', 'nahum': 'Nahum',
    'hab': 'Habakkuk', 'habakkuk': 'Habakkuk',
    'zeph': 'Zephaniah', 'zephaniah': 'Zephaniah',
    'hag': 'Haggai', 'haggai': 'Haggai',
    'zech': 'Zechariah', 'zechariah': 'Zechariah',
    'mal': 'Malachi', 'malachi': 'Malachi',
    
    # New Testament
    'matt': 'Matthew', 'mt': 'Matthew', 'matthew': 'Matthew',
    'mark': 'Mark', 'mk': 'Mark',
    'luke': 'Luke', 'lk': 'Luke',
    'john': 'John', 'jn': 'John', 'joh': 'John',
    'acts': 'Acts',
    'rom': 'Romans', 'romans': 'Romans',
    '1cor': '1 Corinthians', '1 cor': '1 Corinthians', '1 corinthians': '1 Corinthians',
    '2cor': '2 Corinthians', '2 cor': '2 Corinthians', '2 corinthians': '2 Corinthians',
    'gal': 'Galatians', 'galatians': 'Galatians',
    'eph': 'Ephesians', 'ephesians': 'Ephesians',
    'phil': 'Philippians', 'php': 'Philippians', 'philippians': 'Philippians',
    'col': 'Colossians', 'colossians': 'Colossians',
    '1thess': '1 Thessalonians', '1 thess': '1 Thessalonians', '1 thessalonians': '1 Thessalonians',
    '2thess': '2 Thessalonians', '2 thess': '2 Thessalonians', '2 thessalonians': '2 Thessalonians',
    '1tim': '1 Timothy', '1 tim': '1 Timothy', '1 timothy': '1 Timothy',
    '2tim': '2 Timothy', '2 tim': '2 Timothy', '2 timothy': '2 Timothy',
    'titus': 'Titus', 'tit': 'Titus',
    'phlm': 'Philemon', 'philemon': 'Philemon',
    'heb': 'Hebrews', 'hebrews': 'Hebrews',
    'jas': 'James', 'james': 'James',
    '1pet': '1 Peter', '1 peter': '1 Peter', '1 pt': '1 Peter',
    '2pet': '2 Peter', '2 peter': '2 Peter', '2 pt': '2 Peter',
    '1john': '1 John', '1 jn': '1 John', '1 john': '1 John',
    '2john': '2 John', '2 jn': '2 John', '2 john': '2 John',
    '3john': '3 John', '3 jn': '3 John', '3 john': '3 John',
    'jude': 'Jude',
    'rev': 'Revelation', 'revelation': 'Revelation'
}

def normalize_book_name(book_input: str) -> Optional[str]:
    """
    Normalize a book name or abbreviation to the full book name.
    
    Args:
        book_input: The book name or abbreviation (e.g., 'jn', 'john', 'Matthew')
    
    Returns:
        The normalized full book name, or None if not found
    """
    # Clean and normalize the input
    clean_input = book_input.strip().lower()
    
    # Direct lookup in abbreviations
    if clean_input in BOOK_ABBREVIATIONS:
        return BOOK_ABBREVIATIONS[clean_input]
    
    # Try without spaces and numbers for compound books
    clean_no_space = clean_input.replace(' ', '')
    if clean_no_space in BOOK_ABBREVIATIONS:
        return BOOK_ABBREVIATIONS[clean_no_space]
    
    return None

def parse_bible_reference(reference: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Parse a Bible reference into book, chapter, and verses.
    
    Args:
        reference: Bible reference like "John 3:16", "Matt 25:31-33,46", "1 Cor 13:1-13"
    
    Returns:
        Tuple of (book_name, chapter, verses) or (None, None, None) if parsing fails
    """
    # Clean the reference
    reference = reference.strip()
    
    # Pattern to match Bible references
    # Supports: "Book Chapter:Verses", "Book Chapter", "Book Chapter:Verse-Verse,Verse"
    pattern = r'^(.+?)\s+(\d+)(?::(.+))?$'
    
    match = re.match(pattern, reference)
    if not match:
        return None, None, None
    
    book_part = match.group(1).strip()
    chapter = match.group(2)
    verses = match.group(3) if match.group(3) else None
    
    # Normalize the book name
    normalized_book = normalize_book_name(book_part)
    if not normalized_book:
        return None, None, None
    
    return normalized_book, chapter, verses

def format_for_biblegateway(reference: str) -> Optional[str]:
    """
    Format a Bible reference for BibleGateway URL.
    
    Args:
        reference: Bible reference like "John 3:16"
    
    Returns:
        Formatted reference for BibleGateway URL, or None if parsing fails
    """
    book, chapter, verses = parse_bible_reference(reference)
    
    if not book or not chapter:
        return None
    
    if verses:
        return f"{book} {chapter}:{verses}"
    else:
        return f"{book} {chapter}"

def generate_filename(reference: str) -> Optional[str]:
    """
    Generate a filename from a Bible reference.
    
    Args:
        reference: Bible reference like "John 3:16"
    
    Returns:
        Filename like "john_3_16.jpg" or None if parsing fails
    """
    book, chapter, verses = parse_bible_reference(reference)
    
    if not book or not chapter:
        return None
    
    # Convert book name to lowercase and replace spaces with underscores
    book_filename = book.lower().replace(' ', '_')
    
    if verses:
        # Replace colons, hyphens, and commas with underscores for filename
        verses_filename = verses.replace(':', '_').replace('-', '_').replace(',', '_')
        return f"{book_filename}_{chapter}_{verses_filename}.jpg"
    else:
        return f"{book_filename}_{chapter}.jpg"

if __name__ == "__main__":
    # Test the parser
    test_references = [
        "John 3:16",
        "jn 3:16",
        "Matt 25:31-33,46",
        "1 Cor 13:1-13",
        "Romans 8:28",
        "Psalm 23"
    ]
    
    for ref in test_references:
        book, chapter, verses = parse_bible_reference(ref)
        formatted = format_for_biblegateway(ref)
        filename = generate_filename(ref)
        print(f"Input: {ref}")
        print(f"  Parsed: {book}, {chapter}, {verses}")
        print(f"  Formatted: {formatted}")
        print(f"  Filename: {filename}")
        print()