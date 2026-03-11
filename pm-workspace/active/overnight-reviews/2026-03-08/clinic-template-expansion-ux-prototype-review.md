# Overnight Review: Clinic Template Expansion — UX Prototype

Date: 2026-03-08
Source: /Users/chriskim/pm-workspace/active/clinic-ux-prototype/index.html

---

## Critical Issues

1. **The 4-week cycle table has no anchor date mechanism.** The ARMC pattern depends on knowing *which* real-world week maps to Week 1. The prototype shows a 4-row grid with no way to set or display the cycle start date. If a scheduler opens this in March for a template that started in October, they have zero way to verify alignment. The "Week 1 = Oct 7" anchor must be an explicit, editable field — not an assumption baked into the data model.

2. **Cancel rules have no conflict resolution or hierarchy UI.** The prototype promises cancel rules won't add row noise, but it doesn't show what happens when a cancel rule fires against an already-modified session (e.g., someone manually changed Thursday Week 2 to PM, and the cancel rule says "cancel all Week 2 Thursdays"). Which wins? There's no override indicator, no "rule suppressed" state, and no audit trail. The 140-manual-deletions problem gets replaced by 140-silent-conflict problems.

3. **The scope selector ("Apply to") is positioned at the top but its consequence is enormous and irreversible.** Changing scope from "This occurrence" to "All future" on a 4-week cadence template could rewrite months of schedule. There's no confirmation step, no preview of affected dates, and no inline count ("affects 23 sessions"). This is a destructive action dressed as a toggle.

---

## Missing Edge Cases

1. **Mid-cycle edit.** What happens when a scheduler edits the template starting Week 3 of an active cycle? Does Week 1 re-anchor to the edit date, or does the existing cycle continue and the new pattern starts at the next Week 1? Not represented at all.

2. **Holiday collision.** The cancel rules UI presumably handles "cancel if holiday," but the prototype doesn't show the state where a recurring session lands on a holiday *and* a manual override exists. Which label wins in the calendar chip — `ch-cancel` or `ch-amber`?

3. **Partial-week cycle start.** If the anchor date falls on a Wednesday but the template has Monday sessions in Week 1, those Monday slots are orphaned for the first cycle. The prototype has no truncated-first-cycle state.

4. **Zero sessions selected in the cycle table.** A user can click off all cells. The session summary presumably goes to "0 sessions/4 weeks" — is Save blocked? Is there a validation error? Not shown.

5. **Provider with multiple concurrent templates.** Aline's monthly anchor pattern stacked on top of a weekly AM clinic — the calendar view doesn't show what the chip rendering looks like when two rules generate conflicting sessions on the same cell.

---

## Unstated Assumptions

1. **Assumes schedulers understand "Week 1–4" as abstract cycle positions**, not calendar weeks. Most users think in terms of "first Monday of the month." These are different mental models and the prototype never bridges them.

2. **Assumes the cycle table is the right representation for all 4-week patterns.** The ARMC FMI block may be the only use case that needs a true 4-week grid. Weekly-with-exceptions (Aline) may be better served by the weekly pattern plus cancel rules, but the prototype doesn't make this decision explicit or justify it.

3. **Assumes cancel rules are additive and non-overlapping.** The UI implies you add rules and they stack cleanly. No assumption surfaced about rule ordering, precedence, or what "cancel" means when the session was already manually deleted (idempotent? error?).

4. **Assumes the chip visual language (`ch-cancel`, `ch-amber`) is already understood by schedulers.** The calendar view uses these without a legend. New users have no decoding path.

---

## Specific Improvements

1. **Add an explicit "Cycle starts on" date field directly in the 4-week table header**, formatted as "Week 1 begins: [date picker]" with a note showing the next computed Week 1 ("Next: Jan 6, 2025"). Make it editable inline. This single field eliminates the anchor ambiguity.

2. **Replace the scope toggle with a scoped confirmation sheet.** When the user clicks Save with scope = "All future," slide in a summary panel showing: "This will update 23 sessions from Jan 6 onward. 3 manually edited sessions will be overwritten. [Review list] [Confirm] [Cancel]." This is not an extra screen — it's a confirmation state within the existing modal.

3. **Add a "rule preview" column to the cancel rules UI.** Next to each cancel rule row, show the next 3 affected dates inline ("Cancels: Jan 6, Feb 3, Mar 3"). No extra modal — just small muted text. This lets schedulers immediately validate the rule fires on the right dates without leaving the form.

4. **Add a zero-state validation to the cycle table.** When all cells are deselected, disable the Save button and show inline text below the table: "Select at least one session to save this template." Don't wait for form submission.

5. **Put a chip legend as a collapsed "?" tooltip** anchored to the calendar section header, not a separate doc link. One click shows the four chip types with examples. Removes the assumption that users know the visual language.

---

## What's Working

1. **The cycle table's grid layout correctly externalizes the mental model** — showing weeks as rows and weekdays as columns makes the ARMC pattern (e.g., Tuesday Week 1 + Thursday Week 3) directly manipulable rather than requiring users to construct it from a recurrence formula. This is the right abstraction.

2. **Keeping cancel rules out of the row structure** (per the constraint) is the right call — surfacing them as a secondary layer rather than inline rows avoids the visual noise problem that plagues exception-heavy repeat UIs.