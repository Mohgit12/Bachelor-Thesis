import rasterio
import numpy as np
import plotly.graph_objects as go
import plotly.express as px


# 1. LOAD RASTERS

rasters = {
    "Baseline": r"weighted_overlay1.tif", # Baseline
    "Policy": r"weighted_overlay2.tif",
    "Equal": r"weighted_overlay3.tif"
}

data = {}

for name, path in rasters.items():
    with rasterio.open(path) as src:
        arr = src.read(1).astype(float)
        arr[arr == src.nodata] = np.nan
        data[name] = arr


# 2. CREATE IMAGE FIGURES

fig_map = go.Figure()

for i, (name, arr) in enumerate(data.items()):
    fig_map.add_trace(
        go.Heatmap(
            z=arr,
            visible=(i == 0),
            colorscale="Viridis",
            colorbar=dict(title="Suitability"),
            name=name,
            hovertemplate="Suitability: %{z}<extra></extra>"
        )
    )

# Dropdown buttons
buttons = []
for i, name in enumerate(data.keys()):
    visible = [False] * len(data)
    visible[i] = True

    buttons.append(
        dict(
            label=name,
            method="update",
            args=[{"visible": visible},
                  {"title": f"{name} Suitability Map"}]
        )
    )

fig_map.update_layout(
    title="Baseline Suitability Map",
    updatemenus=[dict(buttons=buttons, direction="down")],
    height=700
)


# 3. FLATTEN VALUES FOR HISTOGRAM

hist_fig = go.Figure()

for name, arr in data.items():
    vals = arr[~np.isnan(arr)]
    hist_fig.add_trace(
        go.Histogram(x=vals, name=name, opacity=0.6)
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

val_fig.add_trace(go.Bar(
    x=["Hubs", "Random"],
    y=[hub_vals.mean(), rand_vals.mean()],
    text=[hub_vals.mean(), rand_vals.mean()],
    textposition="auto"
))

val_fig.update_layout(
    title="Validation: Hubs vs Random Suitability",
    yaxis_title="Mean Suitability"
)


# 5. SHOW EVERYTHING

fig_map.show()
hist_fig.show()
val_fig.show()