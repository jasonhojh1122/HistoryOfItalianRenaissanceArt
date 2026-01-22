---
name: export-notes
description: Export notes from NOTES.md to individual markdown files for artists, locations, artworks, and terms following the templates defined in CLAUDE.md. Use when you need to sync reading notes to the structured article format.
---

# Export Notes

Export reading notes from `NOTES.md` to individual markdown files in `artists/`, `locations/`, and `artworks/` directories, plus a `terms.md` glossary file.

## Workflow

### 1. Read and Parse NOTES.md

Read `NOTES.md` and identify:
- **Artists**: Lines with `[Artist Name](wikipedia_link)` format, or the first level indent under h3, usually followed by artworks
- **Artworks**: Indented items under artists with artwork names and details
- **Locations**: Architecture sections with location links, or location lists after artwork name
- **Terms**: Items under the `## Terms` section containing art history terminology

### 2. Extract Entity Information

For each entity, extract:

**Artists**:
- Name and Wikipedia URL
- Biographical context (guild, influences, style)
- List of artworks with their details

**Artworks**:
- Name
- Artist
- Location (museum/church and city)
- Medium (fresco, marble, bronze, etc.)
- Notable details and significance
- Image URL

**Locations**:
- Name and Wikipedia URL
- City
- Architectural style
- Floor plan (if mentioned)
- List of artworks housed there

**Terms**:
- Term name
- Definition/translation
- Any additional context

### 3. Generate File Names

Convert names to PascalCase filenames:
- "Giotto di Bondone" -> `GiottoDiBondone.md`
- "Santa Croce" -> `SantaCroce.md`
- "Ognissanti Madonna" -> `OgnissantiMadonna.md`

Remove articles (The, A), prepositions, and punctuation. Keep proper nouns capitalized.

### 4. Apply Templates

**Artist Template**:
```markdown
# Artist Name

[Wikipedia](https://en.wikipedia.org/wiki/Artist_Name)

Brief biographical context: guild membership, teacher/influences, distinctive style.

## Artworks

### [Artwork A Name](../artworks/ArtworkAFile.md)
### [Artwork B Name](../artworks/ArtworkBFile.md)

```

**Location Template**:
```markdown
# Location Name

[Wikipedia](https://en.wikipedia.org/wiki/Location_Name)
[GoogleMap](links to google map if possble)

City, Country

Architectural style (if applicable).

![floor plan](../img/FloorPlan.png)

## Artworks

### [Artwork Name](../artworks/ArtworkFile.md)
```

**Artwork Template**:
```markdown
# Artwork Name

[Wikipedia](https://en.wikipedia.org/wiki/Artwork_Name)

- **Artist**: [Artist Name](../artists/ArtistFile.md)
- **Location**: [Location Name](../locations/LocationFile.md), City
- **Medium**: (fresco, marble, etc.)
- **Date**: (if known)

## Description

Key observations and art historical significance.

![img](image_url)
```

**Terms File** (`terms.md` in root directory):
```markdown
# Art History Terms

## Religious & Iconographic Terms

### Term Name
Definition or translation. Additional context if available.

## Artistic Techniques

### Term Name
Definition or explanation.
```

### 5. Cross-Reference Links

Ensure bidirectional linking:
- Artist files link to their artworks and artwork locations
- Location files link to artworks they house and their artists
- Artwork files link to their artist and location

### 6. Handle Updates

When updating existing files:
- Preserve existing content not in NOTES.md
- Add new artworks to existing artist/location files
- Update artwork details if changed in notes

## Usage

When the user asks to export notes:

1. Read `NOTES.md` to get current notes
2. Identify which sections/artists to export (or all if not specified)
3. For each artist found:
   - Create/update the artist file in `artists/`
   - Create/update artwork files in `artworks/` for each artwork
   - Create/update location files in `locations/` for each location mentioned
4. If `## Terms` section exists, create/update `terms.md` in the root directory
5. Report what was created/updated

## Example

If NOTES.md contains:

```
- [Giotto di Bondone](https://en.wikipedia.org/wiki/Giotto)
  - Crucifix, Santa Maria Novella, Florence
    ![img](image_url)
    - Earliest artwork by Giotto
```

Generate:

**artists/GiottoDiBondone.md**:
```markdown
# Giotto di Bondone

[Wikipedia](https://en.wikipedia.org/wiki/Giotto)

## Artworks

### [Crucifix](../artworks/CrucifixGiotto.md)
```

**artworks/CrucifixGiotto.md**:
```markdown
# Crucifix

- **Artist**: [Giotto di Bondone](../artists/GiottoDiBondone.md)
- **Location**: [Santa Maria Novella](../locations/SantaMariaNovella.md), Florence

## Description

Earliest artwork by Giotto.

![img](image_url)
```

**locations/SantaMariaNovella.md** (add to existing or create):
```markdown
# Santa Maria Novella

## Artworks

### [Crucifix](../artworks/CrucifixGiotto.md)
```

## Notes

- Use the `wikipedia-search` skill to look up missing Wikipedia links or images
- Preserve any Google Maps links already in location files
- Keep image references consistent (local `../img/` or external URLs)
