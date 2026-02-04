import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const COORDINATES_PATH = path.join(__dirname, '..', 'data', 'coordinates.json');

// Nominatim requires 1 second between requests
const RATE_LIMIT_MS = 1100;

/**
 * Load existing coordinates from file
 */
async function loadCoordinates() {
  try {
    const content = await fs.readFile(COORDINATES_PATH, 'utf-8');
    return JSON.parse(content);
  } catch (err) {
    if (err.code === 'ENOENT') {
      return {};
    }
    throw err;
  }
}

/**
 * Save coordinates to file
 */
async function saveCoordinates(coordinates) {
  // Sort keys alphabetically for consistent output
  const sorted = Object.fromEntries(
    Object.entries(coordinates).sort(([a], [b]) => a.localeCompare(b))
  );
  await fs.writeFile(COORDINATES_PATH, JSON.stringify(sorted, null, 2) + '\n');
}

/**
 * Convert location ID to search query
 * e.g., "UffiziGallery" -> "Uffizi Gallery"
 */
function locationIdToQuery(id, city) {
  // Insert spaces before capital letters and numbers
  const name = id
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/([A-Z]+)([A-Z][a-z])/g, '$1 $2');

  // Add city and country for better results
  const parts = [name];
  if (city) {
    parts.push(city.replace(/, Italy$/, ''));
  }
  parts.push('Italy');

  return parts.join(', ');
}

/**
 * Fetch coordinates from Nominatim API
 */
async function geocodeLocation(query) {
  const url = new URL('https://nominatim.openstreetmap.org/search');
  url.searchParams.set('q', query);
  url.searchParams.set('format', 'json');
  url.searchParams.set('limit', '1');

  const response = await fetch(url, {
    headers: {
      'User-Agent': 'ItalianRenaissanceArtSiteGenerator/1.0'
    }
  });

  if (!response.ok) {
    throw new Error(`Geocoding failed: ${response.status} ${response.statusText}`);
  }

  const results = await response.json();
  if (results.length === 0) {
    return null;
  }

  return {
    lat: parseFloat(results[0].lat),
    lng: parseFloat(results[0].lon)
  };
}

/**
 * Sleep for specified milliseconds
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Update coordinates.json with any missing locations from the index
 * @param {Object} index - The content index with locations
 * @returns {Object} Updated coordinates object
 */
export async function updateCoordinates(index) {
  const coordinates = await loadCoordinates();
  const locationIds = Object.keys(index.locations);

  // Find locations missing coordinates
  const missing = locationIds.filter(id => !coordinates[id]);

  if (missing.length === 0) {
    console.log('  All locations have coordinates');
    return coordinates;
  }

  console.log(`  Found ${missing.length} locations without coordinates`);

  let updated = 0;
  let failed = 0;

  for (const id of missing) {
    const location = index.locations[id];
    const city = location.metadata.city || '';
    const query = locationIdToQuery(id, city);

    console.log(`  Geocoding: ${query}`);

    try {
      const result = await geocodeLocation(query);

      if (result) {
        coordinates[id] = result;
        updated++;
        console.log(`    -> ${result.lat}, ${result.lng}`);
      } else {
        failed++;
        console.log(`    -> Not found`);
      }
    } catch (err) {
      failed++;
      console.log(`    -> Error: ${err.message}`);
    }

    // Rate limiting - wait between requests
    if (missing.indexOf(id) < missing.length - 1) {
      await sleep(RATE_LIMIT_MS);
    }
  }

  if (updated > 0) {
    await saveCoordinates(coordinates);
    console.log(`  Updated coordinates.json: ${updated} added, ${failed} failed`);
  } else if (failed > 0) {
    console.log(`  No coordinates added (${failed} failed)`);
  }

  return coordinates;
}
