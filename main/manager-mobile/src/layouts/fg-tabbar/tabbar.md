# Tab bar strategies

The template supports four tab bar strategies:

- **0 — No tab bar:** one page entry point with no bottom bar, useful for temporary campaign pages.
- **1 — Native tab bar:** uses `switchTab` and caches tab pages.

  - Advantages: native rendering appears first; page state is cached.
  - Limitations: selected/unselected states use two image sets. Changing colors requires different images or an icon font.
- **2 — Cached custom tab bar:** uses `switchTab` and caches tab pages. A third-party UI tab bar replaces the hidden native bar.

  - Advantages: arbitrary SVG icons, easy text-color changes, cached state, and custom animations.
  - Limitation: the tab bar may flicker on the first tap.
- **3 — Uncached custom tab bar:** uses `navigateTo`, does not cache tab pages, and uses a third-party UI tab bar.

  - Advantages: arbitrary SVG icons, easy text-color changes, and custom animations.
  - Limitations: the tab bar may flicker on the first tap; page state is not cached.

Custom animations must be implemented separately; this template does not provide them.
