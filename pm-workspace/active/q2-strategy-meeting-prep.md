# Q2 Product Strategy Meeting — Preparation Guide

**Meeting:** ~4 hours | **Audience:** Professional Services, all PMs, Engineering Lead
**Primary outcome:** Lock Q2 scope commitments (what ships, what's stretch, what's deferred)
**Secondary outcome:** Formalize the shared bugs & enhancements goal

---

## Pre-Work Checklist

### A. Engineering Pre-Alignment (30-min pre-meeting with eng lead)

Resolve these three blocking architectural questions *before* the full meeting so they don't consume strategy time. Frame as binary decisions with a written brief:

1. **STI extension vs. new table** — Can CallShiftPattern and SequenceRule both fit in the existing `ManagerRule` STI without schema changes? The overnight review flags that they have fundamentally different data shapes. Need a yes/no with a one-paragraph justification.

2. **On-demand resolution vs. generation-at-save** — The clinic templates use generation-at-save per ADR-006. The call patterns proposal proposes on-demand. These are opposite architectural choices for the same product surface. Performance concern: 40+ residents across 6 services with overlapping patterns and chained SequenceRules. Eng lead's recommendation needed.

3. **Cancel rule evaluation model** — Render-time vs. generation-time. If engineering recommends generation-at-save for patterns, cancel rules should likely also be generation-time for consistency. These decisions are coupled.

Walk into the full meeting with engineering's recommendation, not an open debate.

### B. Residency Migration Spreadsheet (Google Sheet)

Structure for program-level migration readiness. PS validates and fills gaps in the meeting.

| Column | Content |
|--------|---------|
| Program | ARMC, Fahlsing EM, UCHealth, SUNY Upstate, LCMC/Tulane, BronxCare, Santa Clara Valley, Brooklyn Hospital FM, Cooper |
| Tier | Intermediate / Advanced |
| Current State | Classic / Next / Blocked-returned-to-Classic |
| Blocking Feature(s) | What Next capability is missing (e.g., "4-week clinic cadence", "call patterns", "shift-based patterns") |
| Q2 Unblocked? | Yes / No — based on Q2 Target column from the punchlist |
| Service Count | From Snowflake tier data (UCHealth 2,101 / LCMC 1,233 / ARMC 316) |
| Staff Count | Relevant for render-time performance (Fahlsing EM: 40 residents) |
| Notes | PS-provided context, contract timelines, escalation status |

**Purpose in the meeting:** PS sees which programs move to "unblocked" with Q2 delivery and which require Q3/Q4 features. Every program should leave with a disposition: "unblocked in Q2" or "needs Q3 features" or "Advanced tier — Q4."

### C. Core Enhancements Punchlist

The stretch-goals-with-intermediate-solutions framing. **This one-pager IS the meeting's main working document.** The meeting validates the "Target" column and acknowledges "Stretch" as aspirational.

| Enhancement | Target (Q2 commit) | Stretch (Q2 aspirational) | Full (Q3+) |
|---|---|---|---|
| **Call & Shift Patterns** | Basic CallShiftPattern (Q-call, weekly, biweekly, night float) + visual conflict flags | SequenceRules (cascade, rest enforcement) | Full ACGME compliance with tally backend (AMIONMGR-3315) |
| **Clinic Templates** | 4-week block cadence with anchor date | Cancel clinic rules (simple: on-call/post-call) | Advanced cancel rules + AY rollover |
| **Autoscheduler** | CP-SAT integrated with pattern/template descriptors, deployed for basic constraint types | Handles 80% of named cadences end-to-end | Full constraint coverage including SequenceRules, rest enforcement, ACGME |
| **Latency** | Baseline measurement (AMIONMGR-3320) + top bottlenecks fixed | Key render-path optimizations for 40+ resident orgs | Sub-second for UCHealth-scale (2000+ services) |
| **Viewer / Residency** | SWO table refactor (AMIONMGR-3317) scoped and shipped | Viewer-side updates (AMIONMGR-3197) | Full residency viewer experience |

### D. Bug & Enhancement Backlog Snapshot

Bring to the meeting with severity and frequency data if available:

| Bug | Ticket | Severity | Cross-functional? |
|-----|--------|----------|-------------------|
| 500 error on clinic shift cancel (production) | AMIONMGR-3262 | High | Yes — PS sees in support |
| Time Off disappearing on block schedule | AMIONMGR-3147 | High | Yes — data loss perception |
| Duplicate swap/give shift requests | AMIONMGR-3124 | Medium | Yes — user confusion |
| Viewer date overlap/spill | AMIONMGR-2791 | Medium | Yes — viewer-facing |
| Auto-schedule failure for new users | AMIONMGR-3168 | High | Eng-owned (selected for dev) |
| Schedule draft should operate on refs | AMIONMGR-3077 | Blocked | Eng architectural decision |

---

## Meeting Agenda

### Block 1: Context & Frame (45 min)

**0:00–0:15 — Migration context (Chris presents)**

Open with revenue/retention framing, not features. The core message:

> "We are losing residency programs to Classic. ARMC was routed back because Next couldn't handle their patterns. The programs in our spreadsheet represent [X revenue / Y contracts] waiting on Next capabilities."

Walk through the residency migration spreadsheet. PS identifies which programs move to "unblocked" with Q2 delivery.

**0:15–0:30 — 3/6/9 framework draft**

Present the draft 3/6/9 (see Section below). This is a starting point, not a finished document — the meeting's job is to validate and adjust.

**0:30–0:45 — Core enhancements punchlist introduction**

Introduce the stretch-goals philosophy:

> "We pursue ambitious targets but define intermediate milestones we're happy shipping. The autoscheduler PoC is complete — Q2 is about integrating it with the pattern/template infrastructure, not building from scratch. Patterns/templates and autoscheduler are one initiative: we ship the constraint language AND the solver that consumes it."

### Block 2: Scope Negotiation (90 min)

**0:45–1:15 — Residency features (30 min)**

Walk through each row of the punchlist:
- PS reacts: "which programs does this unblock?"
- Engineering reacts: "is this feasible in this timeframe?"
- PMs react: "does this conflict with other product commitments?"

Goal: Lock the Target column for each row.

**1:15–1:35 — Shared bugs & enhancements goal (20 min)**

Formalize the commitment that's already been discussed:
- Propose: dedicated % of sprint capacity (e.g., 20%) for bugs/enhancements
- Shared P1 SLA — PS surfaces top customer-impacting bugs, eng triages
- Walk through the bug snapshot
- Agree on the process: how bugs get escalated, triaged, and tracked

**1:35–1:55 — ADP integration (20 min)**

Status check on the 7-story epic. Stories 5-6 are in code review. What remains? Timeline to complete? Any blockers?

**1:55–2:15 — Latency and performance (20 min)**

Present the concern:
- 40+ residents across 6 services with overlapping patterns at render time
- UCHealth (2,101 services), LCMC (1,233 services) — scale matters
- Eng lead confirms baseline spike (AMIONMGR-3320) is step one
- Agree: is latency a Q2 Target commitment or Stretch?

### Break (15 min)

### Block 3: 3/6/9 Lockdown (60 min)

**2:30–3:30 — Fill out the 3/6/9 doc in real-time**

Use the punchlist and Block 2 decisions as inputs:
- **3-month:** Committed scope from the Target column + bugs goal + ADP completion + autoscheduler integration
- **6-month:** Stretch items that didn't make Q2 + SequenceRules + advanced cancel rules + AY rollover + autoscheduler constraint expansion
- **9-month:** Full ACGME enforcement, EM shift patterns (Advanced tier), conversational interface, mobile residency experience

For each item, confirm:
- [ ] Owner assigned
- [ ] Dependencies identified
- [ ] Spike required? (If yes, when does it start?)

### Block 4: Decisions & Actions (30 min)

**3:30–4:00 — Close out**

- Ratify architectural decisions from eng pre-meeting in full group
- Confirm owners for each punchlist row
- Identify spikes that must complete before development starts:
  - AMIONMGR-3308 — Call & shift patterns data model spike
  - AMIONMGR-3319 — CP-SAT autoscheduler architecture investigation
  - AMIONMGR-3320 — Baseline residency block schedule rendering performance
- Set the mid-quarter checkpoint date
- Confirm: who updates the 3/6/9 doc as the source of truth going forward?

---

## Draft 3/6/9 Content

### 3-Month (Q2 — April–June)

**Residency core:**
- 4-week clinic template cadence — ships first, unblocks ARMC and similar programs
- Cancel clinic rules: simple (on-call/post-call suppression) — eliminates the 140 manual deletions/month problem
- CallShiftPattern: named cadences (Q-call, weekly, biweekly, alternate week, night float) — covers IM, Surgery, Psych, OB, FM use cases
- **CP-SAT autoscheduler integration** — connect PoC solver to pattern/template descriptors, deploy for basic constraint types

**Platform:**
- ADP Payroll: complete 7-story epic
- Shared bugs: resolve named P1s, dedicated sprint capacity commitment
- Viewer: SWO table refactor (AMIONMGR-3317)
- Performance: baseline measurement (AMIONMGR-3320) + top bottleneck fixes

**Design:**
- Call & shift patterns current state audit (AMIONMGR-3296)
- Clinic schedule UX audit (AMIONMGR-3295)

### 6-Month (Q3 — July–September)

**Residency advanced:**
- SequenceRules (multi-step chaining, post-call rest enforcement)
- Advanced cancel clinic rules (by block service, by staff type, composite conditions)
- Call/shift tallies + duty hour enforcement (AMIONMGR-3315)
- AY rollover for templates and patterns
- Anonymous multi-row templates (Advanced tier — unblocks EM programs like Fahlsing's)

**Platform:**
- Autoscheduler: expand constraint coverage beyond basic cadences (SequenceRules, rest, ACGME)
- Viewer-side residency updates (AMIONMGR-3197)

### 9-Month (Q4 — October–December)

- Full ACGME compliance enforcement (flagging → prevention)
- Autoscheduler: production hardening, edge case coverage, large-org performance
- Conversational scheduling interface (pattern creation via natural language)
- Mobile app residency experience (AMIONMGR-3316)
- Work preferences / resident preference collection (AMIONMGR-3286)

---

## Key Framing Notes

1. **Open with migration, not features.** "Programs are going back to Classic" is a revenue argument everyone in the room understands. PS, PMs, and engineering all have different reasons to care — migration is the unifying frame.

2. **"Ship 80%, learn, then complete."** Patterns that handle Q-call, weekly, biweekly, and night float cover the majority of IM, Surgery, Psych, OB, FM use cases. EM shift patterns are explicitly Q3. Be upfront about what's deferred and why.

3. **Autoscheduler is the payoff for patterns/templates.** The PoC is complete. Q2 is about integration — connecting the solver to the constraint language. Frame it as one initiative: "We ship the constraint language AND the solver that consumes it."

4. **PS needs program-level answers.** Every program in the spreadsheet should leave with a disposition: "unblocked in Q2," "needs Q3 features," or "Advanced tier — Q4."

5. **The bugs goal is a process commitment, not just a list.** The meeting should produce agreement on: capacity allocation, escalation path, and SLA — not just "here are the bugs."
