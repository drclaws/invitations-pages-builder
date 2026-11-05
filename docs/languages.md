# Languages

Every word the pages say on their own — "Add to calendar", the countdown
units, the names of months, the labels of the photo viewer — and the way
dates and times are written come from the **strings** of the site. Two sets
of strings are built in, English (`en`) and Russian (`ru`); any other
language is a matter of data.

- `site.json` `"lang"` picks the language; without it the pages are in
  English.
- `site.json` `"strings"` overrides any key of the built-in set, or gives
  every key for a language without one.
- The texts of the data (titles, descriptions, notes) are written in the
  language of the site anyway; the strings cover only what the pages add.

## Choosing the language

`"lang"` is a language tag in the BCP 47 form: a language, then optionally a
script, a region and variants (`en`, `en-GB`, `ru`, `sr-Latn`, `pt-BR`). It
goes into `<html lang>` as written, which tells screen readers how to speak
the page and the browser which plural rules to use. A value
of another shape is an error (`must be a language tag such as 'en', 'ru' or
'sr-Latn'`).

The primary subtag, in lower case, picks a built-in set: `tools/locales/en.json`
for `en`, `en-GB` or `en-US`, `tools/locales/ru.json` for `ru` or `ru-RU`.
Every other language has no built-in set.

`validate` and `build` name the language in their log, so a forgotten
`"lang"` is easy to spot:

```
validate: language: en (default)
```

The built-in English set writes dates in the international way: "Saturday,
15 June 2030, 16:00". The built-in Russian set is in
`tools/locales/ru.json`, and `examples/data-ru/` is the main example in
Russian, with the informal and formal forms of address
([data-format.md](data-format.md#forms-of-address)).

## Overriding strings

`"strings"` is an object of keys of the set. It goes over the built-in set of
the language:

- the groups `countdown` and `lightbox` merge key by key, so one label of the
  viewer can be changed alone;
- every other key replaces the built-in value as a whole: a list (`months`,
  `weekdays`, `ampm`) and the plural forms of one countdown unit are always
  given in full.

An unknown key is an error with a "did you mean" hint. The values are checked
by their kind: a label is a non-empty line; a list has exactly its number of
lines; a pattern uses only its own placeholders, has every placeholder it
needs and no stray brace; plural forms are an object of plural categories
with at least `other`. A placeholder name longer than 32 characters is left
out of the message (`has an unknown placeholder; known: …`).

```json
"strings": {
  "addToCalendar": "Save the date",
  "lightbox": { "close": "Back to the invitation" }
}
```

Strings are data of the whole site, never of a guest: they may go into the
files every page shares.

## The keys

Every key, its kind and its value in the built-in English:

| Key | Kind | English | Where it shows |
|---|---|---|---|
| `ogLocale` | text | en_GB | the `og:locale` tag of the link preview |
| `invitationTitle` | label | Invitation | the page title and the link preview: "Invitation · Alice & Bob" |
| `addToCalendar` | label | Add to calendar | the calendar button |
| `programme` | label | Programme | the heading of a programme in an event card |
| `directions` | label | Directions | the caption of a directions map |
| `placePending` | label | Details will appear on this page later. | the card of a place that is not announced |
| `openOnMap` | label | Open in maps | the accessible name of the map buttons |
| `mapGoogle` | label | Google Maps | a map button |
| `mapYandex` | label | Yandex Maps | a map button |
| `mapApple` | label | Apple Maps | a map button |
| `past` | label | past | the mark of an event tab that is over |
| `eventPast` | label | this event is over | the mark of an event card that is over |
| `now` | label | happening now | the mark of an event that is on |
| `countdownLabel` | label | Time until the start | the accessible name of the countdown |
| `countdownDays` | label | days | a countdown unit before the script runs |
| `countdownHours` | label | hours | a countdown unit before the script runs |
| `countdownMinutes` | label | minutes | a countdown unit before the script runs |
| `countdownSeconds` | label | seconds | a countdown unit before the script runs |
| `photo` | label | Photo | the label of a photo without `alt` |
| `video` | label | Video | the label of a video tile: "Video: A walk around the manor, 0:05" |
| `months` | list of 12 | January … December | the `{month}` placeholder, in the form a date uses |
| `weekdays` | list of 7 | Monday … Sunday | the `{weekday}` placeholder, Monday first |
| `ampm` | list of 2 | am, pm | the `{ampm}` placeholder, before and after noon |
| `date` | pattern | {d} {month} {yyyy} | the cover, `{eventDate}` |
| `dayMonth` | pattern | {d} {month} | a date without the year |
| `time` | pattern | {HH}:{mm} | `{eventTime}` and every time |
| `dateTime` | pattern | {date}, {time} | the date widget |
| `when` | pattern | {Weekday}, {date}, {time} | the time of an event card |
| `rangeSameDay` | pattern | {when}–{endTime} | an event card with `showEnd`, ending the same day |
| `rangeOtherDay` | pattern | {when} – {endDay}, {endTime} | an event card with `showEnd`, ending another day |
| `tab` | pattern | {dayMonth}, {time} | an event tab when the events fall on different days |
| `countdown.days` | plural forms | one: day, other: days | the countdown, once the script runs |
| `countdown.hours` | plural forms | one: hour, other: hours | the countdown |
| `countdown.minutes` | plural forms | one: minute, other: minutes | the countdown |
| `countdown.seconds` | plural forms | one: second, other: seconds | the countdown |
| `lightbox.photos` | label | Photo viewer | the name of the viewer of a photo gallery |
| `lightbox.mixed` | label | Photo and video viewer | the name of the viewer of photos and videos |
| `lightbox.image` | label | Image viewer | the name of the viewer of a single photo |
| `lightbox.video` | label | Video viewer | the name of the viewer when every item is a video |
| `lightbox.close` | label | Close | the close button |
| `lightbox.prev` | label | Previous photo | a button of a viewer of photos only |
| `lightbox.next` | label | Next photo | a button of a viewer of photos only |
| `lightbox.prevItem` | label | Previous | a button of a viewer with videos |
| `lightbox.nextItem` | label | Next | a button of a viewer with videos |
| `lightbox.itemImage` | label | Photo | `{item}` of the position for a photo |
| `lightbox.itemVideo` | label | Video | `{item}` of the position for a video |
| `lightbox.loading` | label | Loading… | while a picture loads |
| `lightbox.error` | label | The image could not be loaded. | a picture that fails |
| `lightbox.videoError` | label | The video could not be loaded. | a video that fails |
| `lightbox.position` | pattern | {item} {n} of {total} | what a screen reader hears on moving: "Photo 3 of 5" |

The labels go into the page tree as `ui` ([templates.md](templates.md#the-page-tree));
the `countdown` and `lightbox` groups are read by the page script. The page
script has no words of its own: its source holds the English strings on one
line, `var STRINGS = {…}; /* @strings */`, and the build writes the strings
of the site on that line of the published `assets/app.js`. The pages gain no
attribute and no inline script, so the Content Security Policy stays strict.

## Date and time patterns

A pattern is text with placeholders in braces. The build fills them in on
the clock of the event's own UTC offset, never in UTC and never in the time
zone of the machine that runs it, and never from the locale of the operating
system.

| Pattern | Placeholders | Must contain |
|---|---|---|
| `date` | `{d}` `{dd}` `{M}` `{MM}` `{month}` `{yyyy}` `{weekday}` `{Weekday}` | the year, a day and a month |
| `dayMonth` | the same | a day and a month |
| `time` | `{H}` `{HH}` `{h}` `{hh}` `{mm}` `{ampm}` | an hour and `{mm}` |
| `dateTime` | `{date}` `{time}` | both |
| `when` | `{date}` `{time}` `{dayMonth}` `{weekday}` `{Weekday}` | `{date}` and `{time}` |
| `rangeSameDay` | `{when}` `{endTime}` | both |
| `rangeOtherDay` | `{when}` `{endDay}` `{endTime}` | all three |
| `tab` | `{time}` `{dayMonth}` `{date}` `{weekday}` `{Weekday}` | `{time}` |
| `lightbox.position` | `{item}` `{n}` `{total}` | `{n}` and `{total}` |

- `{d}` and `{dd}` are the day without and with a leading zero, `{M}` and
  `{MM}` the number of the month, `{month}` its name from `months`, `{yyyy}`
  the year;
- `{weekday}` is the name from `weekdays`, and `{Weekday}` the same with its
  first letter in upper case (for the start of a sentence);
- `{H}` and `{HH}` are the hour of a 24-hour clock without and with a leading
  zero, `{h}` and `{hh}` the hour of a 12-hour clock, `{mm}` the minutes,
  `{ampm}` the half of the day from `ampm`;
- `{date}`, `{time}` and `{dayMonth}` inside the other patterns are the
  results of those patterns; `{endTime}` is the time of the end, and
  `{endDay}` its `dayMonth`, or its `date` when the year changes too;
- the end of an event is shown on the clock of its start;
- an event tab shows the time alone when all of a guest's events fall on one
  day, and the `tab` pattern otherwise.

With the built-in English:

| Pattern | Result |
|---|---|
| `date` | 15 June 2030 |
| `dateTime` | 15 June 2030, 16:00 |
| `when` with `showEnd` | Saturday, 15 June 2030, 16:00–23:30 |
| `when` ending the next day | Saturday, 15 June 2030, 16:00 – 16 June, 02:00 |
| `tab` | 15 June, 16:00 |

### A US date format

The month first and a 12-hour clock are a few overrides:

```json
"strings": {
  "ogLocale": "en_US",
  "date": "{month} {d}, {yyyy}",
  "dayMonth": "{month} {d}",
  "time": "{h}:{mm} {ampm}",
  "ampm": ["AM", "PM"]
}
```

The date widget then says "June 15, 2030, 4:00 PM", and an event card with
`showEnd` "Saturday, June 15, 2030, 4:00 PM–11:30 PM".

## Plurals in the browser

The countdown runs in the browser, so its units need the right plural form
for any number. Each unit has its forms by the categories of the Unicode
plural rules: `zero`, `one`, `two`, `few`, `many` and `other`, at least
`other`. English needs `one` and `other`; Russian `one`, `few` and `many`;
Serbian `one`, `few` and `other`.

The script picks the category with `Intl.PluralRules` for the language of the
page (`<html lang>`) and uses its form, or `other` when the strings have no
form of that category. In a browser without `Intl.PluralRules`, or for a tag
the browser rejects, every number takes `other`. Before the script runs, the
countdown shows the `countdownDays` … `countdownSeconds` labels.

## A language without a built-in set

For a language without a built-in set, `"strings"` must give **every** key.
`validate` lists the missing ones in one error:

```
error: site.json: field 'strings' must give every key for 'sr-Latn', which has no built-in strings; missing: addToCalendar, ampm, countdown.days, …
```

A key that is given but broken is reported on its own and not counted as
missing.

## One language per site

The strings are part of the shared files (the page script), so one build has
one language: all the pages of a site speak it. A bilingual celebration can
write its texts in both languages, or build two sites.

## A complete Serbian Latin example

Every key, for a language with no built-in set:

```json
"lang": "sr-Latn",
"strings": {
  "ogLocale": "sr_RS",
  "invitationTitle": "Pozivnica",
  "addToCalendar": "Dodaj u kalendar",
  "programme": "Program",
  "directions": "Kako stići",
  "placePending": "Detalji će uskoro biti objavljeni na ovoj stranici.",
  "openOnMap": "Prikaži na mapi",
  "mapGoogle": "Google mape",
  "mapYandex": "Yandex mape",
  "mapApple": "Apple mape",
  "past": "prošlo",
  "eventPast": "događaj je završen",
  "now": "u toku",
  "countdownLabel": "Do početka je ostalo",
  "countdownDays": "dana",
  "countdownHours": "sati",
  "countdownMinutes": "minuta",
  "countdownSeconds": "sekundi",
  "photo": "Fotografija",
  "video": "Video",
  "months": ["januar", "februar", "mart", "april", "maj", "jun",
             "jul", "avgust", "septembar", "oktobar", "novembar", "decembar"],
  "weekdays": ["ponedeljak", "utorak", "sreda", "četvrtak", "petak", "subota", "nedelja"],
  "ampm": ["AM", "PM"],
  "date": "{d}. {month} {yyyy}.",
  "dayMonth": "{d}. {month}",
  "time": "{H}:{mm}",
  "dateTime": "{date} u {time}",
  "when": "{Weekday}, {date} u {time}",
  "rangeSameDay": "{when}–{endTime}",
  "rangeOtherDay": "{when} – {endDay} u {endTime}",
  "tab": "{dayMonth}, {time}",
  "countdown": {
    "days": { "one": "dan", "few": "dana", "other": "dana" },
    "hours": { "one": "sat", "few": "sata", "other": "sati" },
    "minutes": { "one": "minut", "few": "minuta", "other": "minuta" },
    "seconds": { "one": "sekunda", "few": "sekunde", "other": "sekundi" }
  },
  "lightbox": {
    "photos": "Pregled fotografija",
    "mixed": "Pregled fotografija i video snimaka",
    "image": "Pregled slike",
    "video": "Pregled video snimka",
    "close": "Zatvori",
    "prev": "Prethodna fotografija",
    "next": "Sledeća fotografija",
    "prevItem": "Prethodno",
    "nextItem": "Sledeće",
    "itemImage": "Fotografija",
    "itemVideo": "Video",
    "loading": "Učitavanje…",
    "error": "Slika nije mogla da se učita.",
    "videoError": "Video nije mogao da se učita.",
    "position": "{item} {n} od {total}"
  }
}
```

The date widget then says "15. jun 2030. u 16:00", and an event card
"Subota, 15. jun 2030. u 16:00".

## Fonts

The default font is the system stack (San Francisco, Segoe UI, Roboto, Noto,
DejaVu and others), which covers Latin with its extended letters (č, ć, š, ž,
đ and the like) and Cyrillic on every common platform. A custom font
([design-system.md](design-system.md#local-fonts)) must include the subsets
of the language of the site: a font without them falls back to the system
font letter by letter, which looks patchy.

## A new built-in set

A built-in set is a file `tools/locales/<primary subtag>.json` with every
key. The unit tests check that every built-in set is complete and that each
value is of its kind.
