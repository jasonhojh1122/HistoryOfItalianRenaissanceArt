#!/usr/bin/env python3
"""
Embed external images from NOTES.md locally.

Downloads all external image links, saves them to ./img, and updates
the markdown to reference local paths.
"""

import argparse
import hashlib
import os
import re
import shutil
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from urllib.parse import urlparse, unquote


def get_safe_filename(url: str) -> str:
    """Generate a safe, unique filename from a URL."""
    parsed = urlparse(url)
    path = unquote(parsed.path)

    # Get the original filename
    original_name = os.path.basename(path)

    # Get extension
    name, ext = os.path.splitext(original_name)
    if not ext:
        ext = '.jpg'  # Default extension

    # Sanitize the name - keep only alphanumeric, dash, underscore
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)

    # Truncate if too long
    safe_name = safe_name[:50]

    # Add a short hash of the full URL for uniqueness
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]

    return f"{safe_name}_{url_hash}{ext}"


def find_external_images(content: str) -> list[tuple[str, str, int, int]]:
    """
    Find all external image links in markdown content.

    Returns list of tuples: (full_match, url, start_pos, end_pos)
    """
    # Match ![alt](url) pattern where url starts with http
    pattern = r'!\[([^\]]*)\]\((https?://[^)]+)\)'

    results = []
    for match in re.finditer(pattern, content):
        full_match = match.group(0)
        alt_text = match.group(1)
        url = match.group(2)
        results.append((full_match, alt_text, url, match.start(), match.end()))

    return results


def download_image(url: str, dest_path: Path, timeout: int = 30, retry_wait: int = 0) -> bool:
    """Download an image from URL to destination path.

    If retry_wait > 0 and a 429 rate limit is hit, waits and retries once.
    """
    try:
        # Create a request with a User-Agent header
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        request = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(request, timeout=timeout) as response:
            with open(dest_path, 'wb') as f:
                shutil.copyfileobj(response, f)
        return True
    except urllib.error.HTTPError as e:
        if e.code == 429 and retry_wait > 0:
            print(f"  Rate limited. Waiting {retry_wait}s before retry...")
            time.sleep(retry_wait)
            # Retry once without retry_wait to avoid infinite loop
            return download_image(url, dest_path, timeout, retry_wait=0)
        print(f"  Error downloading {url}: {e}", file=sys.stderr)
        return False
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"  Error downloading {url}: {e}", file=sys.stderr)
        return False


def embed_images(
    source_file: Path,
    img_dir: Path,
    dry_run: bool = False,
    delay: float = 1.0,
    retry_wait: int = 0
) -> dict:
    """
    Main function to embed external images.

    Returns dict with stats about the operation.
    """
    stats = {
        'found': 0,
        'downloaded': 0,
        'failed': 0,
        'skipped': 0,
    }

    # Read source file
    content = source_file.read_text(encoding='utf-8')

    # Find all external images
    external_images = find_external_images(content)
    stats['found'] = len(external_images)

    if not external_images:
        print("No external images found.")
        return stats

    print(f"Found {len(external_images)} external image(s)")

    # Ensure img directory exists
    if not dry_run:
        img_dir.mkdir(parents=True, exist_ok=True)

    # Process each image (in reverse order to preserve positions during replacement)
    replacements = []

    for full_match, alt_text, url, start, end in external_images:
        filename = get_safe_filename(url)
        local_path = img_dir / filename
        relative_path = f"img/{filename}"

        print(f"\nProcessing: {url[:80]}...")
        print(f"  -> {relative_path}")

        if dry_run:
            print("  [DRY RUN] Would download and update")
            stats['downloaded'] += 1
            replacements.append((start, end, alt_text, relative_path))
            continue

        # Check if already downloaded
        if local_path.exists():
            print(f"  Already exists, skipping download")
            stats['skipped'] += 1
            replacements.append((start, end, alt_text, relative_path))
            continue

        # Download the image
        if download_image(url, local_path, retry_wait=retry_wait):
            print(f"  Downloaded successfully")
            stats['downloaded'] += 1
            replacements.append((start, end, alt_text, relative_path))
        else:
            stats['failed'] += 1

        # Delay between downloads to avoid rate limiting
        if delay > 0:
            time.sleep(delay)

    # Apply replacements to content (in reverse order)
    if replacements and not dry_run:
        # Create backup
        backup_path = source_file.with_suffix('.md.bak')
        shutil.copy2(source_file, backup_path)
        print(f"\nBackup created: {backup_path}")

        # Sort by position descending
        replacements.sort(key=lambda x: x[0], reverse=True)

        new_content = content
        for start, end, alt_text, local_path in replacements:
            new_link = f"![{alt_text}]({local_path})"
            new_content = new_content[:start] + new_link + new_content[end:]

        source_file.write_text(new_content, encoding='utf-8')
        print(f"Updated {source_file}")

    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Download external images and embed them locally'
    )
    parser.add_argument(
        '--source',
        type=Path,
        default=Path('NOTES.md'),
        help='Source markdown file (default: NOTES.md)'
    )
    parser.add_argument(
        '--img-dir',
        type=Path,
        default=Path('img'),
        help='Directory to save images (default: img)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=1.0,
        help='Delay in seconds between downloads to avoid rate limiting (default: 1.0)'
    )
    parser.add_argument(
        '--retry-wait',
        type=int,
        default=0,
        help='Seconds to wait and retry when rate limited (default: 0, no retry)'
    )

    args = parser.parse_args()

    # Validate source file
    if not args.source.exists():
        print(f"Error: Source file not found: {args.source}", file=sys.stderr)
        sys.exit(1)

    print(f"Source: {args.source}")
    print(f"Image directory: {args.img_dir}")
    print(f"Delay between downloads: {args.delay}s")
    if args.dry_run:
        print("Mode: DRY RUN")
    print("-" * 40)

    stats = embed_images(args.source, args.img_dir, args.dry_run, args.delay, args.retry_wait)

    print("\n" + "=" * 40)
    print("Summary:")
    print(f"  External images found: {stats['found']}")
    print(f"  Downloaded: {stats['downloaded']}")
    print(f"  Already existed: {stats['skipped']}")
    print(f"  Failed: {stats['failed']}")


if __name__ == '__main__':
    main()
