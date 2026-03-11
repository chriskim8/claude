"""
Enrich Client Profile sheet with pager and API report usage from Snowflake.

Adds/updates the Features column (col J) with:
  - Pager systems in use (TigerConnect, DocHalo, group paging, etc.)
  - Whether the org has unsupported reports (migration blocker)

Run once — will open browser for Snowflake SSO auth.

Sources:
  - Paging: PRODUCTION.DUMP_AMION_APP.SCHEDULES.settings + CONTACT_METHODS
  - Reports: stream_amion_app.report_comparison_results (L90D)
  - THDATA-689, THDATA-909
"""
import sys
sys.path.insert(0, '/Users/chriskim/google-services')
from google_client import get_sheets_service
import snowflake.connector

SHEET_ID = '1oSFvhIWlP9xBfaMIG9WKxUPyU-xpUTVZ8aovETRcIVQ'

# ── Snowflake ─────────────────────────────────────────────────────────────────

PAGER_QUERY = """
SELECT
    o.name                                                         AS org_name,
    l.amionc_reference_id                                          AS viewer_code,
    BOOLOR_AGG(
        TRY_CAST(
            JSON_EXTRACT_PATH_TEXT(s.settings, 'enable_group_paging')
        AS BOOLEAN)
    )                                                              AS group_paging,
    LISTAGG(DISTINCT
        CASE cm.system_code
            WHEN 'g' THEN 'TigerConnect'
            WHEN 'h' THEN 'DocHalo'
            WHEN 'q' THEN 'QlicSoft'
            WHEN 'r' THEN 'CoreText'
            WHEN 'C' THEN 'Cureatr'
            WHEN 'O' THEN 'OnPage'
            WHEN 'T' THEN 'CareThread'
        END,
    ', ')                                                          AS pager_systems,
    BOOLOR_AGG(
        cm.value ILIKE '%telmed%'
    )                                                              AS telmediq,
    BOOLOR_AGG(
        cm.value ILIKE '%archwireless%'
    )                                                              AS archwireless,
    BOOLOR_AGG(
        cm.type ILIKE '%Vocera%' OR cm.value ILIKE '%Vocera%'
    )                                                              AS vocera,
    MAX(CASE
        WHEN JSON_EXTRACT_PATH_TEXT(s.settings, 'paging_domain') IS NOT NULL
             AND JSON_EXTRACT_PATH_TEXT(s.settings, 'paging_domain') != ''
        THEN JSON_EXTRACT_PATH_TEXT(s.settings, 'paging_domain')
    END)                                                           AS paging_domain
FROM PRODUCTION.DUMP_AMION_APP.ORGANIZATIONS o
JOIN PRODUCTION.DUMP_AMION_APP.LICENSES l
    ON l.organization_id = o.id
JOIN PRODUCTION.DUMP_AMION_APP.SCHEDULES s
    ON s.organization_id = o.id
    AND s.residency = 1
    AND s.deleted_at IS NULL
LEFT JOIN PRODUCTION.DUMP_AMION_APP.CONTACT_METHODS cm
    ON cm.schedule_id = s.id
WHERE o.demo = FALSE
GROUP BY o.name, l.amionc_reference_id
"""

REPORTS_QUERY = """
SELECT
    o.name                                                          AS org_name,
    COUNT(DISTINCT CASE
        WHEN r.report_type NOT ILIKE '%unsupported%' THEN r.access_code
    END)                                                            AS schedules_with_supported_reports,
    COUNT(DISTINCT CASE
        WHEN r.report_type ILIKE '%unsupported%' THEN r.access_code
    END)                                                            AS schedules_with_unsupported_reports
FROM PRODUCTION.STREAM_AMION_APP.REPORT_COMPARISON_RESULTS r
JOIN PRODUCTION.DUMP_AMION_APP.LICENSES l
    ON LOWER(l.amionc_reference_id) = LOWER(r.access_code)
JOIN PRODUCTION.DUMP_AMION_APP.ORGANIZATIONS o
    ON o.id = l.organization_id
WHERE r.created_at >= DATEADD(day, -90, CURRENT_DATE)
  AND o.demo = FALSE
GROUP BY o.name
"""


def run_snowflake_queries():
    print("Connecting to Snowflake (browser auth will open)...")
    conn = snowflake.connector.connect(connection_name="doximity")
    cur = conn.cursor()

    # Auto-discover a usable warehouse
    cur.execute("SHOW WAREHOUSES")
    warehouses = [row[0] for row in cur.fetchall()]
    print(f"Available warehouses: {warehouses}")
    if not warehouses:
        raise RuntimeError("No warehouses available for your role.")
    # Prefer analyst warehouse, fall back to first available
    wh = next((w for w in warehouses if 'ANALYST' in w.upper()), warehouses[0])
    cur.execute(f"USE WAREHOUSE {wh}")
    print(f"Using warehouse: {wh}")

    import os, json, tempfile
    pager_cache = os.path.join(tempfile.gettempdir(), 'amion_pager_cache.json')

    if os.path.exists(pager_cache):
        print("Loading pager data from cache...")
        with open(pager_cache) as f:
            pager_data = json.load(f)
        print(f"  {len(pager_data)} cached rows")
    else:
        print("Running pager query...")
        cur.execute(PAGER_QUERY)
        pager_cols = [c[0].lower() for c in cur.description]
        pager_rows = cur.fetchall()
        pager_data = [dict(zip(pager_cols, row)) for row in pager_rows]
        print(f"  {len(pager_data)} org/viewer_code rows")
        with open(pager_cache, 'w') as f:
            json.dump(pager_data, f, default=str)
        print(f"  Cached to {pager_cache}")

    print("Running reports query...")
    cur.execute(REPORTS_QUERY)
    report_cols = [c[0].lower() for c in cur.description]
    report_rows = cur.fetchall()
    report_data = [dict(zip(report_cols, row)) for row in report_rows]
    print(f"  {len(report_data)} org rows")

    cur.close()
    conn.close()
    return pager_data, report_data


def build_org_feature_map(pager_data, report_data):
    """
    Returns dict: normalized_org_name -> list of extra feature strings
    """
    def norm(s):
        return s.lower().strip() if s else ''

    # Aggregate pager features per org (multiple viewer codes per org)
    pager_by_org = {}
    for row in pager_data:
        key = norm(row['org_name'])
        if key not in pager_by_org:
            pager_by_org[key] = set()
        if row.get('group_paging'):
            pager_by_org[key].add('Group paging')
        systems = row.get('pager_systems') or ''
        for s in [x.strip() for x in systems.split(',') if x.strip()]:
            pager_by_org[key].add(s)
        if row.get('telmediq'):
            pager_by_org[key].add('TelmedIQ')
        if row.get('archwireless'):
            pager_by_org[key].add('Archwireless')
        if row.get('vocera'):
            pager_by_org[key].add('Vocera')
        if row.get('paging_domain'):
            pager_by_org[key].add('Paging domain')

    # Reports per org
    report_by_org = {}
    for row in report_data:
        key = norm(row['org_name'])
        unsupported = row.get('schedules_with_unsupported_reports') or 0
        supported = row.get('schedules_with_supported_reports') or 0
        if unsupported > 0:
            report_by_org[key] = f'Unsupported reports ({unsupported})'
        elif supported > 0:
            report_by_org[key] = f'Supported reports ({supported})'

    # Merge
    all_orgs = set(list(pager_by_org.keys()) + list(report_by_org.keys()))
    result = {}
    for org in all_orgs:
        extras = sorted(pager_by_org.get(org, set()))
        if org in report_by_org:
            extras.append(report_by_org[org])
        if extras:
            result[org] = extras
    return result


def update_sheet(feature_map):
    svc = get_sheets_service()

    # Read current sheet data
    result = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range='Client Profile!A3:K161'
    ).execute()
    rows = result.get('values', [])

    def norm(s):
        return s.lower().strip() if s else ''

    FEAT_IDX = 9   # col J = Features (after deleting old J+K)
    updates = []
    matched = 0
    unmatched = []

    for i, row in enumerate(rows, start=3):
        new_row = list(row) + [''] * (11 - len(row))
        org_name = norm(new_row[0])

        # Exact match first, then try partial
        extras = feature_map.get(org_name)
        if not extras:
            for key in feature_map:
                if org_name in key or key in org_name:
                    extras = feature_map[key]
                    break

        if extras:
            existing = new_row[FEAT_IDX]
            existing_parts = [f.strip() for f in existing.split(',') if f.strip()]
            # Merge: add new features not already present
            for e in extras:
                if e not in existing_parts:
                    existing_parts.append(e)
            new_feat = ', '.join(existing_parts)
            if new_feat != existing:
                updates.append({'range': f'Client Profile!J{i}', 'values': [[new_feat]]})
                matched += 1
        else:
            unmatched.append(new_row[0])

    if updates:
        svc.spreadsheets().values().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={'valueInputOption': 'RAW', 'data': updates}
        ).execute()
        print(f"Updated features for {matched} orgs.")

    print(f"\nNo Snowflake match found for {len(unmatched)} orgs:")
    for u in unmatched[:20]:
        print(f"  - {u}")


def main():
    pager_data, report_data = run_snowflake_queries()
    feature_map = build_org_feature_map(pager_data, report_data)
    print(f"\nBuilt feature map for {len(feature_map)} orgs.")
    print("Sample:", list(feature_map.items())[:5])
    update_sheet(feature_map)
    print("\nDone. Open sheet to verify:")
    print(f"  https://docs.google.com/spreadsheets/d/{SHEET_ID}")


if __name__ == '__main__':
    main()
