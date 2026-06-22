# Maestro Case Schema — Vendor Risk Assessment

This is the contract every agent and API Workflow integrates against. Agree it
before building anything else. In Phase 1 we implement the first three stages
only (Intake → Assessment → Review); the rest are stubbed.

## Case fields (top-level)

| Field | Type | Set by | Notes |
|---|---|---|---|
| `case_id` | string | Maestro | Auto-generated |
| `vendor_id` | string | Intake | Primary key across all systems |
| `vendor_name` | string | Intake | |
| `vendor_domain` | string | Intake | Used by Research agent |
| `duns_number` | string? | Intake | Optional, used by Financial agent |
| `tier` | enum | Intake | Critical / High / Medium / Low |
| `stage` | enum | Maestro | See stages below |
| `overall_score` | int (0-100) | Risk Scoring | |
| `dimension_scores` | object | Risk Scoring | security/compliance/financial/operational/esg |
| `confidence` | int (0-100) | Risk Scoring | |
| `classification` | enum | Risk Scoring | Low / Medium / High / Critical |
| `decision` | enum? | Human / auto | Approve / ConditionalApprove / Reject / Escalate / Hold |
| `sla_due` | datetime | Maestro | Per-stage deadline |
| `findings` | list | All agents | Evidence attached during assessment |
| `audit_log` | list | All actors | Every transition + who/why |

## Stages, owners, SLAs

| # | Stage | Owner | SLA | Phase 1? |
|---|---|---|---|---|
| 1 | Intake | Intake Agent | 4h | yes |
| 2 | Assessment | Research / Compliance / Financial agents | 24h | yes (Research only) |
| 3 | RiskScoring | Risk Scoring Agent | 1h | yes |
| 4 | Review | Risk Analyst (Action Center) | 48h | yes |
| 5 | Decision | Human or auto-rule | 24h | stub |
| 6 | Monitoring | Scheduled job | continuous | stub |

## Transition rules

- Intake → Assessment: always, once docs parsed and tier set.
- Assessment → RiskScoring: when all in-scope agents have attached findings.
- RiskScoring → Review: if `overall_score > 50` OR `confidence < 60` OR `tier == Critical`.
- RiskScoring → Decision (auto-approve): otherwise (Low / Medium risk skips Review).
- Review → Decision: analyst submits a decision.
- Review → Assessment: analyst requests more investigation (loop-back).
- Decision → Monitoring: on Approve / ConditionalApprove.
- Monitoring → Assessment: when `requires_reopen == true` (reopen loop).

## Exception paths (Phase 1 implements #1)

1. `confidence < 60` → auto loop back to Assessment for more investigation. (Deterministic — best demo path.)
2. Vendor unresponsive → escalate after SLA breach.
3. Contradictory signals → force Review.
4. New regulation → batch reassessment.
5. Vendor acquired/merged → immediate reassessment.
6. Critical product vuln → emergency case.
