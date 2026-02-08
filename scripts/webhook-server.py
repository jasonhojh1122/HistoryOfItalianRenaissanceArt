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
    POST /stop       - Stop running job (kills child process group)
    GET  /git-status - Git status for both repos
    POST /git-reset  - Hard reset both repos to HEAD (blocked while job running)
    GET  /status     - Check pipeline status (JSON)
    GET  /log        - Get full log (JSON)
    POST /terminal   - Execute a zsh command (requires: {"command": "..."})
"""

from flask import Flask, request, jsonify, Response
import subprocess
import threading
import os
import select
import signal
from datetime import datetime

app = Flask(__name__)
PROJECT_DIR = "/Users/jason/src/HistoryOfItalianRenaissanceArt"
GITHUB_PAGES_DIR = "/Users/jason/src/jasonhojh1122.github.io"

# Track the current child process so /stop can kill it
current_process = None
current_process_lock = threading.Lock()

# Timeout in seconds: kill subprocess if it exceeds this
CLAUDE_TIMEOUT = 1800    # 30 minutes for a single claude command
PIPELINE_TIMEOUT = 3600  # 60 minutes for the full pipeline
TERMINAL_TIMEOUT = 120   # 120 seconds for terminal commands


def _kill_process(process, job, timeout):
    """Kill a subprocess and its children via process group."""
    if process.poll() is None:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass
        job["_stop"] = True
        job["log"].append(f"[Killed: exceeded {timeout}s timeout]")


def _read_process_output(process, job):
    """Read process output using select() so the loop can be interrupted via job['_stop']."""
    fd = process.stdout.fileno()
    buf = b''
    while not job.get("_stop"):
        try:
            ready, _, _ = select.select([fd], [], [], 0.5)
        except (ValueError, OSError):
            break
        if ready:
            try:
                chunk = os.read(fd, 4096)
            except OSError:
                break
            if not chunk:
                break
            buf += chunk
            while b'\n' in buf:
                line, buf = buf.split(b'\n', 1)
                decoded = line.decode('utf-8', errors='replace').rstrip()
                job["log"].append(decoded)
                if decoded:
                    job["progress"] = decoded
    # Flush remaining buffer
    if buf:
        decoded = buf.decode('utf-8', errors='replace').rstrip()
        if decoded:
            job["log"].append(decoded)


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
    global current_job, current_process
    current_job = {
        "running": True,
        "type": job_type,
        "target": prompt[:100] + "..." if len(prompt) > 100 else prompt,
        "log": [],
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "exit_code": None,
        "progress": "",
        "_stop": False
    }

    try:
        cmd = [
            "claude", "-p", prompt,
            "--verbose",
            "--allowedTools", "Bash,Read,Write,Edit,Glob,Grep,WebFetch,WebSearch,Skill"
        ]

        current_job["log"].append(f"$ claude -p \"{prompt[:80]}...\"")
        current_job["log"].append("")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=PROJECT_DIR,
            preexec_fn=os.setsid
        )

        with current_process_lock:
            current_process = process

        timer = threading.Timer(CLAUDE_TIMEOUT, _kill_process, args=(process, current_job, CLAUDE_TIMEOUT))
        timer.daemon = True
        timer.start()
        try:
            _read_process_output(process, current_job)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    process.kill()
                except OSError:
                    pass
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    if process.returncode is None:
                        process.returncode = -9
        finally:
            timer.cancel()
            with current_process_lock:
                current_process = None

        current_job["running"] = False
        current_job["completed_at"] = datetime.now().isoformat()
        current_job["exit_code"] = process.returncode
        current_job["log"].append("")
        if process.returncode == -9:
            current_job["log"].append("[Stopped by user]")
        else:
            current_job["log"].append(f"[Completed with exit code {process.returncode}]")
    except Exception as e:
        with current_process_lock:
            current_process = None
        current_job["running"] = False
        current_job["completed_at"] = datetime.now().isoformat()
        current_job["exit_code"] = -1
        current_job["log"].append(f"[Error: {str(e)}]")


def run_pipeline(target=None):
    """Run the full pipeline in background thread"""
    global current_job, current_process
    current_job = {
        "running": True,
        "type": "pipeline",
        "target": target or "(export only)",
        "log": [],
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "exit_code": None,
        "progress": "",
        "_stop": False
    }

    try:
        cmd = [f"{PROJECT_DIR}/scripts/full-pipeline.sh"]
        if target:
            cmd.append(target)

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=PROJECT_DIR,
            preexec_fn=os.setsid
        )

        with current_process_lock:
            current_process = process

        timer = threading.Timer(PIPELINE_TIMEOUT, _kill_process, args=(process, current_job, PIPELINE_TIMEOUT))
        timer.daemon = True
        timer.start()
        try:
            _read_process_output(process, current_job)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    process.kill()
                except OSError:
                    pass
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    if process.returncode is None:
                        process.returncode = -9
        finally:
            timer.cancel()
            with current_process_lock:
                current_process = None

        current_job["running"] = False
        current_job["completed_at"] = datetime.now().isoformat()
        current_job["exit_code"] = process.returncode
        if process.returncode == -9:
            current_job["log"].append("[Stopped by user]")
        else:
            current_job["log"].append(f"[Pipeline completed with exit code {process.returncode}]")
    except Exception as e:
        with current_process_lock:
            current_process = None
        current_job["running"] = False
        current_job["completed_at"] = datetime.now().isoformat()
        current_job["exit_code"] = -1
        current_job["log"].append(f"[Error: {str(e)}]")


# HTML template for web interface — Renaissance aesthetic matching the static site
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Art Research Pipeline</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=Spectral:ital,wght@0,300;0,400;0,500;1,300;1,400&display=swap" rel="stylesheet">
    <style>
        :root {
            --color-ivory: #FAF6F0;
            --color-parchment: #F5EDE3;
            --color-warm-white: #FFFDF9;
            --color-terracotta: #B85C38;
            --color-terracotta-deep: #8B3A2F;
            --color-sienna: #A0522D;
            --color-umber: #5D4037;
            --color-gold: #C7A66B;
            --color-gold-muted: #B8976B;
            --color-ink: #2C2418;
            --color-ink-soft: #4A4035;
            --color-stone: #8D8477;
            --color-border: #E3DCD0;
            --color-border-dark: #C9C0B0;
            --font-display: 'Cormorant Garamond', 'Palatino Linotype', serif;
            --font-body: 'Spectral', 'Georgia', serif;
            --shadow-soft: 0 2px 20px rgba(44, 36, 24, 0.06);
            --shadow-card: 0 4px 30px rgba(44, 36, 24, 0.08);
            --shadow-elevated: 0 12px 40px rgba(44, 36, 24, 0.12);
            --transition-base: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        html {
            font-size: 17px;
            scroll-behavior: smooth;
            -webkit-font-smoothing: antialiased;
        }

        body {
            font-family: var(--font-body);
            background: var(--color-ivory);
            color: var(--color-ink);
            line-height: 1.75;
            min-height: 100vh;
            position: relative;
        }

        /* Subtle grain texture overlay */
        body::before {
            content: '';
            position: fixed;
            inset: 0;
            pointer-events: none;
            opacity: 0.025;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
            z-index: 1000;
        }

        .container {
            max-width: 860px;
            margin: 0 auto;
            padding: 2.5rem 2rem;
        }

        /* Header */
        header {
            text-align: center;
            margin-bottom: 3rem;
            padding-bottom: 2rem;
            border-bottom: 1px solid var(--color-border);
            position: relative;
        }

        header::after {
            content: '';
            position: absolute;
            bottom: -1px;
            left: 50%;
            transform: translateX(-50%);
            width: 80px;
            height: 3px;
            background: linear-gradient(to right, var(--color-terracotta), var(--color-gold));
        }

        h1 {
            font-family: var(--font-display);
            font-size: clamp(2.2rem, 5vw, 3rem);
            font-weight: 500;
            letter-spacing: -0.01em;
            color: var(--color-ink);
            margin-bottom: 0.5rem;
        }

        .subtitle {
            font-family: var(--font-display);
            font-size: 1.15rem;
            font-style: italic;
            color: var(--color-stone);
            letter-spacing: 0.02em;
        }

        /* Cards */
        .card {
            background: var(--color-warm-white);
            border: 1px solid var(--color-border);
            border-radius: 5px;
            padding: 1.75rem;
            margin-bottom: 1.5rem;
            position: relative;
            box-shadow: var(--shadow-soft);
            transition: box-shadow var(--transition-base), border-color var(--transition-base);
        }

        .card:hover {
            box-shadow: var(--shadow-card);
            border-color: var(--color-border-dark);
        }

        .card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: linear-gradient(to bottom, var(--color-terracotta), var(--color-gold));
            border-radius: 5px 0 0 5px;
            opacity: 0;
            transition: opacity var(--transition-base);
        }

        .card:hover::before {
            opacity: 1;
        }

        .card h2 {
            font-family: var(--font-display);
            font-size: 1.35rem;
            font-weight: 600;
            color: var(--color-ink);
            margin-bottom: 1rem;
            position: relative;
            display: inline-block;
        }

        .card h2::after {
            content: '';
            position: absolute;
            bottom: -4px;
            left: 0;
            width: 40px;
            height: 2px;
            background: linear-gradient(to right, var(--color-terracotta), var(--color-gold));
        }

        /* Status Badge */
        .status-row {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
        }

        .status {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.4rem 1rem;
            border-radius: 999px;
            font-family: var(--font-body);
            font-size: 0.85rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        .status::before {
            content: '';
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }

        .status.idle {
            background: linear-gradient(135deg, #E8F0E4 0%, #D4E5CC 100%);
            color: #3A5F35;
            border: 1px solid #B8D4AD;
        }

        .status.idle::before {
            background: #4A7C43;
        }

        .status.running {
            background: linear-gradient(135deg, #FFF4E0 0%, #FFE7C4 100%);
            color: #8B5A00;
            border: 1px solid #E5C896;
            animation: pulse 2s ease-in-out infinite;
        }

        .status.running::before {
            background: #D4940A;
            animation: blink 1s ease-in-out infinite;
        }

        .status.error {
            background: linear-gradient(135deg, #FDEAEA 0%, #F9D6D6 100%);
            color: #8B3A2F;
            border: 1px solid #E5B3AD;
        }

        .status.error::before {
            background: #B85C38;
        }

        @keyframes pulse {
            0%, 100% { box-shadow: 0 0 0 0 rgba(212, 148, 10, 0.3); }
            50% { box-shadow: 0 0 0 8px rgba(212, 148, 10, 0); }
        }

        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }

        .job-info {
            font-family: var(--font-body);
            font-size: 0.9rem;
            color: var(--color-stone);
            font-style: italic;
        }

        /* Log Display */
        #log {
            background: var(--color-parchment);
            border: 1px solid var(--color-border);
            border-radius: 3px;
            padding: 1.25rem;
            font-family: "SF Mono", "Menlo", "Monaco", "Consolas", monospace;
            font-size: 0.8rem;
            line-height: 1.7;
            max-height: 380px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
            color: var(--color-ink-soft);
            position: relative;
        }

        #log::-webkit-scrollbar {
            width: 6px;
        }

        #log::-webkit-scrollbar-track {
            background: var(--color-border);
            border-radius: 3px;
        }

        #log::-webkit-scrollbar-thumb {
            background: var(--color-stone);
            border-radius: 3px;
        }

        .meta {
            font-family: var(--font-body);
            font-size: 0.8rem;
            color: var(--color-stone);
            margin-top: 0.75rem;
            font-style: italic;
        }

        /* Form Elements */
        input[type="text"], textarea {
            width: 100%;
            padding: 0.85rem 1rem;
            border: 1px solid var(--color-border);
            border-radius: 3px;
            background: var(--color-warm-white);
            color: var(--color-ink);
            font-family: var(--font-body);
            font-size: 0.95rem;
            margin-bottom: 1rem;
            transition: all var(--transition-base);
        }

        input[type="text"]::placeholder, textarea::placeholder {
            color: var(--color-stone);
            font-style: italic;
        }

        input[type="text"]:focus, textarea:focus {
            outline: none;
            border-color: var(--color-terracotta);
            box-shadow: 0 0 0 3px rgba(184, 92, 56, 0.1);
        }

        textarea {
            min-height: 90px;
            resize: vertical;
            line-height: 1.6;
        }

        /* Buttons */
        button {
            font-family: var(--font-body);
            font-size: 0.9rem;
            font-weight: 500;
            padding: 0.75rem 1.5rem;
            border-radius: 3px;
            cursor: pointer;
            transition: all var(--transition-base);
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-right: 0.75rem;
            margin-bottom: 0.75rem;
        }

        button.primary {
            background: linear-gradient(135deg, var(--color-terracotta) 0%, var(--color-sienna) 100%);
            color: var(--color-warm-white);
            border: none;
            box-shadow: 0 2px 8px rgba(184, 92, 56, 0.3);
        }

        button.primary:hover {
            background: linear-gradient(135deg, var(--color-terracotta-deep) 0%, var(--color-terracotta) 100%);
            box-shadow: 0 4px 12px rgba(184, 92, 56, 0.4);
            transform: translateY(-1px);
        }

        button.primary:active {
            transform: translateY(0);
        }

        button.primary:disabled {
            background: var(--color-border-dark);
            color: var(--color-stone);
            cursor: not-allowed;
            box-shadow: none;
            transform: none;
        }

        button.secondary {
            background: var(--color-warm-white);
            color: var(--color-ink-soft);
            border: 1px solid var(--color-border);
        }

        button.secondary:hover {
            border-color: var(--color-gold);
            color: var(--color-umber);
            background: var(--color-parchment);
        }

        button.secondary:disabled {
            background: var(--color-parchment);
            color: var(--color-stone);
            border-color: var(--color-border);
            cursor: not-allowed;
        }

        button.danger {
            background: linear-gradient(135deg, var(--color-terracotta) 0%, var(--color-terracotta-deep) 100%);
            color: var(--color-warm-white);
            border: none;
            box-shadow: 0 2px 8px rgba(139, 58, 47, 0.3);
        }

        button.danger:hover {
            background: linear-gradient(135deg, var(--color-terracotta-deep) 0%, #6B2A1F 100%);
            box-shadow: 0 4px 12px rgba(139, 58, 47, 0.4);
            transform: translateY(-1px);
        }

        button.danger:active {
            transform: translateY(0);
        }

        button.danger:disabled {
            background: var(--color-border-dark);
            color: var(--color-stone);
            cursor: not-allowed;
            box-shadow: none;
            transform: none;
        }

        /* Quick Actions */
        .quick-actions {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 1.25rem;
            padding-top: 1.25rem;
            border-top: 1px solid var(--color-border);
        }

        .quick-actions-label {
            width: 100%;
            font-family: var(--font-body);
            font-size: 0.75rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--color-stone);
            margin-bottom: 0.5rem;
        }

        .quick-actions button {
            margin: 0;
            padding: 0.5rem 1rem;
            font-size: 0.8rem;
        }

        /* Pipeline Card Special Styling */
        .pipeline-card {
            background: linear-gradient(135deg, var(--color-parchment) 0%, var(--color-ivory) 100%);
            border-left: 4px solid var(--color-gold);
        }

        .pipeline-card::before {
            display: none;
        }

        .pipeline-steps {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px dashed var(--color-border);
        }

        .pipeline-step {
            font-family: var(--font-body);
            font-size: 0.75rem;
            padding: 0.35rem 0.75rem;
            background: var(--color-warm-white);
            border: 1px solid var(--color-border);
            border-radius: 999px;
            color: var(--color-stone);
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }

        .pipeline-step::after {
            content: '→';
            color: var(--color-border-dark);
        }

        .pipeline-step:last-child::after {
            display: none;
        }

        /* Footer */
        footer {
            text-align: center;
            padding: 2rem;
            border-top: 1px solid var(--color-border);
            margin-top: 2rem;
        }

        footer p {
            font-family: var(--font-display);
            font-size: 0.9rem;
            font-style: italic;
            color: var(--color-stone);
        }

        /* Progress Bar */
        .progress-bar {
            background: var(--color-parchment);
            border: 1px solid var(--color-border);
            border-bottom: none;
            border-radius: 3px 3px 0 0;
            padding: 0.5rem 1rem;
            font-family: "SF Mono", "Menlo", monospace;
            font-size: 0.75rem;
            color: var(--color-terracotta);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 100%;
        }

        /* Terminal — Scribe's Desk */
        .terminal-card {
            background: #1A1510;
            border: 1px solid #3D3225;
            position: relative;
            overflow: hidden;
        }

        .terminal-card::after {
            content: '';
            position: absolute;
            inset: 0;
            pointer-events: none;
            opacity: 0.04;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
        }

        .terminal-card:hover {
            border-color: #56442F;
        }

        .terminal-card::before {
            background: linear-gradient(to bottom, var(--color-gold), var(--color-terracotta));
        }

        .terminal-card h2 {
            color: var(--color-gold);
            font-family: var(--font-display);
            font-weight: 500;
            letter-spacing: 0.04em;
        }

        .terminal-card h2::after {
            background: linear-gradient(to right, var(--color-gold), var(--color-terracotta));
        }

        .terminal-output {
            background: #110E09;
            border: 1px solid #2A2218;
            border-radius: 3px;
            padding: 1.1rem 1.25rem;
            font-family: "SF Mono", "Menlo", "Monaco", "Consolas", monospace;
            font-size: 0.82rem;
            line-height: 1.7;
            max-height: 400px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
            color: #A89880;
            margin-bottom: 0.75rem;
            position: relative;
            z-index: 1;
        }

        .terminal-output::-webkit-scrollbar {
            width: 5px;
        }

        .terminal-output::-webkit-scrollbar-track {
            background: #1A1510;
        }

        .terminal-output::-webkit-scrollbar-thumb {
            background: #3D3225;
            border-radius: 3px;
        }

        .terminal-output::-webkit-scrollbar-thumb:hover {
            background: #56442F;
        }

        .terminal-output .cmd-line {
            color: var(--color-gold);
        }

        .terminal-output .error-text {
            color: #C75B3A;
        }

        .terminal-input-row {
            display: flex;
            align-items: center;
            gap: 0;
            background: #110E09;
            border: 1px solid #2A2218;
            border-radius: 3px;
            overflow: hidden;
            transition: border-color var(--transition-base), box-shadow var(--transition-base);
            position: relative;
            z-index: 1;
        }

        .terminal-input-row:focus-within {
            border-color: var(--color-gold-muted);
            box-shadow: 0 0 0 3px rgba(199, 166, 107, 0.1);
        }

        .terminal-prompt {
            font-family: "SF Mono", "Menlo", "Monaco", "Consolas", monospace;
            font-size: 0.85rem;
            color: var(--color-gold);
            padding: 0.85rem 0 0.85rem 1.1rem;
            user-select: none;
            white-space: nowrap;
        }

        .terminal-input-row input {
            flex: 1;
            background: transparent;
            border: none;
            color: #D4C8B8;
            font-family: "SF Mono", "Menlo", "Monaco", "Consolas", monospace;
            font-size: 0.85rem;
            padding: 0.85rem 0.75rem 0.85rem 0.5rem;
            outline: none;
            margin: 0;
        }

        .terminal-input-row input::placeholder {
            color: #4A3D2E;
            font-style: italic;
        }

        .terminal-actions button.terminal-run-btn {
            background: linear-gradient(135deg, var(--color-gold) 0%, var(--color-gold-muted) 100%);
            color: #1A1510;
            border: none;
            font-weight: 600;
            box-shadow: 0 1px 4px rgba(199, 166, 107, 0.2);
        }

        .terminal-actions button.terminal-run-btn:hover {
            background: linear-gradient(135deg, #D4B578 0%, var(--color-gold) 100%);
            color: #1A1510;
            box-shadow: 0 2px 8px rgba(199, 166, 107, 0.3);
        }

        .terminal-actions button.terminal-run-btn:active {
            background: var(--color-gold-muted);
            box-shadow: none;
        }

        .terminal-actions {
            display: flex;
            gap: 0.5rem;
            margin-top: 0.75rem;
            position: relative;
            z-index: 1;
        }

        .terminal-actions button {
            font-family: var(--font-body);
            font-size: 0.75rem;
            padding: 0.45rem 1rem;
            margin: 0;
            background: #221C14;
            color: #8A7D6B;
            border: 1px solid #3D3225;
            border-radius: 3px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            transition: all var(--transition-base);
        }

        .terminal-actions button:hover {
            background: #2E261C;
            color: var(--color-gold);
            border-color: #56442F;
        }

        /* Responsive */
        @media (max-width: 640px) {
            .container {
                padding: 1.5rem 1rem;
            }

            h1 {
                font-size: 1.85rem;
            }

            .card {
                padding: 1.25rem;
            }

            button {
                width: 100%;
                margin-right: 0;
            }

            .terminal-actions button,
            .terminal-actions .terminal-run-btn {
                width: auto;
                flex: 1;
            }

            .quick-actions button {
                flex: 1;
                min-width: calc(50% - 0.25rem);
            }

            .status-row {
                flex-direction: column;
                align-items: flex-start;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Art Research Pipeline</h1>
        </header>

        <div class="card">
            <h2>Status</h2>
            <div class="status-row">
                <span id="status" class="status idle">Idle</span>
                <span id="job-info" class="job-info"></span>
            </div>
            <div id="progress" class="progress-bar" style="display:none;"></div>
            <div id="log">Awaiting your command...</div>
            <p class="meta">
                <span id="timing"></span>
            </p>
            <div class="quick-actions">
                <div class="quick-actions-label">Quick Actions</div>
                <button onclick="stopJob()" id="stop-btn" class="secondary" disabled>Stop Job</button>
                <button onclick="clearLog()" id="clear-btn" class="secondary">Clear Log</button>
                <button onclick="gitStatus()" id="git-status-btn" class="secondary">Git Status</button>
                <button onclick="hardReset()" id="reset-btn" class="danger">Hard Reset</button>
            </div>
        </div>

        <div class="card pipeline-card">
            <h2>Full Pipeline</h2>
            <input type="text" id="target" placeholder="Research target (optional, e.g., 'Galleria Borghese')">
            <button onclick="runPipeline()" id="pipeline-btn" class="primary">Run Full Pipeline</button>
            <div class="pipeline-steps">
                <span class="pipeline-step">Research</span>
                <span class="pipeline-step">Export</span>
                <span class="pipeline-step">Generate</span>
                <span class="pipeline-step">Publish</span>
                <span class="pipeline-step">Git Push</span>
            </div>
        </div>

        <div class="card">
            <h2>Run Claude Command</h2>
            <textarea id="prompt" placeholder="Enter any instruction for Claude..."></textarea>
            <button onclick="runCommand()" id="run-btn" class="primary">Run Command</button>
        </div>

        <div class="card terminal-card">
            <h2>Terminal</h2>
            <div id="terminal-output" class="terminal-output"></div>
            <div class="terminal-input-row">
                <span class="terminal-prompt">&rsaquo;</span>
                <input type="text" id="terminal-input" placeholder="enter command..." autocomplete="off" spellcheck="false">
            </div>
            <div class="terminal-actions">
                <button class="terminal-run-btn" onclick="runTerminal()">Run</button>
                <button onclick="clearTerminal()">Clear</button>
            </div>
        </div>

        <footer>
            <p>A digital atelier for Renaissance art scholarship</p>
        </footer>
    </div>

    <script>
        let refreshInterval;
        let currentInterval = 2000;
        let lastCompletedAt = null;
        let lastLogTotal = 0;
        let userCleared = false;

        async function fetchStatus() {
            try {
                const res = await fetch('/status');
                const data = await res.json();

                const statusEl = document.getElementById('status');
                const logEl = document.getElementById('log');
                const jobInfo = document.getElementById('job-info');
                const timing = document.getElementById('timing');
                const stopBtn = document.getElementById('stop-btn');
                const resetBtn = document.getElementById('reset-btn');
                const progressEl = document.getElementById('progress');

                if (data.running) {
                    statusEl.textContent = 'Running';
                    statusEl.className = 'status running';
                    jobInfo.textContent = `${data.type}: ${data.target}`;
                    document.getElementById('run-btn').disabled = true;
                    document.getElementById('pipeline-btn').disabled = true;
                    stopBtn.disabled = false;
                    resetBtn.disabled = true;
                } else {
                    statusEl.textContent = data.exit_code === 0 ? 'Completed' : (data.exit_code ? 'Error' : 'Idle');
                    statusEl.className = 'status ' + (data.exit_code === 0 ? 'idle' : (data.exit_code ? 'error' : 'idle'));
                    jobInfo.textContent = data.type ? `Last: ${data.type}` : '';
                    document.getElementById('run-btn').disabled = false;
                    document.getElementById('pipeline-btn').disabled = false;
                    stopBtn.disabled = true;
                    resetBtn.disabled = false;
                }

                // Adaptive polling: 1s when running, 3s when idle
                const newInterval = data.running ? 1000 : 3000;
                if (currentInterval !== newInterval) {
                    clearInterval(refreshInterval);
                    currentInterval = newInterval;
                    refreshInterval = setInterval(fetchStatus, currentInterval);
                }

                // Progress indicator
                if (data.running && data.progress) {
                    progressEl.textContent = data.progress;
                    progressEl.style.display = 'block';
                } else {
                    progressEl.style.display = 'none';
                }

                // Reset userCleared when a new job starts
                if (data.running) {
                    userCleared = false;
                }

                // Skip log updates if user cleared and job is idle
                if (!userCleared || data.running) {
                    // Incremental log updates
                    const newCompleted = data.completed_at || (data.running ? 'running' : null);
                    if (newCompleted !== lastCompletedAt) {
                        // Job state changed — full replace
                        lastCompletedAt = newCompleted;
                        lastLogTotal = 0;
                    }

                    if (data.log_total === 0) {
                        // No log lines yet
                    } else if (lastLogTotal === 0) {
                        // First load or reset — full replace
                        logEl.textContent = data.log.join('\\n');
                        logEl.scrollTop = logEl.scrollHeight;
                        lastLogTotal = data.log_total;
                    } else if (data.log_total > lastLogTotal) {
                        // Append only new lines
                        const newCount = data.log_total - lastLogTotal;
                        const newLines = data.log.slice(-newCount);
                        logEl.textContent += '\\n' + newLines.join('\\n');
                        logEl.scrollTop = logEl.scrollHeight;
                        lastLogTotal = data.log_total;
                    }
                }

                let timingText = '';
                if (data.started_at) {
                    timingText = `Started: ${new Date(data.started_at).toLocaleTimeString()}`;
                    if (data.completed_at) {
                        timingText += ` | Completed: ${new Date(data.completed_at).toLocaleTimeString()}`;
                    }
                }
                if (data.running && data.log_total) {
                    timingText += ` | ${data.log_total} lines`;
                }
                timing.textContent = timingText;

            } catch (e) {
                console.error('Failed to fetch status:', e);
            }
        }

        async function stopJob() {
            try {
                const res = await fetch('/stop', { method: 'POST' });
                const data = await res.json();
                if (data.error) {
                    alert(data.error);
                }
                fetchStatus();
            } catch (e) {
                alert('Failed to stop job: ' + e.message);
            }
        }

        async function gitStatus() {
            const logEl = document.getElementById('log');
            logEl.textContent = 'Fetching git status...';
            try {
                const res = await fetch('/git-status');
                const data = await res.json();
                let output = '';
                for (const [repo, status] of Object.entries(data)) {
                    output += `=== ${repo} ===\\n${status}\\n`;
                }
                logEl.textContent = output;
                lastCompletedAt = '__git_status__';
                lastLogTotal = 0;
            } catch (e) {
                logEl.textContent = 'Failed to fetch git status: ' + e.message;
            }
        }

        function clearLog() {
            document.getElementById('log').textContent = 'Awaiting your command...';
            document.getElementById('timing').textContent = '';
            document.getElementById('job-info').textContent = '';
            document.getElementById('progress').style.display = 'none';
            lastCompletedAt = '__cleared__';
            lastLogTotal = 0;
            userCleared = true;
        }

        async function hardReset() {
            if (!confirm('Hard reset both repos to HEAD? This will discard all uncommitted changes.')) {
                return;
            }
            const logEl = document.getElementById('log');
            logEl.textContent = 'Running git reset --hard HEAD...';
            try {
                const res = await fetch('/git-reset', { method: 'POST' });
                const data = await res.json();
                if (data.error) {
                    logEl.textContent = 'Error: ' + data.error;
                    return;
                }
                let output = '';
                for (const [repo, result] of Object.entries(data)) {
                    output += `=== ${repo} ===\\n${result}\\n`;
                }
                logEl.textContent = output;
                lastCompletedAt = '__git_reset__';
                lastLogTotal = 0;
            } catch (e) {
                logEl.textContent = 'Failed to reset: ' + e.message;
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

        // === Terminal ===
        const termHistory = [];
        let termHistoryIdx = -1;

        const termInput = document.getElementById('terminal-input');
        const termOutput = document.getElementById('terminal-output');

        termInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                runTerminal();
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                if (termHistory.length > 0) {
                    if (termHistoryIdx < termHistory.length - 1) termHistoryIdx++;
                    termInput.value = termHistory[termHistory.length - 1 - termHistoryIdx];
                }
            } else if (e.key === 'ArrowDown') {
                e.preventDefault();
                if (termHistoryIdx > 0) {
                    termHistoryIdx--;
                    termInput.value = termHistory[termHistory.length - 1 - termHistoryIdx];
                } else {
                    termHistoryIdx = -1;
                    termInput.value = '';
                }
            }
        });

        async function runTerminal() {
            const command = termInput.value.trim();
            if (!command) return;

            termHistory.push(command);
            termHistoryIdx = -1;
            termInput.value = '';

            // Show the command
            const cmdSpan = document.createElement('span');
            cmdSpan.className = 'cmd-line';
            cmdSpan.textContent = '$ ' + command + '\\n';
            termOutput.appendChild(cmdSpan);
            termOutput.scrollTop = termOutput.scrollHeight;

            try {
                const res = await fetch('/terminal', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ command })
                });
                const data = await res.json();

                if (data.output) {
                    const outSpan = document.createElement('span');
                    if (data.exit_code !== 0) {
                        outSpan.className = 'error-text';
                    }
                    outSpan.textContent = data.output;
                    termOutput.appendChild(outSpan);
                }
            } catch (e) {
                const errSpan = document.createElement('span');
                errSpan.className = 'error-text';
                errSpan.textContent = 'Failed to execute: ' + e.message + '\\n';
                termOutput.appendChild(errSpan);
            }

            termOutput.scrollTop = termOutput.scrollHeight;
        }

        function clearTerminal() {
            termOutput.textContent = '';
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

    thread = threading.Thread(target=run_claude, args=(prompt,), daemon=True)
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

    thread = threading.Thread(target=run_pipeline, args=(target,), daemon=True)
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
    thread = threading.Thread(target=run_claude, args=(prompt, "research"), daemon=True)
    thread.start()

    return jsonify({"status": "started", "target": target})


@app.route('/stop', methods=['POST'])
def stop_job():
    """Stop the currently running job"""
    global current_process
    with current_process_lock:
        if current_process is None or current_process.poll() is not None:
            return jsonify({"error": "No job is currently running"}), 409
        try:
            os.killpg(os.getpgid(current_process.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass
    current_job["_stop"] = True
    return jsonify({"status": "stopping"})


@app.route('/git-status', methods=['GET'])
def git_status():
    """Get git status for both repos"""
    results = {}
    for name, path in [("HistoryOfItalianRenaissanceArt", PROJECT_DIR),
                        ("jasonhojh1122.github.io", GITHUB_PAGES_DIR)]:
        try:
            result = subprocess.run(
                ["git", "status"], cwd=path, capture_output=True, text=True, timeout=10
            )
            results[name] = result.stdout + result.stderr
        except Exception as e:
            results[name] = f"Error: {str(e)}"
    return jsonify(results)


@app.route('/git-reset', methods=['POST'])
def git_reset():
    """Hard reset both repos to HEAD"""
    if current_job["running"]:
        return jsonify({"error": "Cannot reset while a job is running"}), 409

    results = {}
    for name, path in [("HistoryOfItalianRenaissanceArt", PROJECT_DIR),
                        ("jasonhojh1122.github.io", GITHUB_PAGES_DIR)]:
        try:
            result = subprocess.run(
                ["git", "reset", "--hard", "HEAD"],
                cwd=path, capture_output=True, text=True, timeout=10
            )
            results[name] = result.stdout + result.stderr
        except Exception as e:
            results[name] = f"Error: {str(e)}"
    return jsonify(results)


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
        "log": current_job["log"][-500:],
        "log_total": len(current_job["log"]),
        "progress": current_job.get("progress", "")
    })


@app.route('/terminal', methods=['POST'])
def terminal():
    """Execute a zsh command and return output"""
    data = request.get_json() or {}
    command = data.get('command', '').strip()
    if not command:
        return jsonify({"error": "command required"}), 400

    try:
        result = subprocess.run(
            ["/bin/zsh", "-c", command],
            capture_output=True, text=True,
            cwd=PROJECT_DIR,
            timeout=TERMINAL_TIMEOUT
        )
        return jsonify({
            "output": result.stdout + result.stderr,
            "exit_code": result.returncode
        })
    except subprocess.TimeoutExpired:
        return jsonify({
            "output": f"[Command timed out after {TERMINAL_TIMEOUT}s]",
            "exit_code": -1
        })
    except Exception as e:
        return jsonify({
            "output": f"[Error: {str(e)}]",
            "exit_code": -1
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
