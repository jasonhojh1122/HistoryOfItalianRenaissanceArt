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
  <title>${escapeHtml(title)} - Italian Art</title>
  <link rel="stylesheet" href="${prefix}styles.css">
</head>
<body>
  <header>
    <nav>
      <a href="${prefix}index.html" class="nav-home">Italian Art</a>
    </nav>
  </header>
  <main>
    ${content}
  </main>
  <footer>
    <p>Travel notes on Italian Art</p>
  </footer>
  <script src="${prefix}sort.js"></script>
</body>
</html>`;
}

/**
 * Index page template
 */
export function indexTemplate(artists, locationsByCity, bibleStories = []) {
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

  const bibleStoriesHtml = bibleStories.length > 0 ? `
    <section class="index-section">
      <h2>Bible Stories</h2>
      <ul class="bible-stories-list">
        ${bibleStories.map(s =>
          `<li><a href="biblestories/${s.id}.html">${escapeHtml(s.metadata.title)}</a>${s.metadata.alternateName ? ` <span class="alternate-name">(${escapeHtml(s.metadata.alternateName)})</span>` : ''}</li>`
        ).join('\n        ')}
      </ul>
    </section>
  ` : '';

  const content = `
    <h1>Italian Art</h1>
    <p class="intro">Notes for my upcoming travels through Italy, following Frederick Hartt's "History of Italian Art".</p>

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

    ${bibleStoriesHtml}
  `;

  return layoutTemplate('Home', content, 0);
}

/**
 * Sort controls template
 * @param {boolean} showArtistSort - Whether to show the Artist sort button
 */
function sortControlsTemplate(showArtistSort) {
  return `
    <div class="sort-controls">
      <span>Sort by:</span>
      <button class="sort-btn active" data-sort="date">Date</button>
      <button class="sort-btn" data-sort="title">Title</button>
      ${showArtistSort ? '<button class="sort-btn" data-sort="artist">Artist</button>' : ''}
    </div>
  `;
}

/**
 * Sort artworks by date (earliest first)
 */
function sortArtworksByDate(artworks) {
  return [...artworks].sort((a, b) => {
    const dateA = parseArtworkDate(a.metadata.date);
    const dateB = parseArtworkDate(b.metadata.date);
    return dateA - dateB;
  });
}

/**
 * Parse date string into a number for sorting
 */
function parseArtworkDate(dateStr) {
  if (!dateStr) return Infinity;
  const cleaned = dateStr.replace(/^(c\.|ca\.|circa)\s*/i, '').trim();
  const match = cleaned.match(/\d{4}/);
  if (match) return parseInt(match[0], 10);
  const decadeMatch = cleaned.match(/(\d{3})0s/);
  if (decadeMatch) return parseInt(decadeMatch[1] + '0', 10);
  return Infinity;
}

/**
 * Artwork card template (for embedding in artist/location pages)
 * @param {Object} artwork - Artwork object
 * @param {boolean} includeArtist - Whether to include artist in data attributes
 */
export function artworkCardTemplate(artwork, includeArtist = false) {
  const meta = artwork.metadata;
  const image = meta.images[0];

  const artistAttr = includeArtist && meta.artist ? ` data-artist="${escapeHtml(meta.artist)}"` : '';
  const selfResearchedBadge = meta.selfResearched ? '<span class="badge badge-researched">Self-researched</span>' : '';

  return `
    <article class="artwork-card" data-title="${escapeHtml(meta.title || '')}" data-date="${escapeHtml(meta.date || '')}"${artistAttr}>
      <h3><a href="../artworks/${artwork.id}.html">${escapeHtml(meta.title)}</a> ${selfResearchedBadge}</h3>
      <div class="artwork-meta">
        ${includeArtist && meta.artist ? `<span class="artist"><a href="../artists/${artwork.metadata.artistFile}.html">${escapeHtml(meta.artist)}</a></span>` : ''}
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

  // Sort artworks by date and generate cards (no artist sort for single-artist pages)
  const sortedArtworks = sortArtworksByDate(artworks);
  const artworksHtml = sortedArtworks.length > 0
    ? sortedArtworks.map(a => artworkCardTemplate(a, false)).join('\n')
    : '<p class="no-artworks">No artworks documented yet.</p>';

  const sortControls = sortedArtworks.length > 1 ? sortControlsTemplate(false) : '';

  const content = `
    <article class="artist-page">
      <h1>${escapeHtml(meta.title)}</h1>
      ${links.length > 0 ? `<div class="external-links">${links.join(' ')}</div>` : ''}
      ${meta.bio ? `<div class="bio">${parseMarkdown(meta.bio)}</div>` : ''}

      <section class="artworks-section">
        <h2>Artworks</h2>
        ${sortControls}
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

  // Check if multiple artists are represented
  const uniqueArtists = new Set(artworks.map(a => a.metadata.artist).filter(Boolean));
  const hasMultipleArtists = uniqueArtists.size > 1;

  // Sort artworks by date and generate cards
  const sortedArtworks = sortArtworksByDate(artworks);
  const artworksHtml = sortedArtworks.length > 0
    ? sortedArtworks.map(a => artworkCardTemplate(a, hasMultipleArtists)).join('\n')
    : '<p class="no-artworks">No artworks documented yet.</p>';

  const sortControls = sortedArtworks.length > 1 ? sortControlsTemplate(hasMultipleArtists) : '';

  const content = `
    <article class="location-page">
      <h1>${escapeHtml(meta.title)}</h1>
      ${meta.city ? `<p class="city">${escapeHtml(meta.city)}</p>` : ''}
      ${links.length > 0 ? `<div class="external-links">${links.join(' ')}</div>` : ''}
      ${meta.architecturalStyle ? `<p class="architectural-style"><strong>Architectural style:</strong> ${escapeHtml(meta.architecturalStyle)}</p>` : ''}
      ${floorPlanHtml}

      <section class="artworks-section">
        <h2>Artworks</h2>
        ${sortControls}
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

  const links = [];
  if (meta.wikipedia) {
    links.push(`<a href="${escapeHtml(meta.wikipedia)}" target="_blank" rel="noopener noreferrer">Wikipedia</a>`);
  }

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

  // Add bible story link with context if present
  const bibleStoryHtml = meta.bibleStory ? `
    <div class="biblical-context">
      <h3>Biblical Context</h3>
      <p><a href="../biblestories/${escapeHtml(artwork.metadata.bibleStoryFile)}.html">${escapeHtml(meta.bibleStory)}</a>${meta.biblicalContext ? ` - ${escapeHtml(meta.biblicalContext)}` : ''}</p>
    </div>
  ` : '';

  const imagesHtml = meta.images.map(img =>
    `<figure><img src="${escapeHtml(fixImagePath(img.src, 'artworks'))}" alt="${escapeHtml(img.alt || meta.title)}"></figure>`
  ).join('\n');

  const selfResearchedBadge = meta.selfResearched ? '<span class="badge badge-researched">Self-researched</span>' : '';

  const content = `
    <article class="artwork-page">
      <h1>${escapeHtml(meta.title)} ${selfResearchedBadge}</h1>
      ${links.length > 0 ? `<div class="external-links">${links.join(' ')}</div>` : ''}
      ${metaItems.length > 0 ? `<ul class="artwork-metadata">${metaItems.join('\n')}</ul>` : ''}
      ${bibleStoryHtml}
      ${meta.description ? `<div class="description">${parseMarkdown(meta.description)}</div>` : ''}
      <div class="artwork-images">
        ${imagesHtml}
      </div>
    </article>
  `;

  return layoutTemplate(meta.title, content, 1);
}

/**
 * Bible story page template
 */
export function bibleStoryTemplate(bibleStory, artworks) {
  const meta = bibleStory.metadata;

  const links = [];
  if (meta.wikipedia) {
    links.push(`<a href="${escapeHtml(meta.wikipedia)}" target="_blank" rel="noopener noreferrer">Wikipedia</a>`);
  }

  // Check if multiple artists are represented
  const uniqueArtists = new Set(artworks.map(a => a.metadata.artist).filter(Boolean));
  const hasMultipleArtists = uniqueArtists.size > 1;

  // Sort artworks by date and generate cards
  const sortedArtworks = sortArtworksByDate(artworks);
  const artworksHtml = sortedArtworks.length > 0
    ? sortedArtworks.map(a => artworkCardTemplate(a, hasMultipleArtists)).join('\n')
    : '<p class="no-artworks">No artworks documented yet.</p>';

  const sortControls = sortedArtworks.length > 1 ? sortControlsTemplate(hasMultipleArtists) : '';

  const biblicalRefHtml = (meta.biblicalReference.books || meta.biblicalReference.verses) ? `
      <div class="biblical-reference">
        <h3>Biblical Reference</h3>
        ${meta.biblicalReference.books ? `<p><strong>Book(s):</strong> ${escapeHtml(meta.biblicalReference.books)}</p>` : ''}
        ${meta.biblicalReference.verses ? `<p><strong>Chapters/Verses:</strong> ${escapeHtml(meta.biblicalReference.verses)}</p>` : ''}
      </div>
  ` : '';

  const content = `
    <article class="bible-story-page">
      <h1>${escapeHtml(meta.title)}</h1>
      ${meta.alternateName ? `<p class="alternate-name">${escapeHtml(meta.alternateName)}</p>` : ''}
      ${links.length > 0 ? `<div class="external-links">${links.join(' ')}</div>` : ''}

      ${meta.summary ? `
      <section class="summary-section">
        <h2>Summary</h2>
        <div class="summary">${parseMarkdown(meta.summary)}</div>
      </section>
      ` : ''}

      ${biblicalRefHtml}

      <section class="artworks-section">
        <h2>Artworks Depicting This Story</h2>
        ${sortControls}
        <div class="artwork-grid">
          ${artworksHtml}
        </div>
      </section>
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

  // Handle ../imgAutoResearch/ paths
  if (src.startsWith('../imgAutoResearch/')) {
    return src; // Keep relative path as-is, it will work from subdirectories
  }

  // Handle direct img/ paths
  if (src.startsWith('img/')) {
    return '../' + src;
  }

  return src;
}
