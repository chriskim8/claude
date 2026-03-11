# Bug: [Short Description]

**Type:** Bug
**Priority:** P0 / P1 / P2 / P3
**Reporter:** Chris Kim
**Assignee:** [TBD]
**Sprint:** [TBD]
**Related story/epic:** [link if applicable]

---

## Client Context

[Who reported this, where they found it, and what they said. Include the specific page path (e.g., Settings → Integrations → Epic → Provider Care Team tab). Quote the user directly if available. Note if a workaround was confirmed (e.g., Google Sheets export works, Excel does not).]

> "[Verbatim quote from customer or CS]" — [Name or role]

---

## Summary

[One sentence: what's broken and where. Be specific enough that someone reading this in a sprint list immediately understands the impact. If multiple surfaces are affected, list them.]

Affected paths (if code-level):
- `app/path/to/file.rb` — [what it affects]
- `app/path/to/other_file.rb` — [what it affects]

---

## Steps to Reproduce

1. [First action — include user role, environment, and any required preconditions]
2. [Second action]
3. [Third action]
4. Observe: [exact error message, behavior, or symptom — quote error copy verbatim]

---

## Root Cause

[Technical explanation of why this happens. Include the specific file + line number, what the code does, and why it produces the wrong result. Written for an engineer who hasn't seen this code before.]

---

## Affected Files & Fix

[For each file, show the before/after. Use code blocks. If the fix is a one-liner, say so explicitly.]

**`path/to/file.rb:line`**
```ruby
# Before
[current code]

# After
[proposed fix]
```

---

## Acceptance Criteria

- Given [a user uploads / performs the action that previously failed], then [it succeeds with no errors]
- Given [the fix is applied], then [existing working behavior is unaffected — no regression]
- Given [specific surface — e.g., staff import, Epic PCT import], then [expected outcome per surface]

---

## Impact

- **Severity:** P0 (data loss / outage) / P1 (major feature broken) / P2 (workaround exists) / P3 (minor / cosmetic)
- **Frequency:** Always / Intermittent / Rare
- **Scope:** [Who is affected — e.g., "All customers using Excel to prepare import files"]
- **Failure mode:** [How it fails — silently, with an error, data corruption, etc.]

---

## Workaround

[What customers can do right now until the fix ships. Be specific. If no workaround exists, say so.]

---

## Evidence

[Screenshots, Loom, Sentry links, logs, network traces. More here = faster resolution.]

---

## Additional Notes

[Suspected cause, recent deploy that might be related, related tickets, or implementation notes. Link to the original story if this is a regression.]