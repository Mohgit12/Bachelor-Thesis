import rasterio
import numpy as np
import plotly.graph_objects as go


# 1. LOAD RASTERS WITH REAL COORDINATES

rasters = {
    "Baseline": r"C:\Year 3\Bachelor Thesis\Thesis\Weighted_Overlays\weighted_overlay1.tif", # Baseline
    "Policy": r"C:\Year 3\Bachelor Thesis\Thesis\Weighted_Overlays\weighted_overlay2.tif",
    "Equal": r"C:\Year 3\Bachelor Thesis\Thesis\Weighted_Overlays\weighted_overlay3.tif"
}

data = {}
coords = None

for name, path in rasters.items():
    with rasterio.open(path) as src:
        arr = src.read(1).astype(float)

        if src.nodata is not None:
            arr[arr == src.nodata] = np.nan

        data[name] = arr

        if coords is None:
            rows, cols = arr.shape

            # Pixel center coordinates from GeoTIFF transform
            x = src.transform.c + (np.arange(cols) + 0.5) * src.transform.a
            y = src.transform.f + (np.arange(rows) + 0.5) * src.transform.e

            coords = (x, y)

x, y = coords


# 2. CREATE MAP FIGURE

fig_map = go.Figure()

for i, (name, arr) in enumerate(data.items()):
    fig_map.add_trace(
        go.Heatmap(
            z=arr,
            x=x,
            y=y,
            visible=(i == 0),
            colorscale="Viridis",
            colorbar=dict(title="Suitability"),
            name=name,
            hovertemplate=(
                "X: %{x}<br>"
                "Y: %{y}<br>"
                "Suitability: %{z}<extra></extra>"
            )
        )
    )

buttons = []

for i, name in enumerate(data.keys()):
    visible = [False] * len(data)
    visible[i] = True

    buttons.append(
        dict(
            label=name,
            method="update",
            args=[
                {"visible": visible},
                {"title": f"{name} Suitability Map"}
            ]
        )
    )

fig_map.update_layout(
    title="Baseline Suitability Map",
    updatemenus=[dict(buttons=buttons, direction="down")],
    height=700
)

fig_map.update_yaxes(
    scaleanchor="x",
    scaleratio=1
)


# 3. HISTOGRAM

hist_fig = go.Figure()

for name, arr in data.items():
    vals = arr[~np.isnan(arr)]

    hist_fig.add_trace(
        go.Histogram(
            x=vals,
            name=name,
            opacity=0.6
        )
    )

hist_fig.update_layout(
    barmode="overlay",
    title="Suitability Distribution",
    xaxis_title="Suitability",
    yaxis_title="Count"
)


# 4. VALIDATION PLOT

hub_vals = np.array([2.67])
rand_vals = np.array([2.63])

val_fig = go.Figure()

val_fig.add_trace(
    go.Bar(
        x=["Hubs", "Random"],
        y=[hub_vals.mean(), rand_vals.mean()],
        text=[round(hub_vals.mean(), 2), round(rand_vals.mean(), 2)],
        textposition="auto"
    )
)

val_fig.update_layout(
    title="Validation: Hubs vs Random Suitability",
    yaxis_title="Mean Suitability"
)


# 5. SHOW DASHBOARD FIGURES

fig_map.show()
hist_fig.show()
val_fig.show()