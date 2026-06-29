# Content checklist — LA Associates website

This page is intentionally built so the deferred items can be dropped in without a redesign.
Search the codebase for `TODO` to find every spot that needs an edit.

## ✅ Already in the site
- Logos (wordmark + icon mark) and favicons
- Brand colour `#8C181B`
- Legal name: “LA Associates” Ltd. / «Ел Ей Асошиейтс» ООД
- Address: ul. Deyan Belishki 113A, Sofia, Bulgaria / ул. Деян Белишки 113А, София, България
- Phone: +359 88 718 0555
- Email: contact@laassociatesbg.com
- Supplier: Sumol+Compal, Portugal
- Product description for Guaraná Antarctica (general)
- Sections: Hero · Portfolio · Sourcing · Who we serve · Why us · Contact

## ⏳ To add when available
| Item | Where to edit | Notes |
|------|---------------|-------|
| **VAT / ЕИК number** | `index.html` & `bg/index.html` — footer `<!-- TODO ... VAT -->` and the Company-details `<dl>` | Add a `<dt>VAT</dt><dd>…</dd>` line and append to the footer copyright. |
| **Social media links** | both pages — `<!-- Social links go here -->` in footer, and `"sameAs"` in the JSON-LD `<script>` | Add icon links + list the profile URLs in `sameAs`. |
| **Company story** | both pages — insert a new `<section>` after the Hero | A short "Our Story" block; structure mirrors other sections. |
| **Exact product formats** | both pages — `<!-- TODO: add exact available formats -->` in Portfolio | e.g. can / PET bottle sizes, units per case. |
| **Product photo** | `assets/img/` + Portfolio `.product__visual img` | Replace the placeholder logo image with a real bottle/can photo. |

## Notes
- The two language versions must be kept in sync — edit `index.html` (EN) and `bg/index.html` (BG) together.
- All asset paths are root-absolute (`/assets/...`), so the site must be served from a domain root (which Cloudflare Pages / GitHub Pages / Netlify all do).
