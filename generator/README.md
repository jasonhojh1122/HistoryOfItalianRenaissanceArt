# Renaissance Art Site Generator

A static site generator that transforms markdown notes into a browsable HTML website for Italian Renaissance Art research.

## Usage

```bash
cd generator
npm install
npm run build
```

The generated site will be output to `../site/`.

## Project Structure

```
generator/
├── src/
│   ├── index.js          # Entry point
│   ├── generator.js      # Main site generation logic
│   ├── parser.js         # Markdown parsing and metadata extraction
│   ├── relationships.js  # Content indexing and relationship building
│   └── templates.js      # HTML templates for all page types
├── static/
│   └── styles.css        # Site styling
└── package.json
```

## How It Works

1. **Indexing**: Scans `artists/`, `locations/`, `artworks/`, and `biblestories/` directories for markdown files
2. **Parsing**: Extracts metadata and content from each markdown file
3. **Relationship Building**: Links artworks to their artists, locations, and bible stories
4. **Generation**: Creates HTML pages using templates
5. **Asset Copying**: Copies CSS and images from `img/` to the output directory

## Content Types

### Artists (`artists/*.md`)

Expected format:
```markdown
# Artist Name

[Wikipedia](https://...)

Biography text here.

## Artworks

### [Artwork Title](../artworks/ArtworkFile.md)
```

### Locations (`locations/*.md`)

Expected format:
```markdown
# Location Name

[Wikipedia](https://...)
[GoogleMap](https://...)

City Name

**Architectural style**: Gothic/Romanesque/etc.

![floor plan](../img/floorplan.png)

## Artworks

### [Artwork Title](../artworks/ArtworkFile.md)
```

### Artworks (`artworks/*.md`)

Expected format:
```markdown
# Artwork Title

- **Artist**: [Artist Name](../artists/ArtistFile.md)
- **Location**: [Location Name](../locations/LocationFile.md), City
- **Medium**: Fresco/Oil on panel/etc.
- **Date**: c. 1450

## Biblical Context

[Story Name](../biblestories/StoryFile.md) - Additional context here.

## Description

Description of the artwork.

![alt text](https://image-url.jpg)
```

### Bible Stories (`biblestories/*.md`)

Expected format:
```markdown
# Story Name

Alternate Name (e.g., Chinese translation)

[Wikipedia](https://...)

## Summary

Summary of the biblical narrative.

**Book(s)**: Genesis/Matthew/etc.
**Chapters/Verses**: 1:1-10

## Artworks

### [Artwork Title](../artworks/ArtworkFile.md)
```

## Generated Output

```
site/
├── index.html              # Home page with artist/location/story lists
├── styles.css              # Copied from static/
├── img/                    # Copied from project root img/
├── artists/
│   └── *.html              # Individual artist pages
├── locations/
│   └── *.html              # Individual location pages
├── artworks/
│   └── *.html              # Individual artwork pages
└── biblestories/
    └── *.html              # Bible story pages
```

## Features

- Converts `.md` links to `.html` in generated output
- External links open in new tabs
- Responsive design with mobile support
- Artwork cards with images on artist/location/bible story pages
- Locations grouped by city on the index page
- Cross-references between artworks, artists, locations, and bible stories
- **Interactive sorting**: Artwork grids can be sorted by Date, Title, or Artist (client-side)
  - Date is the default sort order (artworks are pre-sorted at build time)
  - Artist sorting only appears on pages with multiple artists (locations, bible stories)
  - Handles various date formats: "1423", "c. 1427", "1334–1343", "1440s"
- **Artist display on cards**: Artwork cards show artist name as a link on location and bible story pages (when multiple artists are present)

## Dependencies

- **glob**: File pattern matching for content discovery
- **marked**: Markdown to HTML conversion
