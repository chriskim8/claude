# Before: Clinic Template Expansion — UX Prototype

Source: /Users/chriskim/pm-workspace/active/clinic-ux-prototype/index.html

---

<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Clinic Template UX — AMIONMGR-3306</title>
<link rel="stylesheet" href="../../assets/dox-prototype.css">
<style>
/* ── Prototype nav ── */
.proto-nav { background: var(--dox-white); border-bottom: var(--dox-border); display: flex; padding: 0 var(--dox-spacing-lg); position: sticky; top: 60px; z-index: 100; }
.screen { display: none; }
.screen.is-active { display: block; }

/* ── Day-pill grid ── */
.day-pills { display: flex; gap: 6px; flex-wrap: wrap; }
.day-pill {
  width: 42px; height: 42px;
  border-radius: var(--dox-radius-md);
  border: var(--dox-border);
  background: var(--dox-white);
  font-size: var(--dox-font-size-sm);
  font-weight: var(--dox-font-weight-medium);
  color: var(--dox-color-body-font);
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: background 0.1s, border-color 0.1s, color 0.1s;
  font-family: var(--dox-font-family);
}
.day-pill.is-selected {
  background: var(--dox-color-primary);
  border-color: var(--dox-color-primary);
  color: var(--dox-white);
}
.day-pill:hover:not(.is-selected) { border-color: var(--dox-color-primary); color: var(--dox-color-primary); }

/* ── Number stepper (reference screen only) ── */
.stepper { display: flex; align-items: center; gap: 0; }
.stepper__input {
  width: 52px; height: var(--dox-control-height-md);
  border: var(--dox-border); border-radius: var(--dox-radius-md) 0 0 var(--dox-radius-md);
  font-size: var(--dox-font-size-sm); text-align: center;
  color: var(--dox-color-body-font); font-family: var(--dox-font-family);
  border-right: none; padding: 0 8px;
}
.stepper__input:focus { outline: none; }
.stepper__buttons { display: flex; flex-direction: column; }
.stepper__btn {
  width: 26px; height: 18px; border: var(--dox-border); background: var(--dox-gray-100);
  cursor: pointer; font-size: 10px; display: flex; align-items: center; justify-content: center;
  color: var(--dox-gray-700); font-family: var(--dox-font-family);
}
.stepper__btn:first-child { border-radius: 0 var(--dox-radius-md) 0 0; }
.stepper__btn:last-child  { border-radius: 0 0 var(--dox-radius-md) 0; border-top: none; }
.stepper__btn:hover { background: var(--dox-gray-200); }

/* ── Scope selector (Apply to — moved to top) ── */
.scope-selector { display: flex; gap: 0; border: var(--dox-border); border-radius: var(--dox-radius-md); overflow: hidden; }
.scope-btn {
  flex: 1; padding: 7px 10px; font-size: var(--dox-font-size-xs);
  font-family: var(--dox-font-family); cursor: pointer; border: none;
  background: var(--dox-gray-100); color: var(--dox-color-muted);
  border-right: var(--dox-border); transition: background 0.1s, color 0.1s;
  text-align: left; line-height: 1.35;
}
.scope-btn:last-child { border-right: none; }
.scope-btn.is-active { background: var(--dox-white); color: var(--dox-color-body-font); font-weight: var(--dox-font-weight-medium); }
.scope-btn:hover:not(.is-active) { background: var(--dox-gray-200); }
.scope-btn .sub { display: block; font-size: 10px; color: var(--dox-color-muted); font-weight: normal; }
.scope-btn.is-active .sub { color: var(--dox-color-primary); }

/* ── 4-week cycle table ── */
.cycle-table { width: 100%; border: var(--dox-border); border-radius: var(--dox-radius-md); overflow: hidden; }
.cycle-table__head {
  display: grid; grid-template-columns: 100px repeat(5, 1fr);
  background: var(--dox-gray-100); border-bottom: var(--dox-border);
}
.cycle-table__head-cell {
  padding: 6px 4px; font-size: 11px; font-weight: 600;
  color: var(--dox-gray-500); text-align: center;
  text-transform: uppercase; letter-spacing: 0.04em;
}
.cycle-table__head-cell:first-child { text-align: left; padding-left: 10px; }
.cycle-table__row { display: grid; grid-template-columns: 100px repeat(5, 1fr); border-bottom: var(--dox-border); }
.cycle-table__row:last-child { border-bottom: none; }
.cycle-table__week {
  padding: 8px 10px; font-size: var(--dox-font-size-sm);
  font-weight: var(--dox-font-weight-medium); color: var(--dox-color-body-font);
  border-right: var(--dox-border); display: flex; flex-direction: column;
  justify-content: center; gap: 1px;
}
.cycle-table__week span { font-size: 10px; color: var(--dox-color-muted); font-weight: normal; }
.cycle-cell {
  border-right: 1px solid var(--dox-gray-200); min-height: 44px;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: background 0.1s; position: relative;
}
.cycle-cell:last-child { border-right: none; }
.cycle-cell:hover:not(.is-on) { background: var(--dox-color-primary-light); }
.cycle-cell.is-on { background: var(--dox-color-primary); }
.cycle-cell.is-on::after { content: '●'; color: white; font-size: 15px; }
.cycle-cell:not(.is-on):hover::after { content: '○'; color: var(--dox-color-primary); font-size: 14px; opacity: 0.6; }

/* ── Session summary ── */
.session-summary {
  background: var(--dox-color-primary-light); border: 1px solid var(--dox-color-primary);
  border-radius: var(--dox-radius-md); padding: 8px 12px;
  font-size: var(--dox-font-size-sm); color: var(--dox-color-primary-dark);
}

/* ── NEW annotation ── */
.is-new {
  outline: 2px solid var(--dox-color-primary);
  outline-offset: 2px; border-radius: var(--dox-radius-md); position: relative;
}
.is-new::after {
  content: 'NEW';
  position: absolute; top: -9px; right: -1px;
  background: var(--dox-color-primary); color: white;
  font-size: 9px; font-weight: 700; padding: 1px 5px;
  border-radius: 2px; letter-spacing: 0.06em;
}

/* ── calendar cells ── */
.cal-wrap { background: var(--dox-white); border: var(--dox-border); border-radius: var(--dox-radius-lg); overflow: hidden; }
.cal-grid { display: grid; grid-template-columns: 150px repeat(5, 1fr); }
.cal-th { background: var(--dox-gray-100); border-bottom: var(--dox-border); border-right: var(--dox-border); padding: 6px 8px; font-size: 11px; font-weight: 600; color: var(--dox-gray-500); text-transform: uppercase; letter-spacing: 0.04em; text-align: center; }
.cal-th.name-col { text-align: left; }
.cal-name { padding: 0 10px; border-bottom: 1px solid var(--dox-gray-200); border-right: var(--dox-border); font-size: var(--dox-font-size-sm); color: #0891b2; font-weight: 500; display: flex; align-items: center; min-height: 40px; }
.cal-cell { border-bottom: 1px solid var(--dox-gray-200); border-right: var(--dox-border); padding: 3px 4px; min-height: 40px; display: flex; flex-wrap: wrap; gap: 2px; align-content: center; position: relative; cursor: pointer; }
.cal-cell:hover { background: var(--dox-color-primary-light); }
.cal-cell:hover .add-hint { opacity: 1; }
.add-hint { opacity: 0; position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; }
.add-hint span { background: var(--dox-white); border: 1px dashed var(--dox-color-primary); border-radius: var(--dox-radius-sm); padding: 2px 7px; font-size: 11px; color: var(--dox-color-primary); font-weight: 500; }
.sched-chip { display: inline-flex; align-items: center; padding: 2px 5px; border-radius: var(--dox-radius-sm); font-size: 11px; font-weight: 500; white-space: nowrap; }
.ch-am   { background: #dbeafe; color: #1e40af; }
.ch-pm   { background: #fce7f3; color: #9d174d; }
.ch-call { background: var(--dox-color-warning-light); color: var(--dox-color-warning-dark); }
.ch-cancel { background: var(--dox-gray-200); color: var(--dox-gray-500); text-decoration: line-through; }
.ch-amber  { background: var(--dox-color-warning-light); color: var(--dox-color-warning-dark); border: 1px dashed var(--dox-color-warning-dark); }
</style>
</head>
<body>

<!-- Amion header -->
<header class="amion-header">
  <span class="amion-header__logo">AM<span class="highlight">i</span>ON</span>
  <div class="amion-header__divider"></div>
  <button class="amion-header__tab">Schedule: Block</button>
  <button class="amion-header__tab is-active">Schedule: Clinic</button>
  <button class="amion-header__tab">Settings</button>
  <button class="amion-header__tab">Stats</button>
  <span class="amion-header__badge">Prototype — AMIONMGR-3306</span>
</header>

<!-- Prototype nav -->
<nav class="proto-nav">
  <button class="dox-tab proto-tab is-active" onclick="showScreen('existing', this)">Existing Pattern</button>
  <button class="dox-tab proto-tab" onclick="showScreen('weekly', this)">Revised — Weekly <span class="dox-tab__badge">Proposal</span></button>
  <button class="dox-tab proto-tab" onclick="showScreen('fourweek', this)">Revised — 4-Week Cadence <span class="dox-tab__badge">Proposal</span></button>
  <button class="dox-tab proto-tab" onclick="showScreen('cancel', this)">Cancel States</button>
</nav>


<!-- ════════════════════════════════════════
     SCREEN 1 — Existing Repeat Assignments (reference)
════════════════════════════════════════ -->
<div id="sc-existing" class="screen is-active">
  <div class="dox-content" style="max-width:700px">
    <div class="dox-alert dox-alert--info" style="margin-bottom:var(--dox-spacing-lg)">
      <strong>Reference — existing Repeat Assignments modal.</strong> Current pattern for repeating block/call/shift assignments. The clinic extension reuses this exact structure with the minimum necessary additions — no new screens.
    </div>

    <div class="dox-card" style="max-width:420px">
      <div class="dox-modal__header" style="padding:var(--dox-spacing-lg);border-bottom:var(--dox-border);display:flex;align-items:flex-start;justify-content:space-between">
        <h5 class="dox-modal__title">Repeat Assignments for Jake Khan on Long Call</h5>
        <button class="dox-modal__close">×</button>
      </div>
      <div class="dox-modal__body">

        <!-- Repeat Every -->
        <div class="dox-form-group">
          <label class="dox-label">Repeat Every</label>
          <div class="dox-row dox-row--sm">
            <div class="stepper">
              <input type="text" class="stepper__input" value="1">
              <div class="stepper__buttons">
                <button class="stepper__btn">+</button>
                <button class="stepper__btn">−</button>
              </div>
            </div>
            <select class="dox-select" style="width:auto">
              <option>week</option>
              <option>2 weeks</option>
              <option>4 weeks</option>
              <option>month</option>
            </select>
          </div>
        </div>

        <!-- Repeat On -->
        <div class="dox-form-group">
          <label class="dox-label">Repeat On</label>
          <div class="day-pills">
            <button class="day-pill">Su</button>
            <button class="day-pill">Mo</button>
            <button class="day-pill">Tu</button>
            <button class="day-pill">We</button>
            <button class="day-pill is-selected">Th</button>
            <button class="day-pill">Fr</button>
            <button class="day-pill">Sa</button>
          </div>
        </div>

        <!-- Ends -->
        <div class="dox-form-group">
          <label class="dox-label">Ends</label>
          <div class="dox-stack dox-stack--xs">
            <label class="dox-check"><input type="radio" name="ends-ref" checked> After 1 Year</label>
            <label class="dox-check"><input type="radio" name="ends-ref">
              On
              <input type="date" class="dox-input" value="2026-06-19" style="width:auto;margin-left:6px">
            </label>
            <label class="dox-check"><input type="radio" name="ends-ref">
              After
              <div class="stepper" style="margin:0 4px">
                <input type="text" class="stepper__input" value="1">
                <div class="stepper__buttons"><button class="stepper__btn">+</button><button class="stepper__btn">−</button></div>
              </div>
              times
            </label>
          </div>
        </div>

        <!-- Override -->
        <div class="dox-form-group" style="margin-bottom:0">
          <label class="dox-check"><input type="checkbox"> Override Existing Assignments</label>
        </div>
      </div>
      <div class="dox-modal__footer">
        <button class="dox-btn dox-btn--ghost">Cancel</button>
        <button class="dox-btn dox-btn--primary">Apply</button>
      </div>
    </div>
  </div>
</div>


<!-- ════════════════════════════════════════
     SCREEN 2 — Revised: Weekly cadence
════════════════════════════════════════ -->
<div id="sc-weekly" class="screen">
  <div class="dox-content" style="max-width:700px">
    <div class="dox-alert dox-alert--info" style="margin-bottom:var(--dox-spacing-lg)">
      <strong>Revised modal — weekly cadence.</strong>
      Three changes from the existing pattern: (1) Session type radio removed — already encoded in clinic service name. (2) Labels rewritten in coordinator language ("Clinic Days", "Duration", "Scheduling for"). (3) Plain-English summary added before Apply so coordinators know exactly what will be generated.
    </div>

    <div class="dox-card" style="max-width:420px">
      <div class="dox-modal__header" style="padding:var(--dox-spacing-lg);border-bottom:var(--dox-border);display:flex;align-items:flex-start;justify-content:space-between">
        <h5 class="dox-modal__title">Schedule Clinic Sessions — Alicia Nguyen</h5>
        <button class="dox-modal__close">×</button>
      </div>
      <div class="dox-modal__body">

        <!-- Clinic -->
        <div class="dox-form-group">
          <label class="dox-label">Clinic</label>
          <select class="dox-select">
            <option>AM Ambulatory</option>
            <option>PM Ambulatory</option>
            <option>GI Clinic</option>
            <option>Women's Health</option>
          </select>
        </div>

        <!-- Scheduling for (Apply to — moved to top) -->
        <div class="dox-form-group is-new">
          <label class="dox-label">Scheduling for</label>
          <div class="scope-selector">
            <button class="scope-btn is-active" onclick="selectScope(this)">
              Alicia Nguyen only
              <span class="sub">1 resident</span>
            </button>
            <button class="scope-btn" onclick="selectScope(this)">
              All residents in FMI service
              <span class="sub">24 residents</span>
            </button>
          </div>
        </div>

        <!-- Clinic Days -->
        <div class="dox-form-group">
          <label class="dox-label">Clinic Days</label>
          <div class="day-pills">
            <button class="day-pill is-selected" onclick="togglePill(this)">Mo</button>
            <button class="day-pill" onclick="togglePill(this)">Tu</button>
            <button class="day-pill is-selected" onclick="togglePill(this)">We</button>
            <button class="day-pill" onclick="togglePill(this)">Th</button>
            <button class="day-pill" onclick="togglePill(this)">Fr</button>
          </div>
        </div>

        <!-- Frequency -->
        <div class="dox-form-group">
          <label class="dox-label">Frequency</label>
          <select class="dox-select" style="width:auto">
            <option selected>Every week</option>
            <option>Every 2 weeks</option>
            <option>Custom 4-week cycle</option>
          </select>
        </div>

        <!-- Duration -->
        <div class="dox-form-group">
          <label class="dox-label">Duration</label>
          <div class="dox-stack dox-stack--xs">
            <label class="dox-check"><input type="radio" name="dur-w" checked> Full Academic Year (through Jun 2026)</label>
            <label class="dox-check"><input type="radio" name="dur-w"> This block only</label>
            <label class="dox-check"><input type="radio" name="dur-w">
              Custom
              <input type="date" class="dox-input" value="2026-06-19" style="width:auto;margin-left:6px">
            </label>
          </div>
        </div>

      </div>

      <!-- Summary + footer -->
      <div style="padding: 0 var(--dox-spacing-lg) var(--dox-spacing-sm)">
        <div class="session-summary is-new">
          Will create <strong>~96 sessions</strong> (Mon + Wed, every week) for <strong>Alicia Nguyen</strong> through Jun 2026.
        </div>
      </div>
      <div class="dox-modal__footer">
        <button class="dox-btn dox-btn--ghost">Cancel</button>
        <button class="dox-btn dox-btn--primary">Apply</button>
      </div>
    </div>

    <hr class="dox-divider">

    <!-- Trigger context -->
    <h6 style="margin-bottom:var(--dox-spacing-sm)">Triggered from the clinic calendar</h6>
    <p class="dox-text-xs dox-text-muted" style="margin-bottom:var(--dox-spacing-md)">Coordinator hovers an empty cell → "Set Recurring…" → opens this modal. Same trigger as the existing block "Repeat" action — no new navigation or settings page required.</p>

    <div class="cal-wrap">
      <div class="cal-grid">
        <div class="cal-th name-col" style="padding:6px 10px">Sort: A–Z</div>
        <div class="cal-th">Mon 3</div>
        <div class="cal-th">Tue 4</div>
        <div class="cal-th">Wed 5</div>
        <div class="cal-th">Thu 6</div>
        <div class="cal-th">Fri 7</div>

        <div class="cal-name">Alicia Nguyen</div>
        <div class="cal-cell"><div class="add-hint"><span>Set Recurring…</span></div></div>
        <div class="cal-cell"><div class="add-hint"><span>Set Recurring…</span></div></div>
        <div class="cal-cell"><div class="add-hint"><span>Set Recurring…</span></div></div>
        <div class="cal-cell"><div class="add-hint"><span>Set Recurring…</span></div></div>
        <div class="cal-cell"><div class="add-hint"><span>Set Recurring…</span></div></div>

        <div class="cal-name">Brian Reynolds</div>
        <div class="cal-cell"><span class="sched-chip ch-am">AM Ambulatory</span></div>
        <div class="cal-cell"></div>
        <div class="cal-cell"><span class="sched-chip ch-am">AM Ambulatory</span></div>
        <div class="cal-cell"></div>
        <div class="cal-cell"></div>

        <div class="cal-name">Leo Owens</div>
        <div class="cal-cell"></div>
        <div class="cal-cell"><span class="sched-chip ch-pm">PM GI</span></div>
        <div class="cal-cell"></div>
        <div class="cal-cell"></div>
        <div class="cal-cell"><span class="sched-chip ch-pm">PM GI</span></div>
      </div>
    </div>
  </div>
</div>


<!-- ════════════════════════════════════════
     SCREEN 3 — Revised: 4-week cadence
════════════════════════════════════════ -->
<div id="sc-fourweek" class="screen">
  <div class="dox-content" style="max-width:700px">
    <div class="dox-alert dox-alert--info" style="margin-bottom:var(--dox-spacing-lg)">
      <strong>Revised modal — custom 4-week cycle.</strong>
      Same modal as the weekly case, with "Custom 4-week cycle" selected in Frequency. Week tabs + day pills replaced by a single week × day table — the coordinator can see the full 4-week pattern at a glance and toggle individual cells. This directly addresses the ARMC use case (currently requires 316 duplicate block services).
    </div>

    <div class="dox-card" style="max-width:460px">
      <div class="dox-modal__header" style="padding:var(--dox-spacing-lg);border-bottom:var(--dox-border);display:flex;align-items:flex-start;justify-content:space-between">
        <h5 class="dox-modal__title">Schedule Clinic Sessions — Alicia Nguyen</h5>
        <button class="dox-modal__close">×</button>
      </div>
      <div class="dox-modal__body">

        <!-- Clinic -->
        <div class="dox-form-group">
          <label class="dox-label">Clinic</label>
          <select class="dox-select">
            <option>FMI Clinic</option>
            <option>AM Ambulatory</option>
            <option>GI Clinic</option>
          </select>
        </div>

        <!-- Scheduling for -->
        <div class="dox-form-group">
          <label class="dox-label">Scheduling for</label>
          <div class="scope-selector">
            <button class="scope-btn is-active" onclick="selectScope(this)">
              Alicia Nguyen only
              <span class="sub">1 resident</span>
            </button>
            <button class="scope-btn" onclick="selectScope(this)">
              All residents in FMI service
              <span class="sub">24 residents</span>
            </button>
          </div>
        </div>

        <!-- Frequency — 4-week selected -->
        <div class="dox-form-group">
          <label class="dox-label">Frequency</label>
          <select class="dox-select" style="width:auto">
            <option>Every week</option>
            <option>Every 2 weeks</option>
            <option selected>Custom 4-week cycle</option>
          </select>
        </div>

        <!-- 4-week cycle table (replaces week tabs + day pills) -->
        <div class="dox-form-group is-new" style="--dox-radius-md:6px">
          <label class="dox-label">Clinic Days by week</label>
          <p class="dox-text-xs dox-text-muted" style="margin-bottom:8px">Week 1 = first week of each block rotation. Click a cell to toggle.</p>
          <div class="cycle-table">
            <div class="cycle-table__head">
              <div class="cycle-table__head-cell"></div>
              <div class="cycle-table__head-cell">Mon</div>
              <div class="cycle-table__head-cell">Tue</div>
              <div class="cycle-table__head-cell">Wed</div>
              <div class="cycle-table__head-cell">Thu</div>
              <div class="cycle-table__head-cell">Fri</div>
            </div>
            <!-- Week 1: Mon + Wed -->
            <div class="cycle-table__row">
              <div class="cycle-table__week">Week 1 <span>first week</span></div>
              <div class="cycle-cell is-on" onclick="toggleCell(this)"></div>
              <div class="cycle-cell" onclick="toggleCell(this)"></div>
              <div class="cycle-cell is-on" onclick="toggleCell(this)"></div>
              <div class="cycle-cell" onclick="toggleCell(this)"></div>
              <div class="cycle-cell" onclick="toggleCell(this)"></div>
            </div>
            <!-- Week 2: Thu -->
            <div class="cycle-table__row">
              <div class="cycle-table__week">Week 2</div>
              <div class="cycle-cell" onclick="toggleCell(this)"></div>
              <div class="cycle-cell" onclick="toggleCell(this)"></div>
              <div class="cycle-cell" onclick="toggleCell(this)"></div>
              <div class="cycle-cell is-on" onclick="toggleCell(this)"></div>
              <div class="cycle-cell" onclick="toggleCell(this)"></div>
            </div>
            <!-- Week 3: Mon + Wed -->
            <div class="cycle-table__row">
              <div class="cycle-table__week">Week 3</div>
              <div class="cycle-cell is-on" onclick="toggleCell(this)"></div>
              <div class="cycle-cell" onclick="toggleCell(this)"></div>
              <div class="cycle-cell is-on" onclick="toggleCell(this)"></div>
              <div class="cycle-cell" onclick="toggleCell(this)"></div>
              <div class="cycle-cell" onclick="toggleCell(this)"></div>
            </div>
            <!-- Week 4: none -->
            <div class="cycle-table__row">
              <div class="cycle-table__week">Week 4 <span>no sessions</span></div>
              <div class="cycle-cell" onclick="toggleCell(this)"></div>
              <div class="cycle-cell" onclick="toggleCell(this)"></div>
              <div class="cycle-cell" onclick="toggleCell(this)"></div>
              <div class="cycle-cell" onclick="toggleCell(this)"></div>
              <div class="cycle-cell" onclick="toggleCell(this)"></div>
            </div>
          </div>
        </div>

        <!-- Duration -->
        <div class="dox-form-group">
          <label class="dox-label">Duration</label>
          <div class="dox-stack dox-stack--xs">
            <label class="dox-check"><input type="radio" name="dur-4w" checked> Full Academic Year (through Jun 2026)</label>
            <label class="dox-check"><input type="radio" name="dur-4w"> This block only</label>
            <label class="dox-check"><input type="radio" name="dur-4w">
              Custom
              <input type="date" class="dox-input" value="2026-06-19" style="width:auto;margin-left:6px">
            </label>
          </div>
        </div>

      </div>

      <!-- Summary + footer -->
      <div style="padding: 0 var(--dox-spacing-lg) var(--dox-spacing-sm)">
        <div class="session-summary is-new">
          Will create <strong>~90 sessions</strong> across a 4-week cycle (W1: Mon+Wed · W2: Thu · W3: Mon+Wed · W4: none) for <strong>Alicia Nguyen</strong> through Jun 2026.
        </div>
      </div>
      <div class="dox-modal__footer">
        <button class="dox-btn dox-btn--ghost">Cancel</button>
        <button class="dox-btn dox-btn--primary">Apply</button>
      </div>
    </div>
  </div>
</div>


<!-- ════════════════════════════════════════
     SCREEN 4 — Cancel States
════════════════════════════════════════ -->
<div id="sc-cancel" class="screen">
  <div class="dox-content" style="max-width:800px">
    <div class="dox-alert dox-alert--warning" style="margin-bottom:var(--dox-spacing-lg)">
      <strong>Open Design Question (AMIONMGR-3295):</strong> How should auto-canceled sessions appear on the calendar? They must be visually distinct from active sessions — coordinators need to notice them for ACGME compliance.
    </div>

    <div class="dox-row dox-row--md" style="align-items:flex-start;margin-bottom:var(--dox-spacing-lg)">

      <!-- Option A -->
      <div style="flex:1">
        <div class="dox-card">
          <div class="dox-card__header"><h6 class="dox-card__title">Option A — Strikethrough</h6></div>
          <div class="dox-card__body">
            <div class="cal-wrap">
              <div class="cal-grid" style="grid-template-columns:100px 1fr 1fr 1fr">
                <div class="cal-th name-col">Name</div><div class="cal-th">Wed</div><div class="cal-th">Thu ← post-call</div><div class="cal-th">Fri</div>
                <div class="cal-name">Baker, T.</div>
                <div class="cal-cell"><span class="sched-chip ch-call">Night Call</span></div>
                <div class="cal-cell"><span class="sched-chip ch-cancel">AM Clinic</span></div>
                <div class="cal-cell"><span class="sched-chip ch-am">AM Clinic</span></div>
                <div class="cal-name">Evans, P.</div>
                <div class="cal-cell"></div>
                <div class="cal-cell"><span class="sched-chip ch-am">AM Clinic</span></div>
                <div class="cal-cell"><span class="sched-chip ch-am">AM Clinic</span></div>
              </div>
            </div>
            <div style="margin-top:var(--dox-spacing-sm)">
              <p class="dox-text-xs" style="color:var(--dox-color-success)">✓ Familiar pattern. No new colors.</p>
              <p class="dox-text-xs dox-text-muted">✗ Blends with OFF chips. No reinstatement affordance.</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Option B -->
      <div style="flex:1">
        <div class="dox-card" style="border-color:var(--dox-color-primary)">
          <div class="dox-card__header" style="background:var(--dox-color-primary-light)"><h6 class="dox-card__title" style="color:var(--dox-color-primary-dark)">Option B — Warning chip + ↩ icon ★</h6></div>
          <div class="dox-card__body">
            <div class="cal-wrap">
              <div class="cal-grid" style="grid-template-columns:100px 1fr 1fr 1fr">
                <div class="cal-th name-col">Name</div><div class="cal-th">Wed</div><div class="cal-th">Thu ← post-call</div><div class="cal-th">Fri</div>
                <div class="cal-name">Baker, T.</div>
                <div class="cal-cell"><span class="sched-chip ch-call">Night Call</span></div>
                <div class="cal-cell"><span class="sched-chip ch-amber">↩ AM Clinic</span></div>
                <div class="cal-cell"><span class="sched-chip ch-am">AM Clinic</span></div>
                <div class="cal-name">Evans, P.</div>
                <div class="cal-cell"></div>
                <div class="cal-cell"><span class="sched-chip ch-am">AM Clinic</span></div>
                <div class="cal-cell"><span class="sched-chip ch-am">AM Clinic</span></div>
              </div>
            </div>
            <div style="margin-top:var(--dox-spacing-sm)">
              <p class="dox-text-xs" style="color:var(--dox-color-success)">✓ Immediately visible. ↩ signals reinstatement. Warning color = ACGME-safe.</p>
              <p class="dox-text-xs dox-text-muted">✗ Adds a new chip variant.</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Reinstatement flow -->
    <div class="dox-card">
      <div class="dox-card__header"><h6 class="dox-card__title">Reinstatement state flow</h6></div>
      <div class="dox-card__body">
        <div class="dox-row dox-row--lg" style="flex-wrap:wrap">
          <div style="text-align:center"><div class="dox-text-xs dox-text-muted" style="margin-bottom:4px">Active</div><span class="sched-chip ch-am">AM Clinic</span></div>
          <span style="color:var(--dox-gray-400);font-size:18px">→</span>
          <div style="text-align:center"><div class="dox-text-xs dox-text-muted" style="margin-bottom:4px">Auto-canceled</div><span class="sched-chip ch-amber">↩ AM Clinic</span></div>
          <span style="color:var(--dox-gray-400);font-size:18px">→</span>
          <div style="text-align:center"><div class="dox-text-xs dox-text-muted" style="margin-bottom:4px">Coordinator clicks</div><span style="font-size:11px;background:#111;color:#fff;padding:2px 8px;border-radius:3px">Reinstate session?</span></div>
          <span style="color:var(--dox-gray-400);font-size:18px">→</span>
          <div style="text-align:center"><div class="dox-text-xs dox-text-muted" style="margin-bottom:4px">Reinstated (logged)</div><span class="sched-chip" style="background:var(--dox-color-success-light);color:var(--dox-color-success-dark);border:1px solid #a7f3c0">AM Clinic ✓</span></div>
        </div>
        <p class="dox-text-xs dox-text-muted" style="margin-top:var(--dox-spacing-sm)">All reinstatements logged for ACGME compliance. Reinstated sessions show green ✓ — distinct from never-canceled sessions. Cancel rules suppress; delete is permanent.</p>
      </div>
    </div>
  </div>
</div>

<script>
function showScreen(id, btn) {
  document.querySelectorAll('.screen').forEach(function(s) { s.classList.remove('is-active'); });
  document.querySelectorAll('.proto-tab').forEach(function(t) { t.classList.remove('is-active'); });
  document.getElementById('sc-' + id).classList.add('is-active');
  btn.classList.add('is-active');
  window.scrollTo(0, 0);
}

function togglePill(btn) {
  btn.classList.toggle('is-selected');
}

function toggleCell(cell) {
  cell.classList.toggle('is-on');
}

function selectScope(btn) {
  var parent = btn.closest('.scope-selector');
  parent.querySelectorAll('.scope-btn').forEach(function(b) { b.classList.remove('is-active'); });
  btn.classList.add('is-active');
}
</script>
</body>
</html>
