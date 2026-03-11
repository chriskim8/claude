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

def jira_search(jql: str, fields: list, max_results: int = 20) -> list:
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


# ── Section builders ──────────────────────────────────────────────────────
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
    by_status = {}
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


def section_adr() -> str:
    import re
    lines = ["## 🤔 Open Decisions + Recent ADRs\n"]

    # ── Open decisions inbox ──
    lines.append("### Pending Decisions\n")
    if OPEN_DECISIONS_PATH.exists():
        content = OPEN_DECISIONS_PATH.read_text().strip()
        entries = [l for l in content.splitlines() if not l.startswith("_")]
        lines.append("\n".join(entries))
    else:
        lines.append("_No open-decisions.md found. Create it at ~/pm-workspace/decisions/open-decisions.md_")

    lines.append("")

    # ── Recent ADR log (last 5 decisions) ──
    lines.append("### Recent Decisions (last 5)\n")
    if ADR_LOG_PATH.exists():
        content = ADR_LOG_PATH.read_text().strip()
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


# ── Anthropic (overnight review) ──────────────────────────────────────────
IN_PROGRESS_MANIFEST = PM_WORKSPACE / "in-progress.md"
OVERNIGHT_REVIEWS_DIR = PM_WORKSPACE / "active" / "overnight-reviews"
def _get_anthropic_key() -> str:
    """Get API key from env or fall back to reading from ~/.zshrc (for crontab)."""
    key = os.environ.get("DOX_ANTHROPIC_API_KEY", "")
    if key:
        return key
    zshrc = Path.home() / ".zshrc"
    if zshrc.exists():
        import re
        for line in zshrc.read_text().splitlines():
            m = re.match(r'\s*export\s+DOX_ANTHROPIC_API_KEY=["\']?([^"\']+)["\']?', line)
            if m:
                return m.group(1).strip()
    return ""

ANTHROPIC_API_KEY = _get_anthropic_key()

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


def run_overnight_reviews() -> list:
    """
    Read in-progress.md manifest, review each artifact via Claude API.
    Returns list of review result dicts: {title, type, review_path, top_issue, full_review}
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

    manifest = IN_PROGRESS_MANIFEST.read_text()
    import re
    item_blocks = re.split(r'\n### ', manifest)

    today_str = datetime.now().strftime("%Y-%m-%d")
    review_dir = OVERNIGHT_REVIEWS_DIR / today_str
    review_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for block in item_blocks:
        if not block.strip() or block.strip().startswith("#") or "Active Items" in block:
            continue
        lines = block.strip().splitlines()
        title = lines[0].strip()
        if title.startswith("Review Output"):
            continue

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

        content = file_path.read_text()
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

            slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:40]

            before_path = review_dir / f"{slug}-before.md"
            before_path.write_text(f"# Before: {title}\n\nSource: {file_path}\n\n---\n\n{file_path.read_text()}")

            after_path = review_dir / f"{slug}-review.md"
            after_path.write_text(f"# Overnight Review: {title}\n\nDate: {today_str}\nSource: {file_path}\n\n---\n\n{review_text}")

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


def section_overnight_review(reviews: list) -> str:
    import re
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

        sections = re.split(r'\n## ', full_review)
        for section in sections:
            if not section.strip():
                continue
            section_lines = section.strip().splitlines()
            section_title = section_lines[0].strip("# ")
            section_body = "\n".join(section_lines[1:]).strip()

            if any(k in section_title for k in ["Critical", "Weakest", "Rewritten", "Missing Edge"]):
                lines.append(f"**{section_title}:**")
                bullets = [l for l in section_body.splitlines() if l.strip()][:3]
                lines.extend(bullets)
                lines.append("")

        lines.append(f"_Full review: `{review_path}`_\n")

    return "\n".join(lines) + "\n"


# ── Main ───────────────────────────────────────────────────────────────────
def main():
    now = datetime.now()
    date_str = now.strftime("%a %b %-d, %Y")
    time_str = now.strftime("%-I:%M%p").lower()

    print("Running overnight reviews...")
    reviews = run_overnight_reviews()
    print(f"  {len(reviews)} artifact(s) reviewed.")

    sections = [
        f"# Morning Brief — {date_str}\n_Generated {time_str} nightly. Slack follow-ups pulled live below._\n",
        section_overnight_review(reviews),
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
