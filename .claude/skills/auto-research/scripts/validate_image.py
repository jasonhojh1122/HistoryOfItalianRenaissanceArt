#!/usr/bin/env python3
"""
Validate that an image URL is accessible and returns a valid image.

Usage:
    python validate_image.py "https://example.com/image.jpg"
    python validate_image.py "https://example.com/image.jpg" --json
"""

import argparse
import json
import sys
import urllib.request
import urllib.error


def validate_image_url(url: str) -> dict:
    """
    Check if an image URL is valid and accessible.

    Returns dict with:
        - valid: True if image is accessible
        - url: The original URL
        - content_type: The content type if accessible
        - error: Error message if not valid
    """
    if not url:
        return {"valid": False, "url": url, "error": "Empty URL"}

    try:
        req = urllib.request.Request(
            url,
            method='HEAD',
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; ImageValidator/1.0)",
                "Accept": "image/*"
            }
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            content_type = response.headers.get('Content-Type', '')

            # Check if it's actually an image
            if content_type.startswith('image/'):
                return {
                    "valid": True,
                    "url": url,
                    "content_type": content_type
                }
            else:
                return {
                    "valid": False,
                    "url": url,
                    "error": f"Not an image: {content_type}"
                }

    except urllib.error.HTTPError as e:
        return {"valid": False, "url": url, "error": f"HTTP {e.code}: {e.reason}"}
    except urllib.error.URLError as e:
        return {"valid": False, "url": url, "error": f"URL Error: {e.reason}"}
    except Exception as e:
        return {"valid": False, "url": url, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Validate image URL accessibility")
    parser.add_argument("url", help="Image URL to validate")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()
    result = validate_image_url(args.url)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["valid"]:
            print(f"✓ Valid: {result['url']}")
            print(f"  Type: {result['content_type']}")
        else:
            print(f"✗ Invalid: {result['url']}")
            print(f"  Error: {result['error']}")

    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
