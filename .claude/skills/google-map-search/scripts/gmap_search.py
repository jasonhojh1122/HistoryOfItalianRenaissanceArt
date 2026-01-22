#!/usr/bin/env python3
"""
Generate Google Maps links for locations.

Usage:
    python gmap_search.py "Uffizi Gallery"
    python gmap_search.py "Santa Maria Novella" --city "Florence, Italy"
    python gmap_search.py "Basilica di Santa Croce" --json
"""

import argparse
import json
import urllib.parse


def generate_maps_url(location: str, city: str = None, place_type: str = None) -> dict:
    """
    Generate a Google Maps search URL for a location.

    Args:
        location: The location name to search for
        city: Optional city/region context
        place_type: Optional place type (museum, church, etc.)

    Returns dict with:
        - query: The full search query
        - url: Google Maps search URL
        - markdown: Pre-formatted markdown link
    """
    # Build the search query
    query_parts = [location]

    if place_type:
        # Add type context if not already in location name
        if place_type.lower() not in location.lower():
            query_parts[0] = f"{location} {place_type}"

    if city:
        query_parts.append(city)

    full_query = ", ".join(query_parts)

    # Generate the Google Maps search URL
    encoded_query = urllib.parse.quote(full_query)
    url = f"https://maps.google.com/?q={encoded_query}"

    return {
        "query": full_query,
        "url": url,
        "markdown": f"[GoogleMap]({url})"
    }


def format_output(result: dict, as_json: bool = False) -> str:
    """Format the result for display."""
    if as_json:
        return json.dumps(result, indent=2)

    lines = [
        f"Query: {result['query']}",
        f"URL: {result['url']}",
        f"Markdown: {result['markdown']}"
    ]
    return "\n\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate Google Maps links for locations"
    )
    parser.add_argument("location", help="Location name to search for")
    parser.add_argument(
        "--city",
        help="City or region context (e.g., 'Florence, Italy')"
    )
    parser.add_argument(
        "--type",
        dest="place_type",
        help="Place type (museum, church, gallery, palazzo, etc.)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()
    result = generate_maps_url(args.location, args.city, args.place_type)
    print(format_output(result, args.json))


if __name__ == "__main__":
    main()
