# Story: Support ingestion of CSV files for org-level payroll fields

**Type:** Story
**Epic:** AMIONMGR-2950 — Integration ADP
**Priority:** P1
**Reporter:** Chris Kim
**Assignee:** [TBD]
**Sprint:** [TBD]
**Product Proposal:** https://docs.google.com/document/d/1hmMpysUfoBJX86-8AkueMm8I6uDHFqf-FZhy9BKef6Y

---

## Background / Context

Before any payroll reports can be generated, an org needs three sets of payroll data configured at the org level: Agreement Types, Vendor IDs, and Pay Codes. In MVP, this is a concierge onboarding process — clients send CSVs to the biz team, and eng ingests them via scripts or SQL. There is no self-serve admin CRUD UI in this iteration (that's future work).

This story covers the data model and ingestion tooling that supports the three CSV file types. It is a dependency for Story 4 (service → pay code mapping) and Story 6 (report generation).

- Source: [Product Proposal](https://docs.google.com/document/d/1hmMpysUfoBJX86-8AkueMm8I6uDHFqf-FZhy9BKef6Y) | [Technical Proposal](https://docs.google.com/document/d/1jYjJGDUFmPp57iTUHDjFWvfhH_DUEteSMF2Vtbx7evI)

---

## User Story

**As a** member of the biz/eng team onboarding a client onto ADP payroll
**I want** to ingest org-level payroll configuration (Agreement Types, Vendor IDs, Pay Codes) via CSV files
**So that** the organization has the mappings required to generate accurate payroll reports

---

## Requirements

**Agreement Types CSV**
- Single required column: `Agreement Type` (varchar)
- Each row creates one org-level agreement type
- `Activations` is a system-default agreement type that is always present and cannot be edited or deleted
- Upsert key: Agreement Type name

**Vendor IDs CSV**
- Single required column: `Vendor ID` (varchar)
- Each row creates one org-level vendor ID record
- Upsert key: Vendor ID identifier

**Pay Codes CSV**
- Required columns: `Pay Code Name`, `Pay Code ID`, `Agreement Type`, `Cost Center ID`, `Amount (USD)`
- `Agreement Type` must reference an existing agreement type by name
- `Amount` must be a valid USD currency value
- Upsert key: Pay Code Name

**Validation (all CSVs)**
- Required columns must be present; missing columns reject the entire file with a clear error
- Rows with invalid data are rejected individually with an error summary (other valid rows can still be upserted)
- Agreement type reference in Pay Codes CSV must exist at time of import

## Non-Functional Requirements

- **Performance**: Ingestion scripts should handle up to ~50 pay codes and hundreds of vendor IDs without issue
- **Security**: Script-based access only — no public API endpoint for this in MVP; ensure org scoping on all records
- **Accessibility**: N/A — internal tooling only in MVP
- **Scalability**: Providence has ~125k caregivers; Vendor ID volume could be large — index accordingly
- **Reliability**: Upsert behavior must be idempotent — running the same CSV twice should not create duplicates

---

## Designs

- **Figma:** N/A — internal concierge tooling only in MVP; no UI exposed to customers
- **Design notes:** Future work will add self-serve CRUD UIs for these fields (see Future Work section in proposal)

---

## API Information

- No customer-facing API endpoints in MVP
- Internal scripts / rake tasks for ingestion
- Data model:
  - `agreement_types(organization_id, name varchar)` — upsert key: name per org
  - `vendor_ids(organization_id, identifier varchar)` — upsert key: identifier per org
  - `paycodes(organization_id, name varchar, identifier varchar, agreement_type_id bigint, cost_center_id varchar, amount decimal)` — upsert key: name per org

---

## Technical Notes

CSV ingestion follows a similar pattern to existing CSV import tooling in Amion. Confirm with eng whether existing ImportService patterns apply or if dedicated scripts are preferred for MVP. Upsert keys should prevent duplicate creation on re-runs. `Activations` agreement type should be seeded for all ADP-enabled orgs on integration creation (Story 1) — confirm it can be referenced but not modified.

Agreement type is referenced by name in the Pay Codes CSV (not by ID), so import order matters: Agreement Types must be ingested before Pay Codes.

---

## Dox Analytics

- N/A — internal tooling only in MVP; no user-facing events to track

---

## Acceptance Criteria

- [ ] Given a valid Agreement Types CSV is ingested for an org, when the import runs, then all agreement types are created or updated (upsert) and `Activations` remains as a non-editable system default
- [ ] Given a valid Vendor IDs CSV is ingested for an org, when the import runs, then all vendor IDs are created or updated with no duplicates
- [ ] Given a valid Pay Codes CSV is ingested, when the import runs, then pay codes are created or updated with all required fields (name, ID, agreement type, cost center, amount) correctly mapped
- [ ] Given a Pay Codes CSV row references an Agreement Type that does not exist, when the import runs, then that row is rejected with a clear error message and all other valid rows are still upserted
- [ ] Given a CSV with missing required columns is submitted, when the import runs, then the entire file is rejected with an error identifying the missing columns
- [ ] Given the same CSV is ingested twice, when the second import runs, then no duplicate records are created (idempotent upsert behavior)
- [ ] Given an org has the ADP integration enabled, when pay codes are ingested, then those pay codes are scoped only to that organization and not visible to other orgs

**QA test case doc:** [TBD]

---

## Rollout & Sign-off

- **Feature flag required?** Yes — gated behind `adp_payroll_integration` (same as Story 1)
- **Timing constraints?** Must be completed before Story 4 (service→paycode mapping) and Story 6 (report generation)
- **Pre-deployment communication required?** CS/biz team needs to know the CSV formats and the ingestion process before client onboarding begins — provide internal runbook
- **Special approvals required?** None

---

## Out of Scope

- Self-serve admin CRUD UI for Agreement Types, Vendor IDs, or Pay Codes (future work)
- Editing or archiving individual records via UI (future work)
- Approval workflows for data ingestion
- Staff-level payroll mapping (Vendor ID → staff) — covered in Story 3
