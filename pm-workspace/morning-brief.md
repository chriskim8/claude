# Morning Brief — Mon Mar 9, 2026
_Generated 12:10am nightly. Slack follow-ups pulled live below._

---

## 🔧 Overnight Review — Before/After

_Claude reviewed your in-progress work overnight. Full reviews in `~/pm-workspace/active/overnight-reviews/`_

### Clinic Template Expansion — UX Prototype `[ux-prototype]`

**Critical Issues:**
1. **The 4-week cycle table has no clear "anchor date" input.** The ARMC FMI pattern requires knowing *which real calendar week* is "Week 1." Without this, the table is meaningless — a provider clicking cells has no way to know if Week 1 maps to the first Monday of the month, the block start date, or something else. This is the core of the 140-deletion problem and the prototype doesn't solve it. You need a visible, editable "Cycle starts on: [date]" field above the table, with a plain-language preview like "Next Week 1: Oct 6, 2025."
2. **Cancel rules have no defined trigger surface.** The brief says cancel rules must not add visual row noise, but the prototype doesn't show *how* a user discovers, opens, or edits a cancel rule for an existing repeating assignment. There's no affordance on the schedule view — no icon, no secondary action on the chip, nothing. The constraint (no clutter) has eaten the discoverability entirely. Pick one: a collapse-inline chevron on the assignment row, or a dedicated "Exceptions" link in the repeat modal footer. Show it.
3. **Scope selector ("Apply to") is positioned wrong and its consequences aren't shown.** Moving scope to the top sounds logical, but "This assignment only / This and following / All assignments" is a *destructive-consequence* decision that should appear at *save time*, not at form-open time. A user who sets up a complex 4-week pattern and then realizes scope was defaulted to "This only" has wasted all that work. Worse, the prototype shows no confirmation state, no diff preview, no count of affected sessions. At minimum, the save button label should reflect scope: "Save 47 sessions" vs. "Save this session."

**Missing Edge Cases:**
1. **Block boundary crossing.** What happens when a 4-week cycle straddles two academic blocks (e.g., cycle Week 3–4 falls in the next rotation block)? Does the template auto-truncate? Error? Continue into the new block silently? This is exactly the ARMC scenario and it's unaddressed.
2. **Cycle drift after a manual edit.** If a scheduler manually deletes one instance mid-cycle (the current 140/month behavior), does the cycle re-anchor from that deletion, skip it and continue, or flag a conflict? The prototype shows no "exception" state in the 4-week table cells.
3. **Aline monthly anchor pattern vs. 4-week pattern collision.** These are not the same thing — 4 weeks ≠ 1 month. If a provider has both patterns applied, which wins in week 5 of a 5-week month? No handling shown.

_Full review: `/Users/chriskim/pm-workspace/active/overnight-reviews/2026-03-09/clinic-template-expansion-ux-prototype-review.md`_

### Cancel Clinic Rules — Design Spec `[proposal]`

**Weakest Assumptions:**
1. **"No new model — extends existing schema and template application logic."** The proposal asserts this as though it's been validated. A 4-week cyclical cadence with per-week day variation is structurally different from a weekly recurrence. Whether `ResultRuleCondition.settings` can absorb this without model changes hasn't been demonstrated — it's stated as a conclusion, not an engineering finding.
2. **"Cancel rules suppress, don't delete... canceled sessions are visually distinct and reinstatable."** This assumes a suppress/override layer exists in the current session model. The proposal never confirms this. If sessions are currently stored as discrete records with no suppression state, this requires a schema change that the "no new model" claim above makes more complicated.
3. **"Templates persist year-to-year by default... The carry-forward behavior at AY rollover must be explicitly designed — the current implementation does not define this."** This is self-contradicting. The doc states persistence as a design decision, then immediately admits the behavior isn't implemented. This isn't a design decision; it's an unresolved requirement masquerading as one.

_Full review: `/Users/chriskim/pm-workspace/active/overnight-reviews/2026-03-09/cancel-clinic-rules-design-spec-review.md`_

### Call & Shift Patterns — Proposal `[proposal]`

**Weakest Assumptions:**
1. **"STI extension, no new table required"** — This is asserted, not demonstrated. STI works cleanly when subtypes share schema shape. CallShiftPattern (date-range cadence) and SequenceRule (per-assignment trigger with multi-step chaining) have fundamentally different data shapes. Cramming both into `ManagerRule` + `ManagerRuleCondition` without schema changes is an engineering assumption that Open Question #3 explicitly hasn't resolved yet. This is listed as a design decision while simultaneously flagged as an open question — that's contradictory.
2. **"On-demand resolution avoids two-way sync problems"** — Taken as obviously correct, but it introduces a different class of problem: render-time performance at scale. A coordinator with 40 residents across 6 services, each with overlapping CallShiftPatterns and SequenceRules that chain, will hit this at export or schedule view load. No latency budget, no caching strategy, no degradation path is described. The assumption that lazy resolution is uniformly better than generation-at-save is not defended against the ClinicTemplate precedent (ADR-006) that apparently went the other direction.
3. **"Pattern generation must be aware of existing assignments to skip generating on required rest days"** — The proposal states this as a requirement but the conflict detection section says violations are "flagged visually" rather than prevented. These are in direct tension. If a rest-period violation is flagged but still placed, ACGME compliance risk remains. The assumption that "flagging is sufficient" for regulatory enforcement is never examined.

_Full review: `/Users/chriskim/pm-workspace/active/overnight-reviews/2026-03-09/call-shift-patterns-proposal-review.md`_


---

## 🔥 Overnight Jira Activity

- **AMIONMGR-2429** — Residency: Schedule Publish (Green Lock)  
  Status: `Backlog` | Priority: Not Selected
- **AMIONMGR-3197** — Residency: Viewer-side Updates  
  Status: `Backlog` | Priority: Not Selected
- **AMIONMGR-3188** — Residency: Multiple Block Splits  
  Status: `Backlog` | Priority: Not Selected
- **AMIONMGR-1427** — Residency: Academic Year <> Staff Visibility  
  Status: `Backlog` | Priority: Not Selected
- **AMIONMGR-3286** — Work Preferences: Resident Preference Collection & Request Review  
  Status: `Backlog` | Priority: Not Selected
- **AMIONMGR-3269** — [Residency] Residency features for Organization Who's On  
  Status: `Backlog` | Priority: Not Selected
- **AMIONMGR-3316** — Residency: Mobile App Testing & Resident Experience  
  Status: `Backlog` | Priority: Not Selected
- **AMIONMGR-3315** — Residency: Call/Shift Tallies & Duty Hour Awareness  
  Status: `Backlog` | Priority: Not Selected
- **AMIONMGR-3314** — Residency: Block Rotation Swap & Giveaway  
  Status: `Backlog` | Priority: Not Selected
- **AMIONMGR-3313** — Residency: Migration Prerequisites — AY Setup & Bulk Staff Management  
  Status: `Backlog` | Priority: Not Selected
- **AMIONMGR-3294** — Residency: Migration — Map Classic Staff Types to Training Levels  
  Status: `Backlog` | Priority: Not Selected
- **AMIONMGR-3292** — Residency: Clinic Schedule UX — Cancel Clinic Rules, Template Expansio  
  Status: `Backlog` | Priority: Not Selected
- **AMIONMGR-3293** — Residency: Call & Shift Patterns  
  Status: `Backlog` | Priority: Not Selected
- **AMIONMGR-3264** — Move 100% to Amion Next API: Residency & Support All Paging Carriers  
  Status: `Backlog` | Priority: Not Selected
- **AMIONMGR-3251** — Integration: Payroll (Approvals)  
  Status: `Backlog` | Priority: Not Selected
- **AMIONMGR-3255** — Allow scheduler managers to review activation requests in Tasks with e  
  Status: `Backlog` | Priority: Medium
- **AMIONMGR-3254** — Allow schedule managers to apply admin approval to payroll report rows  
  Status: `Backlog` | Priority: Medium
- **AMIONMGR-3253** — Allow providers to review/approve hours and activations in a new My Ho  
  Status: `Backlog` | Priority: Medium
- **AMIONMGR-3252** — Add hours approval for schedules on the facility-level payroll setting  
  Status: `Backlog` | Priority: Medium
- **AMIONMGR-3320** — Baseline Residency Block Schedule Rendering Performance  
  Status: `Backlog` | Priority: High
- **AMIONMGR-3317** — Viewer: Refactor SWO table layout to support sticky headers, density m  
  Status: `Backlog` | Priority: High
- **AMIONMGR-3297** — [Design] Staff Type → Training Level Mapping — Migration UX Design  
  Status: `Backlog` | Priority: Not Selected
- **AMIONMGR-3296** — [Design] Call & Shift Patterns — Current State Audit & Design Directio  
  Status: `Backlog` | Priority: Not Selected
- **AMIONMGR-3307** — Clinic: cross-schedule visibility strip + staff list UX improvements  
  Status: `Backlog` | Priority: Not Selected
- **AMIONMGR-3295** — [Design] Clinic Schedule UX Audit — Problem Statement & Current State  
  Status: `Backlog` | Priority: Not Selected

---

## 📋 Active Queue (top 10 by priority)

- **AMIONMGR-3263** `Backlog` [Not Selected] — From a Call or Shift schedule, the user is redirected to "Schedule: Bloc
- **AMIONMGR-3288** `Backlog` [Not Selected] — Admin code 'Ohs1!', row 'BBPE MD 2nd Call', in June, Timur Durrani has d
- **AMIONMGR-3265** `Backlog` [Not Selected] — Hide 'swap pool' options for staff when swap pool is disabled
- **AMIONMGR-3262** `Backlog` [Not Selected] — 500 ERROR when canceling a published Clinic shift (on Production).
- **AMIONMGR-3077** `Blocked` [Not Selected] — Schedule draft should operate on refs
- **AMIONMGR-3168** `Selected for Development` [Not Selected] — The new users under admin 'Qq8*ifVT' can't auto schedule into May 2026.
- **AMIONMGR-3147** `Backlog` [Not Selected] — [Residency: Block] The "Time Off" assignment will disappear on the front
- **AMIONMGR-3144** `Backlog` [Not Selected] — The "Time Off" pop-up persists on a Block Schedule after clicking Time O
- **AMIONMGR-3124** `Backlog` [Not Selected] — I can create duplicate Swap Shift or Give Shift requests by clicking "Su
- **AMIONMGR-2791** `Backlog` [Not Selected] — On a Viewer Schedule, dates can overlap with other dates and/or spill ou

---

## 🧩 Integration Triage Inbox

**Jira — Integration tickets (last 7 days):**

- **AMIONMGR-2950** `Backlog` — Integration: ADP Payroll (MVP) _(assignee: Unassigned)_
- **AMIONMGR-3264** `Backlog` — Move 100% to Amion Next API: Residency & Support All Paging Carriers _(assignee: Unassigned)_
- **AMIONMGR-3251** `Backlog` — Integration: Payroll (Approvals) _(assignee: Unassigned)_
- **AMIONMGR-3259** `Backlog` — Allow archival of org-level ADP payroll fields _(assignee: Unassigned)_
- **AMIONMGR-3258** `Backlog` — Allow org managers to create and manage ADP-specific fields for their or _(assignee: Unassigned)_
- **AMIONMGR-3276** `Backlog` — Integration: ADP Payroll (Enhancements) _(assignee: Unassigned)_
- **AMIONMGR-3205** `Will Not Do` — Make Epic integration Note field read-only for Service Group rows _(assignee: Unassigned)_
- **AMIONMGR-3239** `Done` — Add e2e test for epic integration _(assignee: Ryan Stawarz)_
- **AMIONMGR-3245** `In Code Review` — Extend staff CSV import to support ADP payroll fields _(assignee: Ben Simpson)_
- **AMIONMGR-3246** `In Code Review` — Allow facility managers to map services to ADP pay codes _(assignee: Ben Simpson)_

**Canny — Integration posts:**

- [Feature Requests] **AMTELCO Integration (Providence Swedish/Oregon Region)** | open | 2 votes | by Amanda Roberts
- [Feature Requests] **UKG/EZ Call Integration** | open | 1 votes | by Amanda Roberts
- [Feature Requests] **Epic Integration: Improve Contact Information Reliability with the Epic ** | open | 2 votes | by Amanda Roberts
- [Feature Requests] **Migration Enhancement: Contact Method Mapping** | under review | 7 votes | by Whitney Weaver
- [Feature Requests] **UKG Integration** | planned | 2 votes | by Whitney Weaver
- [Bugs + Enhancements] **Epic Integration: Hidden Contact Info displaying in Flat File** | planned | 2 votes | by Amanda Roberts
- [Bugs + Enhancements] **Epic Integration - Mapping Warning when Services not Mapped** | planned | 2 votes | by Amanda Roberts
- [Bugs + Enhancements] **Epic Integration - Warning when we Delete a Provider Care Team record an** | open | 2 votes | by Amanda Roberts
- [Bugs + Enhancements] **Epic Integration: Assignment Notes not displaying in Flat File** | planned | 2 votes | by Amanda Roberts
- [Bugs + Enhancements] **Epic Integration - Team Column to show when multiple Teams Selected** | open | 2 votes | by Amanda Roberts

_Slack: Amanda Roberts + Sebastian DeLuca integration threads pulled live at session open via Glean._

---

## 🎓 Residency Planning Status

**Backlog:**
  - **AMIONMGR-3308** — Spike: call & shift patterns data model — generation-at-save vs. on-dema _(Unassigned)_
  - **AMIONMGR-3307** — Clinic: cross-schedule visibility strip + staff list UX improvements _(Unassigned)_
  - **AMIONMGR-3306** — Clinic: 4-week block cadence templates + cancel clinic rules _(Unassigned)_
  - **AMIONMGR-3296** — [Design] Call & Shift Patterns — Current State Audit & Design Direction _(Unassigned)_
  - **AMIONMGR-3295** — [Design] Clinic Schedule UX Audit — Problem Statement & Current State _(Unassigned)_
  - **AMIONMGR-3319** — [Spike] CP-SAT Autoscheduler — Architecture Investigation _(Unassigned)_


---

## 📊 Residency Tier API Comparisons

| LICENSE_VIEWER_CODE | AMIONC_REFERENCE_ID | AMIONC_ACCOUNT_NUMBER | GROUP_NAME | GROUP_ACCESS_CODE | SCHEDULE_NAME | INTERNAL_CLINICIAN_ACCESS_CODE |
| --- | --- | --- | --- | --- | --- | --- |
| SLVHCS | slvhcs | 3 | Medicine Affiliate | hospital medicine | Medicine Residency-Tulane | SLVHCS hospital medicine |
| SLVHCS | slvhcs | 8 | Infectious Diseases | id | Infectious Diseases | SLVHCS id |
| VAPSHCS | vapshcs | 47 | Infectious Disease | ID | Infectious Disease | VAPSHCS ID |
| englewood | new_42886 | 3 | Dental Residency | dental | Dental Residency | englewood dental |
| englewood | new_42886 | 15 | Medicine Residency | medres | Medicine Residency | englewood medres |

---

## 🤔 Open Decisions + Recent ADRs

### Pending Decisions

# Open Decisions (ADR Inbox)


---

## Integration Ticket Prioritization (Amanda Roberts / Sebastian DeLuca)
- **Context:** Amanda and Sebastian have raised integration-related changes via Jira tickets, Canny posts, and Slack. Need to decide prioritization framework for the ADP integration epic.
- **Options:** A) Prioritize by customer impact score, B) Prioritize by engineering effort (lowest first), C) Group by integration type and tackle as batches
- **Who's involved:** Amanda Roberts, Sebastian DeLuca, Engineering lead
- **Deadline:** Before next sprint planning
- **Added:** 2026-03-08

## Steven Hibble — Data Estimation Sessions
- **Context:** Was in a thread with Steven Hibble. Need to decide whether to start inviting him to data estimation sessions.
- **Options:** A) Invite starting next sprint, B) Loop in after residency milestone, C) Ad-hoc invite only
- **Who's involved:** Steven Hibble
- **Deadline:** No hard deadline
- **Added:** 2026-03-08

### Recent Decisions (last 5)

_No decisions logged yet._
