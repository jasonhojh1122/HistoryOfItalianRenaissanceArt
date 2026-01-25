---
name: export-notes
description: Export notes from NOTES.md to individual markdown files for artists, locations, artworks, and terms with automatic enrichment from Wikipedia and Google Maps. Use when you need to sync reading notes to the structured article format.
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

**Born**: c. year, place
**Died**: year, place

Biographical context from Wikipedia summary combined with notes: guild membership, teacher/influences, distinctive style.

## Artworks

### [Artwork A Name](../artworks/ArtworkAFile.md)
### [Artwork B Name](../artworks/ArtworkBFile.md)

```

**Location Template**:
```markdown
# Location Name

[Wikipedia](https://en.wikipedia.org/wiki/Location_Name)

[GoogleMap](url)

City, Country

**Type**: Basilica/Museum/Palazzo/Church
**Architectural style**: style (if applicable)

Brief description from Wikipedia.

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

## Biblical Context

(For religious subjects only) Explanation of the biblical story depicted with scripture reference.

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

### 5. Enrich Content

After creating/updating files, enrich them with additional data using other skills:

**For Artists** - Use `wikipedia-search` skill to add:
- Birth/death dates (e.g., **Born**: c. 1267, Florence, **Died**: 1337, Florence)
- Fuller biographical description from Wikipedia summary

**For Artworks** - Use `wikipedia-search` skill to add:
- Date field if missing
- Medium if found in Wikipedia
- **Biblical Context** section for religious subjects (Annunciation, Crucifixion, Last Supper, Madonna and Child, Pietà, Lamentation, Transfiguration, Baptism of Christ, Nativity, Adoration of the Magi, etc.) explaining the biblical story depicted with scripture reference

**For Locations** - Use `google-map-search` and `wikipedia-search` skills to add:
- `[GoogleMap](url)` link if missing
- Type (Basilica, Museum, Palazzo, Church, etc.)
- Brief description from Wikipedia

### 6. Cross-Reference Links

Ensure bidirectional linking:
- Artist files link to their artworks and artwork locations
- Location files link to artworks they house and their artists
- Artwork files link to their artist and location

### 7. Handle Updates

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

Generate (with enrichment from Wikipedia and Google Maps):

**artists/GiottoDiBondone.md**:
```markdown
# Giotto di Bondone

[Wikipedia](https://en.wikipedia.org/wiki/Giotto)

**Born**: c. 1267, Vespignano, Republic of Florence
**Died**: January 8, 1337, Florence

Italian painter and architect from Florence who worked during the Late Middle Ages. Considered the first of the great Italian masters, he initiated the decisive break with the Byzantine style and laid the foundation for the Renaissance.

## Artworks

### [Crucifix](../artworks/CrucifixGiotto.md)
```

**artworks/CrucifixGiotto.md**:
```markdown
# Crucifix

[Wikipedia](https://en.wikipedia.org/wiki/Crucifix_(Giotto,_Santa_Maria_Novella))

- **Artist**: [Giotto di Bondone](../artists/GiottoDiBondone.md)
- **Location**: [Santa Maria Novella](../locations/SantaMariaNovella.md), Florence
- **Medium**: Tempera on wood
- **Date**: c. 1290

## Biblical Context

The Crucifixion depicts the death of Jesus Christ on the cross at Golgotha, as described in all four Gospels (Matthew 27:32-56, Mark 15:21-41, Luke 23:26-49, John 19:17-37). This central event in Christian theology represents Christ's sacrifice for the redemption of humanity's sins.

## Description

Earliest artwork by Giotto. Revolutionary in its naturalistic depiction of Christ's suffering body, departing from the rigid Byzantine tradition.

![img](image_url)
```

**locations/SantaMariaNovella.md** (add to existing or create):
```markdown
# Santa Maria Novella

[Wikipedia](https://en.wikipedia.org/wiki/Santa_Maria_Novella)

[GoogleMap](https://www.google.com/maps/search/?api=1&query=Santa+Maria+Novella+Florence+Italy)

Florence, Italy

**Type**: Basilica
**Architectural style**: Gothic, Renaissance façade

The first great basilica in Florence and the city's principal Dominican church. The façade was completed by Leon Battista Alberti in 1470.

## Artworks

### [Crucifix](../artworks/CrucifixGiotto.md)
```

## Notes

- Use the `wikipedia-search` skill to look up missing Wikipedia links, images, dates, and descriptions
- Use the `google-map-search` skill to generate Google Maps links for locations
- Preserve any Google Maps links already in location files
- Keep image references consistent (local `../img/` or external URLs)

### Biblical Context Subjects

Add a **Biblical Context** section for artworks depicting these common religious subjects:
- **Annunciation** - Angel Gabriel announces to Mary she will bear Jesus (Luke 1:26-38)
- **Nativity** - Birth of Jesus in Bethlehem (Luke 2:1-20, Matthew 1:18-25)
- **Adoration of the Magi** - Wise men visit infant Jesus (Matthew 2:1-12)
- **Baptism of Christ** - John baptizes Jesus in the Jordan (Matthew 3:13-17)
- **Transfiguration** - Jesus revealed in glory on the mountain (Matthew 17:1-9)
- **Last Supper** - Jesus's final meal with disciples (Matthew 26:17-30)
- **Crucifixion** - Death of Jesus on the cross (Matthew 27:32-56)
- **Lamentation/Pietà** - Mourning over Christ's body (not directly in scripture, derived from burial accounts)
- **Resurrection** - Jesus rises from the dead (Matthew 28:1-10)
- **Madonna and Child** - Virgin Mary with infant Jesus
- **Assumption** - Mary taken bodily to heaven (Catholic tradition)
- **Coronation of the Virgin** - Mary crowned Queen of Heaven (Catholic tradition)
