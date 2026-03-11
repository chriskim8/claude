# Story: Allow facility managers to map services to ADP pay codes

**Type:** Story
**Epic:** AMIONMGR-2950 — Integration ADP
**Priority:** P1
**Reporter:** Chris Kim
**Assignee:** [TBD]
**Sprint:** [TBD]
**Product Proposal:** https://docs.google.com/document/d/1hmMpysUfoBJX86-8AkueMm8I6uDHFqf-FZhy9BKef6Y

---

## Background / Context

For payroll reports to be accurate, each service a staff member works must be mapped to an ADP pay code. This is a facility-level configuration because services are organized at the facility level in Amion. This story adds a new Payroll / ADP section to the facility settings page, following the same pattern as the existing Epic service mappings. It depends on org-level pay codes being configured (Story 2) and ADP integration being enabled (Story 1).

Stored as `IntegrationLinkFacility` records (same model used for Epic service mappings).

- Source: [Product Proposal](https://docs.google.com/document/d/1hmMpysUfoBJX86-8AkueMm8I6uDHFqf-FZhy9BKef6Y) | [Technical Proposal](https://docs.google.com/document/d/1jYjJGDUFmPp57iTUHDjFWvfhH_DUEteSMF2Vtbx7evI)

---

## User Story

**As a** facility manager at an org with ADP payroll integration enabled
**I want** to map each service in my facility to an ADP pay code
**So that** staff hours logged against those services are correctly attributed to the right pay code in payroll reports

---

## Requirements

- A new "Payroll" (or "ADP") section appears in the facility-level Integrations settings page when ADP integration is enabled for the org
- The section lists all non-archived schedules, with services grouped under each schedule
- For each service, a facility manager can:
  - Select an org-level ADP pay code from a dropdown (populated from Story 2)
  - Clear/remove an existing mapping
- Mappings are stored as `IntegrationLinkFacility` records (service → pay code)
- Services without a pay code mapping are visually distinguished (e.g., "Unmapped" label) — these will be excluded from payroll reports and flagged
- Changes are saved immediately (no "Save" button needed per-row) or via a single Save action at the page level — confirm pattern with design

## Non-Functional Requirements

- **Performance**: Page should load within acceptable time even for facilities with many services (group by schedule to keep the list scannable)
- **Security**: Only facility managers (and above) for the given facility can access this page; org-level pay codes are read-only here
- **Accessibility**: Dropdowns must be keyboard accessible; unmapped services must have a visually and semantically distinct indicator
- **Scalability**: N/A — facility-level config, bounded scope
- **Reliability**: Saving a mapping must not affect other services; if a pay code is later removed from the org, existing mappings should be handled gracefully (flag rather than silently break)

---

## Designs

- **Figma:** https://www.figma.com/design/upJE6mbXBXFFftLTU65Fha/ADP?node-id=76-2252
- **Design notes:** The ADP section should follow the same structure as the Epic service mapping UI. Group services by schedule. Clearly distinguish mapped vs. unmapped services. Confirm whether changes auto-save or require an explicit save action.

---

## API Information

- `GET /facilities/:id/integrations/payroll/services` — returns list of non-archived schedules and services with current pay code mappings
- `PUT /facilities/:id/integrations/payroll/service_mappings` — creates or updates `IntegrationLinkFacility` records for service → pay code
- `DELETE /facilities/:id/integrations/payroll/service_mappings/:id` — removes a service → pay code mapping

---

## Technical Notes

This follows the existing `IntegrationLinkFacility` pattern used for Epic service mappings — confirm schema is reusable or if a separate table is needed for payroll mappings. Pay code dropdown should be scoped to the org's configured pay codes (from Story 2). When a pay code is selected, store the `paycode_id` reference on the `IntegrationLinkFacility` record.

Services with no mapping will be excluded from payroll report rows in Story 6 — ensure this exclusion logic is defined early so the report generation story can depend on it cleanly.

---

## Dox Analytics

- `adp_service_paycode_mapped` — fires when a facility manager maps a service to a pay code (include facility ID, service ID, paycode ID)
- `adp_service_paycode_cleared` — fires when a facility manager removes a mapping

---

## Acceptance Criteria

- [ ] Given an org has ADP integration enabled, when a facility manager navigates to the facility's Settings > Integrations page, then they see a "Payroll" or "ADP" section listing all non-archived schedules and their services
- [ ] Given a service has no pay code mapping, when the facility manager views the list, then that service is visually indicated as "Unmapped"
- [ ] Given a facility manager selects a pay code for a service, when the selection is saved, then the mapping is persisted and the service no longer shows as "Unmapped"
- [ ] Given a facility manager clears a service mapping, when the change is saved, then the `IntegrationLinkFacility` record is removed and the service returns to "Unmapped" state
- [ ] Given a non-facility-manager (e.g., Viewer) navigates to the facility settings page, when they view the Integrations section, then they cannot access or modify service → pay code mappings
- [ ] Given ADP integration is disabled for the org, when a facility manager views facility settings, then the Payroll / ADP section is not shown

**QA test case doc:** [TBD]

---

## Rollout & Sign-off

- **Feature flag required?** Yes — gated behind `adp_payroll_integration`
- **Timing constraints?** Depends on Story 1 (integration toggle) and Story 2 (pay codes ingested); should be built in parallel with Stories 2–3
- **Pre-deployment communication required?** CS team should know how to walk facility managers through this setup during onboarding
- **Special approvals required?** None

---

## Out of Scope

- Facility managers creating or editing org-level pay codes (read-only dropdown here; editing is future work)
- Archiving or bulk-managing service mappings
- Any service → pay code mapping at the org level (this is always facility-scoped)
