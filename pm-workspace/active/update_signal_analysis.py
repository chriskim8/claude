"""Add a Signal Analysis tab to the Residency Roadmap spreadsheet.

Reads the Customer Signals tab, applies a critical relevance filter,
and writes a structured PM-readable "Signal Analysis" tab with:
  - Signal type audit (NOISE vs. SALES vs. TRAINING vs. FEATURE)
  - Feature signal breakdown by sub-theme
  - Canny feature requests (all)
  - Per-theme ticket deep-dives with inline summaries

Run: cd ~/pm-workspace && python3 active/update_signal_analysis.py
"""
from __future__ import annotations

import os
import re
import sys
import importlib.util as _ilu
from collections import defaultdict

_GOOGLE = os.path.expanduser("~/google-services")

def _load_pkg(pkg_dir, module_names):
    mods = {}
    for name in module_names:
        path = os.path.join(pkg_dir, f"{name}.py")
        spec = _ilu.spec_from_file_location(f"_{pkg_dir}_{name}", path,
                                            submodule_search_locations=[])
        mod = _ilu.module_from_spec(spec)
        sys.modules[f"_{pkg_dir}_{name}"] = mod
        mods[name] = (spec, mod)
    loaded = {}
    for name, (spec, mod) in mods.items():
        sys.modules["config"] = mods.get("config", (None, None))[1]
        spec.loader.exec_module(mod)
        loaded[name] = mod
    sys.modules.pop("config", None)
    return loaded

_g = _load_pkg(_GOOGLE, ["config", "google_client"])
get_sheets_service = _g["google_client"].get_sheets_service

# Latest spreadsheet (date-sorted roadmap)
SS_ID = "17FhQywXLOCaeGFxe3qMTxRFvqRn7lcPnxuK1ZFICrw0"

# ── colors ────────────────────────────────────────────────────────────────────
DARK_BLUE   = "#1F3864"
HEADER_GRAY = "#434343"
WHITE       = "#FFFFFF"
BLACK       = "#000000"

# Section header background by type
SECTION_BG = {
    "AUDIT":    "#F4CCCC",  # light red
    "FEATURE":  "#C9DAF8",  # light blue
    "CANNY":    "#D0E4F1",  # light teal
    "DEEPDIVE": "#D9EAD3",  # light green
    "THEME":    "#F3F3F3",  # light gray (sub-theme rows)
}

SIGNAL_BG = {
    "NOISE":    "#F9CBAC",  # light orange
    "SALES":    "#FFF2CC",  # yellow
    "ACCOUNT":  "#E9E9E9",  # light gray
    "TRAINING": "#D9EAD3",  # light green
    "FEATURE":  "#C9DAF8",  # light blue
    "OTHER":    "#EFEFEF",  # very light gray
}

SEVERITY_BG = {
    "H": "#F4CCCC",
    "M": "#FFF2CC",
    "L": "#D9EAD3",
}

NUM_COLS = 6  # A-F


# ── helpers ───────────────────────────────────────────────────────────────────

def rgb(h):
    h = h.lstrip("#")
    return {"red": int(h[0:2],16)/255, "green": int(h[2:4],16)/255, "blue": int(h[4:6],16)/255}

def fmt(sid, r0, r1, c0, c1, **kw):
    cell, fields = {}, []
    if "bg"   in kw: cell["backgroundColor"] = rgb(kw["bg"]); fields.append("userEnteredFormat.backgroundColor")
    if "bold" in kw: cell.setdefault("textFormat",{})["bold"] = kw["bold"]; fields.append("userEnteredFormat.textFormat.bold")
    if "fg"   in kw: cell.setdefault("textFormat",{})["foregroundColor"] = rgb(kw["fg"]); fields.append("userEnteredFormat.textFormat.foregroundColor")
    if "sz"   in kw: cell.setdefault("textFormat",{})["fontSize"] = kw["sz"]; fields.append("userEnteredFormat.textFormat.fontSize")
    if "wrap" in kw: cell["wrapStrategy"] = kw["wrap"]; fields.append("userEnteredFormat.wrapStrategy")
    if "ital" in kw: cell.setdefault("textFormat",{})["italic"] = kw["ital"]; fields.append("userEnteredFormat.textFormat.italic")
    return {"repeatCell": {"range": {"sheetId":sid,"startRowIndex":r0,"endRowIndex":r1,
                                     "startColumnIndex":c0,"endColumnIndex":c1},
                           "cell": {"userEnteredFormat": cell}, "fields": ",".join(fields)}}

def merge(sid, r, c0, c1):
    return {"mergeCells": {"range": {"sheetId":sid,"startRowIndex":r,"endRowIndex":r+1,
                                     "startColumnIndex":c0,"endColumnIndex":c1},
                           "mergeType": "MERGE_ALL"}}

def cw(sid, col, px):
    return {"updateDimensionProperties": {"range": {"sheetId":sid,"dimension":"COLUMNS",
                                                     "startIndex":col,"endIndex":col+1},
                                           "properties":{"pixelSize":px},"fields":"pixelSize"}}

def freeze_rows(sid, n):
    return {"updateSheetProperties": {"properties": {"sheetId":sid,
             "gridProperties":{"frozenRowCount":n,"frozenColumnCount":0}},
             "fields":"gridProperties.frozenRowCount,gridProperties.frozenColumnCount"}}


# ── classification ────────────────────────────────────────────────────────────

def classify(source: str, title: str, notes: str) -> tuple[str, str]:
    """Return (signal_type, sub_theme) for a ticket row.

    signal_type: NOISE | SALES | ACCOUNT | TRAINING | FEATURE | OTHER
    sub_theme: human-readable label
    """
    t = title.lower()
    n = notes.lower()
    text = t + " " + n

    # ── NOISE: Zendesk phone call transcripts ────────────────────────────────
    if re.search(r"call (with|from) (\+1|\+\d)", t):
        return ("NOISE", "Phone call transcript")
    if "time of call:" in text or "call to: +1" in text:
        return ("NOISE", "Phone call transcript")

    # ── SALES: pricing, demo, churn, trial ───────────────────────────────────
    if any(k in text for k in [
        "free trial", "how much", "cost for amion", "considering to use",
        "no longer let us use", "will no longer", "cancel", "pricing",
    ]):
        return ("SALES", "Pricing / Demo / Churn")
    if "demo" in text and "schedule" not in text:
        return ("SALES", "Pricing / Demo / Churn")
    if "invoice" in text and "scheduling" not in text:
        return ("SALES", "Billing")
    if re.search(r"order & invoice", t):
        return ("SALES", "Billing")

    # ── ACCOUNT: passwords, access codes, admin perms ────────────────────────
    if any(k in text for k in [
        "password", "access code", "view code", "sign in", "sso",
        "change your access", "change the access",
    ]):
        return ("ACCOUNT", "Account / Access code")
    if "admin access" in text and "scheduling" not in text:
        return ("ACCOUNT", "Admin permissions")
    if "licenses" in text and not any(k in text for k in ["schedule", "resident", "scheduling"]):
        return ("ACCOUNT", "License management")

    # Detect bug/feature keywords before training check
    is_bug = any(k in text for k in [
        "bug", "broken", "not working", "not coming", "incorrect", "wrong date",
        "missing", "disappeared", "not showing", "doesn't work", "error",
        "not matching", "not connect", "not sync", "inconsistently",
    ])
    is_feature_req = any(k in text for k in [
        "migrat", "import", "integration", "medhub", "new innov", "csv", "excel",
        "can you add", "would like to request", "feature request", "is there a way",
        "would it be possible",
    ])

    # ── TRAINING: how-to questions (not bugs, not feature requests) ───────────
    if not is_bug and not is_feature_req:
        if any(k in text for k in [
            "refresher", "training guide", "training video", "how do i", "how to set up",
            "how to add", "how to use", "from scratch", "getting started", "tutorial",
            "please help me", "can you show", "need help with", "have forgotten",
            "i am new", "just started",
        ]):
            return ("TRAINING", "Onboarding / How-to")

    # ── FEATURE: true product signal ─────────────────────────────────────────
    if any(k in text for k in [
        "medhub", "new innov", "ecw", "qgenda", "epic systems",
        "api access", "api integration", "connecting to", "sync", "synchroni",
    ]):
        return ("FEATURE", "Integration")
    if "integration" in text and any(k in text for k in ["residency", "schedule", "amion"]):
        return ("FEATURE", "Integration")

    if any(k in text for k in [
        "migrat", "import schedule", "import from", "switching to", "oncloud",
        "classic", "excel", "spreadsheet", "new innovations or",
        "from new innovations",
    ]):
        return ("FEATURE", "Migration / Import")

    if any(k in text for k in [
        "academic year", "training level", "pgy", "graduation",
        "graduated", "fellow", "incoming intern", "2024-2025",
        "2025-2026", "2026-2027", "past academic", "prior year",
    ]):
        return ("FEATURE", "Academic Year")

    if any(k in text for k in [
        "block", "rotation", "split shift", "split schedule", "block date",
        "tally", "block schedule", "block count", "block service", "block line",
    ]):
        return ("FEATURE", "Block / Rotation")

    if any(k in text for k in ["clinic", "continuity clinic"]):
        return ("FEATURE", "Clinic")

    if any(k in text for k in [
        "viewer", "view schedule", "can't see the schedule", "cannot see",
        "resident view", "residents can't", "non-scheduled staff",
        "make schedule viewable", "make the schedule available",
        "viewable to", "staff members so they c",
    ]):
        return ("FEATURE", "Viewer / Visibility")

    if any(k in text for k in [
        "notification", "pager", "paging", "email alert",
        "not receiving", "did not receive", "didn't receive",
    ]):
        return ("FEATURE", "Notifications")

    if is_bug:
        return ("FEATURE", "Bug (unclassified)")

    if is_feature_req:
        return ("FEATURE", "Feature request (unclassified)")

    return ("OTHER", "General support")


def pm_summary(source: str, title: str, notes: str, sub_theme: str) -> str:
    """Write a short PM-readable description of what this ticket is actually about."""
    notes_clean = notes.strip().replace("\n", " ")
    t = title.strip()
    n = notes_clean.lower()

    # Phone logs
    if sub_theme == "Phone call transcript":
        return "Zendesk auto-logged an inbound support call — no scheduling content."

    # Known patterns
    if "refresher" in n or "have forgotten" in n:
        return f"Coordinator asking for a training refresher or video walkthrough. " \
               f"'{t[:60]}' — CS / Academy load, not a product gap."
    if "from scratch" in n or "just started" in n or "i am new" in n:
        return f"New program setting up Amion for the first time. '{t[:60]}' — onboarding friction."
    if "free trial" in n:
        return "Prospective customer asking about a free trial. Sales inquiry."
    if "no longer let us" in n or "will no longer" in n:
        return "Existing customer reporting that their health system is discontinuing Amion access. Churn signal."
    if "considering to use" in n or "pricing" in n or "how much" in n:
        return "New program evaluating Amion for residency scheduling. Sales / pricing inquiry."
    if "medhub" in n and ("not connect" in n or "problem" in n or "issue" in n):
        return f"MedHub ↔ Amion sync failure. '{t[:60]}'. Customer can't get schedule data into MedHub. " \
               f"Integration reliability issue affecting data handoff."
    if "new innov" in n or "new innovations" in n:
        return f"New Innovations integration question. '{t[:60]}'. Likely NI pulling schedule data failing or " \
               f"asking about CSV export path."
    if "import" in n and ("new innov" in n or "excel" in n or "spreadsheet" in n):
        return f"Customer asking whether schedule data can be imported from NI or Excel. " \
               f"'{t[:60]}' — CSV import feature request, explicit."
    if "migrat" in n or "switching to" in n or "oncloud" in n:
        return f"Migration from Classic. '{t[:60]}'. Program interested in moving to Amion Next / OnCloud."
    if "academic year" in n or "past academic" in n:
        return f"Academic year data issue. '{t[:60]}'. " + (
            "Requesting access to past AY schedules for graduated residents." if "graduated" in n or "past" in n
            else "AY-related scheduling question — residency structure or visibility."
        )
    if "split" in n and ("shift" in n or "not coming" in n or "not showing" in n):
        return f"Bug: split shift assignments not appearing correctly. '{t[:60]}'. " \
               f"Classic parity issue — split shifts are a core block schedule feature."
    if "block date" in n and "not match" in n:
        return f"Date sync issue: block dates on Amion.com (viewer) differ from Amion Online (manager). " \
               f"'{t[:60]}'. Viewer/manager data consistency bug."
    if "access code" in n or "view code" in n:
        return f"Coordinator asking how to change schedule access or view code. " \
               f"'{t[:60]}' — account management, not a product feature request."
    if "admin access" in n:
        return f"User requesting admin permissions for their account. '{t[:60]}' — CS task."
    if "viewer" in n or "non-scheduled staff" in n or "make schedule viewable" in n:
        return f"Program wants to control who can view the residency schedule. '{t[:60]}'. " \
               f"Viewer access / permissions question."
    if "fellow" in n or "fellows" in n:
        return f"Adding fellowship-level staff to residency schedule. '{t[:60]}'. " \
               f"May relate to staff type management or AY visibility."
    if "ecw" in n or "qgenda" in n:
        return f"Third-party system integration. '{t[:60]}'. Customer asking if Amion can integrate with " \
               f"{'eClinicalWorks (ECW)' if 'ecw' in n else 'Qgenda'} — not a direct residency feature."
    if "complex" in n and "residency" in n:
        return f"Program with complex scheduling needs reaching out. '{t[:60]}'. " \
               f"Likely a multi-schedule or multi-service residency setup question."

    # Generic fallback
    snippet = notes_clean[:150] if notes_clean else t
    return f"'{t[:60]}' — {snippet}"


# ── read from spreadsheet ─────────────────────────────────────────────────────

def read_signals(sheets_svc) -> list[dict]:
    result = sheets_svc.spreadsheets().values().get(
        spreadsheetId=SS_ID,
        range="'Customer Signals'!A3:H2000",
    ).execute()
    rows = []
    for row in result.get("values", []):
        if not row or len(row) < 2:
            continue
        rows.append({
            "source": row[0] if len(row) > 0 else "",
            "title":  row[1] if len(row) > 1 else "",
            "theme":  row[2] if len(row) > 2 else "",
            "votes":  row[3] if len(row) > 3 else "",
            "status": row[4] if len(row) > 4 else "",
            "date":   row[5] if len(row) > 5 else "",
            "url":    row[6] if len(row) > 6 else "",
            "notes":  row[7] if len(row) > 7 else "",
        })
    return rows


# ── analysis ──────────────────────────────────────────────────────────────────

SEVERITY_MAP = {
    "Integration":              "H",
    "Migration / Import":       "H",
    "Academic Year":            "H",
    "Block / Rotation":         "H",
    "Viewer / Visibility":      "H",
    "Notifications":            "M",
    "Clinic":                   "M",
    "Bug (unclassified)":       "M",
    "Feature request (unclassified)": "M",
}

ROADMAP_MAP = {
    "Integration":              "New Innovations (Aug 2026), MedHub (Oct 2026), CSV Import (Jul 2026)",
    "Migration / Import":       "Map Classic Staff Types (May 2026), CSV Import (Jul 2026)",
    "Academic Year":            "AY Visibility (Mar 2026), AY Lock (Apr 2026), AY Rollover (Jun 2026)",
    "Block / Rotation":         "Multiple Splits (Mar 2026), Block Tally (Sep 2026)",
    "Viewer / Visibility":      "AY Visibility (Mar 2026), Viewer AY Switching (Sep 2026)",
    "Notifications":            "Not currently on roadmap — CS escalation path",
    "Clinic":                   "Cancel Clinic Rules (Jun 2026), Clinic Tallies (Oct 2026)",
    "Bug (unclassified)":       "Review with engineering — triage individually",
    "Feature request (unclassified)": "Review individually",
}

THEME_NOTES = {
    "Integration": (
        "MedHub is the loudest integration signal — customers report the schedule sync breaks silently "
        "and they only discover it when MedHub calls them. NI users are asking for CSV export as a "
        "workaround. One customer noted the Amion ↔ MedHub problem started July 25th and persisted "
        "through multiple support threads. ECW and Qgenda requests are one-offs and likely don't "
        "reflect a broad residency need."
    ),
    "Migration / Import": (
        "Migration interest is real but fragmented. Customers are asking 'can I import from NI or Excel?' "
        "suggesting they don't know a path exists yet — a communication/documentation gap as much as a "
        "product gap. The 'OnCloud and Next for Residency' ticket is a direct migration demo request. "
        "CSV import (Jul 2026) directly addresses this cluster."
    ),
    "Academic Year": (
        "AY tickets are mostly about historical data access (graduated residents, past-year schedules) "
        "and adding new incoming staff. The 'past academic years migrated' ticket explicitly requests "
        "historical AY migration — this isn't just about Next AY visibility, it's about continuity of "
        "record. AY Rollover (Jun 2026) and AY Lock (Apr 2026) address the forward-looking side; "
        "historical migration needs its own answer."
    ),
    "Block / Rotation": (
        "Block bugs are the most concrete, actionable signals. Split shifts not showing up is a Classic "
        "parity issue reported multiple times. The 'Block dates on Amion.com not matching Amion Online' "
        "is a viewer/manager sync issue — potentially separate from the Multiple Splits work. EM "
        "programs setting up their first Amion schedule surface onboarding complexity alongside real "
        "feature gaps."
    ),
    "Viewer / Visibility": (
        "Two distinct sub-problems: (1) residents/fellows who can't access the schedule at all — "
        "likely a permissions or viewer setup issue; (2) programs wanting to make schedules visible to "
        "non-scheduled clinic staff (attendings, nurses) who aren't on the rotation. The second is "
        "a feature gap — Viewer today requires being on the schedule to access it."
    ),
    "Notifications": (
        "84 keyword hits across all tickets vs. 0 classified tickets suggests notifications issues "
        "are buried inside other ticket types — e.g., 'I changed the schedule but residents didn't "
        "get notified.' Not a standalone feature request but a consistent pain point woven through "
        "block, call, and viewer tickets. Worth a targeted CS audit."
    ),
    "Clinic": (
        "Clinic tickets cluster around two things: adding fellows to clinic schedules and making clinic "
        "schedules visible to non-scheduled staff (same theme as Viewer). Continuity clinic builder "
        "(Jul 2026) and cancel clinic rules (Jun 2026) address the setup side; visibility is shared "
        "with the Viewer work."
    ),
}


def run_analysis(rows: list[dict]) -> dict:
    # Classify every row
    classified: list[dict] = []
    for r in rows:
        sig_type, sub_theme = classify(r["source"], r["title"], r["notes"])
        summary = pm_summary(r["source"], r["title"], r["notes"], sub_theme)
        classified.append({**r, "sig_type": sig_type, "sub_theme": sub_theme, "summary": summary})

    # Count by type
    type_counts: dict[str, int] = {}
    type_rows: dict[str, list] = defaultdict(list)
    for c in classified:
        type_counts[c["sig_type"]] = type_counts.get(c["sig_type"], 0) + 1
        type_rows[c["sig_type"]].append(c)

    # Count feature signals by sub-theme
    feature_rows = type_rows.get("FEATURE", [])
    sub_counts: dict[str, int] = {}
    sub_rows: dict[str, list] = defaultdict(list)
    for c in feature_rows:
        sub_counts[c["sub_theme"]] = sub_counts.get(c["sub_theme"], 0) + 1
        sub_rows[c["sub_theme"]].append(c)

    # Canny posts (separate)
    canny_rows = [r for r in rows if r["source"] == "Canny"]

    total = len(classified)
    return {
        "total": total,
        "type_counts": type_counts,
        "type_rows": type_rows,
        "feature_count": len(feature_rows),
        "sub_counts": sub_counts,
        "sub_rows": sub_rows,
        "canny_rows": canny_rows,
        "classified": classified,
    }


# ── spreadsheet writer ────────────────────────────────────────────────────────

def add_or_get_sheet(sheets_svc, sheet_title: str) -> int:
    """Add 'Signal Analysis' tab if it doesn't exist. Return sheetId."""
    meta = sheets_svc.spreadsheets().get(spreadsheetId=SS_ID).execute()
    for s in meta.get("sheets", []):
        if s["properties"]["title"] == sheet_title:
            return s["properties"]["sheetId"]
    resp = sheets_svc.spreadsheets().batchUpdate(
        spreadsheetId=SS_ID,
        body={"requests": [{"addSheet": {"properties": {"title": sheet_title}}}]},
    ).execute()
    return resp["replies"][0]["addSheet"]["properties"]["sheetId"]


def build_tab(analysis: dict) -> tuple[list[list], list[dict]]:
    """Build (values, row_meta) for the Signal Analysis tab.

    row_meta items: {"type": "title"|"section"|"header"|"data"|"blank"|"note",
                     "bg": hex_or_None, "bold": bool}
    """
    rows: list[list] = []
    meta: list[dict] = []

    def add(row, row_type, bg=None, bold=False, italic=False, wrap=False):
        rows.append(row)
        meta.append({"type": row_type, "bg": bg, "bold": bold, "italic": italic, "wrap": wrap})

    total = analysis["total"]
    type_counts = analysis["type_counts"]

    # ── Title ────────────────────────────────────────────────────────────────
    add(["RESIDENCY CUSTOMER SIGNAL ANALYSIS — Critical Review"] + [""]*5,
        "title", bg=DARK_BLUE, bold=True)

    # ── Sub-title ────────────────────────────────────────────────────────────
    zd_ct = type_counts.get("NOISE",0)+type_counts.get("SALES",0)+type_counts.get("ACCOUNT",0) \
            +type_counts.get("TRAINING",0)+type_counts.get("FEATURE",0)+type_counts.get("OTHER",0)
    add([f"{total} signals matched 'residency' (Amion brand, last 12 mo). "
         f"After critical filtering, {analysis['feature_count']} are true product signals. "
         f"See breakdown below — many tickets are phone logs, pricing, or onboarding requests."]
        + [""]*5,
        "note", bg="#EFF3FB", italic=True, wrap=True)

    add([""] * 6, "blank")

    # ────────────────────────────────────────────────────────────────────────
    # SECTION 1: SIGNAL QUALITY AUDIT
    # ────────────────────────────────────────────────────────────────────────
    add(["SECTION 1 — SIGNAL QUALITY AUDIT: What's in these 499 tickets?"] + [""]*5,
        "section", bg=SECTION_BG["AUDIT"], bold=True)

    add(["Signal Type", "Category", "Count", "% of Total", "What it is", "PM Implication"],
        "header", bg=HEADER_GRAY, bold=True)

    type_rows_display = [
        ("NOISE",    "Phone call transcripts",
         "Zendesk auto-logs inbound phone support calls. These have titles like "
         "'Call with +1 (570) 862-8762' and contain zero scheduling content.",
         "Filter out. Do not count toward residency signal volume."),
        ("SALES",    "Pricing / Demo / Churn / Billing",
         "New programs evaluating Amion, programs leaving, billing questions. "
         "Real customer interactions but not product feature signals.",
         "Route to Sales/CS. Track churn reasons separately."),
        ("ACCOUNT",  "Account mgmt (passwords, access codes, admin)",
         "Coordinators resetting passwords, changing access codes, requesting admin rights. "
         "CS labor but not a product gap.",
         "Potential product: self-serve access code management. Not roadmap priority."),
        ("TRAINING", "Onboarding / How-to questions",
         "Coordinators asking how to use existing Amion features — adding fellows, "
         "publishing schedules, refresher videos. Signals Academy / documentation gap.",
         "Investment in Amion Academy and guided setup, not new features."),
        ("FEATURE",  "True product / feature signals",
         "Specific bugs, missing features, migration requests, integration failures. "
         f"{analysis['feature_count']} tickets — broken down by sub-theme below.",
         "This is the roadmap-relevant cohort. See Section 2."),
        ("OTHER",    "Unclassified / general support",
         "Tickets that mention 'residency' but don't clearly fall into above categories. "
         "Mix of follow-ups, generic help, edge cases.",
         "Low signal. Review individually if volume warrants."),
    ]

    for sig_type, category, what_it_is, pm_impl in type_rows_display:
        count = type_counts.get(sig_type, 0)
        pct = f"{count/total*100:.1f}%"
        add([sig_type, category, count, pct, what_it_is, pm_impl],
            "data", bg=SIGNAL_BG.get(sig_type, "#FFFFFF"), wrap=True)

    # Total row
    add(["TOTAL", "", total, "100%", "", ""],
        "data", bg=HEADER_GRAY, bold=True)

    add([""] * 6, "blank")

    # ────────────────────────────────────────────────────────────────────────
    # SECTION 2: FEATURE SIGNAL BREAKDOWN
    # ────────────────────────────────────────────────────────────────────────
    feat_total = analysis["feature_count"]
    add([f"SECTION 2 — FEATURE SIGNAL BREAKDOWN: {feat_total} actionable product signals"] + [""]*5,
        "section", bg=SECTION_BG["FEATURE"], bold=True)

    add(["Sub-theme", "Count", "% of Features", "Severity", "Key Finding", "Roadmap Feature"],
        "header", bg=HEADER_GRAY, bold=True)

    sub_counts = analysis["sub_counts"]
    # Sort by count desc
    for sub_theme, count in sorted(sub_counts.items(), key=lambda x: -x[1]):
        pct = f"{count/feat_total*100:.1f}%" if feat_total else "—"
        sev = SEVERITY_MAP.get(sub_theme, "L")
        note = THEME_NOTES.get(sub_theme, "")[:200]
        roadmap = ROADMAP_MAP.get(sub_theme, "Review")
        add([sub_theme, count, pct, sev, note, roadmap],
            "data", bg=SEVERITY_BG.get(sev, "#FFFFFF"), wrap=True)

    add([""] * 6, "blank")

    # ────────────────────────────────────────────────────────────────────────
    # SECTION 3: CANNY FEATURE REQUESTS
    # ────────────────────────────────────────────────────────────────────────
    canny_rows = analysis["canny_rows"]
    add([f"SECTION 3 — CANNY FEATURE REQUESTS ({len(canny_rows)} posts matching 'residency')"] + [""]*5,
        "section", bg=SECTION_BG["CANNY"], bold=True)

    add(["Board", "Title", "Votes", "Status", "What it's requesting", "Signal strength"],
        "header", bg=HEADER_GRAY, bold=True)

    for c in sorted(canny_rows, key=lambda x: int(x["votes"]) if str(x["votes"]).isdigit() else 0, reverse=True):
        votes = c["votes"]
        title = c["title"]
        t, n = title.lower(), c["notes"].lower()
        # Generate a useful description
        if "templated" in t or "template" in t:
            desc = "Customer wants multi-week repeating schedule templates. Related to Call & Shift Patterns."
        elif "linked schedule" in t:
            desc = "VA Palo Alto uses Stanford schedule linked in their facility index — display is broken."
        elif "403" in t:
            desc = "Classic admins getting 403 errors clicking into timesheet. Auth/permission bug."
        elif "import" in t or "excel" in t or "csv" in t:
            desc = "Request to import schedule data from Excel/CSV — aligns with CSV Import feature."
        elif "residency" in t and ("viewer" in t or "view" in t):
            desc = "Residency-specific viewer improvement request."
        else:
            desc = c["notes"][:200] if c["notes"] else title
        v = int(votes) if str(votes).isdigit() else 0
        strength = "High — active feature votes" if v > 10 else "Medium" if v > 3 else "Low / informational"
        add([c.get("board", ""), title, votes, c["status"], desc, strength],
            "data", bg="#EFF3FB", wrap=True)

    add([""] * 6, "blank")

    # ────────────────────────────────────────────────────────────────────────
    # SECTION 4: TICKET DEEP-DIVE
    # ────────────────────────────────────────────────────────────────────────
    add(["SECTION 4 — TICKET DEEP-DIVE: Representative examples by theme (no need to open Zendesk)"]
        + [""]*5,
        "section", bg=SECTION_BG["DEEPDIVE"], bold=True)

    add(["Source", "Ticket Title", "Date", "What this ticket is REALLY about",
         "Signal type", "Roadmap Tie"],
        "header", bg=HEADER_GRAY, bold=True)

    sub_rows = analysis["sub_rows"]
    THEME_ORDER = [
        "Block / Rotation", "Academic Year", "Migration / Import", "Integration",
        "Viewer / Visibility", "Clinic", "Notifications",
        "Bug (unclassified)", "Feature request (unclassified)",
    ]

    for sub_theme in THEME_ORDER:
        tickets = sub_rows.get(sub_theme, [])
        if not tickets:
            continue
        # Theme sub-header
        add([f"  {sub_theme.upper()}  ({len(tickets)} signals)"] + [""]*5,
            "theme_header", bg=SECTION_BG["THEME"], bold=True)
        # Note row
        theme_note = THEME_NOTES.get(sub_theme, "")
        if theme_note:
            add(["Note", theme_note[:350], "", "", "", ""],
                "note", bg="#FAFAFA", italic=True, wrap=True)
        # Top 8 tickets by recency
        sample = sorted(tickets, key=lambda x: x.get("date", ""), reverse=True)[:8]
        for t in sample:
            add([
                t["source"],
                t["title"][:80],
                t["date"],
                t["summary"],
                sub_theme,
                ROADMAP_MAP.get(sub_theme, ""),
            ], "ticket", wrap=True)
        add([""] * 6, "blank")

    # Also show TRAINING and SALES briefly (CS load signal)
    for sig_type, label in [("TRAINING", "TRAINING / ONBOARDING (CS Load Signal)"),
                              ("SALES", "SALES / PRICING / CHURN (Business Signal)")]:
        tickets = analysis["type_rows"].get(sig_type, [])
        if not tickets:
            continue
        add([f"  {label}  ({len(tickets)} tickets)"] + [""]*5,
            "theme_header", bg=SECTION_BG["THEME"], bold=True)
        sample = sorted(tickets, key=lambda x: x.get("date", ""), reverse=True)[:5]
        for t in sample:
            add([t["source"], t["title"][:80], t["date"], t["summary"], sig_type, ""],
                "ticket", wrap=True)
        add([""] * 6, "blank")

    return rows, meta


def write_analysis(sheets_svc, sheet_id: int, rows, meta) -> None:
    """Write values, then apply formatting."""
    # Write values
    sheets_svc.spreadsheets().values().update(
        spreadsheetId=SS_ID,
        range="'Signal Analysis'!A1",
        valueInputOption="RAW",
        body={"values": rows},
    ).execute()

    reqs: list[dict] = []
    sid = sheet_id

    # Merge + format each row
    for i, m in enumerate(meta):
        bg = m.get("bg")
        bold = m.get("bold", False)
        italic = m.get("italic", False)
        wrap = m.get("wrap", False)
        row_type = m["type"]

        if row_type == "title":
            reqs.append(merge(sid, i, 0, NUM_COLS))
            reqs.append(fmt(sid, i, i+1, 0, NUM_COLS, bg=bg, bold=True, fg=WHITE, sz=13))

        elif row_type in ("section",):
            reqs.append(merge(sid, i, 0, NUM_COLS))
            reqs.append(fmt(sid, i, i+1, 0, NUM_COLS, bg=bg, bold=True, fg=BLACK))

        elif row_type == "theme_header":
            reqs.append(merge(sid, i, 0, NUM_COLS))
            reqs.append(fmt(sid, i, i+1, 0, NUM_COLS, bg=bg, bold=True, fg=BLACK))

        elif row_type == "header":
            reqs.append(fmt(sid, i, i+1, 0, NUM_COLS, bg=bg, bold=True, fg=WHITE))

        elif row_type == "data":
            if bg:
                reqs.append(fmt(sid, i, i+1, 0, NUM_COLS, bg=bg))
            if bold:
                reqs.append(fmt(sid, i, i+1, 0, NUM_COLS, bold=True))
            if wrap:
                reqs.append(fmt(sid, i, i+1, 0, NUM_COLS, wrap="WRAP"))

        elif row_type == "note":
            reqs.append(merge(sid, i, 0, NUM_COLS))
            if bg:
                reqs.append(fmt(sid, i, i+1, 0, NUM_COLS, bg=bg))
            if italic:
                reqs.append(fmt(sid, i, i+1, 0, NUM_COLS, ital=True))
            if wrap:
                reqs.append(fmt(sid, i, i+1, 0, NUM_COLS, wrap="WRAP"))

        elif row_type == "ticket":
            if wrap:
                reqs.append(fmt(sid, i, i+1, 3, 4, wrap="WRAP"))  # summary col
            reqs.append(fmt(sid, i, i+1, 0, NUM_COLS, bg="#FFFFFF"))

    # Severity cell colors in Section 2 (column D = index 3)
    for i, m in enumerate(meta):
        if m["type"] == "data" and m.get("bg") in SEVERITY_BG.values():
            # Already colored the row — override col D specifically with severity chip
            pass  # row bg is enough

    # Freeze row 0
    reqs.append(freeze_rows(sid, 1))

    # Column widths: A=130, B=280, C=70, D=90, E=360, F=200
    for col, px in enumerate([130, 280, 70, 90, 360, 200]):
        reqs.append(cw(sid, col, px))

    # Row heights — make data/ticket rows taller
    for i, m in enumerate(meta):
        if m["type"] in ("data", "ticket", "note") and m.get("wrap"):
            reqs.append({"updateDimensionProperties": {
                "range": {"sheetId": sid, "dimension": "ROWS",
                          "startIndex": i, "endIndex": i+1},
                "properties": {"pixelSize": 80},
                "fields": "pixelSize",
            }})

    sheets_svc.spreadsheets().batchUpdate(
        spreadsheetId=SS_ID,
        body={"requests": reqs},
    ).execute()


def main():
    print("=" * 60)
    print("Signal Analysis — Residency Roadmap")
    print(f"Spreadsheet: {SS_ID}")
    print("=" * 60)

    svc = get_sheets_service()

    print("\nReading Customer Signals tab...")
    raw_rows = read_signals(svc)
    print(f"  {len(raw_rows)} rows read")

    print("Running analysis...")
    analysis = run_analysis(raw_rows)
    tc = analysis["type_counts"]
    print(f"  NOISE={tc.get('NOISE',0)}  SALES={tc.get('SALES',0)}  "
          f"ACCOUNT={tc.get('ACCOUNT',0)}  TRAINING={tc.get('TRAINING',0)}  "
          f"FEATURE={tc.get('FEATURE',0)}  OTHER={tc.get('OTHER',0)}")
    print(f"  Feature sub-themes: {dict(sorted(analysis['sub_counts'].items(), key=lambda x:-x[1]))}")

    print("\nAdding Signal Analysis tab...")
    sheet_id = add_or_get_sheet(svc, "Signal Analysis")
    print(f"  Sheet ID: {sheet_id}")

    print("Building tab content...")
    rows, meta = build_tab(analysis)
    print(f"  {len(rows)} rows to write")

    print("Writing values + formatting...")
    write_analysis(svc, sheet_id, rows, meta)

    print("\n" + "=" * 60)
    print("✓ Signal Analysis tab added!")
    print(f"  https://docs.google.com/spreadsheets/d/{SS_ID}")
    print("=" * 60)


if __name__ == "__main__":
    main()
