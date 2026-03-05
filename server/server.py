"""
server.py — Avalon Task Tracker Pi Server
==========================================
Flask server running on the Raspberry Pi.
  • Receives button presses from ESPHome devices
  • Serves current state to the e-ink display
  • Sends a single daily 9:30 AM Signal summary to the Favalon group
  • Resets state at 3:00 AM

Configuration — edit the TODO lines below, or set env vars.
"""

import json
import logging
import os
import time
from datetime import datetime, date
from pathlib import Path

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify, request

# ── Configuration ─────────────────────────────────────────────────────────────

# TODO: set EC2_RELAY_URL to your EC2 instance's Signal relay endpoint
EC2_RELAY_URL = os.environ.get("EC2_RELAY_URL", "http://13.58.219.0:8766/send-signal")

# TODO: set RELAY_TOKEN to your shared secret (must match signal_relay.py)
RELAY_TOKEN = os.environ.get("RELAY_TOKEN", "CHANGE_ME_shared_secret")

# State file location — directory must exist (created below if missing)
STATE_FILE = Path(os.environ.get("STATE_FILE", "/var/lib/task-tracker/state.json"))

# Active window: button presses only accepted 6:00 AM – 9:30 AM
WINDOW_START = (6, 0)    # (hour, minute)
WINDOW_END   = (9, 30)

# ── Task definitions ──────────────────────────────────────────────────────────

# Tasks that apply every day
DAILY_TASKS = {
    "ryker": ["laundry", "teeth", "plates", "pills"],
    "logan": ["laundry", "teeth", "plates"],
}

# Tasks that apply on Wednesdays only (weekday index 2)
WEDNESDAY_TASKS = {
    "ryker": ["flute"],
    "logan": ["trumpet"],
}

VALID_OWNERS = list(DAILY_TASKS.keys())


def tasks_for_today(owner: str) -> list[str]:
    """Return the list of applicable task names for the given owner today."""
    tasks = list(DAILY_TASKS.get(owner, []))
    if datetime.now().weekday() == 2:  # Wednesday
        tasks += WEDNESDAY_TASKS.get(owner, [])
    return tasks


def wednesday_tasks_today() -> dict[str, list[str]]:
    """Return Wednesday-only tasks per owner if today is Wednesday, else empty lists."""
    if datetime.now().weekday() == 2:
        return {owner: list(t) for owner, t in WEDNESDAY_TASKS.items()}
    return {owner: [] for owner in VALID_OWNERS}


# ── State helpers ─────────────────────────────────────────────────────────────

def _empty_state() -> dict:
    """Return a fresh, zeroed-out state for today."""
    wednesday = wednesday_tasks_today()
    return {
        "date": date.today().isoformat(),
        "tasks": {
            owner: {task: False for task in tasks_for_today(owner)}
            for owner in VALID_OWNERS
        },
        # Track which Wednesday-only tasks are applicable today
        "wednesday_today": {
            owner: wednesday.get(owner, [])
            for owner in VALID_OWNERS
        },
        # Whether the 9:30 AM summary has been sent today
        "summary_sent": False,
    }


def load_state() -> dict:
    """Load state from disk; reset if missing, corrupt, or from a prior day."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        raw = STATE_FILE.read_text()
        state = json.loads(raw)
        if state.get("date") != date.today().isoformat():
            logging.info("State is from a prior day — resetting.")
            return _empty_state()
        return state
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        logging.info("No valid state file found — starting fresh.")
        return _empty_state()


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def is_done(state: dict, owner: str) -> bool:
    """True if all of today's tasks are complete for this owner."""
    return all(state["tasks"][owner].values())


def is_active_window() -> bool:
    now = datetime.now()
    start = now.replace(hour=WINDOW_START[0], minute=WINDOW_START[1], second=0, microsecond=0)
    end   = now.replace(hour=WINDOW_END[0],   minute=WINDOW_END[1],   second=0, microsecond=0)
    return start <= now <= end


# ── Signal relay ──────────────────────────────────────────────────────────────

def send_signal(message: str) -> None:
    """POST a message to the EC2 Signal relay. Logs errors but never raises."""
    try:
        resp = requests.post(
            EC2_RELAY_URL,
            json={"message": message},
            headers={"X-Relay-Token": RELAY_TOKEN},
            timeout=10,
        )
        resp.raise_for_status()
        logging.info("Signal sent: %s", message)
    except Exception as exc:
        logging.error("Failed to send Signal message: %s", exc)


# ── Scheduled jobs ────────────────────────────────────────────────────────────

def job_reset() -> None:
    """3:00 AM — wipe state for the new day."""
    logging.info("3 AM reset triggered.")
    new_state = _empty_state()
    save_state(new_state)
    app.config["state"] = new_state


def job_morning_summary() -> None:
    """
    9:30 AM — send a single Signal summary for both kids.

    Format examples:
      ✅ Ryker done | ✅ Logan done
      ✅ Ryker done | ⚠️ Logan missed: teeth, plates
      ⚠️ Ryker missed: pills | ⚠️ Logan missed: teeth, plates
    """
    state = app.config["state"]

    if state.get("summary_sent"):
        logging.info("9:30 AM summary already sent today — skipping.")
        return

    parts = []
    for owner in VALID_OWNERS:
        tasks = state["tasks"].get(owner, {})
        if all(tasks.values()):
            parts.append(f"✅ {owner.capitalize()} done")
        else:
            missed = [t for t, done in tasks.items() if not done]
            missed_str = ", ".join(missed)
            parts.append(f"⚠️ {owner.capitalize()} missed: {missed_str}")

    message = " | ".join(parts)
    send_signal(message)

    state["summary_sent"] = True
    save_state(state)
    logging.info("9:30 AM summary sent.")


# ── Flask app ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

app = Flask(__name__)

# Load state on startup
app.config["state"] = load_state()
logging.info("Loaded state for %s", app.config["state"]["date"])


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "date": app.config["state"]["date"]})


@app.route("/press", methods=["POST"])
def press():
    """
    Record a task completion.

    Body: {"owner": "ryker", "task": "laundry"}

    Returns:
      {"status": "ok"}             — recorded
      {"status": "already_done"}   — was already marked complete
      {"status": "outside_window"} — outside 6:00–9:30 AM
      {"status": "not_today"}      — Wednesday-only task on a non-Wednesday
      {"status": "invalid"}        — bad owner/task
    """
    body = request.get_json(silent=True) or {}
    owner = (body.get("owner") or "").lower().strip()
    task  = (body.get("task")  or "").lower().strip()

    if owner not in VALID_OWNERS:
        return jsonify({"status": "invalid", "reason": "unknown owner"}), 400

    # Check active window first
    if not is_active_window():
        return jsonify({"status": "outside_window"})

    state = app.config["state"]
    today_tasks = state["tasks"].get(owner, {})

    if task not in today_tasks:
        # Task not in today's roster — Wednesday-only task on wrong day?
        all_possible = DAILY_TASKS.get(owner, []) + WEDNESDAY_TASKS.get(owner, [])
        if task in all_possible:
            return jsonify({"status": "not_today"})
        return jsonify({"status": "invalid", "reason": "unknown task"}), 400

    if today_tasks[task]:
        return jsonify({"status": "already_done"})

    # Record completion
    state["tasks"][owner][task] = True
    save_state(state)
    logging.info("Recorded: %s / %s", owner, task)

    return jsonify({"status": "ok"})


@app.route("/state", methods=["GET"])
def get_state():
    """
    Return current task state for the e-ink display.

    The display polls this every 5 seconds and renders from flat booleans
    to avoid any JSON nesting logic in ESPHome C++ lambdas.
    """
    state = app.config["state"]
    tasks = state["tasks"]
    wed   = state.get("wednesday_today", {})

    flat = {
        "active_window": is_active_window(),
        "both_done":     all(is_done(state, o) for o in VALID_OWNERS),

        # Ryker
        "ryker_laundry":     tasks.get("ryker", {}).get("laundry", False),
        "ryker_teeth":       tasks.get("ryker", {}).get("teeth",   False),
        "ryker_plates":      tasks.get("ryker", {}).get("plates",  False),
        "ryker_pills":       tasks.get("ryker", {}).get("pills",   False),
        "ryker_flute":       tasks.get("ryker", {}).get("flute",   False),
        "ryker_flute_today": "flute" in tasks.get("ryker", {}),
        "ryker_done":        is_done(state, "ryker"),

        # Logan
        "logan_laundry":      tasks.get("logan", {}).get("laundry",  False),
        "logan_teeth":        tasks.get("logan", {}).get("teeth",    False),
        "logan_plates":       tasks.get("logan", {}).get("plates",   False),
        "logan_trumpet":      tasks.get("logan", {}).get("trumpet",  False),
        "logan_trumpet_today": "trumpet" in tasks.get("logan", {}),
        "logan_done":         is_done(state, "logan"),
    }
    return jsonify(flat)


# ── Scheduler setup ───────────────────────────────────────────────────────────

scheduler = BackgroundScheduler(timezone="America/Los_Angeles")
scheduler.add_job(job_reset,           "cron", hour=3,  minute=0, id="reset")
scheduler.add_job(job_morning_summary, "cron", hour=9,  minute=30, id="summary")
scheduler.start()
logging.info("Scheduler started (reset @ 3:00 AM, summary @ 9:30 AM Pacific).")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8765, debug=False)
