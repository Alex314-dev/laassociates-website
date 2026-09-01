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

## ⚠️ Unverified — confirm before relying on these
| Item | Where | Notes |
|------|-------|-------|
| **Caffeine content** | `guarana-antarctica/index.html` & `en/…` — FAQ, `<!-- TODO -->` | The page says only "noticeably less than a cola", which is safe. The exact mg/100 ml is **not** published because the figure available online (~0.9 mg/100 ml) may describe the Brazilian recipe, not the Sumol+Compal European one. Confirm from the can label. |
| **Ingredient list** | both product pages — Taste section `<!-- TODO -->` | Currently the general recipe. Replace with the European label text. |
| **Geo coordinates** | `index.html` & `en/index.html` — `LocalBusiness.geo` | 42.6603, 23.2995 — street-level for ул. Деян Белишки, not the exact building. Google will prefer the Business Profile anyway. |

## ⏳ To add when available
| Item | Where to edit | Notes |
|------|---------------|-------|
| **VAT / ЕИК number** | `index.html` & `en/index.html` — footer `<!-- TODO ... VAT -->` and the Company-details `<dl>` | Add a `<dt>VAT</dt><dd>…</dd>` line and append to the footer copyright. |
| **Social media links** | both pages — `<!-- Social links go here -->` in footer, and `"sameAs"` in the JSON-LD `<script>` | Add icon links + list the profile URLs in `sameAs`. |
| **Company story** | both pages — insert a new `<section>` after the Hero | A short "Our Story" block; structure mirrors other sections. |
| ~~**Exact product formats**~~ | ✅ done — 330 ml can, 24 units per case | Listed on both home pages, both product pages, and as `size` in the Product schema. |
| **Product photo** | `assets/img/` + Portfolio `.product__visual img` | Replace the placeholder logo image with a real bottle/can photo. |

## Notes
- The two language versions must be kept in sync — edit `index.html` (BG) and
  `en/index.html` (EN) together, and likewise for each content page under
  `guarana/` and `guarana-antarctica/`.
- All asset paths are root-absolute (`/assets/...`), so the site must be served from a domain root (which Cloudflare Pages / GitHub Pages / Netlify all do).
