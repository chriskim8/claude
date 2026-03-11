# Story: Doxers can enable ADP payroll integration for an organization

**Type:** Story
**Epic:** AMIONMGR-2950 — Integration ADP
**Priority:** P1
**Reporter:** Chris Kim
**Assignee:** [TBD]
**Sprint:** [TBD]
**Product Proposal:** https://docs.google.com/document/d/1hmMpysUfoBJX86-8AkueMm8I6uDHFqf-FZhy9BKef6Y

---

## Background / Context

Amion supports on-call scheduling for enterprise healthcare organizations. On-call work directly drives payroll — particularly when staff are called in during on-call shifts and earn activation-based compensation. Clients like Providence are currently blocked from migrating to Amion Next because there is no payroll integration. This story is the gate that unlocks all downstream payroll features for a given org.

Follows the convention of the existing Epic vendor integration toggle pattern.

- Source: [Product Proposal — Payroll Integration for Amion Next (ADP)](https://docs.google.com/document/d/1hmMpysUfoBJX86-8AkueMm8I6uDHFqf-FZhy9BKef6Y) | [Technical Proposal — ADP](https://docs.google.com/document/d/1jYjJGDUFmPp57iTUHDjFWvfhH_DUEteSMF2Vtbx7evI)

---

## User Story

**As a** Doxer (anyone with an @doximity.com or @amion.com email)
**I want** to enable ADP payroll integration for an organization from its settings
**So that** the org's managers can configure payroll mappings, staff can log activations, and schedule managers can generate payroll reports

---

## Requirements

- An "ADP" toggle is exposed in the Integrations section of the Organization Settings page
- This toggle is only visible and actionable by Doxers (internal accounts) — not org admins or managers
- Enabling the toggle creates an integration record of type `Payroll` for that organization
- A policy backed by this record controls access to all downstream payroll features:
  - Facility-level settings page for service → pay code mapping
  - Schedule-level "ADP Reports" page
  - Viewer-side "My Schedule" Activation request type
- Disabling the toggle removes access to all downstream payroll features (non-destructive — data should be preserved)

## Non-Functional Requirements

- **Performance**: Toggle state change should be reflected immediately (no page reload required)
- **Security**: Restricted to Doxer accounts only — enforce at policy layer, not just UI
- **Accessibility**: Toggle must be keyboard-accessible and have clear on/off label state
- **Scalability**: N/A — this is a per-org config record
- **Reliability**: If the integration record creation fails, the UI should surface a clear error and not leave the org in a partially-enabled state

---

## Designs

- **Figma:** https://www.figma.com/design/upJE6mbXBXFFftLTU65Fha/ADP?node-id=76-2252
- **Design notes:** Should visually match the existing Epic vendor integration toggle in the Integrations section. Label: "ADP Payroll Integration." Include a brief description of what enabling it unlocks.

---

## API Information

- `POST /organizations/:id/integrations` — creates integration record of type `Payroll`
- `DELETE /organizations/:id/integrations/:integration_id` — disables integration (soft delete or status change, data preserved)
- Policy check: `payroll_integration_enabled?` on the organization — gates all downstream features

---

## Technical Notes

The integration record pattern mirrors the existing Epic integration. Confirm with eng whether a new integration type needs to be registered or if the existing type system supports `Payroll` already. The policy should be checked at the controller and/or frontend route level for each downstream feature (facility payroll settings, reports page, activation request type).

---

## Dox Analytics

- `adp_integration_enabled` — fires when a Doxer toggles ADP integration on for an org (include org ID)
- `adp_integration_disabled` — fires when a Doxer toggles ADP integration off for an org (include org ID)

---

## Acceptance Criteria

- [ ] Given a Doxer is viewing an organization's Settings > Integrations page, when ADP payroll integration is not yet enabled, then they see an "ADP Payroll Integration" toggle in the off state
- [ ] Given a Doxer enables the ADP toggle, when the change is saved, then an integration record of type `Payroll` is created for the org and all downstream payroll features become accessible to the appropriate roles
- [ ] Given the ADP toggle is enabled, when a non-Doxer (org Manager or Viewer) navigates to Organization Settings, then they do not see the ADP toggle or the ability to change the integration state
- [ ] Given the ADP toggle is enabled, when a Doxer disables it, then downstream payroll features are hidden and the existing payroll data is preserved (not deleted)
- [ ] Given the integration record creation fails, when the Doxer tries to enable the toggle, then a clear error message is shown and the toggle remains in the off state

**QA test case doc:** [TBD]

---

## Rollout & Sign-off

- **Feature flag required?** Yes
  - Flag name: `adp_payroll_integration`
- **Timing constraints?** Must be shipped before other ADP stories — this is the gate for all downstream features
- **Pre-deployment communication required?** Notify CS team before enabling for any org — concierge onboarding flow begins here
- **Special approvals required?** None

---

## Out of Scope

- Self-serve enabling by org admins or managers (Doxer-only in MVP)
- Any UI for org-admins to configure payroll mappings directly (covered in future work — CRUD stories)
- Approval workflow configuration per schedule (future work)
