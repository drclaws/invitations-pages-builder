# Design system

The whole look of the pages is set by **design tokens**: named CSS custom
properties in one place, section 1 of `assets/app.css`. The components
(sections 3–8 of the same file) use only tokens, `calc()` over them and
keywords; there are no raw values in them. The tokens are the default theme:
a neutral system font and a grey-blue palette with at least WCAG AA contrast.
Changing the palette, the fonts, the sizes or the proportions is a change of
section 1 alone, with no change to the markup or the scripts.

`app.css` is split into numbered sections: 1 Tokens, 2 Fonts, 3 Base,
4 Layout primitives, 5 Components, 6 Page layout, 7 Motion & reveal,
8 Gallery & lightbox. The styleguide (`styleguide.html`) shows every token
with its computed value and every component in its states
([testing.md](testing.md#the-styleguide)).

## How to restyle

1. **Section 1 of `app.css`**: the values of the tokens (the mobile/desktop
   pairs where there are pairs, [below](#tokens-pairs-and-derived-values)).
2. **The numbers in the `@media` and `@container` conditions**, when the
   matching threshold tokens change ([Layout thresholds](#layout-thresholds)).
3. **Fonts**: the files in `assets/fonts/` and the `@font-face` block of
   section 2 ([Local fonts](#local-fonts)).
4. **The theme**: `color-scheme` is `only light` both in the tokens and in
   the `<meta name="color-scheme">` tag of `template.html` and
   `styleguide.html`; for a dark theme change both together with the
   colours. `prefers-color-scheme` is used nowhere: the page has one fixed
   theme and does not react to the forced darkening of in-app browsers.
5. **The derived formats** need nothing by hand: the icon, the neutral link
   preview image, the browser colour (`theme-color`) and the placeholder
   pictures of the examples come from the same tokens, and the link preview
   image is a snapshot of the same cover, so restyling the cover changes it
   too (adjust the frame in `assets/preview.css` if needed). Rebuild the site,
   and regenerate the example pictures
   (`python3 tools/gen_example_media.py`).
6. **The styleguide**, when a token or a component is added. The styleguide
   reads the list of tokens from `app.css` itself; the component demos are
   written as markup.
7. **The tests**: `python3 -m unittest`. Some of them know about the design
   system: the gallery styles have no raw values, the layout threshold in a
   condition matches its token, the image generator reads the palette, and no
   styleguide file reaches the output.

How to check the result is in [testing.md](testing.md#checking-a-restyle).

## Tokens: pairs and derived values

A parameter that may differ between a phone and a desktop is set by a
**pair** of tokens, and the components use only the **derived** token
without a suffix:

```css
--text-2xl-mobile: 30;     /* a number: px at a 16px font size */
--text-2xl-desktop: 42;
--text-2xl: clamp(…);      /* this is what the components read */
```

A derived token comes about in one of two ways:

- **smooth interpolation** with `clamp()` between the reference widths
  `--vw-min` (360) and `--vw-max` (1440), for sizes, spacing, widths and the
  distances of motion. The values of a pair are unitless numbers, because
  `calc()` cannot divide a length by a length; the formula turns them into a
  length. **The order within a pair is free**: the mobile value may be larger
  than the desktop one, since the bounds of `clamp()` are the `min()` and
  `max()` of the pair;
- **an override at the layout breakpoint**, in the `@media (min-width: 48em)`
  block at the end of section 1. This is for values that cannot be
  interpolated: the number of columns (`--grid-columns`, `--gallery-columns`,
  `--gallery-columns-venue`), the proportions of images (`--ratio-photo`,
  `--ratio-gallery`, `--ratio-scheme`) and the share of the screen height
  the cover takes (`--cover-height-ratio`).

Parameters without a pair (colours, radii, shadows, durations, line heights)
can be overridden in the same `@media` block when needed.

To change a parameter, change **the values of the pair**, not the formula of
the derived token.

## Units

One question decides the unit of each token: should the value grow when a
person enlarges the text in the system or the browser?

| Unit | What is set in it | Why |
|---|---|---|
| `rem` | the type scale, container widths, icon size, the limit of a countdown cell, the `@container` thresholds | the line length and the icon-to-label proportion hold at any text size |
| `rem` capped by the window width | spacing and gaps: `--space-*`, `--space-section`, `--container-gutter`, `--grid-gap`, `--countdown-gap` | on a wide screen the spacing grows with the text, and on a phone it does not eat the width: `min(<formula in rem>, mobile / --vw-min * 100vw)` |
| `px` | hairlines and borders, the focus ring, radii, shadows, `--tap-min`, the distances of motion | physical values: a 44 px tap target is an accessibility requirement, not a style, and has no reason to grow with the text |
| `em` / `ch` | letter spacing, widths "in characters" | they follow the font of the element itself |

At the default text size and a window of at least `--vw-min` every formula
gives exactly the numbers of its pair.

Two limits on the values of pairs keep the formulas working as intended:

- **type**: the larger value of a pair is at most 2.5 times the smaller one,
  or a 200 % browser zoom would not double the text;
- **capped spacing**: the mobile value is above 0 and the desktop value at
  most 4 times the mobile one, or the cap would apply even at the normal
  text size.

## The tokens

The styleguide lists every token with its computed value and groups them by
its own rules, a little finer than the table below (for example, the grid
has a group of its own apart from the countdown tokens, and
`--gallery-ribbon-item-size`, `--lightbox-scroll-gap` and the top bar tokens
`--cover-bar-*` and `--cover-fade-end` fall under "Other"). The set is the
same, not the names of the groups.

| Group | Tokens | Purpose | Mobile/desktop pairs |
|---|---|---|---|
| Reference widths | `--vw-min`, `--vw-max`, `--fluid`, `--bp-layout` | the bounds of interpolation, the multiplier of the formulas, the layout breakpoint | — |
| Colours | `--color-bg`, `--color-surface`, `--color-surface-sunken`, `--color-text`, `--color-text-muted`, `--color-accent`, `--color-accent-hover`, `--color-on-accent`, `--color-line`, `--color-line-strong`, `--color-focus`, `--color-overlay`, `--color-on-overlay`, `--color-focus-on-overlay`, `--color-overlay-control`, `--color-overlay-control-hover`, `--color-disabled-bg`, `--color-disabled-text`, `--color-shadow` | roles, not values: background, surfaces, text, accent, lines, focus, the overlay of the viewer, the disabled state | — |
| Fonts | `--font-body`, `--font-heading`, `--font-mono`, `--font-weight-body/-medium/-heading`, `--line-height-body/-tight/-heading`, `--tracking-body/-heading/-caps` | typefaces by role, weights, line heights, letter spacing | — |
| Type scale | `--text-xs`, `--text-sm`, `--text-base`, `--text-md`, `--text-lg`, `--text-xl`, `--text-2xl`, `--text-display` | eight steps from a small caption to the cover | all |
| Spacing | `--space-3xs` … `--space-2xl`, `--space-section`, `--flow-space` | the spacing scale, the space between sections, the vertical rhythm inside a block | all but `--flow-space` |
| Container | `--container-text`, `--container-wide`, `--container-gutter` | the width of the text column and of the wide container, the side margins | all |
| Grid and countdown | `--grid-columns`, `--grid-gap`, `--gallery-columns`, `--gallery-columns-venue`, `--gallery-ribbon-item-size`, `--countdown-columns`, `--countdown-columns-narrow`, `--countdown-columns-stack`, `--countdown-inline-min`, `--countdown-stack-max`, `--countdown-gap`, `--countdown-cell-min`, `--countdown-cell-max` | the number of columns and the gaps; the share of the width of a gallery ribbon item; the layout and thresholds of the countdown | the columns and gaps of the grid and the galleries, `--countdown-gap`, `--countdown-cell-max` |
| Radii, shadows, lines, focus | `--radius-sm/-md/-lg/-pill/-round`, `--shadow-sm/-md/-lg`, `--line-width-hairline`, `--line-width`, `--line-width-thick`, `--focus-ring-width`, `--focus-ring-offset`, `--focus-ring-offset-inset`, `--focus-ring-inset-halo`, `--opacity-disabled` | shape and outlines; the focus ring, including the inner one (where `overflow` would clip the outer one) | — |
| Proportions and framing | `--ratio-photo`, `--ratio-gallery`, `--ratio-scheme`, `--ratio-video`, `--ratio-og`, `--image-focus` | the `aspect-ratio` of the components and the focal point of a frame (`object-position`) | `--ratio-photo`, `--ratio-gallery`, `--ratio-scheme` |
| Screen height, cover, media | `--viewport-height`, `--viewport-height-dynamic`, `--cover-height-ratio`, `--cover-min-height`, `--media-max-height-ratio`, `--media-max-height`, `--cover-distance` | `100vh` with `100svh`/`100dvh` where they exist; the height of the cover; the height limit of media | `--cover-height-ratio`, `--cover-distance` |
| The cover photo | `--color-cover-veil`, `--color-cover-text`, `--cover-veil-opacity` | the colour of the veil over the photo (the cover colour), the colour of all the text on the photo, the opacity of the veil: 0.6 gives the text a contrast of 5.4:1 even on a black frame, and below 0.55 it drops under 4.5:1 (the calculation is in the comment at the token; redo it for a new palette) | — |
| The top bar | `--cover-bar-padding-block`, `--cover-bar-size`, `--cover-bar-block-size`, `--cover-fade-end`, `--cover-bar-fade-start` | the bar the cover collapses into: the padding of its line; its height (a `--text-base` line with padding, at least `--tap-min`); the full height with the top safe area (an anchor target stops below it too); the share of the collapse progress by which the cover text fades out, and from which the bar fades in. The bar's background is the veil colour `--color-cover-veil`, and the same colour continues the bar upwards for `--viewport-height` (the area above the stuck bar, with no token of its own) | — |
| Motion | `--duration-fast/-base/-slow`, `--ease-out`, `--ease-in-out`, `--reveal-distance`, `--reveal-stagger`, `--hover-scale` | durations, curves, the distance and delay of the reveal of blocks | `--reveal-distance` |
| Accessibility and layers | `--tap-min`, `--z-base/-raised/-sticky/-overlay/-lightbox`, `--safe-inset-*` | the minimum tap target of 44 px, the order of layers (`--z-sticky` is the top bar: above the page, below the dialogs), the safe areas of the screen | — |
| Components | `--card-padding`, `--btn-padding-block/-inline`, `--divider-thickness`, `--icon-size`, `--schedule-time-max`, `--schedule-body-min`, `--schedule-inline-min`, `--events-tab-min`, `--lightbox-scroll-gap`, `--media-play-size`, `--media-play-icon-size` | the card, the button, the divider, icons, the programme (the time label takes everything but `--schedule-body-min` for the description, and at least `--schedule-time-max`), the event tabs (all in a row while each gets `--events-tab-min`, otherwise all in a column), the viewer; the diameter of the ▶ badge of a video tile and the size of its triangle | `--icon-size` |

`--ratio-video`, `--ratio-og`, `--countdown-columns`, `--tap-min` and
`--safe-inset-*` are not style decisions: they are a data format, an
accessibility requirement and platform parameters. They need no change.

Motion is switched off as a whole at the level of the tokens: in
`@media (prefers-reduced-motion: reduce)` the durations and distances are set
to zero once, in section 1, and the components know nothing about that media
query. The exceptions are the safeguards of section 7: the reveal of blocks
and the cover animation are switched off, and the collapse of the cover into
the bar happens in one step (the scroll progress does not depend on the
durations).

## Layout thresholds

`var()` does not work in the conditions of `@media` and `@container`, so the
thresholds are **written twice in the file**: as a token (which the
styleguide reads and a person goes by) and as a number in the condition
itself. **When a token changes, change the number in the condition too**:
every condition has a comment naming the token it must match.

| Threshold | Token | Where the condition is | What changes |
|---|---|---|---|
| Layout breakpoint | `--bp-layout: 48em` | `@media (min-width: 48em)` at the end of section 1; `@media not all and (min-width: 48em)` in section 8 | one column becomes two, the proportions of images, the share of the cover height; the gallery ribbon is on mobile only |
| Countdown in a row | `--countdown-inline-min: 19.5rem` | `@container (min-width: 19.5rem)` in section 5 | four cells in a row instead of 2×2 |
| Countdown in a column | `--countdown-stack-max: 9rem` | `@container (max-width: 9rem)` in section 5 | one column at a very large text size |
| Programme | `--schedule-inline-min: 18.5rem` | `@container (max-width: 18.5rem)` in section 6 | the time goes above the description instead of to its left |

`@container` measures not the window but the room a component gets: `.container`
and the grid items (`.grid > *`, section 4) are containers. So the countdown
and the programme look right both in a narrow column of a two-column section
and at full width. A browser without `@container` shows the countdown as 2×2
and the programme in a row.

`48em` in a media query is 768 px at the default browser text size; `em` in a
`@media` condition is relative to the browser's **initial** text size, so with
enlarged text the two columns arrive later, when there really is room for
them.

## The system text size

The page **does not set** the font size of the root: the reader does, with a
browser setting or, on a phone, the system text size.

- **Chromium (Android and in-app browsers of messengers)**: the meta tag
  `<meta name="text-scale" content="scale">` in `template.html` and
  `styleguide.html`;
- **iOS and iPadOS**: a rule in section 3,
  `@supports (font: -apple-system-body) and (-webkit-touch-callout: default) { :root { font: -apple-system-body; } }`.
  It is the only way to get the system "Text Size" setting (Dynamic Type);
  the `-webkit-touch-callout` condition leaves out Safari on macOS, where the
  same style would give the root 13 px. At the standard setting `1rem` is
  17 px on iOS and 16 px in other browsers.

What not to do:

- **set the font size of the root in pixels** (`html { font-size: 16px }`):
  it cancels the system setting and breaks the whole scale;
- **put font properties on `html`**: the shorthand `font: -apple-system-body`
  resets the typeface, the weight and the line height of `:root`, so all of
  them are set on `body` from the tokens and are not inherited from the root;
- remove `-webkit-text-size-adjust: 100%` from `html`.

## The colour format

Colours are read not only by the browser but by the build too: the icon and
the neutral link preview image are drawn from the tokens, and the colour of
`--color-cover-veil` becomes the colour of the browser interface above the
page ([below](#the-browser-colour)). The build understands:

- `#rgb`, `#rgba`, `#rrggbb`, `#rrggbbaa`;
- `rgb(…)` and `rgba(…)`, with commas or in the form `rgb(14 16 18 / 78%)`;
- `var(--another-token)`, chained and with a fallback.

It does not understand `hsl()`, `oklch()`, `lab()`, `color-mix()` or
**named colours** (`white`, `tomato`). Such a value in any of the colour
tokens `--color-bg`, `--color-surface`, `--color-surface-sunken`,
`--color-text`, `--color-text-muted`, `--color-accent`, `--color-on-accent`,
`--color-line` and `--color-cover-veil` (including a token it refers to with
`var()`) stops the build with a clear message:

```
error: assets/app.css: design token '--color-accent': unsupported colour 'oklch(70% 0.15 60)' (expected #rgb, #rrggbb, #rrggbbaa, rgb() or rgba()) (the colour of the browser interface, the icon and the link preview image are taken from the design tokens)
build: failed
```

The tokens are read on every build, even when the icon and the preview image
are your own: the browser colour is always needed.

The other colour tokens (overlays, shadows, disabled states) are not read by
the build, but keeping the whole set in one notation is wiser. Translucent
colours are fine: the build blends them onto the background (`--color-bg`,
and that onto white).

Only the top-level `:root` rules are read; values overridden inside `@media`
are invisible to the build, so the images and the browser colour always take
the base values.

## The icon, the link preview image and the browser colour

The icon and the link preview image are drawn on every build and are not kept
in the repository:

- `favicon.svg` is a rounded square of `--color-accent` with a mark of
  `--color-on-accent`;
- **the link preview image is the cover** of the site, captured by headless
  Chrome ([data-format.md](data-format.md#the-rendered-cover)). The preview
  page is `preview.html` with the same cover fragment and `app.css`, plus
  `assets/preview.css` (the cover exactly in the frame, the text in the
  central square, no top bar). Chrome starts with a profile in a temporary
  directory (`TMPDIR`) and no network access: the page and its files are
  served from `127.0.0.1`, and Chrome is driven through its debugging
  protocol over a pipe (`--remote-debugging-pipe`), without any third-party
  package. The page scripts are off, `prefers-reduced-motion` is `reduce`,
  there are no scroll bars, and the capture repeats until two in a row match.
  It is one render per build, about 1–2 s;
- `og.png`, 1200×630, is a neutral composition of `--color-bg`,
  `--color-surface`, `--color-line`, `--color-text` and `--color-accent`,
  with no names or dates: for a site without a cover and for a build with
  `--no-link-preview-image`.

The icon and the neutral image live in `assets/` of the output, and the pages
refer to them as `<base-path>/assets/favicon.svg` and
`<base-path>/assets/og.png` (the fields `faviconPath` and `ogImage`); the
rendered cover lives in the media directory,
`<base-path>/assets/<mediaDir>/<hash>.jpg`. The preview page gets the same
addresses as the guests' pages, `{{assetsPath}}/app.css` and
`{{assetsPath}}/preview.css`, and renders the same under any `--base-path`.

To look at them without building the site:
`python3 tools/gen_assets.py --out path/to/dir`. To use your own files, put
them into the media directory
([data-format.md](data-format.md#your-own-icon-and-preview-image)).

PNG files are written by an encoder of the standard library (`zlib`, a fixed
compression level, no metadata or time stamps). With one Python version the
result is byte-identical; another `zlib` version may give another file size.
The picture looks the same, but two `og.png` files made by different Python
versions may differ in bytes.

### The link preview image and fonts

Without custom fonts the rendered cover is drawn in the system font of the
machine that runs the build: on a Mac as on an iPhone, on a Linux runner in
another typeface. With local `woff2` files ([below](#local-fonts)) the image
picks them up by itself and looks the same everywhere. On one machine with
one Chrome version two builds give a byte-identical image; across machines
and Chrome versions not necessarily.

### The browser colour

Everything the browser paints above the page and beyond its edges takes the
colour of the collapsed cover bar, the `--color-cover-veil` token (equal to
`--color-surface` in the default theme). There are two places:

- `<meta name="theme-color" content="{{themeColor}}">` in `template.html`.
  The build fills in the value: it takes the token (following `var()`),
  reduces it to an opaque `#rrggbb` and puts it into the root field
  `themeColor`. The template has no colour of its own: change the token,
  rebuild;
- the canvas of the page:
  `html.invitation { background-color: var(--color-cover-veil) }` (section 3
  of `app.css`; `template.html` puts the `invitation` class on `<html>`).

Where it shows:

- **Android Chrome**: the address bar and the status bar take the colour of
  the bar, also while the cover is unfolded;
- **Safari on iOS 15–18**: the area under the status bar. Safari 26 does not
  apply the tag and takes the colour from the page itself, from the stuck bar
  and its fill ([testing.md](testing.md#the-area-above-the-bar));
- **pulling past the top and bottom edges** shows the canvas. WebKit takes
  the colour "under the page" from the background of `html` and `body` by
  default, in the in-app browsers of iOS too. At the bottom it is also the
  colour of the bar, not the white background of the page, by design;
- **the Telegram in-app browser**: on iOS it does not read `theme-color`,
  paints its floating "glass" header itself and puts the page under it.
  Under the header the canvas of the bar colour shows: `body` scrolls, so the
  contents of the page never get there. **A known limit**: the colour of the
  header itself is Telegram's, a translucent material over the canvas that
  reads neither `theme-color` nor the page background, so the header is a
  little lighter and more neutral than the bar; a match is not possible. On
  Android, with the adaptive browser colour off (the default), Telegram
  paints its top bar in the colour of its theme; with it on, it takes the
  colour from the page: `tg:theme-accent`, otherwise `theme-color`,
  otherwise the background of `body`.

When `html` has a background of its own, the background of `body` does not
spread to the canvas and paints only `body` itself. So the `body` of an
invitation page is at least as tall as the window
(`min-block-size: var(--viewport-height-dynamic)`): on a short page the area
under the contents keeps the page background, not the bar colour. The
styleguide (and a "not found" page of the site that uses `app.css`) has no
`invitation` class, so its canvas takes the colour of `body`.
`color-scheme: only light` does not affect the colour of the canvas: it is
set explicitly.

To give the top area another colour than the bar, change the token in
`site_colors_context` (`build.py`) and in the `html.invitation` rule
(`app.css`), one line each.

## Local fonts

External fonts are not allowed: the page makes no requests to other domains.
To use a font of your own:

1. put the `woff2` files into `assets/fonts/` (the directory exists);
2. uncomment the sample `@font-face` in section 2 of `app.css` and repeat it
   for every weight;
3. point `--font-heading` and/or `--font-body` of section 1 at the new
   family, keeping the system stack as the last fallback:
   `--font-heading: "Invitation Display", var(--font-body);`
4. adjust `--font-weight-*`, `--line-height-*` and `--tracking-*` if needed;
   the steps of the scale need no change.

`font-display: swap` is required: the text shows at once, with no blank
flash. The paths in `url()` are **relative**, as in the sample:
`url("fonts/invitation-display-400.woff2")`. A relative address is resolved
against the style sheet (`assets/app.css`) and works under any `--base-path`,
while an absolute `/assets/fonts/…` would suit only a build with
`--base-path /` (under a prefix the output check rejects it as an address
outside the output). The output check requires the file to exist.

The font must cover the letters of the language of the site: pick one with
the subsets it needs, such as Latin Extended or Cyrillic
([languages.md](languages.md#fonts)).
