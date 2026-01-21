---
name: wikipedia-search
description: Search Wikipedia for any term and retrieve the page URL, summary, and main image URL. Use when needing to look up information on Wikipedia, get a Wikipedia link for a subject, find the Wikipedia image for an artist/artwork/location, or gather reference information for research notes.
---

# Wikipedia Search

Search Wikipedia and retrieve structured information: page URL, summary text, and main image URL.

## Usage

Run the search script:

```bash
python3 scripts/wiki_search.py "Search Term"
```

For JSON output:

```bash
python3 scripts/wiki_search.py "Search Term" --json
```

### Summary Length Option

Control how much of the summary is returned with `--summary-length`:

```bash
# Short summary (1-2 sentences)
python3 scripts/wiki_search.py "Botticelli" --summary-length short

# Medium summary (3-4 sentences)
python3 scripts/wiki_search.py "Botticelli" --summary-length medium

# Full summary (default)
python3 scripts/wiki_search.py "Botticelli" --summary-length full
```

Options:
- **short**: 1-2 sentences (~200 characters) - ideal for quick reference
- **medium**: 3-4 sentences (~500 characters) - good for artist bios
- **full**: Complete summary (default) - full article extract

## Output

The script returns:
- **title**: The Wikipedia article title
- **url**: Full Wikipedia page URL
- **summary**: Article extract/summary
- **image_url**: URL of the main image (or null if none)

## Example

```bash
python3 scripts/wiki_search.py "Botticelli"
```

Output:
```
Title: Sandro Botticelli

URL: https://en.wikipedia.org/wiki/Sandro_Botticelli

Summary: Alessandro di Mariano di Vanni Filipepi, better known as Sandro Botticelli...

Image: https://upload.wikimedia.org/wikipedia/commons/...
```

## Notes

- The script automatically handles spaces and special characters in search terms
- If an exact match isn't found, it falls back to Wikipedia's search API
- Use `--json` flag when you need to parse the output programmatically
