#!/usr/bin/env node

import path from 'path';
import { fileURLToPath } from 'url';
import { generateSite } from './generator.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Paths relative to generator directory
const rootDir = path.resolve(__dirname, '../..');  // Project root
const outputDir = path.resolve(rootDir, 'site');   // Output to site/

// Run the build
generateSite(rootDir, outputDir).catch(err => {
  console.error('Build failed:', err);
  process.exit(1);
});
