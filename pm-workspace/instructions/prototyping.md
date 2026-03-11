# HTML Prototype Instructions

All HTML prototypes in `pm-workspace/active/` must use the Dox Design System CSS.

## Setup

Every prototype `index.html` must include this link in `<head>`:

```html
<link rel="stylesheet" href="../../assets/dox-prototype.css">
```

Adjust the relative path if the prototype is nested deeper (e.g., `../../../assets/dox-prototype.css`).

Do **not** write custom `<style>` blocks that duplicate or override design system tokens. Use CSS variable overrides only when strictly necessary for prototype-specific chrome (e.g., a mock schedule grid).

---

## Page Structure

All prototypes follow this shell:

```html
<body>
  <!-- App header (always dark) -->
  <header class="amion-header">
    <span class="amion-header__logo">am<span class="highlight">i</span>on</span>
    <div class="amion-header__divider"></div>
    <button class="amion-header__tab is-active">Manager</button>
    <span class="amion-header__badge">Sandbox</span>
  </header>

  <!-- Optional breadcrumb bar -->
  <nav class="amion-breadcrumb">
    <span>Organization</span>
    <span class="amion-breadcrumb__sep">›</span>
    <span class="amion-breadcrumb__current">Schedule Name</span>
  </nav>

  <!-- Main shell: sidebar + content -->
  <div class="dox-shell">
    <aside class="dox-sidebar">
      <!-- sidebar items -->
    </aside>
    <main class="dox-main">
      <!-- sticky page header -->
      <div class="dox-page-header">
        <div>
          <h1 class="dox-page-header__title">Page Title</h1>
          <p class="dox-page-header__subtitle">Optional subtitle</p>
        </div>
        <div class="dox-page-header__actions">
          <button class="dox-btn dox-btn--primary">Primary Action</button>
        </div>
      </div>
      <!-- tab bar (when needed) -->
      <div class="dox-tabs">
        <button class="dox-tab is-active">Tab 1</button>
        <button class="dox-tab">Tab 2</button>
      </div>
      <!-- content -->
      <div class="dox-content">
        <!-- page body here -->
      </div>
    </main>
  </div>
</body>
```

---

## Component Reference

### Buttons

```html
<button class="dox-btn dox-btn--primary">Save</button>
<button class="dox-btn dox-btn--secondary">Cancel</button>
<button class="dox-btn dox-btn--ghost">Learn more</button>
<button class="dox-btn dox-btn--danger">Delete</button>
<button class="dox-btn dox-btn--sm dox-btn--secondary">Small</button>
<button class="dox-btn dox-btn--lg dox-btn--primary">Large</button>
<button class="dox-btn dox-btn--primary" disabled>Disabled</button>
```

Button group:
```html
<div class="dox-btn-group">
  <button class="dox-btn dox-btn--primary">Save</button>
  <button class="dox-btn dox-btn--secondary">Cancel</button>
</div>
```

### Form Fields

```html
<div class="dox-form-group">
  <label class="dox-label dox-label--required" for="name">Label</label>
  <input class="dox-input" id="name" type="text" placeholder="Placeholder">
  <span class="dox-hint">Helper text goes here</span>
</div>

<div class="dox-form-group">
  <label class="dox-label" for="type">Select</label>
  <select class="dox-select" id="type">
    <option>Option 1</option>
    <option>Option 2</option>
  </select>
</div>

<!-- Error state -->
<div class="dox-form-group">
  <label class="dox-label dox-label--required" for="val">Field</label>
  <input class="dox-input dox-input--error" id="val" type="text">
  <span class="dox-error-msg">This field is required.</span>
</div>

<!-- Checkbox -->
<label class="dox-check">
  <input type="checkbox" checked>
  <span>Enable this option</span>
</label>
```

### Cards

```html
<div class="dox-card">
  <div class="dox-card__header">
    <h3 class="dox-card__title">Card Title</h3>
    <button class="dox-btn dox-btn--ghost dox-btn--sm">Edit</button>
  </div>
  <div class="dox-card__body">
    Card content here.
  </div>
  <div class="dox-card__footer">
    <button class="dox-btn dox-btn--primary">Save</button>
  </div>
</div>
```

### Modal

```html
<div class="dox-modal-overlay">
  <div class="dox-modal">
    <div class="dox-modal__header">
      <h2 class="dox-modal__title">Modal Title</h2>
      <button class="dox-modal__close" aria-label="Close">×</button>
    </div>
    <div class="dox-modal__body">
      Modal content here.
    </div>
    <div class="dox-modal__footer">
      <button class="dox-btn dox-btn--secondary">Cancel</button>
      <button class="dox-btn dox-btn--primary">Confirm</button>
    </div>
  </div>
</div>
```

### Badges

```html
<span class="dox-badge dox-badge--neutral">Draft</span>
<span class="dox-badge dox-badge--primary">Active</span>
<span class="dox-badge dox-badge--success">Published</span>
<span class="dox-badge dox-badge--danger">Error</span>
<span class="dox-badge dox-badge--warning">Pending</span>
```

### Alerts

```html
<div class="dox-alert dox-alert--info">Informational message.</div>
<div class="dox-alert dox-alert--success">Changes saved successfully.</div>
<div class="dox-alert dox-alert--warning">Review before proceeding.</div>
<div class="dox-alert dox-alert--danger">Something went wrong.</div>
```

### Table

```html
<table class="dox-table">
  <thead>
    <tr>
      <th>Name</th>
      <th>Role</th>
      <th>Status</th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Dr. Smith</td>
      <td>Resident</td>
      <td><span class="dox-badge dox-badge--success">Active</span></td>
      <td><button class="dox-btn dox-btn--ghost dox-btn--sm">Edit</button></td>
    </tr>
  </tbody>
</table>
```

### Layout Utilities

```html
<!-- Vertical stack with gap -->
<div class="dox-stack dox-stack--md">
  <div>Item 1</div>
  <div>Item 2</div>
</div>

<!-- Horizontal row -->
<div class="dox-row dox-row--sm dox-row--spread">
  <span>Left</span>
  <span>Right</span>
</div>

<!-- Muted/small text -->
<p class="dox-text-muted dox-text-sm">Secondary information</p>

<!-- Divider -->
<hr class="dox-divider">
```

---

## Design Tokens (CSS variables)

Reference these directly when component classes aren't sufficient:

| Variable | Value | Use for |
|---|---|---|
| `--dox-color-primary` | `#1276D3` | Links, primary actions |
| `--dox-color-body-font` | `#333` | Body text |
| `--dox-color-muted` | `#585858` | Secondary text |
| `--dox-spacing-xs/sm/md/lg/xl` | 5/10/15/20/25px | Gaps, padding |
| `--dox-font-size-xs/sm/md/lg` | 12/14/16/20px | Text sizing |
| `--dox-radius-md/lg` | 5px / 8px | Border radius |
| `--dox-border` | `1px solid #BBB` | Dividers, borders |
| `--dox-gray-100..950` | #F9F9F9–#111 | Background tints |
| `--dox-white` | `#FFF` | Surface backgrounds |

---

## Prototype Annotations

Use `.proto-annotation` for notes that should never appear in production mockups:

```html
<span class="proto-annotation">TODO: confirm copy with PM</span>
```

---

## Rules

- Use `dox-btn--primary` for the single primary CTA per section. Use `dox-btn--secondary` for secondary actions.
- Use `dox-badge` for status labels, not inline text styles.
- Forms always use `dox-form-group` wrapper with `dox-label` + control + optional hint/error.
- Never hardcode colors — use `var(--dox-color-*)` or `var(--dox-gray-*)`.
- Schedule state badges: Sandbox → `dox-badge--neutral`, Preview → `dox-badge--warning`, Staging → `dox-badge--primary`, Done → `dox-badge--success`.
