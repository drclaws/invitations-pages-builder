"""Fictional data in the format 2, as Python objects, and helpers around it.

`SITE` / `INVITATIONS` are the main set (`examples/data`): eight invitations
that cover every combination of a guest from another city and a companion, a
different primary event, hidden and switched-on events, notes for sections
and events, a link of an event switched on for two invitations (the others
see a text in its place), a place that is not announced yet, events on two
days, an event description, photos with a portrait and a landscape video, a
single video and a ribbon of photos, and a photo behind the cover.
`PENDING_SITE` / `PENDING_INVITATIONS` (`examples/data-venue-pending`) are the
set without places and media (and a cover without a photo).  Both are in
English, the default language, and need no forms of address; the Russian
set with the forms is `tests/fixtures_ru.py`.

There are no media files: `MEDIA_INFO` stands for what the build would read
from them.  Use `site()` / `invitations()` for copies that a test may change.
"""

from __future__ import annotations

import copy
from datetime import timedelta

from tools._media import MediaInfo
from tools._page import PageSettings

MEDIA_DIR = "kR1sKvBGXluXnZd73eOXRw"

SITE = {
    "schemaVersion": 2,
    "coupleNames": "Alice & Bob",
    "rsvpDeadline": "1 May 2030",
    "mediaDir": MEDIA_DIR,
    "mainEvent": "dinner",
    "texts": {
        "announce": "{coupleNames} are getting married!",
        "invite": "We look forward to seeing you on {eventDate} at {eventTime}.",
    },
    "linkPreview": {"description": "{text:announce} {text:invite}"},
    "sections": [
        {
            "id": "cover",
            "type": "cover",
            "eyebrow": "You are invited",
            "background": "cover",
            "backgroundFocus": "center",
        },
        {
            "id": "invite",
            "title": "{greeting}",
            "align": "center",
            "widgets": [
                {
                    "type": "text",
                    "variant": "lead",
                    "text": "{text:announce}",
                },
                {
                    "id": "plus-one",
                    "type": "text",
                    "variant": "lead",
                    "visible": False,
                    "text": "You are welcome to bring a partner or a friend.\n"
                    "Please let us know their name in advance.",
                },
                {
                    "type": "text",
                    "variant": "lead",
                    "text": "{text:invite}\nWe would love to share this day with you.",
                },
            ],
        },
        {"id": "personal", "title": "A few personal words", "widgets": []},
        {
            "id": "when",
            "title": "Date and time",
            "align": "center",
            "widgets": [{"type": "date"}],
        },
        {
            "id": "where",
            "title": "Where and when",
            "width": "wide",
            "widgets": [{"type": "events"}],
        },
        {
            "id": "travel",
            "title": "For guests from out of town",
            "visible": False,
            "widgets": [
                {
                    "type": "text",
                    "text": "On the day, a shuttle runs between Exampleton station and the "
                    "manor.\n\nIt leaves the station at 14:45\nand goes back at 23:15.",
                },
                {"type": "location", "location": "hotel", "variant": "compact"},
                {
                    "id": "hotel-booked",
                    "type": "text",
                    "visible": False,
                    "text": "We have booked a room for you at this hotel.",
                },
            ],
        },
        {
            "id": "story",
            "title": "Our story",
            "widgets": [
                {"type": "media", "layout": "single", "items": ["proposal"]},
                {"type": "media", "layout": "ribbon", "items": ["story-1", "story-2"]},
            ],
        },
        {
            "id": "rsvp",
            "title": "Reply",
            "align": "center",
            "widgets": [
                {
                    "type": "text",
                    "text": "Please reply by {rsvpDeadline}, wherever this link reached you."
                    "\n\nWe can't wait to celebrate with you!",
                },
                {"type": "text", "variant": "signature", "text": "{coupleNames}"},
            ],
        },
    ],
    "events": {
        "ceremony": {
            "title": "Civil ceremony",
            "location": "registry",
            "start": "2030-06-15T11:00:00+03:00",
            "end": "2030-06-15T12:00:00+03:00",
        },
        "dinner": {
            "title": "Wedding dinner",
            "location": "manor",
            "start": "2030-06-15T16:00:00+03:00",
            "end": "2030-06-15T23:30:00+03:00",
            "showEnd": True,
            "description": "Dress code: light summer colours. Part of the evening is on the "
            "lawn, so comfortable shoes are a good idea.",
            "schedule": "dinner",
            # hidden by default: switched on for two invitations, the others
            # see the text in its place
            "links": {
                "photos": {
                    "text": "Photos from the dinner",
                    "href": "/photos/{token}/",
                    "pending": "Photos from the dinner will appear here after the celebration "
                    "— we will let you know",
                }
            },
        },
        "brunch": {
            "title": "The day after",
            "location": "terrace",
            "start": "2030-06-16T12:00:00+03:00",
            "end": "2030-06-16T15:00:00+03:00",
            "visible": False,
        },
    },
    "locations": {
        "registry": {
            "name": "Exampleton Register Office",
            "address": "2 Central Square, Exampleton",
            "geo": {"lat": 12.340001, "lng": 23.450002},
            "maps": {
                "googleQuery": "Guest entrance, Register Office, Exampleton",
                "yandexGeoId": "1234567890",
                "appleQuery": "Guest entrance, Register Office, Exampleton",
            },
            "photos": ["registry-1"],
        },
        "manor": {
            "name": "Example Manor",
            "address": "1 Example Street, Exampleton",
            "description": "An old manor house by a pond on the edge of Exampleton. The "
            "ceremony takes place in the garden and dinner in the great hall.\n\nThere is "
            "free parking on site.",
            "geo": {"lat": 12.345678, "lng": 23.456789},
            "maps": {
                "googlePlaceId": "EXAMPLE-not-a-real-place-id",
                "yandexOrgId": "1000000001",
                "applePlaceId": "IEXAMPLE0000001",
            },
            "photos": ["venue-1", "venue-2", "walk", "venue-3", "venue-4"],
            "directions": "directions",
            "directionsCredit": "© Exampleton Mapping Service",
        },
        "terrace": {"ready": False},
        "hotel": {
            "name": "The Example Hotel",
            "address": "5 Station Road, Exampleton",
            "geo": {"lat": 12.35, "lng": 23.46},
        },
    },
    "schedules": {
        "dinner": [
            {
                "time": "15:30",
                "title": "Guests arrive",
                "text": "Welcome drinks and light snacks in the garden.",
            },
            {"time": "16:00", "title": "Ceremony", "text": "An outdoor ceremony by the pond."},
            {"time": "17:00", "title": "Photographs"},
            {
                "time": "18:00",
                "title": "Wedding dinner",
                "text": "The great hall of the manor.\nSeating by place cards.",
            },
            {"time": "23:00", "title": "End of the evening"},
        ]
    },
    "media": {
        # the background of the cover: decoration, no description
        "cover": {"type": "image", "file": "cover.png"},
        "registry-1": {"type": "image", "file": "registry-1.png", "alt": "The register office"},
        "venue-1": {"type": "image", "file": "venue-1.png", "alt": "The manor seen from the pond"},
        "venue-2": {"type": "image", "file": "venue-2.png", "alt": "The manor garden"},
        "venue-3": {"type": "image", "file": "venue-3.png", "alt": "The great hall"},
        "venue-4": {"type": "image", "file": "venue-4.png", "alt": "The veranda"},
        # describes the map: the caption under it already says what it is
        "directions": {
            "type": "image",
            "file": "directions.png",
            "alt": "Map from the station to the manor",
        },
        "story-1": {"type": "image", "file": "story-1.png", "alt": "Our first meeting"},
        "story-2": {"type": "image", "file": "story-2.png", "alt": "The engagement"},
        "proposal": {
            "type": "video",
            "file": "proposal.mp4",
            "poster": "proposal-poster.png",
            "width": 720,
            "height": 1280,
            "alt": "Video of the proposal",
        },
        "walk": {
            "type": "video",
            "file": "walk.mp4",
            "poster": "walk-poster.png",
            "width": 1280,
            "height": 720,
            "alt": "A walk around the manor",
        },
    },
}

INVITATIONS = [
    {
        "token": "0R-pnCqGFgrPOR5e-NluZw",
        "greeting": "Dear Carol,",
        "events": {"brunch": {"visible": True}},
        "sections": {
            "personal": {
                "note": "Thank you for being there all these years. We can't wait to see you! <3"
            },
            "invite": {"widgets": {"plus-one": {"visible": True}}},
        },
    },
    {
        "token": "oWaEF01q51e11fwVhCZQqQ",
        "greeting": "Dear Dave,",
        "events": {
            "dinner": {
                "note": "Please tell us about your allergy, and we will keep it in mind when "
                "choosing the dishes.",
                "links": {"photos": {"visible": True}},
            }
        },
    },
    {
        "token": "48lh3whME-jqDOw3yzzWpQ",
        "greeting": "Dear Eve,",
        "primaryEvent": "ceremony",
        "events": {"brunch": {"visible": True}},
        "sections": {
            "personal": {
                "note": "Remember how we met on the train?\nNow you know how it all "
                "ended.\n\nHugs, and see you soon!"
            },
            "travel": {
                "visible": True,
                "note": "We will meet you at the station — just tell us which train you are on.",
            },
        },
    },
    {
        "token": "lXG6kSgXRvYCN6GGk5IcBA",
        "greeting": "Dear Trent,",
        "sections": {"invite": {"widgets": {"plus-one": {"visible": True}}}, "travel": {"visible": True}},
    },
    {
        "token": "uGeJJ1NFz9Q2YYhekmwPtw",
        "greeting": "Dear Peggy and Victor,",
        "primaryEvent": "ceremony",
        "sections": {
            "personal": {
                "note": "You have always been an example to us.\n\nWe very much hope you will "
                "share this day with us."
            }
        },
    },
    {
        "token": "IBAhKaLEOj1DHuOUdUMzQA",
        "greeting": "Dear Grace and Frank,",
        "sections": {
            "travel": {
                "visible": True,
                "note": "Hotel check-in is the day before, from 14:00.",
                "widgets": {"hotel-booked": {"visible": True}},
            }
        },
    },
    {
        "token": "hoC853fn9btumFjSJTlzpQ",
        "greeting": "Dear Mr Brown,",
        "events": {"ceremony": {"visible": False}},
        "sections": {
            "personal": {"note": "It is a great honour for us to invite you to our celebration."},
            "invite": {"widgets": {"plus-one": {"visible": True}}},
        },
    },
    {
        "token": "04e2efb6-33cd-423f-acff-3c14562a3113",
        "greeting": "Dear Mrs Green,",
        "events": {"dinner": {"links": {"photos": {"visible": True}}}},
        "sections": {
            "invite": {"widgets": {"plus-one": {"visible": True}}},
            "travel": {
                "visible": True,
                "note": "The shuttle from the station will be waiting for you at the main "
                "entrance.",
            },
            "where": {
                "note": "If you need help getting to the manor, just write to us and we will "
                "send a car."
            },
        },
    },
]

PENDING_SITE = {
    "schemaVersion": 2,
    "coupleNames": "Alice & Bob",
    "rsvpDeadline": "1 July 2030",
    "mediaDir": "MR7IwBP4RVsVlBUFCeyEqQ",
    "mainEvent": "celebration",
    "sections": [
        {"id": "cover", "type": "cover"},
        {
            "id": "invite",
            "title": "{greeting}",
            "align": "center",
            "widgets": [
                {
                    "type": "text",
                    "variant": "lead",
                    "text": "{coupleNames} invite you to their celebration.",
                },
                {
                    "id": "plus-one",
                    "type": "text",
                    "variant": "lead",
                    "visible": False,
                    "text": "You are welcome to bring a partner or a friend.",
                },
                {
                    "type": "text",
                    "variant": "lead",
                    "text": "We look forward to seeing you on {eventDate} at {eventTime}.",
                },
            ],
        },
        {"id": "personal", "title": "A few personal words", "widgets": []},
        {"id": "when", "title": "Date and time", "align": "center", "widgets": [{"type": "date"}]},
        {"id": "where", "title": "Where and when", "width": "wide", "widgets": [{"type": "events"}]},
        {
            "id": "travel",
            "title": "For guests from out of town",
            "visible": False,
            "widgets": [
                {
                    "type": "text",
                    "text": "We will send the details of travel and accommodation together "
                    "with the address.",
                }
            ],
        },
        {
            "id": "rsvp",
            "title": "Reply",
            "align": "center",
            "widgets": [
                {
                    "type": "text",
                    "text": "Please reply by {rsvpDeadline}, wherever this link reached you.",
                },
                {"type": "text", "variant": "signature", "text": "{coupleNames}"},
            ],
        },
    ],
    "events": {
        "celebration": {
            "title": "Celebration",
            "location": "venue",
            "start": "2030-08-10T15:00:00+05:00",
            "end": "2030-08-10T22:00:00+05:00",
            "schedule": "day",
        }
    },
    "locations": {"venue": {"ready": False}},
    "schedules": {
        "day": [
            {"time": "15:00", "title": "Ceremony"},
            {"time": "16:30", "title": "Wedding dinner", "text": "The venue is still to be confirmed."},
        ]
    },
}

PENDING_INVITATIONS = [
    {
        # a readable token with a random tail (`build.py token --prefix heron`)
        "token": "heron-4tx9",
        "greeting": "Dear Sybil,",
        "sections": {
            "travel": {
                "visible": True,
                "note": "As soon as we know the venue, we will send you the travel details.",
            }
        },
    },
    {
        # a short readable token: counted in the summary of validate and build
        "token": "quokka",
        "greeting": "Dear Walter and Wendy,",
        "sections": {"personal": {"note": "We can't wait to see you!"}},
    },
    {
        "token": "JhlkiN2-7agdX9Fl6D_Z6Q",
        "greeting": "Dear Mrs Grey,",
        "sections": {"invite": {"widgets": {"plus-one": {"visible": True}}}},
    },
]

#: What the build would read from the media files of `SITE`.
MEDIA_INFO = {
    name: MediaInfo(name, width=1200, height=800)
    for name in (
        "registry-1.png",
        "venue-1.png",
        "venue-2.png",
        "venue-3.png",
        "venue-4.png",
        "story-1.png",
        "story-2.png",
    )
}
MEDIA_INFO.update(
    {
        "directions.png": MediaInfo("directions.png", width=1000, height=1000),
        "cover.png": MediaInfo("cover.png", width=2400, height=1600),
        "proposal-poster.png": MediaInfo("proposal-poster.png", width=720, height=1280),
        "walk-poster.png": MediaInfo("walk-poster.png", width=1280, height=720),
        "proposal.mp4": MediaInfo(
            "proposal.mp4", width=720, height=1280, duration_seconds=20.0,
            faststart=True, video_codec="avc1", hdr=False,
        ),
        "walk.mp4": MediaInfo(
            "walk.mp4", width=1280, height=720, duration_seconds=5.0,
            faststart=True, video_codec="avc1", hdr=False,
        ),
    }
)

SITE_IMAGES = {
    "faviconPath": "/assets/favicon.svg",
    "faviconType": "image/svg+xml",
    "ogImage": "/assets/og.png",
    "ogImageType": "image/png",
    "ogImageWidth": 1200,
    "ogImageHeight": 630,
    # not an image, but a site field of the root all the same
    "themeColor": "#f2efe9",
}
DEFAULT_DURATION = timedelta(hours=6)


def site() -> dict:
    return copy.deepcopy(SITE)


def invitations() -> list:
    return copy.deepcopy(INVITATIONS)


def pending_site() -> dict:
    return copy.deepcopy(PENDING_SITE)


def pending_invitations() -> list:
    return copy.deepcopy(PENDING_INVITATIONS)


def settings(**changes) -> PageSettings:
    """The settings of the fixture pages; keyword arguments replace fields."""
    values = {
        "default_duration": DEFAULT_DURATION,
        "site_images": SITE_IMAGES,
        "media_info": MEDIA_INFO,
    }
    values.update(changes)
    return PageSettings(**values)


class Collector:
    """A report that collects the messages (the interface of the checks)."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, text: str) -> None:
        self.errors.append(text)

    def warning(self, text: str) -> None:
        self.warnings.append(text)

    @property
    def messages(self) -> list[str]:
        return self.errors + self.warnings
