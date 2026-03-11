# Story: Allow schedule managers to review payroll data in a new ADP Reports page

**Type:** Story
**Epic:** AMIONMGR-2950 — Integration ADP
**Priority:** P1
**Reporter:** Chris Kim
**Assignee:** [TBD]
**Sprint:** [TBD]
**Product Proposal:** https://docs.google.com/document/d/1hmMpysUfoBJX86-8AkueMm8I6uDHFqf-FZhy9BKef6Y

---

## Background / Context

Once org-level payroll configuration is in place (Stories 1–4) and staff can log activations (Story 5), schedule managers need a way to view and verify the aggregated payroll data before exporting it to ADP. This story introduces a new "Reports" section at the schedule level — a sibling to Schedule, Settings, and Stats — where managers can create, name, and review payroll reports for a given pay period.

The report aggregates assignment hours and activation units by staff → agreement type → pay code for the selected date range. Rows missing required mappings (no service → pay code, or no staff → vendor ID) are excluded and flagged. This is a read-only report view in MVP; download is covered in Story 7.

- Source: [Product Proposal](https://docs.google.com/document/d/1hmMpysUfoBJX86-8AkueMm8I6uDHFqf-FZhy9BKef6Y) | [Technical Proposal](https://docs.google.com/document/d/1jYjJGDUFmPp57iTUHDjFWvfhH_DUEteSMF2Vtbx7evI)

---

## User Story

**As a** schedule manager at an org with ADP payroll integration enabled
**I want** to create and view a payroll report for a specific pay period
**So that** I can review aggregated hours and activations by staff and pay code before submitting payroll to ADP

---

## Requirements

**Reports section navigation:**
- A new "Reports" section is accessible from the schedule-level navigation (sibling to Schedule, Settings, Stats)
- Only visible when ADP integration is enabled for the org
- Right-hand sidebar navigation within Reports for integration-specific report types
- In MVP, only one report type is available: "ADP Reports"
- Sidebar contains: a persistent "New Report" CTA + list of saved reports (e.g., "February 2026") that are clickable to re-open

**New Report creation:**
- "New Report" opens a modal with:
  - **Pay period date range** (required — typically one calendar month)
  - **Report name** (required — auto-suggested based on date, editable)
- On creation, the report is run immediately and displayed; report is persisted in the sidebar

**Report index table:**
- Groups rows by: 1) staff, 2) agreement type, 3) pay code
- Aggregation logic: sum units (hours for assignments, count for activations) per grouping; Total = SumUnits × PayCodeRate
- Columns:

| Column | Source |
|---|---|
| Vendor ID | Staff's payroll `StaffIntegration` record |
| Remit To | Staff's payroll `StaffIntegration` record |
| First Name | Staff |
| Last Name | Staff |
| Agreement Type | Pay code via service |
| Pay Code | Pay code name |
| Pay Code ID | Pay code identifier |
| Cost Center ID | Pay code via service |
| Hours / Units | Hours for assignments; count (units) for activations |
| Amount | Pay code amount × hours/units |
| Pay Period Start Date | From report params |

- Rows where the service has no pay code mapping or staff has no Vendor ID are excluded from the table and surfaced in a separate "Flagged items" section or warning banner
- Clicking a saved report in the sidebar re-runs it with the same parameters (live data; not a snapshot)

**Report persistence:**
- Saved in a `payroll_reports` table: `organization_id`, `name`, `start_date`, `end_date`, `created_at`
- A saved report is re-run via a GET param + payroll reports controller redirect when clicked

## Non-Functional Requirements

- **Performance**: Report generation should complete within a reasonable time for large orgs; consider async generation with a loading state for large data sets
- **Security**: Only schedule managers (and above) can access the Reports section; report data is scoped to the schedule's org
- **Accessibility**: Table must be screen reader accessible with proper column headers; sidebar navigation must be keyboard accessible
- **Scalability**: Reports may span large orgs with hundreds of staff; ensure aggregation query is efficient (avoid N+1 on staff/pay code joins)
- **Reliability**: If a report cannot be generated (e.g., data error), surface a clear error state rather than an empty table with no explanation

---

## Designs

- **Figma:** https://www.figma.com/design/upJE6mbXBXFFftLTU65Fha/ADP?node-id=76-2252
- **Design notes:** The sidebar navigation model should be consistent with how other integration-specific sections are handled. The flagged/excluded items section (missing mappings) needs a clear design treatment — a warning banner or separate collapsible section. Confirm whether clicking a saved report shows a loading state while it re-runs.

---

## API Information

- `POST /schedules/:id/payroll_reports` — creates a report record and runs the report (params: name, start_date, end_date)
- `GET /schedules/:id/payroll_reports` — returns list of saved reports for the sidebar
- `GET /schedules/:id/payroll_reports/:report_id` — re-runs and returns report data for the given params
- Report data query: join consolidated assignments + activation StaffRequests for the pay period → join services → pay codes → staff → StaffIntegration; aggregate by staff / agreement type / pay code

---

## Technical Notes

The report data layer must be vendor-agnostic (proposal calls this out explicitly) — the query aggregates Amion-native data (assignments + activations) and the ADP-specific formatting is applied at the CSV export layer (Story 7). Rows excluded due to missing mappings should be collected and returned in a separate "flagged" array alongside the report rows so the UI can surface them clearly.

Re-running on click (rather than snapshotting) is the MVP behavior — acceptable tradeoff. Confirm with eng whether `payroll_reports` table needs a status field for async generation states, or if sync generation is sufficient for MVP scale.

---

## Dox Analytics

- `adp_report_created` — fires when a schedule manager creates a new report (include org ID, schedule ID, date range)
- `adp_report_viewed` — fires when a saved report is opened/re-run (include report ID)
- `adp_report_flagged_items_present` — fires when a report is generated with excluded rows (include count of flagged items)

---

## Acceptance Criteria

- [ ] Given a schedule's org has ADP integration enabled, when a schedule manager navigates to the schedule, then a "Reports" section is visible in the schedule-level navigation
- [ ] Given a schedule manager opens the Reports section, when the page loads, then they see a right-hand sidebar with "ADP Reports" as the available report type, a "New Report" CTA, and any previously saved reports listed by name
- [ ] Given a schedule manager clicks "New Report," when the modal opens, then they can enter a pay period date range and a report name (auto-suggested, editable), and submit to generate the report
- [ ] Given a report is generated, when it loads, then the index table shows rows grouped by staff → agreement type → pay code, with all required columns correctly populated (Vendor ID, Remit To, First/Last Name, Agreement Type, Pay Code, Pay Code ID, Cost Center ID, Hours/Units, Amount, Pay Period Start Date)
- [ ] Given a staff member has no Vendor ID mapping or a service has no pay code mapping, when the report is generated, then those rows are excluded from the table and surfaced in a clear "flagged items" warning
- [ ] Given a saved report exists in the sidebar, when a schedule manager clicks it, then the report is re-run with the original parameters and the updated data is displayed
- [ ] Given a schedule manager does not have the Reports section available (ADP integration disabled), when they navigate to the schedule, then the Reports link is not shown

**QA test case doc:** [TBD]

---

## Rollout & Sign-off

- **Feature flag required?** Yes — gated behind `adp_payroll_integration`
- **Timing constraints?** Depends on Stories 1–5 being complete; this is the primary consumer of all upstream payroll data
- **Pre-deployment communication required?** CS should brief schedule managers on how to use the Reports page during onboarding
- **Special approvals required?** None

---

## Out of Scope

- Staff or admin sign-off / approval columns in the report (future work — approval workflow)
- Snapshotting report data at time of creation (re-runs on click in MVP)
- Multiple integration report types in the sidebar (only ADP in MVP)
- Archiving old reports (future work)
