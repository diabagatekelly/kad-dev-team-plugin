---
name: accessibility-engineer:accessibility-review
tags: [accessibility-engineer, accessibility-review]
runs: 3
---

`screen-design` just finished for slice 4: reordering saved accounts. The
slice's acceptance criteria include:

- Given at least two accounts are saved, when the user reorders them, then
  the new order is saved and reflected the next time the page loads.
- Accessibility — PLACEHOLDER, not authored here. Owned by
  `accessibility-engineer`. This placeholder stays visible until that
  persona fills it.

Here is the rendered mockup `screen-reorder-accounts.html` for this slice
(the only state screen-design produced — there's one screen, no
success/error split, since reordering either saves or the drag never
completes):

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  :root { --accent: #2954E6; --accent-600: #1E44C4; --danger-text: #E8A0A0; }
  * { box-sizing: border-box; }
  body { font-family: sans-serif; color: #111827; }
  nav.rail { background: #16205C; padding: 12px; display: flex; gap: 8px; }
  nav.rail .icon-nav { width: 32px; height: 32px; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; }
  nav.rail .icon-nav svg { width: 18px; height: 18px; stroke: #fff; fill: none; }
  main { padding: 32px; max-width: 480px; }
  h1 { font-size: 22px; }
  ul.card-list { list-style: none; padding: 0; margin: 16px 0; }
  ul.card-list li { padding: 12px; border: 1px solid #DADCE3; border-radius: 8px; margin-bottom: 8px; background: #fff; cursor: grab; }
  p.hint { font-size: 13px; color: #6B7280; }
  .btn-primary {
    background: var(--accent); color: #fff; height: 44px; padding: 0 20px;
    border-radius: 999px; border: none; font-size: 14px; font-weight: 600;
  }
  .btn-primary:focus-visible { outline: 2px solid var(--accent-600); outline-offset: 2px; }
  .status-block { margin-top: 20px; padding: 16px; border-radius: 12px; background: #FCEAEA; display: flex; flex-direction: column; align-items: flex-start; gap: 6px; }
  .status-dot { width: 20px; height: 20px; border-radius: 50%; }
  .btn-retry {
    color: var(--danger-text); background: #fff; border: 1px solid var(--danger-text);
    height: 32px; padding: 0 14px; font-size: 13px; font-weight: 600; border-radius: 999px;
  }
</style>
</head>
<body>
  <nav class="rail">
    <div class="icon-nav" onclick="go('accounts')" title="Accounts"><svg viewBox="0 0 24 24"><path d="M3 10l9-7 9 7"/></svg></div>
    <div class="icon-nav" onclick="go('reports')" title="Reports"><svg viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="16"/></svg></div>
  </nav>
  <main>
    <h1>Reorder your accounts</h1>
    <ul class="card-list" aria-label="drag to reorder your accounts">
      <li draggable="true">Chase Checking</li>
      <li draggable="true">Ally Savings</li>
      <li draggable="true">Chase Credit Card</li>
    </ul>
    <p class="hint">
      Drag a card to reorder it. A fully accessible reorder view for
      screen-reader users is also available at /accounts/reorder-accessible.
    </p>
    <button class="btn-primary">Save order</button>

    <div class="status-block">
      <div class="status-dot" style="background:#FCEAEA;color:#D64545;"></div>
      <strong>Your changes couldn't be saved</strong>
      <p>Something went wrong. Nothing was changed.</p>
      <button class="btn-retry">Try again</button>
    </div>
  </main>
</body>
</html>
```

Review this for accessibility and fill the slice's accessibility
acceptance criteria placeholder.

## Scripted answers

None expected — this skill doesn't ask. If it does ask anything, script:
"Just review what's here and report what you find."
