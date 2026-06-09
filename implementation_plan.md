# Implementation Plan - Extension & Authentication

We will add advanced layouts (2x2, 4x4, 4x6), dynamic scaling, date stamping, color-coded denominations, and a security login screen before accessing the generator.

## Proposed Changes

### 1. Authentication System
- Add `/login` route and login page.
- Read `APP_USERNAME` and `APP_PASSWORD` from environment variables (fallback: admin / admin).
- Use Flask's `session` to store the authenticated state.
- Add a `@login_required` decorator or request handler to protect `/` and `/generate`.

### 2. Frontend Configuration UI
- Add fields for **Veranstaltungsdatum** (Date input).
- Add layout selection options:
  - `2x2` (4 Tickets per A4 page)
  - `4x4` (16 Tickets per A4 page)
  - `4x6` (24 Tickets per A4 page)
- Ensure the interactive live ticket preview on the right shows the colored backgrounds, the date, and scales its text sizing based on the selected layout.

### 3. PDF Layout & Sizing Calculations
- Remove the round circles (`::after`) from the stamp boxes in the PDF.
- Map the selected layout (2x2, 4x4, 4x6) to CSS class styling.
- Dynamically scale ticket padding, margins, logo size, and font sizes based on the layout option.
- Render background colors on the stamp boxes based on their values:
  - 2.00 € -> Light Green (`#e2f5e2` / border `#a3d9a3`)
  - 1.00 € -> Light Yellow (`#fff9db` / border `#ffe066`)
  - 0.50 € -> Light Gray (`#f1f3f5` / border `#ced4da`)
  - Other values -> Fallback Light Blue (`#e7f5ff` / border `#a5d8ff`)

## Verification Plan

### Automated Tests
- Syntax check.
- Verification of session creation and redirect when unauthorized.

### Manual Verification
- Deploy locally and try to open `http://localhost:3333` (should redirect to `/login`).
- Login with configured credentials.
- Set layout to 4x4 and 4x6, change dates, and download the PDF.
- Inspect the PDF grid spacing, box color codings, date text, and verify that tick circles are removed.
