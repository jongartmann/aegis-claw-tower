"""
AEGIS CLAW TOWER v1.0
Pre-Semantic Security Gate for OpenClaw Agents
X-Loop³ Labs | jon@x-loop3.com
USPTO PPA 63/996,268
"""

import os
import hashlib
import re
import time
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

LICENSES = {
    os.environ.get("LICENSE_KEY_DEV", "XLOOP3-CLAW-DEV-00001"): {
        "name": "Developer",
        "features": ["gate", "tower"],
        "tier": "developer",
        "rate_limit": 99999,
        "active": True,
        "expires": "2027-12-31"
    }
}

RATE_COUNTERS = {}

INJECTION_PATTERNS = [
    # === INSTRUCTION OVERRIDE (EN) ===
    r"ignore\s+(all\s+)?(previous|prior|above|your)\s+instructions?",
    r"disregard\s+(all\s+)?(previous|prior|above|your)\s+(instructions?|guidelines?|rules?|safety)",
    r"forget\s+(everything|all)\s+(you|i)\s+(know|said|told)",
    r"override\s+(your|all|the)\s+(instructions?|rules?|guidelines?|programming)",
    r"new\s+instructions?\s*[:\-]",
    # === INSTRUCTION OVERRIDE (DE) ===
    r"ignorier(e|en?)\s+(alle\s+)?(vorherigen?|bisherigen?|obigen?)\s+(Anweisungen?|Instruktionen?|Regeln?)",
    r"vergiss\s+(alles|alle)\s+(was|die)",
    r"(zeig|offenbar)e?\s+(mir\s+)?(dein|das|den)\s+(System|Prompt|Instruktionen?)",
    r"missacht(e|en?)\s+(alle\s+)?(Sicherheit|Regeln?|Richtlinien?)",
    r"du\s+bist\s+(jetzt|nun|ab\s+sofort)\s+(ein|eine?)",
    # === INSTRUCTION OVERRIDE (FR/ES) ===
    r"ignor(e|a|ez)\s+(toutes?\s+)?(les\s+)?instructions?\s+(pr[ée]c[ée]dentes?|ant[ée]rieures?)",
    r"ignora\s+(todas?\s+)?(las\s+)?instrucciones?\s+(previas?|anteriores?)",
    r"olvida\s+(todo|todas?)\s+(lo|las?)\s+que",
    # === ROLE HIJACK / JAILBREAK ===
    r"you\s+are\s+now\s+(?!going\s+to\s+help)(\w+)",
    r"pretend\s+(you\s+are|to\s+be)\s+an?\s+",
    r"act\s+as\s+(if\s+)?(you\s+are\s+)?(DAN|STAN|AIM|evil|uncensored|unrestricted|unfiltered|jailbroken)",
    r"\b(DAN|STAN|AIM)\s*(mode|prompt|jailbreak)",
    r"(new|different|special)\s+role\s*[:\-]",
    r"(disregard|ignore|bypass|disable)\s+(safety|content|output)\s*(filter|guidelines?|rules?|restrictions?|policy)",
    r"without\s+(any\s+)?(restrictions?|limits?|rules?|guidelines?|filters?|safety)",
    r"no\s+(restrictions?|limits?|rules?|guidelines?|filters?|censorship)",
    r"in\s+this\s+(new\s+)?(role|mode|persona)",
    # === DATA EXFILTRATION ===
    r"send\s+.{0,40}(data|files?|credentials?|keys?|secrets?|passwords?|tokens?|info|information)\s+(to|at|via)",
    r"(forward|transmit|upload|post|exfiltrate?|leak|expose|share)\s+.{0,40}(data|keys?|secrets?|credentials?|tokens?|passwords?)",
    r"https?://(?!tower\.x-loop3\.com|claw\.x-loop3\.com|x-loop3\.com)[^\s]+\.(com|net|org|io)\S*",
    r"(webhook|ngrok|requestbin|pipedream|hookbin|burp|evil|attacker)",
    r"(curl|wget|fetch|http)\s+.{0,60}(api[_-]?key|secret|token|password|credential)",
    # === SYSTEM PROMPT EXTRACTION ===
    r"(show|display|print|reveal|output|repeat|echo)\s+(me\s+)?(your|the|this)\s+(system|initial|original|hidden|secret)\s+(prompt|instructions?|message|context|rules?)",
    r"what\s+(are|is|were?)\s+your\s+(system|initial|original|hidden|secret)\s+(prompt|instructions?|rules?)",
    r"(beginning|start|first)\s+(of\s+)?(the\s+)?(conversation|context|prompt|message)",
    # === CODE INJECTION ===
    r"\[SYSTEM\]|\[INST\]|\[PROMPT\]|\[OVERRIDE\]|\[ADMIN\]",
    r"<\|?(system|im_start|im_end|endoftext)\|?>",
    r"eval\s*\(|exec\s*\(",
    r"subprocess|os\.system|os\.popen",
    r"__import__\s*\(",
    r"import\s+(subprocess|shutil|socket|requests)",
    # === OBFUSCATION ===
    r"(?i)b(?:4|a)s(?:e|3)\s*6\s*4",
    r"(?:i|1|l)(?:g|9)n(?:o|0)r(?:e|3)",
    r"rot13|caesar\s*cipher|decode\s+this",
    r"unicode.*bypass|homoglyph",
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in INJECTION_PATTERNS]

def compute_coherence_score(prompt):
    if not prompt or len(prompt.strip()) < 3:
        return 0.1
    signals = 0
    if 10 <= len(prompt) <= 5000:
        signals += 1
    ratio = sum(1 for c in prompt if c.isalpha()) / max(len(prompt), 1)
    if ratio > 0.5:
        signals += 1
    words = prompt.lower().split()
    if len(words) > 0 and len(set(words)) / len(words) > 0.3:
        signals += 1
    if prompt.count('\n') + prompt.count('\t') < 10:
        signals += 1
    if not re.search(r'[A-Za-z0-9+/]{50,}={0,2}', prompt):
        signals += 1
    coherence_words = r"\b(please|help|can you|what|how|create|build|write|analyze)\b"
    if re.search(coherence_words, prompt, re.IGNORECASE):
        signals += 1
    return round(signals / 6, 3)

def detect_injection(prompt):
    for i, pattern in enumerate(COMPILED_PATTERNS):
        match = pattern.search(prompt)
        if match:
            return True, f"Pattern #{i+1}: '{match.group(0)[:50]}'"
    return False, ""

def compute_hash(prompt, license_key, timestamp):
    content = f"{license_key}:{timestamp}:{prompt[:100]}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]

def check_rate_limit(license_key, limit):
    now = time.time()
    minute = int(now // 60)
    if license_key not in RATE_COUNTERS:
        RATE_COUNTERS[license_key] = {}
    RATE_COUNTERS[license_key] = {k: v for k, v in RATE_COUNTERS[license_key].items() if k >= minute - 1}
    current = RATE_COUNTERS[license_key].get(minute, 0)
    if current >= limit // 60 + 1:
        return False
    RATE_COUNTERS[license_key][minute] = current + 1
    return True

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "service": "Aegis Claw Tower",
        "version": "1.0.0",
        "patent": "USPTO PPA 63/996,268",
        "tagline": "Geometry before language. Gate before token."
    })

@app.route("/api/v1/health", methods=["GET"])
def health():
    return jsonify({"status": "operational", "timestamp": datetime.now(timezone.utc).isoformat()})

@app.route("/api/v1/gate", methods=["POST"])
def gate():
    data = request.json or {}
    license_key = data.get("license_key", "")
    prompt = data.get("prompt", "")
    agent_id = data.get("agent_id", "unknown")
    timestamp = time.time()

    if not license_key or license_key not in LICENSES:
        return jsonify({"decision": "BLOCK", "reason": "Invalid license key", "code": "INVALID_LICENSE"}), 403

    license_data = LICENSES[license_key]
    if not license_data.get("active"):
        return jsonify({"decision": "BLOCK", "reason": "License suspended", "code": "LICENSE_SUSPENDED"}), 403

    if not prompt:
        return jsonify({"decision": "BLOCK", "reason": "Empty prompt", "code": "EMPTY_PROMPT"}), 400

    if len(prompt) > 50000:
        return jsonify({"decision": "BLOCK", "reason": "Prompt too large", "code": "OVERSIZED"}), 400

    if not check_rate_limit(license_key, license_data.get("rate_limit", 100)):
        return jsonify({"decision": "BLOCK", "reason": "Rate limit exceeded", "code": "RATE_LIMIT"}), 429

    coherence_score = compute_coherence_score(prompt)
    is_injection, injection_detail = detect_injection(prompt)
    state_hash = compute_hash(prompt, license_key, timestamp)

    if is_injection:
        return jsonify({"decision": "BLOCK", "reason": f"Injection detected: {injection_detail}", "code": "INJECTION_DETECTED", "coherence_score": coherence_score, "hash": state_hash})

    if coherence_score < 0.25:
        return jsonify({"decision": "QUARANTINE", "reason": f"Low coherence ({coherence_score})", "code": "LOW_COHERENCE", "coherence_score": coherence_score, "hash": state_hash})

    return jsonify({"decision": "PASS", "reason": "Pre-semantic check passed", "code": "PASS_CLEAN", "coherence_score": coherence_score, "hash": state_hash, "agent_id": agent_id, "timestamp": timestamp})

@app.route("/api/v1/license", methods=["POST"])
def validate_license():
    data = request.json or {}
    key = data.get("license_key", "")
    if key not in LICENSES:
        return jsonify({"valid": False}), 403
    l = LICENSES[key]
    if not l.get("active"):
        return jsonify({"valid": False, "error": "Suspended"}), 403
    return jsonify({"valid": True, "tier": l["tier"], "features": l["features"]})

@app.route("/api/v1/kill", methods=["POST"])
def kill_switch():
    data = request.json or {}
    if data.get("admin_key") != os.environ.get("ADMIN_KEY", ""):
        return jsonify({"error": "Unauthorized"}), 401
    key = data.get("license_key", "")
    if key in LICENSES:
        LICENSES[key]["active"] = False
        return jsonify({"success": True})
    return jsonify({"error": "Not found"}), 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
