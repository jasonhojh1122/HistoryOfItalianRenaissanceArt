#!/bin/bash

# Publish site to GitHub Pages repository
# Takes a commit message, commits and pushes this repo,
# syncs ./site/* to ~/src/jasonhojh1122.github.io/site/*,
# then commits and pushes the GitHub Pages repo with the same message.
#
# Usage: ./scripts/publish.sh "commit message"

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SOURCE_DIR="$PROJECT_DIR/site"
GITHUB_PAGES_DIR="$HOME/src/jasonhojh1122.github.io"
DEST_DIR="$GITHUB_PAGES_DIR/site"

COMMIT_MSG="$1"
if [ -z "$COMMIT_MSG" ]; then
    echo "Usage: $0 \"commit message\""
    exit 1
fi

if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: Source directory $SOURCE_DIR does not exist"
    exit 1
fi

if [ ! -d "$GITHUB_PAGES_DIR" ]; then
    echo "Error: Repository $GITHUB_PAGES_DIR does not exist"
    exit 1
fi

# Step 1: Commit and push main repo
echo "Committing main repo..."
cd "$PROJECT_DIR"
git add -A
git commit -m "$COMMIT_MSG" || echo "Nothing to commit in main repo"
git push origin main || echo "Push failed or nothing to push in main repo"

# Step 2: Rsync site to GitHub Pages repo
mkdir -p "$DEST_DIR"
echo "Syncing $SOURCE_DIR/* to $DEST_DIR/"
rsync -av --delete "$SOURCE_DIR/" "$DEST_DIR/"

# Step 3: Commit and push GitHub Pages repo
echo "Committing GitHub Pages repo..."
cd "$GITHUB_PAGES_DIR"
git add -A
git commit -m "$COMMIT_MSG" || echo "Nothing to commit in GitHub Pages"
git push origin master || echo "Push failed or nothing to push in GitHub Pages"

echo "Done!"
