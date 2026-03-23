# Frontify Live Asset Map

## Source of Truth

The Algolia brand guide lives at **https://algolia.frontify.com/document/1** and is publicly accessible (no authentication required). This is the canonical source for all visual assets.

## How to Fetch Live Assets

When a user needs a visual asset (logo, icon, illustration, banner), fetch it live from Frontify:

1. **Navigate** to `https://algolia.frontify.com/document/1` using browser tools
2. **Navigate** to the relevant section (Logo, Icons, Digital Assets, Photography, Social Media)
3. **Extract** current CDN URLs from the page — assets are served from `media.ffycdn.net`
4. **Provide** the user with download links or embed the assets in output

## Frontify Page Map

| Section | URL Path | Assets Available |
|---------|----------|-----------------|
| Welcome | `#/intro/welcome` | Brand overview, company description |
| Logo | `#/basics/logo` | Logo overview |
| Logo - Color Variations | `#/basics/logo/color-variations` | Full Xenon, White text, Full white variants |
| Logo - Containers | `#/basics/logo/containers` | Rounded corner, circle, square containers |
| Logo - Downloads | `#/basics/logo/downloads` | Algolia Logo Pack 2022.zip (all formats) |
| Logo - Guidance | `#/basics/logo/guidance` | Usage don'ts (visual examples) |
| Logo - Partners | `#/basics/logo/algolia-and-partners` | Co-branding template |
| Typography | `#/basics/typography` | Sora font specs, usage rules |
| Typography - Typeface | `#/basics/typography/algolia-primary-typeface` | Font weights, character sets |
| Typography - Scale | `#/basics/typography/typeface-scale` | Full type scale with colors/sizes |
| Icons | `#/basics/icons` | Web icons (Feather v4.29.0) + 33 feature icons |
| Photography | `#/visual-language/photography` | 8 customer brand images |
| Digital Assets | `#/visual-language/digital-assets` | Light & dark background illustrations |
| Editorial | `#/content/editorial` | Editorial standards (text only) |
| Slide Template | `#/content/algolia-slide-template` | Google Slides template link |
| Descriptions | `#/content/algolia-descriptions` | All approved company descriptions |
| Social Media | `#/external-comms/social-media` | Guidelines + banner images |

## Digital Assets Library

A separate Frontify document at **https://algolia.frontify.com/document/9** contains the full hi-res digital assets library with 100+ illustrations organized by category.

## Fallback Strategy

If live fetching fails (network issues, Frontify downtime):
1. Inform the user that live asset fetching is unavailable
2. Reference the bundled brand guidelines text for specifications (colors, typography, rules)
3. Direct the user to visit https://algolia.frontify.com/document/1 manually
4. For the logo pack, direct to the Downloads section of the brand guide

## CDN URL Pattern

Frontify serves assets from: `https://media.ffycdn.net/{asset-id}`

Query parameters control size/quality:
- `?width=800` — resize width
- `?quality=80` — JPEG quality
- Original quality: no query params
