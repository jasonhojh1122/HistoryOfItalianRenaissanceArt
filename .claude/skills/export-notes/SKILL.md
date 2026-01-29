---
name: export-notes
description: Export notes from NOTES.md to individual markdown files for artists, locations, artworks, bible stories, and terms with automatic enrichment from Wikipedia and Google Maps. Use when you need to sync reading notes to the structured article format.
---

# Export Notes

Export reading notes from `NOTES.md` to individual markdown files in `artists/`, `locations/`, `artworks/`, and `biblestories/` directories, plus a `terms.md` glossary file.

## Workflow

### 1. Read and Parse NOTES.md

Read `NOTES.md` and identify:
- **Artists**: Lines with `[Artist Name](wikipedia_link)` format, or the first level indent under h3, usually followed by artworks
- **Artworks**: Indented items under artists with artwork names and details
- **Locations**: Architecture sections with location links, or location lists after artwork name
- **Terms**: Items under the `## Terms` section containing art technique terminology (not religious narratives)
- **Bible Stories**: Identified from two sources:
  1. Items under `## Terms` section that are biblical/religious narratives (Annunciation, Nativity, Crucifixion, etc.)
  2. Auto-detected from artwork names/context that depict religious subjects (e.g., "Adoration of the Magi", "Last Supper", "Baptism of Christ")

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

**Bible Stories**:
- Story name
- Summary/description
- Bible section (book, chapter, verse references)
- Wikipedia URL (if found)
- List of artworks depicting this story

### 3. Generate File Names

Convert names to PascalCase filenames:
- "Giotto di Bondone" -> `artists/GiottoDiBondone.md`
- "Santa Croce" -> `locations/SantaCroce.md`
- "Ognissanti Madonna" -> `artworks/OgnissantiMadonna.md`
- "Annunciation" -> `biblestories/Annunciation.md`
- "Last Supper" -> `biblestories/LastSupper.md`

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

(For religious subjects only) [Story Name](../biblestories/StoryFile.md) - Brief inline description if needed.

## Description

Key observations and art historical significance.

![img](image_url)
```

**Terms File** (`terms.md` in root directory):
```markdown
# Art History Terms

## Artistic Techniques

### Term Name
Definition or explanation.

## Iconographic Types

### Term Name
Definition or translation. Additional context if available.
```

**Bible Story Template** (`biblestories/` directory):
```markdown
# Story Name

[Wikipedia](https://en.wikipedia.org/wiki/Story_Name)

## Summary

Brief narrative summary of the biblical story.

## Biblical Reference

**Book(s)**: Gospel of Matthew, Gospel of Luke, etc.
**Chapters/Verses**: Matthew 1:18-25, Luke 2:1-20, etc.

## Artworks Depicting This Story

### [Artwork Name](../artworks/ArtworkFile.md)
- Artist, Location, Date
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

**For Bible Stories** - Use `wikipedia-search` skill to add:
- Summary from Wikipedia
- Specific biblical references (chapter/verse)
- Cross-references to related artworks in the project

### 6. Cross-Reference Links

Ensure bidirectional linking:
- Artist files link to their artworks and artwork locations
- Location files link to artworks they house and their artists
- Artwork files link to their artist, location, and bible story (in Biblical Context section)
- Bible story files link to artworks depicting them

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
4. For each bible story found (from Terms section or detected from artworks):
   - Create/update bible story files in `biblestories/`
   - Migrate religious narrative terms from `terms.md` to `biblestories/`
   - Keep only art technique terms (Christus triumphans, Christus patiens, tondo, etc.) in `terms.md`
5. If `## Terms` section exists, create/update `terms.md` in the root directory (art techniques only)
6. Report what was created/updated

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

[Crucifixion](../biblestories/Crucifixion.md) - Death of Jesus Christ on the cross at Golgotha.

## Description

Earliest artwork by Giotto. Revolutionary in its naturalistic depiction of Christ's suffering body, departing from the rigid Byzantine tradition.

![img](image_url)
```

**biblestories/Crucifixion.md**:
```markdown
# Crucifixion

[Wikipedia](https://en.wikipedia.org/wiki/Crucifixion_of_Jesus)

## Summary

The Crucifixion depicts the death of Jesus Christ on the cross at Golgotha. This central event in Christian theology represents Christ's sacrifice for the redemption of humanity's sins.

## Biblical Reference

**Book(s)**: All four Gospels
**Chapters/Verses**: Matthew 27:32-56, Mark 15:21-41, Luke 23:26-49, John 19:17-37

## Artworks Depicting This Story

### [Crucifix](../artworks/CrucifixGiotto.md)
- Giotto di Bondone, Santa Maria Novella, c. 1290
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

### Common Bible Stories Reference

Use this list to identify bible stories in artworks and create corresponding files in `biblestories/`:

**Old Testament**:
- **Creation of Adam** - God creates the first man (Genesis 2:7)
- **Expulsion from Paradise** - Adam and Eve banished from Eden (Genesis 3:22-24)
- **Story of Noah** - The flood and the ark (Genesis 6-9)
- **Sacrifice of Isaac** - Abraham's test of faith (Genesis 22:1-19)
- **Moses stories** - Burning bush, parting of Red Sea, receiving commandments
- **David and Goliath** - Young David defeats the giant (1 Samuel 17)
- **Judith and Holofernes** - Jewish heroine beheads Assyrian general (Book of Judith)

**New Testament - Life of Christ**:
- **Annunciation** - Angel Gabriel announces to Mary she will bear Jesus (Luke 1:26-38)
- **Visitation** - Mary visits Elizabeth (Luke 1:39-56)
- **Nativity** - Birth of Jesus in Bethlehem (Luke 2:1-20, Matthew 1:18-25)
- **Adoration of the Shepherds** - Shepherds visit the newborn Jesus (Luke 2:8-20)
- **Adoration of the Magi** - Wise men visit infant Jesus (Matthew 2:1-12)
- **Presentation in the Temple** - Jesus presented to Simeon (Luke 2:22-40)
- **Flight into Egypt** - Holy Family flees Herod (Matthew 2:13-23)
- **Baptism of Christ** - John baptizes Jesus in the Jordan (Matthew 3:13-17)
- **Temptation of Christ** - Satan tempts Jesus in the wilderness (Matthew 4:1-11)
- **Transfiguration** - Jesus revealed in glory on the mountain (Matthew 17:1-9)
- **Raising of Lazarus** - Jesus raises Lazarus from the dead (John 11:1-44)
- **Entry into Jerusalem** - Jesus's triumphal entry on Palm Sunday (Matthew 21:1-11)
- **Last Supper** - Jesus's final meal with disciples (Matthew 26:17-30)
- **Agony in the Garden** - Jesus prays at Gethsemane (Matthew 26:36-46)
- **Betrayal of Christ** - Judas betrays Jesus with a kiss (Matthew 26:47-56)
- **Flagellation** - Jesus scourged by Roman soldiers (Matthew 27:26)
- **Crucifixion** - Death of Jesus on the cross (Matthew 27:32-56)
- **Deposition/Descent from the Cross** - Christ's body removed from the cross
- **Lamentation/Pietà** - Mourning over Christ's body (derived from burial accounts)
- **Entombment** - Christ's body placed in the tomb (Matthew 27:57-60)
- **Resurrection** - Jesus rises from the dead (Matthew 28:1-10)
- **Noli me tangere** - Risen Christ appears to Mary Magdalene (John 20:11-18)
- **Ascension** - Jesus ascends to heaven (Acts 1:6-11)
- **Pentecost** - Holy Spirit descends on the apostles (Acts 2:1-13)

**Marian Subjects**:
- **Madonna and Child** - Virgin Mary with infant Jesus
- **Assumption** - Mary taken bodily to heaven (Catholic tradition)
- **Coronation of the Virgin** - Mary crowned Queen of Heaven (Catholic tradition)
- **Dormition of the Virgin** - Death of Mary (Eastern tradition)

**Saints**:
- **Martyrdom scenes** - Various saints' deaths (St. Stephen, St. Sebastian, etc.)
- **Stigmatization of St. Francis** - Francis receives Christ's wounds
- **Conversion of St. Paul** - Saul struck down on road to Damascus (Acts 9:1-19)
