---
name: google-map-search
description: Generate a Google Maps link for a given location. Use when needing to create map links for location articles, find directions to museums/churches, or add navigation links to travel notes.
---

# Google Map Search

Generate Google Maps URLs for locations.

## Usage

Run the search script:

```bash
python3 scripts/gmap_search.py "Location Name"
```

For JSON output:

```bash
python3 scripts/gmap_search.py "Location Name" --json
```

### Search Options

Search for a specific type of location:

```bash
# Search with city context
python3 scripts/gmap_search.py "Uffizi Gallery" --city "Florence, Italy"

# Search for a specific place type
python3 scripts/gmap_search.py "Santa Maria Novella" --type church
```

Options:
- **--city**: Add city/region context to improve search accuracy
- **--type**: Specify place type (museum, church, gallery, palazzo, etc.)
- **--json**: Output as JSON

## Output

The script returns:
- **query**: The search query used
- **url**: Google Maps search URL
- **markdown**: Pre-formatted markdown link

## Example

```bash
python3 scripts/gmap_search.py "Basilica di Santa Croce" --city "Florence, Italy"
```

Output:
```
Query: Basilica di Santa Croce, Florence, Italy

URL: https://maps.google.com/?q=Basilica+di+Santa+Croce%2C+Florence%2C+Italy

Markdown: [GoogleMap](https://maps.google.com/?q=Basilica+di+Santa+Croce%2C+Florence%2C+Italy)
```

## Notes

- The script generates search URLs that work without an API key
- Adding city context improves accuracy for common location names
- Use the markdown output directly in location articles
