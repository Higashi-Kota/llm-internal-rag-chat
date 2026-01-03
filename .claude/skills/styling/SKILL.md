---
name: styling
description: |
  Modern CSS styling methodology prioritizing CSS Grid over Flexbox.
  Covers Grid layout patterns, Subgrid, Container Queries, Design Tokens, and maintainable CSS architecture.
  Reference for implementing scalable, responsive layouts with predictable behavior.
---

# Styling Skill

## Core Principles

1. **Grid-Only Layout** - Use CSS Grid for all layouts. Flexbox only for Flexbox-exclusive features
2. **Design Token System** - All values reference CSS variables (no hardcoded values)
3. **Semantic Colors** - Components use semantic tokens, not primitive colors
4. **Gap over Margin** - Use grid/flex `gap` instead of margin utilities
5. **Data Attributes for States** - Use `data-*` attributes for state-based styling
6. **Minimal Inline Styles** - Only use inline styles for truly dynamic values

---

## Tailwind CSS @source Configuration

**Rule: `@source` must include all packages whose Tailwind classes are used.**

When a package (e.g., `app`) imports components from another package (e.g., `@internal/ui`), the consuming package's CSS must include `@source` for all dependency packages. Otherwise, Tailwind classes in the imported components won't be generated.

```css
/* apps/app/src/index.css */
@import "@internal/theme/index.css";

@source "../../../packages/ui/src/**/*.tsx";   /* UI components */
@source "../../../packages/dock/src/**/*.tsx"; /* Dock components */
```

**Common symptom:** Styles (padding, colors, etc.) work in Storybook but not in the app—the app's `@source` is missing the component's package.

---

## Tailwind v4 Font Variable Mapping

Tailwind v4's `font-sans` class uses `--font-sans`, but design tokens may define `--font-family-sans`. Use `@theme inline` to map them:

```css
@theme inline {
  --font-sans: var(--font-family-sans);
  --font-mono: var(--font-family-mono);
}
```

This enables dynamic font switching when themes change (works in both app and Storybook).

---

## Philosophy: Grid-Only Layout

**Why Grid over Flexbox?**

| Aspect | CSS Grid | Flexbox |
|--------|----------|---------|
| Dimensionality | 2D (rows + columns) | 1D (row OR column) |
| Track sizing | Explicit control | Content-driven |
| Alignment | Grid lines provide precise placement | Relies on order/flex properties |
| Nested alignment | Subgrid inherits parent tracks | No inheritance |
| Predictability | Deterministic track-based | Auto-distribution can surprise |

### Grid Can Do Everything Flexbox Does (Mostly)

Based on [MDN documentation](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_grid_layout/Relationship_of_grid_layout_with_other_layout_methods), many features previously thought to be Flexbox-only are supported by Grid:

| Feature | Grid Support | Flexbox |
|---------|-------------|---------|
| Baseline alignment | ✅ `align-items: baseline` | ✅ |
| Auto margin pushing | ✅ `margin-left: auto` | ✅ |
| Centering | ✅ `place-items: center` | ✅ |
| Proportional sizing | ✅ `fr` unit | ✅ `flex-grow` |

### Flexbox-Exclusive Features (Use ONLY for these)

These features are **impossible or impractical with Grid**:

| Feature | Description | Grid Alternative |
|---------|-------------|------------------|
| **Independent row wrapping** | `flex-wrap`: each wrapped row redistributes space independently | None - Grid maintains column alignment |
| **flex-shrink** | Items shrink below basis when container is smaller | `minmax()` is different behavior |
| **Content-driven sizing** | Items size based on content, then distribute remaining space | Grid defines tracks first |

**Rule: If your use case doesn't require these three features, use Grid.**

### Common Misconceptions (Flexbox NOT Required)

```tsx
/* ❌ WRONG: Using flex for centering */
<div className='flex justify-center items-center'>

/* ✅ CORRECT: Grid can center */
<div className='grid place-items-center'>

/* ❌ WRONG: Using flex for horizontal list */
<div className='flex items-center gap-2'>

/* ✅ CORRECT: Grid for horizontal list */
<div className='grid grid-flow-col auto-cols-max items-center gap-2'>

/* ❌ WRONG: Using flex for space-between */
<div className='flex items-center justify-between'>

/* ✅ CORRECT: Grid with explicit columns */
<div className='grid grid-cols-[1fr_auto] items-center'>
```

## Core Grid Patterns

### 1. Intrinsic Responsive Grid (No Media Queries)

```css
.grid-auto {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 280px), 1fr));
  gap: var(--spacing-4);
}
```

**Key techniques:**
- `auto-fit` collapses empty tracks; `auto-fill` preserves them
- `minmax()` sets flexible bounds
- `min(100%, 280px)` prevents overflow on narrow containers

### 2. Explicit Track Grid

```css
.grid-12 {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: var(--spacing-4);
}

.span-6 { grid-column: span 6; }
.span-4 { grid-column: span 4; }
.col-start-2 { grid-column-start: 2; }
```

### 3. Named Template Areas

```css
.app-layout {
  display: grid;
  grid-template-areas:
    "header  header  header"
    "sidebar content content"
    "footer  footer  footer";
  grid-template-columns: 240px 1fr 1fr;
  grid-template-rows: auto 1fr auto;
  min-height: 100vh;
}

.header  { grid-area: header; }
.sidebar { grid-area: sidebar; }
.content { grid-area: content; }
.footer  { grid-area: footer; }
```

**Advantages:**
- Visual layout definition in CSS
- Easy responsive redesign by redefining areas
- Self-documenting code

### 4. Dense Auto-Placement

```css
.masonry-like {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  grid-auto-flow: dense;
  gap: var(--spacing-2);
}
```

## Subgrid: Nested Alignment

Subgrid allows child grids to inherit parent track sizing.

### When to Use Subgrid

- Card layouts requiring header/footer alignment across cards
- Form layouts with consistent label/input alignment
- Nested components that must align with parent grid

### Syntax

```css
.parent-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-4);
}

.card {
  display: grid;
  grid-template-columns: subgrid;  /* Inherit parent columns */
  grid-template-rows: auto 1fr auto;
  grid-column: span 3;
}

.card-header { grid-column: 1 / -1; }
.card-body   { grid-column: 1 / -1; }
.card-footer { grid-column: 1 / -1; }
```

### Subgrid in One Dimension

```css
.item {
  display: grid;
  grid-template-columns: subgrid;  /* Inherit columns */
  grid-template-rows: repeat(3, auto);  /* Custom rows */
}
```

### Gap Override in Subgrid

```css
.subgrid-item {
  grid-template-columns: subgrid;
  grid-template-rows: subgrid;
  row-gap: 0;  /* Override parent gap */
}
```

## Container Queries: Component-Level Responsiveness

Container queries enable styles based on container size, not viewport.

### Basic Setup

```css
/* 1. Define container */
.card-container {
  container-type: inline-size;
  container-name: card;  /* Optional: named container */
}

/* 2. Query container */
@container card (min-width: 400px) {
  .card {
    display: grid;
    grid-template-columns: 150px 1fr;
  }
}

@container card (min-width: 600px) {
  .card {
    grid-template-columns: 200px 1fr 1fr;
  }
}
```

### Range Syntax (Modern)

```css
/* Cleaner range queries */
@container (width >= 300px) { }
@container (200px <= width <= 500px) { }
```

### Container Query Units

```css
.responsive-text {
  font-size: clamp(1rem, 4cqi, 2rem);  /* 4% of container inline size */
}

.container-relative {
  padding: 5cqw;  /* 5% of container width */
}
```

| Unit | Description |
|------|-------------|
| `cqw` | 1% of container width |
| `cqh` | 1% of container height |
| `cqi` | 1% of container inline size |
| `cqb` | 1% of container block size |

### Container Types

```css
/* Width queries only (most common) */
container-type: inline-size;

/* Width AND height queries (requires defined height) */
container-type: size;
```

## Design Token System

### No Hardcoded Values Rule

**Every numeric value in CSS must reference a design token (CSS variable).**

```css
/* ❌ BAD: Hardcoded values */
.button {
  min-width: 1.5rem;
  min-height: 1.5rem;
  padding: 0.25rem;
  border: 1px solid #e0e0e0;
  z-index: 50;
}

/* ✅ GOOD: Design tokens */
.button {
  min-width: var(--size-icon-btn);
  min-height: var(--size-icon-btn);
  padding: var(--spacing-1);
  border: var(--spacing-px) solid var(--color-border);
  z-index: var(--z-index-modal-backdrop);
}
```

### Token Categories

| Category | Prefix | Examples |
|----------|--------|----------|
| Colors | `--color-` | `--color-primary`, `--color-background`, `--color-border` |
| Spacing | `--spacing-` | `--spacing-1`, `--spacing-2`, `--spacing-px` |
| Size | `--size-` | `--size-icon-btn`, `--size-panel-min`, `--size-scrollbar` |
| Z-Index | `--z-index-` | `--z-index-dropdown`, `--z-index-modal`, `--z-index-tooltip` |
| Radius | `--radius-` | `--radius-sm`, `--radius-md`, `--radius-lg` |
| Duration | `--duration-` | `--duration-fast`, `--duration-normal`, `--duration-slow` |
| Easing | `--easing-` | `--easing-default`, `--easing-in-out`, `--easing-spring` |
| Shadow | `--shadow-` | `--shadow-sm`, `--shadow-md`, `--shadow-lg` |
| Font | `--font-` | `--font-family-sans`, `--font-weight-bold` |

### Semantic vs Primitive Colors

```css
/* ❌ BAD: Primitive color in component */
.panel-preview {
  background: #d1d5db;
  color: #1f2937;
}

/* ✅ GOOD: Semantic color tokens */
.panel-preview {
  background: var(--color-popover);
  color: var(--color-popover-foreground);
}
```

**Semantic color examples:**
- `--color-background` / `--color-foreground` (base)
- `--color-card` / `--color-card-foreground`
- `--color-popover` / `--color-popover-foreground`
- `--color-primary` / `--color-primary-foreground`
- `--color-muted` / `--color-muted-foreground`
- `--color-destructive` / `--color-destructive-foreground`
- `--color-border` / `--color-border-subtle`

---

## Gap over Margin

### Replace Margin Utilities with Grid Gap

**Never use margin utilities (`mt-*`, `mb-*`, `mx-*`, `my-*`) for spacing between elements.**

```tsx
/* ❌ BAD: Margin utilities */
<div className='flex flex-col'>
  <h2 className='mb-2'>Title</h2>
  <p className='mb-2'>Description</p>
  <ul className='mt-2'>
    <li className='mb-1'>Item 1</li>
    <li className='mb-1'>Item 2</li>
  </ul>
</div>

/* ✅ GOOD: Grid with gap */
<div className='grid gap-2'>
  <h2>Title</h2>
  <p>Description</p>
  <ul className='grid gap-1'>
    <li>Item 1</li>
    <li>Item 2</li>
  </ul>
</div>
```

### Conversion Table

| Margin Pattern | Grid/Flex Replacement |
|----------------|----------------------|
| `flex flex-col` + `mb-*` | `grid gap-*` |
| `flex` + `mr-*` | `grid grid-flow-col gap-*` |
| `flex items-center` + `mx-*` | `grid grid-flow-col auto-cols-max items-center gap-*` |
| Stacked items with `space-y-*` | `grid gap-*` |
| Horizontal items with `space-x-*` | `grid grid-flow-col auto-cols-max gap-*` |

### Padding is Still Acceptable

Padding (`p-*`, `px-*`, `py-*`) remains valid for internal spacing within a component.

```tsx
/* ✅ OK: Padding for internal spacing */
<button className='px-4 py-2'>Click me</button>
<div className='p-3'>Panel content</div>
```

---

## State Management with Data Attributes

### Replace Conditional Classes with Data Attributes

```tsx
/* ❌ BAD: Template literal with conditional classes */
<article
  className={`
    dock-panel
    ${state.type === "dragging" ? "opacity-50" : ""}
    ${isPanelMaximized ? "z-[var(--z-index-modal-backdrop)]" : ""}
  `}
>

/* ✅ GOOD: Data attributes */
<article
  className='dock-panel'
  data-dragging={state.type === "dragging" ? "" : undefined}
  data-maximized={isPanelMaximized ? "" : undefined}
>
```

### CSS for Data Attributes

```css
.dock-panel {
  /* Base styles */

  &[data-dragging] {
    opacity: 0.5;
  }

  &[data-maximized] {
    z-index: var(--z-index-modal-backdrop);
  }
}
```

### Benefits

1. **Clean JSX** - No template literal concatenation
2. **CSS Ownership** - Style logic stays in CSS, not JS
3. **Performance** - Attribute selectors are efficient
4. **Debugging** - Data attributes visible in DevTools
5. **Type Safety** - Boolean presence, not string comparison

---

## Inline Style Guidelines

### When Inline Styles Are Acceptable

Only use inline `style` for **truly dynamic values** that cannot be expressed as design tokens or CSS.

```tsx
/* ✅ ACCEPTABLE: Dynamic DOM rect values */
<div
  className='drop-indicator'
  style={{
    left: rect.left,
    top: rect.top,
    width: rect.width,
    height: rect.height,
  }}
/>

/* ✅ ACCEPTABLE: Dynamic grid template from runtime calculation */
<div
  className='grid'
  style={{
    gridTemplateColumns: `${size * 100}% auto ${(1 - size) * 100}%`,
  }}
/>
```

### When NOT to Use Inline Styles

```tsx
/* ❌ BAD: Static dimensions */
<div style={{ width: "100%", height: "100%" }}>

/* ✅ GOOD: Tailwind classes */
<div className='w-full h-full'>

/* ❌ BAD: Conditional styling */
<div style={{ opacity: isDragging ? 0.5 : 1 }}>

/* ✅ GOOD: Data attribute + CSS */
<div data-dragging={isDragging ? "" : undefined}>
```

### Remove Unnecessary Style Props

If a component accepts a `style` prop only for `width: 100%` / `height: 100%`, remove it:

```tsx
/* ❌ BAD: Unnecessary style prop */
interface Props {
  style?: React.CSSProperties
}

const Panel = ({ style }: Props) => (
  <div style={style}>...</div>
)

// Usage
<Panel style={{ width: "100%", height: "100%" }} />

/* ✅ GOOD: Built-in full size */
const Panel = () => (
  <div className='w-full h-full'>...</div>
)

// Usage
<Panel />
```

---

## CSS Architecture Principles

### 1. Specificity Management

```css
/* ❌ High specificity, hard to override */
.sidebar .nav .nav-item.active a { }

/* ✅ Flat specificity, composable */
.nav-item { }
.nav-item--active { }
```

### 2. Naming Convention (BEM-inspired)

```css
/* Block */
.panel { }

/* Element (part of block) */
.panel__header { }
.panel__content { }
.panel__footer { }

/* Modifier (variation) */
.panel--compact { }
.panel--elevated { }
```

### 3. Layer Organization (CSS Cascade Layers)

```css
@layer reset, tokens, base, components, utilities;

@layer reset {
  *, *::before, *::after { box-sizing: border-box; }
}

@layer tokens {
  :root { --color-primary: #0891b2; }
}

@layer base {
  body { font-family: var(--font-sans); }
}

@layer components {
  .btn { /* component styles */ }
}

@layer utilities {
  .sr-only { /* utility overrides */ }
}
```

### 4. Custom Properties Strategy

```css
/* Component-scoped defaults */
.card {
  --card-padding: var(--spacing-4);
  --card-radius: var(--radius-md);

  padding: var(--card-padding);
  border-radius: var(--card-radius);
}

/* Override via inline or parent */
.compact-layout .card {
  --card-padding: var(--spacing-2);
}
```

## Alignment Reference

### Grid Alignment Properties

```css
.grid {
  /* Align entire grid within container */
  justify-content: center;  /* Horizontal */
  align-content: center;    /* Vertical */

  /* Align all items within cells */
  justify-items: stretch;   /* Horizontal */
  align-items: stretch;     /* Vertical */

  /* Shorthand */
  place-content: center;    /* justify + align content */
  place-items: center;      /* justify + align items */
}

.item {
  /* Individual item alignment */
  justify-self: start;
  align-self: end;
  place-self: start end;
}
```

### Alignment Values

| Value | Behavior |
|-------|----------|
| `start` | Align to start edge |
| `end` | Align to end edge |
| `center` | Center alignment |
| `stretch` | Fill available space (default) |
| `space-between` | Distribute with edges flush |
| `space-around` | Equal space around items |
| `space-evenly` | Equal space including edges |

## Responsive Patterns

### Without Media Queries

```css
/* Fluid grid */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 300px), 1fr));
}

/* Fluid typography */
.heading {
  font-size: clamp(1.5rem, 1rem + 2vw, 3rem);
}

/* Fluid spacing */
.section {
  padding: clamp(var(--spacing-4), 5vw, var(--spacing-12));
}
```

### With Container Queries (Preferred)

```css
.widget-container {
  container-type: inline-size;
}

@container (width < 300px) {
  .widget { flex-direction: column; }
}

@container (width >= 300px) {
  .widget { flex-direction: row; }
}
```

### Media Queries (When Necessary)

```css
/* Viewport-dependent layout only */
@media (min-width: 768px) {
  .app-layout {
    grid-template-areas:
      "sidebar header"
      "sidebar content";
    grid-template-columns: 240px 1fr;
  }
}
```

## Performance Guidelines

1. **Avoid layout thrashing**: Batch DOM reads/writes
2. **Minimize repaints**: Use `transform` and `opacity` for animations
3. **Contain layouts**: Use `contain: layout` for isolated components
4. **Reduce specificity**: Flat selectors parse faster

```css
/* Layout containment for performance */
.card {
  contain: layout style;
}
```

## Accessibility Considerations

### Visual vs DOM Order

```css
/* ⚠️ Grid can reorder visually but not in DOM */
.item { order: -1; }  /* Keyboard/screen reader order unchanged */
```

**Rule:** Never use CSS ordering to restructure content meaning.

### Focus Indicators

```css
:focus-visible {
  outline: 2px solid var(--color-ring);
  outline-offset: 2px;
}
```

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

## Decision Matrix

### Layout Decisions

| Layout Need | Solution |
|-------------|----------|
| Page structure | Grid with template areas |
| Card grid | `auto-fit` + `minmax()` |
| Aligned nested content | Subgrid |
| Component responsiveness | Container queries |
| Single-axis distribution | `grid grid-flow-col auto-cols-max` |
| Centering | `grid place-items-center` |
| Complex alignment | Grid with line placement |
| Vertical stack | `grid gap-*` |
| Horizontal list | `grid grid-flow-col auto-cols-max gap-*` |
| Space between (left/right) | `grid grid-cols-[1fr_auto]` or `grid grid-cols-[auto_1fr_auto]` |
| **Independent row wrap** | Flexbox `flex-wrap` (Grid cannot) |
| **Dynamic shrink below basis** | Flexbox `flex-shrink` (Grid cannot) |

### Styling Decisions

| Need | Solution |
|------|----------|
| Numeric value (size, spacing) | CSS variable from design tokens |
| Color value | Semantic color token (not primitive) |
| Spacing between siblings | Grid/Flex `gap-*` |
| Internal padding | `p-*`, `px-*`, `py-*` |
| Conditional state styling | `data-*` attribute + CSS |
| Dynamic position/size | Inline `style` (only option) |
| Static dimensions | Tailwind classes (`w-full h-full`) |
| Component style prop | Remove if only used for `100%` dimensions |

## Modern CSS Features (2024+)

### CSS Anchor Positioning

Position elements relative to other elements without JavaScript:

```css
/* Define anchor */
.trigger {
  anchor-name: --tooltip-anchor;
}

/* Position relative to anchor */
.tooltip {
  position: fixed;
  position-anchor: --tooltip-anchor;

  /* Position below the anchor */
  top: anchor(bottom);
  left: anchor(center);
  translate: -50% 0;

  /* Fallback positioning */
  position-try-fallbacks: flip-block, flip-inline;
}
```

**Use cases:** Tooltips, popovers, dropdown menus, annotations

### CSS @scope

Scoped styling without Shadow DOM:

```css
@scope (.card) to (.card__content) {
  /* Styles apply to .card but not descendants inside .card__content */
  p { margin-block: 0.5em; }
  a { color: var(--color-primary); }
}

/* Scoped to component boundary */
@scope (.component) {
  :scope { display: grid; }  /* Targets .component itself */
  .header { grid-area: header; }
}
```

### light-dark() Function

Automatic dark mode with single declaration:

```css
:root {
  color-scheme: light dark;
}

.card {
  background: light-dark(#ffffff, #1a1a1a);
  color: light-dark(#1a1a1a, #ffffff);
  border: 1px solid light-dark(#e0e0e0, #333333);
}
```

### @property (Typed Custom Properties)

Enable animation of CSS custom properties:

```css
@property --gradient-angle {
  syntax: "<angle>";
  initial-value: 0deg;
  inherits: false;
}

.animated-gradient {
  background: conic-gradient(from var(--gradient-angle), red, blue, red);
  animation: rotate 3s linear infinite;
}

@keyframes rotate {
  to { --gradient-angle: 360deg; }
}
```

### color-mix()

Mix colors in any color space:

```css
.button {
  --base-color: oklch(50% 0.2 240);

  background: var(--base-color);

  &:hover {
    /* 20% lighter */
    background: color-mix(in oklch, var(--base-color), white 20%);
  }

  &:active {
    /* 20% darker */
    background: color-mix(in oklch, var(--base-color), black 20%);
  }
}
```

### OKLCH Color Space

Perceptually uniform color space for consistent lightness:

```css
:root {
  /* OKLCH: lightness (0-100%), chroma (0-0.4), hue (0-360) */
  --color-primary: oklch(55% 0.25 240);     /* Vibrant blue */
  --color-primary-light: oklch(75% 0.15 240);
  --color-primary-dark: oklch(35% 0.25 240);

  /* Generate consistent palette by varying lightness */
  --gray-50: oklch(97% 0 0);
  --gray-100: oklch(93% 0 0);
  --gray-500: oklch(55% 0 0);
  --gray-900: oklch(15% 0 0);
}
```

**Benefits:**
- Consistent perceived brightness across hues
- Predictable color manipulation
- Better for accessibility (contrast calculations)

## Browser Support Strategy

```css
/* Progressive enhancement pattern */
.component {
  /* Baseline */
  display: flex;
  flex-wrap: wrap;

  /* Modern enhancement */
  @supports (grid-template-columns: subgrid) {
    display: grid;
    grid-template-columns: subgrid;
  }

  @supports (anchor-name: --test) {
    /* Use anchor positioning */
  }
}
```

## Border-Radius and Padding Alignment

**Rule: `padding >= border-radius` to prevent text clipping at corners.**

Descenders (`g`, `y`, `p`, `q`, `j`) clip when padding is less than border-radius.

| Border Radius | Min Padding | Example |
|---------------|-------------|---------|
| `rounded-md` (6px) | `p-1.5` (6px) | `py-1.5 rounded-md` ✅ |
| `rounded-lg` (8px) | `p-2` (8px) | `py-2 rounded-lg` ✅ |

**CSS variable escaping:** Use `var(--spacing-1\.5)` (escaped dot) in CSS, `p-1.5` in Tailwind.

---

## Code Review Checklist

### Before Committing CSS/TSX Changes

- [ ] **No hardcoded px/rem values** - All sizes use `var(--spacing-*)`, `var(--size-*)` etc.
- [ ] **No hardcoded colors** - All colors use semantic tokens like `var(--color-*)` or Tailwind equivalents
- [ ] **No hardcoded z-index** - Use `var(--z-index-*)` tokens
- [ ] **No margin utilities for spacing** - Replace `mt-*`, `mb-*`, etc. with grid `gap-*`
- [ ] **Grid over Flexbox** - Use `grid` always. Flexbox only for `flex-wrap` independent rows or `flex-shrink`
- [ ] **No unnecessary inline styles** - `style={{ width: "100%", height: "100%" }}` → `className='w-full h-full'`
- [ ] **Data attributes for states** - Not conditional class concatenation
- [ ] **No unnecessary style props** - Remove `style?: React.CSSProperties` if only used for full dimensions
- [ ] **CSS owns styling logic** - State-based styles defined in CSS via `&[data-*]`, not in JSX
- [ ] **Padding >= Border-radius** - Ensure padding is at least equal to border-radius to prevent text clipping

### Grep Commands for Validation

```bash
# Find hardcoded rem/px in CSS
grep -r '\d+\.\d*rem\|\d+px' packages/**/*.css

# Find margin utilities in TSX
grep -r 'm[tblrxy]-\|mt-\|mb-\|ml-\|mr-\|mx-\|my-' packages/**/*.tsx

# Find inline styles in TSX
grep -r 'style=\{\{' packages/**/*.tsx

# Find hardcoded z-index
grep -r 'z-\d\+\|z-\[\d' packages/**/*.tsx packages/**/*.css

# Find hardcoded colors
grep -r '#[0-9a-fA-F]\{3,6\}' packages/**/*.tsx packages/**/*.css

# Find flex usage (should be minimal - only flex-wrap or flex-shrink cases)
grep -r 'flex\s' packages/**/*.tsx apps/**/*.tsx | grep -v 'flex-wrap\|flex-shrink\|flexRender'
```

---

## References

### Grid vs Flexbox (Primary Sources)
- [MDN: Relationship of Grid layout with other layout methods](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_grid_layout/Relationship_of_grid_layout_with_other_layout_methods) - **Key source for Grid vs Flexbox decision**
- [MDN: Aligning items in CSS Grid layout](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Grid_layout/Box_alignment) - Baseline alignment, auto margins in Grid
- [MDN: Mastering wrapping of flex items](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_flexible_box_layout/Mastering_wrapping_of_flex_items) - Why flex-wrap is Flexbox-exclusive

### Grid Layout
- [MDN CSS Grid Layout](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Grid_layout)
- [MDN Subgrid](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Grid_layout/Subgrid)
- [CSS-Tricks Grid Guide](https://css-tricks.com/snippets/css/complete-guide-grid/)
- [Josh W. Comeau - Subgrid](https://www.joshwcomeau.com/css/subgrid/)

### Modern CSS
- [MDN Container Queries](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Containment/Container_queries)
- [MDN CSS Anchor Positioning](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_anchor_positioning)
- [MDN @scope](https://developer.mozilla.org/en-US/docs/Web/CSS/@scope)
- [OKLCH Color Picker](https://oklch.com/)
