# Trailer Hunt

Mobile-friendly Craigslist trailer finder with a dark blue/purple theme.

## Status
The site and Python collection workflow are under development. Live Craigslist extraction is **not yet verified**; empty results are not proof that no trailers exist.

## Setup
The site will be hosted using GitHub Pages from the `docs/` folder on `main`. A GitHub Actions workflow will run the Python collector, and publish listings to `docs/data/listings.json` when valid results are found.

No API key is required for the initial HTTP-based collector. Do not share or commit tokens.

Searches target 8.5 x 16 foot trailers and related phrases, up to $1,500, in Charleston, Columbia, Hilton Head, Myrtle Beach, Augusta and Savannah.
