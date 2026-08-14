# Digital Language Map

An interactive Streamlit atlas of Pakistan's languages and Sufi heritage — 55 languages across all regions, an interactive province choropleth, and a highlighted Kashmir region overlay.

## Folder structure (upload exactly like this)

```
Digital-Language-Map/
├── app.py
├── requirements.txt
└── data/
    ├── languages.csv
    ├── sufi_poets.csv
    ├── pakistan_provinces.geojson
    └── kashmir_disputed_region.geojson
```

## How to upload to GitHub

1. Create a new repository named `Digital-Language-Map`.
2. Upload `app.py` and `requirements.txt` to the **repo root**.
3. Create a folder named `data` inside the repo, and upload all 4 files from the `data/` folder into it.
4. Confirm the final layout matches the structure above exactly — `app.py` reads files using the relative path `data/<filename>`, so the `data` folder must sit next to `app.py`, not inside another folder.

## How to deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**.
2. Point it at this repository, branch `main`, main file path `app.py`.
3. Deploy. First boot installs dependencies from `requirements.txt` (includes `requests`, needed to fetch the Pakistan country outline).

## What's inside

- **Languages Map tab** — 55 languages plotted with category-colored markers, Pakistan + Kashmir boundary overlays, a region → language cascading dropdown, and a province-level choropleth.
- **Sufi Poets Map tab** — 10 historical Sufi poets plotted with their region, order, and famous works.
