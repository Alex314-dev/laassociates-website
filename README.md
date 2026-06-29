# LA Associates — website

A lightweight, static, bilingual (English + Bulgarian) informational website for
**LA Associates** — importer and distributor of Guaraná Antarctica in Bulgaria.

No framework, no build step, no dependencies — just HTML, one CSS file and a tiny JS file.

## Structure

```
.
├── index.html              # English (default)        → https://laassociatesbg.com/
├── bg/index.html           # Bulgarian                → https://laassociatesbg.com/bg/
├── assets/
│   ├── css/styles.css       # all styling (brand colours live in :root)
│   ├── js/main.js           # mobile menu + footer year
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
# then open http://localhost:8000/  (Bulgarian at /bg/)
```

## Editing content

- English lives in `index.html`, Bulgarian in `bg/index.html` — **edit both together**.
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

## After deploying — SEO finishing touches
- Submit `https://laassociatesbg.com/sitemap.xml` in
  [Google Search Console](https://search.google.com/search-console).
- Validate the structured data with the
  [Rich Results Test](https://search.google.com/test/rich-results).
