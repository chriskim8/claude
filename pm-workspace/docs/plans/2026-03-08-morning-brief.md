# Morning Brief System — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a nightly Python script + SessionStart hook that delivers a full PM brief to Chris each morning when he opens Claude Code.

**Architecture:** A crontab-scheduled Python script pulls Jira, Canny, and Snowflake data nightly, runs a Claude API review agent on in-progress PM artifacts, and writes `~/pm-workspace/morning-brief.md`. A `SessionStart` hook injects that file into Claude's context, then Claude runs live Glean searches for Slack follow-ups. Two local markdown files (`open-decisions.md`, `adr-log.md`) power the ADR section.

**Tech Stack:** Python 3.9 (`/usr/bin/python3`), Jira REST API v3, Canny client (`~/canny/canny_client.py`), Snowflake CLI (`/opt/homebrew/bin/snow`), Anthropic Python SDK (`anthropic` 0.84), `DOX_ANTHROPIC_API_KEY` env var, macOS crontab, Claude Code `settings.json` hooks.

**Design doc:** `docs/plans/2026-03-08-morning-brief-design.md`

---

## Task 1: Directory structure + ADR seed files

**Files:**
- Create: `~/pm-workspace/scripts/` (directory)
- Create: `~/pm-workspace/decisions/open-decisions.md`
- Create: `~/pm-workspace/decisions/adr-log.md`

**Step 1: Create directories**

```bash
mkdir -p ~/pm-workspace/scripts
mkdir -p ~/pm-workspace/decisions
```

**Step 2: Create `open-decisions.md` with seed content**

```bash
cat > ~/pm-workspace/decisions/open-decisions.md << 'EOF'
# Open Decisions (ADR Inbox)

_Add decisions that need to be made. Claude will surface these each morning._
_Format: ## [Title], Context, Options, Who's involved, Deadline, Added date_

---

## Integration Ticket Prioritization (Amanda Roberts / Sebastian DeLuca)
- **Context:** Amanda and Sebastian have raised integration-related changes via Jira tickets, Canny posts, and Slack. Need to decide prioritization framework for the ADP integration epic.
- **Options:** A) Prioritize by customer impact score, B) Prioritize by engineering effort (lowest first), C) Group by integration type and tackle as batches
- **Who's involved:** Amanda Roberts, Sebastian DeLuca, Engineering lead
- **Deadline:** Before next sprint planning
- **Added:** 2026-03-08

## Steven Hibble — Data Estimation Sessions
- **Context:** Was in a thread with Steven Hibble. Need to decide whether to start inviting him to data estimation sessions.
- **Options:** A) Invite starting next sprint, B) Loop in after residency milestone, C) Ad-hoc invite only
- **Who's involved:** Steven Hibble
- **Deadline:** No hard deadline
- **Added:** 2026-03-08
EOF
```

**Step 3: Create `adr-log.md` with seed content**

```bash
cat > ~/pm-workspace/decisions/adr-log.md << 'EOF'
# Decision Log (ADR)

_Running record of PM decisions made. Most recent first._
_Format: ## [YYYY-MM-DD] [Title], Decision, Rationale, Alternatives rejected, Downside accepted_

---

EOF
```

**Step 4: Verify files exist**

```bash
ls ~/pm-workspace/decisions/
ls ~/pm-workspace/scripts/
```
Expected: `adr-log.md  open-decisions.md` and empty `scripts/`

---

## Task 2: Script skeleton — reads creds, writes brief header

**Files:**
- Create: `~/pm-workspace/scripts/nightly_brief.py`

**Step 1: Write the script skeleton**

```python
#!/usr/bin/env python3
"""
Nightly PM brief generator.
Runs via crontab at 9:47pm, writes ~/pm-workspace/morning-brief.md.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
HOME = Path.home()
PM_WORKSPACE = HOME / "pm-workspace"
BRIEF_PATH = PM_WORKSPACE / "morning-brief.md"
DECISIONS_DIR = PM_WORKSPACE / "decisions"
OPEN_DECISIONS_PATH = DECISIONS_DIR / "open-decisions.md"
ADR_LOG_PATH = DECISIONS_DIR / "adr-log.md"
SQL_PATH = PM_WORKSPACE / "active" / "residency-tier1-access-codes.sql"
CANNY_DIR = HOME / "canny"
SNOW_BIN = "/opt/homebrew/bin/snow"

# ── Jira credentials ───────────────────────────────────────────────────────
def _jira_creds():
    creds = {}
    creds_path = HOME / ".config/.jira/credentials"
    for line in creds_path.read_text().splitlines():
        if "=" in line:
            k, v = line.strip().split("=", 1)
            creds[k] = v
    return creds["JIRA_EMAIL"], creds["JIRA_TOKEN"], creds["JIRA_BASE_URL"]

JIRA_EMAIL, JIRA_TOKEN, JIRA_BASE_URL = _jira_creds()
JIRA_ACCOUNT_ID = "606a4958edc14f00766fcad5"

# ── Jira helper ────────────────────────────────────────────────────────────
import urllib.request
import base64

def jira_search(jql: str, fields: list[str], max_results: int = 20) -> list[dict]:
    """POST to /rest/api/3/search/jql and return issues list."""
    url = f"{JIRA_BASE_URL}/rest/api/3/search/jql"
    payload = json.dumps({
        "jql": jql,
        "fields": fields,
        "maxResults": max_results
    }).encode()
    token = base64.b64encode(f"{JIRA_EMAIL}:{JIRA_TOKEN}".encode()).decode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Basic {token}"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["issues"]


# ── Section builders (stubs — filled in Tasks 3–8) ────────────────────────
def section_jira_overnight() -> str:
    return "## 🔥 Overnight Jira Activity\n_[stub]_\n"

def section_active_queue() -> str:
    return "## 📋 Active Queue\n_[stub]_\n"

def section_integration_triage() -> str:
    return "## 🧩 Integration Triage Inbox\n_[stub]_\n"

def section_residency_status() -> str:
    return "## 🎓 Residency Planning Status\n_[stub]_\n"

def section_snowflake_tiers() -> str:
    return "## 📊 Residency Tier API Comparisons\n_[stub]_\n"

def section_adr() -> str:
    return "## 🤔 Open Decisions + Recent ADRs\n_[stub]_\n"


# ── Main ───────────────────────────────────────────────────────────────────
def main():
    now = datetime.now()
    date_str = now.strftime("%a %b %-d, %Y")
    time_str = now.strftime("%-I:%M%p").lower()

    sections = [
        f"# Morning Brief — {date_str}\n_Generated {time_str} nightly. Slack follow-ups pulled live below._\n",
        section_jira_overnight(),
        section_active_queue(),
        section_integration_triage(),
        section_residency_status(),
        section_snowflake_tiers(),
        section_adr(),
    ]

    brief = "\n---\n\n".join(sections)
    BRIEF_PATH.write_text(brief)
    print(f"Brief written to {BRIEF_PATH}")


if __name__ == "__main__":
    main()
```

**Step 2: Make it executable**

```bash
chmod +x ~/pm-workspace/scripts/nightly_brief.py
```

**Step 3: Run it to verify the skeleton works**

```bash
/usr/bin/python3 ~/pm-workspace/scripts/nightly_brief.py
```
Expected output: `Brief written to /Users/chriskim/pm-workspace/morning-brief.md`

**Step 4: Verify the file was written**

```bash
cat ~/pm-workspace/morning-brief.md
```
Expected: Brief with header + stub sections.

---

## Task 3: Jira overnight activity section

**Files:**
- Modify: `~/pm-workspace/scripts/nightly_brief.py` — replace `section_jira_overnight()`

**Step 1: Replace the stub with real implementation**

Replace the `section_jira_overnight()` function with:

```python
def section_jira_overnight() -> str:
    since = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M")
    jql = (
        f'project = AMIONMGR AND updated >= "{since}" '
        f'AND (assignee = "{JIRA_ACCOUNT_ID}" OR watcher = "{JIRA_ACCOUNT_ID}") '
        f'ORDER BY updated DESC'
    )
    issues = jira_search(jql, ["summary", "status", "priority", "comment", "assignee", "changelog"], max_results=30)

    if not issues:
        return "## 🔥 Overnight Jira Activity\nNo updates in the last 24h.\n"

    lines = ["## 🔥 Overnight Jira Activity\n"]
    for issue in issues:
        key = issue["key"]
        f = issue["fields"]
        summary = f["summary"][:70]
        status = f["status"]["name"]
        priority = f["priority"]["name"]
        lines.append(f"- **{key}** — {summary}  \n  Status: `{status}` | Priority: {priority}")

    return "\n".join(lines) + "\n"
```

**Step 2: Test this section in isolation**

```bash
/usr/bin/python3 -c "
import sys; sys.path.insert(0, '/Users/chriskim/pm-workspace/scripts')
exec(open('/Users/chriskim/pm-workspace/scripts/nightly_brief.py').read())
print(section_jira_overnight())
"
```
Expected: List of recently updated tickets, or "No updates in the last 24h."

**Step 3: Run full script, verify section appears in brief**

```bash
/usr/bin/python3 ~/pm-workspace/scripts/nightly_brief.py && grep "Overnight" ~/pm-workspace/morning-brief.md
```

---

## Task 4: Jira active queue section

**Files:**
- Modify: `~/pm-workspace/scripts/nightly_brief.py` — replace `section_active_queue()`

**Step 1: Replace the stub**

```python
def section_active_queue() -> str:
    jql = (
        f'project = AMIONMGR AND assignee = "{JIRA_ACCOUNT_ID}" '
        f'AND status not in ("Done", "Closed", "Resolved", "Will Not Do") '
        f'ORDER BY priority ASC, updated DESC'
    )
    issues = jira_search(jql, ["summary", "status", "priority"], max_results=10)

    if not issues:
        return "## 📋 Active Queue\nNo open tickets assigned to you.\n"

    lines = ["## 📋 Active Queue (top 10 by priority)\n"]
    for issue in issues:
        key = issue["key"]
        f = issue["fields"]
        summary = f["summary"][:72]
        status = f["status"]["name"]
        priority = f["priority"]["name"]
        lines.append(f"- **{key}** `{status}` [{priority}] — {summary}")

    return "\n".join(lines) + "\n"
```

**Step 2: Run full script and verify**

```bash
/usr/bin/python3 ~/pm-workspace/scripts/nightly_brief.py && grep -A 15 "Active Queue" ~/pm-workspace/morning-brief.md
```

---

## Task 5: Integration triage section (Jira + Canny)

**Files:**
- Modify: `~/pm-workspace/scripts/nightly_brief.py` — replace `section_integration_triage()`

**Step 1: Replace the stub**

```python
def section_integration_triage() -> str:
    lines = ["## 🧩 Integration Triage Inbox\n"]

    # ── Jira: integration-related tickets updated in last 7 days ──
    jql = (
        'project = AMIONMGR AND '
        '(summary ~ "integration" OR summary ~ "ADP" OR summary ~ "API" OR '
        ' labels in ("integration", "adp", "api-change")) '
        'AND updated >= "-7d" '
        'ORDER BY priority ASC, updated DESC'
    )
    try:
        issues = jira_search(jql, ["summary", "status", "priority", "assignee"], max_results=10)
        if issues:
            lines.append("**Jira — Integration tickets (last 7 days):**\n")
            for issue in issues:
                key = issue["key"]
                f = issue["fields"]
                summary = f["summary"][:72]
                status = f["status"]["name"]
                assignee_field = f.get("assignee") or {}
                assignee = assignee_field.get("displayName", "Unassigned")
                lines.append(f"- **{key}** `{status}` — {summary} _(assignee: {assignee})_")
        else:
            lines.append("**Jira:** No integration-related tickets updated in last 7 days.\n")
    except Exception as e:
        lines.append(f"**Jira:** Error fetching — {e}\n")

    lines.append("")

    # ── Canny: integration-related posts ──
    try:
        sys.path.insert(0, str(CANNY_DIR))
        from canny_client import canny_request

        # List all boards first
        boards_resp = canny_request("boards/list")
        boards = boards_resp.get("boards", [])

        canny_lines = []
        for board in boards:
            posts_resp = canny_request("posts/list", {
                "boardID": board["id"],
                "search": "integration",
                "limit": 5,
                "sort": "newest",
            })
            posts = posts_resp.get("posts", [])
            for post in posts:
                title = post.get("title", "")[:72]
                status = post.get("status", "")
                score = post.get("score", 0)
                author = post.get("author", {}).get("name", "unknown")
                canny_lines.append(f"- [{board['name']}] **{title}** | {status} | {score} votes | by {author}")

        if canny_lines:
            lines.append("**Canny — Integration posts:**\n")
            lines.extend(canny_lines)
        else:
            lines.append("**Canny:** No integration-related posts found.\n")
    except Exception as e:
        lines.append(f"**Canny:** Error fetching — {e}\n")

    lines.append("\n_Slack: Amanda Roberts + Sebastian DeLuca integration threads pulled live at session open via Glean._")

    return "\n".join(lines) + "\n"
```

**Step 2: Run and verify**

```bash
/usr/bin/python3 ~/pm-workspace/scripts/nightly_brief.py && grep -A 20 "Integration Triage" ~/pm-workspace/morning-brief.md
```
Expected: Jira integration tickets + Canny posts, or "No integration-related..." messages if none.

---

## Task 6: Residency planning status section

**Files:**
- Modify: `~/pm-workspace/scripts/nightly_brief.py` — replace `section_residency_status()`

**Step 1: Replace the stub**

```python
def section_residency_status() -> str:
    # Residency epics: AMIONMGR-3293 (Call & Shift Patterns), AMIONMGR-3292 (Clinic Template Expansion)
    jql = (
        'project = AMIONMGR AND '
        '("Epic Link" in ("AMIONMGR-3293", "AMIONMGR-3292") OR parent in ("AMIONMGR-3293", "AMIONMGR-3292")) '
        'AND status not in ("Done", "Closed", "Resolved") '
        'ORDER BY status ASC, priority ASC'
    )
    try:
        issues = jira_search(jql, ["summary", "status", "priority", "assignee"], max_results=20)
    except Exception as e:
        return f"## 🎓 Residency Planning Status\nError fetching — {e}\n"

    lines = ["## 🎓 Residency Planning Status\n"]

    if not issues:
        # Fallback: search by summary keyword
        jql_fallback = (
            'project = AMIONMGR AND summary ~ "Residency" '
            'AND status not in ("Done", "Closed", "Resolved") '
            'ORDER BY status ASC, updated DESC'
        )
        try:
            issues = jira_search(jql_fallback, ["summary", "status", "priority", "assignee"], max_results=15)
        except Exception:
            pass

    if not issues:
        lines.append("No open residency tickets found.\n")
        return "\n".join(lines)

    # Group by status
    by_status: dict[str, list] = {}
    for issue in issues:
        status = issue["fields"]["status"]["name"]
        by_status.setdefault(status, []).append(issue)

    for status, status_issues in sorted(by_status.items()):
        lines.append(f"**{status}:**")
        for issue in status_issues:
            key = issue["key"]
            f = issue["fields"]
            summary = f["summary"][:72]
            assignee_field = f.get("assignee") or {}
            assignee = assignee_field.get("displayName", "Unassigned")
            lines.append(f"  - **{key}** — {summary} _({assignee})_")
        lines.append("")

    return "\n".join(lines) + "\n"
```

**Step 2: Run and verify**

```bash
/usr/bin/python3 ~/pm-workspace/scripts/nightly_brief.py && grep -A 20 "Residency Planning" ~/pm-workspace/morning-brief.md
```

---

## Task 7: Snowflake tier API comparisons section

**Files:**
- Modify: `~/pm-workspace/scripts/nightly_brief.py` — replace `section_snowflake_tiers()`

**Step 1: Replace the stub**

```python
def section_snowflake_tiers() -> str:
    lines = ["## 📊 Residency Tier API Comparisons\n"]

    if not SQL_PATH.exists():
        lines.append(f"SQL file not found at `{SQL_PATH}`.\n")
        return "\n".join(lines)

    try:
        result = subprocess.run(
            [SNOW_BIN, "sql", "--connection", "doximity", "--format", "json",
             "-f", str(SQL_PATH)],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            lines.append(f"Snowflake error:\n```\n{result.stderr[:500]}\n```\n")
            return "\n".join(lines)

        rows = json.loads(result.stdout)
        if not rows:
            lines.append("No results returned from Snowflake query.\n")
            return "\n".join(lines)

        # Format as markdown table
        headers = list(rows[0].keys())
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for row in rows:
            cells = [str(row.get(h, "")).replace("|", "\\|")[:30] for h in headers]
            lines.append("| " + " | ".join(cells) + " |")

    except subprocess.TimeoutExpired:
        lines.append("Snowflake query timed out (60s limit).\n")
    except Exception as e:
        lines.append(f"Error running Snowflake query: {e}\n")

    return "\n".join(lines) + "\n"
```

**Step 2: Run and verify**

```bash
/usr/bin/python3 ~/pm-workspace/scripts/nightly_brief.py && grep -A 15 "Tier API" ~/pm-workspace/morning-brief.md
```
Expected: Markdown table of access codes per residency license, or an error message if Snowflake isn't reachable.

---

## Task 8: ADR section (reads local files)

**Files:**
- Modify: `~/pm-workspace/scripts/nightly_brief.py` — replace `section_adr()`

**Step 1: Replace the stub**

```python
def section_adr() -> str:
    lines = ["## 🤔 Open Decisions + Recent ADRs\n"]

    # ── Open decisions inbox ──
    lines.append("### Pending Decisions\n")
    if OPEN_DECISIONS_PATH.exists():
        content = OPEN_DECISIONS_PATH.read_text().strip()
        # Strip the header comment lines, keep decision entries
        entries = [l for l in content.splitlines() if not l.startswith("_")]
        lines.append("\n".join(entries))
    else:
        lines.append("_No open-decisions.md found. Create it at ~/pm-workspace/decisions/open-decisions.md_")

    lines.append("")

    # ── Recent ADR log (last 5 decisions) ──
    lines.append("### Recent Decisions (last 5)\n")
    if ADR_LOG_PATH.exists():
        content = ADR_LOG_PATH.read_text().strip()
        # Split on ## headers, take last 5 entries
        import re
        entries = re.split(r'\n(?=## )', content)
        entries = [e for e in entries if e.strip().startswith("##")]
        recent = entries[-5:] if len(entries) >= 5 else entries
        if recent:
            lines.append("\n\n".join(reversed(recent)))
        else:
            lines.append("_No decisions logged yet._")
    else:
        lines.append("_No adr-log.md found. Create it at ~/pm-workspace/decisions/adr-log.md_")

    return "\n".join(lines) + "\n"
```

**Step 2: Run and verify**

```bash
/usr/bin/python3 ~/pm-workspace/scripts/nightly_brief.py && grep -A 30 "Open Decisions" ~/pm-workspace/morning-brief.md
```
Expected: Pending decisions from open-decisions.md (including the two seed entries).

---

## Task 9: Full end-to-end test + review output

**Step 1: Run the complete script**

```bash
/usr/bin/python3 ~/pm-workspace/scripts/nightly_brief.py
```
Expected: `Brief written to /Users/chriskim/pm-workspace/morning-brief.md` with no Python errors.

**Step 2: Review the full brief**

```bash
cat ~/pm-workspace/morning-brief.md
```
Verify:
- [ ] Header with today's date and time
- [ ] Jira overnight activity populated (or "No updates" message)
- [ ] Active queue populated
- [ ] Integration triage has Jira + Canny results (or "none found")
- [ ] Residency section has tickets
- [ ] Snowflake table OR error message (acceptable)
- [ ] ADR section shows both seed decisions

**Step 3: Fix any section that errors** (check for Python tracebacks, fix inline)

---

## Task 10: Add SessionStart hook to Claude settings

**Files:**
- Modify: `~/.claude/settings.json`

**Step 1: Read current settings**

```bash
cat ~/.claude/settings.json
```

**Step 2: Add the hooks block**

The `hooks` key goes at the top level of the JSON object. Merge this into the existing settings (do not overwrite other keys):

```json
"hooks": {
  "SessionStart": [
    {
      "matcher": "",
      "hooks": [
        {
          "type": "command",
          "command": "bash -c 'if [ -f ~/pm-workspace/morning-brief.md ]; then echo \"=== MORNING BRIEF ===\"; cat ~/pm-workspace/morning-brief.md; echo \"=== END BRIEF ===\"; echo \"\"; echo \"ACTION REQUIRED: Search Glean for Slack threads from the last 48h where Chris was mentioned or sent a message. Flag any threads with no reply from Chris as Needs Reply. Also search for messages from Amanda Roberts and Sebastian DeLuca about integration tickets.\"; else echo \"No morning brief found. Run: python3 ~/pm-workspace/scripts/nightly_brief.py\"; fi'",
          "async": false
        }
      ]
    }
  ]
}
```

**Step 3: Verify settings.json is valid JSON**

```bash
python3 -c "import json; json.load(open('/Users/chriskim/.claude/settings.json')); print('valid JSON')"
```
Expected: `valid JSON`

---

## Task 11: Set up crontab

**Step 1: Write the crontab entry**

```bash
(crontab -l 2>/dev/null; echo "47 21 * * * /usr/bin/python3 /Users/chriskim/pm-workspace/scripts/nightly_brief.py >> /tmp/nightly-brief.log 2>&1") | crontab -
```

**Step 2: Verify crontab was set**

```bash
crontab -l
```
Expected: `47 21 * * * /usr/bin/python3 /Users/chriskim/pm-workspace/scripts/nightly_brief.py >> /tmp/nightly-brief.log 2>&1`

**Step 3: Do a manual run to confirm crontab path works**

```bash
/usr/bin/python3 /Users/chriskim/pm-workspace/scripts/nightly_brief.py >> /tmp/nightly-brief.log 2>&1
cat /tmp/nightly-brief.log
```
Expected: `Brief written to /Users/chriskim/pm-workspace/morning-brief.md`

---

## Task 12: Final verification

**Step 1: Confirm all files exist**

```bash
ls ~/pm-workspace/scripts/nightly_brief.py
ls ~/pm-workspace/decisions/open-decisions.md
ls ~/pm-workspace/decisions/adr-log.md
ls ~/pm-workspace/morning-brief.md
```

**Step 2: Confirm crontab is set**

```bash
crontab -l | grep nightly
```

**Step 3: Confirm settings.json has hooks**

```bash
python3 -c "import json; d=json.load(open('/Users/chriskim/.claude/settings.json')); print('hooks present:', 'hooks' in d)"
```
Expected: `hooks present: True`

**Step 4: Open a new Claude Code session to test the hook**

The next time you open Claude Code, the morning brief should appear in context followed by the Glean Slack prompt.

---

## Task 13: Overnight review agent — in-progress manifest + output dir

**Files:**
- Already created: `~/pm-workspace/in-progress.md` (manifest of active work items)
- Create: `~/pm-workspace/active/overnight-reviews/` (output directory)

**Step 1: Create output directory**

```bash
mkdir -p ~/pm-workspace/active/overnight-reviews
```

**Step 2: Verify manifest exists and has correct structure**

```bash
cat ~/pm-workspace/in-progress.md
```
Expected: 3 active items (Clinic UX prototype, Cancel Clinic Rules spec, Call & Shift Patterns proposal)

---

## Task 14: Overnight review agent — Claude API reviewer function

**Files:**
- Modify: `~/pm-workspace/scripts/nightly_brief.py` — add import + `run_overnight_reviews()` + `section_overnight_review()`

**Step 1: Add anthropic import and constants at top of script (after existing imports)**

```python
# ── Anthropic (overnight review) ──────────────────────────────────────────
import os
IN_PROGRESS_MANIFEST = PM_WORKSPACE / "in-progress.md"
OVERNIGHT_REVIEWS_DIR = PM_WORKSPACE / "active" / "overnight-reviews"
ANTHROPIC_API_KEY = os.environ.get("DOX_ANTHROPIC_API_KEY", "")
```

**Step 2: Add the review runner function**

Add this function before `main()`:

```python
REVIEW_PROMPTS = {
    "ux-prototype": """You are a skeptical senior PM reviewing a UX prototype.
Be direct and critical. Your job is to make this better, not validate it.

Review this prototype and:
1. Identify the 2-3 most critical UX problems or missing interaction states
2. Flag any edge cases the prototype doesn't handle
3. Point out any assumptions baked in that should be made explicit
4. Suggest specific, concrete improvements (not vague "consider adding...")
5. Note what's actually working well (1-2 things max — be stingy with praise)

Output format:
## Critical Issues
[numbered list]

## Missing Edge Cases
[numbered list]

## Unstated Assumptions
[numbered list]

## Specific Improvements
[numbered list]

## What's Working
[1-2 items]""",

    "proposal": """You are a skeptical senior PM reviewing a product proposal.
Be direct and critical. Your job is to stress-test this, not approve it.

Review this proposal and:
1. Identify the weakest assumptions — what's being taken for granted that could be wrong?
2. Find scope gaps — what important scenarios are not covered?
3. Challenge the problem framing — is this solving the right problem?
4. Flag unstated dependencies or risks
5. Point out where the rationale is thin or circular
6. Identify 1-2 things that are genuinely strong

Then rewrite the most problematic section to be tighter and more defensible.

Output format:
## Weakest Assumptions
[numbered list with specific quotes from the doc]

## Scope Gaps
[numbered list]

## Problem Framing Issues
[if any]

## Unstated Risks / Dependencies
[numbered list]

## Thin Rationale
[specific callouts]

## What's Strong
[1-2 items]

## Rewritten Section: [section name]
[improved version]""",

    "story": """You are a skeptical senior PM reviewing a Jira story.
Be direct. Your job is to find what's missing before engineering finds it in the sprint.

Review this story and:
1. Find acceptance criteria that are untestable or ambiguous
2. Identify missing edge cases (permission boundaries, empty states, error states, schedule state transitions)
3. Flag scope that's implied but not stated
4. Point out any AC that tests behavior outside this ticket's scope
5. Rewrite the 2 weakest ACs to be tighter

Output format:
## Untestable / Ambiguous ACs
[numbered list with specific AC quoted]

## Missing Edge Cases
[numbered list — be specific about schedule states, permissions, empty states]

## Implied but Unstated Scope
[numbered list]

## Out-of-Scope ACs
[if any]

## Rewritten ACs
[2 improved versions]"""
}


def run_overnight_reviews() -> list[dict]:
    """
    Read in-progress.md manifest, review each artifact via Claude API.
    Returns list of review result dicts: {slug, type, before_path, after_path, changes_summary}
    """
    if not ANTHROPIC_API_KEY:
        return [{"error": "DOX_ANTHROPIC_API_KEY not set in environment"}]
    if not IN_PROGRESS_MANIFEST.exists():
        return [{"error": f"in-progress.md not found at {IN_PROGRESS_MANIFEST}"}]

    try:
        import anthropic as _anthropic
        client = _anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    except ImportError:
        return [{"error": "anthropic SDK not installed — run: pip3 install anthropic"}]

    # Parse manifest — extract active items
    manifest = IN_PROGRESS_MANIFEST.read_text()
    import re
    # Find sections between ### headers and ---
    item_blocks = re.split(r'\n### ', manifest)

    today_str = datetime.now().strftime("%Y-%m-%d")
    review_dir = OVERNIGHT_REVIEWS_DIR / today_str
    review_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for block in item_blocks:
        if not block.strip() or block.strip().startswith("#") or "Active Items" in block:
            continue
        if "Review Output Location" in block:
            continue

        lines = block.strip().splitlines()
        title = lines[0].strip()

        # Extract fields
        fields = {}
        for line in lines[1:]:
            for key in ["Type", "File", "Context", "Review focus"]:
                if line.strip().startswith(f"- **{key}:**"):
                    fields[key.lower().replace(" ", "_")] = line.split(":**", 1)[1].strip()

        artifact_type = fields.get("type", "proposal").strip("`")
        file_path_str = fields.get("file", "").strip("`")
        context = fields.get("context", "")
        review_focus = fields.get("review_focus", "")

        if not file_path_str:
            results.append({"title": title, "error": "No file path in manifest"})
            continue

        file_path = Path(file_path_str)
        if not file_path.exists():
            results.append({"title": title, "error": f"File not found: {file_path}"})
            continue

        # Read the artifact
        content = file_path.read_text()
        # Truncate very large files (HTML prototypes can be huge)
        if len(content) > 12000:
            content = content[:12000] + "\n\n[... truncated for review ...]"

        prompt = REVIEW_PROMPTS.get(artifact_type, REVIEW_PROMPTS["proposal"])
        full_prompt = f"""Context: {context}

Specific review focus: {review_focus}

---

{content}"""

        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2000,
                messages=[{"role": "user", "content": full_prompt}],
                system=prompt
            )
            review_text = response.content[0].text

            # Generate slug from title
            slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:40]

            # Save before snapshot
            before_path = review_dir / f"{slug}-before.md"
            before_path.write_text(f"# Before: {title}\n\nSource: {file_path}\n\n---\n\n{file_path.read_text()}")

            # Save review/after
            after_path = review_dir / f"{slug}-review.md"
            after_path.write_text(f"# Overnight Review: {title}\n\nDate: {today_str}\nSource: {file_path}\n\n---\n\n{review_text}")

            # Extract first critical issue as summary
            summary_lines = [l for l in review_text.splitlines() if l.strip() and not l.startswith("#")]
            summary = summary_lines[0][:120] if summary_lines else "See review file."

            results.append({
                "title": title,
                "type": artifact_type,
                "review_path": str(after_path),
                "top_issue": summary,
                "full_review": review_text
            })

        except Exception as e:
            results.append({"title": title, "error": f"Claude API error: {e}"})

    return results
```

**Step 3: Add `section_overnight_review()` using the results**

```python
def section_overnight_review(reviews: list[dict]) -> str:
    lines = ["## 🔧 Overnight Review — Before/After\n"]
    lines.append("_Claude reviewed your in-progress work overnight. Full reviews in `~/pm-workspace/active/overnight-reviews/`_\n")

    if not reviews:
        lines.append("_No items in `~/pm-workspace/in-progress.md` — add work items to get overnight reviews._")
        return "\n".join(lines)

    for review in reviews:
        title = review.get("title", "Unknown")
        if "error" in review:
            lines.append(f"### {title}\n⚠️ {review['error']}\n")
            continue

        artifact_type = review.get("type", "")
        review_path = review.get("review_path", "")
        full_review = review.get("full_review", "")

        lines.append(f"### {title} `[{artifact_type}]`\n")

        # Parse the review into sections and show key callouts
        import re
        sections = re.split(r'\n## ', full_review)
        for section in sections:
            if not section.strip():
                continue
            section_lines = section.strip().splitlines()
            section_title = section_lines[0].strip("# ")
            section_body = "\n".join(section_lines[1:]).strip()

            # Show Critical Issues, Weakest Assumptions, and Rewritten sections
            if any(k in section_title for k in ["Critical", "Weakest", "Rewritten", "Missing Edge"]):
                lines.append(f"**{section_title}:**")
                # Show first 3 bullets only — keep brief concise
                bullets = [l for l in section_body.splitlines() if l.strip()][:3]
                lines.extend(bullets)
                lines.append("")

        lines.append(f"_Full review: `{review_path}`_\n")

    return "\n".join(lines) + "\n"
```

**Step 4: Wire into `main()` — run reviews and pass results to section builder**

In `main()`, add the overnight review call and update the sections list:

```python
def main():
    now = datetime.now()
    date_str = now.strftime("%a %b %-d, %Y")
    time_str = now.strftime("%-I:%M%p").lower()

    print("Running overnight reviews...")
    reviews = run_overnight_reviews()
    print(f"  {len(reviews)} artifact(s) reviewed.")

    sections = [
        f"# Morning Brief — {date_str}\n_Generated {time_str} nightly. Slack follow-ups pulled live below._\n",
        section_overnight_review(reviews),   # ← new, leads the brief
        section_jira_overnight(),
        section_active_queue(),
        section_integration_triage(),
        section_residency_status(),
        section_snowflake_tiers(),
        section_adr(),
    ]

    brief = "\n---\n\n".join(sections)
    BRIEF_PATH.write_text(brief)
    print(f"Brief written to {BRIEF_PATH}")
```

---

## Task 15: Test overnight review end-to-end

**Step 1: Export the API key for the test run**

```bash
export DOX_ANTHROPIC_API_KEY=$(grep DOX_ANTHROPIC_API_KEY ~/.zshrc | cut -d'"' -f2)
```

**Step 2: Run the full script**

```bash
/usr/bin/python3 ~/pm-workspace/scripts/nightly_brief.py
```
Expected output:
```
Running overnight reviews...
  3 artifact(s) reviewed.
Brief written to /Users/chriskim/pm-workspace/morning-brief.md
```

**Step 3: Check the overnight review section in the brief**

```bash
grep -A 40 "Overnight Review" ~/pm-workspace/morning-brief.md
```
Expected: Critical issues and rewritten sections for clinic template expansion, cancel clinic rules, and call & shift patterns.

**Step 4: Check the full review files**

```bash
ls ~/pm-workspace/active/overnight-reviews/$(date +%Y-%m-%d)/
```
Expected: `*-before.md` and `*-review.md` for each artifact.

**Step 5: Fix the crontab to source .zshrc for the API key**

The crontab environment doesn't source `.zshrc`, so the API key won't be available. Update the crontab entry:

```bash
(crontab -l 2>/dev/null | grep -v nightly_brief; echo "47 21 * * * bash -c 'source ~/.zshrc && /usr/bin/python3 /Users/chriskim/pm-workspace/scripts/nightly_brief.py >> /tmp/nightly-brief.log 2>&1'") | crontab -
```

Verify:
```bash
crontab -l
```

---

## Notes

- **Snowflake failures are non-fatal.** The script continues even if `snow` times out — it writes an error note in that section.
- **Canny failures are non-fatal.** Same pattern — error note in section.
- **Claude API failures are non-fatal.** Review errors appear in the brief section — the rest of the brief still generates.
- **Glean/Slack** is intentionally live-at-session-open, not nightly, because Glean MCP requires an active Claude session.
- **ADR files are yours to maintain.** Add to `open-decisions.md` when a new decision needs tracking. Move resolved decisions to `adr-log.md`. Claude will prompt you during sessions when you make a decision.
- **in-progress.md is yours to maintain.** Add entries when you start new work. Remove them when done. The overnight agent reads this file each night.
- **Review output accumulates daily** in `~/pm-workspace/active/overnight-reviews/YYYY-MM-DD/`. Prune old reviews periodically.
- **Log file:** Crontab errors go to `/tmp/nightly-brief.log` — check it if brief seems stale.
- **API key in crontab:** The crontab entry sources `~/.zshrc` to pick up `DOX_ANTHROPIC_API_KEY`.
