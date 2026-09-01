# LA Associates — website

A lightweight, static, bilingual (English + Bulgarian) informational website for
**LA Associates** — importer and distributor of Guaraná Antarctica in Bulgaria.

No framework, no build step, no dependencies — just HTML, one CSS file and a tiny JS file.

## Structure

```
.
├── index.html              # Bulgarian (default)      → https://laassociatesbg.com/
├── en/index.html           # English                  → https://laassociatesbg.com/en/
├── guarana/                # BG "Какво е гуарана"     → /guarana/
├── en/guarana/             # EN "What is guaraná"     → /en/guarana/
├── guarana-antarctica/     # BG product page + FAQ    → /guarana-antarctica/
├── en/guarana-antarctica/  # EN product page + FAQ    → /en/guarana-antarctica/
├── bg/index.html           # redirect stub → / (the old Bulgarian URL)
├── 404.html                # branded not-found page
├── assets/
│   ├── css/styles.css       # all styling (brand colours live in :root)
│   ├── js/main.js           # nav menu + footer year
│   └── img/                 # logos, favicons, OG image
├── favicon.ico
├── site.webmanifest
├── robots.txt
├── sitemap.xml
├── CONTENT.md              # checklist of content still to add
└── README.md
```

## Preview locally

Because asset paths are root-absolute (`/assets/...`), open it through a local
server rather than double-clicking the file:

```bash
cd "this folder"
python3 -m http.server 8000
# then open http://localhost:8000/  (Bulgarian at /, English at /en/)
```

## Editing content

- Bulgarian lives in `index.html`, English in `en/index.html` — **edit both together**.
- The same applies to each content page: `guarana/` ↔ `en/guarana/` and
  `guarana-antarctica/` ↔ `en/guarana-antarctica/`.
- Bulgarian is the default language: `/` serves Bulgarian and `hreflang="x-default"`
  points at it, because the site targets the Bulgarian market.
- There is no build step, so the header and footer are duplicated across the eight
  HTML files. Change one, change them all.
- Brand colour and theme: change `--brand` in `assets/css/styles.css` (`:root`).
- Outstanding content (VAT number, socials, company story, product formats) is listed in
  `CONTENT.md`; every spot is marked with a `TODO` comment.

## Deploy

The site is plain static files, so any static host works. Two recommended free options —
both give automatic HTTPS and support your custom domain `laassociatesbg.com`.

### Option A — Cloudflare Pages (recommended)
1. Push this folder to a GitHub repo.
2. Cloudflare dashboard → **Workers & Pages → Create → Pages → Connect to Git**.
3. Select the repo. Build command: **none**. Build output directory: **/** (root).
4. Deploy. You get a `*.pages.dev` URL immediately.
5. **Custom domain:** Pages → your project → *Custom domains* → add `laassociatesbg.com`
   (and `www`). Follow the DNS records it shows.

### Option B — GitHub Pages
1. Push to a GitHub repo.
2. Repo → **Settings → Pages** → Source: *Deploy from a branch* → `main` / `/ (root)`.
3. Add your custom domain under *Settings → Pages → Custom domain* (this writes a `CNAME`
   file). Enable **Enforce HTTPS**.

### DNS — keep your Google Workspace email working
Your domain’s **MX records** (Google Workspace email) are separate from the website’s
**A / CNAME records**. Adding the website records below does **not** affect email.

- **Cloudflare Pages:** add the `CNAME`/`A` records Cloudflare shows for the apex and `www`.
- **GitHub Pages (apex domain):** create four `A` records pointing to
  `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`,
  and a `CNAME` for `www` → `<username>.github.io`.
- Leave all existing `MX` and Google verification `TXT` records untouched.

## Business-card QR code
A branded QR code that opens `https://laassociatesbg.com/` lives in `assets/img/`:

- `qr-laassociatesbg.svg` — vector, scales to any size (use this at the print shop).
- `qr-laassociatesbg.png` — ~1148 px raster for quick previews / digital use.

Brand maroon modules with the logo mark centred, generated at high error correction so the
logo overlay stays scannable. To regenerate (e.g. after a URL or brand-colour change):

```bash
pip install segno Pillow
python3 tools/generate-qr.py
```

The script also works for any other brand — pass a URL and a logo image, and the module
colour is inferred from the logo automatically (override with `--color`). Outputs are
auto-named `qr-<domain>.svg` / `.png` in `assets/img/`:

```bash
python3 tools/generate-qr.py https://example.com path/to/logo.png
python3 tools/generate-qr.py https://example.com path/to/logo.png --color "#123456"
```

By default the logo sits on a white rounded chip. Pass `--no-frame` to drop it so
the modules run all the way up to the logo (best when the logo already has its own
light background/outline):

```bash
python3 tools/generate-qr.py https://example.com path/to/logo.png --no-frame
```

## After deploying — SEO finishing touches
- Submit `https://laassociatesbg.com/sitemap.xml` in
  [Google Search Console](https://search.google.com/search-console) (verify by DNS TXT).
- Validate the structured data with the
  [Rich Results Test](https://search.google.com/test/rich-results).
- Re-request indexing for `/` and `/en/`, and confirm the old `/bg/` URL drops out
  of the index over the following weeks.
- Create a **Google Business Profile** under the company Google Workspace account.
  Location-aware ranking is driven by that profile, not by anything in this repo —
  it is the single biggest remaining lever.
