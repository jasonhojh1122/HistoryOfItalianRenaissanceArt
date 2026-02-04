---
name: auto-research
description: Research and document notable artworks at a museum, church, or other location. Appends findings to AUTO_RESEARCH_NOTES.md organized by location. Use when user wants to research artworks at a specific place.
---

# Auto-Research

Research and document notable artworks at a given location, writing results to `AUTO_RESEARCH_NOTES.md`.

## Usage

```
/auto-research <place name>
```

## Workflow

### Step 1: Research Location on Wikipedia

Use the wikipedia-search skill to get authoritative info about the location:

```bash
python3 .claude/skills/wikipedia-search/scripts/wiki_search.py "<Location Name>" --summary-length medium --json
```

This establishes the canonical location name and provides context about its collection. **Important**: Extract a 2-3 sentence description of the location from the Wikipedia summary to include in the location header section.

### Step 1.5: Check for Existing Research

Read `AUTO_RESEARCH_NOTES.md` if it exists and check if this location has already been researched:

- If the location section exists, note which artworks are already documented
- Skip artworks that are already in the file
- Only add new artworks not already documented

### Step 2: Search for Notable Artworks

**2a. Extract from Wikipedia page directly:**

Using the Wikipedia URL obtained in Step 1, fetch the full page content:

```
WebFetch: <wikipedia_url>
Prompt: "Extract all notable artworks mentioned on this page. For each artwork, list: artwork name, artist name, date/period if mentioned, and any description. Focus on paintings, sculptures, frescoes, and other significant works housed at this location."
```

This often yields the most accurate list since museum/church Wikipedia pages typically have dedicated sections listing their collections.

**2b. Supplement with web search:**

Search for additional artworks that may not be on the main Wikipedia page:

```
WebSearch: "famous artworks" "<exact location name>" site:wikipedia.org
```

**2c. Combine results:**

Merge findings from both sources, collecting 5-10 candidate artworks. For each, note the artwork name and claimed location. Prefer information from the direct Wikipedia page extraction (2a) when there are conflicts.

### Step 3: Research Each Artwork on Wikipedia

For each candidate artwork, search Wikipedia:

```bash
python3 .claude/skills/wikipedia-search/scripts/wiki_search.py "<Artwork Name>" --json
```

**If Wikipedia page EXISTS:**
1. Verify the artwork is at this location (check summary for location mention)
2. Extract the Wikipedia URL from the search results
3. Extract the image URL from the search results
4. Document with link format: `- [Artwork Name](wikipedia_url)`
5. Include the `![img](image_url)` line

**If Wikipedia page DOES NOT EXIST:**
1. Try alternate search terms (e.g., add artist name: `"<Artwork Name> <Artist Name>"`)
2. If still no results, document WITHOUT link: `- Artwork Name`
3. Do NOT include an image line

**Skip artworks where:**
- Location is ambiguous or artwork has moved elsewhere
- Multiple versions exist and you can't identify which

### Step 4: Validate Image URLs

For each verified artwork, validate the image URL works:

```bash
python3 .claude/skills/auto-research/scripts/validate_image.py "<image_url>"
```

If invalid:
- Try the wikipedia-search again with slightly different search terms
- If still no valid image, omit the image line rather than include a broken URL

### Step 5: Write to AUTO_RESEARCH_NOTES.md

**Before writing each artwork entry, verify:**
- [ ] Wikipedia was searched for this artwork
- [ ] If Wikipedia page exists: URL is included in `[Name](url)` format
- [ ] If Wikipedia page exists: Image URL is included as `![img](url)`
- [ ] If no Wikipedia page: Name is plain text (no link brackets)
- [ ] If no Wikipedia page: No image line included

Append findings to `AUTO_RESEARCH_NOTES.md` following the format documented below.

If the file doesn't exist, create it with the header. If the location section already exists, append new artworks/artists/stories to the existing section.

### Step 6: Add Supporting Information

In the same location section of `AUTO_RESEARCH_NOTES.md`:

**Artists**: For each artist not already in the file:
```bash
python3 .claude/skills/wikipedia-search/scripts/wiki_search.py "<Artist Name>" --summary-length medium --json
```

Add to the `### Artists` subsection.

**Bible Stories**: For religious subjects:
```bash
python3 .claude/skills/wikipedia-search/scripts/wiki_search.py "<Story Name> Bible" --json
```

Add to the `### Bible Stories` subsection.

### Step 7: Report Summary

After completing research:

1. Report what was added:
   - Number of new artworks documented
   - Number of new artists added
   - Number of new bible stories added

2. Remind the user:
   > Run `/export-notes` to generate individual files from your research notes.

## AUTO_RESEARCH_NOTES.md Format

The file is organized by location:

```markdown
# Auto-Researched Notes

<!-- Generated by auto-research skill. Use /export-notes to generate individual files. -->

## Accademia, Venice

<!-- Last updated: 2024-01-15 -->

- [Gallerie dell'Accademia](https://en.wikipedia.org/wiki/...)
  - **Type**: Museum
  - **Description**: The Gallerie dell'Accademia is a museum gallery of pre-19th-century art in Venice, housed in the former Santa Maria della Carità complex. It contains the most comprehensive collection of Venetian paintings from the Byzantine and Gothic periods through the Renaissance.

### Artworks

<!-- Artwork WITH Wikipedia page - MUST include link AND image -->
- [San Giobbe Altarpiece](https://en.wikipedia.org/wiki/San_Giobbe_Altarpiece)
  - **Artist**: [Giovanni Bellini](https://en.wikipedia.org/wiki/Giovanni_Bellini)
  - **Medium**: Oil on panel
  - **Date**: c. 1487
  - **Description**: 2-3 sentences...
  ![img](https://upload.wikimedia.org/wikipedia/commons/thumb/...)

<!-- Artwork WITHOUT Wikipedia page - NO link brackets, NO image line -->
- Madonna with Saints
  - **Artist**: [Giovanni Bellini](https://en.wikipedia.org/wiki/Giovanni_Bellini)
  - **Medium**: Oil on panel
  - **Date**: c. 1490
  - **Description**: 2-3 sentences...

<!-- Another artwork WITH Wikipedia page - MUST include link AND image -->
- [Tempest](https://en.wikipedia.org/wiki/The_Tempest_(Giorgione))
  - **Artist**: [Giorgione](https://en.wikipedia.org/wiki/Giorgione)
  - **Medium**: Oil on canvas
  - **Date**: c. 1508
  - **Description**: 2-3 sentences...
  ![img](https://upload.wikimedia.org/wikipedia/commons/thumb/...)

### Artists

- [Giovanni Bellini](https://en.wikipedia.org/wiki/...)
  - **Born**: c. 1430, Venice
  - **Died**: 1516, Venice
  - Biography summary...

- [Giorgione](https://en.wikipedia.org/wiki/...)
  - **Born**: c. 1477, Castelfranco Veneto
  - **Died**: 1510, Venice
  - Biography summary...

### Bible Stories

- [Madonna and Child](https://en.wikipedia.org/wiki/...)
  - **Book(s)**: Gospels of Matthew, Luke
  - **Chapters/Verses**: Matthew 1-2, Luke 1-2
  - Summary...

## Terms

- **Sacra conversazione**: A type of religious painting showing the Madonna and Child with saints in a unified space, rather than separate panels.
```

## File Naming

When exported by `/export-notes`, names convert to PascalCase: "Birth of Venus" → `BirthOfVenus.md`

## Templates

Content in AUTO_RESEARCH_NOTES.md will be marked with `**Source**: Self-researched` when exported to individual files by the export-notes skill. This distinguishes auto-researched content from content derived from NOTES.md (the reading notes).
