---
name: uncodixify
description: Guides UI design away from generic AI aesthetic patterns ("Codex UI") toward human-designed, functional interfaces inspired by Linear, Raycast, Stripe, and GitHub. Use when building any UI, web interface, dashboard, component, or canvas — especially when the user asks for beautiful, professional, or non-generic UI, or when generating HTML/CSS/React UI from scratch.
---

# Uncodixify

Break the default AI aesthetic. Build interfaces that feel human-designed, functional, and honest — not like another generic AI dashboard.

**When you read this skill, internalise the banned patterns first. In your internal reasoning, list every default move you'd normally make — then don't do any of them.**

---

## Keep It Normal

| Element     | Rule                                                                                                    |
| ----------- | ------------------------------------------------------------------------------------------------------- |
| Sidebars    | 240–260px fixed, solid background, simple `border-right`. No floating shells, no rounded outer corners. |
| Headers     | Plain `h1`/`h2`. No eyebrow labels, no uppercase, no gradient text.                                     |
| Buttons     | Solid fill or simple border, 8–10px radius max. No pill shapes, no gradients.                           |
| Cards       | 8–12px radius max, subtle borders, shadows max `0 2px 8px rgba(0,0,0,0.1)`. No floating, no glass.      |
| Forms       | Labels above fields. No floating labels, no animated underlines.                                        |
| Tabs        | Underline or border indicator. No pill backgrounds, no sliding animations.                              |
| Tables      | Clean rows, subtle hover, left-aligned text. No zebra unless actually needed.                           |
| Typography  | System sans or a simple single sans-serif. 14–16px body. No mixed serif/sans combos.                    |
| Spacing     | 4/8/12/16/24/32px scale. No random gaps, no excessive padding.                                          |
| Borders     | 1px solid, subtle colour. No thick decorative or gradient borders.                                      |
| Shadows     | Max `0 2px 8px rgba(0,0,0,0.1)`. No dramatic or coloured shadows.                                       |
| Transitions | 100–200ms ease. Opacity/colour only. No bouncy or transform effects.                                    |
| Containers  | max-width 1200–1400px, centered, standard padding.                                                      |

Think Linear. Think Raycast. Think Stripe. Think GitHub. They don't try to grab attention. They just work.

---

## Hard No

- Oversized rounded corners (20–32px range)
- Pill overload
- Glassmorphism / frosted panels as default visual language
- Soft corporate gradients to fake taste
- Generic dark SaaS blue-black + cyan composition
- Decorative sidebar blobs
- "Control room" cosplay (unless explicitly requested)
- Serif headline + system sans fallback combo as shortcut to "premium"
- `Segoe UI`, `Trebuchet MS`, `Arial`, `Inter`, `Roboto` or safe default font stacks (unless the product already uses them)
- Sticky left rail unless the IA truly needs it
- Metric-card grid as the first instinct
- Fake charts that exist only to fill space
- Random glows, blur haze, conic-gradient donuts as decoration
- Hero sections inside internal UIs without a real product reason
- Alignment that creates dead space to look expensive
- Overpadded layouts
- `<small>` eyebrow headers (e.g. `<small>Team Command</small><h2>One place to…</h2>`)
- Big rounded `<span>` labels
- Colors drifting blue — dark muted tones are best
- Decorative copy like "Operational clarity without the clutter" as page headers
- Section notes explaining what the UI does
- Transform hover animations (`translateX(2px)` on nav links, etc.)
- KPI card grids as the default dashboard layout
- Tag badges on every table row status
- Nav badges showing "Live" status
- Footer lines with meta info about the page itself
- Trend indicators with coloured text classes (`trend-up`, `trend-flat`)
- Multiple nested panel types (`panel`, `panel-2`, `rail-panel`, `table-panel`)

---

## Colour Strategy

Priority order — do not skip steps:

1. **Use existing project colours** if provided (search a few source files first).
2. If no palette exists, **pick one from the tables below** (choose randomly, not always the first).
3. **Do not invent random colour combinations** unless explicitly requested.

### Dark Palettes

| Palette         | Background | Surface   | Primary   | Secondary | Accent    | Text      |
| --------------- | ---------- | --------- | --------- | --------- | --------- | --------- |
| Midnight Canvas | `#0a0e27`  | `#151b3d` | `#6c8eff` | `#a78bfa` | `#f472b6` | `#e2e8f0` |
| Obsidian Depth  | `#0f0f0f`  | `#1a1a1a` | `#00d4aa` | `#00a3cc` | `#ff6b9d` | `#f5f5f5` |
| Slate Noir      | `#0f172a`  | `#1e293b` | `#38bdf8` | `#818cf8` | `#fb923c` | `#f1f5f9` |
| Carbon Elegance | `#121212`  | `#1e1e1e` | `#bb86fc` | `#03dac6` | `#cf6679` | `#e1e1e1` |
| Deep Ocean      | `#001e3c`  | `#0a2744` | `#4fc3f7` | `#29b6f6` | `#ffa726` | `#eceff1` |
| Charcoal Studio | `#1c1c1e`  | `#2c2c2e` | `#0a84ff` | `#5e5ce6` | `#ff375f` | `#f2f2f7` |
| Graphite Pro    | `#18181b`  | `#27272a` | `#a855f7` | `#ec4899` | `#14b8a6` | `#fafafa` |
| Void Space      | `#0d1117`  | `#161b22` | `#58a6ff` | `#79c0ff` | `#f78166` | `#c9d1d9` |
| Twilight Mist   | `#1a1625`  | `#2d2438` | `#9d7cd8` | `#7aa2f7` | `#ff9e64` | `#dcd7e8` |
| Onyx Matrix     | `#0e0e10`  | `#1c1c21` | `#00ff9f` | `#00e0ff` | `#ff0080` | `#f0f0f0` |

### Light Palettes

| Palette         | Background | Surface   | Primary   | Secondary | Accent    | Text      |
| --------------- | ---------- | --------- | --------- | --------- | --------- | --------- |
| Cloud Canvas    | `#fafafa`  | `#ffffff` | `#2563eb` | `#7c3aed` | `#dc2626` | `#0f172a` |
| Pearl Minimal   | `#f8f9fa`  | `#ffffff` | `#0066cc` | `#6610f2` | `#ff6b35` | `#212529` |
| Ivory Studio    | `#f5f5f4`  | `#fafaf9` | `#0891b2` | `#06b6d4` | `#f59e0b` | `#1c1917` |
| Linen Soft      | `#fef7f0`  | `#fffbf5` | `#d97706` | `#ea580c` | `#0284c7` | `#292524` |
| Porcelain Clean | `#f9fafb`  | `#ffffff` | `#4f46e5` | `#8b5cf6` | `#ec4899` | `#111827` |
| Cream Elegance  | `#fefce8`  | `#fefce8` | `#65a30d` | `#84cc16` | `#f97316` | `#365314` |
| Arctic Breeze   | `#f0f9ff`  | `#f8fafc` | `#0284c7` | `#0ea5e9` | `#f43f5e` | `#0c4a6e` |
| Alabaster Pure  | `#fcfcfc`  | `#ffffff` | `#1d4ed8` | `#2563eb` | `#dc2626` | `#1e293b` |
| Sand Warm       | `#faf8f5`  | `#ffffff` | `#b45309` | `#d97706` | `#059669` | `#451a03` |
| Frost Bright    | `#f1f5f9`  | `#f8fafc` | `#0f766e` | `#14b8a6` | `#e11d48` | `#0f172a` |

---

## The Rule

> If a UI choice feels like a default AI move, ban it and pick the harder, cleaner option.

Replicate what a designer in Figma would build. Don't invent new components — use the established patterns of the reference products (Linear, Raycast, Stripe, GitHub).
