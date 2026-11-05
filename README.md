# Invitation pages

Static, private, per-guest invitation pages from two JSON files.

Every guest gets a page of their own at a secret address: their greeting, the
events they are invited to, the places, a programme, photos and videos, and a
personal note if there is one. The build is a single Python script with no
dependencies. It reads `site.json` (what is happening) and `invitations.json`
(who is invited and what each of them sees) and writes plain HTML files that
any static host can serve. There is no server, no database and no forms.

## Features

- **Secret per-guest links.** Each invitation lives at `<path>/<token>/`; the
  token is the only key, and `python3 build.py token` makes a strong one.
- **Per-guest content.** An invitation switches sections, widgets, events and
  event links on or off and adds personal notes. Whatever a guest does not
  see is cut out before rendering, so it is not in their HTML at all.
- **Any language.** English and Russian are built in; any other language is
  a `"lang"` tag and a set of `"strings"` in `site.json`, dates and plural
  forms included.
- **Forms of address.** A text can have an informal and a formal variant
  (*tu*/*vous*, *du*/*Sie*), and each guest gets the one their invitation
  asks for.
- **Calendar files.** Every event has an `.ics` file behind an "Add to
  calendar" button, shown only to the guests who see the event.
- **Link previews.** The build renders the page cover as the image
  messengers show for a shared link.
- **No third-party requests.** No CDN, web fonts, analytics or embedded maps;
  the pages work under a strict Content Security Policy, and all of the text
  is there without JavaScript.
- **Python standard library only.** Nothing to install for the build or the
  tests.
- **Strict validation.** Unknown fields, typos in ids and broken references
  are errors with a "did you mean" hint, and the finished output is checked
  before it replaces the previous build.
- **Reproducible builds.** The same data, media and code give the same files,
  byte for byte (with one machine and Chrome version: the preview image is
  drawn by the browser).

## Quick start

### Requirements

- Python 3.10 or newer;
- `ffmpeg` to generate the example videos (without it only the set without
  media is built);
- Chrome or Chromium for the link preview image, or pass
  `--no-link-preview-image` to do without it.

### Build the examples

```
python3 tools/build_examples.py
```

The script generates placeholder media, builds the three example sets into
`dist/` and prints how to look at them:

```
== data
build: 8 invitation(s), 13 media file(s) validated (data: examples/data, media: examples/media)
…
build: OK -> dist/data (8 page(s), 13 media file(s), 28 file(s) in total, 2.0 MiB)
invitations: dist/data
look at them: python3 -m http.server -d dist/data 8000
  http://localhost:8000/0R-pnCqGFgrPOR5e-NluZw/  Dear Carol,
  http://localhost:8000/oWaEF01q51e11fwVhCZQqQ/  Dear Dave,
  …
```

Serve a set and open one of the printed addresses:

```
python3 -m http.server -d dist/data 8000
```

There is no page at `/` (the built-in server shows a directory listing
there): the invitations are the only pages, and the root of a real site
belongs to whoever publishes it. The sets are:

- `examples/data` — the main set: three events, places with photos, two
  videos and eight guests who each see something different;
- `examples/data-ru` — the same guests in Russian, the example of a second
  language (with the informal and formal forms of address);
- `examples/data-venue-pending` — a celebration whose venue is not announced
  yet, with no media at all.

### Your own data

Put `site.json` and `invitations.json` in a directory of your own and the
photos and videos in another, then validate and build. A copy of
`examples/data` is a good start. Its dinner links to a photo page that the
build does not write, so drop that link or pass `--allow-path /photos`.

```
python3 build.py validate --data path/to/data --media path/to/media
python3 build.py build --data path/to/data --media path/to/media --out path/to/out
```

`site.json` describes the page once, for everybody: an ordered list of
sections, each a list of widgets, and the registries of events, places,
programmes and media they refer to by id. A section can be hidden by
default:

```json
"sections": [
  { "id": "cover", "type": "cover", "eyebrow": "You are invited" },
  { "id": "invite", "title": "{greeting}",
    "widgets": [ { "type": "text", "text": "{coupleNames} are getting married!" },
                 { "type": "date" } ] },
  { "id": "travel", "title": "For guests from out of town", "visible": false,
    "widgets": [ { "type": "location", "location": "hotel", "variant": "compact" } ] }
]
```

An invitation then only switches things on or off and adds notes; it can be
as small as this:

```json
{ "token": "heron-4tx9", "greeting": "Dear Eve,",
  "sections": { "travel": { "visible": true, "note": "We will meet you at the station." } } }
```

Eve's page has the travel section with the note; nobody else's page has
either. Every field is described in [docs/data-format.md](docs/data-format.md).

Once the pages are published, print the links to send:

```
python3 build.py links --url https://example.org/invite --data path/to/data
```

`links` prints one line per guest: the greeting, a tab and the address of
their page. It is the one command that prints personal data, so it refuses
to run in CI.

## How it works

1. `build.py` reads and checks the two JSON files and the media they name.
2. For every invitation it builds a *page tree*: the sections, widgets and
   events that guest sees, with texts in their form of address, dates in the
   language of the site and the addresses of the media files.
3. `template.html` and the fragments in `fragments/` render each tree into
   `<token>/index.html`; the shared styles, script, media and calendar files
   go into `assets/`.
4. Headless Chrome renders the cover of the site into the link preview
   image, which carries the couple's names and the date but nothing about
   any guest.
5. The finished directory is checked (only the expected files, every local
   link resolves, no external resources) and only then replaces the previous
   build.

```
out/
  <token>/index.html     the page of one invitation
  assets/                styles, script, icon
    <mediaDir>/          media, the link preview image and calendar files,
                         named after the hash of their contents
```

The output is published under any path of a site (`--base-path /invite`);
the site around it — its root page, the "not found" page, the response
headers and `robots.txt` — is up to whoever publishes it
([docs/deploying.md](docs/deploying.md)).

## Privacy model

- **The token is the key.** Whoever knows a page's address sees the whole
  page, so tokens should be long and unpredictable: the build counts the
  ones shorter than 12 characters, and `token --prefix heron` gives a
  readable token with a random tail (`heron-4tx9`).
- **A page holds only its guest's data.** Hidden sections, events and other
  guests' notes are cut out before rendering; the shared files hold nothing
  about any guest; media are published under content hashes in a directory
  with a random name; a calendar file is named with a key made of all the
  tokens, so a hidden event's file is as hard to find as a page.
- **Nothing goes to third parties.** No request goes to another domain, the
  build never knows the address of the site, and map buttons are plain links
  that open only when tapped. The publishing site keeps the pages out of
  search engines; link previews have a
  [privacy cost](docs/deploying.md#the-cost-of-link-previews).
- **The build log is safe to share.** Invitations are named by their
  number, tokens are masked in paths and data values are never quoted; the
  only command that prints names and links (`links`) does not run in CI.
- **Replies happen elsewhere.** The pages have no forms, e-mail links or
  phone numbers.

## Documentation

- [docs/cli.md](docs/cli.md) — the commands, their options, the log, exit
  codes, and what the output holds and how it is checked.
- [docs/data-format.md](docs/data-format.md) — `site.json` and
  `invitations.json` field by field, tokens, media, texts and recipes.
- [docs/languages.md](docs/languages.md) — choosing the language, overriding
  strings, date patterns, plurals and a complete Serbian example.
- [docs/templates.md](docs/templates.md) — the template syntax, the page
  tree and the fragments of sections and widgets.
- [docs/design-system.md](docs/design-system.md) — the design tokens and how
  to restyle the pages.
- [docs/video.md](docs/video.md) — preparing a video and how it plays.
- [docs/deploying.md](docs/deploying.md) — publishing the output: headers,
  the Content Security Policy, `robots.txt` and the "not found" page.
- [docs/testing.md](docs/testing.md) — unit tests, CI, checking a restyle and
  the checklist for real devices.

## Development

```
python3 -m unittest
```

The tests use the standard library only; the ones that need a real browser
or `ffmpeg` are skipped when it is missing. CI runs them on Python 3.10 to
3.13, then builds every example set and checks the output and the link
preview tags ([docs/testing.md](docs/testing.md#continuous-integration)).

The repository layout:

```
build.py               the build: data checks, template engine, output checks, tokens, links
template.html          the page frame: <head> and <main>
fragments/             the markup of sections, widgets and media tiles
preview.html           the page the link preview image is rendered from
styleguide.html        the design tokens and components on one page
assets/
  app.css, app.js      the styles and the script of the pages
  preview.css          the frame of the link preview page
  styleguide.css, .js  the styleguide's own files (never published)
  fonts/               local woff2 files (empty by default: the system font is used)
tools/
  _schema.py           the checks of site.json and invitations.json
  _page.py             the page tree of one guest
  _locale.py, locales/ the language of the pages and the built-in strings
  _dates.py            dates in the language of the site, event end times
  _data.py, _maps.py, _media.py, _mp4.py, _png.py, _tokens.py, _preview.py
                       build helpers
  build_examples.py    builds the example sets in one go
  gen_example_media.py placeholder media for the examples (videos need ffmpeg)
  gen_assets.py        the icon and the neutral preview image on their own
examples/              fictional data sets
docs/                  the reference
tests/                 unit tests (unittest)
```

The code follows a few rules, enforced by the tests:

- the standard library only: there is nothing to install;
- no media files and no build output in the repository: the example media
  are generated, `dist/` is ignored by git, and CI rejects both;
- no request from a page to another domain, and no inline script or style;
- no personal data in any message of the build;
- English everywhere except the Russian set of strings, the Russian example
  set, their tests and a few tests that need non-Latin input on purpose.

The styleguide shows every design token with its computed value and every
component in its states. It refers to `/assets/…`, so serve the repository
root:

```
python3 -m http.server 8000
```

and open `http://localhost:8000/styleguide.html`.

## Licence

MIT, see [LICENSE](LICENSE).
