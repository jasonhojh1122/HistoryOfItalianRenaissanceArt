import { parseMarkdown } from './parser.js';

// Build timestamp - set once when module loads
const BUILD_TIMESTAMP = new Date().toLocaleDateString('en-US', {
  year: 'numeric',
  month: 'long',
  day: 'numeric'
});

/**
 * Parse a markdown table into an array of row objects
 */
function parseMarkdownTable(markdown) {
  const lines = markdown.trim().split('\n').filter(line => line.trim());
  if (lines.length < 2) return [];

  // Find the header line (first line with |)
  const headerIdx = lines.findIndex(line => line.includes('|'));
  if (headerIdx === -1) return [];

  const headerLine = lines[headerIdx];
  const headers = headerLine.split('|').map(h => h.trim()).filter(Boolean);

  // Skip the separator line (contains dashes)
  const rows = [];
  for (let i = headerIdx + 2; i < lines.length; i++) {
    const line = lines[i];
    if (!line.includes('|')) continue;
    const cells = line.split('|').map(c => c.trim()).filter(Boolean);
    if (cells.length === headers.length) {
      const row = {};
      headers.forEach((h, idx) => {
        row[h] = cells[idx];
      });
      rows.push(row);
    }
  }
  return rows;
}

/**
 * Base HTML layout wrapper
 */
export function layoutTemplate(title, content, depth = 0, options = {}) {
  const prefix = depth > 0 ? '../'.repeat(depth) : './';
  const extraHead = options.extraHead || '';
  const extraScripts = options.extraScripts || '';
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${escapeHtml(title)} - Italian Art</title>
  <link rel="icon" type="image/svg+xml" href="${prefix}favicon.svg">
  <link rel="stylesheet" href="${prefix}styles.css">
${extraHead}
</head>
<body>
  <header>
    <nav>
      <a href="${prefix}index.html" class="nav-home">Italian Art</a>
      <button class="copy-filename-btn" onclick="(function(btn){var f=location.pathname.split('/').pop()||'index.html';navigator.clipboard.writeText(f).then(function(){btn.classList.add('copied');btn.setAttribute('data-filename',f);setTimeout(function(){btn.classList.remove('copied')},1200)});})(this)" aria-label="Copy filename"></button>
    </nav>
  </header>
  <script>document.querySelector('.copy-filename-btn').setAttribute('data-filename',location.pathname.split('/').pop()||'index.html');</script>
  <main>
    ${content}
  </main>
  <footer>
    <p>Travel notes on Italian Art · <a href="${prefix}credits.html">Image Credits</a></p>
    <p class="last-updated">Last updated: ${BUILD_TIMESTAMP}</p>
  </footer>
  <script src="${prefix}sort.js"></script>
  <script src="${prefix}tabs.js"></script>
  <script src="${prefix}search.js"></script>
${extraScripts}
</body>
</html>`;
}

/**
 * Index page template
 */
export function indexTemplate(artists, locationsByCity, bibleStories = [], mapLocations = [], allArtworks = [], terms = []) {
  const artistsList = artists.map(a => {
    const count = a.artworks?.length || 0;
    const countBadge = count > 0 ? `<span class="artwork-count">${count}</span>` : '';
    return `<li><a href="artists/${a.id}.html">${escapeHtml(a.metadata.title)}</a>${countBadge}</li>`;
  }).join('\n        ');

  const locationsHtml = Object.entries(locationsByCity).map(([city, locations]) => `
      <h3>${escapeHtml(city)}</h3>
      <ul class="location-list">
        ${locations.map(l => {
          const count = l.artworks?.length || 0;
          const countBadge = count > 0 ? `<span class="artwork-count">${count}</span>` : '';
          return `<li><a href="locations/${l.id}.html">${escapeHtml(l.metadata.title)}</a>${countBadge}</li>`;
        }).join('\n        ')}
      </ul>`
  ).join('\n');

  const bibleStoriesListHtml = bibleStories.length > 0 ? `
        ${bibleStories.map(s =>
          `<li><a href="biblestories/${s.id}.html">${escapeHtml(s.metadata.title)}</a>${s.metadata.alternateName ? ` <span class="alternate-name">(${escapeHtml(s.metadata.alternateName)})</span>` : ''}</li>`
        ).join('\n        ')}
  ` : '';

  const artworksListHtml = allArtworks.map(a => {
    const meta = a.metadata;
    const artistSpan = meta.artist ? ` <span class="artwork-artist">${escapeHtml(meta.artist)}</span>` : '';
    const dateSpan = meta.date ? ` <span class="artwork-date">${escapeHtml(meta.date)}</span>` : '';
    return `<li><a href="artworks/${a.id}.html">${escapeHtml(meta.title)}</a>${artistSpan}${dateSpan}</li>`;
  }).join('\n        ');

  const termsHtml = terms.map(category => `
        <div class="terms-category">
          <h3>${escapeHtml(category.name)}</h3>
          <dl>
            ${category.terms.map(term => {
              const termId = slugify(term.name);
              const wikiLink = term.wikipedia
                ? `<div class="external-links"><a href="${escapeHtml(term.wikipedia)}" target="_blank" rel="noopener noreferrer">Wikipedia</a></div>`
                : '';
              return `
            <div class="term-item" id="${termId}">
              <dt>${escapeHtml(term.name)}</dt>
              <dd>${wikiLink}${parseMarkdown(term.body)}</dd>
            </div>`;
            }).join('\n')}
          </dl>
        </div>`
  ).join('\n');

  const content = `
    <h1>Italian Art</h1>
    <p class="intro">Notes for my upcoming travels through Italy, following Frederick Hartt's "History of Italian Art".</p>

    <div class="search-container">
      <input type="search" id="index-search" class="search-input"
             placeholder="Search artists, locations, stories, terms, trip..."
             autocomplete="off" aria-label="Search index">
      <span class="search-icon" aria-hidden="true"></span>
      <button class="search-clear" type="button" aria-label="Clear search" hidden>&times;</button>
    </div>
    <p class="search-results-count" hidden></p>
    <div class="search-results-panel" hidden></div>

    <div class="tab-navigation">
      <button class="tab-btn active" data-tab="artists">Artists</button>
      <button class="tab-btn" data-tab="artworks">Artworks</button>
      <button class="tab-btn" data-tab="locations">Locations</button>
      <button class="tab-btn" data-tab="biblestories">Bible Stories</button>
      <button class="tab-btn" data-tab="terms">Terms</button>
      <button class="tab-btn" data-tab="map">Map</button>
      <button class="tab-btn" data-tab="trip">Trip</button>
    </div>

    <div class="tab-content">
      <section class="tab-panel active" data-tab="artists">
        <ul class="artist-list">
          ${artistsList}
        </ul>
      </section>

      <section class="tab-panel" data-tab="artworks">
        <ul class="artworks-list">
          ${artworksListHtml}
        </ul>
      </section>

      <section class="tab-panel" data-tab="locations">
        ${locationsHtml}
      </section>

      <section class="tab-panel" data-tab="biblestories">
        <ul class="bible-stories-list">
          ${bibleStoriesListHtml}
        </ul>
      </section>

      <section class="tab-panel" data-tab="terms">
        <div class="terms-list">
          ${termsHtml}
        </div>
      </section>

      <section class="tab-panel" data-tab="map">
        <div id="map-container" class="map-container"></div>
        <script type="application/json" id="map-locations-data">${JSON.stringify(mapLocations)}</script>
      </section>

      <section class="tab-panel" data-tab="trip">
        <div id="trip-container"></div>
      </section>
    </div>
  `;

  const leafletHead = `  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="">`;
  const leafletScripts = `  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
  <script src="./map.js"></script>
  <script src="./trip.js"></script>`;

  return layoutTemplate('Home', content, 0, { extraHead: leafletHead, extraScripts: leafletScripts });
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
  const badges = sourceBadges(meta.source);

  return `
    <article class="artwork-card" data-title="${escapeHtml(meta.title || '')}" data-date="${escapeHtml(meta.date || '')}"${artistAttr}>
      <h3><a href="../artworks/${artwork.id}.html">${escapeHtml(meta.title)}</a> ${badges}</h3>
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
 * Location card template (for embedding in artist pages for architectural works)
 */
export function locationCardTemplate(location) {
  const meta = location.metadata;
  const image = meta.images?.[0];

  const metaItems = [];
  if (meta.city) {
    metaItems.push(`<span class="city">${escapeHtml(meta.city.replace(/, Italy$/, ''))}</span>`);
  }
  if (meta.architecturalStyle) {
    metaItems.push(`<span class="style">${escapeHtml(meta.architecturalStyle)}</span>`);
  }

  return `
    <article class="location-card">
      <h3><a href="../locations/${location.id}.html">${escapeHtml(meta.title)}</a></h3>
      <div class="location-card-meta">${metaItems.join('')}</div>
      ${image ? `<img src="${escapeHtml(fixImagePath(image.src, 'locations'))}" alt="${escapeHtml(meta.title)}" loading="lazy">` : ''}
    </article>
  `;
}

/**
 * Artist page template
 */
export function artistTemplate(artist, artworks, architecturalWorks = []) {
  const meta = artist.metadata;

  const links = [];
  if (meta.wikipedia) {
    links.push(`<a href="${escapeHtml(meta.wikipedia)}" target="_blank" rel="noopener noreferrer">Wikipedia</a>`);
  }

  // Generate architectural works section (if any)
  const architecturalWorksHtml = architecturalWorks.length > 0
    ? architecturalWorks.map(l => locationCardTemplate(l)).join('\n')
    : '';

  const architecturalWorksSection = architecturalWorks.length > 0 ? `
      <section class="architectural-works-section">
        <h2>Architectural Works</h2>
        <div class="location-grid">
          ${architecturalWorksHtml}
        </div>
      </section>
  ` : '';

  // Sort artworks by date and generate cards (no artist sort for single-artist pages)
  const sortedArtworks = sortArtworksByDate(artworks);
  const artworksHtml = sortedArtworks.length > 0
    ? sortedArtworks.map(a => artworkCardTemplate(a, false)).join('\n')
    : '<p class="no-artworks">No artworks documented yet.</p>';

  const sortControls = sortedArtworks.length > 1 ? sortControlsTemplate(false) : '';
  const badges = sourceBadges(meta.source);

  const content = `
    <article class="artist-page">
      <h1>${escapeHtml(meta.title)} ${badges}</h1>
      ${links.length > 0 ? `<div class="external-links">${links.join(' ')}</div>` : ''}
      ${meta.bio ? `<div class="bio">${parseMarkdown(meta.bio)}</div>` : ''}
      ${architecturalWorksSection}
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
  const badges = sourceBadges(meta.source);

  const content = `
    <article class="location-page">
      <h1>${escapeHtml(meta.title)} ${badges}</h1>
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

  const badges = sourceBadges(meta.source);

  const content = `
    <article class="artwork-page">
      <h1>${escapeHtml(meta.title)} ${badges}</h1>
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
 * Credits page template
 */
export function creditsTemplate(creditMarkdown) {
  const rows = parseMarkdownTable(creditMarkdown);

  const tableRows = rows.map(row => {
    const localFile = row['Local File'] || '';
    const originalUrl = row['Original URL'] || '';
    const source = row['Source'] || '';

    // Clean up backticks from local file name
    const cleanFileName = localFile.replace(/`/g, '');

    return `
      <tr>
        <td><code>${escapeHtml(cleanFileName)}</code></td>
        <td><a href="${escapeHtml(originalUrl)}" target="_blank" rel="noopener noreferrer">${escapeHtml(originalUrl.length > 60 ? originalUrl.substring(0, 60) + '...' : originalUrl)}</a></td>
        <td>${escapeHtml(source)}</td>
      </tr>
    `;
  }).join('\n');

  const content = `
    <article class="credits-page">
      <h1>Image Credits</h1>
      <p>All images used in this project are sourced from Wikimedia Commons and are used under their respective licenses.</p>
      <table class="credits-table">
        <thead>
          <tr>
            <th>Local File</th>
            <th>Original URL</th>
            <th>Source</th>
          </tr>
        </thead>
        <tbody>
          ${tableRows}
        </tbody>
      </table>
    </article>
  `;

  return layoutTemplate('Image Credits', content, 0);
}

/**
 * Convert a string to a URL-friendly slug
 */
function slugify(text) {
  return text.toLowerCase()
    .replace(/[()]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '');
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
 * Generate source badge(s) based on source metadata
 */
function sourceBadges(source) {
  if (!source) return '';
  const badges = [];
  if (source.myStudy && source.selfResearch) {
    badges.push('<span class="badge badge-study">My Study</span>');
    badges.push('<span class="badge badge-researched">Self-researched</span>');
  } else if (source.myStudy) {
    badges.push('<span class="badge badge-study">My Study</span>');
  } else if (source.selfResearch) {
    badges.push('<span class="badge badge-researched">Self-researched</span>');
  }
  return badges.join(' ');
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
