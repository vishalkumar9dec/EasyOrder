---
name: food-ordering-website
description: Build a modern, premium, visually stunning food ordering or restaurant website. Use this skill whenever the user asks to create a food ordering site, restaurant landing page, food delivery UI, menu page, food e-commerce site, or any food/dining-related web interface. Also trigger when the user mentions "food website", "restaurant website", "menu page", "food ordering", "food delivery landing page", or references Dribbble/Behance food UI inspiration. This skill enforces appetizing dark themes, real-feeling generated food photography, glassmorphism, scroll animations, and premium typography — avoiding generic card grids and template-looking output.
---

# Food Ordering Website

Build food ordering websites that feel hand-crafted by a boutique design studio, not churned out by a template generator. The goal is a site where the food looks irresistible, the layout feels calm and premium, and the interaction design rewards browsing.

## Before You Build

Write three lines in your working notes:

- **Cuisine identity**: What cuisine, what mood? Vietnamese street food is warm and textured. Japanese omakase is minimal and reverent. Indian thali is vibrant and abundant. The cuisine sets the palette, the typography weight, and the image style.
- **Content spine**: Hero → Menu → Spotlight → Process → Social proof → Footer. This is the default. Deviate only with reason.
- **Signature moment**: One thing the user will remember — a hero parallax, a menu filter animation, a dish card hover reveal. Pick one and execute it well.

## Design System

### Color Philosophy

Food websites live or die on appetite appeal. The background must recede so the food photographs dominate.

**Default dark palette** (warm, appetizing):
| Token | Hex | Usage |
|---|---|---|
| `--bg` | `#0D0D0D` | Page background |
| `--surface` | `#1A1A1A` | Cards, elevated sections |
| `--surface-glass` | `rgba(26,26,26,0.7)` | Glassmorphism panels |
| `--accent` | `#FF6B35` | CTAs, active tabs, hover states |
| `--accent-gold` | `#FFB347` | Prices, badges, highlights |
| `--text` | `#F5F5F5` | Primary text |
| `--text-muted` | `#9CA3AF` | Secondary text, descriptions |
| `--success` | `#22C55E` | Add-to-cart confirmations |
| `--border` | `rgba(255,255,255,0.06)` | Subtle dividers |

If the user specifies a light theme or a specific brand palette, adapt — but always ensure food photos have maximum contrast against the background. Never use a mid-tone grey background; go fully dark or fully light.

### Typography

Two typefaces, strict roles:

- **Display**: A serif with character — Playfair Display, DM Serif Display, or Cormorant Garamond. Used only for the hero heading and section titles. Never for body text.
- **Body**: A clean sans-serif — Inter, Plus Jakarta Sans, or Outfit. Everything else: nav, cards, descriptions, buttons, footer.

Scale:
```
--text-hero: clamp(2.5rem, 5vw, 4.5rem)
--text-section: clamp(1.75rem, 3vw, 2.5rem)
--text-card-title: 1.125rem
--text-body: 1rem
--text-caption: 0.875rem
--text-price: 1.25rem (font-weight: 700)
```

Load fonts via `<link>` in `index.html` from Google Fonts. Never use system fonts for display headings.

### Effects

```css
/* Glassmorphism for navbar and floating panels */
.glass {
  background: var(--surface-glass);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--border);
}

/* Card elevation */
.card {
  border-radius: 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0,0,0,0.4);
}

/* CTA buttons — pill shape with glow */
.btn-primary {
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 999px;
  padding: 0.75rem 2rem;
  font-weight: 600;
  cursor: pointer;
  transition: box-shadow 0.3s ease, transform 0.15s ease;
}
.btn-primary:hover {
  box-shadow: 0 0 24px rgba(255,107,53,0.4);
  transform: scale(1.03);
}

/* Scroll entrance animations */
.fade-up {
  opacity: 0;
  transform: translateY(30px);
  transition: opacity 0.6s ease-out, transform 0.6s ease-out;
}
.fade-up.visible {
  opacity: 1;
  transform: translateY(0);
}
```

### Layout Constants

```
Max content width: 1200px, centered with auto margins
Section padding: 100px-120px vertical
Card grid gap: 24px
Mobile breakpoint: 768px
Tablet breakpoint: 1024px
```

## Page Sections

Build in this order. Each section has one job.

### 1. Navigation (glassmorphism sticky bar)

- Fixed to top, transparent on scroll-top, gains glass background on scroll
- Left: logo (text or SVG)
- Center or right: 4-5 nav links (Home, Menu, About, Contact)
- Far right: cart icon with item-count badge (accent color)
- Mobile: hamburger menu with slide-in drawer
- Height: 64-72px

### 2. Hero (the poster)

This is the most important viewport. It must feel like a magazine cover, not a template.

- Full viewport height (`100vh` or `min-height: 100vh`)
- Single high-quality food photograph as background (use `generate_image` — never a placeholder)
- Dark gradient overlay from bottom: `linear-gradient(to top, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.2) 60%, transparent 100%)`
- Content positioned in lower-left or center-left:
  - Display heading (max 6 words, serif font)
  - One-line subtitle (sans-serif, muted color)
  - CTA button ("Order Now" or "Explore Menu")
- Optional: small scroll-down indicator at bottom center

Image prompt guidance: generate an overhead shot of beautifully plated food on a dark surface, dramatic lighting, shallow depth of field, food photography style, no text or UI elements in the image.

### 3. Menu (the core)

- Category tabs: horizontal row with pill-shaped active state (accent background). Scrollable on mobile.
- Dish cards in a responsive grid (4 cols desktop → 2 cols tablet → 1 col mobile)
- Each card contains:
  - Dish photo (aspect-ratio: 4/3, object-fit: cover, 12px border-radius)
  - Dish name (card-title weight)
  - Short description (1 line, text-muted, truncated with ellipsis)
  - Price (accent-gold, bold)
  - "Add" button (small pill, accent border or filled)
- Hover: card lifts, photo scales slightly (1.05)
- Generate 6-8 dish images using `generate_image`. Each image prompt should describe a specific dish relevant to the cuisine.

### 4. Featured / Specials (the spotlight)

- Full-width section, split layout: large dish photo on one side (50%), text content on the other
- Content side: section label ("Chef's Special"), dish name (display font), multi-line description, ingredient tags (small pills), price, CTA
- Second featured item: reverse the layout (photo switches sides)
- Use `generate_image` for the spotlight photos — these should be close-up, dramatic, hero-quality food shots

### 5. How It Works (the flow)

- 3 steps in a horizontal row (stacks vertically on mobile)
- Each step: numbered circle (accent color), icon, title (bold), one-line description
- Steps: Browse Menu → Customize Order → Fast Delivery (or equivalent)
- Subtle connecting line between steps on desktop
- Fade-up animation on scroll entry

### 6. Testimonials (social proof)

- Horizontal carousel (CSS scroll-snap or simple JS auto-slide)
- Each testimonial: large quote text (slightly larger than body), customer name, role/location
- No card borders — use spacing and typography to separate
- Auto-play with pause on hover
- 3-5 testimonials with realistic names and quotes

### 7. Footer

- Dark background (slightly different from page bg, e.g., `#111`)
- 4-column grid: Brand (logo + tagline), Quick Links, Contact Info, Newsletter
- Newsletter: email input + submit button (accent)
- Social media icons row
- Copyright line at bottom
- Generous vertical padding (80px+)

## Food Photography Generation

This is critical. Bad food images ruin everything.

When calling `generate_image`, use prompts like:
- "Overhead flat-lay of [specific dish] on dark slate surface, dramatic side lighting, food photography, garnished with fresh herbs, shallow depth of field, no text"
- "Close-up of [specific dish] with steam rising, dark moody background, professional food photography, rich colors, no text or UI"
- "Three [specific items] arranged artfully on dark wood table, warm lighting, food magazine style, no text"

Rules:
- Always specify "no text" and "no UI elements" in image prompts
- Always specify the lighting style (dramatic, warm, natural)
- Always specify the surface/background (dark slate, dark wood, black marble)
- Generate cuisine-appropriate dishes, not generic "food"
- Minimum 6 unique dish images + 1 hero image + 2 spotlight images

## Technical Implementation

### Stack
```bash
npx -y create-vite@latest ./ -- --template react
```

### File Structure
```
src/
├── App.jsx          # Main app with all sections
├── App.css          # All styles (design system + components)
├── components/
│   ├── Navbar.jsx
│   ├── Hero.jsx
│   ├── Menu.jsx
│   ├── Featured.jsx
│   ├── HowItWorks.jsx
│   ├── Testimonials.jsx
│   └── Footer.jsx
├── data/
│   └── menuData.js  # Menu items array with names, prices, descriptions, image paths
└── main.jsx
index.html           # Google Fonts link tags
```

### Scroll Animation (Intersection Observer)
```javascript
// In App.jsx or a useEffect hook
const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      }
    });
  },
  { threshold: 0.1 }
);
document.querySelectorAll('.fade-up').forEach(el => observer.observe(el));
```

### Responsive Approach
- Use CSS Grid for section layouts
- Use CSS `clamp()` for fluid typography
- Mobile-first: default styles for mobile, `@media (min-width: 768px)` for desktop
- Test navbar collapse, card grid reflow, hero text sizing

## Hard Rules

- No placeholder images. Generate every food image.
- No generic card grids as the first impression. The hero is a full-bleed photograph.
- No more than two typefaces.
- No more than one accent color (gold is a highlight, not a second accent).
- No Tailwind unless the user explicitly requests it.
- No filler copy. Menu descriptions should sound like a real menu.
- No floating UI that overlaps content on mobile.
- Every interactive element gets a unique `id`.
- Semantic HTML: `<nav>`, `<main>`, `<section>`, `<footer>`, `<article>` for cards.
- The page must look premium with all animations disabled (reduced-motion).

## Quality Checks

Before delivering, verify:

- [ ] Hero image is generated and full-bleed, not a placeholder
- [ ] Navbar turns glassy on scroll
- [ ] Menu cards hover with lift + shadow
- [ ] At least 6 dish images are generated and loading
- [ ] Featured section alternates layout direction
- [ ] Testimonials auto-rotate
- [ ] Footer newsletter input is functional-looking
- [ ] Mobile: nav collapses, cards stack, hero text is readable
- [ ] Scroll animations fire on first entry
- [ ] Google Fonts are loading (check Network tab)
- [ ] No horizontal overflow on any viewport
- [ ] `<title>` and `<meta description>` are set
