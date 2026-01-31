---
name: auto-research
description: Research and document notable artworks at a museum, church, or other location. Creates artwork, artist, and bible story markdown files marked as self-researched. Use when user wants to research artworks at a specific place.
---

# Auto-Research

Research and document notable artworks at a given location.

## Usage

```
/auto-research <place name>
```

## Workflow

### Step 1: Research Location on Wikipedia

Use the wikipedia-search skill to get authoritative info about the location:

```bash
python3 .claude/skills/wikipedia-search/scripts/wiki_search.py "<Location Name>" --json
```

This establishes the canonical location name and provides context about its collection.

### Step 2: Search for Notable Artworks

Search for artworks specifically mentioning the location:

```
WebSearch: "famous artworks" "<exact location name>" site:wikipedia.org
```

Collect 5-10 candidate artworks. For each, note the artwork name and claimed location.

### Step 3: Verify Each Artwork's Location

**Critical**: Before creating any file, verify the artwork is actually at this location.

For each candidate artwork:
```bash
python3 .claude/skills/wikipedia-search/scripts/wiki_search.py "<Artwork Name>" --json
```

Read the summary carefully. Only proceed if:
- The summary explicitly states the artwork is at this location, OR
- The summary mentions the location as current home (not "formerly at" or "originally from")

**Skip** artworks where:
- Location is ambiguous or not mentioned
- Artwork has moved to a different museum
- Multiple versions exist in different locations (unless you can identify which version)

### Step 4: Validate Image URLs

For each verified artwork, validate the image URL works:

```bash
python3 .claude/skills/auto-research/scripts/validate_image.py "<image_url>"
```

If invalid:
- Try the wikipedia-search again with slightly different search terms
- If still no valid image, omit the image line rather than include a broken URL

### Step 5: Create Artwork Files

For each verified artwork, check if `artworks/<PascalCaseName>.md` exists. If not, create it:

```markdown
# <Artwork Name>

[Wikipedia](<url>)

- **Artist**: [<Artist Name>](../artists/<ArtistFile>.md)
- **Location**: [<Location Name>](../locations/<LocationFile>.md), <City>
- **Medium**: <medium>
- **Date**: <date>
- **Source**: Self-researched

## Description

<2-3 sentences from Wikipedia summary about the artwork>

![img](<validated_image_url>)
```

### Step 6: Create Supporting Files

For each artwork, create missing support files:

**Artist** (if not in `artists/`):
```bash
python3 .claude/skills/wikipedia-search/scripts/wiki_search.py "<Artist Name>" --summary-length medium --json
```

**Bible Story** (if religious subject, not in `biblestories/`):
```bash
python3 .claude/skills/wikipedia-search/scripts/wiki_search.py "<Story Name> Bible" --json
```

**Location** (if not in `locations/`): Create with `**Source**: Self-researched`

### Step 7: Update Location File

If `locations/<LocationName>.md` exists, append new artworks to its `## Artworks` section.

## File Naming

Convert names to PascalCase: "Birth of Venus" → `BirthOfVenus.md`

## Templates

See `templates/` directory for file formats. Always include `- **Source**: Self-researched` for auto-researched content.
