#!/usr/bin/env python3
"""
Resize images in ./img to ensure all are under 10MB.

Reduces image dimensions progressively until the file size is under the limit.
"""

import argparse
import os
import sys
from pathlib import Path

try:
    from PIL import Image
    # Allow very large images (up to 500 megapixels)
    Image.MAX_IMAGE_PIXELS = 500_000_000
except ImportError:
    print("Error: Pillow is required. Install with: pip install Pillow", file=sys.stderr)
    sys.exit(1)


def get_file_size_mb(path: Path) -> float:
    """Get file size in megabytes."""
    return path.stat().st_size / (1024 * 1024)


def resize_image(img_path: Path, max_size_mb: float = 10.0, quality: int = 85) -> bool:
    """
    Resize an image to be under max_size_mb.

    Returns True if the image was resized, False if already under limit.
    """
    current_size = get_file_size_mb(img_path)

    if current_size <= max_size_mb:
        return False

    print(f"  Resizing {img_path.name} ({current_size:.1f}MB)...")

    # Open the image
    with Image.open(img_path) as img:
        # Convert to RGB if necessary (for JPEG output)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        original_width, original_height = img.size
        current_img = img.copy()
        scale = 1.0

        # Progressively reduce size until under limit
        while True:
            # Save to a temporary file to check size
            temp_path = img_path.with_suffix('.tmp.jpg')

            # Reduce scale
            if scale == 1.0:
                # First try just recompressing with lower quality
                current_img.save(temp_path, 'JPEG', quality=quality, optimize=True)
            else:
                new_width = int(original_width * scale)
                new_height = int(original_height * scale)
                resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                resized.save(temp_path, 'JPEG', quality=quality, optimize=True)

            new_size = get_file_size_mb(temp_path)

            if new_size <= max_size_mb:
                # Success - replace original
                temp_path.replace(img_path)
                print(f"    -> {new_size:.1f}MB (scale: {scale:.0%})")
                return True

            # Reduce scale for next iteration
            scale *= 0.8

            # Safety check - don't go too small
            if scale < 0.1:
                temp_path.unlink()
                print(f"    Warning: Could not reduce below {new_size:.1f}MB")
                return False

            # Clean up temp file for next iteration
            if temp_path.exists():
                temp_path.unlink()


def main():
    parser = argparse.ArgumentParser(
        description='Resize images to be under a maximum file size'
    )
    parser.add_argument(
        '--img-dir',
        type=Path,
        default=Path('img'),
        help='Directory containing images (default: img)'
    )
    parser.add_argument(
        '--max-size',
        type=float,
        default=10.0,
        help='Maximum file size in MB (default: 10.0)'
    )
    parser.add_argument(
        '--quality',
        type=int,
        default=85,
        help='JPEG quality for output (default: 85)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )

    args = parser.parse_args()

    if not args.img_dir.exists():
        print(f"Error: Directory not found: {args.img_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Image directory: {args.img_dir}")
    print(f"Max size: {args.max_size}MB")
    print(f"Quality: {args.quality}")
    if args.dry_run:
        print("Mode: DRY RUN")
    print("-" * 40)

    # Find all images
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.JPG', '.JPEG', '.PNG'}
    images = [f for f in args.img_dir.iterdir() if f.suffix in image_extensions]

    # Find oversized images
    oversized = []
    for img in sorted(images):
        size = get_file_size_mb(img)
        if size > args.max_size:
            oversized.append((img, size))

    if not oversized:
        print(f"\nAll {len(images)} images are under {args.max_size}MB")
        return

    print(f"\nFound {len(oversized)} image(s) over {args.max_size}MB:")
    for img, size in oversized:
        print(f"  {img.name}: {size:.1f}MB")

    if args.dry_run:
        print("\nDry run - no changes made")
        return

    print("\nResizing...")
    resized_count = 0
    for img, size in oversized:
        if resize_image(img, args.max_size, args.quality):
            resized_count += 1

    print("\n" + "=" * 40)
    print(f"Summary: Resized {resized_count} of {len(oversized)} oversized images")


if __name__ == '__main__':
    main()
