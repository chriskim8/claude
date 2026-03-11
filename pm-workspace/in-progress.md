# In-Progress Work Manifest

_Nightly review agent reads this file and runs Claude API review on each artifact._
_Format: each entry has a type, file path, and brief context so the reviewer knows what to look for._
_Remove entries when work is done. Add new entries as you start new work._

---

## Active Items

### Clinic Template Expansion — UX Prototype
- **Type:** ux-prototype
- **File:** `/Users/chriskim/pm-workspace/active/clinic-ux-prototype/index.html`
- **Context:** UX prototype for 4-week block cadence template + cancel clinic rules. Real examples: ARMC 4-week FMI block, Aline monthly anchor pattern, 140 manual deletions/month problem. Key constraint: cancel rules must not add visual row noise.
- **Review focus:** Is the interaction model clear? Are edge cases represented? Does it handle the ARMC 4-week pattern correctly? Is the cancel rules UI intuitive without adding clutter?
- **Jira:** AMIONMGR-3295 (M2), AMIONMGR-3307 (M2b)
- **Proposal:** https://docs.google.com/document/d/1_FmsFlppKNhrHxEZE2LE1OIghwEHBOTzUxRcanLgFks/edit

### Cancel Clinic Rules — Design Spec
- **Type:** proposal
- **File:** `/Users/chriskim/notes/residency/proposals/clinic-template-expansion.md`
- **Context:** Cancel clinic rules: simple (on-call/post-call) and advanced (by block service, by staff type, by assignment type). Must ship with M2. Classic equivalent: Cancel Clinic checkboxes in Preferences.
- **Review focus:** Is the scope clear? Are the rule types well-defined? What edge cases are missing? Is the dependency on M2 correctly stated? Are there unstated assumptions about how Classic cancel rules worked?
- **Jira:** AMIONMGR-3307

### Call & Shift Patterns — Proposal
- **Type:** proposal
- **File:** `/Users/chriskim/notes/residency/proposals/call-shift-patterns.md`
- **Context:** Pattern-based schedule generation — SequenceRule engine (N-in-a-row, cascade, rest enforcement). ACGME duty hour constraints. Three tools must ship together.
- **Review focus:** Is the ACGME constraint coverage complete? Are the specialty call structures correctly documented? What migration blockers are understated?
- **Jira:** AMIONMGR-3296

---

## Review Output Location

Revised versions saved to: `~/pm-workspace/active/overnight-reviews/YYYY-MM-DD/`
Each review creates: `{artifact-slug}-before.md`, `{artifact-slug}-after.md`, `{artifact-slug}-changes.md`
