import fs from 'fs/promises';
import path from 'path';
import { glob } from 'glob';
import {
  buildIndex,
  getArtistArtworks,
  getLocationArtworks,
  getSortedArtists,
  getLocationsByCity
} from './relationships.js';
import {
  indexTemplate,
  artistTemplate,
  locationTemplate,
  artworkTemplate
} from './templates.js';

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

  // Build content index
  console.log('\nIndexing content...');
  const index = await buildIndex(rootDir);
  console.log(`  Found ${Object.keys(index.artists).length} artists`);
  console.log(`  Found ${Object.keys(index.locations).length} locations`);
  console.log(`  Found ${Object.keys(index.artworks).length} artworks`);

  // Generate index page
  console.log('\nGenerating pages...');
  const artists = getSortedArtists(index);
  const locationsByCity = getLocationsByCity(index);
  const indexHtml = indexTemplate(artists, locationsByCity);
  await fs.writeFile(path.join(outputDir, 'index.html'), indexHtml);
  console.log('  Generated index.html');

  // Generate artist pages
  for (const [artistId, artist] of Object.entries(index.artists)) {
    const artworks = getArtistArtworks(index, artistId);
    const html = artistTemplate(artist, artworks);
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

  // Copy static assets
  console.log('\nCopying assets...');
  await copyStaticAssets(rootDir, outputDir);

  console.log('\nBuild complete!');
  console.log(`Site generated at: ${outputDir}`);
}

/**
 * Copy static assets (CSS and images)
 */
async function copyStaticAssets(rootDir, outputDir) {
  // Copy CSS from generator/static/
  const generatorDir = path.dirname(import.meta.url.replace('file://', ''));
  const cssSource = path.join(generatorDir, '..', 'static', 'styles.css');
  const cssDest = path.join(outputDir, 'styles.css');

  try {
    await fs.copyFile(cssSource, cssDest);
    console.log('  Copied styles.css');
  } catch (err) {
    console.error('  Warning: Could not copy styles.css:', err.message);
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
