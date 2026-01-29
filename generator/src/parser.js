import { marked } from 'marked';
import fs from 'fs/promises';
import path from 'path';

/**
 * Custom renderer that converts .md links to .html
 */
function createRenderer() {
  const renderer = new marked.Renderer();

  const originalLink = renderer.link.bind(renderer);
  renderer.link = function(href, title, text) {
    // Handle marked v12+ signature where first arg is token object
    if (typeof href === 'object') {
      const token = href;
      href = token.href;
      title = token.title;
      text = token.text;
    }

    // Convert .md links to .html
    if (href && href.endsWith('.md')) {
      href = href.replace(/\.md$/, '.html');
    }

    // External links open in new tab
    const isExternal = href && (href.startsWith('http://') || href.startsWith('https://'));
    const target = isExternal ? ' target="_blank" rel="noopener noreferrer"' : '';

    const titleAttr = title ? ` title="${title}"` : '';
    return `<a href="${href}"${titleAttr}${target}>${text}</a>`;
  };

  return renderer;
}

const renderer = createRenderer();
marked.setOptions({ renderer });

/**
 * Parse markdown content to HTML
 */
export function parseMarkdown(content) {
  return marked.parse(content);
}

/**
 * Extract title from markdown (first h1)
 */
export function extractTitle(content) {
  const match = content.match(/^#\s+(.+)$/m);
  return match ? match[1].trim() : 'Untitled';
}

/**
 * Extract Wikipedia link from content
 */
export function extractWikipediaLink(content) {
  const match = content.match(/\[Wikipedia\]\(([^)]+)\)/);
  return match ? match[1] : null;
}

/**
 * Extract Google Maps link from content
 */
export function extractGoogleMapLink(content) {
  const match = content.match(/\[GoogleMap\]\(([^)]+)\)/);
  return match ? match[1] : null;
}

/**
 * Extract metadata from artwork file
 */
export function extractArtworkMetadata(content) {
  const metadata = {
    title: extractTitle(content),
    artist: null,
    artistFile: null,
    location: null,
    locationFile: null,
    medium: null,
    date: null,
    bibleStory: null,
    bibleStoryFile: null,
    biblicalContext: '',
    description: '',
    images: []
  };

  // Extract artist: - **Artist**: [Name](../artists/File.md)
  const artistMatch = content.match(/\*\*Artist\*\*:\s*\[([^\]]+)\]\(([^)]+)\)/);
  if (artistMatch) {
    metadata.artist = artistMatch[1];
    metadata.artistFile = path.basename(artistMatch[2], '.md');
  }

  // Extract location: - **Location**: [Name](../locations/File.md), City
  const locationMatch = content.match(/\*\*Location\*\*:\s*\[([^\]]+)\]\(([^)]+)\)(?:,\s*([^*\n]+))?/);
  if (locationMatch) {
    metadata.location = locationMatch[1];
    metadata.locationFile = path.basename(locationMatch[2], '.md');
    metadata.city = locationMatch[3]?.trim();
  }

  // Extract medium
  const mediumMatch = content.match(/\*\*Medium\*\*:\s*([^\n*]+)/);
  if (mediumMatch) {
    metadata.medium = mediumMatch[1].trim();
  }

  // Extract date
  const dateMatch = content.match(/\*\*Date\*\*:\s*([^\n*]+)/);
  if (dateMatch) {
    metadata.date = dateMatch[1].trim();
  }

  // Extract bible story link from Biblical Context section: [Story Name](../biblestories/File.md)
  const bibleStoryMatch = content.match(/##\s*Biblical Context\s*\n+\[([^\]]+)\]\(\.\.\/biblestories\/([^)]+)\.md\)/);
  if (bibleStoryMatch) {
    metadata.bibleStory = bibleStoryMatch[1];
    metadata.bibleStoryFile = bibleStoryMatch[2];
  }

  // Extract biblical context text (after the link)
  const biblicalContextMatch = content.match(/##\s*Biblical Context\s*\n+(?:\[[^\]]+\]\([^)]+\)\s*-?\s*)?([\s\S]*?)(?=\n##|$)/);
  if (biblicalContextMatch) {
    metadata.biblicalContext = biblicalContextMatch[1].trim();
  }

  // Extract description section
  const descMatch = content.match(/##\s*Description\s*\n+([\s\S]*?)(?=\n##|\n!\[|$)/);
  if (descMatch) {
    metadata.description = descMatch[1].trim();
  }

  // Extract all images
  const imageMatches = content.matchAll(/!\[([^\]]*)\]\(([^)]+)\)/g);
  for (const match of imageMatches) {
    metadata.images.push({
      alt: match[1],
      src: match[2]
    });
  }

  return metadata;
}

/**
 * Extract metadata from artist file
 */
export function extractArtistMetadata(content) {
  const metadata = {
    title: extractTitle(content),
    wikipedia: extractWikipediaLink(content),
    bio: '',
    artworkRefs: []
  };

  // Extract bio (content between Wikipedia link and ## Artworks)
  const bioMatch = content.match(/\[Wikipedia\][^\n]*\n+([\s\S]*?)(?=\n##\s*Artworks|$)/);
  if (bioMatch) {
    metadata.bio = bioMatch[1].trim();
  }

  // Extract artwork references from ### [Artwork Name](../artworks/File.md)
  const artworkMatches = content.matchAll(/###\s*\[([^\]]+)\]\(\.\.\/artworks\/([^)]+)\.md\)/g);
  for (const match of artworkMatches) {
    metadata.artworkRefs.push({
      title: match[1],
      file: match[2]
    });
  }

  return metadata;
}

/**
 * Extract metadata from bible story file
 */
export function extractBibleStoryMetadata(content) {
  const metadata = {
    title: extractTitle(content),
    wikipedia: extractWikipediaLink(content),
    summary: '',
    biblicalReference: {
      books: null,
      verses: null
    },
    artworkRefs: []
  };

  // Extract Chinese/alternate name (line after title, before Wikipedia)
  const lines = content.split('\n');
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (line.startsWith('#')) continue;
    if (line.startsWith('[Wikipedia]')) break;
    if (line === '') continue;
    // Chinese characters or simple text line
    if (!line.startsWith('##') && !line.startsWith('**') && !line.startsWith('-')) {
      metadata.alternateName = line;
      break;
    }
  }

  // Extract summary section
  const summaryMatch = content.match(/##\s*Summary\s*\n+([\s\S]*?)(?=\n##|$)/);
  if (summaryMatch) {
    metadata.summary = summaryMatch[1].trim();
  }

  // Extract biblical reference
  const booksMatch = content.match(/\*\*Book\(s\)\*\*:\s*([^\n]+)/);
  if (booksMatch) {
    metadata.biblicalReference.books = booksMatch[1].trim();
  }

  const versesMatch = content.match(/\*\*Chapters\/Verses\*\*:\s*([^\n]+)/);
  if (versesMatch) {
    metadata.biblicalReference.verses = versesMatch[1].trim();
  }

  // Extract artwork references from ### [Artwork Name](../artworks/File.md)
  const artworkMatches = content.matchAll(/###\s*\[([^\]]+)\]\(\.\.\/artworks\/([^)]+)\.md\)/g);
  for (const match of artworkMatches) {
    metadata.artworkRefs.push({
      title: match[1],
      file: match[2]
    });
  }

  return metadata;
}

/**
 * Extract metadata from location file
 */
export function extractLocationMetadata(content) {
  const metadata = {
    title: extractTitle(content),
    wikipedia: extractWikipediaLink(content),
    googleMap: extractGoogleMapLink(content),
    city: '',
    architecturalStyle: null,
    floorPlan: null,
    artworkRefs: []
  };

  // Extract city (line after links, before architectural style)
  const lines = content.split('\n');
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    // Skip title, links, and empty lines
    if (line.startsWith('#') || line.startsWith('[') || line === '') continue;
    // Stop if we hit artworks section
    if (line.startsWith('**') || line.startsWith('##')) break;
    // This should be the city line
    if (line.match(/^[A-Z][^*#\[]+$/)) {
      metadata.city = line;
      break;
    }
  }

  // Extract architectural style
  const styleMatch = content.match(/\*\*Architectural style\*\*:\s*([^\n]+)/);
  if (styleMatch) {
    metadata.architecturalStyle = styleMatch[1].trim();
  }

  // Extract floor plan image
  const floorPlanMatch = content.match(/!\[floor plan\]\(([^)]+)\)/i);
  if (floorPlanMatch) {
    metadata.floorPlan = floorPlanMatch[1];
  }

  // Extract artwork references
  const artworkMatches = content.matchAll(/###\s*\[([^\]]+)\]\(\.\.\/artworks\/([^)]+)\.md\)/g);
  for (const match of artworkMatches) {
    metadata.artworkRefs.push({
      title: match[1],
      file: match[2]
    });
  }

  return metadata;
}

/**
 * Read and parse a markdown file
 */
export async function parseFile(filePath) {
  const content = await fs.readFile(filePath, 'utf-8');
  const dir = path.dirname(filePath);
  const type = path.basename(dir);
  const id = path.basename(filePath, '.md');

  let metadata;
  if (type === 'artworks') {
    metadata = extractArtworkMetadata(content);
  } else if (type === 'artists') {
    metadata = extractArtistMetadata(content);
  } else if (type === 'locations') {
    metadata = extractLocationMetadata(content);
  } else if (type === 'biblestories') {
    metadata = extractBibleStoryMetadata(content);
  } else {
    metadata = { title: extractTitle(content) };
  }

  return {
    id,
    type,
    path: filePath,
    content,
    html: parseMarkdown(content),
    metadata
  };
}
