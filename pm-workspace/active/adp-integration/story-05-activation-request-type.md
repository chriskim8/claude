# Story: Allow providers to log activations as a new request type

**Type:** Story
**Epic:** AMIONMGR-2950 — Integration ADP
**Priority:** P1
**Reporter:** Chris Kim
**Assignee:** [TBD]
**Sprint:** [TBD]
**Product Proposal:** https://docs.google.com/document/d/1hmMpysUfoBJX86-8AkueMm8I6uDHFqf-FZhy9BKef6Y

---

## Background / Context

In healthcare on-call scheduling, an "activation" is when a staff member is called in during an on-call shift and earns activation-based compensation. This is distinct from their regular scheduled hours. Currently, Amion has no way for staff to record these events — they happen outside the system. This story adds an "Activation" request type to the Viewer-side "My Schedule" page, allowing staff to log when they are called in. These records feed directly into payroll report generation (Story 6).

MVP: activations are auto-approved (no approval workflow in this iteration). One activation per staff member per day per service.

- Source: [Product Proposal](https://docs.google.com/document/d/1hmMpysUfoBJX86-8AkueMm8I6uDHFqf-FZhy9BKef6Y) | [Technical Proposal](https://docs.google.com/document/d/1jYjJGDUFmPp57iTUHDjFWvfhH_DUEteSMF2Vtbx7evI)

---

## User Story

**As a** provider (Viewer) at an org with ADP payroll integration enabled
**I want** to log an activation when I am called in during an on-call shift
**So that** my activation-based compensation is captured and included in the payroll report for my pay period

---

## Requirements

- When ADP integration is enabled for the org, the "New Request" flow on My Schedule exposes a new request type: **Activation**
- Required fields for an Activation request:
  - **Activation date** (required)
  - **Pay code** (required — dropdown populated from org-level pay codes with agreement type = Activations)
- Activation requests are stored as `StaffRequest` records — no assignment record is generated
- Activations are **auto-approved** in MVP (no staff or admin sign-off required)
- A staff member may have at most one activation per day per service/pay code combination — enforce on submission
- Activations appear in the staff member's view of My Schedule (either as entries or in a separate list — confirm with design)
- Activations feed into the payroll report data layer in Story 6 as activation units (count, not hours)

## Non-Functional Requirements

- **Performance**: Request submission should be near-instant; form should load pay codes without noticeable delay
- **Security**: Only the logged-in staff member can create activations on their own behalf; org and payroll integration policy must be active
- **Accessibility**: Form must be keyboard accessible; pay code dropdown must include clear labels
- **Scalability**: N/A — one activation per staff per day per pay code; bounded volume
- **Reliability**: Duplicate submission (same date + pay code) should be blocked gracefully with a clear message, not silently ignored

---

## Designs

- **Figma:** https://www.figma.com/design/upJE6mbXBXFFftLTU65Fha/ADP?node-id=76-2252
- **Design notes:** Activation should be a selectable type alongside existing request types (e.g., Time Off). Form is minimal: date picker + pay code dropdown. Confirm how submitted activations appear in My Schedule (e.g., listed as a row with type "Activation," date, pay code). Consider empty state for orgs where ADP is not enabled (option should not appear).

---

## API Information

- `GET /organizations/:id/paycodes?agreement_type=activations` — returns pay codes with the Activations agreement type for the dropdown
- `POST /staff_requests` — creates an Activation `StaffRequest` record with type=activation, date, paycode_id
- `GET /my_schedule/requests?type=activation` — returns the staff member's submitted activations for display in My Schedule

---

## Technical Notes

Activations are stored as `StaffRequest` records (no assignment record generated — this is intentional for MVP; activations represent unscheduled callouts, not schedule changes). The auto-approval behavior means no approval queue is needed in MVP. When report generation queries activations (Story 6), it should query auto-approved `StaffRequest` records of type activation within the pay period.

One activation per staff/day/pay code constraint: implement as a uniqueness validation on `StaffRequest` for (staff_id, date, paycode_id, type=activation).

Future work: optional comment field, approval workflow, and scheduler visibility in Tasks page.

---

## Dox Analytics

- `adp_activation_request_started` — fires when a Viewer opens the Activation request form
- `adp_activation_request_submitted` — fires on successful activation submission (include org ID, paycode ID, date)
- `adp_activation_request_duplicate_blocked` — fires when submission is blocked by duplicate validation

---

## Acceptance Criteria

- [ ] Given a Viewer's org has ADP integration enabled, when they tap "New Request" on My Schedule, then "Activation" appears as a request type option
- [ ] Given a Viewer selects the Activation request type, when the form loads, then it displays a required date picker and a required pay code dropdown containing only pay codes with the Activations agreement type
- [ ] Given a Viewer submits a valid Activation request, when the submission is processed, then a `StaffRequest` record is created with type=activation, is auto-approved, and the activation appears in their My Schedule view
- [ ] Given a Viewer attempts to submit a duplicate activation (same date + pay code), when they submit the form, then submission is blocked with a clear error message and no duplicate record is created
- [ ] Given a Viewer's org does not have ADP integration enabled, when they open the "New Request" flow, then the Activation option is not shown
- [ ] Given a Viewer submits an Activation, when the payroll report is generated for that pay period (Story 6), then the activation appears as a unit (count = 1) in the report under the correct pay code and staff member

**QA test case doc:** [TBD]

---

## Rollout & Sign-off

- **Feature flag required?** Yes — gated behind `adp_payroll_integration`
- **Timing constraints?** Must be completed before Story 6 (reports); activations are part of the report data layer
- **Pre-deployment communication required?** Staff at onboarded orgs need to know how to log activations — CS should include in onboarding materials
- **Special approvals required?** None

---

## Out of Scope

- Optional comment field on Activation request (future work)
- Approval workflow for activations — auto-approved in MVP (future work)
- Scheduler visibility of submitted activations in the Tasks page (future work)
- Notification emails for activation submissions (future work)
- Activation via external webhook (e.g., paging system integration) — future work
