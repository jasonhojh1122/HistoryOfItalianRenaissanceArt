---
name: check-exported
description: Verify all exported markdown files for structural integrity, valid links, and cross-reference consistency. Use to audit exported notes.
user_invocable: true
---

# Check Exported Files

Validates all exported markdown files in artists/, artworks/, locations/, biblestories/, and terms.md.

## Usage

/check-exported [directory]

Arguments:
- `directory`: Optional. One of: artists, artworks, locations, biblestories, terms. If omitted, checks all.

## Workflow

### Step 1: Run Validation Script

```bash
python3 .claude/skills/check-exported/scripts/check_exported.py --json
```

Use `--skip-images` flag if offline or to speed up validation:

```bash
python3 .claude/skills/check-exported/scripts/check_exported.py --json --skip-images
```

### Step 2: Review Results

Report issues by severity:
- **Errors**: Must be fixed (missing required fields, broken internal links)
- **Warnings**: Should be reviewed (missing backlinks, invalid image URLs)

### Step 3: Summarize for User

List all errors and warnings with file paths and specific issues found.

## Validation Rules

### Artist Files (artists/*.md)
- H1 heading with artist name
- Wikipedia link
- Born/Died fields (warning if missing)
- `## Artworks` section

### Artwork Files (artworks/*.md)
- H1 heading with artwork name
- Wikipedia link
- Required fields: Artist, Location, Medium, Date
- `## Description` section
- Artist and Location links point to existing files

### Location Files (locations/*.md)
- H1 heading with location name
- Wikipedia link
- GoogleMap link (warning if missing)
- City line
- Type field
- `## Artworks` section

### Bible Story Files (biblestories/*.md)
- H1 heading with story name
- Wikipedia link
- `## Summary` section
- `## Biblical Reference` section
- `## Artworks Depicting This Story` section

### Cross-References
- Artwork links to artist → artist should list that artwork
- Artwork links to location → location should list that artwork
- Artwork has Biblical Context → bible story should list that artwork

### Image Validation
- Local images (`../img/*`): File must exist
- External URLs: HTTP HEAD request must return 2xx status

## Example Output

```
Checking exported files...

artists/: 53 files
  ✓ 51 valid
  ⚠ 2 warnings
    - GiottoDiBondone.md: Missing artwork backlink to StFrancisUndergoingTheTestByFire.md

artworks/: 107 files
  ✓ 100 valid
  ✗ 5 errors
    - BrokenArtwork.md: Missing required field: Artist
  ⚠ 2 warnings
    - SomeArtwork.md: Image URL returns 404

locations/: 37 files
  ✓ 37 valid

biblestories/: 21 files
  ✓ 21 valid

terms.md: ✓ valid

Summary: 218 files checked, 5 errors, 4 warnings
```
