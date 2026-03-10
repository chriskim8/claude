# Story: Allow schedule managers to download an ADP-compatible payroll CSV

**Type:** Story
**Epic:** AMIONMGR-2950 — Integration ADP
**Priority:** P1
**Reporter:** Chris Kim
**Assignee:** [TBD]
**Sprint:** [TBD]
**Product Proposal:** https://docs.google.com/document/d/1hmMpysUfoBJX86-8AkueMm8I6uDHFqf-FZhy9BKef6Y

---

## Background / Context

Once a schedule manager has reviewed the payroll report (Story 6), they need to export it in a format that ADP can ingest directly. This story adds a download button to the Reports page that produces an ADP-compatible CSV file with a specific column order and structure. The CSV can be downloaded at any time after a report has been created — there are no approval gates in MVP.

The column structure is ADP-specific and includes placeholder columns for Staff Sign-off and Supervisor Sign-off (both empty in MVP, populated in a future approval workflow iteration).

- Source: [Product Proposal](https://docs.google.com/document/d/1hmMpysUfoBJX86-8AkueMm8I6uDHFqf-FZhy9BKef6Y) | [Technical Proposal](https://docs.google.com/document/d/1jYjJGDUFmPp57iTUHDjFWvfhH_DUEteSMF2Vtbx7evI)

---

## User Story

**As a** schedule manager at an org with ADP payroll integration enabled
**I want** to download my payroll report as an ADP-compatible CSV file
**So that** I can submit accurate payroll data directly to ADP without manual reformatting

---

## Requirements

- A "Download" button is available on the Reports page whenever a report is active (either just created or re-opened from saved reports)
- Clicking "Download" exports the current report data as a CSV file
- The CSV contains one row per aggregated report row (same grouping logic as the index table: staff → agreement type → pay code)
- Columns in the ADP-compatible CSV, in this exact order:

| # | Column | Notes |
|---|---|---|
| 1 | Vendor ID | From staff's payroll StaffIntegration record |
| 2 | Remit To | From staff's payroll StaffIntegration record |
| 3 | First Name | Staff first name |
| 4 | Last Name | Staff last name |
| 5 | Agreement Type | From pay code |
| 6 | Pay Code | Pay code name |
| 7 | Pay Code ID | Pay code identifier |
| 8 | Cost Center ID | From pay code |
| 9 | Hours / Units | Hours for assignments; count (units) for activations |
| 10 | Amount | Pay code amount × hours/units |
| 11 | Pay Period Start Date | From report params |
| 12 | Staff Sign-off | Empty in MVP; reserved for approval workflow |
| 13 | Supervisor Sign-off | Empty in MVP; reserved for approval workflow |

- Excluded rows (missing mappings, flagged items from Story 6) are **not included** in the CSV export
- The file is named descriptively (e.g., `adp-payroll-[report-name]-[start-date].csv`)
- The CSV can be re-downloaded at any time after report creation — re-downloading re-runs the report with original parameters

## Non-Functional Requirements

- **Performance**: CSV generation should complete quickly; for large orgs, consider streaming the response rather than building the full file in memory
- **Security**: Download is scoped to the schedule manager's org and schedule; no cross-org data leakage possible; CSV does not include PII beyond names (no SSNs, DOBs, etc.)
- **Accessibility**: Download button must be keyboard accessible and have a clear label; no accessibility concerns with the file itself
- **Scalability**: CSV generation must handle large pay periods with many staff efficiently — avoid loading entire dataset into memory for large orgs
- **Reliability**: If CSV generation fails (e.g., data error mid-stream), the error should be surfaced cleanly; a partial/corrupted CSV should never be delivered to the user

---

## Designs

- **Figma:** https://www.figma.com/design/upJE6mbXBXFFftLTU65Fha/ADP?node-id=76-2252
- **Design notes:** Button label: "Download CSV" or "Export to ADP." Placement: in the reports nav header (consistent with how the proposal describes "Download button in reports nav header"). Confirm whether there is a loading/spinner state for large exports.

---

## API Information

- `GET /schedules/:id/payroll_reports/:report_id/download` — re-runs the report with original parameters and streams the ADP-compatible CSV as a file download
- Response headers: `Content-Type: text/csv`, `Content-Disposition: attachment; filename="adp-payroll-[name]-[start_date].csv"`

---

## Technical Notes

The CSV generation layer should apply ADP-specific formatting on top of the vendor-agnostic report data layer (same data source as Story 6). The 13-column structure must match ADP's expected format exactly — verify against the ADP specs from the Providence meeting (Nov 2025). Columns 12–13 (Staff Sign-off, Supervisor Sign-off) are intentionally blank in MVP — include the column headers in the CSV but leave values empty to preserve the expected file structure for ADP ingestion.

Confirm with eng whether streaming the CSV response is preferable to generating it in memory, especially given Providence's ~125k caregiver scale.

---

## Dox Analytics

- `adp_report_csv_downloaded` — fires when a schedule manager downloads a CSV (include report ID, org ID, schedule ID, row count)

---

## Acceptance Criteria

- [ ] Given a schedule manager is viewing an active report (just created or re-opened), when they click "Download CSV," then a CSV file is downloaded to their device
- [ ] Given the downloaded CSV, when it is opened, then it contains exactly 13 columns in the specified ADP column order, with one row per aggregated report row (staff → agreement type → pay code grouping)
- [ ] Given a staff member or service is flagged/excluded in the report view, when the CSV is downloaded, then those rows are not present in the CSV file
- [ ] Given the report contains activation data, when the CSV is downloaded, then activation rows show the unit count (not hours) in the Hours/Units column and the correct pay code in the Agreement Type/Pay Code columns
- [ ] Given the CSV is downloaded, when columns 12 (Staff Sign-off) and 13 (Supervisor Sign-off) are checked, then the column headers are present but the values are empty for all rows
- [ ] Given the file name of the downloaded CSV, when it is inspected, then it follows the naming convention (e.g., `adp-payroll-february-2026-2026-02-01.csv`)
- [ ] Given a schedule manager downloads a report, when they later re-download the same report, then the CSV re-runs with the original date range params and reflects any data changes since the first download

**QA test case doc:** [TBD]

---

## Rollout & Sign-off

- **Feature flag required?** Yes — gated behind `adp_payroll_integration`
- **Timing constraints?** Depends on Story 6 (Reports page); these two stories should ship together as they form a complete payroll workflow
- **Pre-deployment communication required?** CS should include download instructions in onboarding materials; confirm ADP column format with Providence before shipping
- **Special approvals required?** Recommend a quick review of the CSV output format against ADP's actual import specs before ship

---

## Out of Scope

- Staff or admin sign-off in the CSV (Columns 12–13 are blank in MVP; approval workflow is future work)
- Direct API submission to ADP (file-based export only in MVP)
- Archiving or versioning downloaded reports
- CSV downloads for future integration types (QGenda, New Innovations — future work)
