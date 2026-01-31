#!/bin/bash

# Publish site to GitHub Pages repository
# Syncs ./site/* to ~/src/jasonhojh1122.github.io/site/*

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SOURCE_DIR="$PROJECT_DIR/site"
DEST_DIR="$HOME/src/jasonhojh1122.github.io/site"

if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: Source directory $SOURCE_DIR does not exist"
    exit 1
fi

DEST_REPO="$HOME/src/jasonhojh1122.github.io"
if [ ! -d "$DEST_REPO" ]; then
    echo "Error: Repository $DEST_REPO does not exist"
    exit 1
fi

mkdir -p "$DEST_DIR"

echo "Syncing $SOURCE_DIR/* to $DEST_DIR/"
rsync -av --delete "$SOURCE_DIR/" "$DEST_DIR/"
echo "Done!"
