#!/usr/bin/env python3
"""
Embed external images from NOTES.md and AUTO_RESEARCH_NOTES.md locally.

Downloads all external image links, saves them to ./img, and updates
the markdown to reference local paths. Also tracks image credits.
"""

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from urllib.parse import urlparse, unquote


def get_source_from_url(url: str) -> str:
    """Determine the source based on URL domain."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    if 'wikimedia.org' in domain or 'wikipedia.org' in domain:
        return 'Wikimedia Commons'
    return 'Unknown'


def credit_exists(credit_file: Path, filename: str) -> bool:
    """Check if a credit entry already exists for this filename."""
    if not credit_file.exists():
        return False

    content = credit_file.read_text(encoding='utf-8')
    # Look for the filename in the table (escaped for markdown)
    return f'`{filename}`' in content


def write_credit(credit_file: Path, filename: str, url: str) -> None:
    """Append a credit entry to CREDIT.md."""
    source = get_source_from_url(url)

    # Create file with header if it doesn't exist
    if not credit_file.exists():
        header = """# Image Credits

| Local File | Original URL | Source |
|------------|--------------|--------|
"""
        credit_file.write_text(header, encoding='utf-8')

    # Append the credit entry
    entry = f"| `{filename}` | {url} | {source} |\n"
    with open(credit_file, 'a', encoding='utf-8') as f:
        f.write(entry)


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
    retry_wait: int = 0,
    credit_file: Path | None = None
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
            # Write credit if missing (for previously downloaded images)
            if credit_file and not credit_exists(credit_file, filename):
                write_credit(credit_file, filename, url)
                print(f"  Added missing credit entry")
            continue

        # Download the image
        if download_image(url, local_path, retry_wait=retry_wait):
            print(f"  Downloaded successfully")
            stats['downloaded'] += 1
            # Write credit for newly downloaded image
            if credit_file and not credit_exists(credit_file, filename):
                write_credit(credit_file, filename, url)
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


def backfill_credits(
    credit_file: Path,
    before_commit: str = '953ee6c',
    after_commit: str = '170f653',
    img_dir: Path = Path('img'),
    dry_run: bool = False
) -> dict:
    """
    Extract retroactive credits from git history.

    Compares two commits to find URLs that were replaced with local paths.
    """
    stats = {
        'found': 0,
        'written': 0,
        'skipped': 0,
        'missing': 0,
    }

    # Get the diff for NOTES.md and AUTO_RESEARCH_NOTES.md
    try:
        result = subprocess.run(
            ['git', 'diff', before_commit, after_commit, '--', 'NOTES.md', 'AUTO_RESEARCH_NOTES.md'],
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error running git diff: {e}", file=sys.stderr)
        return stats

    # Pattern to match removed lines with external image URLs
    # Matches lines starting with - that contain ![...](<http url>)
    pattern = r'^\-.*!\[[^\]]*\]\((https?://[^)]+)\)'

    urls_found = set()
    for line in result.stdout.split('\n'):
        match = re.search(pattern, line)
        if match:
            url = match.group(1)
            urls_found.add(url)

    stats['found'] = len(urls_found)
    print(f"Found {len(urls_found)} unique URLs in git history")

    for url in sorted(urls_found):
        filename = get_safe_filename(url)
        local_path = img_dir / filename

        # Check if the image file exists locally
        if not local_path.exists():
            print(f"  Warning: Local file missing for {filename}")
            stats['missing'] += 1
            continue

        # Check if credit already exists
        if credit_exists(credit_file, filename):
            stats['skipped'] += 1
            continue

        if dry_run:
            print(f"  [DRY RUN] Would add credit for {filename}")
            stats['written'] += 1
        else:
            write_credit(credit_file, filename, url)
            print(f"  Added credit for {filename}")
            stats['written'] += 1

    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Download external images and embed them locally'
    )
    parser.add_argument(
        '--source',
        type=Path,
        nargs='*',
        help='Source markdown file(s). Default: NOTES.md and AUTO_RESEARCH_NOTES.md'
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
    parser.add_argument(
        '--credit-file',
        type=Path,
        default=Path('CREDIT.md'),
        help='Output file for image credits (default: CREDIT.md)'
    )
    parser.add_argument(
        '--no-credit',
        action='store_true',
        help='Skip writing credits'
    )
    parser.add_argument(
        '--backfill',
        action='store_true',
        help='Extract retroactive credits from git history'
    )

    args = parser.parse_args()

    # Handle backfill mode
    if args.backfill:
        print("Backfill mode: Extracting credits from git history")
        print(f"Credit file: {args.credit_file}")
        if args.dry_run:
            print("Mode: DRY RUN")
        print("-" * 40)

        stats = backfill_credits(
            args.credit_file,
            img_dir=args.img_dir,
            dry_run=args.dry_run
        )

        print("\n" + "=" * 40)
        print("Backfill Summary:")
        print(f"  URLs found in history: {stats['found']}")
        print(f"  Credits written: {stats['written']}")
        print(f"  Already existed: {stats['skipped']}")
        print(f"  Missing local files: {stats['missing']}")
        return

    # Default source files if none specified
    if args.source:
        source_files = args.source
    else:
        source_files = [Path('NOTES.md'), Path('AUTO_RESEARCH_NOTES.md')]

    # Filter to only existing files
    existing_sources = [f for f in source_files if f.exists()]
    missing_sources = [f for f in source_files if not f.exists()]

    if missing_sources:
        for f in missing_sources:
            print(f"Note: Source file not found, skipping: {f}")

    if not existing_sources:
        print("Error: No source files found", file=sys.stderr)
        sys.exit(1)

    print(f"Source files: {', '.join(str(f) for f in existing_sources)}")
    print(f"Image directory: {args.img_dir}")
    print(f"Delay between downloads: {args.delay}s")
    if not args.no_credit:
        print(f"Credit file: {args.credit_file}")
    if args.dry_run:
        print("Mode: DRY RUN")
    print("-" * 40)

    # Determine credit file (None if --no-credit)
    credit_file = None if args.no_credit else args.credit_file

    # Aggregate stats across all files
    total_stats = {
        'found': 0,
        'downloaded': 0,
        'failed': 0,
        'skipped': 0,
    }

    for source_file in existing_sources:
        print(f"\n{'=' * 40}")
        print(f"Processing: {source_file}")
        print("=" * 40)

        stats = embed_images(
            source_file,
            args.img_dir,
            args.dry_run,
            args.delay,
            args.retry_wait,
            credit_file
        )

        for key in total_stats:
            total_stats[key] += stats[key]

    print("\n" + "=" * 40)
    print("Total Summary:")
    print(f"  Files processed: {len(existing_sources)}")
    print(f"  External images found: {total_stats['found']}")
    print(f"  Downloaded: {total_stats['downloaded']}")
    print(f"  Already existed: {total_stats['skipped']}")
    print(f"  Failed: {total_stats['failed']}")


if __name__ == '__main__':
    main()
