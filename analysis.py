import geopandas as gpd
import rasterio
import numpy as np
import random
from shapely.geometry import Point
from scipy.stats import mannwhitneyu

# =================================================
# 1. RANDOM POINT GENERATION
# =================================================

mask = gpd.read_file(r"suitability_area_ExportFeatures.shp")
mask = mask.to_crs(28992)

study_area = mask.union_all()

def random_points_in_polygon(poly, n):
    minx, miny, maxx, maxy = poly.bounds
    points = []

    while len(points) < n:
        x = random.uniform(minx, maxx)
        y = random.uniform(miny, maxy)
        p = Point(x, y)

        if poly.contains(p):
            points.append(p)

    return points


points = random_points_in_polygon(study_area, 30)

random_gdf = gpd.GeoDataFrame(
    geometry=points,
    crs="EPSG:28992"
)

random_gdf.to_file(r"random.shp")

print("Random points created")

# =================================================
# 2. RASTER STATS
# =================================================

rasters = {
    "Baseline": r"Weighted_Overlays\weighted_overlay1.tif",
    "Policy": r"Weighted_Overlays\weighted_overlay2.tif",
    "Equal": r"Weighted_Overlays\weighted_overlay3.tif"
}

for name, path in rasters.items():

    with rasterio.open(path) as src:
        arr = src.read(1)
        nodata = src.nodata

    if nodata is not None:
        arr = arr[arr != nodata]

    print("\n", name)
    print("Mean:", np.mean(arr))
    print("Std:", np.std(arr))
    print("Min:", np.min(arr))
    print("Max:", np.max(arr))

    unique, counts = np.unique(arr, return_counts=True)

    print("\nClass Distribution:")
    for u, c in zip(unique, counts):
        print(u, c)

# =================================================
# 3. VALIDATION FUNCTION
# =================================================

def extract_values(raster_path, points):
    values = []

    with rasterio.open(raster_path) as src:
        nodata = src.nodata

        for geom in points.geometry:
            for val in src.sample([(geom.x, geom.y)]):
                v = val[0]

                if nodata is not None and v == nodata:
                    continue

                values.append(v)

    return np.array(values)


# =================================================
# 4. LOAD DATA FOR VALIDATION
# =================================================

hubs = gpd.read_file(r"ams_hubs_ExportFeatures.shp")
random_pts = gpd.read_file(r"random.shp")

baseline_raster = rasters["Baseline"]

# =================================================
# 5. CRS ALIGNMENT (CRITICAL)
# =================================================

with rasterio.open(baseline_raster) as src:
    hubs = hubs.to_crs(src.crs)
    random_pts = random_pts.to_crs(src.crs)

# =================================================
# 6. EXTRACT VALUES
# =================================================

hub_vals = extract_values(baseline_raster, hubs)
rand_vals = extract_values(baseline_raster, random_pts)

# =================================================
# 7. STATISTICS
# =================================================

print("\nVALIDATION RESULTS")
print("Mean hubs:", hub_vals.mean())
print("Mean random:", rand_vals.mean())

u, p = mannwhitneyu(hub_vals, rand_vals)

print("U:", u)
print("p:", p)

# =================================================
# NOTE
# =================================================
"""
Initial incorrect Mean hubs = 0.0 was caused by CRS mismatch:
- hubs were EPSG:4326
- raster was EPSG:28992

After reprojection, results are valid and consistent.
"""