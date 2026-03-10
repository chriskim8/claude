# Design: PM Morning Brief System
**Date:** 2026-03-08
**Owner:** Chris Kim
**Status:** Approved — ready for implementation

---

## Problem

Chris needs a daily operational brief as a PM on Amion Next. Without it, each morning requires manually checking Jira, Slack threads, Canny, and open decisions — losing 20–30 minutes before any real work begins. Key inputs (Slack threads needing replies, integration tickets raised by Amanda Roberts and Sebastian DeLuca, residency planning status, open PM decisions) are scattered across systems.

---

## Approved Architecture

**Option A: Shell script + crontab + SessionStart hook**

Three components:
1. **`~/pm-workspace/scripts/nightly_brief.py`** — Python script, runs nightly at 9:47pm via macOS crontab
2. **`~/pm-workspace/morning-brief.md`** — output file, overwritten each run
3. **Claude Code `SessionStart` hook** — injects `morning-brief.md` into context + triggers live Glean/Slack pull

```
nightly (9:47pm)                    morning (session open)
────────────────                    ──────────────────────
crontab → nightly_brief.py          SessionStart hook reads morning-brief.md
  ├── Jira REST API                 Claude auto-runs Glean search for:
  ├── Canny API                       - Slack threads needing reply
  ├── Snowflake (tier SQL)             - Amanda Roberts + Sebastian DeLuca
  └── local ADR files                 - Integration-related posts
  → writes morning-brief.md
```

---

## Morning Brief Sections

| # | Section | Source | When |
|---|---------|--------|------|
| 1 | Overnight Jira Activity | Jira REST API | Nightly script |
| 2 | Active Queue (top 5 prioritized) | Jira REST API | Nightly script |
| 3 | Integration Triage Inbox | Jira + Canny API | Nightly script |
| 4 | Residency Planning Status | Jira REST API | Nightly script |
| 5 | Residency Tier API Comparisons | Snowflake | Nightly script |
| 6 | Open Decisions (ADR Inbox) | `decisions/open-decisions.md` | Nightly script |
| 7 | Recent Decisions (last 5) | `decisions/adr-log.md` | Nightly script |
| 8 | Slack Follow-ups / Needs Reply | Glean MCP | Live at session open |

---

## File Structure

```
~/pm-workspace/
  scripts/
    nightly_brief.py          ← main nightly script
  decisions/
    adr-log.md                ← running decision log (Chris + Claude maintain)
    open-decisions.md         ← inbox of pending decisions
  morning-brief.md            ← generated output (overwritten nightly)
```

---

## Nightly Script Logic

### 1. Jira — Overnight Activity
- Query: tickets in AMIONMGR updated in last 24h where assignee = Chris OR watcher = Chris
- Surface: status changes, new comments, new assignments
- Credentials: `~/.config/.jira/credentials`

### 2. Jira — Active Queue
- Query: AMIONMGR assigned to Chris, status not Done/Closed, ORDER BY priority ASC, limit 10
- Format: key | summary | status | priority

### 3. Integration Triage Inbox
**Jira:** tickets with labels or summary containing "integration", "ADP", or "API" updated in last 7 days
**Canny:** posts from `~/canny/canny_client.py` — search boards for integration-related posts, surface new votes/posts
- Credentials: `~/canny/credentials/api_key`

### 4. Residency Planning Status
- Query: AMIONMGR tickets in epic AMIONMGR-3293 or AMIONMGR-3292, status not Done
- Surface: ticket key, summary, status, assignee

### 5. Residency Tier API Comparisons
- Run: `snow sql --connection doximity --format json -f ~/pm-workspace/active/residency-tier1-access-codes.sql`
- Format output as summary table in brief

### 6 & 7. ADR Files
- Read `decisions/open-decisions.md` verbatim into brief
- Read last 5 entries from `decisions/adr-log.md`

---

## ADR File Formats

### `open-decisions.md`
```markdown
## [Decision Title]
- **Context:** what's driving this
- **Options:** A, B, C
- **Who's involved:** names
- **Deadline:** date or "no deadline"
- **Added:** YYYY-MM-DD
```

### `adr-log.md`
```markdown
## [YYYY-MM-DD] [Decision Title]
- **Decision:** what was decided
- **Rationale:** why
- **Alternatives rejected:** and why
- **Downside accepted:** known tradeoffs
```

---

## SessionStart Hook

Add to `~/.claude/settings.json` hooks:
```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "cat ~/pm-workspace/morning-brief.md 2>/dev/null || echo 'No morning brief yet — run ~/pm-workspace/scripts/nightly_brief.py to generate.'",
        "async": false
      }]
    }]
  }
}
```

After injecting the brief, Claude's first action is to search Glean for:
- Slack threads from the last 48h where Chris was mentioned or replied
- Messages from Amanda Roberts and Sebastian DeLuca
- Any integration-related Slack posts
- Flag threads with no reply from Chris as "Needs Reply"

---

## Crontab Entry

```
47 21 * * * /usr/bin/python3 /Users/chriskim/pm-workspace/scripts/nightly_brief.py >> /tmp/nightly-brief.log 2>&1
```

---

## Credentials Used

| Service | Location |
|---------|----------|
| Jira | `~/.config/.jira/credentials` |
| Canny | `~/canny/credentials/api_key` |
| Snowflake | `~/.snowflake/config.toml` (connection: doximity) |
| Glean | MCP (session only, not available to shell script) |

---

## Out of Scope

- Direct Slack API integration (Glean covers Slack search; direct API not configured)
- Google Docs activity (not a daily operational need)
- Push notifications / desktop alerts
- Historical brief archive (overwrite-only for now)
