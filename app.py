import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
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
    <style>
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

    /* Intro markdown block */
    .intro-box {
        background: linear-gradient(135deg, #f0fdf4 0%, #eff6ff 100%);
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 22px 26px;
        margin-bottom: 22px;
    }
    .intro-box p {
        font-size: 16px;
        color: #334155;
        margin-bottom: 10px;
    }
    .intro-box ul {
        margin: 0;
        padding-left: 20px;
    }
    .intro-box li {
        color: #475569;
        font-size: 15px;
        margin-bottom: 4px;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }
    section[data-testid="stSidebar"] * {
        color: #334155 !important;
    }
    section[data-testid="stSidebar"] h2 {
        color: #0f172a !important;
        font-weight: 700 !important;
        font-size: 20px !important;
        letter-spacing: -0.3px;
        padding-bottom: 10px;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 4px !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: #e2e8f0;
    }
    section[data-testid="stSidebar"] .stTextInput input {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
    }

    /* Sidebar section headers */
    .sidebar-section {
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #64748b !important;
        margin-top: 20px;
        margin-bottom: 8px;
        padding-bottom: 4px;
        border-bottom: 1px solid #e2e8f0;
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

st.markdown(
    """
    <div class="intro-box">
    <p>Explore Pakistan's linguistic diversity and Sufi heritage through an interactive map.</p>
    <p style="margin-bottom:6px;"><strong>This digital atlas connects:</strong></p>
    <ul>
        <li>Languages</li>
        <li>Speaker populations</li>
        <li>Endangerment status</li>
        <li>Historical Sufi poets</li>
        <li>Cultural geography</li>
    </ul>
    </div>
    """,
    unsafe_allow_html=True
)


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
    poet_file = os.path.join(base_path, "data", "sufi_poets.csv")

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
check_required_columns(poets, REQUIRED_POET_COLS, "sufi_poets.csv")

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
# SIDEBAR FILTERS
# -------------------------------

st.sidebar.markdown("## Explore Atlas")

st.sidebar.markdown("<div class='sidebar-section'>Language Category</div>", unsafe_allow_html=True)
main_categories = ["National", "Regional"]
available_categories = [c for c in main_categories if c in languages["Category"].unique()]
category_filter = st.sidebar.pills(
    "Language Category",
    available_categories,
    selection_mode="multi",
    default=available_categories,
    label_visibility="collapsed"
)

# Endangered-category languages live on their own dedicated tab now.
endangered_languages = languages[languages["Category"] == "Endangered"].copy()
languages = languages[languages["Category"] != "Endangered"]

languages = languages[languages["Category"].isin(category_filter)]

st.sidebar.markdown("<div class='sidebar-section'>Endangerment Severity</div>", unsafe_allow_html=True)
all_severities = sorted(endangered_languages["Endangerment_Status"].dropna().unique())
severity_filter = st.sidebar.pills(
    "Endangerment Severity",
    all_severities,
    selection_mode="multi",
    default=all_severities,
    label_visibility="collapsed"
)

endangered_languages = endangered_languages[
    endangered_languages["Endangerment_Status"].isin(severity_filter)
]

st.sidebar.markdown("<div class='sidebar-section'>Search Language</div>", unsafe_allow_html=True)
search_language = st.sidebar.text_input(
    "Search Language",
    placeholder="e.g. Punjabi, Balochi...",
    label_visibility="collapsed"
)

if search_language:
    languages = languages[
        languages["Language"].str.contains(search_language, case=False, na=False)
    ]

st.sidebar.markdown("<div class='sidebar-section'>Search Sufi Poets</div>", unsafe_allow_html=True)
search_poet = st.sidebar.text_input(
    "Search Sufi Poet",
    placeholder="e.g. Bulleh Shah, Rehman Baba...",
    label_visibility="collapsed"
)

if search_poet:
    poets = poets[
        poets["Name"].str.contains(search_poet, case=False, na=False)
    ]

st.sidebar.markdown("<div class='sidebar-section'>Search Endangered Languages</div>", unsafe_allow_html=True)
search_endangered = st.sidebar.text_input(
    "Search Endangered Language",
    placeholder="e.g. Kalasha, Domaaki...",
    label_visibility="collapsed"
)

if search_endangered:
    endangered_languages = endangered_languages[
        endangered_languages["Language"].str.contains(search_endangered, case=False, na=False)
    ]

st.sidebar.caption(
    "Filters above apply to their matching tab — Languages, Sufi Poets, "
    "and Endangered Languages are shown separately."
)

st.sidebar.markdown("---")
st.sidebar.caption("Pakistan Cultural & Linguistic Atlas")


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
# TABS: LANGUAGES vs SUFI POETS
# -------------------------------

lang_tab, endangered_tab, poet_tab = st.tabs(
    ["Languages Map", "Endangered Languages", "Sufi Poets Map"]
)


# ===============================
# LANGUAGES TAB
# ===============================

with lang_tab:

    st.subheader("Languages of Pakistan")

    language_map = folium.Map(
        location=[30.3753, 69.3451],
        zoom_start=5,
        tiles="CartoDB positron"
    )

    add_pakistan_boundary(language_map)

    national_census = load_national_census()

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
            popup=folium.Popup(popup, max_width=350)
        ).add_to(language_group)

    language_group.add_to(language_map)
    folium.LayerControl(collapsed=False).add_to(language_map)

    st_folium(language_map, width=1200, height=600, key="language_map")

    # --- Language distribution choropleth ---
    st.divider()
    st.markdown("#### Language Distribution by Province")
    st.caption(
        "Select a language to see which provinces it is spoken in. "
        "Shading reflects that language's total speaker count wherever it appears "
        "(province-level data — not a per-district breakdown)."
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

        # Use the full (unfiltered) language list for this selector so it isn't
        # affected by the sidebar filters above.
        full_languages, _ = load_data()
        full_languages["Speakers"] = pd.to_numeric(full_languages["Speakers"], errors="coerce").fillna(0)

        lang_col, stat_col = st.columns([2, 1])

        with lang_col:
            selected_language = st.selectbox(
                "Language",
                sorted(full_languages["Language"].dropna().unique()),
                index=0
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
            template="plotly_white"
        )
        fig_choropleth.update_traces(marker_line_color="#94a3b8", marker_line_width=1)
        fig_choropleth.update_geos(fitbounds="locations", visible=False)
        fig_choropleth.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            coloraxis_colorbar_title="Speakers"
        )

        st.plotly_chart(fig_choropleth, use_container_width=True)

    # --- District-level census choropleth (2017 PBS data) ---
    st.divider()
    st.markdown("#### District Map — Official 2017 Census")
    st.caption(
        "Pakistan Bureau of Statistics 2017 census, mother-tongue data by administrative "
        "division. This is the finest resolution PBS publicly released for language — "
        "so districts belonging to the same division share one color. "
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
        census_lang_labels = {
            "URDU": "Urdu", "PUNJABI": "Punjabi", "SINDHI": "Sindhi",
            "PUSHTO": "Pashto", "BALOCHI": "Balochi", "KASHMIRI": "Kashmiri",
            "SARAIKI": "Saraiki", "HINDKO": "Hindko", "BRAHVI": "Brahui",
            "OTHERS": "Other Languages"
        }

        census_col, census_stat_col = st.columns([2, 1])

        with census_col:
            selected_census_lang = st.selectbox(
                "Language (2017 Census)",
                list(census_lang_labels.values()),
                index=0,
                key="census_district_lang"
            )

        census_col_name = [k for k, v in census_lang_labels.items() if v == selected_census_lang][0]
        pct_col = census_col_name + "_PCT"

        national_pct = None
        national_census = load_national_census()
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

        fig_district = px.choropleth(
            district_df,
            geojson=districts_geojson,
            locations="District",
            featureidkey="properties.District",
            color="Percentage_display",
            color_continuous_scale=[[0.0, "#e5e7eb"], [1.0, "#08519c"]],
            range_color=[0, max(max_pct, 1)],
            template="plotly_white",
            hover_data={"Division": True, "Percentage_display": ":.2f"}
        )
        fig_district.update_traces(marker_line_color="#94a3b8", marker_line_width=0.6)
        fig_district.update_geos(fitbounds="locations", visible=False)
        fig_district.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            coloraxis_colorbar_title="% Speakers"
        )

        st.plotly_chart(fig_district, use_container_width=True)


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

with endangered_tab:

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
# SUFI POETS TAB
# ===============================

with poet_tab:

    st.subheader("Sufi Poets of Pakistan")

    poet_map = folium.Map(
        location=[30.3753, 69.3451],
        zoom_start=5,
        tiles="CartoDB positron"
    )

    add_pakistan_boundary(poet_map)

    poet_group = folium.FeatureGroup(name="Sufi Poets")

    for _, row in poets.iterrows():

        popup = f"""
        <div style="font-family: -apple-system, Segoe UI, Roboto, sans-serif; min-width:220px;">
            <h4 style="margin-bottom:6px; color:#0f172a;">{row['Name']}</h4>
            <b>Period:</b> {row['Birth']} - {row['Death']}<br>
            <b>Language:</b> {row['Language']}<br>
            <b>Region:</b> {row['Region']}<br>
            <b>Sufi Order:</b> {row['Sufi_Order']}<br>
            <b>Famous Work:</b> {row['Famous_Work']}<br><br>
            <span style="color:#475569;">{row['Description']}</span>
        </div>
        """

        folium.Marker(
            location=[row["Latitude"], row["Longitude"]],
            popup=folium.Popup(popup, max_width=350),
            tooltip=row["Name"],
            icon=folium.Icon(icon="star", color="purple")
        ).add_to(poet_group)

    poet_group.add_to(poet_map)
    folium.LayerControl(collapsed=False).add_to(poet_map)

    st_folium(poet_map, width=1200, height=600, key="poet_map")

    # --- Poet statistics ---
    st.divider()
    st.markdown("#### Sufi Poet Statistics")

    st.metric("Sufi Poets Displayed", len(poets))

    if len(poets) > 0:
        fig2 = px.bar(
            poets,
            x="Language",
            title="Sufi Poets by Language",
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
