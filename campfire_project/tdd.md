# Technical Design Document (TDD)

> This is a **living document** -- update it whenever requirements, agent behavior, or evals change.
> Update the TDD first, then update evals to match.

## Agent Design

### Architecture
- **Root Agent (`root_agent`)**: Responsible for initial greeting, user intent classification, identity verification (authentication via a 4-digit PIN), answering general inquiries via the Universal FAQ knowledge base, and handling direct escalations.
- **Billing Inquiries Agent (`billing_agent`)**: Dedicated to resolving bill confusion, explaining line item charges (such as late fees or prorated charges), providing product-level charge details, checking current/expired promotions, and verifying pending credits.
- **Dispute Agent (`dispute_agent`)**: Dedicated to checking charge dispute eligibility and submitting disputes. Handles disputes under $100 automatically or routes disputes over $100 and specialized technician-visit disputes to Tier 2 support.
- **Modality**: Primarily voice-capable text conversations. Prompts and tone/style should support natural spoken patterns, enunciation, and standard US English accent.
- **Model**: standard CXAS model (Gemini 1.5 Flash or Gemini 2.0 Flash).

### Tools
| Tool Name | Type | Purpose | Source / Requirement |
|-----------|------|---------|----------------------|
| `verify_customer_identity` | Python function | Prompts and verifies the customer's 4-digit PIN before showing account details. | PRD Section 1: Identity verification rule |
| `set_session_state` | Python function | Writes temporary state variables and action triggers (e.g. `_action_trigger`) in session context. | GECX Best Practice (Trigger Pattern) |
| `get_bill_variance` | API connector | Compares current month bill with previous month at account/service level. | PRD Section 3: Variance API |
| `get_billing_fees` | API connector | Retrieves details for specific charges, fees, proration, and complex billing logic. | PRD Section 3: Confusion & ConfusionFees APIs |
| `get_active_and_promotions` | API connector | Retrieves promotions applied to the account and promotional eligibility. | PRD Section 3: ActiveAndPromotion API |
| `get_pending_credits` | API connector | Checks for any pending adjustments or credits not yet applied to the balance. | PRD Section 3: PendingCredit API |
| `check_dispute_eligibility` | API connector | Validates if a particular bill charge is eligible for dispute. | PRD Section 3: DisputeType API |
| `submit_charge_dispute` | API connector | Submits the dispute for an eligible bill charge. | PRD Section 3: DisputeSubmitCharge API |
| `escalate_to_live_agent` | System tool | Instantly routes the conversation to a standard live human agent. | PRD Section 3: Escalation rules |
| `escalate_to_tier_2` | System tool | Transfers the call to the specialized "Billing Support - Tier 2" queue. | PRD Section 3: Escalation rules |
| `search_universal_faq` | Knowledge base | Queries general policies regarding billing cycles, payment methods, and standard fees. | PRD Section 4: Universal FAQ |
| `search_fee_rules` | Knowledge base | Queries standard limits for late fees, restoral fees, and equipment charges. | PRD Section 4: Fee Rule Tables |
| `search_promotion_guidelines` | Knowledge base | Queries terms and conditions for marketing campaigns and retention offers. | PRD Section 4: Promotion Guidelines |

### Routing Logic
- **Identity Verification Gate**:
  - The `root_agent` must verify the customer's identity by prompting them for their 4-digit PIN before routing to billing/dispute sub-agents or discussing account specific billing/credits details.
  - If customer fails identity verification twice, `root_agent` escalates to Live Agent immediately.
- **Sub-Agent Transfers**:
  - Once authenticated:
    - Route inquiries about bill increases, fees, promotions, or pending credits to `billing_agent`.
    - Route dispute-related inquiries to `dispute_agent`.
- **Escalation Routing**:
  - If user explicitly requests a human representative or uses aggressive language, route to Live Agent immediately.
  - If a dispute is over $100 and cannot be automatically resolved, route to "Billing Support - Tier 2".
  - If a dispute involves a technician visit, initiate the dispute details and transfer to "Billing Support - Tier 2" (Example 2).

### Variables
| Variable | Source | Notes |
|----------|--------|-------|
| `account_id` | Session parameter | Provided by calling platform |
| `customer_id` | Session parameter | Provided by calling platform |
| `customer_profile` | Derived in `before_agent_callback` | JSON containing name, plan_details, active_promotions, billing_cycle, auth_status (`NOT_STARTED`, `AUTHENTICATED`, `FAILED_ONCE`, `FAILED_TWICE`), and metadata. NEVER override in evals. |
| `billing_context` | Set by LLM / Tool calls | JSON storing bill variance, fees, and expired promo findings. |
| `dispute_context` | Set by LLM / Tool calls | JSON storing disputed charge ID, amount, eligibility status, and dispute submission ID. |
| `_action_trigger` | Set by LLM via state-setting tool | Flag used to intercept state transitions (e.g. `TRIGGER_TRANSFER_TIER_2`, `TRIGGER_TRANSFER_LIVE_AGENT`) in callback. Read/cleared by `before_model_callback`. |

### Callbacks
| Callback | Agent | Purpose |
|----------|-------|---------|
| `before_agent` | `root_agent` | Extracts session params (`account_id`, `customer_id`), fetches customer data to initialize `customer_profile` (storing name, plan_details, active_promotions, billing_cycle, etc.), and sets `auth_status = "NOT_STARTED"`. |
| `before_model` | All Agents | Intercepts `_action_trigger` values to execute deterministic routing and tool calling (Trigger Pattern), avoiding LLM-level transfer hallucinations. |
| `after_model` | All Agents | Injects a warm handoff message (e.g. "I'll transfer you now...") immediately prior to an escalation/transfer tool execution. |

---

## Eval Design

### Coverage Map
| Requirement | Eval Type | Rationale | Priority | Severity | Tags |
|-------------|-----------|-----------|----------|----------|------|
| **Verify Identity Before Details** | Golden | Security requirement: verification is mandatory before discussing any bill/credit details. | P0 | NO-GO | `security, auth` |
| **Authentication Failure Escalation** | Golden | Escalation logic: exactly 2 verification failures triggers immediate Live Agent transfer. | P0 | NO-GO | `security, auth, escalation` |
| **Bill Variance Happy Path** | Sim | Explaining month-over-month variances (late fee, expired promo) has high dialogue variability. | P1 | HIGH | `billing, variance` |
| **Promotions Check** | Golden | Verifying active/expired promotions via ActiveAndPromotion API is a linear, predictable query flow. | P1 | MEDIUM | `promotions` |
| **Pending Credits Check** | Golden | Checking for unapplied credits via PendingCredit API is a direct query flow. | P1 | MEDIUM | `credits` |
| **Dispute Charge < $100** | Golden | Submitting an eligible dispute under $100 follows a deterministic API tool path. | P1 | HIGH | `disputes` |
| **Dispute Charge > $100** | Golden | Verification that disputes over $100 are escalated to Tier 2 Billing Support. | P0 | HIGH | `disputes, escalation` |
| **Technician Dispute Escalation** | Golden | Special routing: disputes involving technician visits must initiate dispute and route to Tier 2. | P1 | HIGH | `disputes, escalation` |
| **Live Agent Request** | Golden | Standard routing: immediate transfer when customer requests a human agent. | P0 | HIGH | `escalation` |
| **Aggressive Language Escalation** | Golden | Immediate transfer when customer exhibits aggressive language. | P0 | HIGH | `escalation, safety` |
| **Universal FAQ Search** | Sim | General policy and payment method inquiries rely on FAQ KBs, yielding natural phrasing. | P2 | MEDIUM | `faq` |

### Golden vs Sim Decision
- **Use goldens** for authentication flow, auth failure handling, disputes escalation (amount threshold and technician-visit checks), and immediate human agent requests, as these require strict tool calling sequences and precise state outcomes.
- **Use sims** for bill variance analysis and general FAQ answers, as these involve synthetic reasoning, month-over-month comparisons, and variable user questions mapping to static FAQs.

### Test Data (Customer Profiles)
<!-- TODO: Populate with real customer profile data once mock data sources are provided -->
| Profile | account_id | customer_id | Scenario | Expected Flow |
|---------|------------|-------------|----------|---------------|
| `profile_auth_success` | `1234567890` | `987654321` | Active billing customer, valid 4-digit PIN (1234) | Authenticated flow, allows billing info access |
| `profile_auth_fail` | `0000000000` | `000000000` | Invalid 4-digit PIN (fails twice) | Prompts 2x, then escalates to Live Agent |
| `profile_dispute_over_100`| `999888777` | `888777666` | Customer with bill charge of $150 to dispute, valid 4-digit PIN (1234) | Starts dispute, escalates to Tier 2 |

---

## Build Steps

1. Define variables and session parameters (`account_id`, `customer_id`, `customer_profile`, `billing_context`, `dispute_context`, `_action_trigger`).
2. Implement python tools (`verify_customer_identity`, `set_session_state`).
3. Define API connector tools (`get_bill_variance`, `get_billing_fees`, `get_active_and_promotions`, `get_pending_credits`, `check_dispute_eligibility`, `submit_charge_dispute`).
4. Implement system tools (`escalate_to_live_agent`, `escalate_to_tier_2`).
5. Configure knowledge bases and search tools (`search_universal_faq`, `search_fee_rules`, `search_promotion_guidelines`).
6. Create agents (`root_agent`, `billing_agent`, `dispute_agent`) and write XML-formatted instructions.
7. Implement callbacks (`before_agent`, `before_model`, `after_model`).
8. Create golden evaluation tests.
9. Create simulation evaluation tests.
10. Run linter and verify zero errors/warnings.
11. Run evaluation suite and iterate on instructions/callbacks.

---

## Pass Rate History

| Date | Goldens | Sims | Tool Tests | Callback Tests | Notes |
|------|---------|------|------------|----------------|-------|
| 2026-06-13 | 0/0 | 0/0 | 0/0 | 0/0 | Initial |

---

## Known Issues

- **Dispute Auto-Resolution**: PRD mentions "if a customer disputes a charge over $100 that cannot be automatically resolved", but does not define what qualifies a charge under $100 for automatic resolution vs manual dispute.
- **Dispute Timeline**: PRD mentions "provide a clear timeline for resolution" but does not specify the exact dispute resolution SLA/timeline (e.g. 5 business days).
- **Aggressive Language Filter**: Specific list or threshold for "aggressive language" needs definition.

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-06-13 | Clarified identity verification uses a 4-digit PIN, updated verify_customer_identity tool, and removed auth open question. | TDD-Writer Agent |
| 2026-06-13 | Added customer_profile fields (name, plan_details, active_promotions, billing_cycle) to track personalized customer info. | TDD-Writer Agent |
| 2026-06-13 | Initial requirements-derived TDD draft (sources: prd.md) | TDD-Writer Agent |

***
*Review and approve before scaffolding the agent.*
