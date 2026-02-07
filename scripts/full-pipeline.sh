#!/bin/bash
#
# Full pipeline script for Italian Renaissance Art project
# Runs: research (optional) → export → generate site → publish
#
# Usage:
#   ./scripts/full-pipeline.sh                    # Export and publish only
#   ./scripts/full-pipeline.sh "Galleria Borghese"  # Research location, then export/publish
#

set -e

PROJECT_DIR="/Users/jason/src/HistoryOfItalianRenaissanceArt"
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

# Step 4: Publish to GitHub Pages (sync, commit, and push both repos)
log "Step 4: Publishing..."
if [ -n "$RESEARCH_TARGET" ]; then
    ./scripts/publish.sh "Auto-update ($RESEARCH_TARGET): $(date '+%Y-%m-%d %H:%M')"
else
    ./scripts/publish.sh "Auto-update: $(date '+%Y-%m-%d %H:%M')"
fi
log "Step 4: Publish completed"

log "Pipeline completed successfully"
