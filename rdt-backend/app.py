import os
from flask import Flask, request, jsonify
from storage import (
    add_user,
    opt_out_week,
    opt_out_forever,
    get_user_by_token
)

try: # for local testing
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, assume env vars are set manually
app = Flask(__name__)

ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")


# ── Auth helper ────────────────────────────────────────────────────────────

def _check_admin(req):
    """Returns True if the request carries the correct admin token."""
    token = req.headers.get("X-Admin-Token")
    return token and token == ADMIN_TOKEN

# ── For local dev ────────────────────────────────────────────────────────────

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Admin-Token"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

# ── Public endpoints ───────────────────────────────────────────────────────

@app.route("/signup", methods=["POST"])
def signup():
    data = request.json or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()

    if not name:
        return jsonify({"error": "name required"}), 400
    if not email:
        return jsonify({"error": "email required"}), 400

    user = add_user(name, email)
    return jsonify({"status": "ok", "id": user["id"]}), 201


@app.route("/opt-out-week", methods=["POST"])
def opt_out_week_route():
    token = _get_token()
    if not token:
        return jsonify({"error": "token required"}), 400

    user = opt_out_week(token)
    if not user:
        return jsonify({"error": "user not found"}), 404

    return jsonify({"status": "opted out for this week", "name": user["name"]})


@app.route("/opt-out-forever", methods=["POST"])
def opt_out_forever_route():
    token = _get_token()
    if not token:
        return jsonify({"error": "token required"}), 400

    user = opt_out_forever(token)
    if not user:
        return jsonify({"error": "user not found"}), 404

    return jsonify({"status": "permanently opted out", "name": user["name"]})


@app.route("/me", methods=["GET"])
def me():
    """Used by the opt-out page to greet the user by name."""
    token = request.args.get("token", "").strip()
    if not token:
        return jsonify({"error": "token required"}), 400

    user = get_user_by_token(token)
    if not user:
        return jsonify({"error": "user not found"}), 404

    return jsonify({
        "name": user["name"],
        "status": user["status"]
    })


# ── Admin endpoints ────────────────────────────────────────────────────────

@app.route("/admin/redraw", methods=["POST"])
def admin_redraw():
    """
    Trigger a manual pairing redraw. Protected by admin token.
    Useful when someone opts out after pairs have already been sent.
    """
    if not _check_admin(request):
        return jsonify({"error": "unauthorized"}), 401

    # Import here to avoid circular issues if pairing imports storage
    from pairing import run_pairing

    result = run_pairing()
    return jsonify({"status": "redrawn", "pairs": result})


# ── Health check ───────────────────────────────────────────────────────────

@app.route("/health")
def health():
    return "ok"


# ── Token extraction helper ────────────────────────────────────────────────

def _get_token():
    """
    Pull token from JSON body or query string.
    Supports both POST with body and POST with ?token=... in URL.
    """
    if request.json:
        return request.json.get("token", "").strip()
    return request.args.get("token", "").strip()


if __name__ == "__main__":
    app.run(debug=True)