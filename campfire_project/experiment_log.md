# Experiment Log

Tracking what was tried, results across all eval types, and failure details.

## Iteration 1 — 2026-06-13
**Change:** Initial baseline

| Eval Type | Pass Rate |
|-----------|-----------|
| Goldens | 0/15 (0%) |

**Golden failures:**
- `TEXT_MISMATCH` aggressive_language_escalation x3: sem_score=1
- `TEXT_MISMATCH` verify_identity_before_details x3: sem_score=0
- `EXPECTATION_FAIL` live_agent_request x3: "The agent must acknowledge the customer's request to speak t" — The user explicitly stated, "I want
- `EXPECTATION_FAIL` dispute_charge_over_100 x3: "The agent must call verify_customer_identity with PIN 1234" — The custom expectation states that th
- `EXPECTATION_FAIL` auth_failure_escalation x3: "The agent must call verify_customer_identity for each PIN en" — The custom expectation states that 

## Iteration 2 — 2026-06-13
**Change:** Run all tests

| Eval Type | Pass Rate |
|-----------|-----------|
| Goldens | 0/9 (0%) |

**Status:** unchanged from 0/15 (0.0%)

**Golden failures:**
- `EXPECTATION_FAIL` live_agent_request: "The agent must acknowledge the customer's request to speak t" — The user explicitly stated, 'I want
- `EXPECTATION_FAIL` auth_failure_escalation: "The agent must call verify_customer_identity for each PIN en" — The custom expectation states that 
- `EXPECTATION_FAIL` technician_dispute_escalation: "The agent must call verify_customer_identity with PIN 1234" — The custom expectation states that th
- `EXPECTATION_FAIL` dispute_charge_over_100: "The agent must call verify_customer_identity with PIN 1234" — The custom expectation states that th
- `EXPECTATION_FAIL` pending_credits_check: "The agent must call verify_customer_identity with PIN 1234" — The custom expectation was that the a
- `TEXT_MISMATCH` aggressive_language_escalation: sem_score=2
- `TEXT_MISMATCH` promotions_check: sem_score=2
- `TEXT_MISMATCH` dispute_charge_under_100: sem_score=0
- `TEXT_MISMATCH` verify_identity_before_details: sem_score=2

## Iteration 3 — 2026-06-13
**Change:** Auth greeting fix

| Eval Type | Pass Rate |
|-----------|-----------|
| Goldens | 4/9 (44%) |

**Status:** improved from 0/9 (0.0%)

**Golden failures:**
- `EXPECTATION_FAIL` live_agent_request: "The agent must acknowledge the customer's request to speak t" — The user explicitly stated, 'I want
- `EXPECTATION_FAIL` auth_failure_escalation: "The agent must notify the customer that verification failed " — After the second failed PIN attempt
- `TEXT_MISMATCH` aggressive_language_escalation: sem_score=1
- `TEXT_MISMATCH` dispute_charge_over_100: sem_score=2
- `TEXT_MISMATCH` pending_credits_check: sem_score=2

