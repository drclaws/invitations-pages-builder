# Data format

The data is two files in the `--data` directory, UTF-8 (a byte order mark is
accepted): `site.json` holds everything shared (the sections of the page,
events, places, programmes, media, texts, the language) and
`invitations.json` holds the invitations. `site.json` must have
`"schemaVersion": 2`.

The checks are strict:

- **an unknown field is an error** with a hint of the closest known name
  (`unknown field 'coupleName' (did you mean 'coupleNames'?)`), so a typo
  never passes silently;
- **a repeated key** inside one object is an error: a plain JSON parser would
  silently keep the last value;
- `null` is accepted nowhere: an optional field is simply left out;
- an empty string in an optional text field is the same as no field.

Files in the first version of the format (fields such as `dateISO`,
`dateText`, `venue`, `video` and `schedule` in `site.json`, or flags such as
`ty`, `vy`, `plusOne` and `outOfTown` on the invitations) are not read: the
build prints one message per file that lists the old fields, and the
messages of the individual fields say where their contents belong. To
convert: `dateISO`/`dateText` → `events.<id>.start`; `venue` → `locations`
plus `events`; `video` → `media` and a `media` widget; `schedule` →
`schedules` plus `events.<id>.schedule`; `outOfTownText` → a `text` widget
of the section for guests from out of town; `ty`/`vy` → `"form"`;
`plusOne`/`outOfTown` → `sections.<id>.visible`; `note`/`travelNote` →
`sections.<id>.note`; `directionsImage` → `directions`. See the
[recipes](#recipes).

How a page is put together:

- a page is an **ordered list of sections** from `site.json`, and a section
  is a list of **widgets** (text, date, events, place, programme, media);
- events, places, programmes and media are **registries**, objects keyed by
  id, and the sections refer to them by id;
- an invitation adds nothing and does not reorder anything: it only **switches
  on and off** sections, widgets, events and event links and adds **notes**
  to sections and events. Whatever is hidden is cut out **before** rendering:
  it is not in the HTML of the page, and neither is the link to the calendar
  file of a hidden event.

## A minimal data set

The smallest useful data set: one event, one place, a cover and one section.
Both files below pass `validate` as they are.

`site.json`:

```json
{
  "schemaVersion": 2,
  "coupleNames": "Alice & Bob",
  "mediaDir": "q7Jx2mWb9LtR4vNc8ZpK3s",
  "mainEvent": "dinner",
  "sections": [
    { "id": "cover", "type": "cover" },
    { "id": "invite", "title": "{greeting}",
      "widgets": [
        { "type": "text", "text": "{coupleNames} invite you to dinner on {eventDate} at {eventTime}." },
        { "type": "events" }
      ] }
  ],
  "events": {
    "dinner": { "title": "Dinner", "location": "hall",
                "start": "2030-06-15T18:00:00+01:00", "end": "2030-06-15T23:00:00+01:00" }
  },
  "locations": {
    "hall": { "name": "Example Hall", "address": "1 Example Street, Exampleton" }
  }
}
```

`invitations.json`:

```json
[
  { "token": "8s1Kq0bXc3m5YtLwV2nRgA", "greeting": "Dear Carol," },
  { "token": "Zr4pQe7HvN0uJd2Wk9sTfB", "greeting": "Dear Dave and Eve," }
]
```

There are no media, so the `--media` directory does not even have to exist.
The examples in `examples/` show every other feature.

## `invitations.json`

An array of invitations.

| Field | Type | Required | Rules |
|---|---|---|---|
| `token` | string | yes | see [Tokens](#tokens) |
| `greeting` | string | yes | how the guest is addressed, **one line**; no forms or placeholders |
| `form` | `"informal"` or `"formal"` | when the page shows a text with forms | the form of address for texts that have both ([Forms of address](#forms-of-address)); `"ty"` and `"vy"` are accepted as aliases |
| `primaryEvent` | event id | no | the guest's primary event; `mainEvent` of `site.json` by default |
| `events` | object | no | `{ "<event id>": { "visible": …, "note": …, "links": { "<link id>": { "visible": … } } } }` |
| `sections` | object | no | `{ "<section id>": { "visible": …, "note": …, "widgets": { "<widget id>": { "visible": … } } } }` |

The overrides are a closed list; there are no other fields:

- `events.<id>.visible` shows the guest an event that is hidden in the
  registry (`"visible": false` there), or hides an ordinary one;
- `events.<id>.note` is a **note on the event**, shown in the event card of
  the "Events" widget ("Please tell us about any allergy");
- `events.<id>.links.<id>.visible` switches an
  [event link](#event-links) on or off for this guest; a link is hidden by
  default. A link the event does not declare is an error (its key is shown
  only when it is an id declared in `site.json`, otherwise `<unknown key>`);
  a link holds `visible` and nothing else;
- `sections.<id>.visible` shows a section that is hidden by default, or hides
  an ordinary one;
- `sections.<id>.note` is a **note on the section**: a card at the end of
  the section. A section with a note and no widgets is shown too, which is
  how the section "A few personal words" of the examples works;
- `sections.<id>.widgets.<id>.visible` shows or hides a widget; the widget
  needs an `id` in `site.json` for that.

Rules:

- every guest sees at least one event;
- the primary event must be visible to the guest; when `mainEvent` is hidden
  from a guest, `primaryEvent` is required;
- the cover cannot be overridden: it is the same for everybody;
- a note is a string and may span several lines; placeholders and named
  texts work in it, but it has no forms of its own (it is written to one
  person anyway);
- warnings rather than errors: a note on an event or a section the guest does
  not see; a note on an event that no "Events" widget shows; a link switched
  on for such an event; a section switched on for a guest that has nothing to
  show them.

The keys under `events` and `sections` of an invitation are ids from
`site.json`. Messages about the invitations print only the field names of the
format and the ids declared in `site.json`; any other key is replaced by
`<unknown key>`, since a key may turn out to be a name.

## `site.json`

| Field | Type | Required | Rules |
|---|---|---|---|
| `schemaVersion` | integer | yes | exactly `2` |
| `lang` | string | no | the language of the pages, a tag such as `en`, `ru` or `sr-Latn`; `en` by default ([languages.md](languages.md)) |
| `strings` | object | no | the words and date patterns of the pages over the built-in ones ([languages.md](languages.md#overriding-strings)) |
| `coupleNames` | string | yes | one line; no forms or placeholders |
| `rsvpDeadline` | string | no | one line; needed only by texts with `{rsvpDeadline}` |
| `mediaDir` | string | yes | the name of the media directory, see [the media directory](#the-media-directory-and-file-names) |
| `mainEvent` | event id | yes | the main event; it cannot be hidden by default |
| `sections` | array | yes | the sections of the page in order, at least one |
| `events` | object | yes | the event registry, at least one |
| `locations` | object | no | the place registry |
| `schedules` | object | no | the programme registry |
| `media` | object | no | the registry of photos and videos |
| `texts` | object | no | named texts of the site, inserted with `{text:<id>}` ([Named texts](#named-texts)) |
| `linkPreview` | object | no | `{ "description": "…" }`, the description in link previews, one line for everybody ([Link preview](#link-preview)) |

The keys of the registries are [ids](#ids).

### Sections

| Field | Type | Rules |
|---|---|---|
| `id` | id | required, unique among the sections |
| `type` | `"cover"` or none | `cover` is the cover; without `type` the section is an ordinary one |
| `visible` | boolean | `true` by default; `false` shows the section only to the guests who have it switched on |

**The cover** (`"type": "cover"`) comes first and there is at most one. It
shows the couple's names (the only `h1` of the page) and the date of the
guest's **primary** event. Without a cover there is a warning: the page would
have no main heading. The cover is the same for every guest and cannot be
overridden in an invitation.

| Field | Type | Rules |
|---|---|---|
| `eyebrow` | text | a line above the couple's names |
| `background` | media id | an optional photo behind the cover, **an image only** (a video is an error, "must be an image"); under a veil of the cover colour, see the recipe [A photo on the cover](#a-photo-on-the-cover) |
| `backgroundFocus` | `"center"`, `"top"`, `"bottom"`, `"left"`, `"right"`, `"top-left"`, `"top-right"`, `"bottom-left"` or `"bottom-right"` | which part of the photo stays in view when the screen crops it; `center` by default; without `background` there is a "has no effect" warning |

The photo behind the cover is decoration: it has an empty `alt` on the page,
so a media item shown **only** as the cover background needs no `alt` (and
gets no warning). A background file larger than 1 MiB gets a warning: it is
the first screen.

**An ordinary section**:

| Field | Type | Rules |
|---|---|---|
| `title` | text | required, one line; forms and placeholders work |
| `titleHidden` | boolean | `true` hides the title visually; it stays the accessible name of the section |
| `width` | `"narrow"` or `"wide"` | the width of the column, `narrow` by default |
| `align` | `"start"` or `"center"` | the alignment, `start` by default |
| `widgets` | array | required, may be empty |

A section that has nothing to show a guest (every widget hidden or empty, and
no note) is left out of their page altogether.

### Widgets

The common fields are `type` (required), `id` (needed only to let an
invitation show or hide the widget; unique in its section) and `visible`
(`true` by default).

| `type` | Fields | What it shows |
|---|---|---|
| `text` | `text` (text, required), `variant`: `body`, `lead` or `signature` (`body` by default) | paragraphs of text |
| `date` | `event` (id; the guest's primary event by default), `countdown` (`true` by default), `calendar` (`true` by default) | the date and time of the event, a countdown and an "Add to calendar" button; the title of the event when the guest sees more than one event |
| `events` | `events` (an array of ids; every event the guest sees by default) | event cards: time, description, the guest's note, place, programme; always in order of start time |
| `location` | `location` (id, required), `variant`: `full` or `compact` (`full` by default) | a place card; `compact` shows only the name, the address and the map buttons |
| `schedule` | `schedule` (id, required) | a programme on its own |
| `media` | `items` (an array of ids, at least one), `layout`: `grid`, `ribbon` or `single` (`grid` by default) | photo and video tiles; `single` takes exactly one item |

The date and events widgets show only the events the guest sees: when the
event of a `date` widget is hidden from a guest, the widget disappears. A
programme widget disappears when its programme belongs only to events hidden
from the guest.

### Events

`events.<id>`:

| Field | Type | Required | Rules |
|---|---|---|---|
| `title` | string | yes | one line; no forms or placeholders: it goes into the calendar file too |
| `location` | place id | yes | a place that is not announced yet is a place with `"ready": false` |
| `start` | string | yes | a date and time **with a UTC offset**, see below |
| `end` | string | no, but a warning without it | later than `start`; not shown on the page by default, see below |
| `showEnd` | boolean | no | `false` by default; `true` shows the range "16:00–23:30" on the page |
| `schedule` | programme id | no | the programme of the event (in its card) |
| `description` | text | no | may span several lines; forms and placeholders work |
| `visible` | boolean | no | `true` by default; `false` shows the event only to the guests who have it switched on |
| `links` | object | no | buttons in the event card that lead to other pages of the same site, see [Event links](#event-links) |

`start` and `end` are a strict subset of ISO 8601,
`YYYY-MM-DDThh:mm[:ss[.fff]]`, with a required offset (`+03:00`, `-05:00` or
`Z`). The offset is required because without it the countdown and the
calendar file would show different times in different time zones. Example:
`2030-06-15T16:00:00+03:00`. When the events have different offsets, the
build warns: check them around a change to or from summer time.

The build writes the dates itself, in the language of the site and on the
clock of the event's own offset: "15 June 2030", "16:00", "Saturday, 15 June
2030, 16:00" with the built-in English strings ([languages.md](languages.md)).

**The end** (`end`) is **not shown on the page** by default: guests see the
start only. The end serves three purposes:

- `DTEND` of the event's calendar file ([cli.md](cli.md#calendar-files));
- the "past" and "happening now" marks of the "Events" widget;
- the choice of the default tab: an event that is over gives way to the next
  one.

To show the range on the page ("Saturday, 15 June 2030, 16:00–23:30"), give
the event `"showEnd": true`. Without `end` the flag has nothing to show, and
the build warns `field 'events.<id>.showEnd' has no effect without 'end'`.

`end` is optional. Without it the end is **the start plus six hours**, the
same for every guest and everywhere (calendar, marks, choice of tab), and the
build warns `field 'events.<id>.end' is not set: the calendar and the
past/now marks use start + 6 h`. An event's end never depends on other
events: a neighbouring event does not shorten it, even when it starts
earlier. So it is better to give `end` explicitly.

**The guest's primary event** (`primaryEvent`, `mainEvent` by default) sets
the date on the cover, the date widget without `event`, the countdown and
the values of the placeholders `{eventDate}`, `{eventTime}`, `{eventTitle}`
and `{eventPlace}`; in the "Events" widget its card has a border.

### Event links

An event may hold links: buttons in its card that lead to other pages of the
same site, pages the build does not write. A link is shown **only to the
guests who have it switched on** (`events.<id>.links.<id>.visible` in
`invitations.json`), unless `site.json` makes it visible by default. The key
is the [id](#ids) of the link; the buttons follow the order of the keys.

| Field | Type | Required | Rules |
|---|---|---|---|
| `text` | string | yes | the label of the button; one line, like the `title` of the event: no forms, no `{` or `}` (nothing is filled in) |
| `href` | string | yes | a path from the root of the site to a directory, see below |
| `visible` | boolean | no | `false` by default: the link is shown to the guests who switch it on; `true` shows it to everybody who sees the event (no warning) |
| `pending` | text | no | the text **in place of the button** while the link is not shown to the guest, see below; a text like the event's `description` (forms, placeholders and named texts work) but one line, also once its named texts are expanded; no `{token}`; blank means no text |

The rule of `href`: `/`, then segments, each followed by `/` (so the path
ends with `/` and leads to a directory page). A segment is `A–Z`, `a–z`,
`0–9`, `_` and `-`, or exactly `{token}`, the guest's token, filled in for
every page; `{token}` may be used once at most and only as a whole segment.
At most 200 characters. Anything else is an error, and the value is never
quoted: a scheme or a host, `//`, `.` and `..`, `?`, `#`, `%`, spaces,
`{token}` inside a segment, a path without the trailing `/`, or `/` alone.
An unknown field of a link is an error with a hint.

```json
"dinner": { "title": "Wedding dinner", "location": "manor", "start": "2030-06-15T16:00:00+03:00",
            "links": { "photos": { "text": "Photos from the dinner", "href": "/photos/{token}/" } } }
```

Only the "Events" widget shows the links (the date widget and the cover do
not). A guest's page holds their token only in the `href` of the links
switched on for them, and the address of the page holds it anyway; other
pages and `assets/` never do. Such a link leads outside the output, so the
build needs [`--allow-path`](cli.md#--allow-path-links-to-other-pages-of-the-site)
for its directory; without it the link fails the output check.

**A text in place of the button** (`pending`). While a link is not shown to
a guest, its place in the card may hold a text instead: for example, that the
photos will appear here after the day. Each guest sees either the button or
the text, never both, and the same switch of the invitation
(`events.<id>.links.<id>.visible`) turns one into the other; an invitation
has no text of its own. The text holds neither the token nor an address:
`{token}` in it is an error of its own (`must not contain {token}: the text
stands in place of the link and holds no token`). A link without `pending`
leaves nothing in its place.

```json
"photos": { "text": "Photos from the dinner", "href": "/photos/{token}/",
            "pending": "Photos from the dinner will appear here after the celebration — we will let you know" }
```

### Places

`locations.<id>`:

| Field | Type | Rules |
|---|---|---|
| `ready` | boolean | `true` by default; `false` means the place is not announced: the card says "Details will appear on this page later." (the `placePending` string) and no other field is shown |
| `name` | string | one line; required when the place is announced |
| `address` | string | one line |
| `description` | text | may span several lines; forms and placeholders work |
| `geo` | object | `{ "lat": number, "lng": number }`, both required inside |
| `maps` | object | where the place is on each map: an identifier or a text query (see below) |
| `photos` | array of media ids | photos and videos of the place (a ribbon in its card) |
| `directions` | media id | a directions map, an image only |
| `directionsCredit` | string | the credit of the directions map: one non-empty line without control characters; shown as it is, without forms or placeholders ("©" and the like are part of the field); put a no-break space (U+00A0, `\u00a0` in JSON) after "©" so that it never ends a line on its own |

- **the directions map** sits in the place card under the map buttons with
  the caption "Directions" (the `directions` string); a `directionsCredit`
  follows the caption after a space ("Directions © Exampleton Mapping
  Service"). Without `directions` the credit shows nothing, and the build
  warns `field 'locations.<id>.directionsCredit' has no effect without
  'directions'`;
- `lat` is within ±90 and `lng` within ±180. **`lat: 0, lng: 0` counts as
  "not set"** (a placeholder, not a place in the Atlantic);
- **a map button appears only when the place is given in `maps` for that
  map**, by an identifier or by that map's own query. Coordinates alone are
  not enough for a button: a place with `geo` only has no map buttons, and a
  place given for no map has no block of buttons at all. The coordinates
  hint the area to the Yandex and Apple queries and help Apple when its
  identifier is not recognised;
- the build makes the links from the `maps` fields itself
  ([templates.md](templates.md#map-links)): give an identifier or a query,
  not a link.

The `maps` fields, all optional; each map takes the first one given, in the
order "identifier, then query":

| Field | Map | Value | Where to find it |
|---|---|---|---|
| `googlePlaceId` | Google | a Place ID: only `A–Z`, `a–z`, `0–9`, `_` and `-` | the Place ID Finder page of the Google Maps Platform documentation |
| `googleQuery` | Google | a text query | — |
| `yandexOrgId` | Yandex | an organisation number: digits only | the number after `/org/<name>/` in the address of the organisation's card on Yandex Maps |
| `yandexGeoId` | Yandex | the number of a map object (a building or an entrance, something without an organisation card): digits only | the number after `/geo/<name>/` in the address of the object's card on Yandex Maps |
| `yandexQuery` | Yandex | a text query | — |
| `applePlaceId` | Apple | a Place ID: only `A–Z`, `a–z` and `0–9` | Place ID Lookup in the Apple Maps documentation; the `place-id` parameter of a "Share" link from Apple Maps, when it has one |
| `appleQuery` | Apple | a text query | — |

- **a text query** is what a guest would type into the search box of that
  map, for example `"Guest entrance, Register Office, Exampleton"`: a name
  and a town. It is for a place without an identifier of its own, such as a
  separate entrance to a large building. One line of 1 to 200 characters
  without control characters; an empty string or one of spaces is an error
  (leave the field out instead). Each map has its own query: one place may
  be called differently on different maps;
- `yandexOrgId` and `yandexGeoId` together are an error ("set either
  'yandexOrgId' or 'yandexGeoId'"): one place, one kind of identifier;
- there is no common `query` field: the build suggests splitting the query
  per map.

```json
"maps": { "googleQuery": "Guest entrance, Register Office, Exampleton", "yandexGeoId": "1234567890",
          "applePlaceId": "IEXAMPLE0000001" }
```

### Programmes

`schedules.<id>` is an array of items `{ "time": …, "title": …, "text": … }`:
`title` is required (one line), `time` is one line, `text` may span several
lines. Forms and placeholders work in `title` and `text`
([Texts](#texts)); `time` is a plain string. An empty programme gets a
warning and is not shown.

### Media

`media.<id>`:

| Field | Type | Rules |
|---|---|---|
| `type` | `"image"` or `"video"` | required |
| `file` | file name | required; an image is `.png`, `.jpg`, `.jpeg`, `.webp`, `.avif`, `.gif` or `.svg`; a video is `.mp4` only |
| `poster` | image file name | required for a video, not allowed for an image |
| `thumb` | image file name | the picture of the tile; the poster by default, the file itself for a photo |
| `width`, `height` | integers > 0 | both or neither |
| `alt` | string | one line, the description for screen readers; without it there is a warning and the label "Photo" or "Video" (the `photo` and `video` strings) |

- **the size** lets the page reserve the space of a tile before it loads and
  tells the viewer the proportion of the frame. Without `width`/`height` the
  build reads the size from the header of the image (PNG, JPEG, WebP; for a
  video, of its poster) or from the `.mp4` itself; when that fails, there is
  a warning, and a single tile gets the 16:9 proportion of a design token;
- for a video the build reads the **duration** itself (it is shown on the
  tile) and checks the file: no `+faststart`, a codec other than H.264, HDR,
  an unreadable duration, or a poster whose proportion differs from
  `width`/`height` by more than 1 % are warnings; contents of another type
  than the extension says are an error;
- **a tile has no caption**: it has a fixed proportion and no room for text
  under it, so a `caption` field is an error with a hint; `alt` describes the
  picture;
- a registry item that no page shows gets a warning, and its files are
  neither published nor even read.

The requirements of a video file and how to prepare one: [video.md](video.md).

## Tokens

A token is made up or printed by `python3 build.py token`; it may be readable
(`quokka`, `heron-4tx9`):

- the characters are `A–Z`, `a–z`, `0–9`, `_` and `-`;
- the length is 5 to 200 characters: the token becomes a directory name;
- a token of hex digits and hyphens only (like a UUID) is checked like any
  other; there are no special rules for it;
- tokens are unique **regardless of letter case**: the directories `ABC…/`
  and `abc…/` would be the same on a file system that ignores case;
- **`assets` is reserved** (in any letter case: `Assets`, `ASSETS`): the
  directory of the page would be the directory of the shared files next to
  the pages. Such a token is an error of `validate` and `build`; the message
  names the invitation by its number and does not repeat the value;
- tokens do not change after the invitations are sent: the old links would
  stop working.

A new token: `python3 build.py token` (random) or
`python3 build.py token --prefix <name>` (readable with a random tail,
[cli.md](cli.md#token)).

**The token is the only protection of a guest's page.** Whoever knows or
guesses the address `<base-path>/<token>/` sees the whole page: the greeting,
the notes (an allergy, say), the events and places hidden from other guests,
the calendar files. A short readable token made of a name or a nickname can
be found by trying a dictionary: names, pet names, combinations such as
`*_queen` or `cat_*`. So:

- make tokens **at least 12 characters long**: the build counts the shorter
  ones and reports their number in the line `tokens: …`
  ([cli.md](cli.md#what-the-commands-print));
- do not make a token of a name alone: add something only you and the guest
  know;
- if a token must be readable, add a short random tail: `token --prefix heron`
  gives `heron-4tx9`; it stays readable, and trying a dictionary becomes about
  a million times more expensive;
- keep sensitive things out of the notes (health, addresses, phone numbers):
  with a guessed token a stranger reads them.

Only the length and unpredictability of the tokens protect against guessing.
Rate limiting of requests to `<base-path>/*`, where the host offers it, can
only slow guessing down. Nothing else the site does helps:
`robots.txt` ([deploying.md](deploying.md#robotstxt-and-link-preview-bots))
only keeps the pages out of search engines, and a single "not found" page for
the root and every wrong address only keeps a guess from telling how close
it came. Neither slows down or stops guessing.

## The media directory and file names

`mediaDir` is a random name of the directory where the build puts the media:
the files are published under `<base-path>/assets/<mediaDir>/…`
(`/assets/<mediaDir>/…` with `--base-path /`), so the address of a picture
tells nothing about the links or the event.

- 16 to 200 characters of `A–Z`, `a–z`, `0–9`, `_` and `-`;
- the name must not match (regardless of letter case) anything that is
  already in `assets/` (`fonts`, …); the build checks this.

**Published names are content hashes.** A file is published not under its
own name but as `assets/<mediaDir>/<the first 16 hex digits of the sha256 of
its contents>.<extension>`, for example `…/6606d330914742c8.png`. The name
from the data never reaches the output, so the file of a section shown to one
guest cannot be found by trying names. Files with the same contents and
extension are published once, and the build stays reproducible. **Only the
files of the items shown on at least one page are published**: the others
are neither read nor published (and the unused registry item gets a
warning).

**Calendar files** live in the same directory, one per event that at least
one guest sees: `assets/<mediaDir>/<16 hex digits>.ics`, named with a key
made of all the tokens ([cli.md](cli.md#calendar-files)).

Media file names in the data:

- **a plain file name** inside the media directory: no `/`, `\` or `..`, not
  starting with a dot, no control characters;
- **no colons**: such a name cannot be created on some file systems;
- **letter case matters**: `Venue-1.png` and `venue-1.png` are different
  files (when a file is missing but differs only in case, the build says so);
- the allowed extensions: images `.png`, `.jpg`, `.jpeg`, `.webp`, `.avif`,
  `.gif`, `.svg`; videos `.mp4` only. Any of the image formats serves every
  image role: a photo, a poster, a tile picture, a cover background or a
  directions map;
- symbolic links are not accepted in place of files, and each file is at
  most 25 MiB.

Messages about files name the field (`field 'media.walk.file': the file is
missing from media`), not the file name: the name is data too. There are no
reserved names: calendar files get hash names with the extension `.ics`,
which media never have (the build checks for a clash all the same and calls
it an error).

**The media directory may not exist at all.** When the pages show no media
(say, the places are not announced and there is no `media` registry),
`--media` may point to a directory that does not exist: the build passes,
and `assets/<mediaDir>/` of the output holds only the calendar files. That is
how the second example is built:

```
python3 build.py build --data examples/data-venue-pending --media examples/media-none
```

## Link preview

When a link to an invitation is shared, messengers show a card built from
the tags of the page, the same for every guest:

- **the title** is "Invitation · Alice & Bob": the `invitationTitle` string
  of the language ([languages.md](languages.md)) and `coupleNames`. It goes
  into `<title>`, `og:title` and `og:image:alt` and has no field of its own;
- **the description** is `linkPreview.description`, built from texts in
  their common form (see [the recipe](#the-link-preview-description)); no
  field, no description;
- **the image** is the cover of the pages, rendered by the build (below), or
  your own;
- **the site name** (`og:site_name`) is set on the command line
  ([cli.md](cli.md#link-preview-options)), and `og:locale` comes from the
  `ogLocale` string.

Nothing in the card is about a particular guest: no greeting, no note, no
token. Whether the messengers show the image, and what a preview costs in
privacy, is described in [deploying.md](deploying.md#the-cost-of-link-previews).

### The rendered cover

The build renders the link preview image itself on every build: the same
cover as at the top of the page (`template.html`,
`fragments/sections/cover.html`, `app.css`, the `background` photo under the
veil with its `backgroundFocus`, the couple's names, the divider and the
date), in headless Chrome, as part of `build`. It differs from a guest's page
because the shared image may not hold guest data:

- the date is that of the **main event** (`mainEvent`);
- the `eyebrow` of the cover is shown only when it does not depend on a
  guest: a string without forms and without `{greeting}` (named texts in
  their common form `all` and site-level placeholders are fine); otherwise
  it is left out, and `validate` says so in one line;
- the top bar of the cover is not there, and the page scripts do not run.

The format is **JPEG 1200×630** of **at most 300 KB** (the official limit of
WhatsApp is 600 KB, but in practice it drops the image at about 300 KB): the
quality steps down from 85 to 60, and when the image still does not fit,
there is a warning and it is published anyway. **The safe zone**: the names
and the date stay inside the central 630×630 square (small previews crop the
image to a centred square). The frame is laid out by `assets/preview.css`;
when a cover with long names does not fit the "phone" window of 600×315
(scale ×2), the build takes 800×420 (×1.5), then 1200×630. The image is
published like other media, as `assets/<mediaDir>/<sha256[:16]>.jpg`, one
per site; there is never an image with data at a guessable address such as
`assets/og.*`. The preview page gets the same `<base-path>/assets/…`
addresses as the guests' pages, so the bytes of the image do not depend on
`--base-path`.

**A site without a cover** (no section of `type: "cover"`) gets a neutral
picture of the design tokens, `assets/og.png`; so does a build with
`--no-link-preview-image` (`LINK_PREVIEW_IMAGE=off`). `og.png` is written only
when the pages refer to it.

### Your own icon and preview image

**Your own preview image** replaces the rendered cover for those who want to
draw the preview themselves: a file `og.png` or `og.jpg` in the **media
directory**. It is published in `assets/<mediaDir>/` under the hash of its
contents as well (not in `assets/`), and Chrome is not needed then.
Proportions far from 1200×630 (about 1.91:1) get a warning: the services
would crop the picture.

**Your own icon** is `favicon.svg`, `favicon.png` or `favicon.ico` in the
media directory (the first one that exists wins); it is published as
`assets/favicon.<ext>`. By default the icon is drawn from the design tokens.

These files need no mention in `site.json`. The rules of other media apply to
them. A file that only resembles them (another letter case, another
extension, a name that loses to another, such as `favicon.png` next to
`favicon.svg`) is not published, and the build warns about it, so
that nobody waits for a picture that never appears.

The names `favicon.*` and `og.*` inside `assets/` are taken by the build: a
file with such a name in the code's `assets/` stops the build with a hint to
put it into the media directory.

## Texts

**What works where:**

| Where | Forms of address | Placeholders |
|---|---|---|
| `title` and `eyebrow` of a section, `text` of a text widget | yes | yes, and `{text:<id>}` |
| the guests' notes (`note`) | no | yes, and `{text:<id>}` |
| named texts `texts.<id>` | yes, plus the common form `all` | yes, and `{text:<id>}` |
| `linkPreview.description` | no (named texts in their common form `all`) | site-level only (no `{greeting}`; `{event…}` of the main event), and `{text:<id>}` |
| `description` of an event and a place, `title` and `text` of a programme item, `pending` of an event link (one line, no `{token}`) | yes | yes, and `{text:<id>}` |
| `title` of an event, `name` and `address` of a place, `greeting`, `coupleNames`, `rsvpDeadline`, `alt` of a media item | no | no |

The last row is what goes into **shared files**: the title and place of an
event go into its calendar file, the same for everybody who sees the event,
and `greeting`, `coupleNames` and `rsvpDeadline` are themselves values of
placeholders. They must hold no data of a particular guest.

Descriptions of events and places and the texts of a programme never leave
the guest's page (the calendar file does not have them), so forms and
placeholders work there as in the text of a section. `{eventDate}`,
`{eventTime}`, `{eventTitle}` and `{eventPlace}` are everywhere those of
**the guest's primary event**, not of the event whose description is being
expanded.

### Forms of address

Many languages address a person in one of two registers: informal and formal
(*tu* and *vous*, *du* and *Sie*). A text is either one string for everybody
or an object with both variants:

```json
"text": { "informal": "Can't wait to see you on {eventDate} at {eventTime}!",
          "formal": "We look forward to welcoming you on {eventDate} at {eventTime}." }
```

A guest gets the variant of their `form` field. The canonical names are
`informal` and `formal`; `ty` and `vy` are accepted as their aliases
everywhere a form is named (in a text and in `form`). An object without one of
the variants is an error, and so is an object that gives one form under both
of its names (`gives the informal form twice ('ty' and 'informal')`).

`form` is optional on an invitation: it is required only when the guest's
page shows a text with forms, and then the error names the first such field
(`field 'form' is required: this page shows a text with forms of address
(first: …); set "informal" or "formal"`). The English examples have no forms
at all; the Russian example set (`examples/data-ru`) uses them throughout.

### Placeholders

A placeholder is a name in braces:

| Placeholder | Value |
|---|---|
| `{coupleNames}` | `coupleNames` |
| `{greeting}` | the guest's greeting |
| `{rsvpDeadline}` | `rsvpDeadline` (an error without the field) |
| `{eventTitle}` | the title of the guest's primary event |
| `{eventDate}` | its date: "15 June 2030" (the `date` pattern of the language) |
| `{eventTime}` | its time: "16:00" (the `time` pattern) |
| `{eventPlace}` | the name of its place; an empty string and a warning when the place is not announced |

An unknown name, an unclosed brace and empty braces are errors (with the
character number; the text itself never reaches the message). `{{` and `}}`
are literal braces. Inserted values are not parsed again: braces in a
greeting stay text.

### Named texts

A text needed in several places (say, the main text of the invitation and
the link preview description) is written once in the `texts` registry and
inserted by id:

```json
"texts": {
  "announce": "{coupleNames} are getting married!",
  "invite": { "informal": "Can't wait to see you on {eventDate} at {eventTime}!",
              "formal": "We look forward to welcoming you on {eventDate} at {eventTime}.",
              "all": "We look forward to seeing you on {eventDate} at {eventTime}." } }
```

```json
{ "type": "text", "variant": "lead", "text": "{text:announce}" }
```

- the id follows [the id rule](#ids); the value is a string (one for
  everybody) or an object with `informal` and `formal` and an optional
  **common form `all`**; several lines and placeholders work as in the text
  of a widget;
- **the common form `all`** is the variant for places without a guest (the
  link preview description). It may not hold `{greeting}` (directly or
  through other texts), and its `{event…}` placeholders take the **main**
  event (`mainEvent`). Guests' pages never use `all`. The key `all` is
  allowed only in `texts`: in the `text` of a widget, a `title` or an
  `eyebrow` it is an error. A string without forms serves as its own common
  form when it has no `{greeting}`;
- `{text:x}` works wherever placeholders do: `title`, `eyebrow`, the `text`
  of a widget, the guests' notes, `linkPreview.description`, the
  `description` of an event and a place, the `title` and `text` of a
  programme item, the `pending` of an event link. In the `title` of an event,
  the `name` and `address` of a place, `greeting`, `coupleNames`,
  `rsvpDeadline` and `alt` it does not (it is plain text there).

**How a text is expanded:**

1. the variant of the field for the guest's form is picked;
2. every `{text:<id>}` is replaced by the variant of that text **for the same
   form** (a string fits any form);
3. texts may use each other and are expanded recursively; a **cycle**
   (`a → a`, `a → b → a`) is an error that lists the chain of ids; the depth
   is at most 8, and an expanded text is at most 10,000 characters;
4. then the placeholders are filled in one pass (`{coupleNames}`,
   `{eventDate}`, …), with `{event…}` of the guest's primary event. Inserted
   values are not parsed: `{text:…}` in a greeting stays text.

Errors: an unknown id (with a hint and the list of known ones), `{text:}` and
ids that break the rule (with the character number), a cycle or too much
depth, a multi-line text in a one-line field (`title`, `eyebrow`). A named
text that no page shows and the link preview does not use gets a warning.
`{{text:x}}` is literal text.

### Lines and paragraphs

In **multi-line texts** (the text of a widget, descriptions, notes, programme
items) an empty line starts a new paragraph and a single line break is a line
break. The fields that go into headings and labels (`title`, `eyebrow`,
`greeting`, `coupleNames`, the names of events and places, the address, the
directions credit, `time` and `title` of programme items, `alt`) must be
**one line**; the validation checks it.

The words of the interface ("Add to calendar", "Programme", the countdown
labels, "Details will appear on this page later.") are not in the data: they
are strings of the language ([languages.md](languages.md)).

## Ids

The ids of sections, widgets, events, places, programmes, media, links and
named texts are 1 to 32 characters: lower-case Latin letters, digits and
single hyphens, starting with a letter (`dinner`, `hotel-booked`,
`venue-1`). Two hyphens in a row are not allowed: the build joins the parts
of DOM ids with them ([templates.md](templates.md#dom-ids)).

Ids are **visible**: in the `id` attributes of the markup and in the messages
of the build. So ids hold neither guests' names nor details of the event:
`plus-one`, not `plus-one-ivan`; `hotel`, not the name of the hotel. A
guest's name in the keys of `invitations.json` never reaches the messages
anyway ([invitations.json](#invitationsjson)), but ids from `site.json` are
printed as they are.

## Recipes

All of these are changes to the data only; the code stays the same. The main
example, `examples/data/`, is built exactly this way.

### A section for some guests only

The section is hidden by default in `site.json` and switched on for the guests
from out of town:

```json
{ "id": "travel", "title": "For guests from out of town", "visible": false,
  "widgets": [ { "type": "text", "text": "On the day, a shuttle runs from the station." },
               { "type": "location", "location": "hotel", "variant": "compact" } ] }
```

```json
{ "token": "…", "greeting": "Dear Eve,",
  "sections": { "travel": { "visible": true } } }
```

### A paragraph for some guests only

A "plus one" is not a section of its own but part of the invitation: a text
widget with an `id`, hidden by default, between the main text and the
closing words. Three `lead` widgets in a row read as one text: the spacing
between them is that of paragraphs, not of widgets.

```json
{ "id": "invite", "title": "{greeting}", "align": "center",
  "widgets": [
    { "type": "text", "variant": "lead", "text": "{text:announce}" },
    { "id": "plus-one", "type": "text", "variant": "lead", "visible": false,
      "text": "You are welcome to bring a partner or a friend.\nPlease let us know their name in advance." },
    { "type": "text", "variant": "lead", "text": "{text:invite}\nWe would love to share this day with you." } ] }
```

The guests who may bring someone get the widget switched on:

```json
{ "token": "…", "greeting": "Dear Carol,",
  "sections": { "invite": { "widgets": { "plus-one": { "visible": true } } } } }
```

The others have no such paragraph, neither on the page nor in its HTML. Any
text "for some guests only" inside a section works the same way: the widget
gets an `id` and `"visible": false` and is switched on through the `widgets`
of its section, like "We have booked a room for you at this hotel"
(`hotel-booked`) in the `travel` section of the example.

### Shared texts: the announcement and the invitation

The main text has two parts, the announcement ("Alice & Bob are getting
married!") and the invitation ("We look forward to seeing you on …"). Both
live in `texts` ([Named texts](#named-texts)): on the page each guest gets
their form, and the link preview description is built from the same texts in
their common form `all`:

```json
"texts": {
  "announce": "{coupleNames} are getting married!",
  "invite": "We look forward to seeing you on {eventDate} at {eventTime}." }
```

### The link preview description

The description of the link card is built from the same named texts in their
common form; `{event…}` take the **main** event, so the description is the
same for every guest:

```json
"linkPreview": { "description": "{text:announce} {text:invite}" }
```

gives "Alice & Bob are getting married! We look forward to seeing you on
15 June 2030 at 16:00." Line breaks become spaces. A text with forms but no
`all`, `{greeting}` (directly or through a text) and an object of forms in
the field itself are errors. Put the main point into the first 80 characters
(what WhatsApp shows); beyond 200 characters there is a warning. `//` and
`http` in the description fail the output check (an external address in a
`<meta>` tag). No field, no description.

### A note for a guest

On a section, a card at the end of the section; on an event, inside the
event card:

```json
"sections": { "personal": { "note": "Remember how we met on the train?\n\nSee you soon!" } },
"events": { "dinner": { "note": "Please tell us about your allergy, and we will keep it in mind." } }
```

A section without widgets (`"widgets": []`) suits a personal note: whoever
has no note does not see the section at all.

### An event for some guests only

The event is hidden in the registry and switched on for the guests it is for;
the others see all the other events, and the hidden one is not on their page:
no card, no date, no link to its calendar file.

```json
"brunch": { "title": "The day after", "location": "terrace",
            "start": "2030-06-16T12:00:00+03:00",
            "end": "2030-06-16T15:00:00+03:00", "visible": false }
```

```json
"events": { "brunch": { "visible": true } }
```

### A link to another page of the site, switched on by hand

The event declares the link once, hidden by default; `{token}` makes the
address personal (a page of the site made for this guest):

```json
"dinner": { "title": "Wedding dinner", "location": "manor", "start": "2030-06-15T16:00:00+03:00",
            "links": { "photos": { "text": "Photos from the dinner", "href": "/photos/{token}/" } } }
```

The guests who should see it get it switched on:

```json
{ "token": "…", "greeting": "Dear Dave,",
  "events": { "dinner": { "links": { "photos": { "visible": true } } } } }
```

The button "Photos from the dinner" appears in the dinner card of these
guests only, right after "Add to calendar", and leads to
`/photos/<their token>/`. The build does not write that page, so its
directory is allowed explicitly:

```
python3 build.py build --data path/to/data --media path/to/media --out path/to/site/invite --base-path /invite --allow-path /photos
```

Whether the page exists is up to whoever publishes the whole site. A link
switched on for a guest who does not see the event, or whose page shows the
event in no "Events" widget, gets a warning.

### A text in place of a link until it is switched on

The guests who do not have the link may see a line in place of the button,
in their form of address:

```json
"links": { "photos": { "text": "Photos from the dinner", "href": "/photos/{token}/",
                       "pending": "Photos from the dinner will appear here after the celebration — we will let you know" } }
```

A guest without the link sees the line, muted, right after "Add to
calendar"; the guests who have it switched on see the button instead.
Switching the link on for one more guest (`"visible": true` in their
invitation) replaces the line with the button on their page; nothing else
changes.

### The primary event of a guest

A guest invited to the ceremony only should have it as their primary event:
the cover, the date, the countdown and `{eventDate}` then take its time.

```json
{ "token": "…", "greeting": "Dear Peggy and Victor,", "primaryEvent": "ceremony" }
```

When the main event (`mainEvent`) is hidden from a guest, `primaryEvent` is
required.

### A text with forms of address

Any ordinary section with a text widget:

```json
{ "id": "rsvp", "title": "RSVP", "align": "center",
  "widgets": [
    { "type": "text",
      "text": { "informal": "Let us know by {rsvpDeadline}!",
                "formal": "Kindly reply by {rsvpDeadline}." } },
    { "type": "text", "variant": "signature", "text": "{coupleNames}" } ] }
```

The guests whose pages show it need a `form`. The title of a section can be a
text with forms or a placeholder too: `"title": "{greeting}"`.

### Photos and videos

Put the file into the media directory, describe it in the registry and show
it with a "Media" widget or in the `photos` of a place:

```json
"media": {
  "story-1": { "type": "image", "file": "story-1.jpg", "alt": "Our first meeting" },
  "walk": { "type": "video", "file": "walk.mp4", "poster": "walk-poster.jpg",
            "width": 1280, "height": 720, "alt": "A walk around the manor" } }
```

```json
{ "id": "story", "title": "Our story",
  "widgets": [ { "type": "media", "items": ["story-1", "walk"] } ] }
```

Any supported image format works (the examples use `.png`). A video is
`.mp4` only (H.264 and AAC, `+faststart`), and its poster is required and of
the same proportion; how to prepare the file is in [video.md](video.md). A
single large video is `"layout": "single"`, a row that scrolls sideways on a
phone is `"layout": "ribbon"`.

### A photo on the cover

Put the picture into the media directory, describe it in the registry (no
`alt` is needed: the background is decoration) and name it on the cover:

```json
{ "id": "cover", "type": "cover", "background": "cover", "backgroundFocus": "center" }
```

```json
"media": { "cover": { "type": "image", "file": "cover.jpg" } }
```

The photo fills the cover at any screen proportion: whatever does not fit is
cropped, with no bars. Over the photo lies a translucent veil of the cover
colour, and all of the text on the photo is in the main text colour, so it
reads on any frame, even an almost black one. The photo looks muted, by
design. One frame serves every screen:

- **the file**: a long side of 2000–2400 px, JPEG at about quality 70 or
  WebP, **at most about 400 KB** (compression artefacts disappear under the
  veil). The build does not shrink the file; over 1 MiB there is a warning:
  the photo loads first, before everything else;
- **the focus** (`backgroundFocus`) is the part of the frame that stays in
  view when the screen crops it. A phone in portrait crops a landscape frame
  left and right, a wide screen top and bottom. `center` by default; faces
  near the top call for `top`, a couple on the left for `left`, and the
  corners are `top-left`, `bottom-right` and so on. Check it by opening the
  page in a narrow and a wide window;
- the cover is printed without the photo.

Without `background` the cover is a single colour (as in the example without
a venue).

### Map buttons

A button appears only for the map the place is given for in `maps`;
coordinates alone are not enough. A place with an organisation card is given
by identifiers, a separate entrance to a large building by a query with the
town:

```json
"manor": { "name": "Example Manor", "geo": { "lat": 12.345678, "lng": 23.456789 },
           "maps": { "googlePlaceId": "EXAMPLE-not-a-real-place-id",
                     "yandexOrgId": "1000000001", "applePlaceId": "IEXAMPLE0000001" } },
"registry": { "name": "Exampleton Register Office",
              "maps": { "googleQuery": "Guest entrance, Register Office, Exampleton",
                        "yandexGeoId": "1234567890",
                        "appleQuery": "Guest entrance, Register Office, Exampleton" } }
```

When one map is enough, give only its fields. A place without `maps` (like
`hotel` in the example) has no map buttons. The formats are in
[Places](#places) and in [templates.md](templates.md#map-links).
