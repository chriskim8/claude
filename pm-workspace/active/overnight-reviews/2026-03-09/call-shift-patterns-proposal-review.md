# Overnight Review: Call & Shift Patterns — Proposal

Date: 2026-03-09
Source: /Users/chriskim/notes/residency/proposals/call-shift-patterns.md

---

## Weakest Assumptions

1. **"STI extension, no new table required"** — This is asserted, not demonstrated. STI works cleanly when subtypes share schema shape. CallShiftPattern (date-range cadence) and SequenceRule (per-assignment trigger with multi-step chaining) have fundamentally different data shapes. Cramming both into `ManagerRule` + `ManagerRuleCondition` without schema changes is an engineering assumption that Open Question #3 explicitly hasn't resolved yet. This is listed as a design decision while simultaneously flagged as an open question — that's contradictory.

2. **"On-demand resolution avoids two-way sync problems"** — Taken as obviously correct, but it introduces a different class of problem: render-time performance at scale. A coordinator with 40 residents across 6 services, each with overlapping CallShiftPatterns and SequenceRules that chain, will hit this at export or schedule view load. No latency budget, no caching strategy, no degradation path is described. The assumption that lazy resolution is uniformly better than generation-at-save is not defended against the ClinicTemplate precedent (ADR-006) that apparently went the other direction.

3. **"Pattern generation must be aware of existing assignments to skip generating on required rest days"** — The proposal states this as a requirement but the conflict detection section says violations are "flagged visually" rather than prevented. These are in direct tension. If a rest-period violation is flagged but still placed, ACGME compliance risk remains. The assumption that "flagging is sufficient" for regulatory enforcement is never examined.

4. **"The form and the conversational interface both write to the same JSON descriptor model, so no rework is required when the form is replaced"** — The JSON descriptor model is never specified. There's no schema, no example payload, no field list. The claim that this future-proofs the conversational interface is circular — you can't validate compatibility with a spec that doesn't exist yet.

5. **"These are confirmed scenarios from Arrowhead, Christopher Fahlsing's EM program, and Aline Campbell's Amion Next review"** — Fahlsing's quote is about schedule build time (pain is real), but it doesn't confirm that CallShiftPattern as designed solves his problem. EM programs use shift-based patterns, which the proposal notes are "different scheduling models" — yet the EM pattern type support is explicitly deferred to Advanced tier via anonymous multi-row templates. Fahlsing may remain unblocked by this proposal.

6. **"PGY-1 restrictions — specific committees may impose stricter limits"** — This is acknowledged and then dropped. No mechanism exists in the pattern engine to enforce specialty-specific or institution-specific PGY-1 overrides. Flagging it without designing for it means programs with the most restrictive duty hour requirements (many IM and Surgery programs) get incomplete compliance coverage.

---

## Scope Gaps

1. **Home call is not addressed.** ACGME explicitly distinguishes in-house call from home call (beeper/phone call). The "one day free per seven" rule applies differently depending on call type, and home call hours count toward the 80-hour cap only if the resident is called in. The pattern engine has no call type field, so it cannot correctly model or flag violations for programs that mix in-house and home call — which includes most community IM and Family Medicine programs.

2. **Moonlighting is absent.** ACGME requires moonlighting hours to be counted toward the 80-hour weekly limit. Programs where residents moonlight need patterns that account for those hours. No mention of this anywhere.

3. **Multi-block rotation transitions.** When a resident rotates from a night float block to a day rotation, the rest requirements at the handoff boundary must be respected. A SequenceRule that enforces rest within a block does not handle the transition between blocks managed by different patterns or manual entries. This is a real violation source.

4. **Post-call day assignment collision.** If a coordinator manually assigns someone to a clinic or educational session the day after a 24-hour call, and a SequenceRule is flagging that day as a rest day, who wins? The conflict detection model says "flag, don't overwrite" — but for ACGME purposes the manual assignment is the violation. The proposal has no resolution hierarchy.

5. **Shared-call pools and float coverage.** Several specialty structures (Surgery backup call, EM float shifts) involve a pool of residents where any one of them may be assigned. The pattern engine only supports staff-type-level assignment, not pool/lottery selection logic. This is a gap for programs that assign "whoever is available from the pool."

6. **Emergency Medicine's shift pattern support is deferred but listed as a confirmed use case.** Fahlsing (EM, 40 residents) is cited as evidence of the problem. EM requires shift-based patterns, which are labeled out-of-scope for Q2 (Advanced tier, anonymous multi-row templates). The proposal uses his quote to justify urgency but doesn't ship what he needs. This should be explicit, not buried in the Out of Scope section.

7. **Academic year rollover.** A pattern defined "July through June" — what happens at rollover? Does the coordinator recreate it? Does it auto-extend? Does it need to be associated with the academic year object? The proposal says patterns "persist across academic years" but provides no mechanism.

8. **Pediatric subspecialty and fellowship structures** are entirely absent from the specialty table. Fellowships frequently have idiosyncratic ACGME requirements and are a meaningful segment of the coordinator base.

---

## Problem Framing Issues

The proposal frames this primarily as a **coordinator efficiency problem** ("20–40 hours per block build") but the ACGME section frames it as a **compliance problem**. These require different success criteria and possibly different solutions.

If this is an efficiency play, the right measure is time-to-schedule and coordinator NPS. If it's a compliance play, the right measure is violation detection rate and downstream audit outcomes. The proposal doesn't commit to either. This matters because the flagging-vs-preventing tension (see Assumption #3) gets resolved differently depending on which frame wins.

There's also a hidden third frame: **migration unblocking**. Arrowhead was routed back to Classic because the system couldn't handle 7-on/7-off. That's a revenue/retention problem, not an efficiency or compliance problem. Three different problem frames producing one feature set is a scope-creep risk disguised as coherence.

---

## Unstated Risks / Dependencies

1. **Classic pattern inventory audit is a hard dependency for the enum, and the spike hasn't happened.** The `pattern_type` enum is listed as "pending Classic inventory audit in spike." If that audit surfaces pattern types that don't fit the CallShiftPattern or SequenceRule shapes — and it likely will, given Classic's age and organic growth — the data model may need redesign mid-sprint.

2. **AMIONMGR-3315 (tallies and duty hour enforcement) is listed as blocked until patterns ship.** That means the ACGME flagging described in this proposal is not full compliance enforcement — it's visual conflict marking with no tally backend. The proposal implies ACGME compliance support without disclosing that the enforcement layer (3315) is a separate, later delivery.

3. **Engineering has not confirmed the STI approach.** Open Question #1 (generation model) and Open Question #3 (has_many :result_conditions) are both unresolved. These are architecture questions, not preference questions. Shipping a PRD with two unresolved architectural questions as "open" rather than gated is a timeline risk.

4. **The design audit (AMIONMGR-3296) is listed as a prerequisite for the form UI phase.** If Tim/Brandon's audit requires significant changes to the rule builder interaction model, the form UI described here may be rebuilt before it ships. The proposal underweights this risk.

5. **No mention of how patterns interact with existing manual entries during initial setup.** A coordinator migrating from Classic has an existing hand-built schedule. When they define a CallShiftPattern over a date range that already has manual assignments, the conflict detection behavior at migration time is undefined.

6. **Conversational interface dependency on the LLM or NLP layer is entirely unaddressed.** The proposal asserts the JSON descriptor is the "permanent investment" that enables the conversational interface, but doesn't identify what parses "Q4 overnight call for PGY-2s on Night Float starting July 1" into that descriptor. If that requires a fine-tuned model or significant prompt engineering work, the framing that "no rework is required" is misleading.

---