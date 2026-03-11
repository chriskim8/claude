-- Residency Tier 1: Find schedule-level access codes for residency schedules
-- within each license. Viewer codes below are the license-level access codes
-- from client-profiles.md. We want the account-level access code for the
-- specific sub-account whose schedule has residency = true.
--
-- Access code format (mirrors Account#internal_clinician_access_code):
--   - If group_access_code present:  "<license_code> <group_access_code>"
--   - Otherwise:                     "<license_code> .<account_number>."
--   - Base account (account_number=0) with residency schedule: just "<license_code>"

SELECT
  ac.code                        AS license_viewer_code,
  a.amionc_reference_id,
  a.amionc_account_number,
  a.group_name,
  a.group_access_code,
  s.name                         AS schedule_name,
  CASE
    WHEN a.amionc_account_number = 0
      THEN ac.code
    WHEN a.group_access_code IS NOT NULL AND a.group_access_code <> ''
      THEN ac.code || ' ' || a.group_access_code
    ELSE
      ac.code || ' .' || a.amionc_account_number || '.'
  END                            AS internal_clinician_access_code

FROM PRODUCTION.DUMP_AMION_APP.ACCESS_CODES ac

-- Join accounts on shared amionc_reference_id (license identifier)
JOIN PRODUCTION.DUMP_AMION_APP.ACCOUNTS a
  ON  a.amionc_reference_id = ac.amionc_reference_id
  AND a.deleted = false

-- Join through the join table to get the schedule
JOIN PRODUCTION.DUMP_AMION_APP.ACCOUNTS_SCHEDULES acs ON acs.account_id = a.id
JOIN PRODUCTION.DUMP_AMION_APP.SCHEDULES s
  ON  s.id = acs.schedule_id
  AND s.residency = true

WHERE ac.code IN (
  'new_56844',  -- Baystate Psychiatric Residency
  'new_56496',  -- WCCHC Psychiatric Residency
  'englewood',  -- Englewood FM Residency (already in Next)
  'vaphs',      -- VA Pittsburgh FM Residency
  'SLVHCS',     -- SE Louisiana VA FM Residency
  'VAPSHCS'     -- VA Puget Sound FM Residency
)
AND ac.admin = false

ORDER BY ac.code, a.amionc_account_number;
