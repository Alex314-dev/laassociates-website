#!/usr/bin/env python3
"""Build the "Where to buy" pages from data/stores.json.

data/stores.json is the single source of truth for every place that sells
Guaraná Antarctica. This script validates it and rewrites the generated regions
of both language versions of the page:

    where-to-buy/index.html      (BG)
    en/where-to-buy/index.html   (EN)

Each generated region sits between a pair of marker comments, e.g.

    <!-- STORES:LIST --> ...generated... <!-- /STORES:LIST -->

Everything outside the markers is hand-written and left untouched. The output
is plain HTML that gets committed, so the site still deploys with no build step.

The "last updated" date (on the page and in sitemap.xml) moves to today only
when the generated content actually changes, so running the script twice in a
row produces no diff.

Usage:

    python3 tools/build-stores.py           # validate + rewrite the pages
    python3 tools/build-stores.py --check   # validate only, write nothing

Requires: Python 3.8+, standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
from pathlib import Path

# --- configuration -----------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "stores.json"
SITEMAP = ROOT / "sitemap.xml"
SITE = "https://laassociatesbg.com"
PAGES = {
    "bg": (ROOT / "where-to-buy" / "index.html", f"{SITE}/where-to-buy/"),
    "en": (ROOT / "en" / "where-to-buy" / "index.html", f"{SITE}/en/where-to-buy/"),
}
LANGS = ("bg", "en")

# Place types: visible label per language + the schema.org type used in JSON-LD.
TYPES = {
    "shop":       {"bg": "Магазин",         "en": "Shop",        "schema": "Store"},
    "restaurant": {"bg": "Ресторант",       "en": "Restaurant",  "schema": "Restaurant"},
    "cafe":       {"bg": "Кафене",          "en": "Café",        "schema": "CafeOrCoffeeShop"},
    "bakery":     {"bg": "Пекарна",         "en": "Bakery",      "schema": "Bakery"},
    "bar":        {"bg": "Бар",             "en": "Bar",         "schema": "BarOrPub"},
    "coworking":  {"bg": "Коуъркинг",       "en": "Coworking",   "schema": "LocalBusiness"},
    "online":     {"bg": "Онлайн магазин",  "en": "Online shop", "schema": "OnlineStore"},
}

# Rough bounding box of Bulgaria — catches swapped or mistyped coordinates.
LAT_RANGE = (41.2, 44.3)
LNG_RANGE = (22.3, 28.7)

TEXT = {
    "bg": {
        "maps": "Отвори в Google Maps",
        "website": "Уебсайт",
        "show": "Покажи на картата",
        "online": "Онлайн",
        "online_note": "Доставка до адрес",
        "list_name": "Обекти, в които се предлага Гуарана Антарктика",
        "map_fallback": "Картата се зарежда… Всички обекти са изброени по-долу.",
        "empty": "Списъкът тепърва се попълва — първите обекти ще бъдат добавени съвсем скоро. "
                 "Междувременно ни пишете и ще ви кажем къде да намерите напитката.",
    },
    "en": {
        "maps": "Open in Google Maps",
        "website": "Website",
        "show": "Show on map",
        "online": "Online",
        "online_note": "Home delivery",
        "list_name": "Places selling Guaraná Antarctica",
        "map_fallback": "Loading the map… Every place is also listed below.",
        "empty": "The list is just getting started — the first places will be added very soon. "
                 "In the meantime, write to us and we will tell you where to find the drink.",
    },
}


def summary(lang: str, places: int, cities: list[str], online: int) -> str:
    """The hero sentence with the counts, grammatically correct in each language.

    `cities` holds the city names in `lang`; a single city is named outright
    ("3 places in Sofia"), several are counted ("5 places in 2 cities across Bulgaria").
    """
    if lang == "bg":
        if not places and not online:
            return "Скоро тук ще намерите всички магазини и заведения, в които се предлага напитката."
        parts = []
        if places:
            obj = "обект" if places == 1 else "обекта"
            where = cities[0] if len(cities) == 1 else f"{len(cities)} града в България"
            parts.append(f"{places} {obj} в {where}")
        if online:
            shop = "онлайн магазин" if online == 1 else "онлайн магазина"
            parts.append(f"{online} {shop}")
        return ("Гуарана Антарктика се предлага в " + " и ".join(parts) + ". "
                "Намерете най-близкия обект на картата или в списъка по-долу.")
    if not places and not online:
        return "Soon you will find every shop and venue selling the drink right here."
    parts = []
    if places:
        where = cities[0] if len(cities) == 1 else f"{len(cities)} cities across Bulgaria"
        parts.append(f"{places} place{'s' if places != 1 else ''} in {where}")
    if online:
        parts.append(f"{online} online shop{'s' if online != 1 else ''}")
    return ("Guaraná Antarctica is sold at " + " and ".join(parts) + ". "
            "Find the nearest one on the map or in the list below.")


# --- validation ----------------------------------------------------------------
class DataError(Exception):
    pass


def _bilingual(entry: dict, key: str, where: str, errors: list) -> None:
    value = entry.get(key)
    if not isinstance(value, dict) or any(not str(value.get(l, "")).strip() for l in LANGS):
        errors.append(f'{where}: "{key}" needs non-empty "bg" and "en" texts')


def validate(entries) -> list[dict]:
    if not isinstance(entries, list):
        raise DataError("data/stores.json must contain a JSON array of places")
    errors, seen = [], set()
    for i, e in enumerate(entries):
        where = f'entry #{i + 1} ({e.get("id", "no id")})' if isinstance(e, dict) else f"entry #{i + 1}"
        if not isinstance(e, dict):
            errors.append(f"{where}: must be an object")
            continue
        pid = e.get("id", "")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", str(pid)):
            errors.append(f'{where}: "id" must be a lowercase slug like "cafe-example-sofia"')
        elif pid in seen:
            errors.append(f'{where}: duplicate id "{pid}"')
        seen.add(pid)
        if not str(e.get("name", "")).strip():
            errors.append(f'{where}: "name" is required')
        kind = e.get("type")
        if kind not in TYPES:
            errors.append(f'{where}: "type" must be one of {", ".join(TYPES)}')
        _bilingual(e, "description", where, errors)
        if not isinstance(e.get("active"), bool):
            errors.append(f'{where}: "active" must be true or false')
        try:
            dt.date.fromisoformat(str(e.get("added")))
        except ValueError:
            errors.append(f'{where}: "added" must be a date like 2026-10-15')
        for key in ("website", "maps_url"):
            if key in e and not str(e[key]).startswith("https://"):
                errors.append(f'{where}: "{key}" must start with https://')
        if kind == "online":
            if "website" not in e:
                errors.append(f'{where}: online shops need a "website"')
            continue
        _bilingual(e, "city", where, errors)
        _bilingual(e, "address", where, errors)
        if "maps_url" not in e:
            errors.append(f'{where}: "maps_url" is required for physical places')
        lat, lng = e.get("lat"), e.get("lng")
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in (lat, lng)):
            errors.append(f'{where}: "lat" and "lng" must be numbers')
        elif not (LAT_RANGE[0] <= lat <= LAT_RANGE[1] and LNG_RANGE[0] <= lng <= LNG_RANGE[1]):
            errors.append(f"{where}: coordinates {lat}, {lng} are outside Bulgaria (swapped?)")
    if errors:
        raise DataError("\n".join(errors))
    return [e for e in entries if e["active"]]


# --- rendering -----------------------------------------------------------------
def esc(value) -> str:
    return html.escape(str(value), quote=True)


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def group_by_city(places: list[dict]) -> list[tuple[dict, list[dict]]]:
    """Cities with the most places first, then alphabetically (by English name)."""
    groups: dict[str, tuple[dict, list[dict]]] = {}
    for p in places:
        groups.setdefault(p["city"]["en"], (p["city"], []))[1].append(p)
    ordered = sorted(groups.values(), key=lambda g: (-len(g[1]), g[0]["en"].casefold()))
    return [(city, sorted(items, key=lambda p: p["name"].casefold())) for city, items in ordered]


def render_card(p: dict, lang: str, ind: str) -> str:
    t = TEXT[lang]
    online = p["type"] == "online"
    attrs = f' id="{esc(p["id"])}" data-type="{esc(p["type"])}"'
    if not online:
        attrs += (f' data-city="{esc(slug(p["city"]["en"]))}"'
                  f' data-lat="{p["lat"]}" data-lng="{p["lng"]}"')
    links = []
    if p.get("maps_url"):
        links.append(f'<a href="{esc(p["maps_url"])}" target="_blank" rel="noopener">{t["maps"]}</a>')
    if p.get("website"):
        links.append(f'<a href="{esc(p["website"])}" target="_blank" rel="noopener">{t["website"]}</a>')
    if not online:
        links.append(f'<button class="store__show" type="button" hidden>{t["show"]}</button>')
    where = t["online_note"] if online else f'{esc(p["address"][lang])}, {esc(p["city"][lang])}'
    return "\n".join([
        f'{ind}<li>',
        f'{ind}  <article class="card store"{attrs}>',
        f'{ind}    <span class="store__type">{esc(TYPES[p["type"]][lang])}</span>',
        f'{ind}    <h4 class="store__name">{esc(p["name"])}</h4>',
        f'{ind}    <p class="store__addr">{where}</p>',
        f'{ind}    <p class="store__desc">{esc(p["description"][lang])}</p>',
        f'{ind}    <p class="store__links">{" ".join(links)}</p>',
        f'{ind}  </article>',
        f'{ind}</li>',
    ])


def render_group(title: str, key: str, items: list[dict], lang: str) -> str:
    ind = " " * 10
    cards = "\n".join(render_card(p, lang, ind) for p in items)
    return (f'      <div class="stores__group" data-group="{key}">\n'
            f'        <h3 class="stores__city">{esc(title)} <span class="stores__count">{len(items)}</span></h3>\n'
            f'        <ul class="stores__list">\n{cards}\n        </ul>\n'
            f'      </div>')


def render_list(active: list[dict], lang: str) -> str:
    physical = [p for p in active if p["type"] != "online"]
    online = sorted((p for p in active if p["type"] == "online"), key=lambda p: p["name"].casefold())
    if not active:
        return f'\n      <p class="stores__empty">{TEXT[lang]["empty"]}</p>\n      '
    blocks = [render_group(city[lang], slug(city["en"]), items, lang) for city, items in group_by_city(physical)]
    if online:
        blocks.append(render_group(TEXT[lang]["online"], "online", online, lang))
    return "\n" + "\n".join(blocks) + "\n      "


def render_map(active: list[dict], lang: str) -> str:
    if not any(p["type"] != "online" for p in active):
        return ""
    return (f'\n      <div class="wtb__map" id="map" role="region" aria-label="{"Карта" if lang == "bg" else "Map"}">'
            f'<p class="wtb__map-fallback">{TEXT[lang]["map_fallback"]}</p></div>\n      ')


def render_jsonld(active: list[dict], lang: str, page_url: str) -> str:
    if not active:
        return ""
    items = []
    for pos, p in enumerate(active, 1):
        item = {
            "@type": TYPES[p["type"]]["schema"],
            "@id": f'{page_url}#{p["id"]}',
            "name": p["name"],
            "description": p["description"][lang],
        }
        if p.get("website"):
            item["url"] = p["website"]
        if p["type"] != "online":
            item["address"] = {
                "@type": "PostalAddress",
                "streetAddress": p["address"][lang],
                "addressLocality": p["city"][lang],
                "addressCountry": "BG",
            }
            item["geo"] = {"@type": "GeoCoordinates", "latitude": p["lat"], "longitude": p["lng"]}
        if p.get("maps_url"):
            item["hasMap"] = p["maps_url"]
        items.append({"@type": "ListItem", "position": pos, "item": item})
    data = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "@id": f"{page_url}#places",
        "name": TEXT[lang]["list_name"],
        "numberOfItems": len(items),
        "mainEntityOfPage": {"@id": f"{page_url}#webpage"},
        "itemListElement": items,
    }
    body = json.dumps(data, ensure_ascii=False, indent=2).replace("</", "<\\/")
    body = "\n".join("  " + line for line in body.splitlines())
    return f'\n  <script type="application/ld+json">\n{body}\n  </script>\n  '


def render_updated(date: dt.date, lang: str) -> str:
    shown = date.strftime("%d.%m.%Y") if lang == "bg" else f"{date.day} {date:%B %Y}"
    return f'<time datetime="{date.isoformat()}">{shown}</time>'


# --- writing ---------------------------------------------------------------------
MARKER = re.compile(r"(<!-- STORES:(\w+) -->)(.*?)(<!-- /STORES:\2 -->)", re.S)


def fill(page: str, regions: dict[str, str], path: Path) -> str:
    found = set()

    def sub(m: re.Match) -> str:
        name = m.group(2)
        if name not in regions:
            raise DataError(f"{path.relative_to(ROOT)}: unknown marker STORES:{name}")
        found.add(name)
        return m.group(1) + regions[name] + m.group(4)

    out = MARKER.sub(sub, page)
    missing = set(regions) - found
    if missing:
        raise DataError(f"{path.relative_to(ROOT)}: missing markers {', '.join(sorted(missing))}")
    return out


def current_date(page: str) -> dt.date | None:
    m = re.search(r'<!-- STORES:UPDATED --><time datetime="(\d{4}-\d{2}-\d{2})"', page)
    return dt.date.fromisoformat(m.group(1)) if m else None


def build(active: list[dict], write: bool) -> list[str]:
    places = [p for p in active if p["type"] != "online"]
    online = len(active) - len(places)
    today = dt.date.today()
    changed, dates = [], []

    for lang, (path, url) in PAGES.items():
        page = path.read_text(encoding="utf-8")

        def render(date: dt.date) -> str:
            return fill(page, {
                "SUMMARY": summary(lang, len(places), sorted({p["city"][lang] for p in places}), online),
                "MAP": render_map(active, lang),
                "LIST": render_list(active, lang),
                "JSONLD": render_jsonld(active, lang, url),
                "UPDATED": render_updated(date, lang),
            }, path)

        # Keep the existing date unless the content itself changed.
        date = current_date(page) or today
        new = render(date)
        if new != page and date != today:
            date, new = today, render(today)
        dates.append(date)
        if new != page:
            changed.append(str(path.relative_to(ROOT)))
            if write:
                path.write_text(new, encoding="utf-8")

    lastmod = max(dates).isoformat()
    sitemap = SITEMAP.read_text(encoding="utf-8")
    new_sitemap = sitemap
    for _, url in PAGES.values():
        pattern = re.compile(rf"(<loc>{re.escape(url)}</loc>\s*<lastmod>)[^<]*(</lastmod>)")
        if not pattern.search(new_sitemap):
            raise DataError(f"sitemap.xml has no <url> entry with <lastmod> for {url}")
        new_sitemap = pattern.sub(rf"\g<1>{lastmod}\g<2>", new_sitemap)
    if new_sitemap != sitemap:
        changed.append("sitemap.xml")
        if write:
            SITEMAP.write_text(new_sitemap, encoding="utf-8")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--check", action="store_true", help="validate the data only; write nothing")
    args = parser.parse_args()
    try:
        try:
            entries = json.loads(DATA.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise DataError(f"data/stores.json is not valid JSON: {exc}") from exc
        active = validate(entries)
        changed = build(active, write=not args.check)
    except DataError as exc:
        print(f"error:\n{exc}", file=sys.stderr)
        return 1
    hidden = len(entries) - len(active)
    print(f"{len(active)} active place(s)" + (f", {hidden} hidden" if hidden else "") + ".")
    if args.check:
        print("Data is valid." + (f" Would update: {', '.join(changed)}" if changed else " Pages are up to date."))
    else:
        print(f"Updated: {', '.join(changed)}" if changed else "Pages already up to date.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
