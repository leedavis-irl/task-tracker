"""
signal_relay.py — EC2 Signal Relay Endpoint
============================================
Small Flask app that accepts a message from the Pi and sends it via
signal-cli to the Favalon group.

Run standalone:
  pip install flask
  RELAY_TOKEN=your_secret python signal_relay.py

Or integrate into the existing household-agent on EC2 by importing
and registering the blueprint (see bottom of file).

Port: 8766
Auth: X-Relay-Token header (shared secret)
"""

import logging
import os
import subprocess

from flask import Flask, jsonify, request, Blueprint

# ── Configuration ─────────────────────────────────────────────────────────────

# TODO: set RELAY_TOKEN env var on EC2 to your chosen shared secret.
# Must match RELAY_TOKEN in task-tracker.service on the Pi.
RELAY_TOKEN = os.environ.get("RELAY_TOKEN", "CHANGE_ME_shared_secret")

# Signal account sending messages
SIGNAL_ACCOUNT = "+17074748930"

# Favalon Signal group ID
SIGNAL_GROUP_ID = "B0rtgi79BwsuD2OEFO6CxnVhGG4lHNyEzFWFClsas/4="

# signal-cli binary path
SIGNAL_CLI = os.environ.get("SIGNAL_CLI", "/usr/local/bin/signal-cli")

# ── Blueprint (reusable if integrated into household-agent) ───────────────────

relay_bp = Blueprint("signal_relay", __name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def _check_token() -> bool:
    token = request.headers.get("X-Relay-Token", "")
    return token == RELAY_TOKEN


@relay_bp.route("/send-signal", methods=["POST"])
def send_signal():
    """
    POST /send-signal
    Headers: X-Relay-Token: <secret>
    Body:    {"message": "your message here"}

    Sends the message to the Favalon Signal group via signal-cli.
    Returns {"status": "sent"} or an error JSON with HTTP 4xx/5xx.
    """
    if not _check_token():
        logging.warning("Rejected /send-signal: bad or missing token.")
        return jsonify({"status": "error", "reason": "unauthorized"}), 401

    body = request.get_json(silent=True) or {}
    message = (body.get("message") or "").strip()

    if not message:
        return jsonify({"status": "error", "reason": "empty message"}), 400

    try:
        cmd = [
            SIGNAL_CLI,
            "-a", SIGNAL_ACCOUNT,
            "send",
            "-g", SIGNAL_GROUP_ID,
            "-m", message,
        ]
        logging.info("Sending Signal message: %s", message)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            logging.error("signal-cli error: %s", result.stderr)
            return jsonify({
                "status": "error",
                "reason": "signal-cli failed",
                "detail": result.stderr.strip(),
            }), 500

        logging.info("Signal message sent successfully.")
        return jsonify({"status": "sent"})

    except FileNotFoundError:
        logging.error("signal-cli not found at %s", SIGNAL_CLI)
        return jsonify({"status": "error", "reason": "signal-cli not found"}), 500
    except subprocess.TimeoutExpired:
        logging.error("signal-cli timed out.")
        return jsonify({"status": "error", "reason": "timeout"}), 500
    except Exception as exc:
        logging.error("Unexpected error: %s", exc)
        return jsonify({"status": "error", "reason": str(exc)}), 500


# ── Standalone app ────────────────────────────────────────────────────────────

app = Flask(__name__)
app.register_blueprint(relay_bp)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    # Standalone mode — run directly on EC2
    # sudo ufw allow 8766/tcp  (if not already open)
    app.run(host="0.0.0.0", port=8766, debug=False)

# ── Integration note ──────────────────────────────────────────────────────────
# To integrate into the existing household-agent Flask app instead of running
# standalone, add to household-agent's main app file:
#
#   from signal_relay import relay_bp
#   app.register_blueprint(relay_bp)
#
# Then signal_relay.py does NOT need to run as its own process.
