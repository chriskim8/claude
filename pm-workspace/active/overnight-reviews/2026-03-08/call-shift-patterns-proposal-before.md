# Before: Call & Shift Patterns — Proposal

Source: /Users/chriskim/notes/residency/proposals/call-shift-patterns.md

---

# Product Proposal: Call & Shift Patterns

**Status:** Draft
**Google Doc:** [Product Proposal: Call & Shift Patterns](https://docs.google.com/document/d/16vNPIof661-X22W9gSmKzt7neB5TkxYa2E9LYVNsQKI/edit)
**Related user journey:** [04 — Manager: Call/Shift](../user-journeys/04-manager-call-shift.md)
**Related Jira:** AMIONMGR-3293 (Call & Shift Patterns epic) · AMIONMGR-3308 (Patterns spike — gate)
**Migration tier unlocked:** Intermediate+

---

## Problem

Schedulers hand-enter every call and shift assignment. There is no way to define a repeating pattern — Q4, night float, 7-on/7-off, alternate week — and have it populate assignments automatically. Every rotation cycle, every academic year, coordinators rebuild the same schedule by hand. This is the single largest source of scheduling overhead for call-heavy programs and a primary blocker for migrations at Intermediate and Advanced tiers.

### ACGME regulatory context

ACGME Common Program Requirements impose specific constraints that directly shape how call schedules must be built — and how patterns must generate:

- **80-hour weekly maximum**, averaged over 4 weeks
- **In-house call no more often than Q3** (every third day), averaged over 4 weeks — this is the minimum density allowed for heavy rotations
- **24-hour continuous work period cap** — no scheduled clinical assignment may exceed 24 hours
- **One day free per seven** — a coordinator cannot assign home call for an entire month
- **Minimum 8 hours between clinical work periods** (14 hours after a 24-hour call shift)
- **PGY-1 (intern) restrictions** — specific committees may impose stricter limits in the first year

Patterns that generate assignments without awareness of these constraints create ACGME violations that coordinators must find and fix manually. Rest enforcement (SequenceRule post-call days off) is not a preference — it is a regulatory requirement. Any generated assignment that falls within a rest period should be flagged, not silently placed.

### Specialty call structure variability

Call schedules differ dramatically by specialty. Patterns must support all of these:

| Specialty | Typical pattern | ACGME constraint particulars |
|---|---|---|
| Internal Medicine | Q4–Q5 on wards; Q3 on ICU; night float ~4 weeks/year (7PM–7AM, 7-day blocks) | 14-hour rest after 24-hour call is most common source of violations |
| General Surgery | Q3–Q4 for PGY-1/2; increasing night float; some programs Q4 all 5 years | Post-call day required; 80-hour cap is hardest to maintain in busy surgical programs |
| Emergency Medicine | Scheduled 12-hour shifts (no traditional Q-call); separate shift types per training level | No Q-call — shift patterns only; day-after rest less relevant (shift durations shorter) |
| Psychiatry | Call restricted to specific rotations only (off-service affiliates); lighter Q4–Q5 | Some programs prohibit call during in-service inpatient psych blocks entirely |
| Ob/Gyn | Night float very common; 24-hour call on L&D; Q3–Q4 in junior years | Highest duty hour violation risk specialty — pattern rest enforcement is critical |
| Family Medicine | Blend of call (Q3–Q4 overnight) + continuity clinic coverage | Continuity must not be disrupted by call schedule — templates must interoperate |

The implication for Amion: the `pattern_type` enum must include both Q-call cadences (for IM, Surgery, Psychiatry, OB) and shift-based patterns (for EM and shift-heavy programs). These are different scheduling models and should be first-class options.

## Real Examples — What Coordinators Are Actually Trying to Build

These are confirmed scenarios from Arrowhead, Christopher Fahlsing's EM program, and Aline Campbell's Amion Next review.

**Arrowhead — confirmed migration blocker (Dec 2025)**
Aline Campbell and Katrina Chaffin tested rule creation for a 7-on/7-off night float rotation. The rule builder had no options for "week one, week two, week three." There was no way to represent a schedule where the pattern changes across a multi-week cycle. Aline concluded the system cannot handle patterns longer than one week. The client was routed back to Classic. (Source: Arrowhead Residency Schedule Review, Dec 2025)

**Christopher Fahlsing — EM program, 40 residents**
> "For me, my initial schedule build for a block would take 20 hours. Early on, 30 to 40 hours to figure out rules and schedule building."

This is the annual cost of having no pattern storage. 20–40 hours per block build, every year, rebuilt from scratch. One-time pattern setup converts this to a configure-once-apply workflow that persists across academic years.

**N-in-a-row sequences with day-of-week constraints (Aline's review)**
"Drs. A and B must work 6 Night Call in a row, no matter the day of the week. Also, Drs. C and D must work 2 Night Call in a row only if Mon–Fri." This is a baseline requirement, not an edge case. The pattern engine needs N-in-a-row logic (not just every-Nth-day cadence) and must support day-of-week filters with both staff-specific and staff-type-specific variants.

**Cascade chains across services (Aline's review)**
"Whoever works Friday on Day Call, must also work Day Call and Night Call on Saturday and Sunday following." This is a triggered chain: one assignment on day X generates assignments on X+1 and X+2 on different services. The SequenceRule subtype must support multi-step chaining with different services at each step — not just "same service, next day."

**Rest enforcement as ACGME compliance (Aline's review)**
"All MD staff type must have 2 days off following Swing and Night Call." This is not a preference — it is an ACGME duty hour requirement. Pattern generation must be aware of existing assignments to skip generating on required rest days. Without this, patterns generate violations that coordinators must manually find and correct after the fact.

## What This Proposal Covers

Two new rule subtypes that extend the existing ManagerRule STI system (no new table required):

### CallShiftPattern
A named repeating call structure. Coordinator defines: pattern type, cycle interval, which days, which service, which staff type(s), and a date range. The pattern is stored as a descriptor record. Assignments are resolved on-demand at render and export time — not pre-generated as individual rows.

Supported pattern types (pending Classic inventory audit in spike):
- Q-call (Q2, Q3, Q4 — every Nth night)
- Weekly
- Biweekly
- Alternate week (7-on/7-off)
- Night float (continuous block with handoff day)
- Custom

### SequenceRule
Consecutive-shift logic that applies per-assignment. Examples: "whoever works Friday also works Sat + Sun"; "2 days off required after any Swing call shift." Operates on individual assignment slots, not over a date range like CallShiftPattern.

**CallShiftPattern vs. SequenceRule — key distinction:**

| | CallShiftPattern | SequenceRule |
|---|---|---|
| Shape | Repeating cadence over a date range | Triggered consequence tied to a specific assignment |
| Example | "PGY-2s have Q3 overnight call from July through June" | "Whoever works Friday Day Call also works Day Call + Night Call on Sat and Sun" |
| Trigger | Time-based (start date, end date, cycle interval) | Assignment-based (if assigned to X, then also assign to Y) |
| Multi-step | No — single service, repeating | Yes — must support chaining: IF X → THEN Y (day 1) → THEN Z (day 2) |
| Day-of-week | Built into cadence (e.g., alternate week, Q3) | Constrained by days (e.g., Mon–Fri only) |

Both feel like "patterns" but they're different rule shapes and should be designed separately.

### Minimal Coordinator UI (scaffolding — not the end state)
A form on the Rules & Templates settings page. Inputs: name, pattern type dropdown, cycle interval, day selector, date range, staff type + service dropdowns. A server-rendered preview panel shows the first N resolved dates so the coordinator can confirm before saving. The form is intentionally minimal — it will be superseded by conversational rule entry (see vision below).

## Key Design Decisions

- **On-demand resolution, not generation-at-save.** Pattern records are descriptors; assignments resolve lazily at render and export. This avoids two-way sync problems (a block assignment change doesn't require re-generating call rows), keeps conflict detection always live, and makes the stored JSON directly machine-readable — a deliberate choice that enables the conversational interface with minimal additional work.
- **STI extension, no new table.** CallShiftPattern and SequenceRule reuse the existing `ManagerRule` + `ManagerRuleCondition` premise/result structure. No schema migration beyond registering new STI type values.
- **Conflict detection at render, not at save.** Pattern-resolved assignments that overlap existing manual entries are flagged visually — they are never silently overwritten.
- **AMIONMGR-3308 spike is the gate.** Before implementation begins, the spike must confirm the generation model with engineering, finalize all `pattern_type` enum values from the Classic pattern inventory, and validate the STI extension approach.

## The End State: Conversational Rule Entry

The form UI is scaffolding. The target experience is a single text input on the Rules & Templates page where a coordinator types "Q4 overnight call for PGY-2s on Night Float starting July 1" and a rule is saved and running. No dropdowns, no category selection, no multi-step wizard. The rule entry data model and API designed here are the permanent investment that makes this possible — the form UI is temporary scaffolding that the conversational interface will eventually replace. The form and the conversational interface both write to the same JSON descriptor model, so no rework is required when the form is replaced.

## Out of Scope

- Anonymous multi-row templates (shift-heavy orgs, Advanced tier — deferred). These unblock Advanced-tier programs (EM, Anesthesia, shift-heavy multi-service) that define call/shift structure first and fill in specific staff later. The structure spans multiple service rows and has no staff assigned at definition time. This is a Q3 priority once Q2 Intermediate patterns are shipped and validated.
- Conversational/natural-language rule entry UI (infrastructure built now; interface later)
- Call/shift tallies and duty hour enforcement (AMIONMGR-3315 — blocked until patterns ship)
- Rule override mechanism for sequence-managed slots (deferred)
- **CP-SAT Autoscheduler** — The `CallShiftPattern` and `SequenceRule` descriptors built here are direct inputs to the future CP-SAT constraint solver. The autoscheduler will consume these rule descriptors as scheduling constraints to generate optimal call/shift assignments automatically. That work requires this infrastructure as a prerequisite and is tracked separately.

## Open Questions

1. **Generation model** — Is on-demand the agreed approach, or does engineering prefer generation-at-save for consistency with ClinicTemplate (ADR-006)?
2. **SequenceRule Q2 scope** — Is SequenceRule included in Q2 alongside CallShiftPattern, or deferred to Q3?
3. **Multiple-THEN architecture** — Does `has_many :result_conditions` cover multi-step sequences ("IF on OB Call Friday → THEN Day Call Sat → THEN Night Call Sun")? Needs engineering confirmation before backend work starts.
4. **Design audit (AMIONMGR-3296)** — Tim/Brandon design audit for patterns must complete before the form UI phase begins.