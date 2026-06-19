import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling
import geopandas as gpd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

# =====================================================
# REFERENCE RASTER
# =====================================================

ref_path = r"c:\Year 3\HMI\Data\accessibility_raster1.tif"

ref_src = rasterio.open(ref_path)

ref_crs = ref_src.crs
ref_transform = ref_src.transform
ref_shape = (ref_src.height, ref_src.width)
bounds = ref_src.bounds

left = bounds.left
right = bounds.right
bottom = bounds.bottom
top = bounds.top

# =====================================================
# ALIGN FUNCTION
# =====================================================

def align_raster(path, categorical=False):

    src = rasterio.open(path)

    source = src.read(1).astype("float32")

    destination = np.empty(ref_shape, dtype="float32")

    method = (
        Resampling.nearest
        if categorical
        else Resampling.bilinear
    )

    reproject(
        source=source,
        destination=destination,
        src_transform=src.transform,
        src_crs=src.crs,
        dst_transform=ref_transform,
        dst_crs=ref_crs,
        resampling=method
    )

    return destination

# =====================================================
# LOAD RASTERS
# =====================================================

access = align_raster(
    r"c:\Year 3\HMI\Data\accessibility_raster1.tif"
)

demand = align_raster(
    r"c:\Year 3\HMI\Data\delivpoints_raster.tif"
)

pop = align_raster(
    r"c:\Year 3\HMI\Data\pop_raster.tif"
)

land = align_raster(
    r"c:\Year 3\HMI\Data\landuse_Raster.tif"
)

water = align_raster(
    r"c:\Year 3\HMI\Data\water_raster.tif",
    categorical=True
)

# =====================================================
# NORMALISE
# =====================================================

def normalise(arr):

    arr = np.where(np.isfinite(arr), arr, np.nan)

    mn = np.nanmin(arr)
    mx = np.nanmax(arr)

    if mx - mn == 0:
        return np.zeros_like(arr)

    return (arr - mn) / (mx - mn)

access = normalise(access)
demand = normalise(demand)
pop = normalise(pop)
land = normalise(land)

# =====================================================
# HUBS
# =====================================================

hubs = gpd.read_file(
    r"C:\Year 3\HMI\Data\ams_hubs.shp"
)

hubs = hubs.to_crs(ref_crs)

# =====================================================
# BOUNDARY
# =====================================================

boundary = gpd.read_file(
    r"c:\Year 3\HMI\Data\amsterdam_boundary.shp"
)

boundary = boundary.to_crs(ref_crs)

# =====================================================
# WEIGHTED OVERLAY
# =====================================================

def compute(weights):

    wa, wd, wp, wl = weights

    score = (
        wa * access +
        wd * demand +
        wp * pop +
        wl * land
    )

    score = np.where(water == 1, np.nan, score)

    return score

# =====================================================
# DASH APP
# =====================================================

app = Dash(__name__)

app.layout = html.Div([

    html.H2(
        "Amsterdam Micro-Hub Suitability Dashboard"
    ),

    html.Label("Accessibility Weight"),

    dcc.Slider(
        0,
        1,
        0.05,
        value=0.30,
        id="access_slider"
    ),

    html.Br(),

    html.Label("Delivery Demand Weight"),

    dcc.Slider(
        0,
        1,
        0.05,
        value=0.30,
        id="demand_slider"
    ),

    html.Br(),

    html.Label("Population Weight"),

    dcc.Slider(
        0,
        1,
        0.05,
        value=0.25,
        id="pop_slider"
    ),

    html.Br(),

    html.Label("Land Use Weight"),

    dcc.Slider(
        0,
        1,
        0.05,
        value=0.15,
        id="land_slider"
    ),

    html.Br(),

    dcc.Graph(
        id="map",
        style={"height": "85vh"}
    ),
    html.Div(
    id="explanation_panel",
    children="Click a location on the map to see why it scores that way.",
    style={
        "padding": "15px",
        "border": "1px solid #ddd",
        "backgroundColor": "#f8f8f8",
        "fontSize": "16px"
    }
)
])


# =====================================================
# CALLBACK
# =====================================================

@app.callback(
    Output("map", "figure"),
    Output("explanation_panel", "children"),
    Input("access_slider", "value"),
    Input("demand_slider", "value"),
    Input("pop_slider", "value"),
    Input("land_slider", "value"),
    Input("map", "clickData")
)
def update(wa, wd, wp, wl, clickData):

    # -----------------------------
    # Compute weighted overlay
    # -----------------------------
    score = compute([wa, wd, wp, wl])

    score_min = np.nanmin(score)
    score_max = np.nanmax(score)

    score_5 = 1 + 4 * (score - score_min) / (score_max - score_min + 1e-9)

    # -----------------------------
    # Build map
    # -----------------------------
    fig = go.Figure()

    fig.add_trace(
        go.Heatmap(
            z=np.flipud(score_5),
            x=np.linspace(left, right, score.shape[1]),
            y=np.linspace(bottom, top, score.shape[0]),
            colorscale="Viridis",
            colorbar=dict(title="Suitability (1–5)"),
            hovertemplate=(
                "<b>Suitability</b>: %{z:.2f} / 5<br>"
                "X: %{x:.0f}<br>"
                "Y: %{y:.0f}"
                "<extra></extra>"
            )
        )
    )

    fig.add_trace(
        go.Scatter(
            x=hubs.geometry.x,
            y=hubs.geometry.y,
            mode="markers",
            marker=dict(size=8, color="red"),
            name="Micro-Hubs"
        )
    )

    for geom in boundary.geometry:
        if geom.geom_type == "MultiPolygon":
            for poly in geom.geoms:
                x, y = poly.exterior.xy
                fig.add_trace(go.Scatter(x=list(x), y=list(y), mode="lines", line=dict(width=2), showlegend=False))
        else:
            x, y = geom.exterior.xy
            fig.add_trace(go.Scatter(x=list(x), y=list(y), mode="lines", line=dict(width=2), showlegend=False))

    fig.update_layout(
        title="Weighted Overlay Suitability Map",
        template="plotly_white"
    )

    fig.update_yaxes(scaleanchor="x", scaleratio=1)

    # -----------------------------
    # Explanation panel (default)
    # -----------------------------
    if clickData is None:
        return fig, html.Div([
            html.H3("Explanation"),
            html.P("Click a location on the map to see why it scores that way.")
        ])

    # -----------------------------
    # Get clicked cell
    # -----------------------------
    x = clickData["points"][0]["x"]
    y = clickData["points"][0]["y"]

    col = int((x - left) / (right - left) * (score.shape[1] - 1))
    row = int((top - y) / (top - bottom) * (score.shape[0] - 1))

    row = np.clip(row, 0, score.shape[0] - 1)
    col = np.clip(col, 0, score.shape[1] - 1)

    # -----------------------------
    # Extract layer values
    # -----------------------------
    a = access[row, col]
    d = demand[row, col]
    p = pop[row, col]
    l = land[row, col]

    raw_score = wa*a + wd*d + wp*p + wl*l
    local_score = 1 + 4 * (raw_score - score_min) / (score_max - score_min + 1e-9)

    # -----------------------------
    # Explanation panel (HMI logic)
    # -----------------------------
    explanation = html.Div([
        html.H3("Why this location scores this way"),

        html.P(f"Suitability: {local_score:.2f} / 5"),

        html.Hr(),

        html.P(f"Accessibility: {wa:.2f} × {a:.2f} = {wa*a:.2f}"),
        html.P(f"Delivery demand: {wd:.2f} × {d:.2f} = {wd*d:.2f}"),
        html.P(f"Population: {wp:.2f} × {p:.2f} = {wp*p:.2f}"),
        html.P(f"Land use: {wl:.2f} × {l:.2f} = {wl*l:.2f}"),

        html.Hr(),

        html.P(
            "Interpretation: the weights control which spatial factor dominates the decision."
        )
    ])

    return fig, explanation
# =====================================================
# RUN
# =====================================================

if __name__ == "__main__":
    app.run(debug=True)
