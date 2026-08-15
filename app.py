import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
import os


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Digital Language Map",
    page_icon="🌐",
    layout="wide"
)


# ============================================================
# CUSTOM STYLING
# ============================================================

st.markdown(
    """
    <style>

    /* --------------------------------------------------------
       Overall page
    -------------------------------------------------------- */
    .main {
        background-color: #fafafa;
    }

    /* --------------------------------------------------------
       Main title
    -------------------------------------------------------- */
    h1 {
        font-weight: 800 !important;
        letter-spacing: -0.5px;
        color: #0f172a !important;
    }

    /* --------------------------------------------------------
       Sidebar
    -------------------------------------------------------- */
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
        margin-bottom: 10px !important;
    }

    section[data-testid="stSidebar"] hr {
        border-color: #e2e8f0;
    }

    section[data-testid="stSidebar"] .stTextInput input {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
    }

    /* --------------------------------------------------------
       Sidebar navigation radio buttons
    -------------------------------------------------------- */
    section[data-testid="stSidebar"] div[role="radiogroup"] {
        gap: 4px;
    }

    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        border-radius: 8px;
        padding: 8px 10px;
        transition: background-color 0.2s ease;
    }

    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background-color: #e2e8f0;
    }

    /* --------------------------------------------------------
       Sidebar section headers
    -------------------------------------------------------- */
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

    /* --------------------------------------------------------
       Metric cards
    -------------------------------------------------------- */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 16px 18px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }

    div[data-testid="stMetricLabel"] {
        font-weight: 600;
        color: #64748b;
    }

    div[data-testid="stMetricValue"] {
        color: #0f172a;
    }

    /* --------------------------------------------------------
       Section headers
    -------------------------------------------------------- */
    h2 {
        color: #0f172a !important;
        font-weight: 700 !important;
        margin-top: 10px;
    }

    h3 {
        color: #0f172a !important;
    }

    /* --------------------------------------------------------
       Pills
    -------------------------------------------------------- */
    div[data-testid="stPills"] button {
        border-radius: 999px !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# TITLE
# ============================================================

st.title("🌐 Digital Language Map")


# ============================================================
# REQUIRED DATA COLUMNS
# ============================================================

REQUIRED_LANGUAGE_COLS = [
    "Language",
    "Category",
    "Family",
    "Province",
    "Speakers",
    "Script",
    "Endangerment_Status",
    "Description",
    "Latitude",
    "Longitude"
]

REQUIRED_POET_COLS = [
    "Name",
    "Birth",
    "Death",
    "Language",
    "Region",
    "Sufi_Order",
    "Famous_Work",
    "Description",
    "Latitude",
    "Longitude"
]


# ============================================================
# HELPER FUNCTIONS — DATA
# ============================================================

def normalize_columns(df):
    """
    Strip whitespace from column names.
    """
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def check_required_columns(df, required, file_label):
    """
    Check that all required columns exist.
    """
    missing = [c for c in required if c not in df.columns]

    if missing:
        st.error(
            f"❌ **{file_label} is missing required column(s): "
            f"{', '.join(missing)}**\n\n"
            f"Columns found in the file: {list(df.columns)}\n\n"
            "Please check your CSV header row for typos, extra spaces, "
            "or a different delimiter."
        )
        st.stop()


@st.cache_data
def load_data():

    base_path = os.path.dirname(__file__)

    language_file = os.path.join(
        base_path,
        "data",
        "languages.csv"
    )

    poet_file = os.path.join(
        base_path,
        "data",
        "cultural_sites.csv"
    )

    if not os.path.exists(language_file):
        st.error(f"❌ File not found: {language_file}")
        st.stop()

    if not os.path.exists(poet_file):
        st.error(f"❌ File not found: {poet_file}")
        st.stop()

    languages = pd.read_csv(
        language_file,
        encoding="utf-8-sig"
    )

    poets = pd.read_csv(
        poet_file,
        encoding="utf-8-sig"
    )

    languages = normalize_columns(languages)
    poets = normalize_columns(poets)

    return languages, poets


@st.cache_data
def load_provinces_geojson():

    base_path = os.path.dirname(__file__)

    province_file = os.path.join(
        base_path,
        "data",
        "pakistan_provinces.geojson"
    )

    if not os.path.exists(province_file):
        return None

    with open(
        province_file,
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


def match_provinces(province_text, all_province_names):
    """
    Match free-text province values from languages.csv
    to actual polygon province names.
    """

    if not isinstance(province_text, str):
        return []

    text = province_text.lower()

    if "all pakistan" in text:
        return list(all_province_names)

    matches = [
        name
        for name in all_province_names
        if name.lower() in text
    ]

    return matches


@st.cache_data
def load_kashmir_boundary():

    base_path = os.path.dirname(__file__)

    kashmir_file = os.path.join(
        base_path,
        "data",
        "kashmir_disputed_region.geojson"
    )

    if not os.path.exists(kashmir_file):
        return None

    with open(
        kashmir_file,
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


@st.cache_data
def load_districts_geojson():

    base_path = os.path.dirname(__file__)

    district_file = os.path.join(
        base_path,
        "data",
        "pakistan_districts.geojson"
    )

    if not os.path.exists(district_file):
        return None

    with open(
        district_file,
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


@st.cache_data
def load_census_divisions():

    base_path = os.path.dirname(__file__)

    census_file = os.path.join(
        base_path,
        "data",
        "census_divisions_2017.csv"
    )

    if not os.path.exists(census_file):
        return None

    return pd.read_csv(census_file)


@st.cache_data
def load_national_census():

    base_path = os.path.dirname(__file__)

    national_file = os.path.join(
        base_path,
        "data",
        "national_census_2017.json"
    )

    if not os.path.exists(national_file):
        return None

    with open(
        national_file,
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


@st.cache_data
def load_pakistan_boundary():
    """
    Fetch Pakistan national boundary polygon.
    """

    url = (
        "https://raw.githubusercontent.com/"
        "datasets/geo-countries/main/data/countries.geojson"
    )

    try:

        response = requests.get(
            url,
            timeout=15
        )

        response.raise_for_status()

        world = response.json()

    except Exception:
        return None

    pakistan_feature = next(
        (
            f
            for f in world["features"]
            if f["properties"].get("name") == "Pakistan"
        ),
        None
    )

    if pakistan_feature is None:
        return None

    return {
        "type": "FeatureCollection",
        "features": [pakistan_feature]
    }


# ============================================================
# LOAD DATA
# ============================================================

languages, poets = load_data()

check_required_columns(
    languages,
    REQUIRED_LANGUAGE_COLS,
    "languages.csv"
)

check_required_columns(
    poets,
    REQUIRED_POET_COLS,
    "cultural_sites.csv"
)


# ============================================================
# NUMERIC CONVERSIONS
# ============================================================

languages["Speakers"] = pd.to_numeric(
    languages["Speakers"],
    errors="coerce"
).fillna(0)

languages["Latitude"] = pd.to_numeric(
    languages["Latitude"],
    errors="coerce"
)

languages["Longitude"] = pd.to_numeric(
    languages["Longitude"],
    errors="coerce"
)

poets["Latitude"] = pd.to_numeric(
    poets["Latitude"],
    errors="coerce"
)

poets["Longitude"] = pd.to_numeric(
    poets["Longitude"],
    errors="coerce"
)


# ============================================================
# REMOVE INVALID COORDINATES
# ============================================================

languages = languages.dropna(
    subset=["Latitude", "Longitude"]
)

poets = poets.dropna(
    subset=["Latitude", "Longitude"]
)


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

TAB_NAMES = [
    "Overview",
    "Provinces",
    "Districts",
    "Mother Tongue Speakers",
    "All Languages",
    "Endangered Languages",
    "Cultural Map"
]

TAB_ICONS = {
    "Overview": "🗺️",
    "Provinces": "🏛️",
    "Districts": "📍",
    "Mother Tongue Speakers": "🗣️",
    "All Languages": "🌐",
    "Endangered Languages": "⚠️",
    "Cultural Map": "🕌"
}


st.sidebar.markdown(
    "## Explore Atlas"
)

st.sidebar.markdown(
    '<div class="sidebar-section">Navigate</div>',
    unsafe_allow_html=True
)

selected_page = st.sidebar.radio(
    "Select a section",
    TAB_NAMES,
    format_func=lambda x: f"{TAB_ICONS.get(x, '')}  {x}",
    label_visibility="collapsed"
)

st.sidebar.markdown("---")

st.sidebar.caption(
    "Pakistan Cultural & Linguistic Atlas"
)


# ============================================================
# ENDANGERED LANGUAGES
# ============================================================

endangered_languages = languages[
    languages["Category"] == "Endangered"
].copy()

languages = languages[
    languages["Category"] != "Endangered"
].copy()


# ============================================================
# SHARED CONFIGURATION
# ============================================================

language_colors = {
    "National": "green",
    "Regional": "blue",
    "Endangered": "red"
}


severity_colors = {
    "Vulnerable": "#fbbf24",
    "Definitely Endangered": "#fb923c",
    "Severely Endangered": "#ef4444",
    "Critically Endangered": "#7f1d1d"
}


severity_order = [
    "Vulnerable",
    "Definitely Endangered",
    "Severely Endangered",
    "Critically Endangered"
]


chart_template = "plotly_white"

color_sequence = px.colors.qualitative.Set2


pakistan_boundary = load_pakistan_boundary()

kashmir_boundary = load_kashmir_boundary()


# ============================================================
# CENSUS LANGUAGE MAP
# ============================================================

CENSUS_LANGUAGE_MAP = {
    "Urdu": "URDU",
    "Punjabi": "PUNJABI",
    "Sindhi": "SINDHI",
    "Pashto": "PUSHTO",
    "Balochi": "BALOCHI",
    "Kashmiri": "KASHMIRI",
    "Saraiki": "SARAIKI",
    "Hindko": "HINDKO",
    "Brahui": "BRAHVI"
}


CENSUS_LANG_LABELS = {
    "URDU": "Urdu",
    "PUNJABI": "Punjabi",
    "SINDHI": "Sindhi",
    "PUSHTO": "Pashto",
    "BALOCHI": "Balochi",
    "KASHMIRI": "Kashmiri",
    "SARAIKI": "Saraiki",
    "HINDKO": "Hindko",
    "BRAHVI": "Brahui",
    "OTHERS": "Other Languages"
}


# ============================================================
# MAP BOUNDARY FUNCTION
# ============================================================

def add_pakistan_boundary(map_obj):
    """
    Add Pakistan and Kashmir using exactly the same visual styling.

    Kashmir is deliberately NOT given a different color, opacity,
    or outline. This makes it visually continuous with the rest
    of the map rather than appearing detached.
    """

    base_style = {
        "fillColor": "#2ca25f",
        "color": "#006d2c",
        "weight": 3,
        "fillOpacity": 0.18
    }

    base_highlight = {
        "fillColor": "#2ca25f",
        "color": "#006d2c",
        "fillOpacity": 0.18,
        "weight": 3
    }

    # Pakistan boundary
    if pakistan_boundary:

        folium.GeoJson(
            pakistan_boundary,
            name="Pakistan",
            style_function=lambda feature: base_style,
            highlight_function=lambda feature: base_highlight
        ).add_to(map_obj)

    # Kashmir boundary
    # Same fill + same outline + same opacity
    if kashmir_boundary:

        folium.GeoJson(
            kashmir_boundary,
            name="Kashmir",
            style_function=lambda feature: base_style,
            highlight_function=lambda feature: base_highlight
        ).add_to(map_obj)


# ============================================================
# KASHMIR OUTLINE FOR PLOTLY MAPS
# ============================================================

def add_kashmir_outline_to_choropleth(fig):
    """
    Add Kashmir boundary using the same outline color as the
    Pakistan map boundary.
    """

    if not kashmir_boundary:
        return fig

    try:

        geometry = kashmir_boundary["features"][0]["geometry"]

        coordinates = geometry["coordinates"]

        # Handle Polygon
        if geometry["type"] == "Polygon":

            rings = coordinates

            for ring in rings:

                lons = [pt[0] for pt in ring]
                lats = [pt[1] for pt in ring]

                fig.add_trace(
                    go.Scattergeo(
                        lon=lons,
                        lat=lats,
                        mode="lines",
                        line=dict(
                            color="#006d2c",
                            width=2
                        ),
                        hoverinfo="skip",
                        showlegend=False
                    )
                )

        # Handle MultiPolygon
        elif geometry["type"] == "MultiPolygon":

            for polygon in coordinates:

                for ring in polygon:

                    lons = [pt[0] for pt in ring]
                    lats = [pt[1] for pt in ring]

                    fig.add_trace(
                        go.Scattergeo(
                            lon=lons,
                            lat=lats,
                            mode="lines",
                            line=dict(
                                color="#006d2c",
                                width=2
                            ),
                            hoverinfo="skip",
                            showlegend=False
                        )
                    )

    except Exception:
        pass

    return fig


# ============================================================
# FULL LANGUAGE DATA
# ============================================================

full_languages, _ = load_data()

full_languages["Speakers"] = pd.to_numeric(
    full_languages["Speakers"],
    errors="coerce"
).fillna(0)

national_census = load_national_census()


# ============================================================
# ============================================================
# OVERVIEW
# ============================================================
# ============================================================

if selected_page == "Overview":

    st.subheader("Pakistan at a Glance")

    # --------------------------------------------------------
    # Overview Map
    # --------------------------------------------------------

    overview_map = folium.Map(
        location=[30.3753, 69.3451],
        zoom_start=5,
        tiles="CartoDB positron"
    )

    add_pakistan_boundary(
        overview_map
    )

    folium.LayerControl(
        collapsed=False
    ).add_to(overview_map)

    st_folium(
        overview_map,
        width=1200,
        height=550,
        key="overview_map"
    )

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    st.divider()

    m1, m2, m3, m4, m5 = st.columns(5)

    with m1:

        st.metric(
            "Languages Tracked",
            len(full_languages)
        )

    with m2:

        st.metric(
            "Total Speakers",
            f"{int(full_languages['Speakers'].sum()):,}"
        )

    with m3:

        st.metric(
            "Provinces",
            full_languages["Province"].nunique()
        )

    with m4:

        districts_geojson_preview = (
            load_districts_geojson()
        )

        district_count = (
            len(districts_geojson_preview["features"])
            if districts_geojson_preview
            else 0
        )

        st.metric(
            "Districts Mapped",
            district_count
        )

    with m5:

        st.metric(
            "Cultural Sites",
            len(poets)
        )


# ============================================================
# ============================================================
# PROVINCES
# ============================================================
# ============================================================

elif selected_page == "Provinces":

    st.subheader(
        "Language Distribution by Province"
    )

    provinces_geojson = load_provinces_geojson()

    if provinces_geojson is None:

        st.info(
            "Province boundary file not found. "
            "Add `data/pakistan_provinces.geojson` "
            "to your repo to enable this view."
        )

    else:

        all_province_names = sorted(
            {
                feat["properties"]["Province"]
                for feat in provinces_geojson["features"]
            }
        )

        lang_col, stat_col = st.columns([2, 1])

        with lang_col:

            selected_language = st.selectbox(
                "Language",
                sorted(
                    full_languages[
                        "Language"
                    ].dropna().unique()
                ),
                index=0,
                key="province_lang_select"
            )

        lang_row = full_languages[
            full_languages["Language"]
            == selected_language
        ].iloc[0]

        matched_provinces = match_provinces(
            lang_row["Province"],
            all_province_names
        )

        speaker_count = int(
            lang_row["Speakers"]
        )

        with stat_col:

            st.metric(
                f"{selected_language} — Mother Tongue Speakers",
                f"{speaker_count:,}"
            )

        province_values = pd.DataFrame(
            {
                "Province": all_province_names,
                "Speakers": [
                    speaker_count
                    if p in matched_provinces
                    else 0
                    for p in all_province_names
                ]
            }
        )

        fig_choropleth = px.choropleth(
            province_values,
            geojson=provinces_geojson,
            locations="Province",
            featureidkey="properties.Province",
            color="Speakers",
            color_continuous_scale=[
                [0.0, "#e5e7eb"],
                [1.0, "#08519c"]
            ],
            range_color=[
                0,
                max(speaker_count, 1)
            ],
            template="plotly_white",
            hover_name="Province",
            hover_data={
                "Speakers": ":,"
            }
        )

        fig_choropleth.update_traces(
            marker_line_color="#94a3b8",
            marker_line_width=1
        )

        fig_choropleth = (
            add_kashmir_outline_to_choropleth(
                fig_choropleth
            )
        )

        fig_choropleth.update_geos(
            fitbounds="locations",
            visible=False
        )

        fig_choropleth.update_layout(
            margin=dict(
                t=10,
                b=10,
                l=10,
                r=10
            ),
            coloraxis_colorbar_title="Speakers"
        )

        st.plotly_chart(
            fig_choropleth,
            use_container_width=True
        )

        st.caption(
            f"Currently showing: **{selected_language}**"
        )


# ============================================================
# ============================================================
# DISTRICTS
# ============================================================
# ============================================================

elif selected_page == "Districts":

    st.subheader(
        "District Map — Official 2017 Census"
    )

    st.caption(
        "Pakistan Bureau of Statistics 2017 census, "
        "mother-tongue data by administrative division."
    )

    districts_geojson = load_districts_geojson()

    census_divisions = load_census_divisions()

    if (
        districts_geojson is None
        or census_divisions is None
    ):

        st.info(
            "District boundary or census data file not found. "
            "Add `data/pakistan_districts.geojson` and "
            "`data/census_divisions_2017.csv` to your repo "
            "to enable this view."
        )

    else:

        census_col, census_stat_col = st.columns(
            [2, 1]
        )

        with census_col:

            selected_census_lang = st.selectbox(
                "Language (2017 Census)",
                list(
                    CENSUS_LANG_LABELS.values()
                ),
                index=0,
                key="district_lang_select"
            )

        census_col_name = [
            k
            for k, v
            in CENSUS_LANG_LABELS.items()
            if v == selected_census_lang
        ][0]

        pct_col = census_col_name + "_PCT"

        national_pct = None

        if national_census:

            national_pct = (
                national_census
                .get("languages", {})
                .get(census_col_name, {})
                .get("pct")
            )

        with census_stat_col:

            if national_pct is not None:

                st.metric(
                    f"{selected_census_lang} — % of Pakistan",
                    f"{national_pct}%"
                )

        district_rows = []

        for feat in districts_geojson["features"]:

            props = feat["properties"]

            division = props["Division"]

            match = census_divisions[
                census_divisions["Division"]
                == division
            ]

            pct = (
                float(match.iloc[0][pct_col])
                if len(match) > 0
                else None
            )

            district_rows.append(
                {
                    "District": props["District"],
                    "Division": division,
                    "Percentage": pct
                }
            )

        district_df = pd.DataFrame(
            district_rows
        )

        max_pct = district_df[
            "Percentage"
        ].max()

        district_df[
            "Percentage_display"
        ] = district_df[
            "Percentage"
        ].fillna(0)

        # ----------------------------------------------------
        # District search
        # ----------------------------------------------------

        search_district = st.selectbox(
            "Jump to a district (optional)",
            [
                "— none —"
            ]
            + sorted(
                district_df[
                    "District"
                ].unique()
            ),
            index=0,
            key="district_search"
        )

        if search_district != "— none —":

            row = district_df[
                district_df["District"]
                == search_district
            ].iloc[0]

            pct_display = (
                f"{row['Percentage']:.2f}%"
                if pd.notna(row["Percentage"])
                else "No data"
            )

            st.info(
                f"**{search_district}** "
                f"(Division: {row['Division']}) — "
                f"{selected_census_lang}: "
                f"{pct_display}"
            )

        # ----------------------------------------------------
        # District choropleth
        # ----------------------------------------------------

        fig_district = px.choropleth(
            district_df,
            geojson=districts_geojson,
            locations="District",
            featureidkey="properties.District",
            color="Percentage_display",
            color_continuous_scale=[
                [0.0, "#e5e7eb"],
                [1.0, "#08519c"]
            ],
            range_color=[
                0,
                max(max_pct, 1)
            ],
            template="plotly_white",
            hover_name="District",
            hover_data={
                "Division": True,
                "Percentage_display": ":.2f"
            }
        )

        fig_district.update_traces(
            marker_line_color="#94a3b8",
            marker_line_width=0.6
        )

        fig_district = (
            add_kashmir_outline_to_choropleth(
                fig_district
            )
        )

        fig_district.update_geos(
            fitbounds="locations",
            visible=False
        )

        fig_district.update_layout(
            margin=dict(
                t=10,
                b=10,
                l=10,
                r=10
            ),
            coloraxis_colorbar_title="% Speakers"
        )

        st.plotly_chart(
            fig_district,
            use_container_width=True
        )


# ============================================================
# ============================================================
# MOTHER TONGUE SPEAKERS
# ============================================================
# ============================================================

elif selected_page == "Mother Tongue Speakers":

    st.subheader(
        "Mother Tongue Speakers — 2017 Census"
    )

    if national_census is None:

        st.info(
            "Census data file not found. "
            "Add `data/national_census_2017.json` "
            "to your repo to enable this view."
        )

    else:

        selected_speaker_lang = st.selectbox(
            "Language",
            list(
                CENSUS_LANG_LABELS.values()
            ),
            index=0,
            key="speakers_lang_select"
        )

        speaker_col_name = [
            k
            for k, v
            in CENSUS_LANG_LABELS.items()
            if v == selected_speaker_lang
        ][0]

        lang_data = (
            national_census
            .get("languages", {})
            .get(speaker_col_name, {})
        )

        lang_pct = lang_data.get(
            "pct",
            0
        )

        lang_count = lang_data.get(
            "count",
            0
        )

        # ----------------------------------------------------
        # Ranking
        # ----------------------------------------------------

        rank_rows = [
            {
                "Language": CENSUS_LANG_LABELS[k],
                "Percentage": v["pct"],
                "Count": v["count"]
            }
            for k, v
            in national_census[
                "languages"
            ].items()
            if k != "OTHERS"
        ]

        rank_df = pd.DataFrame(
            rank_rows
        ).sort_values(
            "Percentage",
            ascending=False
        ).reset_index(
            drop=True
        )

        rank_df.index += 1

        rank_position = rank_df[
            rank_df["Language"]
            == selected_speaker_lang
        ].index

        if (
            len(rank_position) > 0
            and selected_speaker_lang
            != "Other Languages"
        ):

            rank_label = (
                f"#{rank_position[0]} most-spoken"
            )

        else:

            rank_label = "—"

        # ----------------------------------------------------
        # Metrics
        # ----------------------------------------------------

        s1, s2, s3 = st.columns(3)

        with s1:

            st.metric(
                f"{selected_speaker_lang} — Speakers",
                f"{lang_count:,}"
            )

        with s2:

            st.metric(
                "% of Pakistan",
                f"{lang_pct}%"
            )

        with s3:

            st.metric(
                "National Rank",
                rank_label
            )

        st.divider()

        st.markdown(
            "##### Comparison with other census-tracked languages"
        )

        # ----------------------------------------------------
        # Ranking chart
        # ----------------------------------------------------

        fig_rank = px.bar(
            rank_df,
            x="Language",
            y="Percentage",
            template=chart_template,
            color="Language",
            color_discrete_sequence=color_sequence,
            hover_data={
                "Count": ":,"
            }
        )

        fig_rank.update_layout(
            showlegend=False,
            margin=dict(
                t=20,
                b=20,
                l=20,
                r=20
            ),
            xaxis_title="",
            yaxis_title="% of Pakistan's Population"
        )

        fig_rank.update_traces(
            marker_line_width=0
        )

        for trace in fig_rank.data:

            if trace.name == selected_speaker_lang:

                trace.marker.line.width = 3

                trace.marker.line.color = (
                    "#0f172a"
                )

        st.plotly_chart(
            fig_rank,
            use_container_width=True
        )

        # ----------------------------------------------------
        # Ranking table
        # ----------------------------------------------------

        st.dataframe(
            rank_df.rename(
                columns={
                    "Percentage":
                        "% of Pakistan",
                    "Count":
                        "Speaker Count"
                }
            ),
            use_container_width=True
        )


# ============================================================
# ============================================================
# ALL LANGUAGES
# ============================================================
# ============================================================

elif selected_page == "All Languages":

    st.subheader(
        "All Languages of Pakistan"
    )

    st.caption(
        "Click any point on the map for that language's details."
    )

    language_map = folium.Map(
        location=[30.3753, 69.3451],
        zoom_start=5,
        tiles="CartoDB positron"
    )

    add_pakistan_boundary(
        language_map
    )

    language_group = folium.FeatureGroup(
        name="Languages"
    )

    for _, row in languages.iterrows():

        census_line = ""

        census_col = CENSUS_LANGUAGE_MAP.get(
            row["Language"]
        )

        if national_census and census_col:

            pct = (
                national_census
                .get("languages", {})
                .get(census_col, {})
                .get("pct")
            )

            if pct is not None:

                census_line = (
                    f"<b>2017 Census:</b> "
                    f"{pct}% of Pakistan's population<br>"
                )

        popup = f"""
        <div style="
            font-family:-apple-system,
            BlinkMacSystemFont,
            'Segoe UI',
            Roboto,
            sans-serif;
            min-width:220px;
        ">

            <h4 style="
                margin-bottom:6px;
                color:#0f172a;
            ">
                {row['Language']}
            </h4>

            <b>Category:</b>
            {row['Category']}<br>

            <b>Family:</b>
            {row['Family']}<br>

            <b>Province:</b>
            {row['Province']}<br>

            <b>Speakers:</b>
            {int(row['Speakers']):,}<br>

            {census_line}

            <b>Script:</b>
            {row['Script']}<br>

            <b>Status:</b>
            {row['Endangerment_Status']}<br>

            <p style="
                margin-top:8px;
                color:#475569;
            ">
                {row['Description']}
            </p>

        </div>
        """

        folium.CircleMarker(
            location=[
                row["Latitude"],
                row["Longitude"]
            ],
            radius=max(
                5,
                min(
                    18,
                    row["Speakers"] / 5000000
                )
            ),
            color=language_colors.get(
                row["Category"],
                "purple"
            ),
            fill=True,
            fill_color=language_colors.get(
                row["Category"],
                "purple"
            ),
            fill_opacity=0.7,
            popup=folium.Popup(
                popup,
                max_width=350
            ),
            tooltip=row["Language"]
        ).add_to(language_group)

    language_group.add_to(
        language_map
    )

    folium.LayerControl(
        collapsed=False
    ).add_to(language_map)

    st_folium(
        language_map,
        width=1200,
        height=600,
        key="language_map"
    )

    # --------------------------------------------------------
    # Language statistics
    # --------------------------------------------------------

    st.divider()

    st.markdown(
        "#### Language Statistics"
    )

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Languages Displayed",
            len(languages)
        )

    with col2:

        total_speakers = (
            languages["Speakers"].sum()
        )

        st.metric(
            "Total Speakers",
            f"{int(total_speakers):,}"
        )


# ============================================================
# ============================================================
# ENDANGERED LANGUAGES
# ============================================================
# ============================================================

elif selected_page == "Endangered Languages":

    st.subheader(
        "Endangered Languages of Pakistan"
    )

    st.caption(
        "Languages classified as endangered, shown with "
        "severity-based coloring."
    )

    endangered_map = folium.Map(
        location=[30.3753, 69.3451],
        zoom_start=5,
        tiles="CartoDB positron"
    )

    add_pakistan_boundary(
        endangered_map
    )

    endangered_group = folium.FeatureGroup(
        name="Endangered Languages"
    )

    for _, row in endangered_languages.iterrows():

        marker_color = severity_colors.get(
            row["Endangerment_Status"],
            "#7f1d1d"
        )

        popup = f"""
        <div style="
            font-family:-apple-system,
            BlinkMacSystemFont,
            'Segoe UI',
            Roboto,
            sans-serif;
            min-width:220px;
        ">

            <h4 style="
                margin-bottom:6px;
                color:#0f172a;
            ">
                {row['Language']}
            </h4>

            <b>Family:</b>
            {row['Family']}<br>

            <b>Province:</b>
            {row['Province']}<br>

            <b>Speakers:</b>
            {int(row['Speakers']):,}<br>

            <b>Script:</b>
            {row['Script']}<br>

            <b>Endangerment Status:</b>
            {row['Endangerment_Status']}<br>

            <p style="
                margin-top:8px;
                color:#475569;
            ">
                {row['Description']}
            </p>

        </div>
        """

        folium.CircleMarker(
            location=[
                row["Latitude"],
                row["Longitude"]
            ],
            radius=(
                max(
                    5,
                    min(
                        16,
                        row["Speakers"] / 20000
                    )
                )
                if row["Speakers"] > 0
                else 5
            ),
            color=marker_color,
            fill=True,
            fill_color=marker_color,
            fill_opacity=0.8,
            popup=folium.Popup(
                popup,
                max_width=350
            )
        ).add_to(
            endangered_group
        )

    endangered_group.add_to(
        endangered_map
    )

    folium.LayerControl(
        collapsed=False
    ).add_to(endangered_map)

    st_folium(
        endangered_map,
        width=1200,
        height=600,
        key="endangered_map"
    )

    # --------------------------------------------------------
    # Legend
    # --------------------------------------------------------

    legend_html = "".join(
        f"""
        <span style="
            display:inline-flex;
            align-items:center;
            margin-right:18px;
            font-size:14px;
            color:#334155;
        ">

            <span style="
                display:inline-block;
                width:12px;
                height:12px;
                border-radius:50%;
                background-color:{severity_colors[status]};
                margin-right:6px;
            "></span>

            {status}

        </span>
        """
        for status in severity_order
    )

    st.markdown(
        f"""
        <div style="
            background-color:#f8fafc;
            border:1px solid #e2e8f0;
            border-radius:10px;
            padding:12px 16px;
            margin-top:10px;
        ">

            <span style="
                font-size:12px;
                font-weight:700;
                text-transform:uppercase;
                letter-spacing:0.06em;
                color:#64748b;
                margin-right:14px;
            ">
                Legend
            </span>

            {legend_html}

        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    st.divider()

    st.markdown(
        "#### Endangered Language Statistics"
    )

    st.metric(
        "Endangered Languages Displayed",
        len(endangered_languages)
    )

    if len(endangered_languages) > 0:

        severity_counts = (
            endangered_languages[
                "Endangerment_Status"
            ]
            .value_counts()
            .reindex(
                severity_order
            )
            .dropna()
            .reset_index()
        )

        severity_counts.columns = [
            "Endangerment_Status",
            "Count"
        ]

        fig_severity = px.bar(
            severity_counts,
            x="Endangerment_Status",
            y="Count",
            title="Endangered Languages by Severity",
            template=chart_template,
            color="Endangerment_Status",
            color_discrete_map=severity_colors,
            category_orders={
                "Endangerment_Status":
                    severity_order
            }
        )

        fig_severity.update_layout(
            title_font_size=18,
            showlegend=False,
            margin=dict(
                t=60,
                b=20,
                l=20,
                r=20
            ),
            xaxis_title="",
            yaxis_title="Number of Languages"
        )

        st.plotly_chart(
            fig_severity,
            use_container_width=True
        )


# ============================================================
# ============================================================
# CULTURAL MAP
# ============================================================
# ============================================================

elif selected_page == "Cultural Map":

    st.subheader(
        "Cultural Map of Pakistan"
    )

    st.caption(
        "Historical Sufi poets and cultural locations."
    )

    poet_map = folium.Map(
        location=[30.3753, 69.3451],
        zoom_start=5,
        tiles="CartoDB positron"
    )

    add_pakistan_boundary(
        poet_map
    )

    # --------------------------------------------------------
    # Cultural categories
    # --------------------------------------------------------

    category_palette = [
        "#7c3aed",
        "#0891b2",
        "#ea580c",
        "#16a34a",
        "#db2777",
        "#0f172a"
    ]

    if "Category" in poets.columns:

        poet_categories = sorted(
            poets[
                "Category"
            ].dropna().unique()
        )

    else:

        poet_categories = [
            "Sufi Poet"
        ]

    culture_colors = {
        cat:
            category_palette[
                i % len(category_palette)
            ]
        for i, cat
        in enumerate(poet_categories)
    }

    poet_group = folium.FeatureGroup(
        name="Cultural Sites"
    )

    # --------------------------------------------------------
    # Add cultural markers
    # --------------------------------------------------------

    for _, row in poets.iterrows():

        if "Category" in poets.columns:

            category = row.get(
                "Category",
                "Sufi Poet"
            )

        else:

            category = "Sufi Poet"

        marker_color = culture_colors.get(
            category,
            "#7c3aed"
        )

        if "Image_URL" in poets.columns:

            image_url = row.get(
                "Image_URL",
                ""
            )

        else:

            image_url = ""

        has_image = (
            isinstance(image_url, str)
            and image_url.strip() != ""
        )

        if has_image:

            image_html = (
                f'<img src="{image_url}" '
                f'style="width:100%; '
                f'max-height:160px; '
                f'object-fit:cover; '
                f'border-radius:8px; '
                f'margin-bottom:8px;">'
            )

        else:

            image_html = ""

        popup = f"""
        <div style="
            font-family:-apple-system,
            BlinkMacSystemFont,
            'Segoe UI',
            Roboto,
            sans-serif;
            min-width:220px;
        ">

            {image_html}

            <h4 style="
                margin-bottom:6px;
                color:#0f172a;
            ">
                {row['Name']}
            </h4>

            <b>Category:</b>
            {category}<br>

            <b>Period:</b>
            {row['Birth']} - {row['Death']}<br>

            <b>Language:</b>
            {row['Language']}<br>

            <b>Region:</b>
            {row['Region']}<br>

            <b>Sufi Order:</b>
            {row['Sufi_Order']}<br>

            <b>Famous Work:</b>
            {row['Famous_Work']}<br><br>

            <span style="
                color:#475569;
            ">
                {row['Description']}
            </span>

        </div>
        """

        # ----------------------------------------------------
        # Image marker
        # ----------------------------------------------------

        if has_image:

            icon_html = f"""
            <div style="
                width:38px;
                height:38px;
                border-radius:50%;
                overflow:hidden;
                border:3px solid {marker_color};
                box-shadow:0 1px 4px rgba(0,0,0,0.3);
            ">

                <img src="{image_url}"
                     style="
                        width:100%;
                        height:100%;
                        object-fit:cover;
                     ">

            </div>
            """

            folium.Marker(
                location=[
                    row["Latitude"],
                    row["Longitude"]
                ],
                popup=folium.Popup(
                    popup,
                    max_width=350
                ),
                tooltip=row["Name"],
                icon=folium.DivIcon(
                    html=icon_html,
                    icon_size=(38, 38),
                    icon_anchor=(19, 19)
                )
            ).add_to(
                poet_group
            )

        # ----------------------------------------------------
        # Standard marker
        # ----------------------------------------------------

        else:

            folium.CircleMarker(
                location=[
                    row["Latitude"],
                    row["Longitude"]
                ],
                radius=9,
                color=marker_color,
                fill=True,
                fill_color=marker_color,
                fill_opacity=0.85,
                popup=folium.Popup(
                    popup,
                    max_width=350
                ),
                tooltip=row["Name"]
            ).add_to(
                poet_group
            )

    poet_group.add_to(
        poet_map
    )

    folium.LayerControl(
        collapsed=False
    ).add_to(poet_map)

    st_folium(
        poet_map,
        width=1200,
        height=600,
        key="poet_map"
    )

    # --------------------------------------------------------
    # Cultural legend
    # --------------------------------------------------------

    legend_items_html = "".join(
        f"""
        <span style="
            display:inline-flex;
            align-items:center;
            margin-right:18px;
            font-size:14px;
            color:#334155;
        ">

            <span style="
                display:inline-block;
                width:12px;
                height:12px;
                border-radius:50%;
                background-color:{culture_colors[cat]};
                margin-right:6px;
            "></span>

            {cat}

        </span>
        """
        for cat in poet_categories
    )

    st.markdown(
        f"""
        <div style="
            background-color:#f8fafc;
            border:1px solid #e2e8f0;
            border-radius:10px;
            padding:12px 16px;
            margin-top:10px;
        ">

            <span style="
                font-size:12px;
                font-weight:700;
                text-transform:uppercase;
                letter-spacing:0.06em;
                color:#64748b;
                margin-right:14px;
            ">
                Legend
            </span>

            {legend_items_html}

        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # Cultural statistics
    # --------------------------------------------------------

    st.divider()

    st.markdown(
        "#### Cultural Site Statistics"
    )

    st.metric(
        "Cultural Sites Displayed",
        len(poets)
    )

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
            margin=dict(
                t=60,
                b=20,
                l=20,
                r=20
            ),
            xaxis_title="",
            yaxis_title="Number of Poets"
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Pakistan Cultural & Linguistic Atlas | Digital Humanities Project"
)
