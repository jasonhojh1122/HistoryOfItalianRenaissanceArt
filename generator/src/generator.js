import fs from 'fs/promises';
import path from 'path';
import { glob } from 'glob';
import { fileURLToPath } from 'url';
import {
  buildIndex,
  getArtistArtworks,
  getArtistArchitecturalWorks,
  getLocationArtworks,
  getBibleStoryArtworks,
  getSortedArtists,
  getSortedArtworks,
  getSortedBibleStories,
  getLocationsByCity,
} from './relationships.js';
import {
  indexTemplate,
  artistTemplate,
  locationTemplate,
  artworkTemplate,
  bibleStoryTemplate,
  creditsTemplate
} from './templates.js';
import { updateCoordinates } from './geocoder.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Generate the complete static site
 */
export async function generateSite(rootDir, outputDir) {
  console.log('Building site...');
  console.log(`  Source: ${rootDir}`);
  console.log(`  Output: ${outputDir}`);

  // Clean and create output directory
  await fs.rm(outputDir, { recursive: true, force: true });
  await fs.mkdir(outputDir, { recursive: true });
  await fs.mkdir(path.join(outputDir, 'artists'), { recursive: true });
  await fs.mkdir(path.join(outputDir, 'locations'), { recursive: true });
  await fs.mkdir(path.join(outputDir, 'artworks'), { recursive: true });
  await fs.mkdir(path.join(outputDir, 'biblestories'), { recursive: true });

  // Build content index
  console.log('\nIndexing content...');
  const index = await buildIndex(rootDir);
  console.log(`  Found ${Object.keys(index.artists).length} artists`);
  console.log(`  Found ${Object.keys(index.locations).length} locations`);
  console.log(`  Found ${Object.keys(index.artworks).length} artworks`);
  console.log(`  Found ${Object.keys(index.biblestories).length} bible stories`);

  // Update coordinates for map (geocodes any missing locations)
  console.log('\nUpdating coordinates...');
  let coordinates = {};
  try {
    coordinates = await updateCoordinates(index);
  } catch (err) {
    console.warn('  Warning: Could not update coordinates:', err.message);
  }

  // Generate index page
  console.log('\nGenerating pages...');
  const artists = getSortedArtists(index);
  const allArtworks = getSortedArtworks(index);
  const locationsByCity = getLocationsByCity(index);
  const bibleStories = getSortedBibleStories(index);
  // Build map locations array with coordinates
  const mapLocations = Object.entries(index.locations).map(([id, location]) => {
    const artworks = getLocationArtworks(index, id);
    const coord = coordinates[id] || null;
    return {
      id,
      title: location.metadata.title,
      city: location.metadata.city || '',
      artworkCount: artworks.length,
      lat: coord?.lat,
      lng: coord?.lng
    };
  }).filter(loc => loc.lat && loc.lng);

  // Parse TERMS.md into structured data
  let terms = [];
  try {
    const termsPath = path.join(rootDir, 'TERMS.md');
    const termsContent = await fs.readFile(termsPath, 'utf-8');
    terms = parseTerms(termsContent);
    console.log(`  Found ${terms.reduce((n, c) => n + c.terms.length, 0)} terms in ${terms.length} categories`);
  } catch (err) {
    if (err.code !== 'ENOENT') {
      console.warn('  Warning: Could not parse TERMS.md:', err.message);
    }
  }

  const indexHtml = indexTemplate(artists, locationsByCity, bibleStories, mapLocations, allArtworks, terms);
  await fs.writeFile(path.join(outputDir, 'index.html'), indexHtml);
  console.log('  Generated index.html');

  // Generate artist pages
  for (const [artistId, artist] of Object.entries(index.artists)) {
    const artworks = getArtistArtworks(index, artistId);
    const architecturalWorks = getArtistArchitecturalWorks(index, artistId);
    const html = artistTemplate(artist, artworks, architecturalWorks);
    await fs.writeFile(path.join(outputDir, 'artists', `${artistId}.html`), html);
  }
  console.log(`  Generated ${Object.keys(index.artists).length} artist pages`);

  // Generate location pages
  for (const [locationId, location] of Object.entries(index.locations)) {
    const artworks = getLocationArtworks(index, locationId);
    const html = locationTemplate(location, artworks);
    await fs.writeFile(path.join(outputDir, 'locations', `${locationId}.html`), html);
  }
  console.log(`  Generated ${Object.keys(index.locations).length} location pages`);

  // Generate artwork pages
  for (const [artworkId, artwork] of Object.entries(index.artworks)) {
    const html = artworkTemplate(artwork);
    await fs.writeFile(path.join(outputDir, 'artworks', `${artworkId}.html`), html);
  }
  console.log(`  Generated ${Object.keys(index.artworks).length} artwork pages`);

  // Generate bible story pages
  for (const [bibleStoryId, bibleStory] of Object.entries(index.biblestories)) {
    const artworks = getBibleStoryArtworks(index, bibleStoryId);
    const html = bibleStoryTemplate(bibleStory, artworks);
    await fs.writeFile(path.join(outputDir, 'biblestories', `${bibleStoryId}.html`), html);
  }
  console.log(`  Generated ${Object.keys(index.biblestories).length} bible story pages`);

  // Generate credits page
  try {
    const creditPath = path.join(rootDir, 'CREDIT.md');
    const creditMarkdown = await fs.readFile(creditPath, 'utf-8');
    const creditsHtml = creditsTemplate(creditMarkdown);
    await fs.writeFile(path.join(outputDir, 'credits.html'), creditsHtml);
    console.log('  Generated credits.html');
  } catch (err) {
    if (err.code !== 'ENOENT') {
      console.warn('  Warning: Could not generate credits page:', err.message);
    }
  }

  // Build search index
  console.log('\nBuilding search index...');
  const searchIndex = buildSearchIndex(index, terms);
  await fs.writeFile(path.join(outputDir, 'search-index.json'), JSON.stringify(searchIndex));
  console.log(`  Generated search-index.json (${searchIndex.length} entries)`);

  // Copy static assets
  console.log('\nCopying assets...');
  await copyStaticAssets(rootDir, outputDir);

  console.log('\nBuild complete!');
  console.log(`Site generated at: ${outputDir}`);
}

/**
 * Strip markdown syntax to produce plain text for search indexing
 */
function stripMarkdown(md) {
  return md
    .replace(/!\[[^\]]*\]\([^)]*\)/g, '')       // images
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')     // links → text
    .replace(/^#{1,6}\s+/gm, '')                 // headings
    .replace(/(\*{1,3}|_{1,3})(.*?)\1/g, '$2')   // bold/italic
    .replace(/`{1,3}[^`]*`{1,3}/g, '')           // inline code
    .replace(/^\s*[-*+]\s+/gm, '')               // unordered list markers
    .replace(/^\s*\d+\.\s+/gm, '')               // ordered list markers
    .replace(/^\s*>\s+/gm, '')                    // blockquotes
    .replace(/\|/g, ' ')                          // table pipes
    .replace(/^-{3,}$/gm, '')                     // horizontal rules
    .replace(/\n{2,}/g, '\n')                     // collapse blank lines
    .trim();
}

/**
 * Build search index JSON from all content
 */
function buildSearchIndex(index, terms) {
  const entries = [];

  // Artists
  for (const [id, artist] of Object.entries(index.artists)) {
    entries.push({
      type: 'artist',
      id,
      title: artist.metadata.title,
      url: `artists/${id}.html`,
      content: stripMarkdown(artist.content)
    });
  }

  // Artworks
  for (const [id, artwork] of Object.entries(index.artworks)) {
    const meta = artwork.metadata;
    const subtitleParts = [meta.artist, meta.date, meta.medium].filter(Boolean);
    entries.push({
      type: 'artwork',
      id,
      title: meta.title,
      url: `artworks/${id}.html`,
      subtitle: subtitleParts.join(' · '),
      content: stripMarkdown(artwork.content)
    });
  }

  // Locations
  for (const [id, location] of Object.entries(index.locations)) {
    entries.push({
      type: 'location',
      id,
      title: location.metadata.title,
      url: `locations/${id}.html`,
      subtitle: location.metadata.city || '',
      content: stripMarkdown(location.content)
    });
  }

  // Bible stories
  for (const [id, story] of Object.entries(index.biblestories)) {
    entries.push({
      type: 'bible story',
      id,
      title: story.metadata.title,
      url: `biblestories/${id}.html`,
      subtitle: story.metadata.alternateName || '',
      content: stripMarkdown(story.content)
    });
  }

  // Terms
  for (const category of terms) {
    for (const term of category.terms) {
      entries.push({
        type: 'term',
        id: term.name,
        title: term.name,
        url: `index.html?tab=terms#${term.name.toLowerCase().replace(/[()]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '')}`,
        subtitle: category.name,
        content: stripMarkdown(term.body)
      });
    }
  }

  return entries;
}

/**
 * Copy static assets (CSS, JS, and images)
 */
/**
 * Parse TERMS.md into structured categories and terms
 */
function parseTerms(content) {
  const categories = [];
  let currentCategory = null;
  let currentTerm = null;

  for (const line of content.split('\n')) {
    if (line.startsWith('## ')) {
      // New category
      currentCategory = { name: line.slice(3).trim(), terms: [] };
      categories.push(currentCategory);
      currentTerm = null;
    } else if (line.startsWith('### ') && currentCategory) {
      // New term
      currentTerm = { name: line.slice(4).trim(), wikipedia: null, body: '' };
      currentCategory.terms.push(currentTerm);
    } else if (currentTerm) {
      currentTerm.body += line + '\n';
    }
  }

  // Extract Wikipedia links and trim bodies
  for (const cat of categories) {
    for (const term of cat.terms) {
      const wikiMatch = term.body.match(/^\[Wikipedia\]\(([^)]+)\)\s*\n?/);
      if (wikiMatch) {
        term.wikipedia = wikiMatch[1];
        term.body = term.body.slice(wikiMatch[0].length);
      }
      term.body = term.body.trim();
    }
  }

  return categories;
}

/**
 * Copy static assets (CSS, JS, and images)
 */
async function copyStaticAssets(rootDir, outputDir) {
  // Copy all files from generator/static/
  const generatorDir = path.dirname(import.meta.url.replace('file://', ''));
  const staticDir = path.join(generatorDir, '..', 'static');

  try {
    const staticFiles = await glob('*', { cwd: staticDir, nodir: true });
    for (const file of staticFiles) {
      const src = path.join(staticDir, file);
      const dest = path.join(outputDir, file);
      await fs.copyFile(src, dest);
    }
    console.log(`  Copied ${staticFiles.length} static files (${staticFiles.join(', ')})`);
  } catch (err) {
    console.error('  Warning: Could not copy static files:', err.message);
  }

  // Copy local images from img/
  const imgDir = path.join(rootDir, 'img');
  const imgOutputDir = path.join(outputDir, 'img');

  try {
    const imgFiles = await glob('**/*', { cwd: imgDir, nodir: true });
    if (imgFiles.length > 0) {
      await fs.mkdir(imgOutputDir, { recursive: true });
      for (const file of imgFiles) {
        const src = path.join(imgDir, file);
        const dest = path.join(imgOutputDir, file);
        await fs.mkdir(path.dirname(dest), { recursive: true });
        await fs.copyFile(src, dest);
      }
      console.log(`  Copied ${imgFiles.length} images from img/`);
    }
  } catch (err) {
    if (err.code !== 'ENOENT') {
      console.error('  Warning: Error copying images:', err.message);
    }
  }
}
