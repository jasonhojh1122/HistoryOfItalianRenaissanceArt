#!/usr/bin/env bash
set -euo pipefail

cd "generator"
npm install --silent
npm run build
