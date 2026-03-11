# Overnight Review: Call & Shift Patterns — Proposal

Date: 2026-03-08
Source: /Users/chriskim/notes/residency/proposals/call-shift-patterns.md

---

## Weakest Assumptions

1. **"STI extension, no new table required"** — This is stated as a design decision but has not been validated. The spike is listed as a *gate*, yet the proposal already commits to this architecture. If `ManagerRule` + `ManagerRuleCondition` cannot cleanly represent multi-step SequenceRule chains (the "Multiple-THEN architecture" is listed as an open question), you may need a new table anyway. The assumption that STI handles this is doing heavy lifting without engineering confirmation.

2. **"On-demand resolution, not generation-at-save"** — The proposal frames this as obviously superior, but ADR-006 (referenced in Open Questions) apparently went the other way for ClinicTemplate. The rationale for diverging from an existing ADR is not given. "Avoids two-way sync problems" is stated, not demonstrated — it may just relocate the complexity to render/export performance.

3. **"Pattern records are descriptors; assignments resolve lazily at render and export"** — If conflict detection also runs at render, you're running conflict logic every time a coordinator opens a view. At 40+ residents across overlapping rotations, this could be a render-blocking performance problem. No latency budget or caching strategy is mentioned.

4. **"The form UI is intentionally minimal — it will be superseded by conversational rule entry"** — The proposal treats NLP rule entry as near-certain future investment, but it's fully out of scope with no timeline. This is a common rationalization for shipping weak UI: "it's temporary." Temporary UI tends to become permanent. The assumption that the form will be replaced is not a design decision — it's a hope.

5. **"PGY-1 (intern) restrictions — specific committees may impose stricter limits"** — The ACGME coverage section acknowledges PGY-1 restrictions but does not define them, does not say how they'd be represented in the data model, and does not flag them as a scope gap. This reads as awareness-without-coverage masquerading as coverage.

6. **"These are confirmed scenarios from Arrowhead, Christopher Fahlsing's EM program, and Aline Campbell's review"** — Three sources, two of which involve the same internal reviewer (Aline Campbell appears in multiple examples). The sample is thin and concentrated. Arrowhead is a migration blocker example, not a pattern design validation. Fahlsing's quote is about scheduling time, not pattern requirements. The "confirmed" framing overstates the validation depth.

---

## Scope Gaps

1. **PGY-1 / intern-year restrictions are undefined.** The ACGME section explicitly says "specific committees may impose stricter limits in the first year" and stops there. This affects pattern generation for every first-year resident in every program. Either this is in scope (and the rules must be specifiable) or it's explicitly deferred — neither is stated.

2. **Home call is not modeled.** ACGME distinguishes in-house call (24-hour cap applies) from home call (different constraints). The "one day free per seven" rule mentioned applies specifically to home call scenarios. Home call appears nowhere in the `pattern_type` enum candidates or the specialty table. Many IM and Surgery programs use home call heavily.

3. **Moonlighting and leave interactions.** ACGME duty hour calculations include moonlighting hours. The 80-hour cap can be violated by moonlighting even when the schedule itself is clean. Pattern-generated hours plus moonlighting is a known audit risk. No mention of how patterns interact with leave blocks, either — a generated Q4 pattern over a vacation week produces a violation.

4. **Multi-resident conflict resolution is undefined.** The proposal says conflicts are "flagged visually — never silently overwritten." What happens when a SequenceRule cascade targets a slot already occupied by a manual entry? Who gets the slot? What does the coordinator see? The flag behavior is stated but not specified.

5. **Emergency Medicine shift patterns are listed in the specialty table but not in the `pattern_type` enum.** The enum candidates (Q-call, weekly, biweekly, alternate week, night float, custom) are Q-call-centric. The proposal says EM shift-based patterns are "first-class options" but doesn't define what those pattern types are. Fahlsing's program is cited as a key reference and he runs an EM program.

6. **Family Medicine continuity clinic interoperability.** The specialty table says "continuity must not be disrupted by call schedule — templates must interoperate." This is a cross-feature constraint (patterns + clinic templates) that is not mentioned in scope, not in out-of-scope, and not in open questions. It is simply dropped after being stated.

7. **Cascade chains with different services at each step** — the multi-service SequenceRule chain ("Friday Day Call → Saturday Day Call → Sunday Night Call" on potentially different services) is described as a requirement but the data model section only says `has_many :result_conditions` *needs engineering confirmation*. This is a core requirement left as an open question with no fallback position.

8. **No rollback or edit behavior for pattern-resolved assignments.** If a coordinator edits one resolved assignment, does it detach from the pattern? Does editing the pattern retroactively change prior assignments? The on-demand resolution model makes this ambiguous. Nothing is said about what happens to manual overrides within a pattern window.

9. **Academic year boundary handling.** Patterns have date ranges, but the proposal doesn't address what happens at July 1 rollover — the highest-stakes moment in GME scheduling. Do patterns carry over? Do they need to be re-created? Does PGY-1 status automatically change to PGY-2, affecting which pattern rules apply?

---

## Problem Framing Issues

The problem is framed as "schedulers hand-enter every assignment, no repeating patterns exist." This is real, but it conflates two distinct problems that may have different solutions and different ROI:

**Problem A: Pattern storage and re-application across academic years.** Fahlsing's 20–40 hours is about rebuilding from scratch annually. This is solved by saving and replaying a pattern descriptor — essentially a template. This is tractable.

**Problem B: ACGME constraint enforcement.** Rest enforcement, 80-hour caps, Q3 density limits. This is a compliance and liability problem, not just a scheduling overhead problem. The proposal folds this into pattern generation as a feature, but ACGME compliance enforcement is a meaningfully different scope with different stakeholders (GME offices, DIO, not just schedulers) and different risk profiles.

By bundling these, the proposal may be over-engineering the pattern feature (adding ACGME awareness to every generated assignment) while under-engineering the compliance problem (tallies and duty hour enforcement are explicitly out of scope in AMIONMGR-3315). You can't credibly say "rest enforcement is a regulatory requirement, not a preference" in the problem section and then exclude duty hour enforcement as out of scope without explaining the logic of the split. As written, the proposal catches *some* violations at generation time (rest day conflicts) but not others (80-hour cap, Q3 density), with no stated rationale for why those specific lines were drawn.

---

## Unstated Risks / Dependencies

1. **Classic pattern inventory audit is a hard prerequisite for `pattern_type` enum finalization, but it's scoped inside the spike, not before it.** If the Classic audit reveals pattern types that don't fit the proposed enum (e.g., irregular call cycles, "floating" call where no fixed interval exists), the enum may need to be redesigned before implementation. The spike is listed as a gate but its deliverables are underspecified.

2. **AMIONMGR-3308 spike has no stated timeline or owner.** It is described as the gate for all implementation work, but there is no indication of when it completes, who owns it, or what the decision criteria are for passing the gate. The proposal can't be scheduled without this.

3. **"Three tools must ship together"** is stated in the review context but not in the proposal.** What are the three tools? If CallShiftPattern, SequenceRule, and something else must ship atomically, that's a coordination dependency that should be explicit. If one of the three is delayed, does the whole release slip?

4. **Duty hour tallies (AMIONMGR-3315) are blocked on this work shipping.** But this proposal is also implicitly blocked by AMIONMGR-3315 in the other direction — without tallies, coordinators can't verify that pattern-generated schedules are actually compliant. Flagging a rest-day conflict at render time