"""The Russian example set (`examples/data-ru`) as Python objects.

`RU_SITE` / `RU_INVITATIONS` are the same eight invitations as the main set
of `tests/fixtures_v2.py`, written in Russian with `"lang": "ru"`, and with
the forms of address: four guests are addressed informally (`ty`), four
formally (`vy`), and the link preview uses the common form.  The media
registry is the one of the main set, so `fixtures_v2.MEDIA_INFO` and
`fixtures_v2.settings()` serve both.  Use `ru_site()` / `ru_invitations()`
for copies that a test may change.
"""

from __future__ import annotations

import copy

from tests.fixtures_v2 import MEDIA_DIR

RU_SITE = {
    "schemaVersion": 2,
    "lang": "ru",
    "coupleNames": "Алиса и Боб",
    "rsvpDeadline": "1 мая 2030",
    "mediaDir": MEDIA_DIR,
    "mainEvent": "dinner",
    "texts": {
        "announce": "Мы, {coupleNames}, женимся!",
        "invite": {
            "ty": "Ждём тебя {eventDate} в {eventTime}.\n"
            "Нам очень хочется разделить этот день с тобой.",
            "vy": "Ждём вас {eventDate} в {eventTime}.\n"
            "Нам очень хочется разделить этот день с вами.",
            "all": "Ждём вас {eventDate} в {eventTime}.",
        },
    },
    "linkPreview": {"description": "{text:announce} {text:invite}"},
    "sections": [
        {"id": "cover", "type": "cover", "background": "cover", "backgroundFocus": "center"},
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
                    "text": {
                        "ty": "Ты можешь прийти со спутником или спутницей.\n"
                        "Пожалуйста, сообщи нам заранее имя своего гостя.",
                        "vy": "Вы можете прийти со спутником или спутницей.\n"
                        "Пожалуйста, сообщите нам заранее имя вашего гостя.",
                    },
                },
                {
                    "type": "text",
                    "variant": "lead",
                    "text": "{text:invite}",
                },
            ],
        },
        {"id": "personal", "title": "Несколько слов лично", "widgets": []},
        {
            "id": "when",
            "title": "Дата и время",
            "align": "center",
            "widgets": [{"type": "date"}],
        },
        {
            "id": "where",
            "title": "Где и когда",
            "width": "wide",
            "widgets": [{"type": "events"}],
        },
        {
            "id": "travel",
            "title": "Гостям из других городов",
            "visible": False,
            "widgets": [
                {
                    "type": "text",
                    "text": "В день праздника от вокзала Энска до усадьбы и обратно будет "
                    "ходить трансфер.\n\nОтправление от вокзала — в 14:45,\nобратно — в 23:15.",
                },
                {"type": "location", "location": "hotel", "variant": "compact"},
                {
                    "id": "hotel-booked",
                    "type": "text",
                    "visible": False,
                    "text": {
                        "ty": "Для тебя забронирован номер в этой гостинице.",
                        "vy": "Для вас забронирован номер в этой гостинице.",
                    },
                },
            ],
        },
        {
            "id": "story",
            "title": "Наша история",
            "widgets": [{"type": "media", "items": ["story-1", "proposal", "story-2"]}],
        },
        {
            "id": "rsvp",
            "title": "Подтверждение",
            "align": "center",
            "widgets": [
                {
                    "type": "text",
                    "text": {
                        "ty": "Пожалуйста, ответь нам до {rsvpDeadline} — там же, где тебе "
                        "пришла эта ссылка.\n\nБудем очень рады встрече!",
                        "vy": "Пожалуйста, ответьте нам до {rsvpDeadline} — там же, где вы "
                        "получили эту ссылку.\n\nБудем очень рады встрече!",
                    },
                },
                {"type": "text", "variant": "signature", "text": "{coupleNames}"},
            ],
        },
    ],
    "events": {
        "ceremony": {
            "title": "Регистрация",
            "location": "registry",
            "start": "2030-06-15T11:00:00+03:00",
            "end": "2030-06-15T12:00:00+03:00",
        },
        "dinner": {
            "title": "Праздничный ужин",
            "location": "manor",
            "start": "2030-06-15T16:00:00+03:00",
            "end": "2030-06-15T23:30:00+03:00",
            "showEnd": True,
            "schedule": "dinner",
            # hidden by default: switched on for two invitations, the others
            # see the text in its place
            "links": {
                "photos": {
                    "text": "Фотографии с ужина",
                    "href": "/photos/{token}/",
                    "pending": {
                        "ty": "Фотографии с ужина появятся здесь после праздника — мы тебе напишем",
                        "vy": "Фотографии с ужина появятся здесь после праздника — мы вам напишем",
                    },
                }
            },
        },
        "brunch": {
            "title": "Второй день",
            "location": "terrace",
            "start": "2030-06-16T12:00:00+03:00",
            "end": "2030-06-16T15:00:00+03:00",
            "visible": False,
        },
    },
    "locations": {
        "registry": {
            "name": "Дворец бракосочетания Энска",
            "address": "г. Энск, Центральная площадь, д. 2",
            "geo": {"lat": 12.340001, "lng": 23.450002},
            "maps": {
                "googleQuery": "Гостевой вход, Дворец бракосочетания, Энск",
                "yandexGeoId": "1234567890",
                "appleQuery": "Гостевой вход, Дворец бракосочетания, Энск",
            },
            "photos": ["registry-1"],
        },
        "manor": {
            "name": "Усадьба «Образец»",
            "address": "г. Энск, ул. Примерная, д. 1",
            "description": "Старинная усадьба на берегу пруда в пригороде Энска. Церемония "
            "пройдёт в саду, ужин — в главном зале.\n\nНа территории есть бесплатная "
            "парковка.",
            "geo": {"lat": 12.345678, "lng": 23.456789},
            "maps": {
                "googlePlaceId": "EXAMPLE-not-a-real-place-id",
                "yandexOrgId": "1000000001",
                "applePlaceId": "IEXAMPLE0000001",
            },
            "photos": ["venue-1", "venue-2", "walk", "venue-3", "venue-4"],
            "directions": "directions",
            "directionsCredit": "© Картографическая служба Энска",
        },
        "terrace": {"ready": False},
        "hotel": {
            "name": "Гостиница «Пример»",
            "address": "г. Энск, Вокзальная ул., д. 5",
            "geo": {"lat": 12.35, "lng": 23.46},
        },
    },
    "schedules": {
        "dinner": [
            {
                "time": "15:30",
                "title": "Сбор гостей",
                "text": "Приветственные напитки и лёгкие закуски в саду.",
            },
            {"time": "16:00", "title": "Церемония", "text": "Выездная регистрация на берегу пруда."},
            {"time": "17:00", "title": "Фотосессия"},
            {
                "time": "18:00",
                "title": "Праздничный ужин",
                "text": "Главный зал усадьбы.\nРассадка — по карточкам.",
            },
            {"time": "23:00", "title": "Завершение вечера"},
        ]
    },
    "media": {
        # the background of the cover: decoration, no description
        "cover": {"type": "image", "file": "cover.png"},
        "registry-1": {"type": "image", "file": "registry-1.png", "alt": "Дворец бракосочетания"},
        "venue-1": {"type": "image", "file": "venue-1.png", "alt": "Усадьба со стороны пруда"},
        "venue-2": {"type": "image", "file": "venue-2.png", "alt": "Сад усадьбы"},
        "venue-3": {"type": "image", "file": "venue-3.png", "alt": "Главный зал"},
        "venue-4": {"type": "image", "file": "venue-4.png", "alt": "Веранда"},
        "directions": {"type": "image", "file": "directions.png", "alt": "Схема проезда"},
        "story-1": {"type": "image", "file": "story-1.png", "alt": "Первая встреча"},
        "story-2": {"type": "image", "file": "story-2.png", "alt": "Помолвка"},
        "proposal": {
            "type": "video",
            "file": "proposal.mp4",
            "poster": "proposal-poster.png",
            "width": 720,
            "height": 1280,
            "alt": "Видео предложения",
        },
        "walk": {
            "type": "video",
            "file": "walk.mp4",
            "poster": "walk-poster.png",
            "width": 1280,
            "height": 720,
            "alt": "Прогулка по усадьбе",
        },
    },
}

RU_INVITATIONS = [
    {
        "token": "0R-pnCqGFgrPOR5e-NluZw",
        "greeting": "Дорогая Кэрол!",
        "form": "ty",
        "events": {"brunch": {"visible": True}},
        "sections": {
            "personal": {"note": "Спасибо, что столько лет рядом. Очень ждём! <3"},
            "invite": {"widgets": {"plus-one": {"visible": True}}},
        },
    },
    {
        "token": "oWaEF01q51e11fwVhCZQqQ",
        "greeting": "Дорогой Дэйв!",
        "form": "ty",
        "events": {
            "dinner": {
                "note": "Напиши нам, пожалуйста, про аллергию — учтём это при выборе блюд.",
                "links": {"photos": {"visible": True}},
            }
        },
    },
    {
        "token": "48lh3whME-jqDOw3yzzWpQ",
        "greeting": "Дорогая Ева!",
        "form": "ty",
        "primaryEvent": "ceremony",
        "events": {"brunch": {"visible": True}},
        "sections": {
            "personal": {
                "note": "Помнишь, как мы познакомились в поезде?\nТеперь ты знаешь, чем всё "
                "закончилось.\n\nОбнимаем и ждём!"
            },
            "travel": {
                "visible": True,
                "note": "Встретим тебя на вокзале — просто скажи, каким поездом приедешь.",
            },
        },
    },
    {
        "token": "lXG6kSgXRvYCN6GGk5IcBA",
        "greeting": "Дорогой Трент!",
        "form": "ty",
        "sections": {"invite": {"widgets": {"plus-one": {"visible": True}}}, "travel": {"visible": True}},
    },
    {
        "token": "uGeJJ1NFz9Q2YYhekmwPtw",
        "greeting": "Дорогие Пегги и Виктор!",
        "form": "vy",
        "primaryEvent": "ceremony",
        "sections": {
            "personal": {
                "note": "Вы — пример для нас во всём.\n\nОчень надеемся, что вы разделите с "
                "нами этот день."
            }
        },
    },
    {
        "token": "IBAhKaLEOj1DHuOUdUMzQA",
        "greeting": "Дорогие Грейс и Фрэнк!",
        "form": "vy",
        "sections": {
            "travel": {
                "visible": True,
                "note": "Заезд в гостиницу — накануне, после 14:00.",
                "widgets": {"hotel-booked": {"visible": True}},
            }
        },
    },
    {
        "token": "hoC853fn9btumFjSJTlzpQ",
        "greeting": "Уважаемый Оскар Петрович!",
        "form": "vy",
        "events": {"ceremony": {"visible": False}},
        "sections": {
            "personal": {"note": "Для нас большая честь пригласить вас на наш праздник."},
            "invite": {"widgets": {"plus-one": {"visible": True}}},
        },
    },
    {
        "token": "04e2efb6-33cd-423f-acff-3c14562a3113",
        "greeting": "Уважаемая Хайди Андреевна!",
        "form": "vy",
        "events": {"dinner": {"links": {"photos": {"visible": True}}}},
        "sections": {
            "invite": {"widgets": {"plus-one": {"visible": True}}},
            "travel": {
                "visible": True,
                "note": "Трансфер от вокзала будет ждать вас у главного входа.",
            },
            "where": {
                "note": "Если понадобится помощь с дорогой до усадьбы — напишите нам, пришлём "
                "машину."
            },
        },
    },
]


def ru_site() -> dict:
    return copy.deepcopy(RU_SITE)


def ru_invitations() -> list:
    return copy.deepcopy(RU_INVITATIONS)
