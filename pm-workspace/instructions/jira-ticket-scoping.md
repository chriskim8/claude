# Jira Ticket Scoping Rules

## The Core Principle

Each ticket's Acceptance Criteria must only verify what **that ticket builds**. Never bake downstream story behavior into an upstream story's ACs.

---

## Requirements vs. Acceptance Criteria

| Section | What belongs here |
|---------|------------------|
| **Requirements** | What this story is building. Can reference downstream stories for context (e.g., "the sign-off flow is built in AMIONMGR-3253") but should not describe that behavior in detail. |
| **Acceptance Criteria** | Only what an engineer, QA, or PM can verify by testing **this ticket in isolation**. If the AC requires a downstream story to be built first, it belongs in that story. |

---

## Common Scoping Mistakes

### Mistake 1: ACs that test downstream behavior

**Wrong** (in a settings story):
> Given 'Staff Only' is selected, then staff members are required to review and approve their hours via My Hours before export.

**Right** (in the settings story):
> Given a facility manager selects 'Staff Only' and saves, the setting persists for that schedule.

The downstream enforcement behavior (My Hours gate) belongs in the My Hours story's ACs.

---

### Mistake 2: Requirements that describe another story's implementation

**Wrong** (in a settings story):
> Staff Only — unlocks the My Hours page for staff to review and approve their hours for the pay period — including scheduled assignments and any submitted activations — before those rows are eligible for payroll export

**Right**:
> Staff Only — requires staff sign-off before rows are eligible for payroll export; the sign-off flow is built in AMIONMGR-3253

Keep the description brief and point to the story that owns the behavior.

---

### Mistake 3: Duplicate ACs across stories

If the same Given/Then appears in two tickets, one of them is wrong. Decide which story owns the verification and remove it from the other. Use a comment or reference link to explain why it was removed.

---

## Ticket Dependency Language

When a story's behavior depends on another story being built:

- In Requirements: `"the [X] flow is built in [AMIONMGR-XXXX]"`
- In ACs: do not write ACs that require the other story — instead, note the dependency: `"Behavior gated on AMIONMGR-XXXX"`
- In Background: describe the full flow for context, but be clear which parts this story owns

---

## Epic-Level Flow Tickets

For epics with multiple interconnected stories (e.g., a settings story → staff-facing story → admin-facing story), structure ACs like this:

| Story | AC scope |
|-------|---------|
| Settings story (e.g., 3252) | Dropdown exists, saves, applies retroactively |
| Staff-facing story (e.g., 3253) | Staff page visible, approve action works, CSV column populates |
| Admin-facing story (e.g., 3254) | Admin approval actions visible, undo works, CSV column populates |

Each story's ACs are independently testable. The settings story does not need to verify that the sign-off gate works — that's tested in the downstream stories.

---

## Checklist Before Finalizing ACs

- [ ] Can every AC be tested without building any story that comes after this one?
- [ ] Do any ACs reference behavior that lives on a different page or surface owned by another story?
- [ ] Are there duplicate ACs in related tickets that should be consolidated?
- [ ] Does each AC have a clear pass/fail condition that QA can verify?
