# Testing

## Unit tests

```
python3 -m unittest
```

The tests use the standard library only. They build the example sets, render
the fragments on hand-written and built page trees, and check the data
checks, the output checks, the privacy of the log, the dates of both built-in
languages, the link preview image, the page script and the docs (every link
and anchor of `README.md` and `docs/` resolves, and the samples of the docs
pass the checks). The tests that need a real browser are skipped without
Chrome or Chromium, and the ones that need `ffmpeg` without it. A test also
keeps Cyrillic in the Russian files only: the Russian set of strings, the
Russian example set and its tests, and a few robustness tests that need
non-Latin input.

## Continuous integration

`.github/workflows/ci.yml` runs on every push and pull request (and by hand).
It uses no secrets and deploys nothing. The matrix is Python 3.10, 3.11, 3.12
and 3.13; third-party actions are pinned to a commit SHA; the permissions are
`contents: read`.

Each step and how to repeat it locally:

| CI step | Locally |
|---|---|
| repository hygiene: no tracked media (every file is checked, with no exceptions), no tracked build output, no line breaks in file names | `git -c core.quotePath=false ls-files \| grep -Ei '\.(png\|jpe?g\|webp\|gif\|avif\|mp4\|mov\|webm\|ico\|svg)$'` prints nothing |
| Chrome is on the runner and starts headless as an ordinary user, with its sandbox, as the build starts it (it prints its version and loads a blank page; when it is missing or does not start, the step fails with its output): the build renders the link preview image with it, and the tests with a real browser run after this step instead of being skipped | `google-chrome --version && google-chrome --headless=new --disable-gpu --dump-dom about:blank` |
| unit tests | `python3 -m unittest` |
| placeholder media (with `ffmpeg` installed when needed) | `python3 tools/gen_example_media.py` |
| validate and build the main example (with `SITE_NAME=Example` and `--allow-path /photos`: the photos link leads to a directory of the fictional site) | `python3 build.py validate && SITE_NAME=Example python3 build.py build --allow-path /photos --out path/to/dist` |
| validate and build the example without a venue and media | `python3 build.py build --data examples/data-venue-pending --media examples/media-none --out path/to/dist-pending` |
| validate and build the Russian example (it shares the media of the main one) | `python3 build.py validate --data examples/data-ru && SITE_NAME=Example python3 build.py build --data examples/data-ru --allow-path /photos --out path/to/dist-ru` |
| build the main example under a prefix, the layout of a real site | `SITE_NAME=Example python3 build.py build --base-path /invite --allow-path /photos --out path/to/site/invite` |
| the link preview tags of the main and Russian pages: `og:image` is `/assets/<mediaDir>/<hash>.jpg` (`/invite/assets/…` under the prefix), the file is in the output and is a JPEG of 1200×630 and at most 300 KB, there is nothing at `assets/og.*`, `og:site_name` is there, `og:url` is not, no `://` in any `<meta>`, and the title is a word of the language and the couple's names, the same in `<title>`, `og:title` and `og:image:alt` | `grep -o '<meta property="og:[^>]*>' path/to/site/invite/*/index.html` |
| check the output of every build: no `index.html`, `404.html`, `_headers` or `robots.txt`, no `*.json`, `*.map`, styleguide or preview files, as many `*/index.html` pages outside `assets/` as there are invitations | `ls path/to/dist`: only `assets` and the page directories |
| reproducibility: two builds in a row (the main example, `--allow-path /photos`) give the same checksums | build twice into different directories and compare the `sha256` of the files |
| the working tree stays clean | `git status --porcelain` |

Chrome on `ubuntu-24.04` is the `google-chrome` preinstalled on the runner
(the Google package in `/opt/google/chrome/`): the Ubuntu AppArmor profile
allows it user namespaces, so its sandbox works without `--no-sandbox` or a
`sysctl` change (Chrome for Testing or a container without user namespaces
would not start like that). Which window of the rendered cover fits long
names depends on the system font (DejaVu Sans on the runner, wider than the
macOS font), so the test checks the safe zone and that the widest window was
not needed, not one particular window.

The results are on the Actions tab of the repository.

## The styleguide

`styleguide.html` refers to `/assets/…` from the root of the site, so open it
through a server started **at the root of the repository**:

```
python3 -m http.server 8000             # http://localhost:8000/styleguide.html
```

It never reaches the output: every file named `styleguide.*` is skipped.

## Checking a restyle

- **The styleguide** shows a table of every token with its computed value
  (recomputed when the window width changes), the type scale, the layout, and
  the components in their states (hover, focus-visible, active, disabled).
  **Photo and video tiles** are shown as plain cards instead of pictures (the
  repository has no media): the ▶ badge, focus, hover, the duration and a
  single tile `.gallery--single`. The styleguide only describes a video in
  the viewer: the script makes the viewer, and the panel of a video is the
  browser's, with no styles or tokens of its own. Check the viewer with a
  video and a single tile in the proportion of the frame on a built page
  with a video (a page of the main example does).
- **The text size switch** of the styleguide (100 / 125 / 150 / 200 / 330 %)
  is a quick check that the layout holds at a large system text size. The
  real check is to enlarge the text in the settings of the browser or the
  system.
- **Widths** 360, 390, 768, 1024, 1440 and 1920 px, and a phone in landscape
  (740×360, say): no horizontal scrolling, no overlaps, no clipped text, and
  on a desktop the contents do not stretch across the whole width.
- **The collapse of the cover into the bar**, on a built page (the styleguide
  shows the bar collapsed only). Scroll the cover slowly: the text of the
  cover fades out by the `--cover-fade-end` share of the progress, the veil of
  the photo thickens to full, the bar fades in from `--cover-bar-fade-start`
  and sticks to the top when a strip of the cover's height is left; the layout
  does not shift. Check at 360 px and 1440 px, in landscape and at a text size
  of 200 % (the bar is taller, the names end with an ellipsis, the date is
  whole); a jump to an anchor (`#s-where`) puts the target below the bar, not
  under it; Tab through the whole page keeps the focus out from under the
  bar; the photo viewer lies over the bar. In Chrome CSS drives the progress
  (a scroll timeline). The path for browsers without timelines (iOS 18 and
  older) is checked on a copy of the build where the condition
  `(animation-timeline: --a) and (timeline-scope: --a)` in `assets/app.css`
  and `assets/app.js` is replaced with one that is always false, such as
  `(not (color: red))`: the script then writes the progress, and the view must
  be the same. With "Reduce motion" (in DevTools, Rendering →
  `prefers-reduced-motion`) the cover does not change and the bar appears in
  one step; without JavaScript there is no bar; printed from the middle of the
  page, the cover is unfolded and there is no bar.
- **The area above the bar**: see [below](#the-area-above-the-bar).
- **The raw values check**: the components must have none.

  ```bash
  python3 - <<'PY'
  import re
  src = open('assets/app.css', encoding='utf-8').read()
  start = src.count('\n', 0, src.rindex('   3. Base'))
  body = re.sub(r'/\*.*?\*/', lambda m: '\n' * m.group(0).count('\n'), src, flags=re.S)
  raw = re.compile(r'#[0-9a-fA-F]{3,8}\b|\b(?:rgb|rgba|hsl|hsla|oklch|color-mix)\('
                   r'|(?<![\w.#-])\d*\.?\d+(?:px|rem|em|ms|s|vw|vh|svh|dvh)\b')
  bad = [(n, l.strip()) for n, l in enumerate(body.split('\n')[start:], start + 1)
         if not re.search(r'@media|@container|@supports', l) and raw.search(l)]
  print(len(bad), 'lines with raw values in sections 3-8')
  for n, l in bad:
      print(' ', n, l)
  PY
  ```

  It looks at sections 3–8 without comments and skips the lines of `@media`,
  `@container` and `@supports` conditions, whose numbers are the documented
  exception. It prints `0 lines with raw values in sections 3-8`.

### The area above the bar

The Telegram in-app browser on iOS (with its floating "glass" header) and
Safari on iOS 26 put the page under their translucent header: the layout
viewport starts at its lower edge, but WebKit draws the scrolled contents of
the document above it too. It clips everything sticky and fixed at the
layout viewport, so neither a fill above the bar, nor a fixed strip, nor an
upward shadow covers that area. The solution is body scrolling on touch
screens instead of document scrolling
([templates.md](templates.md#on-touch-screens-the-body-scrolls)): the
contents are clipped at the edge of `body`, and above the viewport only the
canvas of `html`, in the colour of the bar, remains.

The check in Chrome is the mobile mode with touch (DevTools → Device Toolbar;
through the protocol, `Emulation.setTouchEmulationEnabled` and
`Emulation.setEmitTouchEventsForMouse`, which make `(pointer: coarse)` true):
`document.scrollingElement.scrollTop` and `window.pageYOffset` stay 0, while
`document.body.scrollTop` grows as the page scrolls. Without touch emulation
the document scrolls, and PageDown works right after the page loads. In both
modes the collapse of the cover behaves the same with both drivers (the
timelines, and the copy with the false condition above), a jump to an anchor
puts the target under the bar, the background does not scroll under the
viewer, and print is unchanged. The fill `.cover-bar::before` (the bar
continued upwards in its colour for `--viewport-height`) stays: on an
invitation page with body scrolling it goes beyond the edge of `body` and is
not visible, and the styleguide shows it in a clipping frame. The safe area
of a notch can be set in Chrome DevTools through the protocol
(`Emulation.setSafeAreaInsetsOverride`): the bar becomes taller by its size,
and the text stays in the lower strip.

The `theme-color` meta tag does not cover the strip inside the page: Safari
26 does not apply it and takes the colour of the system area itself (from the
bar and the page), and Safari 18 and Android Chrome paint only their own
interface with it. It is there for the browser interface and the canvas
beyond the edges of the page
([design-system.md](design-system.md#the-browser-colour)). The check in
Chrome: on an invitation page `<meta name="theme-color">` equals the computed
`--color-cover-veil`, and `getComputedStyle(document.documentElement).backgroundColor`
is the same colour; the styleguide has no such tag, and its `html` background
is transparent.

## On real devices

This cannot be checked automatically: it needs a real phone and real apps.

1. **Video**: playback, seeking, sound and full screen in iOS Safari, Android
   Chrome and the in-app browsers of messengers (Telegram, WhatsApp), where
   the link is opened most often. Point by point:
   - a tap on the tile opens the viewer, and the video **plays at once with
     sound**, not in full screen; a tap pauses, the track seeks; a swipe
     across the frame does not page, the arrows of the viewer do;
   - the full screen button: on an iPhone the system player opens, as
     expected; after "Done" the viewer is back and the panel is fine; closing
     the viewer stops the sound;
   - in Telegram and WhatsApp on an iPhone the video may open in the system
     player at once (a setting of the app); after leaving it the viewer must
     be there;
   - Android: "Back" in full screen leaves it, a second "Back" closes the
     viewer; turning the screen in full screen;
   - a video reached by paging does not start by itself and does not load
     before a tap; one tap on its frame or on ▶ starts it (once, with no
     instant pause); leaving a playing video cuts the sound;
   - without JavaScript (switched off in the Safari settings) the tile opens
     the video in the system player, and "Back" returns to the page;
   - VoiceOver and TalkBack: the tile reads as "Video", the viewer as "Video
     viewer", and after closing the focus is on the tile.
2. **The system text size**: "Settings → Display & Brightness → Text Size" on
   iOS (including "Larger Text") and "Font size" on Android: the page follows
   the setting without horizontal scrolling. Look at the countdown and the
   programme in particular: they change their layout to fit.
3. **A phone in landscape** on the cover, on a video tile and in the viewer:
   a portrait video is visible as a whole together with its panel.
4. **Forced darkening** in an in-app browser (the dark theme of a messenger):
   the page keeps its own theme.
5. **The link preview**, on the published site (the address is not given to
   the build: `og:image` is a path from the root and there is no `og:url`,
   [cli.md](cli.md#link-preview-options)):
   1. **Telegram on iOS and Android**: send the link to "Saved Messages": the
      site name (or the domain), "Invitation · <names>", the description;
      write down **whether the rendered cover shows and whether it is large**;
      no greeting of a guest; the cards of two guests are the same. The
      cache: after publishing, send the link to
      [@WebpageBot](https://t.me/webpagebot); old messages may keep the old
      card;
   2. **WhatsApp** (Android and iOS), **iMessage** and, if possible, **X**:
      the same. The main risk is the relative `og:image` and the missing
      `og:url`: write down for each messenger whether the image shows
      ([deploying.md](deploying.md#the-cost-of-link-previews));
   3. no image: check its weight and that `<prefix>/assets/<mediaDir>/….jpg`
      opens by its direct address; no title either: see whether the bot
      reaches the page at all (the bot's group in `robots.txt`, no `noindex`
      on `<prefix>/*`, bot protection of the host,
      [deploying.md](deploying.md)), and whether an old preview cache is
      showing;
   4. the "not found" page: a preview without names or image;
   5. the typeface of the names on the image: does it match the page on an
      iPhone (a matter of fonts,
      [design-system.md](design-system.md#the-link-preview-image-and-fonts)).
6. **Map buttons**: do the links open in the installed map apps.
7. **The calendar**: is the event added by the "Add to calendar" button on
   iOS and Android.
8. **Event tabs** on the page of a guest with several events:
   - the current tab is selected: the guest's primary event until it is over,
     then the next one, after all of them the last one; past events have the
     "past" mark, the one that is on "happening now" (check on the day, or by
     changing the phone's clock);
   - a tap on a tab shows its card, and from then on the tabs do not switch
     by themselves;
     at a system text size of 200 % the tabs stack in a column;
   - on a desktop with a keyboard: Tab reaches the selected tab, the arrows
     (round the list), Home and End switch tabs, the next Tab goes into the
     card; VoiceOver and TalkBack read "tab, selected" and the mark.
9. **The "not found" page** on the host itself: the root and an address that
   is surely wrong give the same page.
10. **The collapse of the cover into the top bar**, on an iPhone with iOS 26
    (CSS drives it there) and with iOS 17 or 18 (the script drives it), in
    Safari and in the Telegram in-app browser, and in Android Chrome:
    1. open an invitation (preferably with a photo on the cover): the text of
       the cover reads well, the bar is not visible;
    2. scroll slowly: the photo sinks into the veil, the names and the date
       fade; when a strip of the cover is left, it holds "Names · date", the
       bar sticks to the top and stays there; no jumps or flicker;
    3. the same with quick flings: at the end of a fling the bar is in place;
       scrolling up unfolds the cover again;
    4. turn the phone in the middle of the page: the bar is at the top, no
       wider than the screen, not under the notch; on iOS 26 look at how
       Safari tints the status bar under the bar;
    5. tap the status bar (scroll to the top): the cover is unfolded and the
       bar is not visible. `body` scrolls the page, and iOS scrolls only the
       document itself on this tap: if it does not work, write it down
       (item 12);
    6. open a photo of a gallery: the viewer is over the bar; after closing,
       the bar is in place;
    7. "Accessibility → Motion → Reduce Motion": the cover does not change on
       scroll, and the bar appears at once when the cover is gone;
    8. the largest system "Text Size": the bar is taller, the names end with
       "…", the date is whole; in landscape the bar is noticeably taller
       (about a fifth of the screen): judge whether it is in the way;
    9. **the top edge after the collapse**, on an iPhone with iOS 26 and with
       iOS 18, in Safari and in the Telegram in-app browser: between the top
       edge of the screen and the bar there is no strip through which the
       scrolling text of the page shows; the whole area above the bar (the
       status bar, the notch, the Telegram header) is in the colour of the
       bar, also on a page with a photo on the cover and at the end of a
       quick fling. On a cover with a photo the photo does not vanish before
       the bar has appeared. The Telegram header itself is a little lighter
       and more neutral than the bar: that is its material, not a defect of
       the page ([design-system.md](design-system.md#the-browser-colour)).
11. **The colour above the page and beyond its edges**
    ([design-system.md](design-system.md#the-browser-colour)):
    1. **Telegram on iOS**: open an invitation from a chat. Expected: pulling
       the page down past the top edge while the cover is unfolded, and up
       past the bottom edge, opens an area in the colour of the bar. Above the
       collapsed bar, under the Telegram header, there is **no** text of the
       page, only the colour of the bar (`body` scrolls,
       [above](#the-area-above-the-bar)); check with the Telegram header
       expanded and collapsed (scroll down and up), and note the iOS and
       Telegram versions. The header itself is a little lighter and more
       neutral than the bar: its colour is Telegram's (a glass material that
       reads neither `theme-color` nor the page background), a known limit
       that cannot be fixed;
    2. **Telegram on Android**: the same. Expected: pulling past an edge shows
       the colour of the bar; the top bar of the Telegram browser is in the
       colour of its theme (with the adaptive colour on, in the colour of the
       cover bar);
    3. **Android Chrome**: the address bar and the status bar take the colour
       of the bar both with the cover unfolded and collapsed; pulling past an
       edge shows the colour of the bar;
    4. **the "not found" page** (the root of the site): an address bar of the
       usual colour and a white background beyond the edges.
12. **Body scrolling instead of the document on touch screens**
    ([templates.md](templates.md#on-touch-screens-the-body-scrolls)): side
    effects that headless Chrome does not show; write each down as it is,
    with the version of iOS or the browser (on a desktop the document
    scrolls):
    1. **Safari on an iPhone** (iOS 18 and 26): does the address bar (the tab
       bar) collapse on scrolling down? Safari collapses it on scrolling of
       the document itself, so it probably stays expanded; the scrolling is
       smooth all the same, with momentum and the rubber band at the edges;
    2. **Android Chrome**: the same about the address bar;
    3. **a tap on the status bar** of an iPhone: does it scroll to the top
       (item 10.5)?
    4. **the position after a reload** of the page and after "Back" from
       another page (maps, calendar): the browser restores only the scrolling
       of the document by itself, so after a reload the page probably opens
       at the top; "Back" from the page cache (usually Safari) keeps the
       position;
    5. **the photo viewer**: while it is open, the page under it does not
       scroll, neither by finger nor by rubber band; after closing it is at
       the same place;
    6. **a desktop with a keyboard** (Chrome, Safari, Firefox): right after
       the page opens, without a mouse click, the space bar, PageDown, the
       arrows and End scroll the page; a reload keeps the position;
    7. **mixed devices**: the main pointer decides the mode (`pointer`): a PC
       with a touch screen and a mouse probably scrolls the document; an iPad
       with a keyboard (and a trackpad) scrolls `body`. On an iPad with a
       keyboard check the space bar and the arrows right after the page
       opens: if they do not scroll until the page is touched, write it down.
