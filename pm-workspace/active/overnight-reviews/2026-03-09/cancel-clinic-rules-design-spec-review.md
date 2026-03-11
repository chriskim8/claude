# Overnight Review: Cancel Clinic Rules — Design Spec

Date: 2026-03-09
Source: /Users/chriskim/notes/residency/proposals/clinic-template-expansion.md

---

## Weakest Assumptions

1. **"No new model — extends existing schema and template application logic."** The proposal asserts this as though it's been validated. A 4-week cyclical cadence with per-week day variation is structurally different from a weekly recurrence. Whether `ResultRuleCondition.settings` can absorb this without model changes hasn't been demonstrated — it's stated as a conclusion, not an engineering finding.

2. **"Cancel rules suppress, don't delete... canceled sessions are visually distinct and reinstatable."** This assumes a suppress/override layer exists in the current session model. The proposal never confirms this. If sessions are currently stored as discrete records with no suppression state, this requires a schema change that the "no new model" claim above makes more complicated.

3. **"Templates persist year-to-year by default... The carry-forward behavior at AY rollover must be explicitly designed — the current implementation does not define this."** This is self-contradicting. The doc states persistence as a design decision, then immediately admits the behavior isn't implemented. This isn't a design decision; it's an unresolved requirement masquerading as one.

4. **"Must ship with M2."** The M2 dependency is stated in the header context but never explained in the proposal body. What does M2 gate? Is this a contractual commitment, a migration prerequisite, or a product sequencing assumption? The proposal doesn't say, which means the constraint can't be evaluated or challenged.

5. **"Cancel clinic rules eliminate this [140 manual deletions/month] entirely."** This assumes rule coverage is exhaustive — that every call assignment type that should suppress a session is configured correctly by the coordinator. Edge cases (split assignments, retroactive call changes, ad-hoc coverage swaps) could leave sessions uncanceled regardless of rule existence.

6. **"Classic equivalent: the Cancel Clinic checkboxes in Preferences / Rule Writer's advanced cancel clinic rules."** The proposal treats Classic parity as a known, stable baseline. But Classic cancel clinic behavior — how rules were evaluated, whether they were render-time or generation-time, how conflicts were resolved — is never documented here. If Classic had undocumented behaviors that coordinators rely on, this proposal will ship something that looks equivalent but isn't.

---

## Scope Gaps

1. **Conflict resolution between cancel rules is undefined.** What happens when a simple rule and an advanced rule both apply to the same session? Which wins? What if two advanced rules conflict (block service says cancel; assignment type says don't)? There's no priority model, no mention of AND/OR logic between composite conditions.

2. **Retroactive call changes are unhandled.** If a call assignment is modified after cancel rules have already been evaluated (or sessions generated), what happens? The open question on evaluation model acknowledges generation-time vs. render-time but doesn't address the downstream impact of call edits on already-suppressed or already-active sessions.

3. **The 5th-week deferral creates an immediate gap for stated users.** Elizabeth Byrd's request is deferred, but ARMC's 4-week cycle will produce 5th-week occurrences in certain months. The proposal doesn't describe what the system does in those cases — does it generate an incorrect session, generate nothing, or error? "Deferred" is not an answer to what the system does today.

4. **Partial-block cancel behavior is undefined.** "If resident is on ICU rotation, cancel clinic" — what if a resident is on ICU for days 1–12 of a block and switches to a different service for days 13–28? Does the cancel rule apply to sessions in the first half only? Block-service cancel rules are described as applying to "everyone on that block service," but split-block assignments break this assumption.

5. **Multi-resident session handling is absent.** Some clinic templates may apply to a shared session (e.g., a precepted clinic where multiple residents attend). If one resident's cancel rule fires but another's doesn't, what happens to the session slot? Is it canceled for one and not the other? The proposal only discusses per-resident suppression.

6. **Coordinator notification or audit trail for suppressed sessions is not mentioned.** Given the ACGME compliance stakes described later in the doc, coordinators need visibility into which sessions were suppressed by rules vs. which were manually deleted. There's no mention of a cancel rule activity log or suppression report.

7. **The "Swing is staffed only if an NP is on Day Call" case is noted and immediately dropped.** The proposal flags this as out of scope for "future scope" but doesn't create a tracked deferral or explain what coordinators currently do when this pattern exists in Next. It's a real scenario from a named reviewer and deserves a disposition, not a footnote.

8. **Migration path for existing workaround services is not addressed.** Programs like ARMC with 316 block/clinic services built around the per-week workaround — what's the migration path? Does implementing 4-week cadence automatically collapse these? Is there a migration script? A coordinator workflow to consolidate? The proposal describes the problem (service proliferation table) but says nothing about remediation.

---

## Problem Framing Issues

The proposal frames this as two parallel features (4-week cadence + cancel clinic rules) bundled because they share a Jira epic and a ship date. That's a project management framing, not a product framing. The connection between them is never argued — why must these ship together? A coordinator who needs 4-week cadence doesn't necessarily need cancel clinic rules, and vice versa.

More substantively: the proposal spends considerable energy on the ACGME compliance angle, but this reframes the product from "scheduling convenience" to "compliance infrastructure." That's a much stronger justification — but it also raises the bar. If incorrect template generation creates ACGME citation risk, then the stale template bug (AMIONMGR-3223) being "out of scope" becomes harder to defend. The proposal uses compliance stakes to justify urgency while simultaneously deferring the compliance-affecting bug. That's inconsistent and a reviewer or executive will notice it.

The "ambulatory scheduling — non-weekly cadence patterns" example (1st and 3rd Monday, 5th Friday) is included in the real examples section but is explicitly not covered by this proposal. Including out-of-scope examples in the problem section inflates the apparent problem size without committing to solve it.

---

## Unstated Risks / Dependencies

1. **Engineering has not signed off on "schema extension, not new model."** This is stated as a design decision, but if it's wrong — if the 4-week cadence requires a new model — the scope and timeline both change. There's no reference to a spike, ADR, or engineering validation of this claim.

2. **Classic cancel rule semantics are not documented.** The proposal relies on "Classic equivalent" as a correctness anchor but doesn't document how Classic rules actually evaluated. If Classic used render-time evaluation and Next uses generation-time (or vice versa), coordinators will experience behavioral differences they weren't told about, during migration.

3. **Call schedule finalization dependency creates a chicken-and-egg problem.** The proposal states: "Cancel clinic rules can only be validated after call/shift assignments exist." In practice, coordinators often build clinic templates before the call schedule is finalized. This means cancel rules will be defined but untestable for weeks or months, increasing the risk of misconfiguration discovered late.

4. **AY rollover carry-forward is a live dependency, not a design decision.** The proposal says this "must be explicitly designed" but includes it in the Key Design Decisions section as though it's resolved. If this isn't implemented before M2 ship, coordinators will lose templates at year rollover and face re-setup burden — directly contradicting the Classic behavior promise.

5. **The CP-SAT autoscheduler dependency is understated.** The proposal notes that 4-week cadence and cancel clinic rules are "inputs to the future CP-SAT constraint solver" and a "prerequisite." If CP-SAT is a committed roadmap item, any schema decision made here that proves incompatible with CP-SAT's constraint model creates rework. There's no mention of CP-SAT requirements being consulted in the design of this schema extension.

6. **No mention of performance implications.** Programs like UCHealth (2,101 services) and LCMC (1,233) are in the client table. If cancel rules are evaluated at render-time, query complexity against these schedules is a real concern. If generation-time, session record volume increases. Neither is analyzed.

---

## Thin Rationale

**"Cancel rules suppress, don't delete"** — The distinction is stated as a decision but the rationale is one sentence. Why is suppression the right model rather