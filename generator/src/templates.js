import { parseMarkdown } from './parser.js';

/**
 * Base HTML layout wrapper
 */
export function layoutTemplate(title, content, depth = 0) {
  const prefix = depth > 0 ? '../'.repeat(depth) : './';
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${escapeHtml(title)} - Italian Renaissance Art</title>
  <link rel="stylesheet" href="${prefix}styles.css">
</head>
<body>
  <header>
    <nav>
      <a href="${prefix}index.html" class="nav-home">Italian Renaissance Art</a>
    </nav>
  </header>
  <main>
    ${content}
  </main>
  <footer>
    <p>Travel notes on Italian Renaissance Art</p>
  </footer>
</body>
</html>`;
}

/**
 * Index page template
 */
export function indexTemplate(artists, locationsByCity) {
  const artistsList = artists.map(a =>
    `<li><a href="artists/${a.id}.html">${escapeHtml(a.metadata.title)}</a></li>`
  ).join('\n        ');

  const locationsHtml = Object.entries(locationsByCity).map(([city, locations]) => `
      <h3>${escapeHtml(city)}</h3>
      <ul>
        ${locations.map(l =>
          `<li><a href="locations/${l.id}.html">${escapeHtml(l.metadata.title)}</a></li>`
        ).join('\n        ')}
      </ul>`
  ).join('\n');

  const content = `
    <h1>Italian Renaissance Art</h1>
    <p class="intro">Notes for my upcoming travels through Italy, following Frederick Hartt's "History of Italian Renaissance Art".</p>

    <section class="index-section">
      <h2>Artists</h2>
      <ul class="artist-list">
        ${artistsList}
      </ul>
    </section>

    <section class="index-section">
      <h2>Locations by City</h2>
      ${locationsHtml}
    </section>
  `;

  return layoutTemplate('Home', content, 0);
}

/**
 * Artwork card template (for embedding in artist/location pages)
 */
export function artworkCardTemplate(artwork) {
  const meta = artwork.metadata;
  const image = meta.images[0];

  return `
    <article class="artwork-card">
      <h3><a href="../artworks/${artwork.id}.html">${escapeHtml(meta.title)}</a></h3>
      <div class="artwork-meta">
        ${meta.medium ? `<span class="medium">${escapeHtml(meta.medium)}</span>` : ''}
        ${meta.date ? `<span class="date">${escapeHtml(meta.date)}</span>` : ''}
      </div>
      ${meta.description ? `<p class="description">${escapeHtml(meta.description)}</p>` : ''}
      ${image ? `<img src="${escapeHtml(fixImagePath(image.src, 'artworks'))}" alt="${escapeHtml(meta.title)}" loading="lazy">` : ''}
    </article>
  `;
}

/**
 * Artist page template
 */
export function artistTemplate(artist, artworks) {
  const meta = artist.metadata;

  const links = [];
  if (meta.wikipedia) {
    links.push(`<a href="${escapeHtml(meta.wikipedia)}" target="_blank" rel="noopener noreferrer">Wikipedia</a>`);
  }

  const artworksHtml = artworks.length > 0
    ? artworks.map(a => artworkCardTemplate(a)).join('\n')
    : '<p class="no-artworks">No artworks documented yet.</p>';

  const content = `
    <article class="artist-page">
      <h1>${escapeHtml(meta.title)}</h1>
      ${links.length > 0 ? `<div class="external-links">${links.join(' ')}</div>` : ''}
      ${meta.bio ? `<div class="bio">${parseMarkdown(meta.bio)}</div>` : ''}

      <section class="artworks-section">
        <h2>Artworks</h2>
        <div class="artwork-grid">
          ${artworksHtml}
        </div>
      </section>
    </article>
  `;

  return layoutTemplate(meta.title, content, 1);
}

/**
 * Location page template
 */
export function locationTemplate(location, artworks) {
  const meta = location.metadata;

  const links = [];
  if (meta.wikipedia) {
    links.push(`<a href="${escapeHtml(meta.wikipedia)}" target="_blank" rel="noopener noreferrer">Wikipedia</a>`);
  }
  if (meta.googleMap) {
    links.push(`<a href="${escapeHtml(meta.googleMap)}" target="_blank" rel="noopener noreferrer">Google Maps</a>`);
  }

  const floorPlanHtml = meta.floorPlan
    ? `<div class="floor-plan"><img src="${escapeHtml(fixImagePath(meta.floorPlan, 'locations'))}" alt="Floor plan"></div>`
    : '';

  const artworksHtml = artworks.length > 0
    ? artworks.map(a => artworkCardTemplate(a)).join('\n')
    : '<p class="no-artworks">No artworks documented yet.</p>';

  const content = `
    <article class="location-page">
      <h1>${escapeHtml(meta.title)}</h1>
      ${meta.city ? `<p class="city">${escapeHtml(meta.city)}</p>` : ''}
      ${links.length > 0 ? `<div class="external-links">${links.join(' ')}</div>` : ''}
      ${meta.architecturalStyle ? `<p class="architectural-style"><strong>Architectural style:</strong> ${escapeHtml(meta.architecturalStyle)}</p>` : ''}
      ${floorPlanHtml}

      <section class="artworks-section">
        <h2>Artworks</h2>
        <div class="artwork-grid">
          ${artworksHtml}
        </div>
      </section>
    </article>
  `;

  return layoutTemplate(meta.title, content, 1);
}

/**
 * Individual artwork page template
 */
export function artworkTemplate(artwork) {
  const meta = artwork.metadata;

  const metaItems = [];
  if (meta.artist) {
    metaItems.push(`<li><strong>Artist:</strong> <a href="../artists/${artwork.metadata.artistFile}.html">${escapeHtml(meta.artist)}</a></li>`);
  }
  if (meta.location) {
    const locationLink = artwork.metadata.locationFile
      ? `<a href="../locations/${artwork.metadata.locationFile}.html">${escapeHtml(meta.location)}</a>`
      : escapeHtml(meta.location);
    metaItems.push(`<li><strong>Location:</strong> ${locationLink}${meta.city ? `, ${escapeHtml(meta.city)}` : ''}</li>`);
  }
  if (meta.medium) {
    metaItems.push(`<li><strong>Medium:</strong> ${escapeHtml(meta.medium)}</li>`);
  }
  if (meta.date) {
    metaItems.push(`<li><strong>Date:</strong> ${escapeHtml(meta.date)}</li>`);
  }

  const imagesHtml = meta.images.map(img =>
    `<figure><img src="${escapeHtml(fixImagePath(img.src, 'artworks'))}" alt="${escapeHtml(img.alt || meta.title)}"></figure>`
  ).join('\n');

  const content = `
    <article class="artwork-page">
      <h1>${escapeHtml(meta.title)}</h1>
      ${metaItems.length > 0 ? `<ul class="artwork-metadata">${metaItems.join('\n')}</ul>` : ''}
      ${meta.description ? `<div class="description">${parseMarkdown(meta.description)}</div>` : ''}
      <div class="artwork-images">
        ${imagesHtml}
      </div>
    </article>
  `;

  return layoutTemplate(meta.title, content, 1);
}

/**
 * Escape HTML special characters
 */
function escapeHtml(text) {
  if (!text) return '';
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/**
 * Fix relative image paths for generated HTML
 */
function fixImagePath(src, currentDir) {
  if (!src) return '';

  // External URLs stay as-is
  if (src.startsWith('http://') || src.startsWith('https://')) {
    return src;
  }

  // Handle ../img/ paths - from artworks or other dirs, go up to site root then into img
  if (src.startsWith('../img/')) {
    return src; // Keep relative path as-is, it will work from subdirectories
  }

  // Handle direct img/ paths
  if (src.startsWith('img/')) {
    return '../' + src;
  }

  return src;
}
