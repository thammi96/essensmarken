# Walkthrough: Wertmarken & Verzehrkarten Generator

We have successfully rebuilt the application to incorporate density layouts, color coding, date printing, and a secure session-based authentication screen.

## Project Structure
- [app.py](file:///home/marcothamm/.gemini/antigravity-ide/brain/cdb65283-1cf3-4a12-8d29-03e6d7b012a2/app.py): Handles protected routes, session auth, and WeasyPrint PDF compile.
- [templates/login.html](file:///home/marcothamm/.gemini/antigravity-ide/brain/cdb65283-1cf3-4a12-8d29-03e6d7b012a2/templates/login.html): Beautiful login screen for authorization.
- [templates/index.html](file:///home/marcothamm/.gemini/antigravity-ide/brain/cdb65283-1cf3-4a12-8d29-03e6d7b012a2/templates/index.html): Custom ticket setup form, date input, layout chooser, color boxes, and live ticket scaling previews.
- [templates/pdf_template.html](file:///home/marcothamm/.gemini/antigravity-ide/brain/cdb65283-1cf3-4a12-8d29-03e6d7b012a2/templates/pdf_template.html): Dynamic CSS variable-based sizing to fit 2x2 (4), 4x4 (16), or 4x6 (24) grids.
- [Dockerfile](file:///home/marcothamm/.gemini/antigravity-ide/brain/cdb65283-1cf3-4a12-8d29-03e6d7b012a2/Dockerfile): Trixie-compatible package dependencies.
- [docker-compose.yml](file:///home/marcothamm/.gemini/antigravity-ide/brain/cdb65283-1cf3-4a12-8d29-03e6d7b012a2/docker-compose.yml): Configured for port `3333`.

## Authentication / Login Credentials

When you publish this service, the application will enforce an authentication wall.
- **Default Username:** `admin`
- **Default Password:** `admin`

*Note: You can override these credentials by setting `APP_USERNAME` and `APP_PASSWORD` environment variables in your deployment environment or inside the `docker-compose.yml` file.*

## Run Instructions

1. Rebuild and start the container:
   ```bash
   docker compose up --build
   ```
2. Open your browser and navigate to:
   ```
   http://localhost:3333
   ```
3. Enter the credentials (`admin` / `admin`) to access the generator dashboard.

## Completed Features

- **No Tick Circles:** The printable PDF ticket boxes no longer contain the checkbox circles, leaving a clean stamp field.
- **Dynamic Density Scaling:** You can choose between:
  - **2x2** (4 large tickets/page)
  - **4x4** (16 medium tickets/page)
  - **4x6** (24 small tickets/page)
  The font sizes, borders, and margins adapt dynamically in the PDF to prevent clipping.
- **Color Coding:** Stamp boxes are color-coded based on their value:
  - **2.00 €** boxes have a soft green background (`#e2f5e2`).
  - **1.00 €** boxes have a soft yellow background (`#fff9db`).
  - **0.50 €** boxes have a soft grey background (`#f1f3f5`).
- **Date Stamp:** You can input the event date, which is printed at the bottom of each ticket.
