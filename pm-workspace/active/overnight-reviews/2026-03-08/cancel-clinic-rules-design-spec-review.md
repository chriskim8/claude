# Overnight Review: Cancel Clinic Rules — Design Spec

Date: 2026-03-08
Source: /Users/chriskim/notes/residency/proposals/clinic-template-expansion.md

---

## Weakest Assumptions

1. **"No new model — extends existing schema"** — This is asserted without showing what `ResultRuleCondition.settings` currently looks like or what the extension cost actually is. "Schema extension" can be trivial or it can be a breaking change depending on how the field is typed and validated. This is load-bearing and completely undefended.

2. **"Templates persist year-to-year by default... The carry-forward behavior at AY rollover must be explicitly designed — the current implementation does not define this."** — The proposal simultaneously claims Classic parity as a selling point *and* admits the behavior isn't implemented. That's not a design decision, that's an unresolved gap being laundered as one.

3. **"Cancel rules suppress, don't delete"** — The distinction between suppression and deletion is stated as policy, but there's no description of what the data model looks like. Where is the suppression state stored? Is it on the session record? A separate override table? If it's on the session record generated at save time (per ADR-006), how does a render-time rule evaluation interact with it? This assumption hides significant implementation complexity.

4. **"Simple cancel: Apply to on-call only, or on-call + post-call / Apply to all staff types, or specific training levels only"** — This implies the system knows who is "on-call" vs. "post-call" at session-evaluation time. That requires the cancel rule engine to understand call schedule semantics (overnight = post-call the next morning). That's not a trivial dependency and it's not called out.

5. **"Classic equivalent: the Cancel Clinic checkboxes in Preferences"** — This is mentioned twice without any description of what Classic actually did. How did Classic define "post-call"? Was it assignment-type-based? Time-based? Did it handle overnight shifts crossing midnight correctly? Assuming behavioral parity without documenting Classic's actual logic is how you ship a broken migration.

6. **"Must ship with M2"** — This constraint appears in the framing context but not in the proposal body. There's no discussion of what M2 is, what it unlocks, or what breaks if this slips. A hard ship dependency this significant needs to be surfaced and defended in the doc itself.

---

## Scope Gaps

1. **Post-call definition is undefined.** If a resident has a 24-hour shift ending at 7am Tuesday, does Tuesday's clinic cancel? What about a 16-hour shift? What if they're on backup call and don't get called in? The proposal uses "post-call" as if it's a well-understood system concept. It may not be.

2. **Conflict between cancel rule and ACGME minimum is unresolved.** The regulatory section correctly identifies that canceled sessions can cause compliance gaps, and says "the reinstatement mechanism is not optional" — but the reinstatement UX, the mechanism for tracking it, and any warning system when cancellations push a resident below minimum are entirely unspecified. You've identified the risk and deferred the solution.

3. **4-week cycle anchor date is undefined.** If a 4-week template starts Week 1 on July 1, what happens when the AY rolls over? Does the cycle reset? Does it continue mid-cycle? What if a block assignment starts on a date that falls in the middle of a cycle? The "per-week day configuration" example doesn't address how the cycle origin is established or maintained.

4. **Overlapping cancel rules.** What happens when a simple cancel rule and an advanced cancel rule both fire on the same session? What's the precedence model? Can rules conflict (one says cancel, one implies active)?

5. **Partial-day sessions.** The proposal handles "Monday AM" and "Thursday PM" as session units, but cancel rules fire at the session level. If a resident is post-call and has two half-day sessions on the same day, do both cancel? Is there a way to cancel AM but not PM?

6. **The "conditional service activation" scenario (Swing/NP example) is noted as out of scope but given no disposition.** If this is a pattern Aline Campbell surfaced in a review, other programs likely have it too. Noting it without even a "tracked as future work in ticket X" is a gap.

7. **5th-week handling is deferred with no interim guidance.** Elizabeth Byrd requested this. What do coordinators do in the meantime — manual deletion? That's the exact manual burden this proposal claims to eliminate.

8. **Multi-resident templates.** The examples all describe per-resident session generation. What happens when multiple residents share a clinic slot (e.g., a clinic that requires exactly one resident present)? Can cancel rules fire on one without affecting the other?

---

## Problem Framing Issues

The proposal frames cancel clinic rules as solving "manual deletion burden" but the deeper problem for compliance-heavy programs is **session count integrity across the AY** — whether the right number of sessions exist, not just whether coordinators have to delete them manually. The manual deletion framing undersells the compliance risk and oversells the workflow relief. A coordinator who ignores manual deletions doesn't just have messy schedules — they have inaccurate ACGME data. That framing should lead the problem statement, not live in a separate regulatory section.

Additionally, the proposal bundles two substantially different features (4-week cadence and cancel clinic rules) into one proposal without a clear statement of whether they share implementation surface or are just co-shipped. If they're independent, they should be reviewable independently. If they're coupled (e.g., cancel rules depend on the session generation model introduced by 4-week cadence), that coupling needs to be explicit.

---

## Unstated Risks / Dependencies

1. **ADR-006 (generation-at-save) may be fundamentally incompatible with render-time cancel rule evaluation.** Open Question #1 acknowledges this trade-off but doesn't surface it as a risk to the proposal's architecture. If the decision goes render-time, the "schema extension, not new model" claim may collapse.

2. **Call schedule finalization dependency is a sequencing risk in practice.** The proposal notes that cancel rules "can only be validated after call/shift assignments exist." In reality, coordinators set up templates before call schedules are finalized. If rule validation is blocked, coordinators will apply templates, not set up cancel rules, forget, and have incorrect schedules at go-live. There's no workflow mitigation proposed.

3. **"Must ship with M2" is an unstated hard constraint** with no fallback. What's the consequence of partial delivery? Can 4-week cadence ship without cancel clinic rules? Can simple cancel ship without advanced cancel? The proposal doesn't define a shippable subset.

4. **Migration from Classic cancel rules is not addressed.** If existing Classic programs have cancel clinic configurations, how do they migrate? Manual re-entry? Automated mapping? This is a direct migration blocker for Intermediate-tier programs and it's not mentioned.

5. **The CP-SAT autoscheduler dependency is noted as future work but the constraint is one-way.** If this proposal ships with design decisions that are later incompatible with CP-SAT's input requirements, rework is expensive. There's no statement that CP-SAT's input spec has been reviewed against this design.

6. **The stale template bug (AMIONMGR-3223) is explicitly out of scope but the regulatory section says it "is a compliance prerequisite."** These two statements are in direct contradiction. If it's a compliance prerequisite, it cannot be out of scope without an explicit justification.

---

## Thin Rationale

- **"Two rule levels" (simple vs. advanced)** — The distinction is presented as obvious, but it's not clear why "by staff type" is Advanced rather than Simple. A coordinator who only wants to cancel clinic for PGY-1s on call nights is doing something conceptually simple. The simple/advanced split appears to mirror Classic's UI structure rather than reflecting actual complexity or user mental models. This needs justification or the structure needs to be reconsidered.

- **"Visual treatment for canceled sessions"** is listed as an open question, but this is not optional for launch. If canceled sessions aren't visually distinct, coordinators cannot audit whether rules are firing correctly, and the reinstatement workflow has no entry point. Leaving this open is leaving a launch-blocking UX decision unresolved while calling it an "open question."

- **The service proliferation table** is compelling evidence for 4-week cadence, but it's used to justify cancel clinic rules too, which it doesn't support. UCHealth's 2,101 services is a cadence problem, not a cancel rule problem. The evidence and the claim need to be separated.

- **"Composite