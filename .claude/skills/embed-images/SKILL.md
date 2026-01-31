---
name: embed-images
description: Download all external image links in NOTES.md, save them under ./img, and update the links to reference the local files. Use when needing to embed remote images locally for offline access or to preserve images.
---

# Embed Images

Download all external images referenced in NOTES.md and update the markdown to use local paths.

## Usage

Run the embed script:

```bash
python3 scripts/embed_images.py
```

### Options

```bash
# Dry run - show what would be downloaded without making changes
python3 scripts/embed_images.py --dry-run

# Specify a different source file
python3 scripts/embed_images.py --source path/to/file.md

# Specify a different image directory
python3 scripts/embed_images.py --img-dir path/to/images
```

## What It Does

1. Scans NOTES.md for image links with external URLs (http/https)
2. Downloads each image to the `./img` folder
3. Generates unique filenames based on the URL (sanitized, with hash suffix)
4. Updates NOTES.md to reference the local image paths
5. Skips images that already point to local paths (e.g., `img/...`)

## Output

The script reports:
- Number of external images found
- Download progress for each image
- Any errors encountered
- Summary of changes made

## Example

Before:
```markdown
![img](https://upload.wikimedia.org/wikipedia/commons/example.jpg)
```

After:
```markdown
![img](img/example_abc123.jpg)
```

## Notes

- Only processes URLs starting with `http://` or `https://`
- Preserves the original alt text in image links
- Creates unique filenames using a hash of the URL to avoid conflicts
- Existing local images are not re-downloaded
- The script creates a backup of NOTES.md before making changes
