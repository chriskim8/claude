# Common Rules

## Never Invent (stop and ask instead)

Do NOT fabricate or guess the following. If unknown, STOP and ask clarifying questions instead.

- Jira project keys or issue numbers
- Experiment results, A/B test winners, or metric baselines
- Stakeholder names, team assignments, or approval chains
- Launch dates, roadmap timelines, or sprint commitments
- System behavior, API contracts, or technical constraints

If you don't know, say: _"I don't have this information — can you provide it, or should I search Glean/GitHub?"_

## Use Placeholders for Unknowns

When information is missing, use `[TBD]` inline and include an **Assumptions** block at the bottom of the artifact listing everything that was assumed or left blank.

Example:
> **Launch date:** [TBD]
> **Assumptions:** Launch date unknown — flagged for PM confirmation.

## Cite or Label as Hypothesis

For any factual claim, do one of the following:

1. **Include a source link** — Glean URL, GitHub PR/issue URL, or Jira ticket ID
2. **Label as hypothesis with confidence level** — e.g., _"Hypothesis (medium confidence): users drop off at the Preview step based on CS anecdotes — not yet validated with data."_
3. **Mark as unknown** — `[TBD — check with X]` where X is the person or system that would have the answer
