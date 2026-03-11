# Before: Cancel Clinic Rules — Design Spec

Source: /Users/chriskim/notes/residency/proposals/clinic-template-expansion.md

---

# Product Proposal: Clinic Template Expansion

**Status:** Draft
**Google Doc:** [Product Proposal: Clinic Template Expansion](https://docs.google.com/document/d/1_FmsFlppKNhrHxEZE2LE1OIghwEHBOTzUxRcanLgFks/edit)
**Related user journey:** [05 — Manager: Clinic](../user-journeys/05-manager-clinic.md)
**Related Jira:** AMIONMGR-3292 (Clinic Schedule UX epic) · AMIONMGR-3306 (4-week cadence + cancel clinic rules)
**Migration tier unlocked:** Intermediate (ARMC, X+Y programs)

---

## Problem

Clinic templates currently support only weekly and every-other-week session cadences. ARMC and X+Y programs use 4-week per-week clinic patterns where the session schedule varies by week within each 4-week cycle — for example, Week 1: Mon + Wed sessions; Week 2: Thu only; Week 3: Mon + Wed; Week 4: none. Without this, these programs cannot migrate to Amion Next.

A second gap: programs with call-heavy schedules need clinic sessions to automatically cancel when a resident is on-call or post-call, or when they're assigned to a rotation that precludes clinic (e.g., ICU). Today this must be managed manually.

## Real Examples — What Coordinators Are Actually Trying to Do

These are grounded scenarios from ARMC, Elizabeth Byrd's feature requests, and Aline Campbell's Amion Next review.

**ARMC — 4-week FMI block with per-week clinic variation**
ARMC uses a 4-week block structure where a resident's clinic schedule varies by week within the block: Week 1 might have Monday AM + Wednesday AM, Week 2 has Thursday PM only, Week 3 repeats Week 1, Week 4 has no clinic. Next cannot represent this. The current workaround is artificially duplicating block services ("FMI week 1", "FMI week 2", "FMI week 3", "FMI week 4") so that specialty clinic templates can map to each sub-service separately. This workaround fails when the program has multiple splits within the same block, is not portable to other programs, and would not survive migration without the 4-week cadence feature. (Source: Residency on Amion Next weekly sync, Jan 30, 2026)

**Call-heavy program without cancel clinic rules — manual deletion burden**
A 20-resident program running Q3 call generates roughly 7 call nights per resident per month — meaning ~7 clinic sessions per resident must be deleted the morning after each call night. For 20 residents, that is 140 manual deletions per month, every month, all year. Cancel clinic rules eliminate this entirely. Without them, the coordinator either ignores the issue (residents have clinics scheduled on post-call days) or spends hours monthly on deletion maintenance. (Source: Amion Classic training guide, Elizabeth Byrd feature requests)

**Ambulatory scheduling — non-weekly cadence patterns**
From Aline Campbell's Amion Next review: "Clinic 1 is staffed every Tuesday + the 1st and 3rd Monday of the month + the 5th Friday of the month." This is a normal ambulatory pattern. Next cannot represent monthly anchor patterns (1st Monday, 3rd Thursday) in any current clinic template type. Programs that use these patterns must either hand-enter every session or stay on Classic.

**Conditional service activation — cancel clinic is not always about canceling**
From the same review: "Swing is staffed only if an NP is scheduled for Day Call the same day. If an MD is on Day Call, Swing is grayed out." This is not a standard cancel clinic rule — it is a conditional service activation rule that checks *who is on another service* before deciding whether to show a clinic slot at all. The rule evaluates a different service's assignment type, not the resident's own schedule. This is a more complex trigger than simple/advanced cancel clinic rules and is noted here as a design constraint for future scope.

## What This Proposal Covers

Two extensions to the existing `ClinicTemplate` rule subtype:

### 1. 4-Week Block Cadence
Extend `ResultRuleCondition.settings` to support `frequency: "every_4_weeks"` with per-week day configuration. No new model — extends existing schema and template application logic. When a coordinator applies a 4-week template, it generates individual session records across the AY following the defined per-week pattern.

Example settings structure:
```
Week 1: Mon, Wed
Week 2: Thu
Week 3: Mon, Wed
Week 4: (no sessions)
```

### 2. Cancel Clinic Rules
Conditions under which a template-generated session is automatically suppressed. Two rule levels:

**Simple cancel:** Cancel clinic when a resident is on-call or post-call from any call schedule assignment. Configurable options:
- Apply to on-call only, or on-call + post-call
- Apply to all staff types, or specific training levels only

Classic equivalent: the "Cancel Clinic" checkboxes in schedule Preferences.

**Advanced cancel:** Cancel based on more granular conditions:
- **By block service:** "If resident is on ICU rotation, cancel clinic" — applies to everyone on that block service regardless of call
- **By staff type:** Cancel for specific training levels only (e.g., PGY-1s lose clinic on call nights; attendings do not)
- **By call/shift assignment type:** "Overnight call cancels clinic; Backup call does not"
- **Composite ('if') conditions:** Combine block service + staff type + assignment type in one rule

Classic equivalent: the Rule Writer's advanced cancel clinic rules.

Cancel rules layer on top of templates — templates generate sessions; cancel rules suppress specific ones.

## Key Design Decisions

- **Schema extension, not new model.** 4-week cadence is an extension to `ResultRuleCondition.settings`. The existing generation-at-save model (ADR-006) is preserved — templates continue to generate individual session records at apply time.
- **Cancel rules suppress, don't delete.** Canceled sessions are visually distinct on the schedule (grayed out or struck-through) and reinstatable. Delete is permanent; cancel is rule-driven and reversible. A manually reinstated session is marked as an override — the cancel rule still applies on that date but the session remains active until the override is removed.
- **Manual reinstatement is an override.** A reinstated session remains active even if the cancel rule still applies, until the override is explicitly removed.
- **Templates persist year-to-year by default.** Classic behavior (from the Residency 101 training guide): "These templates follow the staff each program year unless they are removed or replaced." Coordinators expect continuity clinic templates to carry forward at AY rollover without re-setup. The carry-forward behavior at AY rollover must be explicitly designed — the current implementation does not define this.
- **Setup sequence dependency.** Specialty clinic templates can only be applied after block assignments are finalized for the relevant block service. Cancel clinic rules can only be validated after call/shift assignments exist. Template definition should be possible before these dependencies are met, but application and testing require them.
- **Stale template bug (AMIONMGR-3223) is out of scope.** The known issue where specialty clinic templates go stale after split date remodeling is a separate fix — not part of this proposal.

## Out of Scope

- 5th-week handling — some programs skip clinic sessions in "5th weeks" (calendar weeks where a 4-week cycle produces a 5th occurrence in a given month). Requested by Elizabeth Byrd. Deferred because it requires a cadence normalization concept beyond standard day-of-week rules.
- Per-split clinic template regeneration fix (AMIONMGR-3223 — tracked separately)
- "Skip" logic for specific date ranges (deferred)
- Clinic template import / bulk generation (deferred)
- **CP-SAT Autoscheduler** — `ClinicTemplate` descriptors (including 4-week cadence and cancel clinic conditions) are inputs to the future CP-SAT constraint solver. The autoscheduler will use these to generate and validate clinic schedules against availability and rotation constraints. That work requires this infrastructure as a prerequisite and is tracked separately.

## Regulatory context — why template accuracy is not optional

Continuity clinic is not just a scheduling preference. ACGME program requirements mandate minimum ambulatory session counts by specialty. Templates are the mechanism by which programs ensure those minimums are scheduled. Poor template generation = missed sessions = ACGME citation risk.

| Specialty | ACGME minimum ambulatory requirement |
|---|---|
| Internal Medicine | 108 continuity clinic sessions over 36 months (~3 sessions/week); may be excused during ICU, night float, emergency, or away electives |
| Family Medicine | 1,000 hours in FM practice site; scheduled at the site minimum 40 weeks/year; PGY-2 must achieve ≥30% resident-sided continuity, PGY-3 ≥40% |
| Ob/Gyn | 120 half-day ambulatory sessions over 4 years; at least 1 half-day/week for at least 30 months |
| Most other specialties | Outpatient experience requirements defined in specialty-specific requirements |

These requirements have direct implications for template design:

1. **Templates that generate incorrectly** (e.g., specialty templates going stale after a split remodel — AMIONMGR-3223) cause gaps in a resident's session count that may not be caught until logging. Fixing stale specialty templates is therefore not just a UX improvement — it is a compliance prerequisite.
2. **Cancel clinic rules must track reinstatements.** If a cancel rule fires on a post-call day, that session is suppressed. If a resident already has fewer sessions than their minimum due to an ICU rotation, a coordinator may need to reinstate canceled sessions to maintain compliance. The reinstatement mechanism is not optional.
3. **The 4-week cadence expansion enables correct session counting.** Programs currently workarounding with duplicate block services (e.g., "FMI week 1", "FMI week 2") may be generating duplicate sessions, under-generating, or generating the wrong sessions on the wrong weeks — all of which affect session counts used for ACGME compliance reporting.

## Client profile evidence — scale of the clinic proliferation problem

The "clinic service proliferation" pattern is documented across the entire client base. Programs create one service per week variant because templates don't support per-week cadences. This inflates block/clinic service counts and is a direct migration blocker:

| Program | Block/Clinic services in Next | Root cause |
|---|---|---|
| ARMC Family Medicine | 316 | Per-week clinic workaround |
| Santa Clara Valley Healthcare | 312 | Clinic proliferation |
| BronxCare Family Medicine | 114 | Per-week clinic workaround |
| BronxCare Pediatrics | 94 | Clinic proliferation |
| Brooklyn Hospital FM | 88 | Per-week clinic workaround |
| Cooper University Hospital | 186 (one schedule) | Clinic proliferation |
| SUNY Upstate | 622 (one schedule) | Extreme clinic proliferation |
| UCHealth | 2,101 (one schedule) | Most extreme case in dataset |
| LCMC / Tulane | 1,233 | Clinic proliferation |

Every one of these programs has an inflated block/clinic service count as a direct consequence of not having 4-week cadence templates. AMIONMGR-3292 fixes this across all of them. Without it, Tier 4 programs like SUNY Upstate, UCHealth, and LCMC cannot be migrated at any reasonable cost.

## Open Questions

1. **Cancel rule evaluation model** — Are cancel rules evaluated at template generation time (call schedule must be finalized first) or at render time (live rules that reflect call changes immediately)? Trade-off: generation-time is simpler but fragile; render-time is more resilient but adds query complexity.
2. **Visual treatment for canceled sessions** — What distinguishes a canceled session from an active one in the coordinator view? (Grayed text, strikethrough, distinct color chip?)
3. **Re-application flow** — When a 4-week cadence template definition changes after initial application, what is the coordinator's path to update already-generated sessions? Manual correction vs. guided re-apply flow?
