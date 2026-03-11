"""
Update Amion Next — Residency Client Profile spreadsheet.
1. Fix unlabeled column headers on "Client Profile" tab.
2. Create "CS — Migration Readiness" tab with formula-driven rows.
"""
import sys
sys.path.insert(0, '/Users/chriskim/google-services')
from google_client import get_sheets_service

SHEET_ID = '1oSFvhIWlP9xBfaMIG9WKxUPyU-xpUTVZ8aovETRcIVQ'
CS_TAB_TITLE = 'CS — Migration Readiness'


def get_sheet_metadata(svc):
    meta = svc.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    sheets = {s['properties']['title']: s['properties']['sheetId']
              for s in meta['sheets']}
    return sheets


# ── Step 1: Fix unlabeled headers on Client Profile ───────────────────────────

def fix_client_profile_headers(svc):
    print("Step 1: Fixing unlabeled column headers on 'Client Profile'...")
    svc.spreadsheets().values().batchUpdate(
        spreadsheetId=SHEET_ID,
        body={
            'valueInputOption': 'RAW',
            'data': [
                {'range': 'Client Profile!E2', 'values': [['Staff']]},
                {'range': 'Client Profile!F2', 'values': [['Services']]},
                {'range': 'Client Profile!I2', 'values': [['Block / Clinic']]},
                {'range': 'Client Profile!J2', 'values': [['Type 5']]},
                {'range': 'Client Profile!K2', 'values': [['Total Assignments']]},
            ]
        }
    ).execute()
    print("  Done.")


# ── Step 2: Create CS tab ─────────────────────────────────────────────────────

def get_client_profile_row_count(svc):
    result = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range='Client Profile!A:A'
    ).execute()
    return len(result.get('values', []))


def create_cs_tab(svc, sheets):
    if CS_TAB_TITLE in sheets:
        print(f"  Tab '{CS_TAB_TITLE}' already exists, skipping creation.")
        return sheets[CS_TAB_TITLE]

    print(f"Step 2a: Creating '{CS_TAB_TITLE}' tab...")
    resp = svc.spreadsheets().batchUpdate(
        spreadsheetId=SHEET_ID,
        body={'requests': [{'addSheet': {'properties': {
            'title': CS_TAB_TITLE,
            'index': 2
        }}}]}
    ).execute()
    new_id = resp['replies'][0]['addSheet']['properties']['sheetId']
    print(f"  Created with sheetId={new_id}")
    return new_id


def write_cs_headers(svc):
    print("Step 2b: Writing CS tab headers...")
    svc.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range=f"'{CS_TAB_TITLE}'!A1:F1",
        valueInputOption='RAW',
        body={'values': [['Client', 'Tier', 'Specialties', '# Programs', 'Schedules', 'Migration Readiness']]}
    ).execute()
    print("  Done.")


def write_cs_formulas(svc, total_rows):
    # Client Profile data starts at row 3 (row 1=title, row 2=headers)
    # We map to CS tab rows 2..N
    print(f"Step 2c: Writing {total_rows - 2} formula rows to CS tab...")
    rows = []
    for src_row in range(3, total_rows + 1):
        rows.append([
            f"='Client Profile'!A{src_row}",
            f"='Client Profile'!B{src_row}",
            f"='Client Profile'!C{src_row}",
            f"='Client Profile'!D{src_row}",
            f"=SUBSTITUTE('Client Profile'!M{src_row},CHAR(10),\", \")",
            ''  # Migration Readiness — blank for PS to fill
        ])
    svc.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range=f"'{CS_TAB_TITLE}'!A2",
        valueInputOption='USER_ENTERED',
        body={'values': rows}
    ).execute()
    print(f"  Wrote {len(rows)} rows.")


def apply_formatting(svc, sheet_id, data_row_count):
    requests = []

    # 2d: Freeze header row
    requests.append({'updateSheetProperties': {
        'properties': {'sheetId': sheet_id, 'gridProperties': {'frozenRowCount': 1}},
        'fields': 'gridProperties.frozenRowCount'
    }})

    # 2e: Protect columns A–E (warningOnly)
    requests.append({'addProtectedRange': {
        'protectedRange': {
            'range': {'sheetId': sheet_id, 'startColumnIndex': 0, 'endColumnIndex': 5},
            'description': 'Formula columns — edit source data in Client Profile tab',
            'warningOnly': True
        }
    }})

    # 2f: Column widths (in pixels)
    col_widths = [260, 180, 200, 100, 300, 220]
    for col_idx, width in enumerate(col_widths):
        requests.append({'updateDimensionProperties': {
            'range': {
                'sheetId': sheet_id,
                'dimension': 'COLUMNS',
                'startIndex': col_idx,
                'endIndex': col_idx + 1
            },
            'properties': {'pixelSize': width},
            'fields': 'pixelSize'
        }})

    print("Step 2d–2f: Applying freeze, protection, column widths...")
    svc.spreadsheets().batchUpdate(
        spreadsheetId=SHEET_ID,
        body={'requests': requests}
    ).execute()
    print("  Done.")


def main():
    svc = get_sheets_service()
    sheets = get_sheet_metadata(svc)
    print(f"Existing tabs: {list(sheets.keys())}")

    # Step 1
    fix_client_profile_headers(svc)

    # Step 2
    total_rows = get_client_profile_row_count(svc)
    print(f"Client Profile has {total_rows} rows (including headers).")

    cs_sheet_id = create_cs_tab(svc, sheets)
    write_cs_headers(svc)
    write_cs_formulas(svc, total_rows)
    apply_formatting(svc, cs_sheet_id, total_rows)

    print("\nAll done. Open the sheet to verify:")
    print(f"  https://docs.google.com/spreadsheets/d/{SHEET_ID}")


if __name__ == '__main__':
    main()
