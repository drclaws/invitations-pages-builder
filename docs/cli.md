# Command line

`build.py` has four commands; three helper scripts in `tools/` build the
examples and generate placeholder files. Everything runs on Python 3.10 or
newer with the standard library only.

- Chrome or Chromium renders the link preview image during `build`; without
  one, `build` stops with a hint; pass `--no-link-preview-image` to build
  without the image. `validate`, `token`, `links` and
  the tests do not need a browser (the tests that use one are skipped
  without it).
- `ffmpeg` is needed by one tool only, the generator of placeholder media
  for the examples, and for preparing a real video
  ([video.md](video.md)).

## Commands and options

```
python3 build.py build    [--data DIR] [--media DIR] [--out DIR] [--base-path PATH]
                          [--allow-path PATH]... [--site-name NAME] [--chrome PATH]
                          [--no-link-preview-image]
python3 build.py validate [--data DIR] [--media DIR]
python3 build.py token    [--prefix NAME]
python3 build.py links    --url URL [--data DIR]
```

| Option | Default |
|---|---|
| `--data` | `examples/data` next to `build.py` |
| `--media` | `examples/media` next to `build.py` |
| `--out` | `dist`, relative to the current directory |
| `--base-path` | `/`: the contents of `--out` are published at the root of the site |
| `--allow-path` | none: every local link of the pages leads to a file of the output |
| `--site-name` | the `SITE_NAME` environment variable, otherwise none (no `og:site_name` tag) |
| `--chrome` | the `CHROME` environment variable, otherwise the usual places: on macOS `/Applications/Google Chrome.app/…` and `Chromium.app`, on Linux `google-chrome`, `google-chrome-stable`, `chromium` or `chromium-browser` in `PATH` |
| `--no-link-preview-image` | the `LINK_PREVIEW_IMAGE=off` environment variable, otherwise the image is rendered |

`--data` and `--media`, when given, are relative to the current directory.
`python3 build.py <command> --help` describes every option.

## `build`

`build` checks the data and the media, builds the page tree of every guest,
renders the pages, writes the calendar files, puts everything into `--out`
and checks the finished result ([below](#the-output-and-its-checks)).
`--out` receives **the invitations only**: `<token>/index.html` for every
guest and `assets/`. There is no root page, no `404.html`, no `_headers` and
no `robots.txt`: those belong to the site that publishes the output
([deploying.md](deploying.md)). The build writes into a temporary directory
next to `--out` and replaces `--out` only when every check has passed, so a
failed build never leaves a half-written result.

```
python3 build.py build --data path/to/data --media path/to/media --out path/to/out
```

### The output directory

`--out` is replaced as a whole, so the build refuses an `--out` that is the
file system root, the home directory, the code, data, media or current
directory, or a parent of one of them. An existing directory is replaced only
when it is empty or holds the output of a previous build: an `assets/`
directory with `app.css` and `app.js` (every build writes them) and, next to
it, only directories named like a token with a single `index.html` inside
(files the operating system creates are ignored; a build of an empty
`invitations.json` has no such directories at all).

Anything else is never replaced, and the message suggests removing the
directory by hand or choosing another `--out`: pages without `assets/`,
`assets/` without `app.css` and `app.js`, the directory of a single page, and
a whole site (`index.html`, `404.html`, `_headers` or `robots.txt` at the top,
or pages one level deeper). For the last case the message points to
[publishing into a directory of a site](deploying.md#publishing-into-a-directory-of-a-site).

### `--base-path`: where the output is published

`--base-path PATH` is the path from the root of the site under which the
contents of `--out` are published. Every address in the output starts with
it: the styles, the script, the icon, `og:image`, media, posters and
calendar files are at `<PATH>/assets/…`, and a guest's page is at
`<PATH>/<token>/`. With `--base-path /` the addresses are exactly
`/assets/…`.

- The format is `/` or `/seg[/seg…]`, segments of `A–Z`, `a–z`, `0–9`, `_`
  and `-`; a trailing `/` is dropped; at most 200 characters.
- A bad value (no leading `/`, `//`, `.` or `..`, `%`, `?`, `#`, a scheme,
  spaces) is a usage error, exit code 2, and the value is not repeated in the
  message.
- The layout of `--out` does not depend on the path: only the addresses inside
  the pages change, and media, calendar files and the link preview image are
  the same bytes under the same names.

```
python3 build.py build --data path/to/data --media path/to/media --out path/to/site/invite --base-path /invite
```

### `--allow-path`: links to other pages of the site

`--allow-path PATH` names a directory of the site that the build does not
write: another page of the same site, such as the target of an
[event link](data-format.md#event-links). A link of the pages (`<a href>`,
`<area href>`) under `PATH` is allowed and is **not** looked up in the
output; whoever publishes the whole site makes sure the page is there. Only
links are allowed: a resource under `PATH` (`src`, `poster`, `srcset`,
`<link href>`, `url()` and `@import` in CSS) is still an error, and so is a
link whose path is not plain (an empty segment, `.` or `..`).

- The format is that of `--base-path`; a trailing `/` is dropped, repeats are
  ignored, and the option may be given several times.
- `PATH` must lie apart from `--base-path`: it may not be `/`, the base path
  itself, a directory above it or — unless the base path is `/` — a directory
  below it, because the addresses under the base path are files of the output
  and are checked against them.
- With `--base-path /`, `PATH` must not lead into the output either: its
  first segment is neither `assets` nor the token of an invitation (letter
  case aside). The first case is a usage error; the second is known only once
  the data is read, so it is exit code 1, and the message names no token.
- A bad value is a usage error: exit code 2, and the value is not repeated.
- Without the option, a link outside `--base-path` "points outside the
  output", and with `--base-path /` it "does not exist in the output"; both
  messages suggest `--allow-path`.
- `validate` has no such option: it is a property of publishing, not of the
  data.

The main example links each dinner guest to a page of photos of the
fictional site, `/photos/<token>/`, which the build does not write, so it is
built with:

```
python3 build.py build --data examples/data --media examples/media --out path/to/site/invite --base-path /invite --allow-path /photos
```

## `validate`

`validate` reads `site.json` and `invitations.json` and checks them against
[the data format](data-format.md): field types and required fields, **unknown
fields (an error with a "did you mean" hint)**, repeated keys, ids and
references between the registries, texts and placeholders, the language and
its strings, and the overrides of the invitations. It then builds the page
trees, which tells what at least one guest sees, and checks the media files
of those items only: that they exist, the letter case of their names,
symbolic links, size, the type of their contents and video properties
(codec, duration, `+faststart`).
The template is not parsed: `build` does that. Nothing is written.

It prints the language and the counts:

```
validate: language: en (default)
validate: OK - 8 invitation(s), 3 event(s), 8 section(s), 13 media file(s) (data: examples/data, media: examples/media)
```

Messages have the form `<site.json | invitation #N>: field '<path>'
<problem>`, for example:

```
error: site.json: unknown field 'coupleName' (did you mean 'coupleNames'?)
error: site.json: field 'sections[4].widgets[0].events[1]' refers to an unknown event 'diner' (did you mean 'dinner'?); known: ceremony, dinner, brunch
error: invitation #2: field 'greeting' is required
warning: site.json: media item 'story-3' is not shown on any page and its files are not published
```

The values of fields are never quoted. Ids from `site.json` are printed when
they follow [the id rule](data-format.md#ids). In the invitations a key is
printed only when it is a field name of the format or an id declared in
`site.json`; any other key is shown as `<unknown key>`, because a guest's key
may be somebody's name. The same rule holds for repeated keys in
`invitations.json`.

## `token`

`token` prints a random token (`secrets.token_urlsafe(16)`, 128 bits of
entropy) that passes [the token rules](data-format.md#tokens).

With `--prefix NAME` it prints a readable token `NAME-xxxx`: the tail is four
random characters (`secrets`) from lower-case Latin letters and digits
without the easily confused `0`, `o`, `1`, `l` and `i`:

```
python3 build.py token --prefix heron
heron-4tx9
```

Such a token is still easy to read out and type, yet guessing it from a list
of names and nicknames is about a million times harder than guessing a bare
`heron`. `NAME` uses the characters of a token (`A–Z`, `a–z`, `0–9`, `_`,
`-`) and is at most 195 characters long; otherwise the command exits with
code 2 and does not repeat the value.

## `links`

`links` prints one line per invitation, the greeting and the link separated
by a tab. `--url` is the address where the `--out` of the build is
published, that is the address of the site plus `--base-path`; a link is
`<URL>/<token>/`:

```
python3 build.py links --url https://example.org/invite
Dear Carol,	https://example.org/invite/0R-pnCqGFgrPOR5e-NluZw/
```

`--url` is `http` or `https`, without user information, query string or
fragment; a trailing `/` is dropped; a bad address is exit code 2, and the
address is not repeated in the message. The option `--base` is not accepted:
it is exit code 2 with a hint about `--url`, and nothing is printed.

This is the one command that prints personal data, so it **refuses to run in
CI**: when the environment variable `CI` or `GITHUB_ACTIONS` is set, it exits
with an error and prints nothing. The links are meant to be printed by hand,
on your own machine. Nothing is printed until the whole data set passes the
checks.

## Link preview options

The pages carry the tags that messengers read to show a card for a shared
link: a title, a description, an image and, when set, the **name of the
site** (`og:site_name`; messengers show it above the title, or the domain
without it). What goes into them is described in
[data-format.md](data-format.md#link-preview).

```
python3 build.py build --data path/to/data --media path/to/media --out path/to/out --site-name "Our invitations"
SITE_NAME="Our invitations" python3 build.py build --data path/to/data --media path/to/media --out path/to/out
```

The name is one line without control characters, at most 80 characters, with
no `//`. A bad `--site-name` is exit code 2, a bad variable exit code 1; the
value is never repeated, and the log only says
`build: link preview site name: set` or `not set`. An empty variable is the
same as none. In a deployment from CI the name fits a repository variable:

```yaml
env:
  SITE_NAME: ${{ vars.SITE_NAME }}   # empty: no og:site_name tag
```

The image is rendered by Chrome or Chromium (`--chrome PATH`, the `CHROME`
variable, or the usual places). `--no-link-preview-image`
(`LINK_PREVIEW_IMAGE=off`) uses a neutral image drawn from the design tokens
instead, and Chrome is not needed then.

The address of the site is **never given to the build**: every link in the
preview tags is a path from the root of the site (`og:image` is
`<base-path>/assets/…`), there is no `og:url`, and the output never holds an
absolute address of the site (the output checks reject any absolute URL in a
`<meta>` tag). The messenger knows the address of the page: it was sent the
link.

## Helper tools

### `tools/build_examples.py`

```
python3 tools/build_examples.py [--set data|data-ru|data-venue-pending|all] [--out DIR] [--port N]
                                [--chrome PATH] [--no-link-preview-image]
```

The script generates the placeholder media of the two main sets into
`examples/media/` (ignored by git; both sets share it), builds the sets with
`--base-path /` and `--allow-path /photos` into `dist/<set>/` (all of them by
default) and prints the build log, where the invitations are, the command to
serve them (`python3 -m http.server -d dist/<set> 8000`) and the address of
every page, `http://localhost:8000/<token>/`, with its greeting (the example
data is fictional; in CI the addresses and greetings are not printed).

The directory of a set is a ready root to serve; at `/` the built-in server
shows a directory listing, which is fine for fictional data. The main sets
show videos, so they need `ffmpeg`: without it they are not built, one line
each says why and the exit code is 1, while the set without media is built
all the same. Only the sets in `examples/` are accepted; a bad command line
is exit code 2. `--chrome` and `--no-link-preview-image` are passed on to
`build.py`. Nothing is written outside `--out` and `examples/media/`:
`git status` stays clean.

### `tools/gen_example_media.py`

```
python3 tools/gen_example_media.py [--data DIR] [--out DIR] [--css FILE]
```

Reads `site.json` and creates exactly the files of its media registry:
photos, the directions map (the image a place names in `directions`), the
cover background (the image of the cover's `background`), posters, tile
pictures (`thumb`) and videos. Each item has its own size: `width`/`height`
of the item, otherwise a size by role (the cover background is a landscape
2400×1600, a video a portrait 720×1280, a poster and a tile picture the size
of their video). The pictures are neutral cards with a grid and a frame
mark, so cropping and `object-position` are easy to see; the cover
background is dark with a light grid and marks in the corners and the
middle, to show the veil and the chosen `backgroundFocus`. The colours come
from the tokens of `app.css`; posters have no ▶ mark, since the tile draws
its own. Videos (`.mp4`, 5 s, a test pattern with sound) and `.jpg`/`.jpeg`
pictures need `ffmpeg`; without it the videos are skipped with a warning and
the exit code stays 0. The defaults are `examples/data` and `examples/media`.

### `tools/gen_assets.py`

```
python3 tools/gen_assets.py --out DIR [--css FILE]
```

Writes `favicon.svg` and the neutral `og.png` (1200×630) from the design
tokens, to look at them without building the site. The build draws them
itself; the neutral picture is used only when the site has no cover or the
link preview image is switched off. The rendered cover is made by `build`
only.

## Environment variables

| Variable | Effect |
|---|---|
| `SITE_NAME` | the name of the site in link previews, when `--site-name` is not given |
| `CHROME` | the browser that renders the link preview image, when `--chrome` is not given |
| `LINK_PREVIEW_IMAGE` | `off` (or `0`, `false`, `no`) does what `--no-link-preview-image` does; `on`, `1`, `true`, `yes` or empty renders the image; anything else is an error |
| `CI`, `GITHUB_ACTIONS` | when either is set (and not empty, `0` or `false`), `links` refuses to run and `build_examples.py` prints no addresses or greetings |
| `BUILD_DEBUG` | `1` (or `true`, `yes`) prints the traceback of an internal error |
| `TMPDIR` | where the temporary Chrome profile of the link preview image is made |

`BUILD_DEBUG` is for debugging on your own machine: a traceback may contain
values of the data, so it must not be switched on in CI.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | success |
| `1` | an error in the data, the template or the result of the build |
| `2` | a bad command line (an unknown command, a missing or bad option) |

## What the commands print

- **stdout** carries counts and paths only: how many invitations, events,
  sections and media files were checked, how many pages and calendar files
  were written, how many files were published, where the icon and the link
  preview image come from (for the rendered cover: size, weight, JPEG
  quality, window and Chrome version, but no names or dates), whether the
  site name is set, the language and the total size. When some tokens are
  shorter than 12 characters, `validate` and `build` add a summary with
  numbers only, never the tokens:
  `validate: tokens: 23 (20 shorter than 12 characters, see docs/data-format.md#tokens)`.
  It is neither a warning nor an error, so it goes to stdout; without short
  tokens there is no such line.
- **stderr** carries warnings (`warning: …`) and errors (`error: …`), and at
  the end a line such as `build: failed with N error(s)`.

There is no personal data in the output; this is a requirement of the code,
covered by tests:

- an invitation is named only by its number, its position in
  `invitations.json` counted from 1: `invitation #3`. Not a single character
  of a token is printed: a token may be short and readable, and even a part
  of one is a part of somebody's page address. A repeated token is reported
  with the numbers of both invitations:
  `invitation #7: duplicate token (same as invitation #2; …)`;
- the name of the media directory is replaced by `<mediaDir>` in paths, and
  the directory of a page by `…` as a whole, whatever the length of the
  token: `…/index.html` (any top-level entry of the output except `assets`
  and names with a dot). As soon as `invitations.json` is read, a path
  component that equals a token (letter case aside, as on a file system that
  ignores it) becomes `…` in any path of any message: `--data`, `--media`,
  `--out`, the temporary directory next to it, the file of an internal
  error: `dist/…/index.html`, `./…`, `dist/.….tmp-…`. A whole component is
  hidden, not a substring: a token inside a longer name
  (`--out dist/<token>_old`) stays visible, since the author of the command
  chose that name. The words of the messages are never masked, even when one
  equals a token (a `…` in place of a word would give the token away), and a
  path of one component is printed as `./name` to tell it from a word;
- before the data is read no token is known, so the check of `--out` shows
  neither its path (the messages just say `--out`: it may point at the
  directory of a page by mistake) nor the names of its entries: unexpected
  entries are only counted (`unexpected at the top: 1 directory and 3 other
  entries`), so `<token>.zip`, `<token>~` or `<token> copy` next to the pages
  give nothing away. A file system error at that step names the reason
  alone (`cannot inspect --out: Permission denied`), and so does an internal
  error before the data is read;
- the build never knows the address of the site, and the site name is not
  logged, only "set" or "not set";
- data values are never quoted: only field paths, field names, types and ids
  from `site.json`, and keys of the invitations only when they are field
  names of the format or declared ids;
- the names of media files are not printed in messages about the data: the
  field is named instead (`media.walk.file`).

## The output and its checks

```
out/                            --out, published under --base-path
  <token>/index.html            the page of an invitation (nothing else in the directory)
  assets/app.css, app.js, fonts/
  assets/favicon.svg            the icon (from the design tokens, or your own)
  assets/og.png                 the neutral link preview image, only for a site
                                without a cover or with --no-link-preview-image
  assets/<mediaDir>/<hash>.<ext>  media shown on at least one page
  assets/<mediaDir>/<hash>.jpg  the link preview image (the rendered cover, or your own)
  assets/<mediaDir>/<hash>.ics  a calendar file for every event at least one guest sees
```

The top level of `--out` holds only the page directories and `assets/`.
Every address inside is a path from the root of the site under
`--base-path`. Nothing else is published: no JSON with the data, no list of
tokens, no source maps, no styleguide files, no template fragments, no link
preview page or its `preview.css`, no `.md` files and no dot files.

**Media** are published under the hash of their contents
([data-format.md](data-format.md#the-media-directory-and-file-names)); when
the pages show no media, `assets/<mediaDir>/` holds only the calendar files.

### Calendar files

There is one calendar file per event **for the whole site**: three events
give three files, whatever the invitations. Only an event that at least one
guest sees gets a file; an event hidden from everybody gets none, and there
is no common file with all the events. The "Add to calendar" button that
leads to an event's file is only on the pages of the guests who see it.

- **The name** is the first 16 hex digits of `HMAC-SHA256(key, contents)`,
  where the key is the `sha256` of the tokens of all invitations, sorted and
  joined by line breaks: `assets/<mediaDir>/6f1c…e2a9.ics`. A plain hash of
  the contents would not do: the contents can be guessed (the title, time and
  place of the event), and such a name could be found by trying addresses on
  the site. With the key, computing the name requires **all** the tokens,
  and whoever knows them can open every page anyway. So the file of a hidden
  event is protected exactly as a guest's page, and that protection depends
  on the strength of the tokens: a short, guessable token weakens it too. A
  new invitation changes the names of all calendar files, which is harmless:
  the pages are rebuilt with them.
- **The contents** are one event (`VEVENT`). `SUMMARY`, the title of the
  calendar entry, is "couple names · event title", for example
  "Alice & Bob · Wedding dinner": the names are `coupleNames` from
  `site.json`, the separator is `ICS_SUMMARY_SEPARATOR` in `build.py`.
  `DTSTART` and `DTEND` are in UTC; `LOCATION` is "name, address" of the
  place once it is announced; `UID` is
  `sha256(mediaDir \n eventId \n start)[:32]@invitation`. Commas, semicolons
  and backslashes in the text are escaped, and lines longer than 75 bytes
  are folded. There is no guest data (greeting, notes, token) in the file, so
  one file serves everybody who sees the event. The couple's names are data
  of the whole site; outside the pages they are only in the calendar files,
  whose names are protected as described above.
- **`DTEND`** is the `end` of the event or, without one, the start plus six
  hours ([data-format.md](data-format.md#events)); it is the same for every
  guest.
- **When an event changes**, its contents change and so does the name of the
  file: the pages of the next build link to the new file, and the old one is
  gone from the output. A new title, couple names, end or announced place
  with the same start keep the `UID`. But `DTSTAMP` is constant and
  `SEQUENCE` grows only when the place is announced, so whether a guest's
  calendar updates the old entry when the event is added again depends on
  the calendar: some keep the old entry or create a second one. A new start
  gives a new `UID`: whoever added the event already gets a second entry and
  removes the old one themselves.

### What is checked

After writing, the build checks **the finished tree** and fails with a list
of problems if anything is wrong (the messages never quote the text of the
pages; at most 25 problems are listed):

- **contents**: only the expected files and directories. At the top,
  `assets/` and one directory per invitation, which holds only `index.html`
  (a calendar file there is an error); no files at the top. In `assets/`
  only the allowed file types (`.css`, `.js`, `.woff2`, `.ico`, `.txt`,
  images, `.mp4`) and of the subdirectories only `fonts/` and the media
  directory; in `assets/<mediaDir>/` exactly the published hash names of the
  media shown and of the calendar files (a file under its original name, an
  extra hash or an extra `.ics` is an error), and without them no such
  directory. `.json`, `.map`, `.py` and `.md` files are published nowhere;
  symbolic links are forbidden; the required files (pages, media, calendar
  files) are in place. The directory of a page is `…` in the messages: its
  name is a token;
- **size**: no file larger than **25 MiB** (the per-file limit of common
  static hosts);
- **HTML**: no template syntax and no comments left; no external resources,
  inline scripts or event handlers, embedded documents, CDATA or processing
  instructions; external links only to the three map services and only with
  `target` and `rel`; every local address lies under `--base-path` (otherwise
  it "points outside the output") and, without it, names an existing file of
  the build (the address `/`, the root of the site, is not part of the
  output), except `<a>`/`<area>` links under `--allow-path`, which are not
  looked up; no text that the parser sees as text but a browser might read as
  markup ([templates.md](templates.md#what-a-template-may-not-do));
- **CSS**: `url()` and `@import` point to existing local files; a relative
  address is resolved against the style sheet and works under any
  `--base-path`, an absolute one must lie under `--base-path`; CSS escape
  sequences, which can hide an address, are forbidden;
- **SVG**: no scripts, styles, event handlers, `<foreignObject>`, entities or
  external links.

### Reproducible builds

The same data, media, code and `--base-path` give a byte-identical result
(the calendar files have a fixed `DTSTAMP`, and the order of files does not
depend on the file system) — **on one machine with one Chrome version and
the same fonts**: the link preview image is drawn by the browser, so on
another machine or another Chrome version the image, and with it its hash
name, may differ ([design-system.md](design-system.md#the-link-preview-image-and-fonts)).
CI checks this by comparing the checksums of two builds in a row.
