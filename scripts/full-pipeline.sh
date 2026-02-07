#!/bin/bash
#
# Full pipeline script for Italian Renaissance Art project
# Runs: research (optional) → export → generate site → publish → git commit/push
#
# Usage:
#   ./scripts/full-pipeline.sh                    # Export and publish only
#   ./scripts/full-pipeline.sh "Galleria Borghese"  # Research location, then export/publish
#

set -e

PROJECT_DIR="/Users/jason/src/HistoryOfItalianRenaissanceArt"
GITHUB_PAGES_DIR="/Users/jason/src/jasonhojh1122.github.io"
LOG_FILE="$PROJECT_DIR/full_pipeline.log"

RESEARCH_TARGET="$1"

cd "$PROJECT_DIR"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" | tee -a "$LOG_FILE"
}

log "Pipeline started"

# Step 1: Auto-research (if target provided)
if [ -n "$RESEARCH_TARGET" ]; then
    log "Step 1: Researching '$RESEARCH_TARGET'..."
    claude -p "/auto-research $RESEARCH_TARGET" \
        --verbose \
        --allowedTools "Bash,Read,Write,Edit,Glob,Grep,WebFetch,WebSearch,Skill"
    log "Step 1: Research completed"
else
    log "Step 1: Skipped (no research target)"
fi

# Step 2: Export notes
log "Step 2: Exporting notes..."
claude -p "/export-notes" \
    --verbose \
    --allowedTools "Bash,Read,Write,Edit,Glob,Grep,WebFetch,WebSearch,Skill"
log "Step 2: Export completed"

# Step 3: Generate site
log "Step 3: Generating site..."
cd "$PROJECT_DIR/generator" && npm run build && cd "$PROJECT_DIR"
log "Step 3: Site generation completed"

# Step 4: Publish to GitHub Pages
log "Step 4: Publishing..."
./scripts/publish.sh
log "Step 4: Publish completed"

# Step 5: Commit and push main repo
log "Step 5: Committing main repo..."
git add -A
if [ -n "$RESEARCH_TARGET" ]; then
    git commit -m "Auto-update ($RESEARCH_TARGET): $(date '+%Y-%m-%d %H:%M')" || log "Nothing to commit in main repo"
else
    git commit -m "Auto-update: $(date '+%Y-%m-%d %H:%M')" || log "Nothing to commit in main repo"
fi
git push origin main || log "Push failed or nothing to push in main repo"
log "Step 5: Main repo commit completed"

# Step 6: Commit and push GitHub Pages repo
log "Step 6: Pushing GitHub Pages..."
cd "$GITHUB_PAGES_DIR"
git add -A
if [ -n "$RESEARCH_TARGET" ]; then
    git commit -m "Site update ($RESEARCH_TARGET): $(date '+%Y-%m-%d %H:%M')" || log "Nothing to commit in GitHub Pages"
else
    git commit -m "Site update: $(date '+%Y-%m-%d %H:%M')" || log "Nothing to commit in GitHub Pages"
fi
git push origin master || log "Push failed or nothing to push in GitHub Pages"
log "Step 6: GitHub Pages commit completed"

log "Pipeline completed successfully"
