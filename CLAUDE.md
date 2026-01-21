# Project Purpose

This project contains notes on Italian Renaissance Art for my upcoming travel

# Structure

- `NOTES.md` - Reading notes following the textbook "History Of Italian Renaissance Art Painting, Sculpture, Architecture Hartt, Frederick 7th Ed 2011"
- `README.md` - Navigation index with links organized by location, artist, period, and medium
- `artists/` - Individual artist pages
- `locations/` - Individual location pages
- `img/` - Local images (floor plans, diagrams, etc.)

# Article Templates

## Artist Article Template

Each artist file should follow this structure:

```markdown
# Artist Name

[Wikipedia](https://en.wikipedia.org/wiki/Artist_Name)

Brief biographical context: guild membership, teacher/influences, distinctive style.

## Artworks

### Artwork Name

- **Location**: [Location Name](../locations/LocationFile.md), City
- **Medium**: (if relevant - fresco, marble, bronze, etc.)
- Key observations and significance

![img](image_url_or_path)
```

### Template Notes

- Wikipedia link at the top for quick reference
- Brief biographical context (guild, teacher, style)
- Each artwork as a separate heading under Artworks section
- Location links connect to location articles
- Notable details and art historical significance
- Image at the end of each artwork entry

## Location Article Template

Each location file should follow this structure:

```markdown
# Location Name

[Wikipedia](https://en.wikipedia.org/wiki/Location_Name)

[GoogleMap](link_to_google_map)

City, Country

**Architectural style**: (if applicable - Italian Gothic, Renaissance, etc.)

![floor plan](../img/FloorPlan.png) (if applicable - Italian Gothic, Renaissance, etc.)

## Artworks

### Artwork Name

- **Artist**: [Artist Name](../artists/ArtistFile.md)
- **Medium**: (fresco, sculpture, altarpiece, etc.)
- Notable details

![img](image_url_or_path)
```

### Template Notes

- Wikipedia and google map link at the top
- City location
- Architectural style for churches/buildings
- Floor plan image when available (helps locate artworks during visit)
- Each artwork as a separate heading
- Artist links connect to artist articles
- Medium specified for each work
