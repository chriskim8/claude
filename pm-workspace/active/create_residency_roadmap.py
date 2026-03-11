"""Create the Residency Roadmap Google Spreadsheet.

Fetches live data from Canny, Zendesk, and Jira, then creates a formatted
Google Sheet matching the Operation Surge spreadsheet style.

Run: cd ~/pm-workspace && python3 active/create_residency_roadmap.py
"""

from __future__ import annotations

import os
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta

# ── path setup ──────────────────────────────────────────────────────────────
# All three service directories have a `config.py` that would conflict if
# added to sys.path simultaneously. Load each module directly via importlib.

import importlib.util as _ilu  # noqa: E402
import requests as _req  # noqa: E402

_GOOGLE  = os.path.expanduser("~/google-services")
_CANNY   = os.path.expanduser("~/canny")
_ZENDESK = os.path.expanduser("~/zendesk")


def _load_pkg(pkg_dir: str, module_names: list[str]) -> dict:
    """Load a list of modules from pkg_dir into isolated namespaces."""
    mods: dict[str, object] = {}
    for name in module_names:
        path = os.path.join(pkg_dir, f"{name}.py")
        spec = _ilu.spec_from_file_location(f"_{pkg_dir}_{name}", path,
                                            submodule_search_locations=[])
        mod = _ilu.module_from_spec(spec)
        sys.modules[f"_{pkg_dir}_{name}"] = mod
        mods[name] = (spec, mod)
    loaded: dict[str, object] = {}
    for name, (spec, mod) in mods.items():
        sys.modules["config"] = mods.get("config", (None, None))[1]  # type: ignore
        spec.loader.exec_module(mod)
        loaded[name] = mod
    sys.modules.pop("config", None)
    return loaded


_g = _load_pkg(_GOOGLE, ["config", "google_client"])
_google_client = _g["google_client"]
get_sheets_service = _google_client.get_sheets_service  # type: ignore
get_drive_service  = _google_client.get_drive_service   # type: ignore
get_gmail_service  = _google_client.get_gmail_service   # type: ignore

_c = _load_pkg(_CANNY, ["config", "canny_client"])
_canny_client = _c["canny_client"]
canny_request = _canny_client.canny_request  # type: ignore

_z = _load_pkg(_ZENDESK, ["config", "zendesk_client"])
_zd_client = _z["zendesk_client"]
zendesk_request = _zd_client.zendesk_request  # type: ignore


# ── helpers ──────────────────────────────────────────────────────────────────

def rgb(hex_color: str) -> dict:
    """Convert #RRGGBB string to Sheets API color object (0–1 floats)."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return {"red": r / 255, "green": g / 255, "blue": b / 255}


def cell_fmt(
    sheet_id: int,
    start_row: int, end_row: int,
    start_col: int, end_col: int,
    **kwargs,
) -> dict:
    """Build a repeatCell request."""
    fmt: dict = {}
    fields: list[str] = []

    if "bg" in kwargs:
        fmt["backgroundColor"] = rgb(kwargs["bg"])
        fields.append("userEnteredFormat.backgroundColor")
    if "bold" in kwargs:
        fmt.setdefault("textFormat", {})["bold"] = kwargs["bold"]
        fields.append("userEnteredFormat.textFormat.bold")
    if "italic" in kwargs:
        fmt.setdefault("textFormat", {})["italic"] = kwargs["italic"]
        fields.append("userEnteredFormat.textFormat.italic")
    if "fg" in kwargs:
        fmt.setdefault("textFormat", {})["foregroundColor"] = rgb(kwargs["fg"])
        fields.append("userEnteredFormat.textFormat.foregroundColor")
    if "font_size" in kwargs:
        fmt.setdefault("textFormat", {})["fontSize"] = kwargs["font_size"]
        fields.append("userEnteredFormat.textFormat.fontSize")
    if "wrap" in kwargs:
        fmt["wrapStrategy"] = kwargs["wrap"]
        fields.append("userEnteredFormat.wrapStrategy")
    if "valign" in kwargs:
        fmt["verticalAlignment"] = kwargs["valign"]
        fields.append("userEnteredFormat.verticalAlignment")
    if "halign" in kwargs:
        fmt["horizontalAlignment"] = kwargs["halign"]
        fields.append("userEnteredFormat.horizontalAlignment")

    return {
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": start_row,
                "endRowIndex": end_row,
                "startColumnIndex": start_col,
                "endColumnIndex": end_col,
            },
            "cell": {"userEnteredFormat": fmt},
            "fields": ",".join(fields),
        }
    }


def merge_cells(sheet_id: int, row: int, start_col: int, end_col: int) -> dict:
    return {
        "mergeCells": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": row,
                "endRowIndex": row + 1,
                "startColumnIndex": start_col,
                "endColumnIndex": end_col,
            },
            "mergeType": "MERGE_ALL",
        }
    }


def col_width(sheet_id: int, col: int, pixels: int) -> dict:
    return {
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "COLUMNS",
                "startIndex": col,
                "endIndex": col + 1,
            },
            "properties": {"pixelSize": pixels},
            "fields": "pixelSize",
        }
    }


def row_height(sheet_id: int, start_row: int, end_row: int, pixels: int) -> dict:
    return {
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "ROWS",
                "startIndex": start_row,
                "endIndex": end_row,
            },
            "properties": {"pixelSize": pixels},
            "fields": "pixelSize",
        }
    }


def freeze(sheet_id: int, rows: int = 2, cols: int = 0) -> dict:
    return {
        "updateSheetProperties": {
            "properties": {
                "sheetId": sheet_id,
                "gridProperties": {"frozenRowCount": rows, "frozenColumnCount": cols},
            },
            "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount",
        }
    }


# ── color constants ──────────────────────────────────────────────────────────
DARK_BLUE   = "#1F3864"
HEADER_GRAY = "#434343"
WHITE       = "#FFFFFF"
BLACK       = "#000000"

SECTION_COLORS = {
    "BLOCK SCHEDULE":        "#C9DAF8",
    "CALL & SHIFT SCHEDULE": "#D9D2E9",
    "CLINIC SCHEDULE":       "#D9EAD3",
    "ACADEMIC YEAR":         "#FFF2CC",
    "MIGRATION":             "#F4CCCC",
    "INTEGRATIONS":          "#D0E4F1",
    "AUTOMATION":            "#FCE5CD",
}

STATUS_COLORS = {
    "Shipped":     "#B7E1CD",
    "In QA":       "#FFF2CC",
    "In Dev":      "#FFF2CC",
    "Not Started": "#FFFFFF",
    "Backlog":     "#F3F3F3",
    "Accepted":    "#CFE2F3",
}

# Status chip colors — (bg_hex, fg_hex) tuples
STATUS_CHIP: dict[str, tuple[str, str]] = {
    "Shipped":     ("#274E13", "#FFFFFF"),  # dark green + white
    "In QA":       ("#FFE599", "#7F6000"),  # amber + dark amber
    "In Dev":      ("#9FC5E8", "#073763"),  # blue + dark blue
    "Not Started": ("#EFEFEF", "#555555"),  # light gray + charcoal
    "Backlog":     ("#F3F3F3", "#888888"),  # lightest gray + medium gray
    "Accepted":    ("#CFE2F3", "#073763"),  # light blue + dark blue
}

# Delivery chip colors — (bg_hex, fg_hex) tuples by urgency tier
# Tier 0: Shipped          — green
# Tier 1: Mar–Apr 2026     — amber (imminent, < 2 months)
# Tier 2: May–Jul 2026     — blue  (near-term, 3–5 months)
# Tier 3: Aug–Oct 2026     — purple (mid-term, 6–8 months)
# Tier 4: Nov 2026+        — gray  (far-term, 9+ months)
# TBD                      — lightest gray
DELIVERY_CHIP: dict[str, tuple[str, str]] = {
    "Shipped":  ("#B7E1CD", "#0A5C2D"),
    "Mar 2026": ("#FFE599", "#7F6000"),
    "Apr 2026": ("#FFE599", "#7F6000"),
    "May 2026": ("#9FC5E8", "#073763"),
    "Jun 2026": ("#9FC5E8", "#073763"),
    "Jul 2026": ("#9FC5E8", "#073763"),
    "Aug 2026": ("#B4A7D6", "#20124D"),
    "Sep 2026": ("#B4A7D6", "#20124D"),
    "Oct 2026": ("#B4A7D6", "#20124D"),
    "Nov 2026": ("#D9D9D9", "#3C3C3C"),
    "Dec 2026": ("#D9D9D9", "#3C3C3C"),
    "TBD":      ("#F3F3F3", "#666666"),
}

# ── Delivery date sort order ─────────────────────────────────────────────────
DELIVERY_SORT: dict[str, int] = {
    "Shipped":  0,
    "Mar 2026": 1,
    "Apr 2026": 2,
    "May 2026": 3,
    "Jun 2026": 4,
    "Jul 2026": 5,
    "Aug 2026": 6,
    "Sep 2026": 7,
    "Oct 2026": 8,
    "Nov 2026": 9,
    "Dec 2026": 10,
    "TBD":      99,
}

# ── Jira status mapping ──────────────────────────────────────────────────────
JIRA_STATUS_MAP = {
    "Backlog":      "Not Started",
    "To Do":        "Not Started",
    "In Progress":  "In Dev",
    "In Review":    "In Dev",
    "Ready for QA": "In QA",
    "In QA":        "In QA",
    "Accepted":     "Accepted",
    "Done":         "Shipped",
    "Closed":       "Shipped",
    "Won't Do":     "Backlog",
    "Duplicate":    "Backlog",
}


# ── feature data ─────────────────────────────────────────────────────────────
# Tuple: (name, status, effort, jira, delivery, priority, notes)
# Status: "Shipped" | "In Dev" | "In QA" | "Not Started" — live Jira overrides non-Shipped
# Notes: written from the scheduler/resident perspective — what they gain

FEATURES = {
    "BLOCK SCHEDULE": [
        ("Block Splits",
         "In Dev", "4 wk", "AMIONMGR-3188", "Mar 2026", "P1",
         "Split one block period into two service assignments with independent dates. "
         "Core for ARMC and any program with mid-block service changes."),
        ("Rotation Tallies & Staffing Requirements",
         "Not Started", "6 wk", "AMIONMGR-3134", "Sep 2026", "P1",
         "Live per-resident rotation count (red = short, yellow = over target) plus "
         "min/max staff targets per service — coverage gaps visible without a separate report."),
        ("Cross-Coverage Assignments",
         "Not Started", "2 wk", "AMIONMGR-3134", "Sep 2026", "P2",
         "Designate backup coverage for a service when the assigned resident is out. "
         "Visible across block, call, and shift views."),
        ("Compliance Flags & Schedule Lock",
         "Not Started", "6 wk", "AMIONMGR-3134", "Oct 2026", "P2",
         "Visual flags for duty-hour violations and dual assignments. Lock prevents "
         "accidental structural changes once setup is finalized."),
        ("Resident Preference Requests",
         "Not Started", "4 wk", "AMIONMGR-3286", "Nov 2026", "P1",
         "Time-limited window for residents to submit vacation and rotation preferences "
         "before the schedule is built. Approved requests import in one step."),
        ("View Options (Service View, Sort by Level, Condensed / Extended)",
         "Not Started", "6 wk", "AMIONMGR-3134", "TBD", "P3",
         "Toggle service-centric view; sort by PGY level; switch between condensed "
         "13-block and extended 52-week views."),
        ("Repeating Block Patterns & Coverage Groups",
         "Not Started", "4 wk", "AMIONMGR-3134", "TBD", "P2",
         "Enter the first block of a repeating structure and Amion fills the rest (e.g., 4+1). "
         "Group services so resident counts combine in tally reports."),
    ],
    "CALL & SHIFT SCHEDULE": [
        ("Call & Shift Patterns",
         "Not Started", "4 wk", "AMIONMGR-3293", "Jun 2026", "P1",
         "Named patterns fill in repeating call structures (Q4 overnight, alternate weekends, "
         "night float) automatically. The most manual part of call scheduling today."),
        ("Call Tallies & Equity Tracking",
         "Not Started", "4 wk", "AMIONMGR-3315", "Sep 2026", "P2",
         "Per-resident call count with duty-hour flags. Optional point weights "
         "verify equitable distribution beyond raw call counts."),
        ("Custom Schedule Views (Subsets)",
         "Not Started", "4 wk", "AMIONMGR-3293", "TBD", "P2",
         "Named views (e.g., 'ICU Call', 'Night Team') so each viewer group sees "
         "only their relevant services. Essential for programs with 20+ call services."),
        ("Staff Scheduling Preferences",
         "Not Started", "3 wk", "AMIONMGR-3293", "TBD", "P3",
         "Attach shared pagers to call services; designate resident couples "
         "to prefer or avoid the same call nights."),
    ],
    "CLINIC SCHEDULE": [
        ("Continuity Clinic Builder",
         "Not Started", "4 wk", "AMIONMGR-3292", "Jun 2026", "P1",
         "Dedicated view for the recurring resident-clinic relationship, with 4-week "
         "repeating templates and automatic cancellation rules."),
        ("Clinic & Block Schedule Sync",
         "Not Started", "5 wk", "AMIONMGR-3292", "TBD", "P2",
         "Auto-populate clinic assignments from block rotation. Block service shows "
         "inline in the clinic view."),
        ("Clinic Compliance Reporting",
         "Not Started", "4 wk", "AMIONMGR-3292", "Oct 2026", "P2",
         "Per-resident clinic session counts for ACGME documentation. "
         "Replaces the manual export-and-count process."),
    ],
    "ACADEMIC YEAR": [
        ("Academic Year Filtering — All Schedule Types",
         "In QA", "4 wk", "AMIONMGR-2429", "Mar 2026", "P1",
         "Only residents in the selected year appear across all schedule types with correct "
         "PGY labels. Eliminates ghost names from prior or future years."),
        ("Academic Year Lock",
         "Not Started", "2 wk", "AMIONMGR-2429", "Apr 2026", "P1",
         "Control when next year's schedule becomes visible to residents. "
         "Build and review privately before releasing."),
        ("Year Transition Tools",
         "Not Started", "5 wk", "AMIONMGR-3313", "Jun 2026", "P1",
         "Add the incoming class and archive graduating residents in one action. "
         "Replaces a 2–4 hour manual process at every academic year transition."),
        ("Resident Viewer — Year Switching",
         "Not Started", "2 wk", "AMIONMGR-3197", "Sep 2026", "P2",
         "Residents switch between current and next year's schedule once the "
         "program director unlocks the upcoming year."),
        ("Staff Classification & Labels",
         "Not Started", "5 wk", "AMIONMGR-3294", "TBD", "P2",
         "Role labels (Chief, Prelim, Categorical) next to names; guest access for visiting "
         "rotators; support for off-cycle start dates."),
        ("Advanced Program Configuration",
         "Not Started", "5 wk", "AMIONMGR-3294", "TBD", "P3",
         "Cohort / team groupings (A/B/C), granular publish controls by year level, "
         "and time-off category prioritization."),
    ],
    "MIGRATION": [
        ("Staff Setup for Migration",
         "In Dev", "5 wk", "AMIONMGR-3294", "May 2026", "P1",
         "Map year-specific Classic staff types (e.g., 'PGY-1 2024') to standardized training "
         "levels. Required before academic year logic works correctly."),
        ("Clinic Viewer — Frontend Architecture Alignment",
         "Not Started", "TBD", "AMIONMGR-3264", "Jun 2026", "P1",
         "Clinic viewer pages run on a different frontend stack. Blocks all "
         "viewer-side clinic features until resolved."),
    ],
    "INTEGRATIONS": [
        ("CSV Import of Block Schedules",
         "Not Started", "3 wk", "AMIONMGR-3134", "Jul 2026", "P1",
         "Import block assignments from CSV — primary migration path for programs "
         "from MedHub or New Innovations."),
        ("Calendar Subscriptions (iCal / Google / Outlook)",
         "Not Started", "3 wk", "AMIONMGR-3271", "Oct 2026", "P1",
         "One-time personal link syncs block, call, clinic, and shift assignments "
         "to Google, Apple, or Outlook. Top-requested Amion feature."),
        ("MedHub & New Innovations Integration",
         "Not Started", "8 wk", "AMIONMGR-3134", "Oct 2026", "P2",
         "Monitored API connection with failure alerts replaces the silent-failing "
         "flat-file export for 117 MedHub programs and all NI programs."),
        ("ACGME Duty Hours Validation",
         "Not Started", "6 wk", "AMIONMGR-3315", "Oct 2026", "P2",
         "Real-time compliance checking flags violations before publish. "
         "Programs cannot track 80-hour weekly limits by hand."),
        ("Supporting Tools",
         "Not Started", "TBD", "AMIONMGR-3268", "TBD", "P3",
         "Staffing links, announcement banners on Who's On, print calendar, "
         "and lightweight rotation evaluation tool."),
    ],
    "AUTOMATION": [
        ("CP-SAT Autoscheduler — Architecture Spike",
         "Backlog", "2 wk", "AMIONMGR-3319", "TBD", "P2",
         "Investigate feasibility of porting Classic's constraint-based autoscheduler to Next. "
         "Defines solver input schema (rules + patterns as constraints), required infrastructure, "
         "and sequencing relative to patterns and rules engine parity. Spike precedes all build work."),
        ("CP-SAT Autoscheduler — Call & Shift Schedule Generation",
         "Backlog", "TBD", "TBD", "TBD", "P2",
         "Generate optimized call/shift assignments from CallShiftPattern, SequenceRule, and "
         "AvailabilityRule constraints. Requires patterns infrastructure (AMIONMGR-3293), "
         "duty hours validation (AMIONMGR-3315), and spike completion."),
        ("CP-SAT Autoscheduler — Clinic Schedule Validation",
         "Backlog", "TBD", "TBD", "TBD", "P3",
         "Validate generated clinic sessions against cancel rules and rotation constraints. "
         "Requires clinic template expansion (AMIONMGR-3292) and call/shift autoscheduler baseline."),
    ],
}

TAB1_HEADERS = [
    "Feature / Need",
    "Category",
    "Status",
    "Effort",
    "Jira Epic",
    "Est. Delivery",
    "Notes — What users gain",
]

# ── milestone rows ─────────────────────────────────────────────────────────────
# Inserted after the last feature in each delivery-date group.
# Format follows Operation Surge: "Milestone: <customer outcome statement>"
MILESTONES: dict[str, str] = {
    "Mar 2026": (
        "Milestone: Residency Programs Can Build and Preview Their First Academic Year "
        "Schedule in Amion Next"
    ),
    "May 2026": (
        "Milestone: First Single-Specialty Residency Programs Can Start End-to-End Migration"
    ),
    "Jul 2026": (
        "Milestone: Programs Using Block, Call, and Clinic Schedules Can Fully Migrate "
        "to Amion Next"
    ),
    "Sep 2026": (
        "Milestone: ACGME Compliance Baseline Live — Block and Call Coverage Verification "
        "Available in Next"
    ),
    "Oct 2026": (
        "Milestone: All Single Residency Schedule Programs Can Migrate to Amion Next"
    ),
    "Nov 2026": (
        "Milestone: Enterprise Multi-Program Residency Accounts Can Migrate to Amion Next"
    ),
}

# ── technical notes data ──────────────────────────────────────────────────────
# Tuple: (area, status, reference, what_to_resolve, roadmap_impact)
# Matches the column structure in the user's Technical Notes tab.
TECH_NOTES = [
    (
        "Online Edits / Swaps Not Importing for Residency",
        "Done",
        "MOFONETAM-4522",
        "The swap and online edit importers always looked up schedules by the amionc_reference_id. "
        "Since residency schedules have a year appended to them, they never were found and updates "
        "were never applied. This update pulls all years of a schedule and applies the updates to "
        "each one. To keep things limited, the updates are tied to the academic year dates so that "
        "only updates within a month of the academic year are applied to each schedule.",
        "",
    ),
    (
        "Staff Subscription Linking Post-Condensing",
        "Done",
        "AMIONMGR-2401",
        "Confirm that staff subscriptions (paging, messaging) are valid after each residency "
        "migration. The condensing code should handle this today.",
        "",
    ),
    (
        "Move 100% to Amion Next API: Residency & Support All Paging Carriers",
        "Backlog",
        "MOFONETAM-5034",
        "What is the sequencing and effort estimate for MOFONETAM-5034? What Manager prerequisites "
        "(condensing, AY visibility, staff type cleanup) must be complete before the team can start? "
        "Is there a dependency map?",
        "Otherwise, need to manually confirm API data matches for each residency schedule due to "
        "migrate. Do not plan residency viewer milestones against the 75% rollout — Greg Dutcher "
        "confirmed on Feb 4, 2026 that residency schedules are deliberately excluded from the 75% "
        "API migration milestone (MOFONETAM-4883).",
    ),
    (
        "allow_access_service.rb — Cutoff Date Logic Needs a Story",
        "Backlog",
        "AMIONMGR-2644",
        "PR #6009 (Feb 2026) reduced a misfiring Bugsnag alert from residency/condensing/"
        "allow_access_service.rb from fatal to non-fatal, but the underlying cutoff logic was not "
        "fixed — only snoozed.",
        "Without work defined, the cutoff will be missed and orgs may see the wrong residency "
        "schedule or incorrect access switching during migration.",
    ),
    (
        "Performance Stress Testing",
        "Not Started",
        "N/A",
        "Has any performance test been run against Yale-scale residency data? What are current "
        "block schedule render times at 200+ staff? Is a performance test included in the residency "
        "viewer/manager milestone plan, and who is responsible for running it?",
        "Without load/stress testing of condensing and the residency viewer at scale, migration "
        "could cause production incidents (timeouts, slow pages).",
    ),
    (
        "Mobile App Testing for Residency Schedules (iOS / Android)",
        "Not Started",
        "N/A",
        "Has block schedule rendering been tested on mobile for programs with 52 weekly blocks? "
        "Does academic year switching work on mobile for both the manager and viewer apps? Are "
        "calendar subscription iCal deep-links tested on iOS and Android before the feature ships? "
        "What is the current mobile regression testing process as residency features launch, and "
        "who owns it?",
        "The Amion mobile app is the primary interface for residents checking their schedules day "
        "to day. No formal residency-specific mobile testing from Q1FY27 onwards.",
    ),
]


# ── customer signal classification ───────────────────────────────────────────

# Per-theme descriptions synthesized from ticket content
THEME_SUMMARIES: dict[str, str] = {
    "Block / Rotation": (
        "Split shifts not appearing is the most-repeated bug — filed across multiple programs and "
        "dates. Block dates on Amion.com (viewer) differing from Amion Online (manager) is a "
        "separate sync bug that programs only catch when residents notice the mismatch. EM and "
        "Family Medicine programs setting up first-time schedules surface setup complexity alongside "
        "real feature gaps. Block Tally demand is implicit — coordinators asking 'can I see how many "
        "rotations each resident has done?' without naming the feature."
    ),
    "Academic Year": (
        "Two distinct patterns: (1) programs requesting access to past AY schedules for graduated "
        "residents — for ACGME compliance review or evaluation lookback; (2) coordinators adding an "
        "entire incoming PGY-1 class at AY start and finding the per-resident process tedious. The "
        "'past academic years migrated' ticket is explicit — programs need historical data continuity, "
        "not just forward-looking AY management."
    ),
    "Clinic": (
        "Adding fellows and non-resident staff to clinic schedules is the most common ask. The second "
        "cluster: programs want clinic schedules visible to non-scheduled clinical staff (attendings, "
        "nurses, schedulers) who aren't on the rotation. Viewer today requires being on the schedule "
        "to access it — a genuine product gap for clinic coverage visibility. Continuity clinic "
        "builder addresses the setup side; the visibility gap needs its own solution."
    ),
    "Bugs / Product Issues": (
        "Mix of product bugs without a clear feature category: assignments disappearing after edits, "
        "incorrect data displaying after schedule changes, unexpected behavior on state transitions. "
        "Scattered across schedule types without a single root cause. Recommend a dedicated "
        "engineering triage pass — some may connect to known condensing or sync issues."
    ),
    "Migration / Import": (
        "Programs explicitly asking whether Amion can import from New Innovations or Excel. The "
        "phrasing ('can you import schedules from NI or a spreadsheet?') suggests most don't know "
        "a migration path exists — a documentation gap as much as a product gap. One direct "
        "Classic→Next migration demo request ('OnCloud and Next for Residency'). CSV import (Jul "
        "2026) directly addresses this but needs better discovery / CS handoff."
    ),
    "Integration": (
        "MedHub sync is the loudest issue: the Amion↔MedHub connection breaks silently and programs "
        "only discover it when MedHub calls them. One program tracked the break to July 25th across "
        "multiple threads on both sides. NI API failures appear less urgent but are a known pain. "
        "ECW and Qgenda requests are one-offs — not a broad residency demand — but signal that "
        "programs are evaluating Amion's ecosystem reach."
    ),
    "Notifications": (
        "Notification issues are embedded inside other ticket types rather than standalone — "
        "'I updated the schedule but residents weren't notified' or 'attendings didn't receive "
        "the alert.' No direct feature requests for new notification types, but the pattern is "
        "consistent enough to warrant a CS audit. May indicate a gap in how publish events "
        "trigger notifications specifically for residency schedules."
    ),
    "Viewer / Visibility": (
        "Two sub-problems: (1) residents and fellows who can't access the schedule at all — likely "
        "a viewer setup or permissions issue, onboarding gap; (2) programs wanting to share schedules "
        "with non-scheduled clinical staff who aren't on the rotation. The second is a genuine "
        "product gap — Viewer today requires being assigned to the schedule to get access."
    ),
    "General Feature Requests": (
        "Miscellaneous requests: multi-week templated schedules, API access for custom integrations, "
        "linked schedule display improvements (VA Palo Alto/Stanford). Small volume but some may "
        "align with later roadmap work."
    ),
}

SIGNAL_SEVERITY: dict[str, str] = {
    "Block / Rotation":        "H",
    "Academic Year":           "H",
    "Migration / Import":      "H",
    "Integration":             "H",
    "Viewer / Visibility":     "H",
    "Clinic":                  "M",
    "Notifications":           "M",
    "Bugs / Product Issues":   "M",
    "General Feature Requests": "L",
}

THEME_ORDER = [
    "Block / Rotation", "Academic Year", "Migration / Import", "Integration",
    "Clinic", "Viewer / Visibility", "Notifications",
    "Bugs / Product Issues", "General Feature Requests",
]


def is_feature_signal(title: str, notes: str) -> tuple[bool, str]:
    """Return (is_feature, sub_theme). Filters out noise/sales/account/training tickets."""
    t = title.lower()
    n = notes.lower()
    text = t + " " + n

    # NOISE: Zendesk phone call transcripts
    if re.search(r"call (with|from) (\+1|\+\d)", t) or "time of call:" in text:
        return False, ""

    # SALES: pricing, demo, churn
    if any(k in text for k in [
        "free trial", "how much", "cost for amion", "considering to use",
        "no longer let us use", "cancel", "pricing", "order & invoice",
    ]):
        return False, ""
    if "demo" in text and "schedule" not in text:
        return False, ""

    # ACCOUNT: passwords, access codes, admin (not scheduling-related)
    if any(k in text for k in ["password", "access code", "view code", "sign in", "sso",
                                "change your access", "change the access"]):
        return False, ""
    if "admin access" in text and "scheduling" not in text:
        return False, ""

    # TRAINING: how-to questions without bug/feature keywords
    is_bug = any(k in text for k in [
        "bug", "broken", "not working", "not coming", "incorrect", "wrong date",
        "missing", "disappeared", "not showing", "not matching", "not connect",
        "inconsistently", "not sync",
    ])
    is_feature_req = any(k in text for k in [
        "migrat", "import", "integration", "medhub", "new innov", "csv", "excel",
    ])
    if not is_bug and not is_feature_req:
        if any(k in text for k in [
            "refresher", "training guide", "how do i", "how to set up", "how to add",
            "from scratch", "getting started", "please help me", "have forgotten",
            "i am new", "just started",
        ]):
            return False, ""

    # FEATURE: classify sub-theme
    if any(k in text for k in [
        "medhub", "new innov", "ecw", "qgenda", "api access",
        "connecting to", "sync", "integration",
    ]):
        return True, "Integration"
    if any(k in text for k in [
        "migrat", "import schedule", "import from", "switching to", "oncloud",
        "classic", "excel", "spreadsheet", "new innovations or",
    ]):
        return True, "Migration / Import"
    if any(k in text for k in [
        "academic year", "training level", "pgy", "graduation", "graduated",
        "fellow", "incoming", "2024-2025", "2025-2026", "2026-2027", "past academic",
    ]):
        return True, "Academic Year"
    if any(k in text for k in [
        "block", "rotation", "split shift", "split schedule", "block date",
        "tally", "block schedule", "block count", "block service",
    ]):
        return True, "Block / Rotation"
    if any(k in text for k in ["clinic", "continuity"]):
        return True, "Clinic"
    if any(k in text for k in [
        "viewer", "view schedule", "can't see", "cannot see", "resident view",
        "non-scheduled staff", "make schedule viewable", "make the schedule available",
    ]):
        return True, "Viewer / Visibility"
    if any(k in text for k in [
        "notification", "pager", "paging", "email alert",
        "not receiving", "did not receive",
    ]):
        return True, "Notifications"
    if is_bug:
        return True, "Bugs / Product Issues"
    if is_feature_req:
        return True, "General Feature Requests"

    return False, ""


def ticket_summary(title: str, notes: str, sub_theme: str) -> str:
    """Generate a PM-readable description of what a ticket is actually requesting."""
    t = title.strip()
    n = notes.lower().strip().replace("\n", " ")
    nc = notes.strip().replace("\n", " ")

    if "split" in n and ("not coming" in n or "not showing" in n or "not appear" in n):
        return ("Bug: split shift assignments not appearing on the schedule. A Classic parity gap — "
                "split shifts are a core block scheduling feature programs rely on for coverage overlap.")
    if "block date" in n and "not match" in n:
        return ("Block dates on Amion.com (viewer) differ from Amion Online (manager). Viewer/manager "
                "data sync issue — programs see different data depending on which surface they use.")
    if "medhub" in n and any(k in n for k in ["not connect", "problem", "issue", "correctly", "broken"]):
        return ("MedHub↔Amion sync failure. The schedule connection is broken and MedHub is not "
                "pulling current data. Program only discovered the break when MedHub contacted them.")
    if "new innov" in n or "new innovations" in n:
        return ("New Innovations integration — NI pulling schedule data from Amion. Asking about "
                "reliability or workaround if the API connection fails silently.")
    if any(k in n for k in ["import from", "import schedule"]) and any(
            k in n for k in ["new innov", "excel", "spreadsheet"]):
        return ("Feature request: can I bulk-import schedule data from NI or Excel into Amion? "
                "Program is aware of the manual entry burden and wants a CSV/import path.")
    if "switching to" in n or "oncloud" in n or ("migrat" in n and "classic" in n):
        return ("Program requesting a demo or migration conversation to move from Classic to Amion "
                "Next/OnCloud. Direct migration pipeline signal.")
    if "past academic" in n or ("graduated" in n and ("year" in n or "access" in n)):
        return ("Requesting access to or migration of past AY schedule data for graduated residents. "
                "Compliance or evaluation use case — historical continuity, not just forward-looking AY.")
    if "incoming" in n or ("pgy-1" in n and any(k in n for k in ["add", "new", "class"])):
        return ("Coordinator adding all incoming PGY-1s to schedule for the new AY. Finds the "
                "per-resident manual process tedious — maps directly to Bulk Staff Addition.")
    if "fellow" in n and any(k in n for k in ["add", "adding", "list"]):
        return ("Adding fellowship-level staff to the residency schedule. May be a staff type "
                "management issue or a clinic schedule question — fellows often need separate assignments.")
    if any(k in n for k in ["non-scheduled staff", "make schedule viewable", "make the schedule available",
                              "staff members so they c"]):
        return ("Program wants to share the schedule with clinical staff not on the rotation "
                "(attendings, nurses, schedulers). Viewer today requires being assigned — genuine gap.")
    if "viewer" in n or "view schedule" in n:
        return ("Resident or fellow unable to access the schedule in the viewer. Permissions/setup "
                "issue or viewer access bug.")
    if "ecw" in n:
        return ("Integration request with eClinicalWorks (ECW). Program wants schedule data to flow "
                "into their EMR. One-off — not a broad residency demand.")
    if "qgenda" in n:
        return ("Integration request with Qgenda. Program asking if Amion schedule data can display "
                "or sync with Qgenda. Competitive/complementary system question.")
    if "api" in n and "access" in n:
        return ("Request for API access to pull schedule data programmatically. Likely an IT team "
                "building a custom integration or data pipeline.")
    if "clinic" in n and any(k in n for k in ["view", "visible", "access", "available"]):
        return ("Program wants clinic schedule visible to non-scheduled clinical staff. Attendings "
                "or nurses need to see which residents are at clinic without being assigned.")
    if "clinic" in n:
        return (f"Clinic schedule question: '{t[:60]}'. "
                f"{'Adding staff to clinic.' if 'add' in n else 'Clinic scheduling workflow issue.'}")
    if any(k in n for k in ["notification", "pager", "not receiving", "did not receive"]):
        return (f"Notification/alert delivery issue. '{t[:60]}' — residents or attendings not "
                f"receiving schedule change notifications.")
    if any(k in n for k in ["not working", "broken", "bug", "disappeared", "not showing"]):
        return f"Product bug: '{t[:60]}'. {nc[:160]}"
    # Generic fallback
    return f"'{t[:60]}' — {nc[:200]}"


# ── Reddit posts (hard-coded from manual research) ────────────────────────────
# Tuple: (subreddit, title, date, score, url, key_signal, theme)
REDDIT_POSTS = [
    (
        "r/Residency",
        "Anybody else feel like Amion has gotten a million times worse since Doximity bought it?",
        "2024-02-11", 279,
        "https://www.reddit.com/r/Residency/comments/1aojabc/anybody_else_feel_like_amion_has_gotten_a_million/",
        "\"We filed a patient safety event during my EM clerkship because the new log in procedure almost delayed a trauma page.\" (↑162) / \"The magic was logging on from anywhere as long as you knew your org's password.\" (↑116) / \"Only able to view 2 weeks at a time now.\" (↑116)",
        "Login / UX Regression",
    ),
    (
        "r/Residency",
        "AMiON",
        "2021-01-10", 95,
        "https://www.reddit.com/r/Residency/comments/kumvyn/amion/",
        "\"As an aside, it makes Cerner look well designed. It's a glorified calendar. How do you [mess] it up so badly?!\" (↑32) / General frustration with Amion UX despite name recognition.",
        "General UX Feedback",
    ),
    (
        "r/Residency",
        "Amion scheduler?",
        "2023-05-27", 18,
        "https://www.reddit.com/r/Residency/comments/13tjdzs/amion_scheduler/",
        "\"Amion syncs to Google and iCal — links at the bottom of the page.\" (↑17) / \"The rule writer and autoscheduler are godsends.\" (↑8) / Post author: \"A well designed Google Sheet would've been miles better.\"",
        "Calendar Sync / Scheduler UX",
    ),
    (
        "r/medicine",
        "Scheduling software for residents",
        "2020-05-26", 14,
        "https://www.reddit.com/r/medicine/comments/gqzsz5/scheduling_software_for_residents/",
        "\"We used amion.com — I just opened their main page and my heart rate jumped 30 bpm. I guess I have more PTSD than I realized.\" (↑14) / ShiftAdmin cited as preferred for EM.",
        "Competitor Comparison",
    ),
    (
        "r/Residency",
        "Is Amion still the best shift scheduling software?",
        "2025-06-04", 9,
        "https://www.reddit.com/r/Residency/comments/1l3cxlr/is_amion_still_the_best_shift_scheduling_software/",
        "\"The biggest problem with Amion is the back end is absolutely atrocious. QGenda is the best one I've used on the user end.\" (↑8) / QGenda mentioned favorably in 4 of 9 comments.",
        "Competitor Comparison",
    ),
    (
        "r/Residency",
        "Scheduling Is The Worst",
        "2025-10-27", 9,
        "https://www.reddit.com/r/Residency/comments/1ohqiog/scheduling_is_the_worst/",
        "\"QGenda is the way.\" (↑10) / \"Have used both Amion and QGenda — I preferred Amion, more user friendly.\" (↑3) / Post author built competing app citing Amion as \"expensive.\"",
        "Competitor Comparison",
    ),
    (
        "r/Residency",
        "Just curious - do most of you have a schedule?",
        "2021-07-03", 10,
        "https://www.reddit.com/r/Residency/comments/ocycej/just_curious_do_most_of_you_have_a_schedule/",
        "\"Radiology resident: I have my whole year schedule with call weekends in Amion, although weekends are freely traded to accommodate life needs.\" (↑9) / Used positively for year-long block + call visibility.",
        "Schedule Visibility / Viewer",
    ),
    (
        "r/Residency",
        "Amion Block to Day sync",
        "2022-06-20", 4,
        "https://www.reddit.com/r/Residency/comments/vgk9ub/amion_block_to_day_sync/",
        "\"We entered our entire block schedule but it didn't populate to the day schedule. Is there a way to do this?\" / Community: \"You have to enter the shift schedule manually.\" Confirms block→day workflow confusion.",
        "Block / Rotation",
    ),
    (
        "r/managers",
        "What is your favorite on-call scheduling software?",
        "2025-06-04", 2,
        "https://www.reddit.com/r/managers/comments/1l3cb8v/what_is_your_favorite_oncall_scheduling_software/",
        "\"We like the Amion feature that we can import the work shift calendar into [external calendar] — trying to cut down on manual input work.\" Calendar integration cited as primary retained value.",
        "Calendar Sync / Viewer",
    ),
    # ── additional posts from expanded search ──────────────────────────────
    (
        "r/Residency",
        "Interest in an automated call scheduling tool?",
        "2023-02-13", 39,
        "https://www.reddit.com/r/Residency/comments/111m91s/interest_in_an_automated_call_scheduling_tool/",
        "Developer posted asking if there's demand for an auto-scheduler; commenter dismissed Amion's capability but another said \"just use amion, it's $300/yr and does all this\" — reveals auto-scheduler is undersold/unknown to potential users.",
        "Feature Request",
    ),
    (
        "r/Residency",
        "How does your program schedule shifts? (EM)",
        "2019-09-06", 19,
        "https://www.reddit.com/r/Residency/comments/d0gr7r/how_does_your_program_schedule_shifts_em/",
        "Radiology commenter: \"we use Amion and just trade call shifts freely\" — positions call swap/trade as a valued differentiator vs. MedRez randomization.",
        "Block / Rotation",
    ),
    (
        "r/Residency",
        "Do you use scheduling software for residents?",
        "2021-03-24", 15,
        "https://www.reddit.com/r/Residency/comments/mc76m9/do_you_use_scheduling_software_for_residents/",
        "Amion first named in response but commenter notes \"great for tracking who was on\" while uncertain about building — highlights perception gap that Amion is a viewer tool, not a builder tool.",
        "General UX Feedback",
    ),
    (
        "r/Residency",
        "Software for scheduling",
        "2024-02-06", 15,
        "https://www.reddit.com/r/Residency/comments/1akmdg9/software_for_scheduling/",
        "Senior resident asked for block/call/vacation scheduling software — nobody mentioned Amion; Excel and ChatGPT suggested instead. Amion not top-of-mind for schedule-building.",
        "Competitor Comparison",
    ),
    (
        "r/Residency",
        "Scheduling Software",
        "2023-09-19", 9,
        "https://www.reddit.com/r/Residency/comments/16n0mfu/scheduling_software/",
        "Incoming chief resident asked for software to reduce manual burden; only substantive reply was \"try Amion with their autoscheduler\" — known solution but no evidence of satisfaction.",
        "Feature Request",
    ),
    (
        "r/Residency",
        "Software programs for rotation/clinic/call scheduling?",
        "2025-12-19", 8,
        "https://www.reddit.com/r/Residency/comments/1pqvcxb/software_programs_for_rotationcliniccall/",
        "Incoming chief explicitly wanted duty-hour compliance + wellness equity; Amion not mentioned at all; QGenda the only recommendation. Amion losing ground in new-adopter consideration set.",
        "Competitor Comparison",
    ),
    (
        "r/Residency",
        "Administrative scheduling advice",
        "2022-03-27", 8,
        "https://www.reddit.com/r/Residency/comments/tpuoen/administrative_scheduling_advice/",
        "Post-acquisition: commenter notes Doximity is \"working on it\" but points to cheaper alternatives (Calerity, Equina) — captures the uncertainty window where programs were watching for improvement.",
        "Migration",
    ),
    (
        "r/Residency",
        "Scheduling software?",
        "2020-04-07", 8,
        "https://www.reddit.com/r/Residency/comments/fwd4ab/scheduling_software/",
        "Chief at large academic program asked for shift software with equity features; Lightning Bolt and SpinFusion recommended — Amion not associated with large-program complex-equity use case.",
        "Competitor Comparison",
    ),
    (
        "r/emergencymedicine",
        "EM Scheduling Software",
        "2025-05-05", 2,
        "https://www.reddit.com/r/emergencymedicine/comments/1kfbtu0/em_scheduling_software/",
        "\"Amion is the worst, don't use it\" (↑4). ShiftAdmin and QGenda dominate EM recommendations — strong negative brand signal in EM segment.",
        "Competitor Comparison",
    ),
    (
        "r/emergencymedicine",
        "Scheduling Software Recs",
        "2024-09-25", 2,
        "https://www.reddit.com/r/emergencymedicine/comments/1fpgit3/scheduling_software_recs/",
        "EM residency program actively switching away from MedRez; only ShiftAdmin recommended — Amion not in consideration set when programs evaluate replacements.",
        "Migration",
    ),
]


# ── live data fetchers ────────────────────────────────────────────────────────

def fetch_gmail_residency_emails() -> list[dict]:
    """Search Gmail for high-value residency-related emails from external senders."""
    print("Fetching Gmail residency emails...")
    gmail_svc = get_gmail_service()

    # Tighter queries — only external-facing, scheduling-specific threads
    queries = [
        "subject:residency amion -from:doximity.com",
        "subject:(block schedule) residency -from:doximity.com",
        "subject:(call schedule) residency -from:doximity.com",
        "subject:(residency migration) amion -from:doximity.com",
        "subject:(residency scheduling) -from:doximity.com",
        "label:sent to:(residency OR scheduler OR chief OR coordinator) amion",
    ]

    # Senders / patterns to filter out (internal, automated, or irrelevant)
    _SKIP_SENDER = re.compile(
        r"doximity\.com|noreply|no-reply|notifications?@|mailer|"
        r"support@amion|billing|zendesk|jira|confluence|github|"
        r"pagerduty|datadog|slack|atlassian",
        re.IGNORECASE,
    )
    # Snippet must contain at least one of these to be considered relevant
    _SIGNAL_KEYWORDS = re.compile(
        r"block|call|shift|clinic|rotation|schedule|migration|residency|"
        r"chief|coordinator|amion|pgy|academic.?year|import|export|"
        r"medhub|new.?innovations|duty.?hour",
        re.IGNORECASE,
    )

    seen_ids: set[str] = set()
    emails: list[dict] = []

    from email.utils import parsedate_to_datetime  # noqa: PLC0415

    for query in queries:
        try:
            result = gmail_svc.users().messages().list(
                userId="me",
                q=query,
                maxResults=50,
            ).execute()
            messages = result.get("messages", [])
            for m in messages:
                mid = m["id"]
                if mid in seen_ids:
                    continue
                seen_ids.add(mid)

                detail = gmail_svc.users().messages().get(
                    userId="me",
                    id=mid,
                    format="metadata",
                    metadataHeaders=["From", "Subject", "Date"],
                ).execute()

                headers = {h["name"]: h["value"]
                           for h in detail.get("payload", {}).get("headers", [])}
                snippet = detail.get("snippet", "")[:300].replace("\r", " ").replace("\n", " ")
                raw_from = headers.get("From", "")

                # Skip internal / automated senders
                if _SKIP_SENDER.search(raw_from):
                    continue

                # Skip if snippet has no scheduling signal
                subject = headers.get("Subject", "")
                if not _SIGNAL_KEYWORDS.search(snippet + " " + subject):
                    continue

                # Parse date
                raw_date = headers.get("Date", "")
                try:
                    dt = parsedate_to_datetime(raw_date)
                    date_str = dt.strftime("%Y-%m-%d")
                except Exception:
                    date_str = raw_date[:10]

                # Clean display name from "Name <addr>" format
                sender = re.sub(r"<[^>]+>", "", raw_from).strip().strip('"') or raw_from

                emails.append({
                    "id":      mid,
                    "subject": subject,
                    "from":    sender[:50],
                    "date":    date_str,
                    "snippet": snippet,
                    "url":     f"https://mail.google.com/mail/u/0/#all/{mid}",
                })
        except Exception as exc:
            print(f"  [Gmail error for query '{query}']: {exc}")

    # Sort newest first; cap at 75
    emails.sort(key=lambda x: x["date"], reverse=True)
    emails = emails[:75]
    print(f"  Gmail: {len(emails)} high-value residency emails (after filtering)")
    return emails


def fetch_canny_residency_posts() -> list[dict]:
    """Fetch all Canny posts with 'residency' in title or details."""
    print("Fetching Canny boards...")
    boards_resp = canny_request("boards/list")
    boards = boards_resp.get("boards", [])
    print(f"  Found {len(boards)} boards")

    posts: list[dict] = []
    for board in boards:
        board_id = board["id"]
        board_name = board["name"]
        skip = 0
        while True:
            resp = canny_request("posts/list", {
                "boardID": board_id,
                "limit": 100,
                "skip": skip,
            })
            batch = resp.get("posts", [])
            if not batch:
                break
            for p in batch:
                title = (p.get("title") or "").lower()
                details = (p.get("details") or "").lower()
                if "residency" in title or "residency" in details:
                    posts.append({
                        "source": "Canny",
                        "title": p.get("title", ""),
                        "board": board_name,
                        "votes": p.get("score", 0),
                        "status": p.get("status", ""),
                        "date": p.get("created", ""),
                        "url": p.get("url", ""),
                        "notes": (p.get("details") or "")[:300].replace("\n", " "),
                    })
            if len(batch) < 100:
                break
            skip += 100
            time.sleep(0.2)

    posts.sort(key=lambda x: x["votes"], reverse=True)
    print(f"  Canny: found {len(posts)} residency posts")
    return posts


def fetch_zendesk_residency_tickets() -> list[dict]:
    """Fetch Zendesk tickets with 'residency' from the past year (Amion brand only)."""
    print("Fetching Zendesk tickets (Amion brand, last 12 months)...")
    since = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    # brand_id:6456809521171 restricts to Amion support tickets only
    query = f"residency brand_id:6456809521171 created>{since}"

    tickets: list[dict] = []
    page = 1
    while True:
        resp = zendesk_request("search.json", params={
            "query": query,
            "sort_by": "created_at",
            "sort_order": "desc",
            "per_page": 100,
            "page": page,
        })
        results = resp.get("results", [])
        if not results:
            break
        for t in results:
            if t.get("result_type") != "ticket":
                continue
            tickets.append({
                "source": "Zendesk",
                "title": t.get("subject", ""),
                "board": "Support",
                "votes": 1,
                "status": t.get("status", ""),
                "date": (t.get("created_at") or "")[:10],
                "url": f"https://doximity.zendesk.com/agent/tickets/{t.get('id', '')}",
                "notes": (t.get("description") or "")[:300].replace("\n", " "),
            })
        if not resp.get("next_page"):
            break
        page += 1
        if page > 5:  # cap at 500 tickets
            break
        time.sleep(0.3)

    print(f"  Zendesk: found {len(tickets)} Amion residency tickets")
    return tickets


def fetch_jira_statuses(jira_keys: list[str]) -> dict[str, str]:
    """Fetch current status for Jira issues. Returns {key: display_status}.

    Only fetches non-TBD keys. Skips keys where the feature is already Shipped
    (caller should filter). Uses credentials from ~/.config/.jira/credentials.
    """
    creds_path = os.path.expanduser("~/.config/.jira/credentials")
    creds: dict[str, str] = {}
    try:
        with open(creds_path) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    creds[k.strip()] = v.strip()
    except FileNotFoundError:
        print(f"  Warning: Jira credentials not found at {creds_path} — skipping live status")
        return {}

    email    = creds.get("JIRA_EMAIL", "")
    token    = creds.get("JIRA_TOKEN", "")
    base_url = creds.get("JIRA_BASE_URL", "https://doximity.atlassian.net")
    auth = (email, token)

    unique_keys = sorted(set(k for k in jira_keys if k and k != "TBD"))
    statuses: dict[str, str] = {}
    print(f"  Fetching Jira status for {len(unique_keys)} tickets: {unique_keys}")

    for key in unique_keys:
        try:
            resp = _req.get(
                f"{base_url}/rest/api/3/issue/{key}",
                auth=auth,
                params={"fields": "status"},
                timeout=10,
            )
            if resp.ok:
                raw = resp.json()["fields"]["status"]["name"]
                mapped = JIRA_STATUS_MAP.get(raw, raw)
                statuses[key] = mapped
                print(f"    {key}: {raw!r} → {mapped!r}")
            else:
                print(f"    {key}: HTTP {resp.status_code} (skipping)")
        except Exception as exc:
            print(f"    {key}: error ({exc})")

    return statuses


def build_canny_signal_map(canny_posts: list[dict]) -> dict[str, int]:
    """Build a keyword → vote-count map for Tab 1 Canny Signal column."""
    keyword_map: dict[str, list[int]] = {}
    keywords = [
        "block", "call", "shift", "clinic", "academic year",
        "training level", "migration", "tally", "pattern",
        "viewer", "marker", "duty hour", "medhub", "new innovations",
        "split", "graduation", "cross-cover",
    ]
    for post in canny_posts:
        text = (post["title"] + " " + post["notes"]).lower()
        for kw in keywords:
            if kw in text:
                keyword_map.setdefault(kw, []).append(post["votes"])
    return {kw: sum(vs) for kw, vs in keyword_map.items()}


def build_zendesk_signal_map(zd_tickets: list[dict]) -> dict[str, int]:
    """Build a keyword → ticket-count map for Tab 1 Zendesk Signal column."""
    keyword_map: dict[str, int] = {}
    keywords = [
        "block", "call", "shift", "clinic", "academic year",
        "training level", "migration", "tally", "pattern",
        "viewer", "marker", "duty hour", "medhub", "new innovations",
        "split", "graduation", "color", "cross-cover", "cross cover",
    ]
    for ticket in zd_tickets:
        text = (ticket["title"] + " " + ticket["notes"]).lower()
        for kw in keywords:
            if kw in text:
                keyword_map[kw] = keyword_map.get(kw, 0) + 1
    return keyword_map


def feature_signal(feature_name: str, notes: str, signal_map: dict[str, int]) -> str:
    """Return a signal value (vote count or ticket count) for a feature row."""
    text = (feature_name + " " + notes).lower()
    total = 0
    for kw, val in signal_map.items():
        if kw in text:
            total += val
    return str(total) if total > 0 else ""


# ── spreadsheet builder ───────────────────────────────────────────────────────

def create_spreadsheet(sheets_svc) -> tuple[str, dict]:
    """Create the spreadsheet and return (spreadsheet_id, sheet_id_map)."""
    body = {
        "properties": {"title": "Residency Roadmap — Amion Next"},
        "sheets": [
            {"properties": {"title": "Residency Roadmap", "index": 0}},
            {"properties": {"title": "Customer Signals", "index": 1}},
            {"properties": {"title": "Technical Notes", "index": 2}},
            {"properties": {"title": "Feature Primer", "index": 3}},
        ],
    }
    result = sheets_svc.spreadsheets().create(body=body).execute()
    ss_id = result["spreadsheetId"]
    sheet_id_map = {
        s["properties"]["title"]: s["properties"]["sheetId"]
        for s in result["sheets"]
    }
    return ss_id, sheet_id_map


def write_values(sheets_svc, ss_id: str, sheet: str, values: list[list],
                 value_input_option: str = "RAW") -> None:
    sheets_svc.spreadsheets().values().update(
        spreadsheetId=ss_id,
        range=f"'{sheet}'!A1",
        valueInputOption=value_input_option,
        body={"values": values},
    ).execute()


def apply_formatting(
    sheets_svc,
    ss_id: str,
    sheet_id_map: dict,
    tab1_row_meta: list,
    tab2_row_meta: list,
    primer_meta: list | None = None,
) -> None:
    """Apply all formatting in a single batchUpdate call."""
    sid_r = sheet_id_map["Residency Roadmap"]
    sid_c = sheet_id_map["Customer Signals"]
    sid_t = sheet_id_map["Technical Notes"]
    sid_p = sheet_id_map["Feature Primer"]
    num_cols = len(TAB1_HEADERS)

    requests_list: list[dict] = []

    # ── Tab 1: Residency Roadmap ─────────────────────────────────────────────

    # Merge + format title row (row 0)
    requests_list.append(merge_cells(sid_r, 0, 0, num_cols))
    requests_list.append(cell_fmt(sid_r, 0, 1, 0, num_cols,
                                  bg=DARK_BLUE, bold=True, fg=WHITE, font_size=13,
                                  valign="MIDDLE"))

    # Header row (row 1)
    requests_list.append(cell_fmt(sid_r, 1, 2, 0, num_cols,
                                  bg=HEADER_GRAY, bold=True, fg=WHITE, valign="MIDDLE"))

    # Per-row formatting based on tab1_row_meta
    for row_idx, meta in enumerate(tab1_row_meta):
        actual_row = row_idx + 2  # offset for title + header rows
        row_type = meta["type"]

        if row_type == "milestone":
            # Milestone rows: merged dark green bar, white bold text, full-width
            requests_list.append(merge_cells(sid_r, actual_row, 0, len(TAB1_HEADERS)))
            requests_list.append(cell_fmt(sid_r, actual_row, actual_row + 1, 0,
                                          len(TAB1_HEADERS),
                                          bg="#274E13", bold=True, fg=WHITE,
                                          font_size=10))

        elif row_type == "feature":
            status = meta["status"]
            delivery = meta.get("delivery", "")

            # Status chip: col C (index 2) — colored bg + contrasting fg + centered bold
            chip = STATUS_CHIP.get(status)
            if chip:
                bg_hex, fg_hex = chip
                requests_list.append(cell_fmt(sid_r, actual_row, actual_row + 1, 2, 3,
                                              bg=bg_hex, fg=fg_hex, bold=True,
                                              halign="CENTER"))

            # Effort column (col D = index 3): plain text, no special formatting

            # Est. Delivery (col F = index 5): colored text only, no bg change
            dchip = DELIVERY_CHIP.get(delivery)
            if dchip:
                _, fg_hex = dchip
                requests_list.append(cell_fmt(sid_r, actual_row, actual_row + 1, 5, 6,
                                              fg=fg_hex, bold=True))

            # Wrap notes column (col G = index 6, last col)
            requests_list.append(cell_fmt(sid_r, actual_row, actual_row + 1, 6, 7,
                                          wrap="WRAP"))

    # Freeze rows 1–2, no column freeze (conflicts with merged title row)
    requests_list.append(freeze(sid_r, rows=2, cols=0))

    # Column widths Tab 1
    col_widths_r = [300, 130, 90, 65, 110, 95, 400]
    for i, w in enumerate(col_widths_r):
        requests_list.append(col_width(sid_r, i, w))

    # ── Tab 2: Customer Signals (combined filtered signals + analysis) ───────
    CS_COLS = 5
    SEV_COLORS = {"H": "#F4CCCC", "M": "#FFF2CC", "L": "#D9EAD3"}
    for row_idx, meta in enumerate(tab2_row_meta):
        rtype = meta["type"]
        bg    = meta.get("bg")
        if rtype == "title":
            requests_list.append(merge_cells(sid_c, row_idx, 0, CS_COLS))
            requests_list.append(cell_fmt(sid_c, row_idx, row_idx + 1, 0, CS_COLS,
                                          bg=DARK_BLUE, bold=True, fg=WHITE, font_size=13,
                                          valign="MIDDLE"))
        elif rtype == "subtitle":
            requests_list.append(merge_cells(sid_c, row_idx, 0, CS_COLS))
            requests_list.append(cell_fmt(sid_c, row_idx, row_idx + 1, 0, CS_COLS,
                                          bg="#EFF3FB", italic=True, wrap="WRAP"))
        elif rtype == "section_hdr":
            requests_list.append(merge_cells(sid_c, row_idx, 0, CS_COLS))
            requests_list.append(cell_fmt(sid_c, row_idx, row_idx + 1, 0, CS_COLS,
                                          bg=bg or "#E8EAED", bold=True, fg=BLACK))
        elif rtype == "col_hdr":
            requests_list.append(cell_fmt(sid_c, row_idx, row_idx + 1, 0, CS_COLS,
                                          bg=HEADER_GRAY, bold=True, fg=WHITE))
        elif rtype == "theme_summary":
            sev = meta.get("sev", "L")
            requests_list.append(cell_fmt(sid_c, row_idx, row_idx + 1, 0, CS_COLS,
                                          bg=SEV_COLORS.get(sev, "#FFFFFF")))
            requests_list.append(cell_fmt(sid_c, row_idx, row_idx + 1, 3, 4, wrap="WRAP"))
        elif rtype == "theme_hdr":
            requests_list.append(merge_cells(sid_c, row_idx, 0, CS_COLS))
            requests_list.append(cell_fmt(sid_c, row_idx, row_idx + 1, 0, CS_COLS,
                                          bg="#E8EAED", bold=True, fg=BLACK))
        elif rtype == "theme_note":
            requests_list.append(merge_cells(sid_c, row_idx, 0, CS_COLS))
            requests_list.append(cell_fmt(sid_c, row_idx, row_idx + 1, 0, CS_COLS,
                                          bg="#FAFAFA", italic=True, wrap="WRAP"))
        elif rtype == "ticket":
            requests_list.append(cell_fmt(sid_c, row_idx, row_idx + 1, 3, 4, wrap="WRAP"))
            requests_list.append(cell_fmt(sid_c, row_idx, row_idx + 1, 0, CS_COLS,
                                          bg="#FFFFFF"))
    requests_list.append(freeze(sid_c, rows=2, cols=0))
    col_widths_c = [110, 280, 80, 360, 150]
    for i, w in enumerate(col_widths_c):
        requests_list.append(col_width(sid_c, i, w))

    # ── Tab 3: Technical Notes ───────────────────────────────────────────────
    requests_list.append(merge_cells(sid_t, 0, 0, 5))
    requests_list.append(cell_fmt(sid_t, 0, 1, 0, 5,
                                  bg=DARK_BLUE, bold=True, fg=WHITE, font_size=13))
    requests_list.append(cell_fmt(sid_t, 1, 2, 0, 5,
                                  bg=HEADER_GRAY, bold=True, fg=WHITE))
    requests_list.append(freeze(sid_t, rows=2))
    requests_list.append(cell_fmt(sid_t, 2, 2 + len(TECH_NOTES), 0, 5, wrap="WRAP"))
    col_widths_t = [270, 80, 120, 340, 300]
    for i, w in enumerate(col_widths_t):
        requests_list.append(col_width(sid_t, i, w))

    # ── Tab 4: Feature Primer ────────────────────────────────────────────────
    if primer_meta:
        for row_idx, rmeta in enumerate(primer_meta):
            rtype = rmeta["type"]
            if rtype == "title":
                requests_list.append(merge_cells(sid_p, row_idx, 0, 5))
                requests_list.append(cell_fmt(sid_p, row_idx, row_idx + 1, 0, 5,
                                              bg=DARK_BLUE, bold=True, fg=WHITE,
                                              font_size=13, valign="MIDDLE"))
            elif rtype == "subtitle":
                requests_list.append(merge_cells(sid_p, row_idx, 0, 5))
                requests_list.append(cell_fmt(sid_p, row_idx, row_idx + 1, 0, 5,
                                              bg="#EFF3FB", italic=True, wrap="WRAP"))
            elif rtype == "section_hdr":
                requests_list.append(merge_cells(sid_p, row_idx, 0, 5))
                requests_list.append(cell_fmt(sid_p, row_idx, row_idx + 1, 0, 5,
                                              bg="#1F3864", bold=True, fg=WHITE,
                                              font_size=11))
            elif rtype == "col_hdr":
                requests_list.append(cell_fmt(sid_p, row_idx, row_idx + 1, 0, 5,
                                              bg=HEADER_GRAY, bold=True, fg=WHITE))
            elif rtype == "subsection_hdr":
                requests_list.append(merge_cells(sid_p, row_idx, 0, 5))
                requests_list.append(cell_fmt(sid_p, row_idx, row_idx + 1, 0, 5,
                                              bg="#D9E1F2", bold=True))
            elif rtype == "addon_hdr":
                requests_list.append(merge_cells(sid_p, row_idx, 0, 5))
                requests_list.append(cell_fmt(sid_p, row_idx, row_idx + 1, 0, 5,
                                              bg="#FFF2CC", italic=True))
            elif rtype in ("feature", "prereq"):
                requests_list.append(cell_fmt(sid_p, row_idx, row_idx + 1, 0, 5,
                                              wrap="WRAP"))
        # Freeze title + subtitle only
        requests_list.append(freeze(sid_p, rows=2, cols=0))
        col_widths_p = [220, 300, 300, 140, 300]
        for i, w in enumerate(col_widths_p):
            requests_list.append(col_width(sid_p, i, w))

    sheets_svc.spreadsheets().batchUpdate(
        spreadsheetId=ss_id,
        body={"requests": requests_list},
    ).execute()


def build_feature_primer_values() -> tuple[list[list], list[dict]]:
    """Build the Feature Primer tab — 3 sections: Available Today / Still Needed / Migration."""
    BLANK5 = [""] * 5
    rows: list[list] = []
    meta: list[dict] = []

    def add(row: list, rtype: str) -> None:
        rows.append(row)
        meta.append({"type": rtype})

    # ── Header ────────────────────────────────────────────────────────────────
    add(["FEATURE PRIMER — Residency Scheduling in Amion Next"] + [""] * 4, "title")
    add(["A quick reference for CS and Sales: what's live today, what programs still need, "
         "and what must be in place before a program can migrate from Classic."] + [""] * 4,
        "subtitle")
    add(BLANK5, "blank")

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 1 — WHAT'S AVAILABLE IN AMION NEXT TODAY
    # ══════════════════════════════════════════════════════════════════════════
    add(["SECTION 1 — WHAT'S AVAILABLE IN AMION NEXT TODAY"] + [""] * 4, "section_hdr")
    add(["Feature", "What It Does in Next Today", "Who Can Use It",
         "Schedule Type", "Status / Notes"], "col_hdr")

    def avail(name: str, desc: str, who: str, sched: str, status: str = "") -> None:
        add([name, desc, who, sched, status], "feature")

    avail(
        "Block Schedule — Core Scheduling",
        "Create services, assign residents to blocks, set service colors, manage time-off "
        "(vacation, day-off, service requests). Split a block to assign a resident to two "
        "different services within one block period (e.g., 2 weeks Medicine + 2 weeks Surgery).",
        "Managers", "Block",
        "Live; Splits In Dev (Mar 2026)",
    )
    avail(
        "Preserve Block Services on Block Count Change",
        "Changing the total number of blocks no longer erases existing service assignments. "
        "Coordinators can adjust block count at any time without rebuilding from scratch.",
        "Managers", "Block",
        "Shipped ✓",
    )
    avail(
        "Call & Shift — Core Scheduling",
        "Assign residents to call nights and shifts. Configure day-after Off rules to enforce "
        "rest requirements automatically. Basic auto-assignment available.",
        "Managers", "Call / Shift",
        "Live",
    )
    avail(
        "Clinic — Basic Assignment & Templates",
        "Assign residents to clinic sessions and set up continuity clinic templates using "
        "1-week rules. Clinic staffing report available in the resident viewer.",
        "Managers & Residents", "Clinic",
        "Live (viewer on legacy stack)",
    )
    avail(
        "Resident Viewer — Who's On & Monthly Schedule",
        "Residents see who's on call, shift, or clinic today; view their own monthly schedule; "
        "and check upcoming assignments across all schedule types.",
        "Residents", "All schedules",
        "Live (Vue)",
    )
    avail(
        "Enforce Resident Graduation",
        "Residents automatically drop off the schedule when their final training year ends. "
        "No manual cleanup needed when each academic year starts.",
        "Managers", "Academic Year",
        "Shipped ✓",
    )
    avail(
        "Academic Year Visibility — Block, Call, Shift, Clinic",
        "Only residents training in the selected academic year appear in the schedule view, "
        "with correct PGY labels. Eliminates ghost names from prior or future years cluttering "
        "the schedule.",
        "Managers", "Academic Year",
        "In QA — Mar 2026",
    )
    avail(
        "Default Service Colors on Migration",
        "Day-off services migrate red; rotation services migrate black — matching Classic "
        "conventions. Migrated schedules look familiar without any color reconfiguration.",
        "Managers", "Migration",
        "Shipped ✓",
    )
    add(BLANK5, "blank")

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 2 — WHAT RESIDENCY PROGRAMS STILL NEED
    # ══════════════════════════════════════════════════════════════════════════
    add(["SECTION 2 — WHAT RESIDENCY PROGRAMS STILL NEED"] + [""] * 4, "section_hdr")
    add(["Feature", "The Gap Today", "What Amion Next Needs to Support",
         "Who Needs It", "Comments"], "col_hdr")

    def feat(name: str, gap: str, enables: str, who: str, comment: str = "") -> None:
        add([name, gap, enables, who, comment], "feature")

    def section(title: str) -> None:
        add([title] + [""] * 4, "subsection_hdr")

    def addon_hdr(label: str = "Aline's add-ons:") -> None:
        add([label] + [""] * 4, "addon_hdr")

    # ── BLOCK SCHEDULE ────────────────────────────────────────────────────────
    section("BLOCK SCHEDULE — How rotations are assigned across the academic year")
    feat("Block Tally",
         "Block schedules do provide tallies visually on the block, but not as a tally report. "
         "Also, limited to tallying for only one academic year at a time. Coordinators collect "
         "each resident's completed rotations for their entire program in a spreadsheet to verify "
         "ACGME compliance before the schedule is approved/finalized.",
         "A per-resident rotation count table updates live in the schedule, turning red when a "
         "resident is short and yellow when over target. One view replaces hours of manual verification.",
         "Every program")
    feat("Block Service Staffing Requirements (Min / Max Targets)",
         "Coordinators track whether each service has enough residents by manually counting rows "
         "in the schedule — catching under-staffing only after the fact.",
         "Each block service has a minimum, target, and maximum staff count. The schedule highlights "
         "violations in color as they happen, giving coordinators a compliance dashboard without "
         "running a separate report.",
         "Every program")
    feat("Pool Staff With",
         "Groups multiple services together so their resident counts add up in tally reports. "
         "Service directors with parallel ward teams rely on this.\nExample: Wards Team A + "
         "Wards Team B pooled so you see total Wards coverage per block, not per-team counts",
         "A block service needs to store a 'pool' relationship — a list of other services whose "
         "residents count together. In Classic this is a per-service setting ('Pool staff with…') "
         "stored on the service itself. Next needs a data model that says: Service A + Service B = "
         "Pool, and that pool is the unit of counting for tally purposes.",
         "Few residency programs")
    feat("Multiple Splits with Unique Dates",
         "When a resident needs to cover two services within one block period (e.g., 2 weeks on "
         "Medicine, 2 weeks on Surgery), the split dates are rigidly tied to time-off entries, "
         "creating conflicts.",
         "Splits within a block are fully independent of time-off. Each split gets its own date "
         "range, and schedulers can set them without worrying about collisions.",
         "Most residency programs")
    feat("Block Online Requests — Enrollment Window",
         "Residents email vacation preferences and rotation requests to the coordinator before the "
         "schedule is built. The coordinator tracks these in a spreadsheet, manually "
         "cross-referencing before entering anything into Amion.",
         "A scheduler-defined enrollment window opens for residents to submit preferences directly "
         "in Amion. Approved requests import onto the schedule in one step.",
         "Most residency programs")
    feat("Block Template Autofill (4+1 Pattern)",
         "Building a full-year block schedule using the 4-week inpatient + 1-week outpatient "
         "pattern requires entering dozens of repetitive assignment pairs by hand.",
         "Enter the first two weeks and Amion applies the repeating 4+1 pattern across the full "
         "year automatically.",
         "Most residency programs",
         "Aline: I can see this being a block repeating assignment with options of how often it "
         "repeats (every block, every other block, every 3rd block, every 4th block, etc). Also, "
         "I think we can do templates differently than OnCall. Something that offers more options "
         "and can be later used for block automation. Instead of a 4+1 pattern, a pattern template, "
         "much like how one is used for daily call, shift, and clinic. Maybe one template tool that "
         "can be used for all pages.")
    feat("CSV Import of Block Schedules",
         "Coordinators upload a CSV of block assignments and Amion maps them onto the schedule. "
         "Cuts hours of manual work.",
         "",
         "Few residency programs",
         "Aline: If we can offer more scheduling options for blocks, it won't be necessary for "
         "programs to build in Excel first.")
    addon_hdr("Aline's add-ons:")
    feat("Cross-Cover Markers",
         "Cross-coverage is only one instead of having multiple, and no cross-coverage schedule "
         "offered. Need to have a cross-coverage schedule of who is covering and when, and are they "
         "1st, 2nd, or for one service vs another.",
         "Need to have more than one cross-coverage setup for same service (i.e. 1st pull, 2nd "
         "pull). Also, need markers on the block schedule. On call/shift schedules, autoscheduler "
         "should never pull CC staff. Offer to assign residents for specific CC by date.",
         "Most residency programs")
    feat("Service View",
         "Can only build block schedules by staff. Need to view and build by service.",
         "Provide a way to transpose the block schedule by service. If service has a staff "
         "requirement for 3, only 3 lines appear for the service to be filled.",
         "Few residency programs")
    feat("Block Types, Rules & Autoscheduler",
         "Block scheduling is very manual in Amion. If rules and requirements could be set per "
         "service per staff type, it'll help make building easier, faster, and more equitable.",
         "Along with block and staff requirements, be able to define block types such as inpatient, "
         "elective, time-off. Then set block rules such as: can have 2 consecutive inpatient blocks "
         "but not 3; must have an elective rotation when coming off a specific service; no XX "
         "rotation for PGY1s the first 6 blocks. Being able to autoschedule the block will save a "
         "chief 2 months of their time.",
         "Every program")
    add(BLANK5, "blank")

    # ── CALL/SHIFT SCHEDULE ───────────────────────────────────────────────────
    section("CALL/SHIFT SCHEDULE — How overnight and weekend call assignments are managed")
    feat("Call & Shift Patterns",
         "Coordinators maintain call rotation patterns (Q4 call, alternate weekends, night float "
         "rotations) in separate spreadsheets, then manually enter each assignment into Amion.",
         "Named patterns fill in automatically across the full schedule period. Repeating "
         "structures like Q4 overnight call or alternate weekend shifts require setup once, not "
         "weekly re-entry.",
         "Every program with call schedules",
         "Aline: Patterns need to replace OnCall's pattern tool, pattern links, and template "
         "pattern tool. I have ideas on what it needs and maybe how to do it.")
    feat("Call / Shift Tallies (Duty Hour-Aware)",
         "For programs that don't have built-in patterns and templates to ensure they meet "
         "duty-hour requirements, chiefs track each resident's call count in a separate spreadsheet "
         "or in their heads, checking ACGME limits manually at the end of each period.",
         "A per-resident call count updates automatically, with flags when anyone approaches the "
         "duty hour limit — giving the chief an always-current compliance view.",
         "Every program with call schedules",
         "Aline: We need a duty hour report AND flags on the schedule when in violation. Also, "
         "the autoscheduler should follow duty hour requirements.")
    feat("Subsets — Named Filtered Views",
         "Programs with 20+ call services expose the full call list to everyone — nursing staff, "
         "attendings, and residents all scroll through irrelevant services to find what they need.",
         "Admins create named views (e.g., 'ICU Services,' 'Night Team,' 'Senior Call') that each "
         "viewer group can switch to, showing only the services relevant to them.",
         "Large enterprise and academic programs",
         "Aline: Issue with current setup is if new rows or services are added, the filter views "
         "now need to be edited, which most do not think to do — and then they get messed up. Need "
         "Group services that color both on the Who's On and monthly schedule pages. If grouped, "
         "have a filter automatically created.")
    addon_hdr("Aline's Add-on:")
    feat("Basic Rules (Day-After On/Off)",
         "We offer day-after Off rules for services but not On rules. It is easier to use this "
         "tool for basic rules than building an auto-assignment rule.",
         "Expand the use of Off and On day-after rules to be conditional such as by staff, staff "
         "type, day-of-week, time-off the next day, etc. (i.e. must be off the next day IF a "
         "Sunday. Or, PGY2s must be scheduled on backup call the next day but not PGY1s.)",
         "Every program with call schedules")
    feat("Advanced Rules (Rule Writer)",
         "Need to offer custom rules in what Rule Writer offered such as Staff-by rule, Coverage "
         "rule, and daily staffing level rules.",
         "",
         "Most programs")
    add(BLANK5, "blank")

    # ── CLINIC SCHEDULE ───────────────────────────────────────────────────────
    section("CLINIC SCHEDULE — How continuity and outpatient clinic sessions are managed")
    feat("Continuity Clinic Builder View",
         "Coordinators manage clinic assignments through the same interface as block and call — "
         "there is no dedicated view for the recurring resident-clinic relationship that defines "
         "continuity.",
         "A dedicated clinic builder manages the ongoing assignment between a resident and their "
         "continuity clinic separately from other schedule types, with its own rules and templates.",
         "Every program with clinic schedules",
         "Aline: Need to expand the current cont clinic template to allow different cont clinics "
         "per week during a block. Also, need to see the block, call and shift assignments on the "
         "clinic page, just as call and shift needs to see clinic assignments.")
    feat("Clinic Auto-Assign by Block Service",
         "Coordinators maintain two parallel schedules: the block schedule and the clinic schedule. "
         "When a resident's rotation changes, the clinic schedule must be updated separately to match.",
         "A rule links clinic assignments to block services: 'If on Rheumatology block, assign "
         "Rheum Clinic every Thursday morning.' The clinic schedule populates from the block "
         "schedule automatically.",
         "Every program with clinic schedules")
    addon_hdr("Aline's add-on:")
    feat("Clinic Service View and Order",
         "Programs will need to be able to schedule clinics by clinic, not by staff, to arrange "
         "the clinics to appear in a certain order, and designate the order staff types appear for "
         "the same clinic. (i.e. Clinic A, show Preceptor at top, then PGY3, then PGY2, and PGY1 "
         "last). Also, they need an easy way to pair a preceptor to a resident's clinic.",
         "",
         "Most programs with clinic schedules")
    feat("Cancel Clinic Rules",
         "No way to say when a clinic should be canceled in Next. Cancelling clinics should be "
         "mostly automated.",
         "Allow clinics to cancel based on block, call and shift schedules. Offer basic rules as "
         "well as advanced rules. Define when a clinic is canceled manually vs by rule. Cancelling "
         "of clinics should be what OnCall offered as it is widely used and easy to setup.",
         "All programs using clinics")
    add(BLANK5, "blank")

    # ── ACADEMIC YEAR ─────────────────────────────────────────────────────────
    section("ACADEMIC YEAR — How programs manage the annual resident class transition")
    feat("Academic Year Rollover (Bulk Archive / Unarchive)",
         "At the end of each academic year, coordinators manually archive each graduating resident "
         "and manually add each incoming resident — a process that takes 2–4 hours per program.",
         "A single action archives the graduating class and activates the incoming class for the "
         "new year.",
         "Every program",
         "Lee: I imagined this going away...and groups being able to roll ahead as in the "
         "attending world.")
    feat("Academic Year Lock",
         "Program directors cannot finalize next year's schedule without it being visible to "
         "residents, making it impossible to review and correct before releasing to the team.",
         "A scheduler controls when the upcoming year's schedule becomes visible to residents. "
         "Build and review in private; unlock when ready.",
         "Every program")
    feat("Bulk Staff Addition to Schedule",
         "Adding an incoming PGY-1 class of 10–30 new residents requires adding each person "
         "individually — a repetitive manual process at the busiest time of the academic year.",
         "Add the entire incoming class to the schedule in one action at the start of the "
         "academic year.",
         "Every program")
    feat("Off-Cycle Resident Handling",
         "Programs where interns begin June 24 for orientation — while PGY-2s and above start "
         "July 1 — cannot correctly model the boundary. Amion requires all staff types in a year "
         "to share the same start date, creating a 7-day gap or overlap where both groups are "
         "technically active at once.",
         "Staff-type-level year boundary settings let programs specify that PGY-1s start June 24 "
         "while upper levels start July 1. The overlap week is handled automatically, with both "
         "cohorts appearing as active for their respective dates.",
         "Programs with early-start interns (common in medicine and surgery)")
    feat("Cohort / Team Groupings (A/B/C Teams)",
         "Medicine programs on four-plus-one schedules divide residents into cohorts so Team A is "
         "on outpatient week while Teams B and C are on inpatient. Today programs add letters in "
         "parentheses to resident names (e.g., 'Smith, J. (A)') as a workaround — this breaks "
         "every tally, report, and filter that relies on names.",
         "Named cohorts group residents for staggered scheduling. Teams can be assigned to "
         "outpatient blocks on different weeks, tallied separately, and displayed as a unit — "
         "without embedding the label in the name field.",
         "Medicine programs; any program using four-plus-one or parallel team schedules",
         "Aline: Need to set tracks/labels and well as have call-coverage team staff (i.e. ICU A, "
         "ICU B, ICU C team names to determine which team is on-call for ICU. If ICU-A is on-call, "
         "then show all ICUA staff). Also need placeholder names.")
    feat("External Rotator / Guest Staff Addition",
         "When a visiting resident or sub-intern rotates through a program, there is no way to add "
         "them to the Amion schedule without IT adding them to the full org directory. Programs "
         "currently either skip scheduling them or create fake accounts.",
         "A scheduler can create a temporary guest staff record for a visiting rotator. The person "
         "appears on the schedule for their rotation period and is archived when they leave — "
         "without requiring full org onboarding.",
         "All programs hosting sub-interns, away rotators, or visiting residents")
    add(BLANK5, "blank")

    # ── INTEGRATIONS ─────────────────────────────────────────────────────────
    section("INTEGRATIONS — How Amion connects to external systems")
    feat("Calendar Subscriptions (iCal / Google / Outlook)",
         "Residents view their Amion assignments in one place and their personal calendar in "
         "another — there is no link between them. Residents manually re-enter call nights and "
         "block assignments into their personal calendars.",
         "Residents subscribe to their Amion schedule with a one-time link. Block, call, clinic, "
         "and shift assignments automatically appear in Google Calendar, Apple Calendar, or Outlook "
         "alongside personal events.",
         "Residents — cited as top Amion feature request")
    feat("MedHub Integration",
         "The Amion-to-MedHub connection is a flat CSV export that breaks silently. Programs only "
         "discover the break when MedHub contacts them — sometimes weeks after the last successful "
         "sync.",
         "A monitored API-based connection replaces the file export. Admins are notified when sync "
         "fails, and the connection is bidirectional.",
         "117 MedHub-connected programs (source)")
    feat("New Innovations Integration",
         "New Innovations pulls Amion rotation and assignment data via API to drive evaluations, "
         "duty hour tracking, and clinical hours reporting. Rotation and shift names must match "
         "exactly between Amion and NI or the sync fails without any error message; mismatches "
         "are only caught during manual reconciliation. Time-off data never flows to NI, so "
         "programs manually enter leave in both systems to keep clinical hours reporting accurate. "
         "Setup is done entirely between the scheduler and an NI representative with no Amion "
         "involvement — leaving no visibility into whether the integration is functioning.",
         "???? - Needs product discovery",
         "All NI-connected programs (standard residency integration offering)")
    add(BLANK5, "blank")

    # ── MISC ──────────────────────────────────────────────────────────────────
    section("MISC")
    feat("Track Changes",
         "Month-by-month audit trail on Call, Shift, or Clinic schedules. Important for programs "
         "with multiple schedulers — who changed what?",
         "",
         "Few residency programs",
         "Aline: Need track change markers as well as when changes occur from a template. Need to "
         "know who made the change and when and offer an option to make a private note as to why. "
         "A track change report would also be nice.")
    feat("Group Paging",
         "Page everyone on a specific service or staff type at once; custom groups built via Rule "
         "Writer (e.g., 'everyone on call today').",
         "",
         "Few residency programs",
         "Aline: Need the same feature to make custom paging/messaging groups, but still offer the "
         "default groups by staff types and by service.")
    addon_hdr("Aline's add-ons:")
    feat("Staffing Links",
         "Links in call/shift is a small gray icon easily overlooked. No way for programs to know "
         "if their data is linked into another program. Links are easily broken if the service "
         "expands, reduces, or changes the name.",
         "Services that are linked schedules appear in color indicating 'To'. Services that feed "
         "another schedule appear in gray indicating 'From.' If a service expands or reduces, "
         "notification goes to admin to let them know.",
         "All programs using links")
    feat("Setting Menu Order",
         "The order of menu items is out of line from how someone would setup a new schedule. The "
         "menu should be intuitive on what to set up first and so on. The less admins need to "
         "watch tutorials the better.",
         "I have an idea of the order it should be, which should also change in the provider "
         "platform. For instance, you cannot set up block services without defining your staff "
         "types and staff first. You cannot set up rules until you have set up your call services.",
         "All programs")
    feat("More Who's On Views",
         "No all-services view that PDs need to see where everyone is at for the day across all "
         "schedules. Need to be able to build custom Who's On views for programs based on their "
         "needs.",
         "",
         "All programs")
    feat("Meeting / Conference Schedule",
         "OnCall offers a meeting/conference note which creates a schedule on the published side. "
         "It does not allow the admin to see it in OnCall, nor can it be tallied. It is also "
         "limited on assigning presenters.",
         "Programs all have meetings/conference schedules, especially what is being presented, who "
         "is presenting and who should attend. These conferences are based on block, call, shift, "
         "or clinic schedules. We really need a Meeting/Conference schedule page that is not the "
         "meeting note.",
         "All programs have meetings/conferences")
    add(BLANK5, "blank")

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 3 — WHAT'S REQUIRED FOR MIGRATION
    # ══════════════════════════════════════════════════════════════════════════
    add(["SECTION 3 — WHAT'S REQUIRED FOR MIGRATION"] + [""] * 4, "section_hdr")
    add(["Migration Prerequisite", "Why It's Needed", "Current Status",
         "Target Date", "Notes / Dependency"], "col_hdr")

    def prereq(name: str, why: str, status: str, target: str, notes: str = "") -> None:
        add([name, why, status, target, notes], "prereq")

    prereq(
        "Remove Duplicate Year-Specific Staff Types",
        "Classic creates 'PGY-1 2023,' 'PGY-1 2024' as separate staff types. These must be "
        "consolidated before Next can correctly identify which residents belong to which "
        "academic year.",
        "In Dev", "Mar 2026",
        "Prerequisite for AY visibility",
    )
    prereq(
        "Academic Year Visibility — All Schedule Types",
        "Residents must appear correctly per academic year before a program can validate their "
        "migrated schedule. Foundational for every residency customer.",
        "In QA", "Mar 2026",
        "Required for first migration",
    )
    prereq(
        "Map Classic Staff Types → Next Training Levels",
        "Migration staging step: coordinators review how each Classic staff type maps to a PGY "
        "training level. Prelim, research year, and categorical types often need manual "
        "correction before mapping.",
        "Not Started", "May 2026",
        "Product Proposal available",
    )
    prereq(
        "Academic Year Lock",
        "Program directors need to build and review next year's schedule privately before "
        "releasing to residents. Without lock, there is no safe review period before the "
        "schedule goes live.",
        "Not Started", "Apr 2026",
        "All programs",
    )
    prereq(
        "Bulk Staff Addition to Schedule",
        "Adding 10–30 incoming PGY-1s one by one is not a viable migration experience. "
        "Programs need to batch-add the full incoming class in one action at the start of "
        "each academic year.",
        "Not Started", "Apr 2026",
        "All programs",
    )
    prereq(
        "Call & Shift Patterns",
        "Programs using repeating call structures (Q4 overnight, alternate weekends, night "
        "float) cannot build a complete call schedule without patterns. Migration without "
        "patterns means manual entry of every assignment.",
        "Not Started", "Jun 2026",
        "Most residency programs",
    )
    prereq(
        "Academic Year Rollover",
        "Programs bulk-archive graduating residents and activate the returning class for the "
        "new year in one action. Required for programs to self-serve year transitions without "
        "CS assistance.",
        "Not Started", "Jun 2026",
        "All programs",
    )
    prereq(
        "CSV Import of Block Schedules",
        "The primary migration path for programs coming from MedHub or New Innovations. "
        "Eliminates manual re-entry of the full year's block assignments — a multi-day task "
        "for large programs.",
        "Not Started", "Jul 2026",
        "Programs migrating from MedHub / NI",
    )
    prereq(
        "Continuity Clinic Builder View",
        "Programs with formal ACGME continuity clinic requirements cannot fully migrate until "
        "clinic assignments are managed separately from block and call. Without this, clinic "
        "scheduling in Next is a workaround.",
        "Not Started", "Jul 2026",
        "Programs with continuity clinics",
    )
    prereq(
        "Clinic Viewer — Frontend Architecture Alignment",
        "Viewer-side clinic features (tallies, continuity builder, staffing report, cancel "
        "rules) cannot be built to the same standard as other viewer pages until the frontend "
        "stack is aligned. Blocks all viewer-side clinic work.",
        "Not Started", "Jun 2026",
        "Blocks all viewer-side clinic features",
    )
    prereq(
        "MedHub / New Innovations Integration Reliability",
        "Programs integrated with MedHub or NI need a reliable, monitored API connection "
        "before they can fully cut over from Classic. The current connection fails silently; "
        "programs only discover the break when the vendor contacts them.",
        "Not Started", "Aug 2026",
        "117 MedHub programs + all NI programs",
    )
    add(BLANK5, "blank")

    return rows, meta


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 60)
    print("Residency Roadmap — Amion Next")
    print("=" * 60)

    # 1. Fetch live data
    canny_posts = fetch_canny_residency_posts()
    zd_tickets  = fetch_zendesk_residency_tickets()

    canny_signal_map = build_canny_signal_map(canny_posts)
    zd_signal_map    = build_zendesk_signal_map(zd_tickets)
    gmail_emails     = fetch_gmail_residency_emails()

    # 2. Fetch live Jira statuses for in-flight tickets
    print("\nFetching live Jira statuses...")
    all_jira_keys = [
        feat[3]  # jira field
        for feats in FEATURES.values()
        for feat in feats
        if feat[1] != "Shipped"  # skip already-shipped features
    ]
    jira_statuses = fetch_jira_statuses(all_jira_keys)

    # 3. Create spreadsheet
    print("\nCreating Google Spreadsheet...")
    sheets_svc = get_sheets_service()
    ss_id, sheet_id_map = create_spreadsheet(sheets_svc)
    ss_url = f"https://docs.google.com/spreadsheets/d/{ss_id}"
    print(f"  Created: {ss_url}")

    # 4. Build Tab 1 values + row metadata
    print("\nWriting Tab 1: Residency Roadmap...")
    today_str = datetime.now().strftime("%Y-%m-%d")
    tab1_values = [
        [f"RESIDENCY ROADMAP — AMION NEXT (Last updated: {today_str})"]
        + [""] * (len(TAB1_HEADERS) - 1),
        TAB1_HEADERS,
    ]
    tab1_row_meta: list[dict] = []

    # Flatten all features across sections; sort globally by delivery date
    all_features = [
        (section_name, feat)
        for section_name, feats in FEATURES.items()
        for feat in feats
    ]
    sorted_features = sorted(all_features,
                             key=lambda x: DELIVERY_SORT.get(x[1][4], 50))

    for i, (section_name, feat) in enumerate(sorted_features):
        (name, status, effort, jira, delivery, priority, notes) = feat

        # Override status with live Jira data if available
        if jira != "TBD" and status != "Shipped" and jira in jira_statuses:
            status = jira_statuses[jira]

        # Build Jira cell - hyperlink for known tickets
        if jira and jira != "TBD":
            jira_cell = f'=HYPERLINK("https://doximity.atlassian.net/browse/{jira}","{jira}")'
        else:
            jira_cell = "TBD"

        row = [
            name,
            section_name.title(),
            status,
            effort,
            jira_cell,
            delivery,
            notes,
        ]
        tab1_values.append(row)
        tab1_row_meta.append({
            "type":     "feature",
            "status":   status,
            "priority": priority,
            "delivery": delivery,
        })

        # After the last feature for this delivery date, insert a milestone row if one exists
        next_delivery = sorted_features[i + 1][1][4] if i + 1 < len(sorted_features) else None
        if delivery != next_delivery and delivery in MILESTONES:
            tab1_values.append([MILESTONES[delivery]] + [""] * (len(TAB1_HEADERS) - 1))
            tab1_row_meta.append({"type": "milestone", "delivery": delivery})

    write_values(sheets_svc, ss_id, "Residency Roadmap", tab1_values, "USER_ENTERED")

    # 5. Build Tab 2: Customer Signals (filtered + combined analysis)
    print("Writing Tab 2: Customer Signals...")

    # Filter Zendesk to feature signals only; keep all Canny posts
    feature_zd: list[dict] = []
    for t in zd_tickets:
        is_feat, sub_theme = is_feature_signal(t["title"], t["notes"])
        if is_feat:
            feature_zd.append({
                **t,
                "sub_theme": sub_theme,
                "summary": ticket_summary(t["title"], t["notes"], sub_theme),
            })
    for p in canny_posts:
        _, sub_theme = is_feature_signal(p["title"], p["notes"])
        p["sub_theme"] = sub_theme or "Feature request (unclassified)"
        p["summary"] = ticket_summary(p["title"], p["notes"], p["sub_theme"])

    theme_groups: dict[str, list] = defaultdict(list)
    for t in feature_zd:
        theme_groups[t["sub_theme"]].append(t)
    for p in canny_posts:
        theme_groups[p["sub_theme"]].append(p)

    total_relevant = len(feature_zd) + len(canny_posts)
    BLANK5 = [""] * 5

    tab2_values: list[list] = []
    tab2_row_meta: list[dict] = []

    def t2(row, rtype, **kw):
        tab2_values.append(row)
        tab2_row_meta.append({"type": rtype, **kw})

    # Title + subtitle
    t2(["CUSTOMER SIGNALS — Residency (Amion Brand, Filtered, Last 12 Mo)"] + [""] * 4, "title")
    t2([f"{len(feature_zd)} Zendesk signals + {len(canny_posts)} Canny posts + "
        f"{len(REDDIT_POSTS)} Reddit posts + {len(gmail_emails)} Gmail threads "
        f"(phone logs, pricing, account mgmt, and training questions excluded). "
        f"Percentages reflect Zendesk share only."] + [""] * 4,
       "subtitle")
    t2(BLANK5, "blank")

    # ── SECTION 1: Theme Summary ─────────────────────────────────────────────
    t2(["WHAT CUSTOMERS ARE REQUESTING — Theme Summary"] + [""] * 4,
       "section_hdr", bg="#F4CCCC")
    t2(["Theme", "% of Signals", "Severity", "What programs are requesting", ""], "col_hdr")

    for sub_theme in THEME_ORDER:
        tickets = theme_groups.get(sub_theme, [])
        if not tickets:
            continue
        zd_count = sum(1 for t in tickets if t.get("source") == "Zendesk")
        pct = f"{round(zd_count / len(feature_zd) * 100)}%" if feature_zd else "—"
        t2([sub_theme, pct, SIGNAL_SEVERITY.get(sub_theme, "L"),
            THEME_SUMMARIES.get(sub_theme, ""), ""],
           "theme_summary", sev=SIGNAL_SEVERITY.get(sub_theme, "L"))

    t2(BLANK5, "blank")

    # ── SECTION 2: Ticket Breakdown ──────────────────────────────────────────
    t2([f"TICKET BREAKDOWN — {total_relevant} signals ({len(feature_zd)} Zendesk + "
        f"{len(canny_posts)} Canny) sorted by theme then recency"] + [""] * 4,
       "section_hdr", bg="#C9DAF8")
    t2(["Source", "Title", "Date", "What they're requesting", "Theme"], "col_hdr")

    for sub_theme in THEME_ORDER:
        tickets = theme_groups.get(sub_theme, [])
        if not tickets:
            continue
        t2([f"  {sub_theme}  ({len(tickets)} signals)"] + [""] * 4, "theme_hdr")
        t2([THEME_SUMMARIES.get(sub_theme, "")] + [""] * 4, "theme_note")
        for tkt in sorted(tickets, key=lambda x: x.get("date", ""), reverse=True):
            url = tkt.get("url", "")
            raw_title = tkt["title"][:80].replace('"', "'")
            title_cell = (f'=HYPERLINK("{url}","{raw_title}")'
                          if url else raw_title)
            t2([tkt["source"], title_cell, tkt["date"],
                tkt.get("summary", ""), sub_theme], "ticket")
        t2(BLANK5, "blank")

    # ── SECTION 3: Reddit Signals ─────────────────────────────────────────────
    t2(["REDDIT SIGNALS — r/Residency + Related Communities "
        f"({len(REDDIT_POSTS)} posts, 2020–2025)"] + [""] * 4,
       "section_hdr", bg="#D9EAD3")
    t2(["Source", "Post Title", "Date", "Key Signal", "Theme"], "col_hdr")
    for subreddit, title, date, score, url, key_signal, theme in REDDIT_POSTS:
        safe_title = title[:80].replace('"', "'")
        title_cell = f'=HYPERLINK("{url}","{safe_title}")'
        t2([f"{subreddit}  ↑{score}", title_cell, date, key_signal, theme], "ticket")
    t2(BLANK5, "blank")

    # ── SECTION 4: Gmail Signals ──────────────────────────────────────────────
    t2([f"GMAIL SIGNALS — Residency-Related Emails ({len(gmail_emails)} threads)"]
       + [""] * 4,
       "section_hdr", bg="#FFF2CC")
    t2(["From", "Subject", "Date", "Snippet", ""], "col_hdr")
    for em in gmail_emails:
        safe_subj = em["subject"][:80].replace('"', "'")
        subj_cell = f'=HYPERLINK("{em["url"]}","{safe_subj}")'
        t2([em["from"][:40], subj_cell, em["date"], em["snippet"][:200], ""], "ticket")
    t2(BLANK5, "blank")

    write_values(sheets_svc, ss_id, "Customer Signals", tab2_values,
                 "USER_ENTERED")

    # 6. Build Tab 3 values (Technical Notes)
    print("Writing Tab 3: Technical Notes...")
    tab3_values = [
        ["TECHNICAL NOTES"] + [""] * 4,
        ["Area / Open Question", "Status", "Reference",
         "What needs to be resolved", "Why This Affects the Roadmap"],
    ]
    for note in TECH_NOTES:
        tab3_values.append(list(note))

    write_values(sheets_svc, ss_id, "Technical Notes", tab3_values)

    # 7. Build Tab 4: Feature Primer
    print("Writing Tab 4: Feature Primer...")
    primer_values, primer_meta = build_feature_primer_values()
    write_values(sheets_svc, ss_id, "Feature Primer", primer_values, "RAW")

    # 8. Apply formatting
    print("Applying formatting...")
    apply_formatting(sheets_svc, ss_id, sheet_id_map, tab1_row_meta, tab2_row_meta,
                     primer_meta=primer_meta)

    # 9. Done
    print("\n" + "=" * 60)
    print("✓ Spreadsheet created successfully!")
    print(f"  URL: {ss_url}")
    print("=" * 60)


if __name__ == "__main__":
    main()
