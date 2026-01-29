---
name: auto-research
description: Research and document notable artworks at a museum, church, or other location. Creates artwork, artist, and bible story markdown files marked as self-researched.
---

# Auto-Research

Automatically research and document notable artworks at a given location (museum, church, city).

## Usage

```
/auto-research <place name>
```

### Examples

```
/auto-research Galleria dell'Accademia Florence
/auto-research Santa Maria Novella
/auto-research San Marco Venice
```

## Workflow

### Step 1: Search for Notable Artworks

Use WebSearch to find the most notable/must-see artworks at the location:

```
WebSearch: "most famous artworks at [location name]" OR "[location name] notable paintings sculptures"
```

Identify 5-10 key artworks that are highlights of the collection.

### Step 2: For Each Artwork Found

1. **Check if artwork already exists**: Look in `artworks/` directory
2. **If not exists, research it**:
   - Use `python3 scripts/wiki_search.py "[Artwork Name]" --json` to get Wikipedia info
   - Extract: title, url, summary, image_url
3. **Create artwork markdown file** with `- **Source**: Self-researched` field

### Step 3: Create Supporting Files

For each artwork:
1. **Check if artist exists** in `artists/` - create if missing using wikipedia-search
2. **Check if bible story exists** in `biblestories/` (for religious subjects) - create if missing
3. **Check if location exists** in `locations/` - create if missing

### Step 4: Update Location File

If the location file exists in `locations/`, append newly found artworks to its `## Artworks` section.

## File Templates

See [templates/](../../../templates/) for canonical file formats:
- `templates/artwork.md` - Artwork file format (include `- **Source**: Self-researched`)
- `templates/artist.md` - Artist file format
- `templates/location.md` - Location file format (include `**Source**: Self-researched`)
- `templates/biblestory.md` - Bible story file format

## File Naming Convention

Convert artwork/artist/location names to PascalCase without spaces:
- "Birth of Venus" → `BirthOfVenus.md`
- "Sandro Botticelli" → `SandroBotticelli.md`
- "Santa Maria Novella" → `SantaMariaNovella.md`

## Notes

- Always include `- **Source**: Self-researched` for auto-researched artworks
- Always include `**Source**: Self-researched` for auto-researched locations
- This field triggers the "Self-researched" badge in the generated site
- Skip artworks that already have markdown files
- Update existing location files rather than creating duplicates
- Use the wikipedia-search script for consistent data retrieval
