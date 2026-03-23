import subprocess
import hmac
import hashlib
import os
from flask import Flask, request, jsonify

app = Flask(__name__)
SECRET = os.environ.get("WEBHOOK_SECRET", "aegis-webhook-2026")

@app.route("/webhook", methods=["POST"])
def webhook():
    sig = request.headers.get("X-Hub-Signature-256", "")
    body = request.data
    expected = "sha256=" + hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return jsonify({"error": "Unauthorized"}), 401
    subprocess.Popen(["/root/webhook/deploy.sh"])
    return jsonify({"status": "deploying"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000)
