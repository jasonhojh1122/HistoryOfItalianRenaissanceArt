import { glob } from 'glob';
import path from 'path';
import { parseFile } from './parser.js';

/**
 * Build an index of all content and relationships
 */
export async function buildIndex(rootDir) {
  const index = {
    artists: {},
    locations: {},
    artworks: {},
    biblestories: {},
    byCity: {}  // locations grouped by city
  };

  // Parse all artworks first (they contain the relationship data)
  const artworkFiles = await glob('artworks/*.md', { cwd: rootDir });
  for (const file of artworkFiles) {
    const parsed = await parseFile(path.join(rootDir, file));
    index.artworks[parsed.id] = {
      ...parsed,
      artistId: parsed.metadata.artistFile,
      locationId: parsed.metadata.locationFile,
      bibleStoryId: parsed.metadata.bibleStoryFile
    };
  }

  // Parse all artists
  const artistFiles = await glob('artists/*.md', { cwd: rootDir });
  for (const file of artistFiles) {
    const parsed = await parseFile(path.join(rootDir, file));
    index.artists[parsed.id] = {
      ...parsed,
      artworks: []  // Will be populated below
    };
  }

  // Parse all locations
  const locationFiles = await glob('locations/*.md', { cwd: rootDir });
  for (const file of locationFiles) {
    const parsed = await parseFile(path.join(rootDir, file));
    index.locations[parsed.id] = {
      ...parsed,
      artworks: []  // Will be populated below
    };

    // Group by city
    const city = parsed.metadata.city || 'Unknown';
    if (!index.byCity[city]) {
      index.byCity[city] = [];
    }
    index.byCity[city].push(parsed.id);
  }

  // Parse all bible stories
  const bibleStoryFiles = await glob('biblestories/*.md', { cwd: rootDir });
  for (const file of bibleStoryFiles) {
    const parsed = await parseFile(path.join(rootDir, file));
    index.biblestories[parsed.id] = {
      ...parsed,
      artworks: []  // Will be populated below
    };
  }

  // Build relationships from artworks to artists, locations, and bible stories
  for (const [artworkId, artwork] of Object.entries(index.artworks)) {
    // Link artwork to artist
    if (artwork.artistId && index.artists[artwork.artistId]) {
      index.artists[artwork.artistId].artworks.push(artworkId);
    }

    // Link artwork to location
    if (artwork.locationId && index.locations[artwork.locationId]) {
      index.locations[artwork.locationId].artworks.push(artworkId);
    }

    // Link artwork to bible story
    if (artwork.bibleStoryId && index.biblestories[artwork.bibleStoryId]) {
      index.biblestories[artwork.bibleStoryId].artworks.push(artworkId);
    }
  }

  return index;
}

/**
 * Get all artworks for an artist with full data
 */
export function getArtistArtworks(index, artistId) {
  const artist = index.artists[artistId];
  if (!artist) return [];

  return artist.artworks.map(artworkId => index.artworks[artworkId]).filter(Boolean);
}

/**
 * Get all artworks for a location with full data
 */
export function getLocationArtworks(index, locationId) {
  const location = index.locations[locationId];
  if (!location) return [];

  return location.artworks.map(artworkId => index.artworks[artworkId]).filter(Boolean);
}

/**
 * Get sorted list of artists by name
 */
export function getSortedArtists(index) {
  return Object.values(index.artists)
    .sort((a, b) => a.metadata.title.localeCompare(b.metadata.title));
}

/**
 * Get sorted list of locations by name
 */
export function getSortedLocations(index) {
  return Object.values(index.locations)
    .sort((a, b) => a.metadata.title.localeCompare(b.metadata.title));
}

/**
 * Get locations grouped by city
 */
export function getLocationsByCity(index) {
  // Geographic order from north to south
  const cityOrder = [
    'Milan',
    'Venice',
    'Florence',
    'Vatican City',
    'Rome',
    'Naples',
    'Pompeii'
  ];

  const result = {};

  for (const [city, locationIds] of Object.entries(index.byCity)) {
    // Remove ", Italy" suffix from city name
    const cleanCity = city.replace(/, Italy$/, '');
    result[cleanCity] = locationIds
      .map(id => index.locations[id])
      .filter(Boolean)
      .sort((a, b) => a.metadata.title.localeCompare(b.metadata.title));
  }

  // Sort cities by geographic order (north to south)
  return Object.fromEntries(
    Object.entries(result).sort(([a], [b]) => {
      const indexA = cityOrder.indexOf(a);
      const indexB = cityOrder.indexOf(b);
      // Put unknown cities at the end
      if (indexA === -1 && indexB === -1) return a.localeCompare(b);
      if (indexA === -1) return 1;
      if (indexB === -1) return -1;
      return indexA - indexB;
    })
  );
}

/**
 * Get all artworks for a bible story with full data
 */
export function getBibleStoryArtworks(index, bibleStoryId) {
  const bibleStory = index.biblestories[bibleStoryId];
  if (!bibleStory) return [];

  return bibleStory.artworks.map(artworkId => index.artworks[artworkId]).filter(Boolean);
}

/**
 * Get sorted list of bible stories by name
 */
export function getSortedBibleStories(index) {
  return Object.values(index.biblestories)
    .sort((a, b) => a.metadata.title.localeCompare(b.metadata.title));
}

/**
 * Get century label from a year
 */
function getCenturyLabel(year) {
  if (year === Infinity || isNaN(year)) return null;

  // Handle BCE years (negative)
  if (year < 0) {
    const century = Math.ceil(Math.abs(year) / 100);
    const suffix = century === 1 ? 'st' : century === 2 ? 'nd' : century === 3 ? 'rd' : 'th';
    return `${century}${suffix} Century BCE`;
  }

  // Handle early CE/AD years (1st-12th century)
  if (year > 0 && year < 1200) {
    const century = Math.floor(year / 100) + 1;
    const suffix = century === 1 ? 'st' : century === 2 ? 'nd' : century === 3 ? 'rd' : 'th';
    return `${century}${suffix} Century`;
  }

  // Handle Renaissance and later (13th century+)
  const century = Math.floor(year / 100) + 1;
  const names = {
    13: '13th Century (Duecento)',
    14: '14th Century (Trecento)',
    15: '15th Century (Quattrocento)',
    16: '16th Century (Cinquecento)'
  };
  return names[century] || `${century}th Century`;
}

/**
 * Parse date string into a number for sorting
 * Returns negative numbers for BCE dates
 */
function parseArtworkDateForTimeline(dateStr) {
  if (!dateStr) return Infinity;

  const cleaned = dateStr.replace(/^(c\.|ca\.|circa)\s*/i, '').trim();
  const isBCE = /BCE|BC/i.test(cleaned);

  // Handle century notation like "2nd century BCE" or "1st century AD"
  const centuryMatch = cleaned.match(/(\d+)(?:st|nd|rd|th)\s+century/i);
  if (centuryMatch) {
    const centuryNum = parseInt(centuryMatch[1], 10);
    // Use middle of century for sorting (e.g., 2nd century BCE = -150)
    const midCentury = (centuryNum - 1) * 100 + 50;
    return isBCE ? -midCentury : midCentury;
  }

  // Handle year ranges like "60-50 BCE" - use the first year
  const rangeMatch = cleaned.match(/(\d+)\s*[-–]\s*\d+/);
  if (rangeMatch) {
    const year = parseInt(rangeMatch[1], 10);
    return isBCE ? -year : year;
  }

  // Handle single years like "100 BCE" or "1440"
  const yearMatch = cleaned.match(/\d{2,4}/);
  if (yearMatch) {
    const year = parseInt(yearMatch[0], 10);
    return isBCE ? -year : year;
  }

  // Handle decade notation like "1430s"
  const decadeMatch = cleaned.match(/(\d{3})0s/);
  if (decadeMatch) {
    return parseInt(decadeMatch[1] + '0', 10);
  }

  return Infinity;
}

/**
 * Get all artworks grouped by century, sorted chronologically
 */
export function getArtworksGroupedByCentury(index) {
  const artworks = Object.values(index.artworks);

  // Parse dates and filter undated
  const datedArtworks = artworks
    .map(artwork => ({
      ...artwork,
      parsedYear: parseArtworkDateForTimeline(artwork.metadata.date)
    }))
    .filter(artwork => artwork.parsedYear !== Infinity)
    .sort((a, b) => a.parsedYear - b.parsedYear);

  // Group by century
  const grouped = {};
  for (const artwork of datedArtworks) {
    const centuryLabel = getCenturyLabel(artwork.parsedYear);
    if (!centuryLabel) continue;

    if (!grouped[centuryLabel]) {
      grouped[centuryLabel] = [];
    }
    grouped[centuryLabel].push(artwork);
  }

  return grouped;
}
