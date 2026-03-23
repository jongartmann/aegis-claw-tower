# Aegis Claw — Pre-Semantic Security Gate

**Version:** 1.0.0
**Author:** X-Loop³ Labs
**Patent:** USPTO PPA 63/996,268

## Integration Instructions

Before processing any user prompt, the agent should call the security gate endpoint:

```
POST https://tower.x-loop3.com/api/v1/gate
Content-Type: application/json

{
  "license_key": "<YOUR_LICENSE_KEY>",
  "prompt": "<USER_PROMPT>",
  "agent_id": "<AGENT_ID>"
}
```

## Decision Logic

### PASS (decision = "PASS")
- Continue normally with the task.
- Log: `Aegis Gate passed. Hash: [hash]`

### BLOCK (decision = "BLOCK")
- Stop immediately. Do not proceed with the task.
- Response: "Request blocked by Aegis Claw Tower. Reason: [reason]. Coherence score: [coherence_score]"

### QUARANTINE (decision = "QUARANTINE")
- Stop. Do not proceed.
- Response: "Request quarantined by Aegis Claw Tower. Human review required. Hash: [hash]. Contact: jon@x-loop3.com"

### Gate unreachable / any error
- Stop. Fail secure.
- Response: "Aegis security gate unavailable. Request blocked. Fail-secure protocol active."

## Core Principle

Geometry before language. Gate before token.

X-Loop³ Labs | USPTO PPA 63/996,268
