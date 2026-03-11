# Story: [Short Title]

**Type:** Story
**Epic:** [AMIONMGR-XXXX — Epic name]
**Priority:** P0 / P1 / P2 / P3
**Reporter:** Chris Kim
**Assignee:** [TBD]
**Sprint:** [TBD]

---

## Jira Format Reference

When pushing this ticket to Jira via the REST API, apply the following ADF structure exactly:

| Section | Heading level | Notes |
|---------|--------------|-------|
| Background | H1 | End with inlineCard chips for Product Proposal + Technical Proposal |
| User Story | H1 | Single paragraph, As a / I want / So that |
| Requirements | H1 | Nested bullet lists — group by feature area |
| Acceptance Criteria | H1 | Flat bullet list, Given/When/Then |
| Designs | H2 | Bullet: "Designs provided?" + Figma as hyperlink text. Bullet: "Design review needed?" Then embed Figma frames as inline PNGs using the Figma→Jira image pipeline (see Designs section below). |
| *(horizontal rule)* | — | `rule` node before Technical Notes |
| Technical Notes | H2 | Lead with inlineCard chip to tech proposal, then 1–3 targeted callouts |
| *(horizontal rule)* | — | `rule` node before Rollout & Sign-off |
| Rollout & Sign-off | H2 | Feature flag name, dependencies, CS comms needed |

**Link formatting:**
- Google Docs / Notion / Confluence → `inlineCard` chip (renders as a smart card in Jira)
- Figma → regular hyperlink text (e.g., label: "Figma", href: url)

**Do not include** as separate top-level sections: Non-Functional Requirements, API Information, Dox Analytics, Out of Scope. Fold relevant notes from those into Requirements or Technical Notes as needed.

---

# Background

[Why are we doing this? State the customer or business problem, who is blocked, and what this story unlocks. 2–4 sentences max.]

Product Proposal: [link — renders as inlineCard chip in Jira]
Technical Proposal: [link — renders as inlineCard chip in Jira]

---

# User Story

As a [Manager / Viewer / Admin / Doxer],
I want [capability or action],
So that [outcome or value delivered].

---

# Requirements

- [Group requirements by feature area using nested bullets]
  - [Sub-requirement or constraint]
  - [Sub-requirement or constraint]
- [Next feature area]
  - [Sub-requirement]

---

# Acceptance Criteria

- [ ] Given [context], when [action], then [expected outcome]
- [ ] Given [a Viewer / non-Manager], when [attempts the action], then [expected restriction or message]
- [ ] Given [schedule in X state — Sandbox / Preview / Staging / Done], when [action], then [expected behavior]
- [ ] Given [failure condition], when [action], then [user sees appropriate error, no data corruption]

---

## Designs

- **Designs provided?** [Figma](link) / No — [reason, e.g., internal tooling only in MVP]
- **Design review needed?** Yes / No

**Figma frames to embed** — list node IDs below; Claude will export as PNGs and embed them inline in this section when pushing to Jira:

| Node ID | Description |
|---------|-------------|
| `[e.g. 76-2653]` | [e.g., Settings UI — approval options] |
| `[e.g. 442-12426]` | [e.g., Reports view — approval flow] |

> Figma file key for ADP: `upJE6mbXBXFFftLTU65Fha`. For other files, specify the file key.
> Pipeline: Figma API `/v1/images/{file_key}?ids={node_ids}&format=png&scale=2` → upload to Jira attachments → extract media UUID from redirect → embed as `mediaSingle` ADF nodes.

---

## Technical Notes

Based on aligned technical approach in [Technical Proposal link — inlineCard chip in Jira].

[1–3 targeted callouts: key data model decisions, dependencies on other stories, known gotchas, or implementation constraints. Not a full spec — enough to unblock the engineer.]

---

## Rollout & Sign-off

Feature flag: `[flag_name]` / N/A

[Any timing constraints, pre-deployment CS/Sales comms needed, or special approvals. 1–3 bullets max. N/A if none.]
