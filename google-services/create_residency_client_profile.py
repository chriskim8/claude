"""
Amion Next — Residency Client Profile
Two tabs:
  1. Tier Guide  — persona columns × feature rows (SaaS-style checkbox matrix)
  2. Client Profile — condensed grouped columns, ready for Airtable import
"""
import sys
sys.path.insert(0, '/Users/chriskim/google-services')
from google_client import get_sheets_service

TITLE = "Amion Next — Residency Client Profile"
EXISTING_SHEET_ID = "1oSFvhIWlP9xBfaMIG9WKxUPyU-xpUTVZ8aovETRcIVQ"

# ── Availability markers ───────────────────────────────────────────────────────
# Used in the "Status in Next" column only — not in persona checkmarks
LIVE  = "✓  Live"
SOON  = "→  Coming soon"
ROAD  = "◌  On roadmap"

CHECK = "✓"
EMPTY = ""

# ── Colors ─────────────────────────────────────────────────────────────────────
DARK      = "1C2833"
WHITE     = "FFFFFF"
SECTION   = "2E4053"   # dark blue-grey — section header rows

# Persona header colors (simple → most advanced)
P_COLORS = ["1565C0", "2E7D32", "6A1B9A", "BF360C", "37474F"]
P_LIGHT  = ["E3F2FD", "E8F5E9", "F3E5F5", "FBE9E7", "ECEFF1"]

# Check cell styles by availability
CHK_LIVE = ("E8F5E9", "1B5E20")   # green
CHK_SOON = ("FFF9C4", "E65100")   # amber
CHK_ROAD = ("FCE4EC", "880E4F")   # pink — needed but not in Next yet
EMPTY_BG = ("FAFAFA", "BDBDBD")

# ── 5 Personas ─────────────────────────────────────────────────────────────────
PERSONAS = [
    {
        "name":    "The Community\nProgram",
        "label":   "Simple",
        "desc":    "Manually assigns block rotations, clinic sessions, and basic call or shift. "
                   "No patterns, no rules, no integrations.",
        "example": "Small IM, FM, or EM program. Single schedule. Standard July AY.",
        "gate":    "Apr–May 2026",
    },
    {
        "name":    "The Structured\nRotation Program",
        "label":   "Intermediate",
        "desc":    "Relies on repeating call/shift patterns and cross-coverage rules. "
                   "Uses cancel clinic rules to manage clinic load automatically.",
        "example": "Mid-size Peds or Surgery program with Q4 overnight call, alternating weekend patterns.",
        "gate":    "Jun–Jul 2026",
    },
    {
        "name":    "The Rules\nArchitect",
        "label":   "Intermediate–Advanced",
        "desc":    "Builds eligibility and staffing rules into the schedule. "
                   "Uses anonymous templates and needs iCal sync for resident visibility.",
        "example": "IM or Surgery program with ICU coverage rules (PGY-2+ only), 4+1 block templates.",
        "gate":    "Aug 2026+",
    },
    {
        "name":    "The Integrated\nAutomator",
        "label":   "Advanced",
        "desc":    "Depends on external system integrations (MedHub, NI) and uses "
                   "the autoscheduler with work preferences and duty hours compliance.",
        "example": "Large academic Surgery or IM program syncing to MedHub, tracking ACGME duty hours.",
        "gate":    "Sep 2026+",
    },
    {
        "name":    "The Academic\nMedical Center",
        "label":   "Most Advanced",
        "desc":    "Multi-program organization with linked schedules, all integrations, "
                   "full automation, and ACGME historical compliance data needs.",
        "example": "University health system with 5+ residency programs, VA-linked schedules, NI + MedHub.",
        "gate":    "TBD",
    },
]

# ── Feature matrix ─────────────────────────────────────────────────────────────
# (feature_label, is_section, [p1,p2,p3,p4,p5], status_in_next)
# Persona checks: True = needed, False = not needed
# status_in_next: LIVE / SOON / ROAD

FEATURES = [
    # ── Schedule Setup ────────────────────────────────────────────────────────
    ("SCHEDULE SETUP", True,  [0,0,0,0,0], ""),
    ("Block Schedule",                False, [1,1,1,1,1], LIVE),
    ("Clinic Schedule",               False, [1,1,1,1,1], LIVE),
    ("Call Schedule",                 False, [1,1,1,1,1], LIVE),
    ("Shift Schedule  (EM programs)", False, [1,1,1,1,1], LIVE),

    # ── Block ─────────────────────────────────────────────────────────────────
    ("BLOCK MANAGEMENT", True, [0,0,0,0,0], ""),
    ("Block Tally & Lock Services",       False, [1,1,1,1,1], LIVE),
    ("Cross-Coverage (X-Cover)",          False, [0,1,1,1,1], LIVE),
    ("Multiple Splits / Custom Dates",    False, [0,1,1,1,1], SOON),
    ("Block Staffing Rules (Min / Max)",  False, [0,0,1,1,1], SOON),
    ("Block Template Autofill (X+Y)",     False, [0,0,1,1,1], ROAD),
    ("CSV Import of Block Schedules",     False, [0,0,0,1,1], ROAD),

    # ── Call & Shift ──────────────────────────────────────────────────────────
    ("CALL & SHIFT", True, [0,0,0,0,0], ""),
    ("Basic Manual Assignment",           False, [1,1,1,1,1], LIVE),
    ("Repeating Patterns (Q4, alt. wknd)",False, [0,1,1,1,1], SOON),
    ("Call / Shift Tallies",              False, [0,1,1,1,1], SOON),
    ("Duty Hours Tracking & Flags",       False, [0,0,0,1,1], ROAD),

    # ── Clinic ────────────────────────────────────────────────────────────────
    ("CLINIC", True, [0,0,0,0,0], ""),
    ("Continuity Clinic Template",        False, [1,1,1,1,1], LIVE),
    ("Cancel Clinic Rules",               False, [0,1,1,1,1], SOON),
    ("Auto-Assign Clinic by Block",       False, [0,0,0,1,1], ROAD),

    # ── Academic Year ─────────────────────────────────────────────────────────
    ("ACADEMIC YEAR", True, [0,0,0,0,0], ""),
    ("AY Progression (July start)",       False, [1,1,1,1,1], LIVE),
    ("AY Visibility & Viewer Lock",       False, [1,1,1,1,1], SOON),
    ("Off-Cycle Residents",               False, [0,1,1,1,1], SOON),
    ("Cohort / Team Groupings (A/B/C)",   False, [0,0,0,0,1], ROAD),
    ("Historical AY Data (compliance)",   False, [0,0,0,0,1], ROAD),

    # ── Integrations ──────────────────────────────────────────────────────────
    ("INTEGRATIONS", True, [0,0,0,0,0], ""),
    ("Calendar Subscriptions (iCal)",     False, [0,0,1,1,1], SOON),
    ("MedHub",                            False, [0,0,0,1,1], ROAD),
    ("New Innovations",                   False, [0,0,0,1,1], ROAD),
    ("MyEvaluations / Other",             False, [0,0,0,0,1], ROAD),

    # ── Smart Scheduling ──────────────────────────────────────────────────────
    ("SMART SCHEDULING", True, [0,0,0,0,0], ""),
    ("Staff-by Rules (eligibility)",      False, [0,0,1,1,1], ROAD),
    ("Anonymous Templates",               False, [0,0,1,1,1], ROAD),
    ("Staff Requests / Work Preferences", False, [0,0,0,1,1], SOON),
    ("Autoscheduler",                     False, [0,0,0,1,1], ROAD),
    ("Multi-Schedule / Linked Schedules", False, [0,0,0,0,1], ROAD),
]

# ── Client Profile columns ─────────────────────────────────────────────────────
CP_GROUPS = [
    ("IDENTIFICATION", "E3F2FD", [
        ("Org / Client Name",  "Text"),
        ("Program Type",       "IM / EM / Surgery / Peds / Psych / FM / Other"),
        ("Program Size",       "Small (<20) / Mid (20–50) / Large (50+)"),
    ]),
    ("SCHEDULING NEEDS", "E8F5E9", [
        ("Schedule Types",     "Block / Clinic / Call / Shift — all that apply"),
        ("Call or Shift?",     "Call / Shift (EM) / Neither"),
        ("Complexity Level",   "Basic (manual) / Patterns + rules / Full automation"),
    ]),
    ("INTEGRATIONS", "FCE4EC", [
        ("Integration Needs",  "None / iCal / MedHub / New Innovations / Other"),
    ]),
    ("OUTPUT", "E8EAF6", [
        ("Persona",            "Community / Structured / Rules Architect / Integrated Automator / Academic MC"),
        ("Can Migrate Now?",   "Yes / No / Pending: [feature]"),
        ("Blocking Features",  "List roadmap items blocking migration"),
        ("Notes",              "Text"),
    ]),
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def rgb(h):
    h = h.lstrip('#')
    return {"red": int(h[0:2],16)/255, "green": int(h[2:4],16)/255, "blue": int(h[4:6],16)/255}

def cell(value, bold=False, bg=None, fg=None, size=10, halign=None,
         valign="MIDDLE", wrap=True, italic=False):
    fmt = {
        "textFormat": {"bold": bold, "fontSize": size, "italic": italic},
        "wrapStrategy": "WRAP" if wrap else "CLIP",
        "verticalAlignment": valign,
    }
    if bg: fmt["backgroundColor"] = rgb(bg)
    if fg: fmt["textFormat"]["foregroundColor"] = rgb(fg)
    if halign: fmt["horizontalAlignment"] = halign
    return {"userEnteredValue": {"stringValue": str(value)}, "userEnteredFormat": fmt}

def check_cell(needed, status):
    """Green/amber/pink ✓ if needed; grey dash if not."""
    if not needed:
        return cell("—", bg=EMPTY_BG[0], fg=EMPTY_BG[1], halign="CENTER", size=12)
    # Color by availability
    if status == LIVE:
        bg, fg = CHK_LIVE
    elif status == SOON:
        bg, fg = CHK_SOON
    else:  # ROAD
        bg, fg = CHK_ROAD
    return cell(CHECK, bold=True, bg=bg, fg=fg, halign="CENTER", size=13)

def merge(sid, r0, r1, c0, c1):
    return {"mergeCells": {
        "range": {"sheetId": sid, "startRowIndex": r0, "endRowIndex": r1,
                  "startColumnIndex": c0, "endColumnIndex": c1},
        "mergeType": "MERGE_ALL"
    }}

def col_width(sid, ci, w):
    return {"updateDimensionProperties": {
        "range": {"sheetId": sid, "dimension": "COLUMNS",
                   "startIndex": ci, "endIndex": ci+1},
        "properties": {"pixelSize": w}, "fields": "pixelSize"
    }}

def row_height(sid, ri, h):
    return {"updateDimensionProperties": {
        "range": {"sheetId": sid, "dimension": "ROWS",
                   "startIndex": ri, "endIndex": ri+1},
        "properties": {"pixelSize": h}, "fields": "pixelSize"
    }}


# ── Build Tier Guide ───────────────────────────────────────────────────────────

def build_tier_guide(tg_id):
    """Returns (rows_data, merge_requests, dim_requests)."""
    n_p = len(PERSONAS)
    n_cols = 1 + n_p + 1  # feature col + 5 persona cols + status col

    rows = []
    merges = []
    dims = []

    # ── Row 0: Title ──────────────────────────────────────────────────────────
    rows.append({"values":
        [cell("Amion Next — Residency Client Profile: Tier Guide",
              bold=True, bg=DARK, fg=WHITE, size=13)] +
        [cell("", bg=DARK) for _ in range(n_cols - 1)]
    })
    merges.append(merge(tg_id, 0, 1, 0, n_cols))
    dims.append(row_height(tg_id, 0, 30))

    # ── Rows 1–4: Persona descriptions ───────────────────────────────────────
    label_row   = [cell("", bg="ECEFF1")]
    desc_row    = [cell("", bg="FAFAFA")]
    example_row = [cell("Examples", bold=True, bg="ECEFF1", fg="546E7A", size=8, italic=True)]
    gate_row    = [cell("Ready when", bold=True, bg="ECEFF1", size=8)]

    for i, p in enumerate(PERSONAS):
        pc = P_COLORS[i]; pl = P_LIGHT[i]
        label_row.append(cell(f"{p['name']}\n{p['label']}", bold=True,
                               bg=pc, fg=WHITE, size=10, halign="CENTER"))
        desc_row.append(cell(p["desc"], size=8, bg=pl, halign="CENTER"))
        example_row.append(cell(p["example"], size=8, italic=True, bg=pl, fg="546E7A", halign="CENTER"))
        gate_row.append(cell(p["gate"], size=8, bg=pl, fg="546E7A", halign="CENTER"))

    label_row.append(cell("Status in\nAmion Next", bold=True, bg="37474F", fg=WHITE, size=9, halign="CENTER"))
    desc_row.append(cell("", bg="FAFAFA"))
    example_row.append(cell("", bg="FAFAFA"))
    gate_row.append(cell("", bg="FAFAFA"))

    rows.append({"values": label_row})
    rows.append({"values": desc_row})
    rows.append({"values": example_row})
    rows.append({"values": gate_row})
    for ri, h in [(1, 44), (2, 52), (3, 40), (4, 22)]:
        dims.append(row_height(tg_id, ri, h))

    # ── Legend / key rows ─────────────────────────────────────────────────────
    legend_cells = [cell("Feature", bold=True, bg=SECTION, fg=WHITE, size=9)]
    for i in range(n_p):
        legend_cells.append(cell("", bg=P_COLORS[i]))
    legend_cells.append(cell("", bg="37474F"))
    rows.append({"values": legend_cells})
    dims.append(row_height(tg_id, 5, 8))  # thin separator

    key_cells = [
        cell("  ✓ = needed by this program type", size=8, fg="546E7A", italic=True, bg="FAFAFA")
    ]
    for i in range(n_p): key_cells.append(cell("", bg=P_LIGHT[i]))
    key_cells.append(cell("", bg="FAFAFA"))
    rows.append({"values": key_cells})
    dims.append(row_height(tg_id, 6, 18))

    status_key = [cell("", bg="FAFAFA")]
    for _ in range(n_p): status_key.append(cell("", bg="FAFAFA"))
    status_key.append(cell(
        f"{LIVE}  =  in Next today\n{SOON}  =  shipping soon\n{ROAD}  =  on roadmap",
        size=7, italic=True, fg="546E7A", bg="FAFAFA"
    ))
    rows.append({"values": status_key})
    dims.append(row_height(tg_id, 7, 40))

    # ── Feature rows ──────────────────────────────────────────────────────────
    for feat_label, is_section, checks, status in FEATURES:
        if is_section:
            section_cells = [
                cell(feat_label, bold=True, bg=SECTION, fg=WHITE, size=9)
            ] + [cell("", bg=SECTION) for _ in range(n_p)] + [cell("", bg=SECTION)]
            rows.append({"values": section_cells})
            merges.append(merge(tg_id, len(rows)-1, len(rows), 0, n_cols))
            dims.append(row_height(tg_id, len(rows)-1, 22))
        else:
            row_cells = [cell(feat_label, size=9)]
            for i, needed in enumerate(checks):
                row_cells.append(check_cell(needed, status))
            row_cells.append(cell(status, size=8, italic=True,
                                   fg={"✓  Live":"1B5E20","→  Coming soon":"E65100","◌  On roadmap":"880E4F"}.get(status,"546E7A"),
                                   bg={"✓  Live":CHK_LIVE[0],"→  Coming soon":CHK_SOON[0],"◌  On roadmap":CHK_ROAD[0]}.get(status,"FAFAFA")))
            rows.append({"values": row_cells})
            dims.append(row_height(tg_id, len(rows)-1, 22))

    # Column widths for Tier Guide
    widths = [220] + [130]*n_p + [160]
    for ci, w in enumerate(widths):
        dims.append(col_width(tg_id, ci, w))

    return rows, merges, dims


# ── Build Client Profile ───────────────────────────────────────────────────────

def build_client_profile(cp_id):
    col_info = []
    for group_label, group_color, cols in CP_GROUPS:
        for col_name, col_note in cols:
            col_info.append((group_label, group_color, col_name, col_note))

    n = len(col_info)
    rows = []
    merges = []
    dims = []

    # Title row
    rows.append({"values":
        [cell(TITLE, bold=True, bg=DARK, fg=WHITE, size=11)] +
        [cell("", bg=DARK) for _ in range(n-1)]
    })
    merges.append(merge(cp_id, 0, 1, 0, n))
    dims.append(row_height(cp_id, 0, 26))

    # Group header row (labels added after via separate updateCells)
    group_row = {"values": [cell("", bg=gc) for _, gc, _, _ in col_info]}
    rows.append({"values": [cell("", bg=gc) for _, gc, _, _ in col_info]})
    dims.append(row_height(cp_id, 1, 20))

    # Column headers
    rows.append({"values": [
        cell(cn, bold=True, bg="263238", fg=WHITE, size=9, halign="CENTER")
        for _, _, cn, _ in col_info
    ]})
    dims.append(row_height(cp_id, 2, 34))

    # Value guide row
    rows.append({"values": [
        cell(note, size=8, bg="F8F9FA", fg="546E7A")
        for _, _, _, note in col_info
    ]})
    dims.append(row_height(cp_id, 3, 46))

    # Group label merges
    current_group = None
    group_start = 0
    group_color = None
    for i, (gl, gc, _, _) in enumerate(col_info):
        if gl != current_group:
            if current_group is not None and i - group_start > 1:
                merges.append(merge(cp_id, 1, 2, group_start, i))
            current_group = gl
            group_start = i
            group_color = gc
    if n - group_start > 1:
        merges.append(merge(cp_id, 1, 2, group_start, n))

    # Column widths  (matches new 10-col CP_GROUPS)
    widths = [
        190, 110, 110,         # Identification (3)
        180, 90, 220,          # Scheduling Needs (3)
        230,                   # Integrations (1)
        200, 150, 240, 200,    # Output (4)
    ]
    for ci, w in enumerate(widths[:n]):
        dims.append(col_width(cp_id, ci, w))

    return rows, merges, dims, col_info


# ── Main ───────────────────────────────────────────────────────────────────────

def create_sheet():
    svc = get_sheets_service()

    if EXISTING_SHEET_ID:
        sid = EXISTING_SHEET_ID
        ss = svc.spreadsheets().get(
            spreadsheetId=sid,
            fields="sheets.properties,sheets.bandedRanges"
        ).execute()
        sheet_ids = {s["properties"]["title"]: s["properties"]["sheetId"] for s in ss["sheets"]}

        pre = []
        for s in ss["sheets"]:
            for br in s.get("bandedRanges", []):
                pre.append({"deleteBanding": {"bandedRangeId": br["bandedRangeId"]}})
            pre.append({"unmergeCells": {
                "range": {"sheetId": s["properties"]["sheetId"],
                          "startRowIndex": 0, "endRowIndex": 200,
                          "startColumnIndex": 0, "endColumnIndex": 60}
            }})
            pre.append({"updateSheetProperties": {
                "properties": {"sheetId": s["properties"]["sheetId"],
                               "gridProperties": {"frozenColumnCount": 0}},
                "fields": "gridProperties.frozenColumnCount"
            }})
        if pre:
            svc.spreadsheets().batchUpdate(spreadsheetId=sid, body={"requests": pre}).execute()
        print(f"Using existing sheet: https://docs.google.com/spreadsheets/d/{sid}")
    else:
        body = {
            "properties": {"title": TITLE},
            "sheets": [
                {"properties": {"title": "Tier Guide",     "index": 0}},
                {"properties": {"title": "Client Profile", "index": 1}},
            ]
        }
        ss = svc.spreadsheets().create(body=body, fields="spreadsheetId,sheets").execute()
        sid = ss["spreadsheetId"]
        sheet_ids = {s["properties"]["title"]: s["properties"]["sheetId"] for s in ss["sheets"]}
        print(f"Created: https://docs.google.com/spreadsheets/d/{sid}")

    tg_id = sheet_ids["Tier Guide"]
    cp_id = sheet_ids["Client Profile"]

    tg_rows, tg_merges, tg_dims = build_tier_guide(tg_id)
    cp_rows, cp_merges, cp_dims, col_info = build_client_profile(cp_id)
    n_cp = len(col_info)

    requests = []

    # Ensure enough columns on Client Profile
    if EXISTING_SHEET_ID and n_cp > 26:
        requests.append({"appendDimension": {
            "sheetId": cp_id, "dimension": "COLUMNS", "length": n_cp - 26 + 5
        }})

    # Write Tier Guide
    requests.append({"updateCells": {
        "rows": tg_rows, "fields": "userEnteredValue,userEnteredFormat",
        "start": {"sheetId": tg_id, "rowIndex": 0, "columnIndex": 0}
    }})

    # Write group labels on Client Profile row 1
    for group_label, group_color, cols in CP_GROUPS:
        col_start = next(i for i, (gl,_,_,_) in enumerate(col_info) if gl == group_label)
        requests.append({"updateCells": {
            "rows": [{"values": [cell(group_label, bold=True, bg=group_color,
                                       halign="CENTER", size=9)]}],
            "fields": "userEnteredValue,userEnteredFormat",
            "start": {"sheetId": cp_id, "rowIndex": 1, "columnIndex": col_start}
        }})

    # Write Client Profile data rows (0, 2, 3 — row 1 labels already written)
    requests.append({"updateCells": {
        "rows": [cp_rows[0]],
        "fields": "userEnteredValue,userEnteredFormat",
        "start": {"sheetId": cp_id, "rowIndex": 0, "columnIndex": 0}
    }})
    requests.append({"updateCells": {
        "rows": cp_rows[2:],
        "fields": "userEnteredValue,userEnteredFormat",
        "start": {"sheetId": cp_id, "rowIndex": 2, "columnIndex": 0}
    }})

    # Merges
    requests.extend(tg_merges)
    requests.extend(cp_merges)

    # Dimensions
    requests.extend(tg_dims)
    requests.extend(cp_dims)

    # Freeze rows
    requests.append({"updateSheetProperties": {
        "properties": {"sheetId": tg_id, "gridProperties": {"frozenRowCount": 5}},
        "fields": "gridProperties.frozenRowCount"
    }})
    requests.append({"updateSheetProperties": {
        "properties": {"sheetId": cp_id, "gridProperties": {"frozenRowCount": 3}},
        "fields": "gridProperties.frozenRowCount"
    }})

    # Alternating banding on Client Profile
    requests.append({"addBanding": {"bandedRange": {
        "range": {"sheetId": cp_id, "startRowIndex": 4, "endRowIndex": 104,
                   "startColumnIndex": 0, "endColumnIndex": n_cp},
        "rowProperties": {
            "firstBandColor":  {"red":1, "green":1, "blue":1},
            "secondBandColor": {"red":0.972, "green":0.976, "blue":0.98},
        }
    }}})

    # Bottom borders under header rows on Client Profile
    for ri in [1, 2, 3]:
        requests.append({"updateBorders": {
            "range": {"sheetId": cp_id, "startRowIndex": ri, "endRowIndex": ri+1,
                       "startColumnIndex": 0, "endColumnIndex": n_cp},
            "bottom": {"style": "SOLID_MEDIUM", "color": rgb("263238")}
        }})

    svc.spreadsheets().batchUpdate(spreadsheetId=sid, body={"requests": requests}).execute()
    print(f"Sheet built.\nURL: https://docs.google.com/spreadsheets/d/{sid}")


if __name__ == "__main__":
    create_sheet()
