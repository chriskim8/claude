# Story: Extend staff CSV import to support ADP payroll fields

**Type:** Story
**Epic:** AMIONMGR-2950 — Integration ADP
**Priority:** P1
**Reporter:** Chris Kim
**Assignee:** [TBD]
**Sprint:** [TBD]
**Product Proposal:** https://docs.google.com/document/d/1hmMpysUfoBJX86-8AkueMm8I6uDHFqf-FZhy9BKef6Y

---

## Background / Context

Each staff member needs to be linked to their ADP payroll identity before they can appear in payroll reports. This is done via two fields: Vendor ID (their payroll identifier in ADP) and Remit To (their payroll routing destination). These fields already exist in the data model (backed by `StaffIntegration` records) from prior Epic integration work. This story extends the existing staff CSV import/export workflow to include these fields, enabling bulk setup as part of concierge onboarding.

Staff payroll fields are displayed as a read-only "Payroll info" section on staff profiles when the ADP integration is enabled.

- Source: [Product Proposal](https://docs.google.com/document/d/1hmMpysUfoBJX86-8AkueMm8I6uDHFqf-FZhy9BKef6Y) | [Technical Proposal](https://docs.google.com/document/d/1jYjJGDUFmPp57iTUHDjFWvfhH_DUEteSMF2Vtbx7evI)

---

## User Story

**As an** org manager or biz team member onboarding staff onto ADP payroll
**I want** to assign Vendor IDs and Remit To values to staff via the existing staff CSV workflow
**So that** each staff member is correctly mapped for payroll report generation without requiring manual one-by-one updates

---

## Requirements

**CSV Export (when ADP integration is enabled for the org):**
- The staff member CSV export includes two new columns to the right of any existing Epic integration columns:
  - `Vendor ID`
  - `Remit To`
- If a staff member already has payroll records, the exported values are pre-populated
- If no payroll record exists, the columns are present but empty

**CSV Import:**
- When both `Vendor ID` and `Remit To` columns are provided and populated for a row, create or update the staff member's `StaffIntegration` payroll record
- If only one of the two columns is provided for a row, skip that row and flag it as an error in the validation summary — do not partially update
- Vendor ID uses find-by-name matching against the org's configured vendor IDs (from Story 2)
- Import is additive — existing staff data is not affected beyond the payroll fields

**Staff Profile (read-only display):**
- When ADP integration is enabled, a read-only "Payroll info" section appears on the staff profile / org staff form
- Displays: Vendor ID, Remit To
- Not editable via the UI in MVP (self-serve staff edit is future work)

## Non-Functional Requirements

- **Performance**: Bulk import should handle orgs with large staff lists (Providence: ~125k caregivers) — async processing if needed
- **Security**: Payroll fields are only visible when ADP integration policy is active for that org; staff cannot view or edit their own payroll fields in MVP
- **Accessibility**: Read-only "Payroll info" section on staff profile must be screen reader accessible
- **Scalability**: Vendor ID matching logic must be efficient at scale — avoid N+1 queries on large imports
- **Reliability**: Import must be atomic per row — a failure on one row does not roll back other rows

---

## Designs

- **Figma:** https://www.figma.com/design/upJE6mbXBXFFftLTU65Fha/ADP?node-id=76-2252
- **Design notes:** The Payroll info section should only appear when the org's ADP integration is enabled. Position: below Epic integration fields if present. Read-only state in MVP.

---

## API Information

- Extends existing staff CSV import/export controller
- `StaffIntegration` records — two records per staff member per ADP mapping: one for Vendor ID, one for Remit To
- Vendor ID matching: find by `identifier` within the org's configured vendor IDs

---

## Technical Notes

This story leverages the existing Epic integration `StaffIntegration` record pattern — confirm the data model can accommodate a second integration type (Payroll) alongside Epic without conflicts. The import CSV column names (`Vendor ID`, `Remit To`) should match what clients will send — align with the ADP specs from the Providence meeting (Nov 2025). Find-by-name matching for Vendor ID means the org-level Vendor IDs from Story 2 must be ingested first.

---

## Dox Analytics

- `adp_staff_payroll_csv_import_started` — fires when a CSV import containing payroll columns is initiated
- `adp_staff_payroll_csv_import_completed` — fires on completion; include count of rows updated and count of rows skipped/errored

---

## Acceptance Criteria

- [ ] Given an org has ADP integration enabled, when a manager exports the staff CSV, then the file includes `Vendor ID` and `Remit To` columns to the right of Epic fields, with existing payroll values pre-populated where applicable
- [ ] Given a staff CSV with both `Vendor ID` and `Remit To` populated for a row, when the import is processed, then the staff member's payroll `StaffIntegration` records are created or updated correctly
- [ ] Given a staff CSV row with only one of `Vendor ID` or `Remit To` provided, when the import is processed, then that row is skipped and flagged in the validation summary with a clear error; the staff member's existing data is not changed
- [ ] Given a `Vendor ID` value in the CSV that does not match any org-level vendor ID, when the import is processed, then that row is flagged as an error with a message identifying the unrecognized value
- [ ] Given an org manager views a staff profile when ADP integration is enabled, when the profile page loads, then a read-only "Payroll info" section displays the staff member's Vendor ID and Remit To (or empty if not yet mapped)
- [ ] Given an org does not have ADP integration enabled, when a manager exports the staff CSV, then no payroll columns are present in the export

**QA test case doc:** [TBD]

---

## Rollout & Sign-off

- **Feature flag required?** Yes — gated behind `adp_payroll_integration`
- **Timing constraints?** Should be completed alongside Story 2; both are part of concierge onboarding setup
- **Pre-deployment communication required?** CS team needs updated CSV template with payroll columns to share with clients; provide internal runbook
- **Special approvals required?** None

---

## Out of Scope

- Staff self-editing their own Vendor ID or Remit To (future work)
- Any UI for one-off manual edits to payroll fields (future work)
- Approval workflows for payroll field changes
