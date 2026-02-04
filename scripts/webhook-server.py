#!/usr/bin/env python3
"""
Webhook server for remote pipeline triggering and Claude commands.

Usage:
    python3 scripts/webhook-server.py

Endpoints:
    GET  /           - Web interface
    POST /pipeline   - Trigger full pipeline (optional: {"target": "Location Name"})
    POST /research   - Research only (requires: {"target": "Location Name"})
    POST /run        - Run any Claude command (requires: {"prompt": "..."})
    GET  /status     - Check pipeline status (JSON)
    GET  /log        - Get full log (JSON)
"""

from flask import Flask, request, jsonify, Response
import subprocess
import threading
from datetime import datetime

app = Flask(__name__)
PROJECT_DIR = "/Users/jason/src/HistoryOfItalianRenaissanceArt"

# Track running jobs
current_job = {
    "running": False,
    "type": None,
    "target": None,
    "log": [],
    "started_at": None,
    "completed_at": None,
    "exit_code": None
}


def run_claude(prompt, job_type="claude"):
    """Run any Claude command in background thread"""
    global current_job
    current_job = {
        "running": True,
        "type": job_type,
        "target": prompt[:100] + "..." if len(prompt) > 100 else prompt,
        "log": [],
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "exit_code": None
    }

    try:
        cmd = [
            "claude", "-p", prompt,
            "--allowedTools", "Bash,Read,Write,Edit,Glob,Grep,WebFetch,WebSearch,Skill"
        ]

        current_job["log"].append(f"$ claude -p \"{prompt[:80]}...\"")
        current_job["log"].append("")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=PROJECT_DIR
        )

        for line in process.stdout:
            current_job["log"].append(line.rstrip())

        process.wait()
        current_job["running"] = False
        current_job["completed_at"] = datetime.now().isoformat()
        current_job["exit_code"] = process.returncode
        current_job["log"].append("")
        current_job["log"].append(f"[Completed with exit code {process.returncode}]")
    except Exception as e:
        current_job["running"] = False
        current_job["completed_at"] = datetime.now().isoformat()
        current_job["exit_code"] = -1
        current_job["log"].append(f"[Error: {str(e)}]")


def run_pipeline(target=None):
    """Run the full pipeline in background thread"""
    global current_job
    current_job = {
        "running": True,
        "type": "pipeline",
        "target": target or "(export only)",
        "log": [],
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "exit_code": None
    }

    try:
        cmd = [f"{PROJECT_DIR}/scripts/full-pipeline.sh"]
        if target:
            cmd.append(target)

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=PROJECT_DIR
        )

        for line in process.stdout:
            current_job["log"].append(line.rstrip())

        process.wait()
        current_job["running"] = False
        current_job["completed_at"] = datetime.now().isoformat()
        current_job["exit_code"] = process.returncode
        current_job["log"].append(f"[Pipeline completed with exit code {process.returncode}]")
    except Exception as e:
        current_job["running"] = False
        current_job["completed_at"] = datetime.now().isoformat()
        current_job["exit_code"] = -1
        current_job["log"].append(f"[Error: {str(e)}]")


# HTML template for web interface
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Art Research Pipeline</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: #1a1a2e;
            color: #eee;
        }
        h1 { color: #e94560; margin-bottom: 5px; }
        .subtitle { color: #888; margin-bottom: 20px; }
        .card {
            background: #16213e;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .card h2 { margin-top: 0; color: #e94560; font-size: 1.1em; }
        input[type="text"], textarea {
            width: 100%;
            padding: 12px;
            border: 1px solid #333;
            border-radius: 6px;
            background: #0f0f23;
            color: #eee;
            font-size: 16px;
            margin-bottom: 10px;
        }
        textarea { min-height: 80px; resize: vertical; font-family: inherit; }
        button {
            background: #e94560;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
            margin-right: 10px;
            margin-bottom: 10px;
        }
        button:hover { background: #ff6b6b; }
        button:disabled { background: #555; cursor: not-allowed; }
        button.secondary { background: #0f3460; }
        button.secondary:hover { background: #1a4a7a; }
        .status {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
        }
        .status.running { background: #f39c12; color: #000; }
        .status.idle { background: #27ae60; }
        .status.error { background: #e74c3c; }
        #log {
            background: #0f0f23;
            border-radius: 6px;
            padding: 15px;
            font-family: "SF Mono", Monaco, monospace;
            font-size: 13px;
            line-height: 1.5;
            max-height: 400px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        .meta { color: #888; font-size: 0.85em; margin-top: 10px; }
        .quick-actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 15px; }
        .quick-actions button { margin: 0; padding: 8px 16px; font-size: 14px; }
        @media (max-width: 600px) {
            body { padding: 10px; }
            button { width: 100%; margin-right: 0; }
        }
    </style>
</head>
<body>
    <h1>Art Research Pipeline</h1>
    <p class="subtitle">Italian Renaissance Art Project</p>

    <div class="card">
        <h2>Status</h2>
        <p>
            <span id="status" class="status idle">Idle</span>
            <span id="job-info" style="margin-left: 10px; color: #888;"></span>
        </p>
        <div id="log">Waiting for activity...</div>
        <p class="meta">
            <span id="timing"></span>
        </p>
    </div>

    <div class="card">
        <h2>Run Claude Command</h2>
        <textarea id="prompt" placeholder="Enter any instruction for Claude..."></textarea>
        <button onclick="runCommand()" id="run-btn">Run Command</button>
        <button onclick="runCommand('/export-notes')" class="secondary">Export Notes</button>

        <div class="quick-actions">
            <button class="secondary" onclick="runCommand('/auto-research Galleria Borghese')">Borghese</button>
            <button class="secondary" onclick="runCommand('/auto-research Uffizi Gallery')">Uffizi</button>
            <button class="secondary" onclick="runCommand('/auto-research Vatican Museums')">Vatican</button>
        </div>
    </div>

    <div class="card">
        <h2>Full Pipeline</h2>
        <input type="text" id="target" placeholder="Research target (optional, e.g., 'Galleria Borghese')">
        <button onclick="runPipeline()" id="pipeline-btn">Run Full Pipeline</button>
        <p class="meta">Runs: research (if target) → export → generate site → publish → git push</p>
    </div>

    <script>
        let refreshInterval;

        async function fetchStatus() {
            try {
                const res = await fetch('/status');
                const data = await res.json();

                const statusEl = document.getElementById('status');
                const logEl = document.getElementById('log');
                const jobInfo = document.getElementById('job-info');
                const timing = document.getElementById('timing');

                if (data.running) {
                    statusEl.textContent = 'Running';
                    statusEl.className = 'status running';
                    jobInfo.textContent = `${data.type}: ${data.target}`;
                    document.getElementById('run-btn').disabled = true;
                    document.getElementById('pipeline-btn').disabled = true;
                } else {
                    statusEl.textContent = data.exit_code === 0 ? 'Completed' : (data.exit_code ? 'Error' : 'Idle');
                    statusEl.className = 'status ' + (data.exit_code === 0 ? 'idle' : (data.exit_code ? 'error' : 'idle'));
                    jobInfo.textContent = data.type ? `Last: ${data.type}` : '';
                    document.getElementById('run-btn').disabled = false;
                    document.getElementById('pipeline-btn').disabled = false;
                }

                if (data.log && data.log.length > 0) {
                    logEl.textContent = data.log.join('\\n');
                    logEl.scrollTop = logEl.scrollHeight;
                }

                let timingText = '';
                if (data.started_at) {
                    timingText = `Started: ${new Date(data.started_at).toLocaleTimeString()}`;
                    if (data.completed_at) {
                        timingText += ` | Completed: ${new Date(data.completed_at).toLocaleTimeString()}`;
                    }
                }
                timing.textContent = timingText;

            } catch (e) {
                console.error('Failed to fetch status:', e);
            }
        }

        async function runCommand(preset) {
            const prompt = preset || document.getElementById('prompt').value.trim();
            if (!prompt) {
                alert('Please enter a command');
                return;
            }

            try {
                const res = await fetch('/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt })
                });
                const data = await res.json();
                if (data.error) {
                    alert(data.error);
                } else {
                    document.getElementById('prompt').value = '';
                    fetchStatus();
                }
            } catch (e) {
                alert('Failed to start command: ' + e.message);
            }
        }

        async function runPipeline() {
            const target = document.getElementById('target').value.trim();

            try {
                const res = await fetch('/pipeline', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ target: target || null })
                });
                const data = await res.json();
                if (data.error) {
                    alert(data.error);
                } else {
                    document.getElementById('target').value = '';
                    fetchStatus();
                }
            } catch (e) {
                alert('Failed to start pipeline: ' + e.message);
            }
        }

        // Initial fetch and start polling
        fetchStatus();
        refreshInterval = setInterval(fetchStatus, 2000);
    </script>
</body>
</html>'''


@app.route('/')
def index():
    """Web interface"""
    return Response(HTML_TEMPLATE, mimetype='text/html')


@app.route('/run', methods=['POST'])
def run_command():
    """Run any Claude command"""
    if current_job["running"]:
        return jsonify({
            "error": "A job is already running",
            "type": current_job["type"],
            "target": current_job["target"]
        }), 409

    data = request.get_json() or {}
    prompt = data.get('prompt', '').strip()
    if not prompt:
        return jsonify({"error": "prompt required"}), 400

    thread = threading.Thread(target=run_claude, args=(prompt,))
    thread.start()

    return jsonify({"status": "started", "prompt": prompt[:100]})


@app.route('/pipeline', methods=['POST'])
def trigger_pipeline():
    """Trigger the full pipeline"""
    if current_job["running"]:
        return jsonify({
            "error": "A job is already running",
            "type": current_job["type"],
            "target": current_job["target"]
        }), 409

    data = request.get_json() or {}
    target = data.get('target')

    thread = threading.Thread(target=run_pipeline, args=(target,))
    thread.start()

    return jsonify({"status": "started", "target": target})


@app.route('/research', methods=['POST'])
def trigger_research_only():
    """Trigger only auto-research"""
    if current_job["running"]:
        return jsonify({"error": "A job is already running"}), 409

    data = request.get_json() or {}
    target = data.get('target')
    if not target:
        return jsonify({"error": "target required"}), 400

    prompt = f"/auto-research {target}"
    thread = threading.Thread(target=run_claude, args=(prompt, "research"))
    thread.start()

    return jsonify({"status": "started", "target": target})


@app.route('/status', methods=['GET'])
def get_status():
    """Check job status"""
    return jsonify({
        "running": current_job["running"],
        "type": current_job["type"],
        "target": current_job["target"],
        "started_at": current_job["started_at"],
        "completed_at": current_job["completed_at"],
        "exit_code": current_job["exit_code"],
        "log": current_job["log"][-100:]  # Last 100 lines for web view
    })


@app.route('/log', methods=['GET'])
def get_full_log():
    """Get full log"""
    return jsonify({
        "log": current_job["log"],
        "line_count": len(current_job["log"])
    })


if __name__ == '__main__':
    print(f"Starting webhook server on port 8765...")
    print(f"Project directory: {PROJECT_DIR}")
    print(f"Web interface: http://localhost:8765/")
    app.run(host='0.0.0.0', port=8765)
