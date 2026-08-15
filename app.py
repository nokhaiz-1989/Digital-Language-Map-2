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
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM STYLING
# ============================================================

st.markdown(
    """
    <style>

    /* ========================================================
       GENERAL PAGE
       ======================================================== */

    .main {
        background-color: #ffffff;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    h1 {
        color: #0f172a !important;
        font-weight: 800 !important;
        letter-spacing: -0.6px;
    }

    h2 {
        color: #0f172a !important;
        font-weight: 700 !important;
    }

    h3 {
        color: #0f172a !important;
        font-weight: 700 !important;
    }


    /* ========================================================
       SIDEBAR
       ======================================================== */

    section[data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }

    section[data-testid="stSidebar"] > div {
        padding-top: 1.2rem;
    }

    section[data-testid="stSidebar"] h2 {
        color: #0f172a !important;
        font-size: 20px !important;
        font-weight: 700 !important;
        letter-spacing: -0.3px;
        border-bottom: 1px solid #e2e8f0;
        padding-bottom: 12px;
        margin-bottom: 12px !important;
    }

    section[data-testid="stSidebar"] hr {
        border-color: #e2e8f0;
    }


    /* Navigation buttons */

    section[data-testid="stSidebar"] .stButton {
        margin-bottom: 4px;
    }

    section[data-testid="stSidebar"] .stButton > button {
        width: 100%;
        min-height: 44px;
        border-radius: 8px;
        border: none;
        background-color: transparent;
        color: #334155;
        font-size: 15px;
        font-weight: 500;
        text-align: left;
        justify-content: flex-start;
        padding-left: 12px;
        transition: all 0.15s ease;
    }

    section[data-testid="stSidebar"] .stButton > button:hover {
        background-color: #e7eef7;
        color: #173b68;
        border: none;
    }


    /* ========================================================
       METRIC CARDS
       ======================================================== */

    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 15px 18px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
    }

    div[data-testid="stMetricLabel"] {
        color: #64748b;
        font-weight: 600;
    }

    div[data-testid="stMetricValue"] {
        color: #0f172a;
        font-weight: 700;
    }


    /* ========================================================
       OVERVIEW INFORMATION CARDS
       ======================================================== */

    .info-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        height: 100%;
    }

    .info-card-title {
        color: #334155;
        font-size: 13px;
        font-weight: 600;
        margin-bottom: 5px;
    }

    .info-card-value {
        color: #0f172a;
        font-size: 25px;
        font-weight: 750;
    }

    .info-card-small {
        color: #64748b;
        font-size: 12px;
        margin-top: 3px;
    }


    /* ========================================================
       PROVINCE LEGEND
       ======================================================== */

    .province-legend {
        display: flex;
        flex-wrap: wrap;
        gap: 10px 22px;
        padding: 13px 16px;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        margin-top: 10px;
    }

    .legend-item {
        display: flex;
        align-items: center;
        color: #334155;
        font-size: 14px;
        font-weight: 500;
    }

    .legend-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 7px;
    }


    /* ========================================================
       POPULATION TABLE
       ======================================================== */

    .population-note {
        color: #64748b;
        font-size: 13px;
        margin-bottom: 8px;
    }


    /* ========================================================
       FOOTER
       ======================================================== */

    .footer {
        color: #64748b;
        font-size: 12px;
        text-align: center;
        padding-top: 8px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# PAGE TITLE
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
# DATA FUNCTIONS
# ============================================================

def normalize_columns(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def check_required_columns(df, required, file_label):

    missing = [
        c for c in required
        if c not in df.columns
    ]

    if missing:

        st.error(
            f"❌ **{file_label} is missing required column(s): "
            f"{', '.join(missing)}**\n\n"
            f"Columns found: {list(df.columns)}"
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

        st.error(
            f"❌ File not found: {language_file}"
        )

        st.stop()

    if not os.path.exists(poet_file):

        st.error(
            f"❌ File not found: {poet_file}"
        )

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

    file_path = os.path.join(
        base_path,
        "data",
        "pakistan_provinces.geojson"
    )

    if not os.path.exists(file_path):
        return None

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


@st.cache_data
def load_kashmir_boundary():

    base_path = os.path.dirname(__file__)

    file_path = os.path.join(
        base_path,
        "data",
        "kashmir_disputed_region.geojson"
    )

    if not os.path.exists(file_path):
        return None

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


@st.cache_data
def load_districts_geojson():

    base_path = os.path.dirname(__file__)

    file_path = os.path.join(
        base_path,
        "data",
        "pakistan_districts.geojson"
    )

    if not os.path.exists(file_path):
        return None

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


@st.cache_data
def load_census_divisions():

    base_path = os.path.dirname(__file__)

    file_path = os.path.join(
        base_path,
        "data",
        "census_divisions_2017.csv"
    )

    if not os.path.exists(file_path):
        return None

    return pd.read_csv(file_path)


@st.cache_data
def load_national_census():

    base_path = os.path.dirname(__file__)

    file_path = os.path.join(
        base_path,
        "data",
        "national_census_2017.json"
    )

    if not os.path.exists(file_path):
        return None

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


@st.cache_data
def load_pakistan_boundary():

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
            feature
            for feature in world["features"]
            if feature["properties"].get("name")
            == "Pakistan"
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
# CLEAN NUMERIC DATA
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

languages = languages.dropna(
    subset=["Latitude", "Longitude"]
)

poets = poets.dropna(
    subset=["Latitude", "Longitude"]
)


# ============================================================
# FULL LANGUAGE DATA
# ============================================================

full_languages = languages.copy()


# ============================================================
# NATIONAL CENSUS
# ============================================================

national_census = load_national_census()


# ============================================================
# CENSUS LANGUAGE LABELS
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
# ENDANGERED LANGUAGES
# ============================================================

endangered_languages = languages[
    languages["Category"] == "Endangered"
].copy()

languages = languages[
    languages["Category"] != "Endangered"
].copy()


# ============================================================
# SHARED COLORS
# ============================================================

severity_colors = {

    "Vulnerable":
        "#fbbf24",

    "Definitely Endangered":
        "#fb923c",

    "Severely Endangered":
        "#ef4444",

    "Critically Endangered":
        "#7f1d1d"
}

severity_order = [
    "Vulnerable",
    "Definitely Endangered",
    "Severely Endangered",
    "Critically Endangered"
]


language_colors = {

    "National":
        "#2563eb",

    "Regional":
        "#0891b2",

    "Endangered":
        "#dc2626"
}


chart_template = "plotly_white"

color_sequence = (
    px.colors.qualitative.Set2
)


# ============================================================
# MAP DATA
# ============================================================

pakistan_boundary = load_pakistan_boundary()

kashmir_boundary = load_kashmir_boundary()


# ============================================================
# KASHMIR VISUAL STYLE
# ============================================================
#
# IMPORTANT:
# Kashmir is deliberately NOT green.
#
# It uses:
#   - same light-blue family as the map
#   - white boundary
#   - no green outline
#   - no separate visual emphasis
#
# This makes it visually integrated with Pakistan.
# ============================================================

KASHMIR_FILL = "#d9e7f5"
KASHMIR_LINE = "#ffffff"


# ============================================================
# FOLIUM BASE MAP
# ============================================================

def add_pakistan_boundary(map_obj):

    pakistan_style = {
        "fillColor": "#d9e7f5",
        "color": "#94a3b8",
        "weight": 1.5,
        "fillOpacity": 0.85
    }

    pakistan_highlight = {
        "fillColor": "#d9e7f5",
        "color": "#64748b",
        "weight": 2,
        "fillOpacity": 0.9
    }

    if pakistan_boundary:

        folium.GeoJson(
            pakistan_boundary,
            name="Pakistan",
            style_function=lambda feature:
                pakistan_style,
            highlight_function=lambda feature:
                pakistan_highlight
        ).add_to(map_obj)

    # Kashmir receives the same light-blue visual treatment.
    if kashmir_boundary:

        kashmir_style = {
            "fillColor": KASHMIR_FILL,
            "color": KASHMIR_LINE,
            "weight": 2,
            "fillOpacity": 0.85
        }

        kashmir_highlight = {
            "fillColor": KASHMIR_FILL,
            "color": "#ffffff",
            "weight": 2.5,
            "fillOpacity": 0.9
        }

        folium.GeoJson(
            kashmir_boundary,
            name="Kashmir Region",
            style_function=lambda feature:
                kashmir_style,
            highlight_function=lambda feature:
                kashmir_highlight
        ).add_to(map_obj)


# ============================================================
# GET COORDINATE RINGS
# ============================================================

def get_geometry_rings(geometry):

    geometry_type = geometry.get(
        "type"
    )

    coordinates = geometry.get(
        "coordinates",
        []
    )

    rings = []

    if geometry_type == "Polygon":

        for ring in coordinates:
            rings.append(ring)

    elif geometry_type == "MultiPolygon":

        for polygon in coordinates:

            for ring in polygon:
                rings.append(ring)

    return rings


# ============================================================
# ADD KASHMIR TO PLOTLY
# ============================================================

def add_kashmir_to_plotly(fig):

    if not kashmir_boundary:
        return fig

    for feature in kashmir_boundary.get(
        "features",
        []
    ):

        geometry = feature.get(
            "geometry",
            {}
        )

        rings = get_geometry_rings(
            geometry
        )

        for ring in rings:

            if not ring:
                continue

            lons = [
                point[0]
                for point in ring
            ]

            lats = [
                point[1]
                for point in ring
            ]

            fig.add_trace(
                go.Scattergeo(

                    lon=lons,

                    lat=lats,

                    mode="lines",

                    fill="toself",

                    fillcolor=KASHMIR_FILL,

                    line=dict(
                        color=KASHMIR_LINE,
                        width=2
                    ),

                    hoverinfo="skip",

                    showlegend=False
                )
            )

    return fig


# ============================================================
# PLOTLY MAP VIEW
# ============================================================

def style_pakistan_plotly_map(fig):

    fig.update_geos(

        visible=False,

        projection_type="mercator",

        center=dict(
            lat=30.5,
            lon=69.5
        ),

        projection_scale=4.7
    )

    fig.update_layout(

        margin=dict(
            t=10,
            b=10,
            l=10,
            r=10
        ),

        paper_bgcolor="#ffffff",

        plot_bgcolor="#ffffff"
    )

    return fig


# ============================================================
# PROVINCE MATCHING
# ============================================================

def normalize_name(name):

    if not isinstance(name, str):
        return ""

    return (
        name
        .lower()
        .strip()
        .replace("_", " ")
        .replace("-", " ")
    )


def match_provinces(
    province_text,
    all_province_names
):

    if not isinstance(
        province_text,
        str
    ):

        return []

    text = normalize_name(
        province_text
    )

    if "all pakistan" in text:

        return list(
            all_province_names
        )

    matches = []

    for name in all_province_names:

        normalized = normalize_name(
            name
        )

        if normalized in text:

            matches.append(
                name
            )

    return matches


# ============================================================
# PROVINCE DISPLAY COLORS
# ============================================================

PROVINCE_COLORS = {

    "Punjab":
        "#5B8DB8",

    "Sindh":
        "#7EA6C6",

    "Khyber Pakhtunkhwa":
        "#8DB7A5",

    "Balochistan":
        "#C7A66B",

    "Islamabad":
        "#A58BB8"
}


PROVINCE_ALIASES = {

    "punjab":
        "Punjab",

    "sindh":
        "Sindh",

    "khyber pakhtunkhwa":
        "Khyber Pakhtunkhwa",

    "khyber pakhtunkhwa province":
        "Khyber Pakhtunkhwa",

    "kpk":
        "Khyber Pakhtunkhwa",

    "balochistan":
        "Balochistan",

    "islamabad":
        "Islamabad",

    "islamabad capital territory":
        "Islamabad"
}


# ============================================================
# OFFICIAL 2023 POPULATION DATA
# ============================================================
#
# Pakistan Bureau of Statistics
# Population & Housing Census 2023
#
# Five major census areas:
# Punjab
# Sindh
# Khyber Pakhtunkhwa
# Balochistan
# Islamabad Capital Territory
# ============================================================

CENSUS_2023 = {

    "Punjab": {

        "population":
            127_688_922,

        "male":
            65_448_376,

        "female":
            62_226_589,

        "transgender":
            13_957
    },

    "Sindh": {

        "population":
            55_696_147,

        "male":
            29_014_424,

        "female":
            26_677_501,

        "transgender":
            4_222
    },

    "Khyber Pakhtunkhwa": {

        "population":
            40_856_097,

        "male":
            20_845_747,

        "female":
            20_009_233,

        "transgender":
            1_117
    },

    "Balochistan": {

        "population":
            14_894_402,

        "male":
            7_768_166,

        "female":
            7_125_471,

        "transgender":
            765
    },

    "Islamabad": {

        "population":
            2_363_863,

        "male":
            1_247_693,

        "female":
            1_115_900,

        "transgender":
            270
    }
}


PAKISTAN_2023 = {

    "population":
        241_499_431,

    "male":
        124_324_406,

    "female":
        117_154_694,

    "transgender":
        20_331
}


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

NAVIGATION = {

    "Overview":
        ":material/map:",

    "Provinces":
        ":material/account_balance:",

    "Districts":
        ":material/location_on:",

    "Mother Tongue Speakers":
        ":material/groups:",

    "All Languages":
        ":material/public:",

    "Endangered Languages":
        ":material/warning:",

    "Cultural Map":
        ":material/mosque:"
}


if "selected_page" not in st.session_state:

    st.session_state.selected_page = (
        "Overview"
    )


def set_page(page):

    st.session_state.selected_page = page


st.sidebar.markdown(
    "## Explore Atlas"
)

for page, icon in NAVIGATION.items():

    is_selected = (
        st.session_state.selected_page
        == page
    )

    button_type = (
        "primary"
        if is_selected
        else "secondary"
    )

    if st.sidebar.button(
        page,
        icon=icon,
        type=button_type,
        width="stretch",
        key=f"nav_{page}"
    ):

        set_page(page)
        st.rerun()


st.sidebar.markdown("---")

st.sidebar.caption(
    "Pakistan Cultural & Linguistic Atlas"
)


selected_page = (
    st.session_state.selected_page
)


# ============================================================
# ============================================================
# OVERVIEW
# ============================================================
# ============================================================

if selected_page == "Overview":

    st.subheader(
        "Pakistan at a Glance"
    )


    # ========================================================
    # TOP NATIONAL STATISTICS
    # ========================================================

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.metric(
            "Population",
            f"{PAKISTAN_2023['population']:,}"
        )

    with c2:

        st.metric(
            "Male",
            f"{PAKISTAN_2023['male']:,}"
        )

    with c3:

        st.metric(
            "Female",
            f"{PAKISTAN_2023['female']:,}"
        )

    with c4:

        st.metric(
            "Transgender",
            f"{PAKISTAN_2023['transgender']:,}"
        )


    st.markdown("")


    # ========================================================
    # LANGUAGE SUMMARY
    # ========================================================

    language_count = (
        full_languages[
            "Language"
        ]
        .dropna()
        .nunique()
    )

    language_speakers = int(
        full_languages[
            "Speakers"
        ].sum()
    )

    l1, l2 = st.columns(2)

    with l1:

        st.markdown(
            f"""
            <div class="info-card">

                <div class="info-card-title">
                    Total Languages in Atlas
                </div>

                <div class="info-card-value">
                    {language_count:,}
                </div>

                <div class="info-card-small">
                    Languages represented in the
                    Digital Language Map dataset
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    with l2:

        st.markdown(
            f"""
            <div class="info-card">

                <div class="info-card-title">
                    Speakers Represented in Atlas
                </div>

                <div class="info-card-value">
                    {language_speakers:,}
                </div>

                <div class="info-card-small">
                    Sum of speaker figures recorded
                    in the language dataset
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


    st.markdown("")


    # ========================================================
    # OVERVIEW MAP
    # ========================================================

    st.markdown(
        "### Administrative Regions"
    )

    st.caption(
        "Five major census areas are shown in distinct "
        "muted colours. Kashmir is visually integrated "
        "with the surrounding map using the same light-blue treatment."
    )


    provinces_geojson = (
        load_provinces_geojson()
    )


    if provinces_geojson is None:

        st.info(
            "Province boundary file not found. "
            "Add `data/pakistan_provinces.geojson` "
            "to display the administrative map."
        )

    else:

        province_features = (
            provinces_geojson[
                "features"
            ]
        )

        province_rows = []

        for feature in province_features:

            name = feature[
                "properties"
            ].get(
                "Province",
                ""
            )

            normalized = normalize_name(
                name
            )

            canonical = (
                PROVINCE_ALIASES.get(
                    normalized,
                    name
                )
            )

            province_rows.append(
                {
                    "Province": name,
                    "Region": canonical,
                    "Value": 1
                }
            )

        province_df = pd.DataFrame(
            province_rows
        )


        fig_overview = px.choropleth(

            province_df,

            geojson=provinces_geojson,

            locations="Province",

            featureidkey="properties.Province",

            color="Region",

            color_discrete_map={
                key: PROVINCE_COLORS[key]
                for key in PROVINCE_COLORS
            },

            hover_name="Region",

            hover_data={
                "Province": False,
                "Region": True,
                "Value": False
            }
        )


        fig_overview.update_traces(

            marker_line_color="#ffffff",

            marker_line_width=1.8
        )


        fig_overview = (
            add_kashmir_to_plotly(
                fig_overview
            )
        )


        # ----------------------------------------------------
        # Province labels
        # ----------------------------------------------------

        province_label_coordinates = {

            "Punjab":
                (30.8, 72.8),

            "Sindh":
                (25.8, 68.5),

            "Khyber Pakhtunkhwa":
                (34.2, 71.4),

            "Balochistan":
                (28.0, 65.0),

            "Islamabad":
                (33.72, 73.05)
        }


        label_lats = []
        label_lons = []
        label_text = []


        for name, coords in (
            province_label_coordinates.items()
        ):

            label_lats.append(
                coords[0]
            )

            label_lons.append(
                coords[1]
            )

            label_text.append(
                name
            )


        fig_overview.add_trace(

            go.Scattergeo(

                lat=label_lats,

                lon=label_lons,

                text=label_text,

                mode="text",

                textfont=dict(
                    size=11,
                    color="#334155"
                ),

                hoverinfo="skip",

                showlegend=False
            )
        )


        fig_overview = (
            style_pakistan_plotly_map(
                fig_overview
            )
        )


        fig_overview.update_layout(
            showlegend=False
        )


        st.plotly_chart(
            fig_overview,
            use_container_width=True
        )


        # ----------------------------------------------------
        # Legend
        # ----------------------------------------------------

        legend_html = ""

        for name, colour in (
            PROVINCE_COLORS.items()
        ):

            legend_html += f"""
                <div class="legend-item">

                    <span
                        class="legend-dot"
                        style="background:{colour};">
                    </span>

                    {name}

                </div>
            """


        st.markdown(
            f"""
            <div class="province-legend">

                {legend_html}

            </div>
            """,
            unsafe_allow_html=True
        )


    # ========================================================
    # POPULATION DETAILS
    # ========================================================

    st.markdown("")

    st.markdown(
        "### Population by Region"
    )

    st.markdown(
        """
        <div class="population-note">
            Population and sex-disaggregated figures are from
            Pakistan's 2023 Population & Housing Census.
        </div>
        """,
        unsafe_allow_html=True
    )


    population_table = pd.DataFrame(

        [

            {
                "Region": name,

                "Population":
                    values["population"],

                "Male":
                    values["male"],

                "Female":
                    values["female"],

                "Transgender":
                    values["transgender"]
            }

            for name, values
            in CENSUS_2023.items()
        ]
    )


    display_table = (
        population_table.copy()
    )

    for column in [
        "Population",
        "Male",
        "Female",
        "Transgender"
    ]:

        display_table[column] = (
            display_table[column]
            .map(
                lambda x:
                    f"{x:,}"
            )
        )


    st.dataframe(
        display_table,
        hide_index=True,
        use_container_width=True
    )


    # ========================================================
    # NATIONAL LANGUAGE SNAPSHOT
    # ========================================================

    st.markdown("")

    st.markdown(
        "### Linguistic Snapshot"
    )

    q1, q2, q3 = st.columns(3)

    with q1:

        st.metric(
            "Languages in Atlas",
            f"{language_count:,}"
        )

    with q2:

        st.metric(
            "Language Families",
            f"{full_languages['Family'].dropna().nunique():,}"
        )

    with q3:

        st.metric(
            "Cultural Sites",
            f"{len(poets):,}"
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

    provinces_geojson = (
        load_provinces_geojson()
    )


    if provinces_geojson is None:

        st.info(
            "Province boundary file not found. "
            "Add `data/pakistan_provinces.geojson` "
            "to your repo."
        )

    else:

        all_province_names = sorted(
            {
                feature[
                    "properties"
                ]["Province"]

                for feature
                in provinces_geojson[
                    "features"
                ]
            }
        )


        lang_col, stat_col = (
            st.columns([2, 1])
        )


        with lang_col:

            selected_language = (
                st.selectbox(
                    "Language",
                    sorted(
                        full_languages[
                            "Language"
                        ]
                        .dropna()
                        .unique()
                    ),
                    index=0,
                    key="province_language"
                )
            )


        language_rows = (
            full_languages[
                full_languages[
                    "Language"
                ]
                == selected_language
            ]
        )


        if language_rows.empty:

            st.warning(
                "No data found for this language."
            )

        else:

            lang_row = (
                language_rows.iloc[0]
            )

            matched_provinces = (
                match_provinces(
                    lang_row["Province"],
                    all_province_names
                )
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
                    "Province":
                        all_province_names,

                    "Speakers": [

                        speaker_count
                        if province
                        in matched_provinces
                        else 0

                        for province
                        in all_province_names
                    ]
                }
            )


            fig_province = px.choropleth(

                province_values,

                geojson=provinces_geojson,

                locations="Province",

                featureidkey=
                    "properties.Province",

                color="Speakers",

                color_continuous_scale=[
                    [0.0, "#dbe7f5"],
                    [0.35, "#a9c7e4"],
                    [0.7, "#5b93c7"],
                    [1.0, "#175a9c"]
                ],

                range_color=[
                    0,
                    max(
                        speaker_count,
                        1
                    )
                ],

                hover_name="Province",

                hover_data={
                    "Speakers": ":,"
                }
            )


            fig_province.update_traces(

                marker_line_color="#ffffff",

                marker_line_width=1.8
            )


            # IMPORTANT:
            # Kashmir is filled light blue and
            # outlined in white.
            fig_province = (
                add_kashmir_to_plotly(
                    fig_province
                )
            )


            fig_province = (
                style_pakistan_plotly_map(
                    fig_province
                )
            )


            fig_province.update_layout(

                coloraxis_colorbar=dict(
                    title="Mother Tongue<br>Speakers"
                )
            )


            st.plotly_chart(
                fig_province,
                use_container_width=True
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

    districts_geojson = (
        load_districts_geojson()
    )

    census_divisions = (
        load_census_divisions()
    )


    if (
        districts_geojson is None
        or census_divisions is None
    ):

        st.info(
            "District boundary or census data file "
            "not found. Add the required files inside "
            "`data/`."
        )

    else:

        census_col, stat_col = (
            st.columns([2, 1])
        )


        with census_col:

            selected_census_lang = (
                st.selectbox(
                    "Language (2017 Census)",
                    list(
                        CENSUS_LANG_LABELS.values()
                    ),
                    index=0,
                    key="district_language"
                )
            )


        census_col_name = next(
            key
            for key, value
            in CENSUS_LANG_LABELS.items()
            if value
            == selected_census_lang
        )


        pct_col = (
            census_col_name
            + "_PCT"
        )


        national_pct = None


        if national_census:

            national_pct = (
                national_census
                .get(
                    "languages",
                    {}
                )
                .get(
                    census_col_name,
                    {}
                )
                .get(
                    "pct"
                )
            )


        with stat_col:

            if national_pct is not None:

                st.metric(
                    f"{selected_census_lang} — % of Pakistan",
                    f"{national_pct}%"
                )


        district_rows = []


        for feature in (
            districts_geojson[
                "features"
            ]
        ):

            properties = (
                feature[
                    "properties"
                ]
            )

            district = (
                properties[
                    "District"
                ]
            )

            division = (
                properties[
                    "Division"
                ]
            )


            match = (
                census_divisions[
                    census_divisions[
                        "Division"
                    ]
                    == division
                ]
            )


            if (
                len(match) > 0
                and pct_col
                in match.columns
            ):

                pct = float(
                    match.iloc[0][
                        pct_col
                    ]
                )

            else:

                pct = None


            district_rows.append(

                {
                    "District":
                        district,

                    "Division":
                        division,

                    "Percentage":
                        pct
                }
            )


        district_df = pd.DataFrame(
            district_rows
        )


        max_pct = (
            district_df[
                "Percentage"
            ]
            .max()
        )


        district_df[
            "Percentage_display"
        ] = (
            district_df[
                "Percentage"
            ]
            .fillna(0)
        )


        search_district = (
            st.selectbox(
                "Jump to a district (optional)",
                [
                    "— none —"
                ]
                + sorted(
                    district_df[
                        "District"
                    ]
                    .unique()
                ),
                index=0,
                key="district_search"
            )
        )


        if (
            search_district
            != "— none —"
        ):

            selected_row = (
                district_df[
                    district_df[
                        "District"
                    ]
                    == search_district
                ]
                .iloc[0]
            )


            percentage_text = (

                f"{selected_row['Percentage']:.2f}%"

                if pd.notna(
                    selected_row[
                        "Percentage"
                    ]
                )

                else
                "No data"
            )


            st.info(
                f"**{search_district}** "
                f"({selected_row['Division']}) — "
                f"{selected_census_lang}: "
                f"{percentage_text}"
            )


        fig_district = px.choropleth(

            district_df,

            geojson=districts_geojson,

            locations="District",

            featureidkey=
                "properties.District",

            color=
                "Percentage_display",

            color_continuous_scale=[
                [0.0, "#dbe7f5"],
                [0.35, "#a9c7e4"],
                [0.7, "#5b93c7"],
                [1.0, "#175a9c"]
            ],

            range_color=[
                0,
                max(
                    max_pct,
                    1
                )
            ],

            hover_name="District",

            hover_data={
                "Division": True,
                "Percentage_display":
                    ":.2f"
            }
        )


        fig_district.update_traces(

            marker_line_color="#ffffff",

            marker_line_width=0.9
        )


        # IMPORTANT:
        # Kashmir is filled instead of being
        # shown as a green outline.
        fig_district = (
            add_kashmir_to_plotly(
                fig_district
            )
        )


        fig_district = (
            style_pakistan_plotly_map(
                fig_district
            )
        )


        fig_district.update_layout(

            coloraxis_colorbar=dict(
                title="% Speakers"
            )
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
            "Add `data/national_census_2017.json`."
        )

    else:

        selected_language = (
            st.selectbox(
                "Language",
                list(
                    CENSUS_LANG_LABELS.values()
                ),
                index=0,
                key="speaker_language"
            )
        )


        speaker_key = next(

            key
            for key, value
            in CENSUS_LANG_LABELS.items()

            if value
            == selected_language
        )


        language_data = (
            national_census
            .get(
                "languages",
                {}
            )
            .get(
                speaker_key,
                {}
            )
        )


        speaker_count = (
            language_data.get(
                "count",
                0
            )
        )


        speaker_percentage = (
            language_data.get(
                "pct",
                0
            )
        )


        rank_rows = [

            {
                "Language":
                    CENSUS_LANG_LABELS[
                        key
                    ],

                "Percentage":
                    value.get(
                        "pct",
                        0
                    ),

                "Count":
                    value.get(
                        "count",
                        0
                    )
            }

            for key, value
            in national_census.get(
                "languages",
                {}
            ).items()

            if key != "OTHERS"
        ]


        rank_df = (
            pd.DataFrame(
                rank_rows
            )
            .sort_values(
                "Percentage",
                ascending=False
            )
            .reset_index(
                drop=True
            )
        )


        rank_df.index += 1


        rank_position = (
            rank_df[
                rank_df[
                    "Language"
                ]
                == selected_language
            ]
            .index
        )


        rank_label = (

            f"#{rank_position[0]}"

            if len(
                rank_position
            ) > 0

            else
            "—"
        )


        a, b, c = (
            st.columns(3)
        )


        with a:

            st.metric(
                f"{selected_language} — Speakers",
                f"{speaker_count:,}"
            )


        with b:

            st.metric(
                "% of Pakistan",
                f"{speaker_percentage}%"
            )


        with c:

            st.metric(
                "National Rank",
                rank_label
            )


        st.divider()


        fig_rank = px.bar(

            rank_df,

            x="Language",

            y="Percentage",

            color="Language",

            color_discrete_sequence=
                color_sequence,

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

            yaxis_title=
                "% of Pakistan's Population"
        )


        fig_rank.update_traces(
            marker_line_width=0
        )


        for trace in (
            fig_rank.data
        ):

            if (
                trace.name
                == selected_language
            ):

                trace.marker.line.width = 3

                trace.marker.line.color = (
                    "#0f172a"
                )


        st.plotly_chart(
            fig_rank,
            use_container_width=True
        )


        st.dataframe(

            rank_df.rename(

                columns={
                    "Percentage":
                        "% of Pakistan",

                    "Count":
                        "Speaker Count"
                }
            ),

            hide_index=False,

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

    language_map = folium.Map(

        location=[
            30.3753,
            69.3451
        ],

        zoom_start=5,

        tiles="CartoDB positron"
    )


    add_pakistan_boundary(
        language_map
    )


    language_group = (
        folium.FeatureGroup(
            name="Languages"
        )
    )


    for _, row in (
        languages.iterrows()
    ):

        census_line = ""


        census_key = (
            CENSUS_LANGUAGE_MAP.get(
                row["Language"]
            )
        )


        if (
            national_census
            and census_key
        ):

            pct = (

                national_census
                .get(
                    "languages",
                    {}
                )
                .get(
                    census_key,
                    {}
                )
                .get(
                    "pct"
                )
            )


            if pct is not None:

                census_line = (
                    f"<b>2017 Census:</b> "
                    f"{pct}% of Pakistan's population<br>"
                )


        popup = f"""

        <div style="
            font-family:
            -apple-system,
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


        category_color = (
            language_colors.get(
                row["Category"],
                "#7c3aed"
            )
        )


        folium.CircleMarker(

            location=[
                row["Latitude"],
                row["Longitude"]
            ],

            radius=max(
                5,
                min(
                    18,
                    row["Speakers"]
                    / 5_000_000
                )
            ),

            color=category_color,

            fill=True,

            fill_color=category_color,

            fill_opacity=0.72,

            popup=folium.Popup(
                popup,
                max_width=350
            ),

            tooltip=row[
                "Language"
            ]

        ).add_to(
            language_group
        )


    language_group.add_to(
        language_map
    )


    folium.LayerControl(
        collapsed=False
    ).add_to(
        language_map
    )


    st_folium(

        language_map,

        width=1200,

        height=600,

        key="language_map"
    )


    st.divider()


    x1, x2 = (
        st.columns(2)
    )


    with x1:

        st.metric(
            "Languages Displayed",
            languages[
                "Language"
            ]
            .nunique()
        )


    with x2:

        st.metric(
            "Speakers Represented",
            f"{int(languages['Speakers'].sum()):,}"
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


    endangered_map = folium.Map(

        location=[
            30.3753,
            69.3451
        ],

        zoom_start=5,

        tiles="CartoDB positron"
    )


    add_pakistan_boundary(
        endangered_map
    )


    endangered_group = (
        folium.FeatureGroup(
            name="Endangered Languages"
        )
    )


    for _, row in (
        endangered_languages.iterrows()
    ):

        marker_color = (
            severity_colors.get(
                row[
                    "Endangerment_Status"
                ],
                "#7f1d1d"
            )
        )


        popup = f"""

        <div style="
            font-family:
            -apple-system,
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
                        row["Speakers"]
                        / 20_000
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
    ).add_to(
        endangered_map
    )


    st_folium(

        endangered_map,

        width=1200,

        height=600,

        key="endangered_map"
    )


    # --------------------------------------------------------
    # Legend
    # --------------------------------------------------------

    legend_html = ""


    for status in severity_order:

        legend_html += f"""

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
                background-color:
                    {severity_colors[status]};
                margin-right:6px;
            "></span>

            {status}

        </span>

        """


    st.markdown(

        f"""

        <div style="
            background-color:#f8fafc;
            border:1px solid #e2e8f0;
            border-radius:10px;
            padding:12px 16px;
            margin-top:10px;
        ">

            <strong>
                Legend
            </strong>

            {legend_html}

        </div>

        """,

        unsafe_allow_html=True
    )


    st.divider()


    st.metric(
        "Endangered Languages Displayed",
        len(
            endangered_languages
        )
    )


    if len(
        endangered_languages
    ) > 0:

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

            color=
                "Endangerment_Status",

            color_discrete_map=
                severity_colors,

            category_orders={
                "Endangerment_Status":
                    severity_order
            }
        )


        fig_severity.update_layout(

            showlegend=False,

            margin=dict(
                t=20,
                b=20,
                l=20,
                r=20
            ),

            xaxis_title="",

            yaxis_title=
                "Number of Languages"
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


    poet_map = folium.Map(

        location=[
            30.3753,
            69.3451
        ],

        zoom_start=5,

        tiles="CartoDB positron"
    )


    add_pakistan_boundary(
        poet_map
    )


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
            ]
            .dropna()
            .unique()
        )

    else:

        poet_categories = [
            "Sufi Poet"
        ]


    culture_colors = {

        category:
            category_palette[
                index
                % len(
                    category_palette
                )
            ]

        for index, category
        in enumerate(
            poet_categories
        )
    }


    poet_group = (
        folium.FeatureGroup(
            name="Cultural Sites"
        )
    )


    for _, row in (
        poets.iterrows()
    ):

        category = (

            row.get(
                "Category",
                "Sufi Poet"
            )

            if "Category"
            in poets.columns

            else
            "Sufi Poet"
        )


        marker_color = (
            culture_colors.get(
                category,
                "#7c3aed"
            )
        )


        image_url = (

            row.get(
                "Image_URL",
                ""
            )

            if "Image_URL"
            in poets.columns

            else
            ""
        )


        has_image = (

            isinstance(
                image_url,
                str
            )

            and
            image_url.strip()
            != ""
        )


        image_html = (

            f"""
            <img src="{image_url}"
                 style="
                    width:100%;
                    max-height:160px;
                    object-fit:cover;
                    border-radius:8px;
                    margin-bottom:8px;
                 ">
            """

            if has_image

            else
            ""
        )


        popup = f"""

        <div style="
            font-family:
            -apple-system,
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
            {row['Birth']}
            -
            {row['Death']}<br>

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


        if has_image:

            icon_html = f"""

            <div style="
                width:38px;
                height:38px;
                border-radius:50%;
                overflow:hidden;
                border:3px solid
                    {marker_color};
                box-shadow:
                    0 1px 4px
                    rgba(0,0,0,0.3);
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

                tooltip=row[
                    "Name"
                ],

                icon=folium.DivIcon(

                    html=icon_html,

                    icon_size=(
                        38,
                        38
                    ),

                    icon_anchor=(
                        19,
                        19
                    )
                )

            ).add_to(
                poet_group
            )


        else:

            folium.CircleMarker(

                location=[
                    row["Latitude"],
                    row["Longitude"]
                ],

                radius=9,

                color=marker_color,

                fill=True,

                fill_color=
                    marker_color,

                fill_opacity=0.85,

                popup=folium.Popup(
                    popup,
                    max_width=350
                ),

                tooltip=row[
                    "Name"
                ]

            ).add_to(
                poet_group
            )


    poet_group.add_to(
        poet_map
    )


    folium.LayerControl(
        collapsed=False
    ).add_to(
        poet_map
    )


    st_folium(

        poet_map,

        width=1200,

        height=600,

        key="cultural_map"
    )


    # --------------------------------------------------------
    # Cultural Legend
    # --------------------------------------------------------

    legend_items = ""


    for category in (
        poet_categories
    ):

        legend_items += f"""

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
                background-color:
                    {culture_colors[category]};
                margin-right:6px;
            "></span>

            {category}

        </span>

        """


    st.markdown(

        f"""

        <div style="
            background-color:#f8fafc;
            border:1px solid #e2e8f0;
            border-radius:10px;
            padding:12px 16px;
            margin-top:10px;
        ">

            <strong>
                Legend
            </strong>

            {legend_items}

        </div>

        """,

        unsafe_allow_html=True
    )


    st.divider()


    st.metric(
        "Cultural Sites Displayed",
        len(poets)
    )


    if len(poets) > 0:

        fig_cultural = px.bar(

            poets,

            x="Language",

            color="Language",

            color_discrete_sequence=
                color_sequence
        )


        fig_cultural.update_layout(

            showlegend=False,

            margin=dict(
                t=20,
                b=20,
                l=20,
                r=20
            ),

            xaxis_title="",

            yaxis_title=
                "Number of Cultural Figures"
        )


        st.plotly_chart(

            fig_cultural,

            use_container_width=True
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    """
    <div class="footer">
        Pakistan Cultural & Linguistic Atlas
        | Digital Humanities Project
    </div>
    """,
    unsafe_allow_html=True
)
