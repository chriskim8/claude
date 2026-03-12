# Hours vs Units: Design Clarification

**Status:** Response to Ben's Question on Story 6 (ADP Reports Page)
**Date:** 2026-03-12
**Related Stories:** Story 5 (Activation Request Type), Story 6 (ADP Reports Page), Story 7 (CSV Export)

---

## Ben's Question

> "If someone works an 8 hour shift, and is activated for 1 unit, am I summing these to be 9? Then multiplying by pay code? I feel like we are working with apples and oranges. How do I translate between units <-> hours?"

---

## The Answer: Hours and Units Should **NOT** Be Mixed

**The correct design:** Hours and Units are tracked **separately** and should **never be summed together** on the same payroll row.

### Key Principle

In the ADP payroll model:
- **Hours** = time tracked on scheduled assignments (shifts, blocks, etc.)
- **Units** = count of discrete activations (when a staff member is called in)

These are **two different agreement types** / **pay codes**. A staff member earning "regular shift pay" (hours) is on a different pay code than one earning "activation pay" (units).

### Correct Example

A provider works an 8-hour shift AND gets called in once during a given pay period:

| Staff | Pay Code | Agreement Type | Hours / Units | Pay Code Rate | Amount |
|-------|----------|----------------|---------------|---------------|--------|
| Jane Doe | SHIFT | Regular | 8 | $25/hr | $200 |
| Jane Doe | ACTIVATION | Activation | 1 | $50/unit | $50 |
| **TOTAL** | | | | | **$250** |

**NOT THIS:**
| Staff | Pay Code | Hours / Units | Amount |
|-------|----------|---------------|--------|
| Jane Doe | SHIFT/ACTIVATION | 9 | ??? |

### Why This Works

The aggregation logic in Story 6 groups by: **Staff → Agreement Type → Pay Code**

This means:
1. The same staff member can appear on **multiple rows** in the report (one per pay code / agreement type)
2. Each row aggregates **only one type of unit** (either hours from assignments, or count from activations)
3. The Amount calculation is clean: `Amount = Hours/Units × PayCodeRate`

---

## Translation Between Hours and Units

There is **no direct translation** (e.g., "1 unit = X hours"). They are:
- **Tracked independently** — assignments generate hours, activations generate units
- **Paid independently** — each via its own pay code with its own rate
- **Grouped independently** — aggregated by pay code / agreement type

The "translation" is simply: **different pay codes, different rates.**

---

## Report Row Structure (Detailed)

From Story 6, the report aggregation groups by:
```
staff_id → agreement_type → pay_code
```

For each group, the report:
1. **Sums** the hours (if all records are assignments)
2. **Counts** the activations (if all records are activations)
3. **Multiplies** by the pay code rate to get the Amount

**Result:** One row per unique (staff, agreement type, pay code) combination.

### Example Payroll Report

```
Vendor ID | Name | Agreement Type | Pay Code | Hours/Units | Rate | Amount
123       | Jane | Regular        | SHIFT    | 8           | $25  | $200
123       | Jane | Activation     | CALL_IN  | 1           | $50  | $50
124       | Bob  | Regular        | SHIFT    | 12          | $25  | $300
124       | Bob  | On-Call        | ONCALL   | 40          | $5   | $200
```

Each row is independent and pays out separately.

---

## Implementation Notes

### Aggregation Query (Story 6)

The report query must:
1. **Query assignments** → sum hours grouped by (staff_id, service, agreement_type)
2. **Query activations** → count rows grouped by (staff_id, paycode, agreement_type)
3. **Join** each group to its pay code and rate
4. **Calculate** Amount = Hours/Units × PayCodeRate
5. **Union** the two result sets (assignments + activations)

The key is: assignments and activations are **separate queries that are unioned**, not joined/summed together.

### CSV Export (Story 7)

The "Hours / Units" column shows:
- **For assignment rows:** actual hours (e.g., "8")
- **For activation rows:** unit count (e.g., "1")

Both are multiplied by their respective pay code rates. No mixing.

---

## Edge Cases Addressed

| Scenario | Handling |
|----------|----------|
| Staff has both regular hours and activations in same pay period | **Two rows** — one per agreement type |
| Staff works 8 hours on SHIFT and gets 1 activation on CALL_IN | **Two rows** — different pay codes, independent amounts |
| Staff has 5 activations on CALL_IN | **One row** — Units = 5, Amount = 5 × Rate |
| Service mapped to SHIFT code but staff member also has ACTIVATION code | **Separate rows** — each pays independently |
| Staff has no Vendor ID or service has no pay code | **Flagged/excluded** — not included in report (Story 6, AC 5) |

---

## Design Summary

✅ **Correct:** Group by pay code → aggregate hours OR units separately → multiply by rate
❌ **Incorrect:** Sum hours + units on same row → multiply by single rate

The "apples and oranges" concern is **addressed by grouping** — each row is homogeneous (all hours, or all units), so multiplication by pay code rate is unambiguous.

---

## Acceptance Criteria (Story 6 & 7) That Enforce This

**Story 6, AC 4:**
> "Given a report is generated, when it loads, then the index table shows rows grouped by staff → agreement type → pay code..."

**Story 7, AC 3:**
> "Given the downloaded CSV, when it contains activation data, then activation rows show the unit count (not hours) in the Hours/Units column..."

These ACs enforce the separation — activations show units, assignments show hours, never mixed on the same row.

---

## Questions for Ben (If Needed)

1. Is the grouping logic (staff → agreement type → pay code) clear?
2. Should the report UI show a visual grouping or hierarchy for the same staff across multiple pay codes?
3. Is the "one row per pay code" model acceptable for the MVP, or do you need aggregation at a higher level?

---

## Next Steps

1. **Confirm** this design aligns with ADP's payroll input format (Nov 2025 Providence meeting specs)
2. **Update** Story 6 acceptance criteria if any grouping logic needs clarification
3. **Implement** the aggregation query to separate assignments and activations
4. **Test** with example data: staff with mixed hours + activations
