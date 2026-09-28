# static/

Contains all custom CSS and JavaScript. Django serves these files directly in development via `STATICFILES_DIRS = [BASE_DIR / "static"]`.

For production, run `python manage.py collectstatic` to copy everything into `staticfiles/` (gitignored), then serve that directory via nginx or a CDN.

## Files

### `css/app.css`

Single CSS file for the entire application. Organised into sections:

| Section | What it covers |
|---|---|
| CSS custom properties (variables) | Colours, radii, shadows for both light and dark themes |
| Reset / base | Box-sizing, font, body defaults |
| Public shell | Landing page layout, hero section, stats, feature cards |
| Staff shell | App shell grid, sidebar, navbar, app-content area |
| Citizen shell | Simple header for citizen portal |
| Components | Badges, status colours, buttons, cards, citizen cards, issue rows |
| Forms | Input styles, label, select, textarea |
| Sidebar | Active link highlight, section labels, footer user block |
| Responsive | Mobile sidebar overlay, hamburger button |

#### Theme system

The app supports light and dark themes. The theme is stored in `localStorage` under the key `dcrs_theme`. A small inline script in `base.html` applies the theme before the first paint to prevent flash.

CSS variables are defined under `:root` and `[data-theme="dark"]` selectors. The `data-theme` attribute is set on `<html>`.

#### Status badge colours

The `status-*` CSS classes used in badge elements:

| Class | Colour | Used for |
|---|---|---|
| `status-PENDING` | Amber | Citizen awaiting approval / Issue open |
| `status-APPROVED` | Green | Citizen approved |
| `status-REJECTED` | Red | Citizen rejected |
| `status-SUSPENDED` | Grey | Citizen suspended |
| `status-OPEN` | Blue | Issue open |
| `status-IN_PROGRESS` | Indigo | Issue in progress |
| `status-ESCALATED` | Orange | Issue escalated |
| `status-RESOLVED` | Green | Issue resolved |
| `status-CLOSED` | Grey | Issue closed |

### `js/app.js`

Client-side interactions:

| Feature | How it works |
|---|---|
| Theme toggle | Toggles `data-theme` on `<html>`, saves to `localStorage`, updates button icon |
| Mobile sidebar | Hamburger button and overlay toggle the `open` class on `.app-sidebar` |
| Active sidebar link | Compares `window.location.pathname` to each link's `href`, adds `active` class |
| Cascading dropdowns | Listens to region/district/ward selects on the registration form, fetches options via the `/api/localities/` JSON API |

## External assets (CDN, not stored locally)

| Asset | Version | Purpose |
|---|---|---|
| Bootstrap CSS | 5.3.3 | Grid, utilities, dropdowns |
| Bootstrap JS bundle | 5.3.3 | Dropdowns, modals |
| Bootstrap Icons | 1.11.3 | Icon font used throughout |
| Google Fonts — Inter | Latest | Primary UI font |
