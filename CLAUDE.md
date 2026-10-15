# LA Associates website — notes for Claude

Static bilingual site (BG at `/`, EN at `/en/`), no build step. See `README.md` for structure
and `CONTENT.md` for outstanding content. Keep BG and EN pages in sync.

## Adding a place to "Where to buy"

When asked to add a place that sells Guaraná Antarctica (e.g. "add Café X on Vitosha 12, Sofia"):

1. **Look it up.** Search the web / Google Maps for the exact business. Collect the official
   name, street address, city, coordinates (lat/lng to 4–5 decimals), website, and the Google
   Maps link. A shared `maps.app.goo.gl` link redirects to a URL with
   `ftid=0x…:0x<hex>`; the second hex number is the place's CID. Use
   `https://maps.google.com/?cid=<CID in decimal>` as the `maps_url` (stable, short), and open
   it in the browser to read the exact coordinates (`!3d<lat>!4d<lng>` in the final URL),
   category, address and website.
   If the place is ambiguous (a chain with several branches, two businesses with the same
   name), ask which one before adding it.
2. **Write the entry** in `data/stores.json` (format and field rules in `README.md`,
   section "Where to buy"):
   - `id`: lowercase slug of name + city, e.g. `cafe-x-sofia`.
   - `type`: `shop` | `restaurant` | `cafe` | `bakery` | `bar` | `coworking` | `online`.
   - `address` and `city` in both Bulgarian and English (Latin transliteration for EN,
     e.g. "ул. Граф Игнатиев 5" → "5 Graf Ignatiev St").
   - `description`: 1–2 sentences in BG and EN, in our own words — what kind of place it is.
     Never copy Google reviews, ratings or photos.
   - `added`: today's date; `active`: true.
3. **Rebuild:** `python3 tools/build-stores.py` (fix any validation error it prints).
4. **Check** `/where-to-buy/` and `/en/where-to-buy/` in the `static` preview: the card
   appears in the right city and its pin lands on the right building.
5. **Commit** as `Where to buy: add <name>` (only the data file, the two pages and
   `sitemap.xml`).

To remove a place, set `"active": false` and rebuild, rather than deleting the entry.
