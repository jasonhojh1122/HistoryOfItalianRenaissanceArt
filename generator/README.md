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
│   ├── styles.css        # Site styling
│   ├── tabs.js           # Tab navigation for index page
│   ├── sort.js           # Client-side artwork sorting
│   ├── search.js         # Index page search functionality
│   └── map.js            # Interactive map with Leaflet
├── data/
│   └── coordinates.json  # Lat/lng coordinates for location markers
└── package.json
```

## How It Works

1. **Indexing**: Scans `artists/`, `locations/`, `artworks/`, and `biblestories/` directories for markdown files
2. **Parsing**: Extracts metadata and content from each markdown file
3. **Relationship Building**: Links artworks to their artists, locations, and bible stories
4. **Coordinate Loading**: Reads location coordinates from `data/coordinates.json` for the map
5. **Generation**: Creates HTML pages using templates
6. **Asset Copying**: Copies CSS, JS, and images from `img/` to the output directory

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

### Coordinates (`data/coordinates.json`)

Maps location IDs to geographic coordinates for the interactive map:
```json
{
  "UffiziGallery": { "lat": 43.7687, "lng": 11.2551 },
  "Bargello": { "lat": 43.7702, "lng": 11.2580 }
}
```

## Generated Output

```
site/
├── index.html              # Home page with tabbed navigation
├── styles.css              # Site styling
├── tabs.js                 # Tab navigation script
├── sort.js                 # Artwork sorting script
├── search.js               # Search functionality script
├── map.js                  # Interactive map script
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

### Index Page

- **Tabbed Navigation**: Five tabs organize content:
  - **Artists**: Alphabetical list with artwork counts
  - **Locations**: Grouped by city with artwork counts
  - **Bible Stories**: List with alternate names
  - **Timeline**: Visual timeline of artworks by century with cards
  - **Map**: Interactive map of all locations

- **Search**: Filter artists, locations, and stories by name

### Interactive Map

- Powered by Leaflet.js with OpenStreetMap tiles
- **Heat map visualization**: Circle markers vary in size and color based on artwork count
  - Size: 12px (few artworks) to 40px (many artworks)
  - Color gradient: Gold → Terracotta → Deep terracotta
- Click markers to see location name, city, and artwork count
- Legend shows the size/color scale
- Lazy-loaded when the Map tab is activated

### Artwork Display

- **Sorting**: Artwork grids can be sorted by Date, Title, or Artist (client-side)
  - Date is the default sort order (artworks are pre-sorted at build time)
  - Artist sorting only appears on pages with multiple artists
  - Handles various date formats: "1423", "c. 1427", "1334–1343", "1440s"

- **Cards**: Show title, artist link, medium, date, description, and image
  - Artist links appear on location and bible story pages (when multiple artists)

### Cross-References

- Artworks linked to their artists, locations, and bible stories
- Artwork counts displayed as badges on index page lists
- Converts `.md` links to `.html` in generated output
- External links open in new tabs

### Design

- Responsive layout with mobile support
- Museum-inspired aesthetic with Renaissance color palette
- Smooth animations and hover effects

## Dependencies

- **glob**: File pattern matching for content discovery
- **marked**: Markdown to HTML conversion

## External Libraries (CDN)

- **Leaflet 1.9.4**: Interactive map (loaded only on index page)
