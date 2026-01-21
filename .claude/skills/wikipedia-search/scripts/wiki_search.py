#!/usr/bin/env python3
"""
Search Wikipedia and return page URL, summary, and main image URL.

Usage:
    python wiki_search.py "Leonardo da Vinci"
    python wiki_search.py "Sistine Chapel" --json
    python wiki_search.py "Botticelli" --summary-length short
"""

import argparse
import json
import sys
import urllib.request
import urllib.parse
import urllib.error


def search_wikipedia(term: str) -> dict:
    """
    Search Wikipedia for a term and return page info.

    Returns dict with:
        - title: Article title
        - url: Wikipedia page URL
        - summary: Extract/summary of the article
        - image_url: URL of the main image (if available)
        - error: Error message (if search failed)
    """
    # Use Wikipedia API to search and get page info
    base_url = "https://en.wikipedia.org/api/rest_v1/page/summary/"
    encoded_term = urllib.parse.quote(term.replace(" ", "_"))
    url = base_url + encoded_term

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "WikipediaSearchSkill/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

            result = {
                "title": data.get("title", term),
                "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                "summary": data.get("extract", ""),
                "image_url": None
            }

            # Get the main image if available
            if "originalimage" in data:
                result["image_url"] = data["originalimage"].get("source")
            elif "thumbnail" in data:
                result["image_url"] = data["thumbnail"].get("source")

            return result

    except urllib.error.HTTPError as e:
        if e.code == 404:
            # Try search API as fallback
            return search_wikipedia_fallback(term)
        return {"error": f"HTTP Error {e.code}: {e.reason}"}
    except urllib.error.URLError as e:
        return {"error": f"URL Error: {e.reason}"}
    except json.JSONDecodeError:
        return {"error": "Failed to parse Wikipedia response"}
    except Exception as e:
        return {"error": str(e)}


def search_wikipedia_fallback(term: str) -> dict:
    """
    Fallback search using Wikipedia's search API.
    """
    search_url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": term,
        "format": "json",
        "srlimit": 1
    }
    url = search_url + "?" + urllib.parse.urlencode(params)

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "WikipediaSearchSkill/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

            results = data.get("query", {}).get("search", [])
            if not results:
                return {"error": f"No Wikipedia article found for '{term}'"}

            # Get the first result's title and fetch full info
            title = results[0]["title"]
            return search_wikipedia(title)

    except Exception as e:
        return {"error": f"Search failed: {e}"}


def truncate_summary(summary: str, length: str) -> str:
    """
    Truncate the summary based on the requested length.

    Args:
        summary: Full summary text
        length: One of 'short', 'medium', or 'full'

    Returns:
        Truncated summary text
    """
    if not summary or length == "full":
        return summary

    sentences = []
    current = ""
    for char in summary:
        current += char
        if char in ".!?" and len(current.strip()) > 0:
            sentences.append(current.strip())
            current = ""
    if current.strip():
        sentences.append(current.strip())

    if length == "short":
        # Return first 1-2 sentences (up to ~150 chars)
        result = ""
        for sentence in sentences[:2]:
            if len(result) + len(sentence) > 200:
                break
            result = (result + " " + sentence).strip()
        return result or (summary[:150] + "..." if len(summary) > 150 else summary)

    elif length == "medium":
        # Return first paragraph or ~3-4 sentences
        result = ""
        for sentence in sentences[:4]:
            if len(result) + len(sentence) > 500:
                break
            result = (result + " " + sentence).strip()
        return result or summary[:500]

    return summary


def format_output(result: dict, as_json: bool = False, summary_length: str = "full") -> str:
    """Format the result for display."""
    if as_json:
        if "summary" in result:
            result = result.copy()
            result["summary"] = truncate_summary(result["summary"], summary_length)
        return json.dumps(result, indent=2)

    if "error" in result:
        return f"Error: {result['error']}"

    summary = truncate_summary(result.get("summary", ""), summary_length)

    lines = [
        f"Title: {result['title']}",
        f"URL: {result['url']}",
        f"Summary: {summary}",
        f"Image: {result['image_url'] or 'No image available'}"
    ]
    return "\n\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Search Wikipedia and get page info"
    )
    parser.add_argument("term", help="Search term")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )
    parser.add_argument(
        "--summary-length",
        choices=["short", "medium", "full"],
        default="full",
        help="Summary length: short (1-2 sentences), medium (3-4 sentences), full (default)"
    )

    args = parser.parse_args()
    result = search_wikipedia(args.term)
    print(format_output(result, args.json, args.summary_length))

    if "error" in result:
        sys.exit(1)


if __name__ == "__main__":
    main()
