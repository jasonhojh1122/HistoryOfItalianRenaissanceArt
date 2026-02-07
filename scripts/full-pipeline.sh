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

format_duration() {
    local secs=$1
    if [ "$secs" -ge 3600 ]; then
        printf "%dh %dm %ds" $((secs/3600)) $((secs%3600/60)) $((secs%60))
    elif [ "$secs" -ge 60 ]; then
        printf "%dm %ds" $((secs/60)) $((secs%60))
    else
        printf "%ds" "$secs"
    fi
}

log "Pipeline started"

# Step 1: Auto-research (if target provided)
if [ -n "$RESEARCH_TARGET" ]; then
    step1_start=$(date +%s)
    step1_time=$(date '+%H:%M:%S')
    log "Step 1: Research '$RESEARCH_TARGET' — Started $step1_time"
    claude -p "/auto-research $RESEARCH_TARGET" \
        --verbose \
        --allowedTools "Bash,Read,Write,Edit,Glob,Grep,WebFetch,WebSearch,Skill"
    step1_elapsed=$(( $(date +%s) - step1_start ))
    log "Step 1: Research '$RESEARCH_TARGET' — Started $step1_time | Completed $(date '+%H:%M:%S') ($(format_duration $step1_elapsed))"
else
    log "Step 1: Research — Skipped (no research target)"
fi

# Step 2: Export notes
step2_start=$(date +%s)
step2_time=$(date '+%H:%M:%S')
log "Step 2: Export notes — Started $step2_time"
claude -p "/export-notes" \
    --verbose \
    --allowedTools "Bash,Read,Write,Edit,Glob,Grep,WebFetch,WebSearch,Skill"
step2_elapsed=$(( $(date +%s) - step2_start ))
log "Step 2: Export notes — Started $step2_time | Completed $(date '+%H:%M:%S') ($(format_duration $step2_elapsed))"

# Step 3: Generate site
step3_start=$(date +%s)
step3_time=$(date '+%H:%M:%S')
log "Step 3: Generate site — Started $step3_time"
cd "$PROJECT_DIR/generator" && npm run build && cd "$PROJECT_DIR"
step3_elapsed=$(( $(date +%s) - step3_start ))
log "Step 3: Generate site — Started $step3_time | Completed $(date '+%H:%M:%S') ($(format_duration $step3_elapsed))"

# Step 4: Publish to GitHub Pages (sync, commit, and push both repos)
step4_start=$(date +%s)
step4_time=$(date '+%H:%M:%S')
log "Step 4: Publish — Started $step4_time"
if [ -n "$RESEARCH_TARGET" ]; then
    ./scripts/publish.sh "Auto-update ($RESEARCH_TARGET): $(date '+%Y-%m-%d %H:%M')"
else
    ./scripts/publish.sh "Auto-update: $(date '+%Y-%m-%d %H:%M')"
fi
step4_elapsed=$(( $(date +%s) - step4_start ))
log "Step 4: Publish — Started $step4_time | Completed $(date '+%H:%M:%S') ($(format_duration $step4_elapsed))"

log "Pipeline completed successfully"
