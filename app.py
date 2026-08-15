import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
import os


# -------------------------------
# PAGE CONFIGURATION
# -------------------------------

st.set_page_config(
    page_title="Digital Language Map",
    page_icon="🌐",
    layout="wide"
)


# -------------------------------
# CUSTOM STYLING
# -------------------------------

st.markdown(
    """
    <link rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />
    <style>
    .material-symbols-outlined {
        font-family: 'Material Symbols Outlined';
        font-weight: normal;
        font-style: normal;
        display: inline-block;
        line-height: 1;
        white-space: nowrap;
        word-wrap: normal;
        direction: ltr;
    }
    /* Overall page */
    .main {
        background-color: #fafafa;
    }

    /* Title area */
    h1 {
        font-weight: 800 !important;
        letter-spacing: -0.5px;
        color: #0f172a !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }

    /* Sidebar nav header */
    .sidebar-brand {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 4px 0 14px 0;
        margin-bottom: 6px;
    }
    .sidebar-brand-icon {
        font-size: 26px;
        color: #2563eb;
    }
    .sidebar-brand-text {
        font-size: 17px;
        font-weight: 800;
        color: #0f172a;
        letter-spacing: -0.3px;
    }
    .sidebar-eyebrow {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #94a3b8;
        margin-bottom: 6px;
    }

    /* Sidebar nav buttons */
    section[data-testid="stSidebar"] div[data-testid="stButton"] button {
        text-align: left !important;
        justify-content: flex-start !important;
        border: none !important;
        background-color: transparent !important;
        color: #334155 !important;
        font-weight: 500 !important;
        padding: 8px 12px !important;
        border-radius: 8px !important;
        box-shadow: none !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {
        background-color: #eff6ff !important;
        color: #2563eb !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stButton"] button p {
        font-size: 15px !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="primary"] {
        background-color: #dbeafe !important;
        color: #1d4ed8 !important;
        font-weight: 700 !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="primary"] p {
        color: #1d4ed8 !important;
    }

    /* Overview stat cards */
    .stat-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 18px 12px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        height: 100%;
    }
    .stat-card .stat-icon {
        font-size: 26px;
        margin-bottom: 6px;
    }
    .stat-card .stat-label {
        font-size: 13px;
        font-weight: 600;
        color: #64748b;
        margin-bottom: 4px;
    }
    .stat-card .stat-value {
        font-size: 22px;
        font-weight: 800;
        color: #0f172a;
    }
    .stat-card .stat-sub {
        font-size: 12px;
        font-weight: 700;
        margin-top: 2px;
    }

    /* Overview info callout */
    .info-callout {
        background-color: #eff6ff;
        border: 1px solid #bfdbfe;
        border-radius: 12px;
        padding: 14px 18px;
        color: #1e3a8a;
        font-size: 14px;
        display: flex;
        gap: 10px;
        align-items: flex-start;
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 16px 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    div[data-testid="stMetricLabel"] {
        font-weight: 600;
        color: #64748b;
    }
    div[data-testid="stMetricValue"] {
        color: #0f172a;
    }

    /* Section headers in main body */
    h2 {
        color: #0f172a !important;
        font-weight: 700 !important;
        margin-top: 10px;
    }

    /* Pills widget (category / status selectors) */
    div[data-testid="stPills"] button {
        border-radius: 999px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# -------------------------------
# TITLE
# -------------------------------

st.title("🌐 Digital Language Map")


# -------------------------------
# LOAD DATA
# -------------------------------

REQUIRED_LANGUAGE_COLS = [
    "Language", "Category", "Family", "Province", "Speakers",
    "Script", "Endangerment_Status", "Description",
    "Latitude", "Longitude"
]

REQUIRED_POET_COLS = [
    "Name", "Birth", "Death", "Language", "Region",
    "Sufi_Order", "Famous_Work", "Description",
    "Latitude", "Longitude"
]


def normalize_columns(df):
    """Strip whitespace and normalize casing/spacing so small CSV
    formatting differences (e.g. ' category ', 'category') don't
    break the app."""
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def check_required_columns(df, required, file_label):
    missing = [c for c in required if c not in df.columns]
    if missing:
        st.error(
            f"❌ **{file_label} is missing required column(s): "
            f"{', '.join(missing)}**\n\n"
            f"Columns found in the file: {list(df.columns)}\n\n"
            "Please check your CSV header row for typos, extra spaces, "
            "or a different delimiter (e.g. semicolon instead of comma)."
        )
        st.stop()


@st.cache_data
def load_data():

    base_path = os.path.dirname(__file__)

    language_file = os.path.join(base_path, "data", "languages.csv")
    poet_file = os.path.join(base_path, "data", "cultural_sites.csv")

    if not os.path.exists(language_file):
        st.error(f"❌ File not found: {language_file}")
        st.stop()

    if not os.path.exists(poet_file):
        st.error(f"❌ File not found: {poet_file}")
        st.stop()

    languages = pd.read_csv(language_file, encoding="utf-8-sig")
    poets = pd.read_csv(poet_file, encoding="utf-8-sig")

    languages = normalize_columns(languages)
    poets = normalize_columns(poets)

    return languages, poets


@st.cache_data
def load_provinces_geojson():
    """Load the local Pakistan provinces boundary file (data/pakistan_provinces.geojson)."""
    base_path = os.path.dirname(__file__)
    province_file = os.path.join(base_path, "data", "pakistan_provinces.geojson")

    if not os.path.exists(province_file):
        return None

    with open(province_file, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_5_provinces_geojson():
    """Load the simplified 5-province boundary file used on the Overview page
    (Punjab, Sindh, KP, Balochistan, Azad Kashmir)."""
    base_path = os.path.dirname(__file__)
    province_file = os.path.join(base_path, "data", "pakistan_5_provinces.geojson")

    if not os.path.exists(province_file):
        return None

    with open(province_file, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_province_population():
    """Load 2017 census population totals (with sex breakdown) per province."""
    base_path = os.path.dirname(__file__)
    pop_file = os.path.join(base_path, "data", "province_population_2017.json")

    if not os.path.exists(pop_file):
        return None

    with open(pop_file, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_province_label_positions():
    """Load lon/lat label positions for each province, used on the Overview map."""
    base_path = os.path.dirname(__file__)
    label_file = os.path.join(base_path, "data", "province_label_positions.json")

    if not os.path.exists(label_file):
        return {}

    with open(label_file, "r", encoding="utf-8") as f:
        return json.load(f)


def match_provinces(province_text, all_province_names):
    """Map a free-text Province value from languages.csv (e.g. 'Southern Punjab',
    'Khyber Pakhtunkhwa and Punjab', 'All Pakistan') to one or more actual
    polygon province names."""
    if not isinstance(province_text, str):
        return []

    text = province_text.lower()

    if "all pakistan" in text:
        return list(all_province_names)

    matches = [
        name for name in all_province_names
        if name.lower() in text
    ]
    return matches


@st.cache_data
def load_kashmir_boundary():
    """Load the local Kashmir region (disputed/approximate) boundary file."""
    base_path = os.path.dirname(__file__)
    kashmir_file = os.path.join(base_path, "data", "kashmir_disputed_region.geojson")

    if not os.path.exists(kashmir_file):
        return None

    with open(kashmir_file, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_districts_geojson():
    """Load the district-level (ADM3) boundary file. Each district carries its
    parent Division name so it can be joined to the census division data."""
    base_path = os.path.dirname(__file__)
    district_file = os.path.join(base_path, "data", "pakistan_districts.geojson")

    if not os.path.exists(district_file):
        return None

    with open(district_file, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_census_divisions():
    """Load 2017 PBS census mother-tongue data at division level."""
    base_path = os.path.dirname(__file__)
    census_file = os.path.join(base_path, "data", "census_divisions_2017.csv")

    if not os.path.exists(census_file):
        return None

    return pd.read_csv(census_file)


@st.cache_data
def load_national_census():
    """Load 2017 PBS national mother-tongue percentages."""
    base_path = os.path.dirname(__file__)
    national_file = os.path.join(base_path, "data", "national_census_2017.json")

    if not os.path.exists(national_file):
        return None

    with open(national_file, "r", encoding="utf-8") as f:
        return json.load(f)


# Maps a language name as it appears in languages.csv to the matching
# column name in the PBS census tables (only major census-tracked languages
# have a direct match; others are not individually broken out by PBS).
CENSUS_LANGUAGE_MAP = {
    "Urdu": "URDU",
    "Punjabi": "PUNJABI",
    "Sindhi": "SINDHI",
    "Pashto": "PUSHTO",
    "Balochi": "BALOCHI",
    "Kashmiri": "KASHMIRI",
    "Saraiki": "SARAIKI",
    "Hindko": "HINDKO",
    "Brahui": "BRAHVI",
}


@st.cache_data
def load_pakistan_boundary():
    """Fetch Pakistan's national boundary polygon (cached) for map highlighting."""
    url = "https://raw.githubusercontent.com/datasets/geo-countries/main/data/countries.geojson"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        world = response.json()
    except Exception:
        return None

    pakistan_feature = next(
        (f for f in world["features"] if f["properties"].get("name") == "Pakistan"),
        None
    )

    if pakistan_feature is None:
        return None

    return {"type": "FeatureCollection", "features": [pakistan_feature]}


languages, poets = load_data()

check_required_columns(languages, REQUIRED_LANGUAGE_COLS, "languages.csv")
check_required_columns(poets, REQUIRED_POET_COLS, "cultural_sites.csv")

# Make sure numeric columns are actually numeric (guards against
# stray text, commas, or blank cells in the CSV).
languages["Speakers"] = pd.to_numeric(languages["Speakers"], errors="coerce").fillna(0)
languages["Latitude"] = pd.to_numeric(languages["Latitude"], errors="coerce")
languages["Longitude"] = pd.to_numeric(languages["Longitude"], errors="coerce")
poets["Latitude"] = pd.to_numeric(poets["Latitude"], errors="coerce")
poets["Longitude"] = pd.to_numeric(poets["Longitude"], errors="coerce")

# Drop rows with missing coordinates so the map doesn't error out.
languages = languages.dropna(subset=["Latitude", "Longitude"])
poets = poets.dropna(subset=["Latitude", "Longitude"])


# -------------------------------
# PAGES (name -> Material icon shortcode)
# -------------------------------

PAGES = {
    "Overview": "map",
    "Provinces": "account_balance",
    "Districts": "location_on",
    "Mother Tongue Speakers": "groups",
    "All Languages": "public",
    "Endangered Languages": "warning",
    "Cultural Map": "museum",
}


# -------------------------------
# SIDEBAR — real clickable navigation
# -------------------------------

if "current_page" not in st.session_state:
    st.session_state.current_page = "Overview"

st.sidebar.markdown(
    """
    <div class="sidebar-brand">
        <span class="sidebar-brand-icon">🌐</span>
        <span class="sidebar-brand-text">Digital Language Map</span>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown("<div class='sidebar-eyebrow'>Explore Atlas</div>", unsafe_allow_html=True)

for page_name, icon in PAGES.items():
    is_active = st.session_state.current_page == page_name
    if st.sidebar.button(
        f":material/{icon}: {page_name}",
        key=f"nav_{page_name}",
        use_container_width=True,
        type="primary" if is_active else "secondary"
    ):
        st.session_state.current_page = page_name
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style="display:flex; align-items:center; gap:8px; padding:4px 12px; color:#94a3b8; font-size:13px;">
        <span style="font-size:16px;">🏛️</span>
        <span>Pakistan Cultural &amp; Linguistic Atlas</span>
    </div>
    """,
    unsafe_allow_html=True
)

current_page = st.session_state.current_page

# Endangered-category languages live on their own dedicated page.
endangered_languages = languages[languages["Category"] == "Endangered"].copy()
languages = languages[languages["Category"] != "Endangered"]


# -------------------------------
# SHARED HELPERS
# -------------------------------

language_colors = {
    "National": "green",
    "Regional": "blue",
    "Endangered": "red"
}

# Endangerment severity color scale, used on the Endangered Languages tab
# map markers and its legend.
severity_colors = {
    "Vulnerable": "#fbbf24",
    "Definitely Endangered": "#fb923c",
    "Severely Endangered": "#ef4444",
    "Critically Endangered": "#7f1d1d",
}
severity_order = ["Vulnerable", "Definitely Endangered", "Severely Endangered", "Critically Endangered"]

chart_template = "plotly_white"
color_sequence = px.colors.qualitative.Set2

pakistan_boundary = load_pakistan_boundary()
kashmir_boundary = load_kashmir_boundary()


def add_pakistan_boundary(map_obj):
    # Both layers use identical styling so Pakistan + Kashmir read as one
    # visually consistent base color across the whole country.
    base_style = {
        "fillColor": "#2ca25f",
        "color": "#006d2c",
        "weight": 3,
        "fillOpacity": 0.18,
    }
    base_highlight = {
        "fillOpacity": 0.32,
        "weight": 4,
    }

    if pakistan_boundary:
        folium.GeoJson(
            pakistan_boundary,
            name="Pakistan Boundary",
            style_function=lambda feature: base_style,
            highlight_function=lambda feature: base_highlight,
        ).add_to(map_obj)

    if kashmir_boundary:
        folium.GeoJson(
            kashmir_boundary,
            name="Kashmir Region (Approximate Boundary)",
            style_function=lambda feature: base_style,
            highlight_function=lambda feature: base_highlight,
            tooltip="Kashmir Region — approximate boundary",
        ).add_to(map_obj)


# -------------------------------
# TABS: OVERVIEW -> PROVINCES -> DISTRICTS -> SPEAKERS -> LANGUAGES -> ENDANGERED -> POETS
# -------------------------------

# (Navigation now happens via the sidebar buttons above, not a tab bar.)

full_languages, _ = load_data()
full_languages["Speakers"] = pd.to_numeric(full_languages["Speakers"], errors="coerce").fillna(0)
national_census = load_national_census()

CENSUS_LANG_LABELS = {
    "URDU": "Urdu", "PUNJABI": "Punjabi", "SINDHI": "Sindhi",
    "PUSHTO": "Pashto", "BALOCHI": "Balochi", "KASHMIRI": "Kashmiri",
    "SARAIKI": "Saraiki", "HINDKO": "Hindko", "BRAHVI": "Brahui",
    "OTHERS": "Other Languages"
}


# ===============================
# OVERVIEW PAGE
# ===============================

if current_page == "Overview":

    st.subheader("Pakistan at a Glance")
    st.caption(
        "An overview of Pakistan's provinces, population, and linguistic diversity "
        "based on the 2017 Census of Pakistan."
    )

    provinces_5_geojson = load_5_provinces_geojson()
    province_population = load_province_population()
    label_positions = load_province_label_positions()

    if provinces_5_geojson is None or province_population is None:
        st.info(
            "Province summary files not found. Add `data/pakistan_5_provinces.geojson` "
            "and `data/province_population_2017.json` to your repo to enable this view."
        )
    else:
        province_names = [f["properties"]["Province"] for f in provinces_5_geojson["features"]]
        province_color_map = {
            "Punjab": "#3b82f6",
            "Sindh": "#f97316",
            "Khyber Pakhtunkhwa": "#2dd4bf",
            "Balochistan": "#a78bfa",
            "Azad Kashmir": "#7dd3fc",
        }

        map_df = pd.DataFrame({"Province": province_names})

        fig_overview = px.choropleth(
            map_df,
            geojson=provinces_5_geojson,
            locations="Province",
            featureidkey="properties.Province",
            color="Province",
            color_discrete_map=province_color_map,
            template="plotly_white"
        )
        fig_overview.update_traces(marker_line_color="#ffffff", marker_line_width=1.5)
        fig_overview.update_geos(fitbounds="locations", visible=False)

        # Province name labels directly on the map
        label_lons = [label_positions[p]["lon"] for p in province_names if p in label_positions]
        label_lats = [label_positions[p]["lat"] for p in province_names if p in label_positions]
        label_text = [
            "Azad Jammu &<br>Kashmir" if p == "Azad Kashmir" else p
            for p in province_names if p in label_positions
        ]
        fig_overview.add_trace(go.Scattergeo(
            lon=label_lons,
            lat=label_lats,
            mode="text",
            text=label_text,
            textfont=dict(size=12, color="#0f172a", family="-apple-system, Segoe UI, sans-serif"),
            showlegend=False,
            hoverinfo="skip"
        ))

        fig_overview.update_layout(
            title=dict(text="Provinces of Pakistan", font=dict(size=16, color="#0f172a"), x=0.02),
            margin=dict(t=50, b=10, l=10, r=10),
            legend=dict(title="Provinces", orientation="v", yanchor="bottom", y=0.02, xanchor="right", x=0.98,
                        bgcolor="rgba(255,255,255,0.9)", bordercolor="#e2e8f0", borderwidth=1),
            height=520
        )

        st.plotly_chart(fig_overview, use_container_width=True)

        st.divider()

        # --- Stat cards ---
        national = province_population["national_total"]
        male_pct = round(100 * national["Male"] / national["Total"], 2)
        female_pct = round(100 * national["Female"] / national["Total"], 2)
        trans_pct = round(100 * national["Transgender"] / national["Total"], 2)
        total_languages = len(full_languages)

        stat_cards = [
            ("groups", "Total Population", f"{national['Total']:,}", None, "#2563eb"),
            ("man", "Men", f"{national['Male']:,}", f"{male_pct}%", "#2563eb"),
            ("woman", "Women", f"{national['Female']:,}", f"{female_pct}%", "#db2777"),
            ("transgender", "Transgender", f"{national['Transgender']:,}", f"{trans_pct}%", "#16a34a"),
            ("forum", "Total Languages Spoken", str(total_languages), None, "#0f172a"),
        ]

        cols = st.columns(5)
        for col, (icon, label, value, sub, color) in zip(cols, stat_cards):
            with col:
                sub_html = f"<div class='stat-sub' style='color:{color};'>{sub}</div>" if sub else ""
                st.markdown(
                    f"""
                    <div class="stat-card">
                        <div class="stat-icon" style="color:{color};">
                            <span class="material-symbols-outlined" style="font-size:26px; vertical-align:middle;">{icon}</span>
                        </div>
                        <div class="stat-label">{label}</div>
                        <div class="stat-value">{value}</div>
                        {sub_html}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        st.caption(
            "Source: Pakistan Bureau of Statistics — 6th Population & Housing Census 2017 (final results). "
            f"Language count reflects the {total_languages} languages catalogued in this atlas; "
            "Pakistan's total documented languages are commonly estimated at 70–80."
        )

        st.divider()

        # --- Population by Province table ---
        st.markdown("##### Population by Province")

        table_rows = []
        for name, v in province_population["provinces"].items():
            table_rows.append({
                "Province": name,
                "Population": v["Total"],
                "Men": v["Male"] if v["Male"] is not None else None,
                "Women": v["Female"] if v["Female"] is not None else None,
                "Transgender": v["Transgender"] if v["Transgender"] is not None else None,
                "% of Total": v["Percentage"]
            })
        table_df = pd.DataFrame(table_rows)

        st.dataframe(
            table_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Population": st.column_config.NumberColumn(format="%d"),
                "Men": st.column_config.NumberColumn(format="%d"),
                "Women": st.column_config.NumberColumn(format="%d"),
                "Transgender": st.column_config.NumberColumn(format="%d"),
                "% of Total": st.column_config.ProgressColumn(
                    format="%.2f%%", min_value=0, max_value=max(table_df["% of Total"])
                ),
            }
        )
        st.caption(
            "Men/Women/Transgender for Azad Jammu & Kashmir are not shown — that figure comes from the "
            "AJK Bureau of Statistics' separate 2017 census, which was not broken down by sex in the "
            "source used here. Khyber Pakhtunkhwa includes the former FATA, merged into KP in 2018. "
            "Percentages are of the five regions shown in this table."
        )

        st.markdown(
            """
            <div class="info-callout">
                <span class="material-symbols-outlined" style="font-size:20px; color:#2563eb;">info</span>
                <span>Pakistan is home to a rich linguistic diversity. These languages belong to several
                families, including Indo-Aryan, Iranian, Dravidian, Turkic, and Tibetic, among others.</span>
            </div>
            """,
            unsafe_allow_html=True
        )


# ===============================
# PROVINCES TAB
# ===============================

if current_page == "Provinces":

    st.subheader("Language Distribution by Province")
    st.caption(
        "Pick a language to see which provinces it is spoken in. Shading reflects "
        "that language's total speaker count wherever it appears — hover any province "
        "for its exact value."
    )

    provinces_geojson = load_provinces_geojson()

    if provinces_geojson is None:
        st.info(
            "Province boundary file not found. Add `data/pakistan_provinces.geojson` "
            "to your repo to enable this view."
        )
    else:
        all_province_names = sorted({
            feat["properties"]["Province"] for feat in provinces_geojson["features"]
        })

        lang_col, stat_col = st.columns([2, 1])

        with lang_col:
            selected_language = st.selectbox(
                "Language",
                sorted(full_languages["Language"].dropna().unique()),
                index=0,
                key="province_lang_select"
            )

        lang_row = full_languages[full_languages["Language"] == selected_language].iloc[0]
        matched_provinces = match_provinces(lang_row["Province"], all_province_names)
        speaker_count = int(lang_row["Speakers"])

        with stat_col:
            st.metric(f"{selected_language} — Mother Tongue Speakers", f"{speaker_count:,}")

        province_values = pd.DataFrame({
            "Province": all_province_names,
            "Speakers": [speaker_count if p in matched_provinces else 0 for p in all_province_names]
        })

        fig_choropleth = px.choropleth(
            province_values,
            geojson=provinces_geojson,
            locations="Province",
            featureidkey="properties.Province",
            color="Speakers",
            color_continuous_scale=[[0.0, "#e5e7eb"], [1.0, "#08519c"]],
            range_color=[0, max(speaker_count, 1)],
            template="plotly_white",
            hover_name="Province",
            hover_data={"Speakers": ":,"}
        )
        fig_choropleth.update_traces(marker_line_color="#94a3b8", marker_line_width=1)
        fig_choropleth.update_geos(fitbounds="locations", visible=False)
        fig_choropleth.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            coloraxis_colorbar_title="Speakers"
        )

        st.plotly_chart(fig_choropleth, use_container_width=True)

        st.caption(f"Currently showing: **{selected_language}** — click the dropdown above to explore another language.")


# ===============================
# DISTRICTS TAB
# ===============================

if current_page == "Districts":

    st.subheader("District Map — Official 2017 Census")
    st.caption(
        "Pakistan Bureau of Statistics 2017 census, mother-tongue data by administrative "
        "division. This is the finest resolution PBS publicly released for language — "
        "so districts belonging to the same division share one color. Hover any district "
        "to see its name, division, and exact percentage. "
        "Azad Kashmir and Gilgit-Baltistan aren't part of this dataset."
    )

    districts_geojson = load_districts_geojson()
    census_divisions = load_census_divisions()

    if districts_geojson is None or census_divisions is None:
        st.info(
            "District boundary or census data file not found. Add "
            "`data/pakistan_districts.geojson` and `data/census_divisions_2017.csv` "
            "to your repo to enable this view."
        )
    else:
        census_col, census_stat_col = st.columns([2, 1])

        with census_col:
            selected_census_lang = st.selectbox(
                "Language (2017 Census)",
                list(CENSUS_LANG_LABELS.values()),
                index=0,
                key="district_lang_select"
            )

        census_col_name = [k for k, v in CENSUS_LANG_LABELS.items() if v == selected_census_lang][0]
        pct_col = census_col_name + "_PCT"

        national_pct = None
        if national_census:
            national_pct = national_census["languages"].get(census_col_name, {}).get("pct")

        with census_stat_col:
            if national_pct is not None:
                st.metric(f"{selected_census_lang} — % of Pakistan", f"{national_pct}%")

        district_rows = []
        for feat in districts_geojson["features"]:
            props = feat["properties"]
            division = props["Division"]
            match = census_divisions[census_divisions["Division"] == division]
            pct = float(match.iloc[0][pct_col]) if len(match) > 0 else None
            district_rows.append({
                "District": props["District"],
                "Division": division,
                "Percentage": pct
            })

        district_df = pd.DataFrame(district_rows)
        max_pct = district_df["Percentage"].max()
        district_df["Percentage_display"] = district_df["Percentage"].fillna(0)

        # Quick jump-to-district search, above the map.
        search_district = st.selectbox(
            "Jump to a district (optional)",
            ["— none —"] + sorted(district_df["District"].unique()),
            index=0,
            key="district_search"
        )
        if search_district != "— none —":
            row = district_df[district_df["District"] == search_district].iloc[0]
            pct_display = f"{row['Percentage']:.2f}%" if pd.notna(row["Percentage"]) else "No data"
            st.info(f"**{search_district}** (Division: {row['Division']}) — {selected_census_lang}: {pct_display}")

        fig_district = px.choropleth(
            district_df,
            geojson=districts_geojson,
            locations="District",
            featureidkey="properties.District",
            color="Percentage_display",
            color_continuous_scale=[[0.0, "#e5e7eb"], [1.0, "#08519c"]],
            range_color=[0, max(max_pct, 1)],
            template="plotly_white",
            hover_name="District",
            hover_data={"Division": True, "Percentage_display": ":.2f"}
        )
        fig_district.update_traces(marker_line_color="#94a3b8", marker_line_width=0.6)
        fig_district.update_geos(fitbounds="locations", visible=False)
        fig_district.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            coloraxis_colorbar_title="% Speakers"
        )

        st.plotly_chart(fig_district, use_container_width=True)


# ===============================
# MOTHER TONGUE SPEAKERS TAB
# ===============================

if current_page == "Mother Tongue Speakers":

    st.subheader("Mother Tongue Speakers — 2017 Census")
    st.caption(
        "Pick a language for its official national numbers, ranked against every other "
        "census-tracked language."
    )

    if national_census is None:
        st.info("Census data file not found. Add `data/national_census_2017.json` to your repo to enable this view.")
    else:
        selected_speaker_lang = st.selectbox(
            "Language",
            list(CENSUS_LANG_LABELS.values()),
            index=0,
            key="speakers_lang_select"
        )
        speaker_col_name = [k for k, v in CENSUS_LANG_LABELS.items() if v == selected_speaker_lang][0]
        lang_data = national_census["languages"].get(speaker_col_name, {})
        lang_pct = lang_data.get("pct", 0)
        lang_count = lang_data.get("count", 0)

        # Build ranking across all census languages (excluding "Others")
        rank_rows = [
            {"Language": CENSUS_LANG_LABELS[k], "Percentage": v["pct"], "Count": v["count"]}
            for k, v in national_census["languages"].items() if k != "OTHERS"
        ]
        rank_df = pd.DataFrame(rank_rows).sort_values("Percentage", ascending=False).reset_index(drop=True)
        rank_df.index += 1
        rank_position = rank_df[rank_df["Language"] == selected_speaker_lang].index
        rank_label = f"#{rank_position[0]} most-spoken" if len(rank_position) > 0 and selected_speaker_lang != "Other Languages" else "—"

        s1, s2, s3 = st.columns(3)
        with s1:
            st.metric(f"{selected_speaker_lang} — Speakers", f"{lang_count:,}")
        with s2:
            st.metric("% of Pakistan", f"{lang_pct}%")
        with s3:
            st.metric("National Rank", rank_label)

        st.divider()
        st.markdown("##### How it compares to other census-tracked languages")

        fig_rank = px.bar(
            rank_df,
            x="Language",
            y="Percentage",
            template=chart_template,
            color="Language",
            color_discrete_sequence=color_sequence,
            hover_data={"Count": ":,"}
        )
        fig_rank.update_layout(
            showlegend=False,
            margin=dict(t=20, b=20, l=20, r=20),
            xaxis_title="",
            yaxis_title="% of Pakistan's Population"
        )
        # Highlight the selected language's bar
        fig_rank.update_traces(marker_line_width=0)
        for trace in fig_rank.data:
            if trace.name == selected_speaker_lang:
                trace.marker.line.width = 3
                trace.marker.line.color = "#0f172a"

        st.plotly_chart(fig_rank, use_container_width=True)

        st.dataframe(
            rank_df.rename(columns={"Percentage": "% of Pakistan", "Count": "Speaker Count"}),
            use_container_width=True
        )


# ===============================
# ALL LANGUAGES TAB
# ===============================

if current_page == "All Languages":

    st.subheader("All Languages of Pakistan")
    st.caption("Click any point on the map for that language's full details.")

    language_map = folium.Map(
        location=[30.3753, 69.3451],
        zoom_start=5,
        tiles="CartoDB positron"
    )

    add_pakistan_boundary(language_map)

    language_group = folium.FeatureGroup(name="Languages")

    for _, row in languages.iterrows():

        census_line = ""
        census_col = CENSUS_LANGUAGE_MAP.get(row["Language"])
        if national_census and census_col:
            pct = national_census["languages"].get(census_col, {}).get("pct")
            if pct is not None:
                census_line = f"<b>2017 Census:</b> {pct}% of Pakistan's population<br>"

        popup = f"""
        <div style="font-family: -apple-system, Segoe UI, Roboto, sans-serif; min-width:220px;">
            <h4 style="margin-bottom:6px; color:#0f172a;">{row['Language']}</h4>
            <b>Category:</b> {row['Category']}<br>
            <b>Family:</b> {row['Family']}<br>
            <b>Province:</b> {row['Province']}<br>
            <b>Speakers:</b> {int(row['Speakers']):,}<br>
            {census_line}<b>Script:</b> {row['Script']}<br>
            <b>Status:</b> {row['Endangerment_Status']}<br>
            <p style="margin-top:8px; color:#475569;">{row['Description']}</p>
        </div>
        """

        folium.CircleMarker(
            location=[row["Latitude"], row["Longitude"]],
            radius=max(5, min(18, row["Speakers"] / 5000000)),
            color=language_colors.get(row["Category"], "purple"),
            fill=True,
            fill_opacity=0.7,
            popup=folium.Popup(popup, max_width=350),
            tooltip=row["Language"]
        ).add_to(language_group)

    language_group.add_to(language_map)
    folium.LayerControl(collapsed=False).add_to(language_map)

    st_folium(language_map, width=1200, height=600, key="language_map")

    st.divider()
    st.markdown("#### Language Statistics")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Languages Displayed", len(languages))

    with col2:
        total_speakers = languages["Speakers"].sum()
        st.metric("Total Speakers", f"{int(total_speakers):,}")


# ===============================
# ENDANGERED LANGUAGES TAB
# ===============================

if current_page == "Endangered Languages":

    st.subheader("Endangered Languages of Pakistan")
    st.caption(
        "Languages classified as endangered, shown with severity-based coloring "
        "on both the map and chart below."
    )

    endangered_map = folium.Map(
        location=[30.3753, 69.3451],
        zoom_start=5,
        tiles="CartoDB positron"
    )

    add_pakistan_boundary(endangered_map)

    endangered_group = folium.FeatureGroup(name="Endangered Languages")

    for _, row in endangered_languages.iterrows():

        marker_color = severity_colors.get(row["Endangerment_Status"], "#7f1d1d")

        popup = f"""
        <div style="font-family: -apple-system, Segoe UI, Roboto, sans-serif; min-width:220px;">
            <h4 style="margin-bottom:6px; color:#0f172a;">{row['Language']}</h4>
            <b>Family:</b> {row['Family']}<br>
            <b>Province:</b> {row['Province']}<br>
            <b>Speakers:</b> {int(row['Speakers']):,}<br>
            <b>Script:</b> {row['Script']}<br>
            <b>Endangerment Status:</b> {row['Endangerment_Status']}<br>
            <p style="margin-top:8px; color:#475569;">{row['Description']}</p>
        </div>
        """

        folium.CircleMarker(
            location=[row["Latitude"], row["Longitude"]],
            radius=max(5, min(16, row["Speakers"] / 20000)) if row["Speakers"] > 0 else 5,
            color=marker_color,
            fill=True,
            fill_color=marker_color,
            fill_opacity=0.8,
            popup=folium.Popup(popup, max_width=350)
        ).add_to(endangered_group)

    endangered_group.add_to(endangered_map)
    folium.LayerControl(collapsed=False).add_to(endangered_map)

    st_folium(endangered_map, width=1200, height=600, key="endangered_map")

    # --- Legend ---
    legend_html = "".join(
        f"""
        <span style="display:inline-flex; align-items:center; margin-right:18px; font-size:14px; color:#334155;">
            <span style="display:inline-block; width:12px; height:12px; border-radius:50%;
                         background-color:{severity_colors[status]}; margin-right:6px;"></span>
            {status}
        </span>
        """
        for status in severity_order
    )
    st.markdown(
        f"""
        <div style="background-color:#f8fafc; border:1px solid #e2e8f0; border-radius:10px;
                    padding:12px 16px; margin-top:10px;">
            <span style="font-size:12px; font-weight:700; text-transform:uppercase;
                         letter-spacing:0.06em; color:#64748b; margin-right:14px;">Legend</span>
            {legend_html}
        </div>
        """,
        unsafe_allow_html=True
    )

    # --- Endangered language statistics ---
    st.divider()
    st.markdown("#### Endangered Language Statistics")

    st.metric("Endangered Languages Displayed", len(endangered_languages))

    if len(endangered_languages) > 0:
        severity_counts = (
            endangered_languages["Endangerment_Status"]
            .value_counts()
            .reindex(severity_order)
            .dropna()
            .reset_index()
        )
        severity_counts.columns = ["Endangerment_Status", "Count"]

        fig_severity = px.bar(
            severity_counts,
            x="Endangerment_Status",
            y="Count",
            title="Endangered Languages by Severity",
            template=chart_template,
            color="Endangerment_Status",
            color_discrete_map=severity_colors,
            category_orders={"Endangerment_Status": severity_order}
        )
        fig_severity.update_layout(
            title_font_size=18,
            showlegend=False,
            margin=dict(t=60, b=20, l=20, r=20),
            xaxis_title="",
            yaxis_title="Number of Languages"
        )
        st.plotly_chart(fig_severity, use_container_width=True)


# ===============================
# CULTURAL MAP TAB
# ===============================

if current_page == "Cultural Map":

    st.subheader("Cultural Map of Pakistan")
    st.caption(
        "Historical Sufi poets today, with room to grow — future updates can add "
        "shrines, festivals, forts, and other cultural sites as new categories."
    )

    poet_map = folium.Map(
        location=[30.3753, 69.3451],
        zoom_start=5,
        tiles="CartoDB positron"
    )

    add_pakistan_boundary(poet_map)

    # Color assigned per category so future categories (shrines, festivals, etc.)
    # automatically get their own consistent color without code changes.
    category_palette = ["#7c3aed", "#0891b2", "#ea580c", "#16a34a", "#db2777", "#0f172a"]
    poet_categories = sorted(poets["Category"].dropna().unique()) if "Category" in poets.columns else ["Sufi Poet"]
    culture_colors = {cat: category_palette[i % len(category_palette)] for i, cat in enumerate(poet_categories)}

    poet_group = folium.FeatureGroup(name="Cultural Sites")

    for _, row in poets.iterrows():

        category = row.get("Category", "Sufi Poet") if "Category" in poets.columns else "Sufi Poet"
        marker_color = culture_colors.get(category, "#7c3aed")
        image_url = row.get("Image_URL", "") if "Image_URL" in poets.columns else ""
        has_image = isinstance(image_url, str) and image_url.strip() != ""

        image_html = (
            f'<img src="{image_url}" style="width:100%; max-height:160px; object-fit:cover; '
            f'border-radius:8px; margin-bottom:8px;">'
            if has_image else ""
        )

        popup = f"""
        <div style="font-family: -apple-system, Segoe UI, Roboto, sans-serif; min-width:220px;">
            {image_html}
            <h4 style="margin-bottom:6px; color:#0f172a;">{row['Name']}</h4>
            <b>Category:</b> {category}<br>
            <b>Period:</b> {row['Birth']} - {row['Death']}<br>
            <b>Language:</b> {row['Language']}<br>
            <b>Region:</b> {row['Region']}<br>
            <b>Sufi Order:</b> {row['Sufi_Order']}<br>
            <b>Famous Work:</b> {row['Famous_Work']}<br><br>
            <span style="color:#475569;">{row['Description']}</span>
        </div>
        """

        if has_image:
            # Circular photo marker when an image URL is provided.
            icon_html = f"""
            <div style="width:38px; height:38px; border-radius:50%; overflow:hidden;
                        border:3px solid {marker_color}; box-shadow:0 1px 4px rgba(0,0,0,0.3);">
                <img src="{image_url}" style="width:100%; height:100%; object-fit:cover;">
            </div>
            """
            folium.Marker(
                location=[row["Latitude"], row["Longitude"]],
                popup=folium.Popup(popup, max_width=350),
                tooltip=row["Name"],
                icon=folium.DivIcon(html=icon_html, icon_size=(38, 38), icon_anchor=(19, 19))
            ).add_to(poet_group)
        else:
            folium.CircleMarker(
                location=[row["Latitude"], row["Longitude"]],
                radius=9,
                color=marker_color,
                fill=True,
                fill_color=marker_color,
                fill_opacity=0.85,
                popup=folium.Popup(popup, max_width=350),
                tooltip=row["Name"]
            ).add_to(poet_group)

    poet_group.add_to(poet_map)
    folium.LayerControl(collapsed=False).add_to(poet_map)

    st_folium(poet_map, width=1200, height=600, key="poet_map")

    # --- Legend ---
    legend_items_html = "".join(
        f"""
        <span style="display:inline-flex; align-items:center; margin-right:18px; font-size:14px; color:#334155;">
            <span style="display:inline-block; width:12px; height:12px; border-radius:50%;
                         background-color:{culture_colors[cat]}; margin-right:6px;"></span>
            {cat}
        </span>
        """
        for cat in poet_categories
    )
    st.markdown(
        f"""
        <div style="background-color:#f8fafc; border:1px solid #e2e8f0; border-radius:10px;
                    padding:12px 16px; margin-top:10px;">
            <span style="font-size:12px; font-weight:700; text-transform:uppercase;
                         letter-spacing:0.06em; color:#64748b; margin-right:14px;">Legend</span>
            {legend_items_html}
        </div>
        """,
        unsafe_allow_html=True
    )
    st.caption(
        "Markers show as a colored circle by default, or a circular photo when an "
        "Image_URL is provided in `data/cultural_sites.csv`."
    )

    # --- Cultural site statistics ---
    st.divider()
    st.markdown("#### Cultural Site Statistics")

    st.metric("Cultural Sites Displayed", len(poets))

    if len(poets) > 0:
        fig2 = px.bar(
            poets,
            x="Language",
            title="Cultural Sites by Language",
            template=chart_template,
            color="Language",
            color_discrete_sequence=color_sequence
        )
        fig2.update_layout(
            title_font_size=18,
            showlegend=False,
            margin=dict(t=60, b=20, l=20, r=20),
            xaxis_title="",
            yaxis_title="Number of Poets"
        )
        st.plotly_chart(fig2, use_container_width=True)


# -------------------------------
# FOOTER
# -------------------------------

st.divider()
st.caption("Pakistan Cultural & Linguistic Atlas | Digital Humanities Project")
