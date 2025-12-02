#!/usr/bin/env python3
"""
Configuration file for Xtream Proxy Server
Edit this file to modify filtering patterns
"""

# Category filter patterns for dynamic filtering
# These patterns are checked against category names to determine inclusion
CATEGORY_PATTERNS = {
    "live": {
        # Patterns included in both FULL and MINI filters
        "full_and_mini": ["US|", "UK|", "ES|", "SE|"],
        # Additional patterns for FULL filter only
        "full_only": [
            "IT|",
            "DK|",
            "NO|",
            "FI|",
            "4K|",
        ],
    },
    "vod": {
        # Patterns included in both FULL and MINI filters
        "full_and_mini": ["EN -", "LA -", "NORDIC", "SVENSKA", "TOP"],
        # Additional patterns for FULL filter only
        "full_only": [
            "AMAZON",
            "APPLE+",
            "DANSKE",
            "DISCOVERY+",
            "DISNEY+",
            "DREAMWORKS",
            "MARVEL",
            "NETFLIX",
            "NORGE",
            "UNIVERSAL",
            "VIAPLAY KIDS",
            "VIAPLAY MOVIES",
        ],
    },
    "series": {
        # Patterns included in both FULL and MINI filters
        "full_and_mini": ["ENGLISH", "LATINO", "SVENSK", "VIAPLAY KIDS"],
        # Additional patterns for FULL filter only
        "full_only": [
            "AMAZON",
            "APPLE+",
            "DANSK",
            "DISCOVERY+",
            "ESPAÑA",
            "MARVEL",
            "NETFLIX",
            "NORDIC",
            "PARAMOUNT+",
            "PEACOCK",
            "SHOWTIME",
            "SKY",
            "VIAPLAY SERIES",
        ],
    },
}

# Individual stream/channel filtering
# Exclude any stream/channel/series that starts with these characters
EXCLUDE_STREAM_PREFIXES = ["#"]  # Exclude streams starting with #

# Server configuration
CACHE_TIMEOUT = 86400  # Cache category lookups for 24 hours to improve performance
