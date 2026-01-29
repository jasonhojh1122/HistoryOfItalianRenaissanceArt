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
  const result = {};

  for (const [city, locationIds] of Object.entries(index.byCity)) {
    result[city] = locationIds
      .map(id => index.locations[id])
      .filter(Boolean)
      .sort((a, b) => a.metadata.title.localeCompare(b.metadata.title));
  }

  // Sort cities alphabetically
  return Object.fromEntries(
    Object.entries(result).sort(([a], [b]) => a.localeCompare(b))
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
