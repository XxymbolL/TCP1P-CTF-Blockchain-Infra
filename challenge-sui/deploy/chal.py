import os
import json
import pickle
import subprocess
import tempfile
import sys
from uuid import uuid4
from pathlib import Path
from typing import Any, Optional

from ppow import Challenge, check as pow_check
from flask import Flask, request, jsonify, send_from_directory

class PersistentStore:
    def __init__(self, filename: str):
        self.filename = filename
    def get(self, key: str) -> Optional[Any]:
        try:
            with open(self.filename, "rb") as f:
                data = pickle.load(f)
                return data.get(key)
        except (FileNotFoundError, pickle.UnpicklingError):
            return None
    def set(self, key: str, value: Any) -> None:
        try:
            with open(self.filename, "rb") as f:
                data = pickle.load(f)
        except (FileNotFoundError, pickle.UnpicklingError):
            data = {}
        data[key] = value
        with open(self.filename, "wb") as f:
            pickle.dump(data, f)

app = Flask(__name__)
secret_key = os.urandom(32).hex()
app.secret_key = secret_key
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

FLAG = os.getenv("FLAG", "PCTF{placeholder}")
CHALLENGE_DIR = Path("/home/ctf/setup")
SOLVER_SCRIPT = Path("/home/ctf/solver/verify.py")
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
store = PersistentStore("/tmp/sui_state.pickle")

@app.route("/")
def index():
    return send_from_directory(str(FRONTEND_DIR), "index.html")

@app.route("/data")
def data():
    return jsonify({"uuid": request.cookies.get("session", "")})

@app.route("/challenge")
def challenge():
    return jsonify({
        "challenge_dir": str(CHALLENGE_DIR),
        "type": "sui",
        "description": "Upload your compiled solution .mv file to solve the challenge."
    })


@app.route("/solution", methods=["GET"])
def get_solution():
    chal = Challenge.generate(5)
    return {"challenge": str(chal)}

@app.route("/solution", methods=["POST"])
def solve_solution():
    data = request.get_json()
    if not data or "solution" not in data or "challenge" not in data:
        return {"error": "Missing solution or challenge"}, 400
    try:
        chal = Challenge.from_string(data["challenge"])
        if pow_check(chal, data["solution"]):
            ticket = os.urandom(16).hex()
            store.set(f"ticket_{ticket}", True)
            return {"ticket": ticket}
        return {"error": "Invalid solution"}, 400
    except Exception as e:
        return {"error": str(e)}, 400
@app.route("/launch", methods=["POST"])
def launch():
    ticket = request.headers.get("X-Ticket") or (request.get_json() or {}).get("ticket")
    if not ticket or not store.get(f"ticket_{ticket}"):
        return jsonify({"error": "Solve the PoW challenge first at /solution"}), 403
    store.set(f"ticket_{ticket}", None)
    session_id = str(uuid4())
    store.set(f"session_{session_id}", {"solved": False})
    return jsonify({
        "uuid": session_id,
        "message": "Instance created. Upload your solution .move file to /submit-solution/<uuid>",
        "challenge_address": "0x0",
    })

@app.route("/submit-solution/<uuid_str>", methods=["POST"])
def submit_solution(uuid_str):
    session = store.get(f"session_{uuid_str}")
    if session is None:
        return jsonify({"error": "Invalid session"}), 404

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file.filename.endswith(".move"):
        return jsonify({"error": "Please upload a .move source file"}), 400

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".move", mode="w")
    content = file.read().decode("utf-8")
    tmp.write(content)
    tmp.close()

    try:
        result = subprocess.run(
            [sys.executable, str(SOLVER_SCRIPT),
             "--challenge-dir", str(CHALLENGE_DIR),
             "--solution-file", tmp.name,
             "--flag", FLAG],
            capture_output=True, text=True, timeout=120
        )

        if result.returncode != 0:
            return jsonify({
                "solved": False,
                "stdout": result.stdout[:2000],
                "stderr": result.stderr[:2000],
            }), 400

        output = json.loads(result.stdout)
        if output.get("solved"):
            store.set(f"session_{uuid_str}", {"solved": True})
        return jsonify(output)
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Solution check timed out"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        os.unlink(tmp.name)

@app.route("/flag/<uuid_str>")
def flag(uuid_str):
    session = store.get(f"session_{uuid_str}")
    if session is None:
        return jsonify({"error": "Invalid session"}), 404
    if session.get("solved"):
        return jsonify({"flag": FLAG})
    return jsonify({"error": "Challenge not yet solved"}), 400

@app.route("/kill/<uuid_str>", methods=["POST"])
def kill(uuid_str):
    store.set(f"session_{uuid_str}", None)
    return jsonify({"message": "Instance killed"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("LAUNCHER_PORT", 8080)))
