# Templates

`template.html` is the frame of a page: `<head>` and `<main>`, where
`<!-- include:partials/sections -->` renders the sections; the markup of the
sections and widgets lives in the fragments ([Fragments](#fragments)). The
frame and the fragments are plain HTML that a browser can open as it is.
Data goes in through three kinds of constructs — values (`{{…}}`), conditions
and lists — and nothing else. The `include` and `with` directives print no
data: `include` inserts the markup of a fragment, and `with` changes the
current item.

The `<head>` of a page holds the title and the link preview tags, the same
for every guest:

```html
<title>Invitation · Alice & Bob</title>
<meta name="description" content="Alice & Bob are getting married! We look forward to seeing you on 15 June 2030 at 16:00.">
<meta property="og:title" content="Invitation · Alice & Bob">
<meta property="og:description" content="(the same description)">
<meta property="og:type" content="website">
<meta property="og:locale" content="en_GB">
<meta property="og:site_name" content="Our invitations">   <!-- only with SITE_NAME -->
<meta property="og:image" content="/assets/…">             <!-- a path from the root: <base-path>/assets/… -->
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Invitation · Alice & Bob">
<meta name="twitter:card" content="summary_large_image">
```

"Invitation" is the `invitationTitle` string and `og:locale` the `ogLocale`
string of the language ([languages.md](languages.md)); the description
(`linkDescription`) and the site name (`siteName`) are written only when they
are set. There is no `og:url` ([data-format.md](data-format.md#link-preview)).

## Syntax

| Construct | What it does |
|---|---|
| `{{field}}` | the value of a field |
| `{{a.b}}` | a nested field (`{{primaryEvent.title}}`) |
| `{{.field}}` | a field of the current item inside `each` or `with` |
| `{{.}}` | the current item itself inside `each`, for an array of plain values only |
| `<!-- if:flag --> … <!-- endif -->` | the block when the value is "true" |
| `<!-- if:!flag --> … <!-- endif -->` | the block when the value is "false" |
| `<!-- each:list --> … <!-- endeach -->` | the block for every item of an array |
| `<!-- with:obj --> … <!-- endwith -->` | `obj` becomes the current item `.`; `null`, `false` and `{}` skip the block |
| `<!-- include:dir/name -->` | inserts the fragment `fragments/dir/name.html`; it sees the same page fields and the same current item `.` as the place of the include |
| `<!-- include:dir/{{.type}} -->` | **choice by type**: inserts `fragments/dir/<the value of .type>.html`; only inside `each` or `with` of the same file |

Rules:

- directives are written in lower case; a field name is Latin letters,
  digits and `_`;
- "true" is `true`, a non-empty string, a non-empty array, a non-empty object
  or a number other than 0; "false" is a missing field, `null`, `false`, `""`,
  `[]`, `{}` and `0`;
- inside `each` and `with` both the fields of the item (`{{.time}}`) and the
  fields of the page (`{{coupleNames}}`) are available;
- `with` over a missing field or over a value that is not an object (a
  string, a number, an array, `true`) is a build error, and so is `with:.`;
- `{{.}}` works only for an array of strings or numbers: inserting an object
  or a nested array as a whole is a build error with a hint. Every array of
  the page tree is an array of objects, so the fragments use `{{.field}}`;
- blocks nest; an unclosed or mismatched block is a build error with the line
  number;
- a reference to a field that does not exist is a build error (a typo never
  turns into an empty spot);
- a comment that does not look like a directive stays an ordinary HTML
  comment and is **removed from the finished page**, so notes in the template
  never reach the output.

**Fragments.** Shared pieces of markup and the markup chosen by the data live
in the `fragments/` directory next to `template.html`:

- the name of a fragment is the path to its file without `.html`: parts of
  `a-z`, `0-9` and `-`, each starting with a letter and at most 40 characters
  long, separated by `/` (`widgets/text` is `fragments/widgets/text.html`).
  The directory holds only `.html` files and subdirectories: a symbolic link
  or another extension is a build error, and files and directories whose
  names start with a dot are skipped. Without the directory there are no
  fragments;
- every fragment is read and checked once, before any page is built; no file
  is read while rendering. The build stops before rendering when a fragment
  has a syntax error (the message names the file and the line), when a
  fragment that does not exist is included, when fragments include each other
  in a circle, or when a choice by type stands outside `each`/`with` or leads
  to an empty or missing directory. The `each`/`with` of a choice by type
  must be in the same file: a choice at the top level of a fragment is an
  error even when the fragment itself is included inside `each`;
- `{{.field}}` in a fragment outside its own `each`/`with` is a field of the
  item at the place of the include. Such a fragment, and a fragment that
  includes it outside its own `each`/`with`, may be included in
  `template.html` only inside `each` or `with`, otherwise it is a build
  error;
- **a choice by type**: the directory is chosen by the template, the data
  picks only a file name in it. The value of the field is a string of one
  name part (no `/`), the name of a fragment directly in that directory.
  Anything else is a build error: "the value of '.type' is not a fragment
  name" or "no fragment in fragments/widgets/ for the value of '.type'
  (known: …)". The value itself never reaches the message; the known names
  come from the files of the code. Only a field of the current item can
  choose, a nested one included (`{{.media.type}}`); the fragment gets the
  item itself;
- an error while rendering a fragment (a missing field, an unknown type)
  names the fragment file, the line and the chain of includes:

  ```
  fragments/widgets/text.html line 5: field '.txt' not found (included from fragments/sections/custom.html line 8 <- template.html line 33)
  ```

- fragments nest at most 12 levels deep; beyond that is a build error (which
  stops a recursion through the data);
- a block (`if`, `each`, `with`) opens and closes in one file;
- escaping, line breaks, "false" values, the error on a missing field and the
  removal of comments work in fragments as they do in `template.html`;
- there is no access to the fields of an outer item, no comparison, no
  parameters of an include and no `else`: the build puts what is needed into
  the item itself; instead of parameters there is
  `<!-- with:… --><!-- include:… --><!-- endwith -->`, and instead of `else`
  a pair `if:x` / `if:!x`.

## How text is inserted

A value is escaped first (`<`, `>`, `&`, quotes, and also `{` and `}`), then
its line breaks become markup:

- `\r\n` and `\r` become `\n`;
- an empty line (two or more line breaks in a row) becomes `</p><p>`;
- a single line break becomes `<br>`;
- empty lines at the start and the end are dropped.

Hence the rule: **a multi-line field must be the only content of its
`<p>…</p>`**:

```html
<p>{{.note}}</p>                         <!-- right -->
<p>A note: {{.note}} — thank you!</p>    <!-- wrong: paragraphs would break the markup -->
```

The fields that go into headings, attributes and labels (section titles,
`greeting`, `coupleNames`, `rsvpDeadline`, the names of events and places,
addresses, the directions credit, `time` and `title` of programme items,
`alt`) are checked to be one line already when the data is validated
([data-format.md](data-format.md#lines-and-paragraphs)); the build writes the
dates itself.

## What a template may not do

The build **rejects** the following. The check runs on the finished pages,
not on the template ([cli.md](cli.md#what-is-checked)), so data cannot get
around it:

- **literal `{{` and `}}`** outside a placeholder: they mean an unfilled
  placeholder (in the data `{{` is safe: it is escaped);
- **`<style>`**: styles come only from files in `assets/`;
- **inline scripts and event handlers** (`onclick=…`): scripts come only from
  files;
- **`<meta http-equiv="refresh">`**, `<iframe>`, `<object>`, `<embed>`,
  `<frame>`, `<base>`;
- **CDATA (`<![…`) and processing instructions (`<?…`)**;
- **any HTML comment in the result**: comments are removed while rendering,
  and one that survives (say, after an unclosed `-->`) stops the build;
- **text that the parser sees as text but a browser may read as markup**: the
  contents of `<title>` and `<textarea>` inside `<svg>`, and the tail of an
  unclosed comment; there `<` before a letter, `/`, `!` or `?` is not
  allowed;
- relative paths to resources: only absolute paths from the root of the site
  under `--base-path` (`{{assetsPath}}/…`, that is `<base-path>/assets/…`);
  an address outside `--base-path` points outside the output and is an error
  too.

**Reserved words.** A comment that starts with `if:`, `each:`, `with:`,
`include:`, `endif`, `endeach` or `endwith` (in any letter case) is read as a
directive, and a badly written directive is a build error. Ordinary notes in
the template and the fragments never start like that. A directive left in a
finished page stops the build.

**A rule the build cannot check.** The parser reads a literal `<` in plain
text (`<y z>`, `</b c>`) as a tag: for it this is markup, not text, so such a
line passes the checks and reaches the page as an unknown element. So a
less-than sign in the text of a template is always written as `&lt;`. Data
needs no such care: values are escaped when inserted.

## The page tree

The template and the fragments do not get the data as it is, but the **page
tree** of a guest (`tools/_page.py`), which the build makes for every
invitation:

- whatever the guest does not see is not in the tree at all: no sections,
  widgets or events of theirs, no notes of other guests, no links to the
  calendar files of hidden events;
- texts are ready: the form of address is picked and the placeholders are
  filled in;
- the dates, the addresses of files (with hash names), the map links, the
  sizes and durations of media and the DOM ids are computed beforehand;
- **every field always exists**: an empty string, `[]`, `false` or `null`
  stands for a missing value, so `if:` and `{{…}}` never stumble over a
  missing field. A fragment reads only the fields listed here; a test checks
  it by giving the fragments a tree in which reading any other field breaks
  the render.

**The root:**

| Field | Value |
|---|---|
| `lang` | the language tag of the site (`<html lang>`) |
| `ogLocale` | the locale of the link preview tags (`en_GB`) |
| `ui` | the labels of the language: `ui.addToCalendar`, `ui.programme`, … (the label keys of [languages.md](languages.md#the-keys)) |
| `greeting` | the guest's greeting |
| `form`, `informal`, `formal` | the form of address of the invitation (`informal`, `formal` or `""` without one) and two booleans for it |
| `coupleNames`, `rsvpDeadline` | from `site.json` (`rsvpDeadline` is `""` when not set) |
| `assetsPath` | `<base-path>/assets`, the address of the shared files: `{{assetsPath}}/app.css`, `{{assetsPath}}/app.js` (`/assets` with `--base-path /`) |
| `mediaPath` | `<base-path>/assets/<mediaDir>` |
| `faviconPath`, `faviconType` | the path and MIME type of the icon |
| `ogImage`, `ogImageType`, `ogImageWidth`, `ogImageHeight` | the link preview image |
| `themeColor` | the colour of the browser interface, an opaque `#rrggbb` from the `--color-cover-veil` token ([design-system.md](design-system.md#the-browser-colour)) |
| `linkDescription` | the link preview description: `linkPreview.description` in its common form with spaces collapsed; the same for every guest; `""` without the field |
| `siteName` | the site name of `og:site_name` (`--site-name` / `SITE_NAME`), `""` when not set |
| `primaryEvent` | the guest's primary event (an event object; its `domId` and the `domId` of its place and programme are `""`: it is not rendered on its own) |
| `sections[]` | the sections the guest sees, in order |

**A section:** `id`, `type` (`cover` or `custom`), `domId`, `titleId`,
`title`, `titleHidden`, `align`, `width`, `note` (the guest's note),
`widgets[]`, and for the cover also `eyebrow`, `event` (the primary event),
`background` (the photo behind it, a media object or `null`) and
`backgroundFocus` (a value of the enumeration, `center` by default; `""` for
an ordinary section). Sections of both types have all of these fields; the
ones that do not apply are empty. The background photo is published like any
media shown, under a hash name.

**A widget:** `type`, `domId`, `labelledBy` (the `titleId` of its section)
and the fields of its type:

| Type | Fields |
|---|---|
| `text` | `text` (a ready string), `variant` |
| `date` | `event`, `countdown`, `calendar`, `showEventTitle` (the guest sees more than one event) |
| `events` | `items[]` (events), `count`, `multiple`, `primaryDomId` (the `domId` of the card of the primary event, or `""`) |
| `location` | `location` (a place, `nested: false`) |
| `schedule` | `items[]` (programme items), `nested: false` |
| `media` | `items[]` (media), `layout` |

**An event:** `id`, `domId`, `title`, `description`, `note` (the guest's
note), `isMain`, `isPrimary`, `kind` (`primary` or `regular`), `startISO`,
`endISO` (the end: `end` or the start plus six hours; on the page only in
`data-events-end`), `dateText` ("15 June 2030"), `timeText` ("16:00"),
`dateTimeText` ("15 June 2030, 16:00", the date widget), `whenText`
("Saturday, 15 June 2030, 16:00"; with `showEnd` "…, 16:00–23:30"), `tabText`
("16:00", or "15 June, 16:00" when the guest's events fall on different
days), `icsPath` (`<base-path>/assets/<mediaDir>/<hash>.ics`, the event's
calendar file), `location` (a place, `nested: true`), `program`
(`{domId, items[], nested: true}`, or `null` without a programme) and
`links[]` (the event links on the guest's page in the order of their keys,
see below; `[]` without links). The strings of the dates follow the patterns
of the language ([languages.md](languages.md#date-and-time-patterns)).

**An event link** (`links[]`) is one of two kinds. A link the guest sees has
`id`, `href` with `{token}` replaced by their token, `text`, and `pending`
`""`. A hidden link with a text in its place
([data-format.md](data-format.md#event-links)) has that text in `pending`,
ready (the form of address, the named texts and the placeholders resolved),
and `href` and `text` `""`: no token, no address. A hidden link without such
a text is not in the list. A link has no `domId`. The tree of the link
preview page has no links at all.

**A place:** `id`, `domId`, `ready`, `name`, `address`, `description`,
`mapLinks` (`google`, `yandex`, `apple`: a ready link or `""`),
`hasMapLinks`, `photos[]` (media), `directions` (a media object or `null`),
`directionsCredit` (`""` without a credit or without a map), `compact`,
`nested`. A place that is not announced (`ready: false`) has every field
empty.

**A media item:** `id`, `type` (`image` or `video`), `isVideo`, `src`,
`posterSrc`, `thumbSrc` (`thumb`, otherwise the poster, the file itself for a
photo), `width`, `height` (`""` when the size is unknown), `ratio`
(`"w / h"`), `durationText` ("0:20"), `label` ("Video: <alt>, 0:20", built
from the `video` string) and `alt` (the `photo` or `video` string without
one). The addresses carry hash names
([data-format.md](data-format.md#the-media-directory-and-file-names)); the
file names of the data never reach them.

**A programme item:** `time`, `title`, `text`.

The link preview page (`preview.html`) gets a smaller tree: `lang`,
`coupleNames`, `assetsPath` and `cover`, the cover section of nobody in
particular (the main event, no greeting, no links).

**The script hooks of the `events` widget.** The page script (its `events`
module) finds its elements only by these attributes; the texts of the marks
are in the markup, the script has no words of its own.

| Hook | Where | Meaning |
|---|---|---|
| `data-events` | the root of the widget | one tab switcher |
| `data-events-primary` | the root | `primaryDomId`: the fallback choice when the time cannot be read |
| `data-events-tablist` | the list of tabs | hidden with `hidden` in the markup; the script shows it as its last step |
| `data-events-tab` | a tab (`button`) | `aria-controls` is the `domId` of its card |
| `data-events-panel` | an event card | a panel; the script sets the role `tabpanel`, `tabindex` and `aria-labelledby` pointing at the tab |
| `data-events-start`, `data-events-end` | a card | `startISO` and `endISO`, moments with an offset |
| `data-events-when="past"` / `"now"` | in the tab and in the time line of the card | the "past" and "happening now" marks, hidden with `hidden` |

The states the script sets are for the styles: on a tab `aria-selected="true"`
and `tabindex="0"` (on the selected one only), on a tab and a card the classes
`is-past` (the event is over) and `is-now` (it is on), on the inactive cards
`hidden`, and on the list of tabs the CSS variable `--events-count` (the
number of tabs, set through the CSSOM: there is no `style` attribute in the
markup). On any error the script restores the view without it.

## Map links

Each map takes the first value given: the identifier, then the query of that
map. With neither there is no button for that map, even when the place has
`geo`.

| Map | By identifier | By query |
|---|---|---|
| Google | `https://www.google.com/maps/search/?api=1&query=<query or name>&query_place_id=<googlePlaceId>` | `https://www.google.com/maps/search/?api=1&query=<googleQuery>` |
| Yandex | `https://yandex.ru/maps/org/<yandexOrgId>` or `https://yandex.ru/maps/geo/<yandexGeoId>/` | `https://yandex.ru/maps/?text=<yandexQuery>&ll=<lng>,<lat>&z=16` |
| Apple | `https://maps.apple.com/place?place-id=<applePlaceId>&coordinate=<lat>,<lng>&name=<name>` | `https://maps.apple.com/search?query=<appleQuery>&center=<lat>,<lng>` |

- **Google** needs `query` next to `query_place_id`, and uses it only when
  the identifier is not found. It gets `googleQuery`, otherwise the name,
  otherwise the coordinates, otherwise the address. Google search takes no
  area hint, so the town goes into the query itself;
- **the area hint**, `ll` for Yandex (longitude first) and `center` for
  Apple, is added only when the place has `geo`; without it the link holds
  the query alone;
- **Apple**: `coordinate` and `name` next to `place-id` are the fallback when
  the identifier is not recognised; each is added only when it exists;
- queries, names and identifiers are encoded as a whole (UTF-8, a space is
  `%20`), so `&`, `#`, `?`, quotes and non-Latin letters do not break a link.

Without any link there is no block of buttons at all. Every external link
opens with `target="_blank" rel="noopener noreferrer"`, which the output
check verifies.

## Fragments

A page is an ordered list of sections, a section a list of widgets. The
markup of each kind lives in its fragment; `template.html` includes
`partials/sections`, which includes the sections by type. The fragments read
[the page tree](#the-page-tree); the tests render them both on trees written
by hand and on trees the build makes.

```
fragments/
  partials/sections.html     every section in order: the contents of <main>
  sections/cover.html        the cover: the only h1 (the names), the date, the photo; then the top bar
  sections/custom.html       the frame of an ordinary section
  widgets/text.html          text: variant body | lead | signature
  widgets/date.html          the date of an event (the primary one by default), the countdown, the calendar button
  widgets/events.html        events: the tab list (hidden without the script) and the cards (calendar and link buttons)
  widgets/location.html      a place card
  widgets/schedule.html      a programme as a widget (its items are h3)
  widgets/media.html         a gallery: layout grid | ribbon | single
  media/image.html           a photo tile
  media/video.html           a video tile: the poster, the ▶ badge, the duration
  partials/section-head.html the section heading (h2, visually hidden with titleHidden)
  partials/section-note.html the guest's note at the end of a section
  partials/location-card.html a place: full, compact, not announced
  partials/map-links.html    the map buttons
  partials/schedule.html     a programme: items are h5 in an event card, h3 in the widget
  partials/countdown.html    the countdown (hidden until the script starts)
```

**The file name is the type.** The frame chooses a fragment by the `type`
field of the current item: `include:sections/{{.type}}`,
`include:widgets/{{.type}}`, `include:media/{{.type}}`. `sections/`,
`widgets/` and `media/` hold only fragments that can be chosen; shared pieces
live in `partials/`, so the data can never choose a helper fragment. The
first line of every fragment is a comment that says what it expects in `.`
and which fields it reads; it is removed from the finished page like every
comment. A fragment reads only fields of the page tree, and the tree always
has them.

**The frame of a section** (`sections/custom.html`):

```html
<section class="section section--{{.align}}" id="{{.domId}}" aria-labelledby="{{.titleId}}">
  <div class="container container--{{.width}}" data-reveal>
    <!-- include:partials/section-head -->
    <div class="stack section__body">
      <!-- each:.widgets --><!-- include:widgets/{{.type}} --><!-- endeach -->
      <!-- include:partials/section-note -->
    </div>
  </div>
</section>
```

A class modifier is filled in from a field only for checked enumerations:
`align` (`start` | `center`), `width` (`narrow` | `wide`), `variant`,
`layout`, `kind` (`primary` | `regular`) and `backgroundFocus` (the focus of
the cover photo: `cover__photo--top` and so on). Every other difference is a
pair `if:x` / `if:!x`.

### DOM ids

The build makes the DOM ids from the path in the configuration; the
fragments only append constant suffixes. The parts of the path and the
suffixes are joined with `--`: an id of the data never has two hyphens in a
row, so different paths never give the same id.

| What | id |
|---|---|
| a section | `s-<section>` |
| the heading of a section | `s-<section>--title` |
| a widget | `s-<section>--w<N>`, N being the position of the widget in the configuration from 1 (hidden widgets count too) |
| an event | `<parent>--e-<event>`, the parent being a date or events widget (`s-where--w1--e-dinner`) or the cover (`s-cover--e-dinner`); the tab is `…--tab`, the heading of the card `…--title` (appended by the fragment) |
| the programme of an event | `<event>--program` (made by the build) |
| a place | `<event or place widget>--l-<place>` (`s-where--w1--e-dinner--l-manor`) |
| `primaryEvent` at the root of the tree, its place and programme | `""`: they are not rendered on their own |

The ids of the registries are not used on their own: one event may appear
twice on a page (in a date widget and among the events), while a path is
always unique. The build still checks the tree of every page and stops with
an error on a repeated id.

### The event card

The head of an event card ends with the paragraph of the calendar file, and
every event link on the guest's page (`links[]`) follows it as a paragraph of
its own, on the same line of the fragment: a button, or the text in its place
when `pending` is not empty:

```html
<p class="events__actions"><a class="btn btn--secondary" href="{{.icsPath}}" type="text/calendar">{{ui.addToCalendar}}</a></p><!-- each:.links --><!-- if:!.pending --><p class="events__actions"><a class="btn btn--secondary" href="{{.href}}">{{.text}}</a></p><!-- endif --><!-- if:.pending --><p class="events__actions card__text">{{.pending}}</p><!-- endif --><!-- endeach -->
```

A paragraph of its own keeps two buttons from touching when they wrap on a
phone: the spacing of `.events__head > .events__actions` applies. The text in
place of a button is a plain paragraph in the same place with the same
spacing, in the muted text colour of a card (`card__text`); it needs no
script and prints as it is shown. The date widget and the cover show neither.

**Heading levels:** h1 is the cover; h2 a section; h3 an event, the name of a
place in a place widget, and the items of a programme widget; h4 a place
inside an event and the "Programme" subheading; h5 the items of an event's
programme. A piece that appears at different depths (a place card, a
programme) picks its tag by the `nested` flag. Widgets have no headings of
their own: a block with its own heading is a section of its own.

### The cover and the top bar

As the page scrolls, the cover collapses into a bar at the top of the window:
the text of the cover and its photo fade, and a bar with one line,
"names · date", fades in and sticks to the top. The bar is a separate element
right after the cover, in the same fragment:

```html
<section class="cover" id="{{.domId}}" aria-labelledby="{{.titleId}}" data-cover> … </section>
<div class="cover-bar" aria-hidden="true" data-cover-bar>
  <div class="container cover-bar__inner"><span class="cover-bar__title">{{coupleNames}}</span><span class="cover-bar__sep">·</span><span class="cover-bar__date">{{.event.dateText}}</span></div>
</div>
```

| Hook or marker | Meaning |
|---|---|
| `data-cover` | the cover, whose scrolling drives the collapse |
| `data-cover-bar` | the bar: a copy of the names and the date, hidden from screen readers (`aria-hidden`), with nothing focusable in it, so the page still has one h1 |
| `html.cover-bar-on` | the marker the `coverBar` module of the page script sets; only under it is the bar visible, and a jump to an anchor stops below its height (`scroll-padding`) |
| `--cover-progress` | the progress of the collapse, 0…1, on the cover and the bar, for browsers without CSS scroll timelines (`animation-timeline`, `timeline-scope`; iOS 18 and older): the `coverBar` module writes it once a frame through the CSSOM. Where the timelines exist, CSS fades the veil, the text of the cover and the bar with three `opacity` animations right on the timeline, and the module only sets the marker |

The bar stands in the flow with a negative margin of its own height and takes
no room: its appearance does not shift the layout. Without the script the
cover stays still and there is no bar; with "Reduce motion" the cover does
not change on scroll and the bar appears at once when the cover is gone; in
print there is no bar and the cover is unfolded.

### On touch screens the body scrolls

On a touch screen (`@media screen and (pointer: coarse)`), the invitation
page (`html.invitation`, section 3 of `app.css`) makes `<html>` and `<body>`
exactly the size of the window: `<html>` does not scroll
(`overflow: hidden`), `<body>` does (`overflow-y: auto`). The contents are
then clipped at the edge of `body`, and nothing that scrolls shows above the
layout viewport, under the translucent header of the Telegram in-app browser
on iOS or the status bar of Safari on iOS 26 ([testing.md](testing.md#the-area-above-the-bar)).
The bar sticks to the top of `body`, and the timeline of the cover follows
its scrolling. On a desktop (where the main pointer is a mouse or a touchpad)
the document scrolls as usual: the keyboard scrolls the page right after it
loads, and a reload keeps the position. The main pointer decides: a PC with a
touch screen and a mouse usually gets document scrolling, an iPad with a
keyboard gets body scrolling. So the scripts and the styles of the page work
with both kinds of scrolling:

- the scroll position is read from whatever scrolls: `document.body`
  (`scrollTop`) when its `overflow-y` is not `visible`, otherwise the window
  (`window.pageYOffset`, always 0 in body mode);
- the `scroll` event of an element does not bubble up to `window`: a listener
  on `window` uses `capture: true` (and is removed with the same flag);
- the margin under the bar (`scroll-padding-block-start`) and the scroll lock
  under the viewer are set on `body` as well;
- the width of the scroll bar (the margin under the viewer) is measured on
  `body` too;
- print is the plain document: the rules are for screens only. The
  styleguide has no `invitation` class and scrolls as usual.

### Reveal and the page without a script

**The reveal mark `data-reveal`** is exactly one per section, in the frame, on
the container of the heading and the body. It is not on the cover or the bar
(they have their own animation), on widgets, list items, tiles, event cards,
the tab list, the countdown or notes: nested marks would flash twice, and an
element that the script or the `hidden` attribute hides would blink. A test
checks the rule both on the fragment files and on the finished pages.

**Without a script everything is visible**: the event tab list, the countdown
and the "past" and "happening now" marks are hidden with `hidden` and shown
by the script (the top bar is a copy of the cover and simply does not exist
without it); the event cards follow one another, the primary one with an
accent border; tiles are plain links to the files. The words of the pages
come from the `ui` labels; the script takes its own from the strings line of
`assets/app.js` ([languages.md](languages.md#the-keys)).

### Adding a widget type

1. A file `fragments/widgets/<type>.html` with one root element
   `class="widget <type>-widget"` (and `id="{{.domId}}"` when an anchor or
   ARIA links need it) and the contract comment on its first line.
2. The type and its fields in the data checks (`WIDGET_TYPES`,
   `WIDGET_FIELDS` in `tools/_schema.py`) and in the page tree
   (`tools/_page.py`); the description in
   [data-format.md](data-format.md#widgets) and in [the page tree](#the-page-tree).
3. A row in the contract table `WIDGET_FIELDS` of
   `tests/test_fragments_contract.py` (the test takes the list of types from
   `tools/_schema.py` and compares it with the files of
   `fragments/widgets/`), and an example widget in `widget_variants()`.
4. The styles in the "Widget: <type>" part of section 6 of `app.css`, tokens
   only.
5. A demonstration in the markup of `styleguide.html`, in a block of its own
   `<!-- sg:<component> --> … <!-- /sg:<component> -->`.

## Third-party code

The pages use no third-party library: they run on two files of their own,
`app.css` and `app.js`, and a video plays in the native `<video controls>`
with the browser's own panel ([video.md](video.md#the-tile-and-the-viewer)).

Should a library ever be needed, it comes on these terms:

- **local files only**, in a directory of `assets/` named after the library
  and its version, which is added to the allowed directories of `assets/`
  (`ASSET_DIRECTORIES` in `build.py`; the output check allows only `fonts/`
  and the media directory there). A CDN or any other external address is
  forbidden, including the ones the library reaches for by itself (icons,
  fonts, blank videos, statistics): its settings switch them off, and a test
  pins that;
- **a fixed version**: the version number is in the directory name, and the
  source of the package, its checksum and the list of its files with their
  checksums are recorded in the docs;
- **an acceptable licence** (MIT, BSD, Apache 2.0 and the like), its text
  next to the files as `LICENSE.txt`: `.md` files are never published;
- **compatible with the Content Security Policy**
  ([deploying.md](deploying.md#headers-and-the-content-security-policy)):
  no inline scripts, no `eval` and no `new Function`; the policy is never
  relaxed for a library;
- **weight**: all third-party code together at most about 150 KB after gzip;
  no `*.map` files;
- **the template stays plain HTML**: the library improves the finished
  markup, it does not build the page, and without it the contents are fully
  available;
- **media files** (an SVG sprite of icons, say) in that directory only
  together with a deliberate exception in the repository hygiene rule
  ([testing.md](testing.md#continuous-integration)) and a test for that
  exception; `.js`, `.css`, `.woff2` and `.txt` files are not affected by the
  rule.

The build copies `assets/` into the output (all but the styleguide and link
preview files), so such files would be in the output of any data set, even
when no page refers to them.
