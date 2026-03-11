# Overnight Review: Clinic Template Expansion — UX Prototype

Date: 2026-03-09
Source: /Users/chriskim/pm-workspace/active/clinic-ux-prototype/index.html

---

## Critical Issues

1. **The 4-week cycle table has no clear "anchor date" input.** The ARMC FMI pattern requires knowing *which real calendar week* is "Week 1." Without this, the table is meaningless — a provider clicking cells has no way to know if Week 1 maps to the first Monday of the month, the block start date, or something else. This is the core of the 140-deletion problem and the prototype doesn't solve it. You need a visible, editable "Cycle starts on: [date]" field above the table, with a plain-language preview like "Next Week 1: Oct 6, 2025."

2. **Cancel rules have no defined trigger surface.** The brief says cancel rules must not add visual row noise, but the prototype doesn't show *how* a user discovers, opens, or edits a cancel rule for an existing repeating assignment. There's no affordance on the schedule view — no icon, no secondary action on the chip, nothing. The constraint (no clutter) has eaten the discoverability entirely. Pick one: a collapse-inline chevron on the assignment row, or a dedicated "Exceptions" link in the repeat modal footer. Show it.

3. **Scope selector ("Apply to") is positioned wrong and its consequences aren't shown.** Moving scope to the top sounds logical, but "This assignment only / This and following / All assignments" is a *destructive-consequence* decision that should appear at *save time*, not at form-open time. A user who sets up a complex 4-week pattern and then realizes scope was defaulted to "This only" has wasted all that work. Worse, the prototype shows no confirmation state, no diff preview, no count of affected sessions. At minimum, the save button label should reflect scope: "Save 47 sessions" vs. "Save this session."

---

## Missing Edge Cases

1. **Block boundary crossing.** What happens when a 4-week cycle straddles two academic blocks (e.g., cycle Week 3–4 falls in the next rotation block)? Does the template auto-truncate? Error? Continue into the new block silently? This is exactly the ARMC scenario and it's unaddressed.

2. **Cycle drift after a manual edit.** If a scheduler manually deletes one instance mid-cycle (the current 140/month behavior), does the cycle re-anchor from that deletion, skip it and continue, or flag a conflict? The prototype shows no "exception" state in the 4-week table cells.

3. **Aline monthly anchor pattern vs. 4-week pattern collision.** These are not the same thing — 4 weeks ≠ 1 month. If a provider has both patterns applied, which wins in week 5 of a 5-week month? No handling shown.

4. **Empty cycle (no cells selected).** User opens the 4-week table, selects nothing, hits Save. What happens? No validation state shown.

5. **Single-day providers.** A provider who only works Fridays — does the 4-week table still render all 5 weekday columns? That's visual waste and implies false optionality.

---

## Unstated Assumptions

1. **Assumes the cycle table rows map to "weeks within the block," not calendar weeks.** This needs to be explicit in the UI label. "Week 1" is ambiguous — is it the first week of the rotation block, the first week of the month, or the first week after the anchor date?

2. **Assumes all recurrence patterns fit Mon–Fri.** The table only shows 5 columns. Weekend clinics are excluded with no explanation or fallback.

3. **Assumes cancel rules are additive exceptions, not replacement rules.** The prototype doesn't clarify whether a cancel rule voids one instance, shifts it, or flags it for manual review. The system behavior has to be defined before the UI can be correct.

4. **Assumes providers operate in a single timezone.** Not stated but relevant for any date anchor logic, especially for health systems spanning time zones.

5. **Assumes the "140 manual deletions" problem is caused by lack of a 4-week cadence template, not by downstream workflow issues** (e.g., approvals, EHR sync). If schedulers are deleting manually for *other* reasons, this entire prototype solves the wrong thing.

---

## Specific Improvements

1. **Add a cycle anchor field with a live plain-language preview.** Directly above the 4-week table, add: `Cycle starts: [date picker] → "Week 1 = Oct 6 · Week 2 = Oct 13 · …"` Update the column date hints in real time. This is the single most important piece of information and it's absent.

2. **Add a cell-level exception state to the cycle table.** Cells need three states, not two: Off (empty), On (filled), and Cancelled-this-instance (strikethrough or `—`). Right now there's no way to express "Week 2 Tuesday is normally on but is cancelled for this rotation." That's exactly the exception that generates manual deletions.

3. **Replace the generic Save button with a contextual action label.** "Save 23 sessions across 4 providers" makes the scope concrete and forces the user to confront consequences before confirming. Add a secondary link: "Preview affected dates" that expands an inline list — no new screen needed.

4. **Show a cancel rule inline as a collapsed sub-row, not a separate UI section.** Under any `is-on` cell in the 4-week table, allow a right-click or long-press (desktop: hover menu) to add an exception: "Cancel if [holiday] / [block off-service] / [custom date range]." Render it as a `—` in the cell with a tooltip. This directly addresses the no-row-noise constraint without hiding the feature entirely.

5. **Add a "Matches X existing sessions" reconciliation notice** when the repeat rule is saved over a date range that already has manual entries. Don't silently overwrite. Show: "3 sessions already exist in this range — keep manual entries or replace with template?"

---

## What's Working

1. **The day-pill interaction model is clean and fast.** Toggle-on/off with clear selected state, compact footprint — this is the right pattern for day selection and should be extended to the 4-week table cells rather than replaced.

2. **Scope selector as a segmented control (not a dropdown or radio group) is the right call** — it keeps a high-consequence choice visible without a modal. The positioning issue is fixable; the control type itself is correct.